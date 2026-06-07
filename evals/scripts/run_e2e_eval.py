"""End-to-end eval runner — judge-LLM scored rewrite quality.

For each AI input in evals/corpus/{lang}/e2e/, run the skill, then ask a
judge LLM to score the rewrite on human-ness, meaning preservation, and
length appropriateness. Each case is run 3 times to capture both skill
sampling and judge noise; thresholds apply to the mean across runs.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

from anthropic import Anthropic

from evals.scripts._shared import (
    SkillRunError,
    retry_with_backoff,
    run_skill,
    verify_skill_install,
    write_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
JUDGE_PROMPT_PATH = REPO_ROOT / "evals" / "scripts" / "judge_prompt.md"

DEFAULT_RUNS = 3
# meaning threshold reconciled to the documented acceptance criterion in
# docs/plans/2026-05-27-phase-2-de-pack.md (meaning >= 8.0). One canonical
# bar, documented — not "whichever passes".
DEFAULT_THRESHOLDS = {"human_ness": 7.5, "meaning": 8.0, "length": 7.0}


# Anthropic tool schema for structured judge scoring
_REPORT_SCORES_TOOL = {
    "name": "report_scores",
    "description": "Report the three judge scores for one rewrite.",
    "input_schema": {
        "type": "object",
        "properties": {
            "human_ness": {"type": "integer", "minimum": 1, "maximum": 10},
            "meaning": {"type": "integer", "minimum": 1, "maximum": 10},
            "length": {"type": "integer", "minimum": 1, "maximum": 10},
            "rationale": {
                "type": "object",
                "properties": {
                    "human_ness": {"type": "string"},
                    "meaning": {"type": "string"},
                    "length": {"type": "string"},
                },
                "required": ["human_ness", "meaning", "length"],
            },
        },
        "required": ["human_ness", "meaning", "length", "rationale"],
    },
}


def _model_to_api_id(model: str) -> str:
    """Map short names ('sonnet', 'opus') to current API IDs per repo conventions."""
    mapping = {
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-7",
        "haiku": "claude-haiku-4-5-20251001",
    }
    return mapping.get(model, model)


def _call_judge(
    *,
    judge_model: str,
    input_text: str,
    rewrite: str,
    domain: str,
) -> dict:
    """Single judge call. Returns parsed scores dict."""
    client = Anthropic()
    system_prompt = JUDGE_PROMPT_PATH.read_text(encoding="utf-8")
    user_msg = (
        f"Domain: {domain}\n\n"
        f"## ORIGINAL AI INPUT\n\n{input_text}\n\n"
        f"## SKILL REWRITE\n\n{rewrite}\n\n"
        "Reason briefly, then call report_scores."
    )
    response = client.messages.create(
        model=_model_to_api_id(judge_model),
        # 2048 (was 1024): long inputs (career Anschreiben, technical docs) made the
        # reasoning + rationale exceed 1024 tokens, truncating the tool_use JSON so a
        # score key (e.g. human_ness) was missing → KeyError downstream.
        max_tokens=2048,
        system=system_prompt,
        tools=[_REPORT_SCORES_TOOL],
        tool_choice={"type": "tool", "name": "report_scores"},
        messages=[{"role": "user", "content": user_msg}],
    )
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "report_scores":
            scores = dict(block.input)
            missing = [k for k in ("human_ness", "meaning", "length") if k not in scores]
            if missing:
                raise SkillRunError(
                    f"judge tool_use missing score(s) {missing} "
                    f"(stop_reason={response.stop_reason}) — likely max_tokens truncation"
                )
            return scores
    raise RuntimeError("judge LLM did not call report_scores tool")


# A failed skill run sometimes emits ONLY an editorial change-log (no rewrite
# block); the parser then hands that commentary back as the "rewrite" and the
# judge scores it ~1, tanking the mean. Detect such runs and retry the skill
# rather than scoring an extraction failure as a meaning judgement.
#
# Detection bias: over-catching just triggers a retry (cheap); under-catching
# corrupts a score. So we err on the side of catching more.  Each signal below
# is necessary because the skill emits changelogs in multiple formats.

# Signal A: bold/explicit change-log headers (original, EN-only form).
_FAILED_REWRITE_RE = re.compile(
    r"\*\*\s*(?:changes(?: made)?|what changed|summary|audit|notes?|editorial|"
    r"rationale|diff|removed|edits)\b"
    r"|concept-noun check|fabrication check|editorial annotation|change[- ]?log",
    re.IGNORECASE,
)

# Signal B: ≥2 edit-arrows total (→ or ->) across the whole text.
# Changelogs list "X → Y" per line; genuine prose almost never contains 2+.
_EDIT_ARROW_RE = re.compile(r"→|->")

# Signal C: ≥2 lines starting with a rule-ID prefix.
# Matches: #7, # 7, pattern #7, pattern7, §7, regel7 (case-insensitive).
_RULE_ID_LINE_RE = re.compile(
    r"^\s*(?:#\s?\d+|pattern\s*#?\d+|§\s?\d+|regel\s*\d+)\b",
    re.IGNORECASE | re.MULTILINE,
)

# Signal D: explicit changelog header line (line-anchored, case-insensitive).
# Catches: "Transformationen:", "entfernt:", "changes:", "removed:", "applied:", etc.
# NOT triggered by bare "entfernt" mid-sentence — requires the trailing colon.
_CHANGELOG_HEADER_RE = re.compile(
    r"^\s*(?:transformationen?|änderungen|changes?|removed|applied|entfernt)\s*:",
    re.IGNORECASE | re.MULTILINE,
)

# Signal F: a markdown bold span CONTAINING a change/edit keyword, with leading
# words allowed inside the bold — catches "**Wesentliche Änderungen:**",
# "**Änderungen:**", "**Changes made:**", "**Zusammenfassung der Änderungen:**".
# (Signal A only fires when ** is immediately followed by the keyword; a leading
# adjective like "Wesentliche" slips past it — this is the gap that leaked.)
# The bold wrapper keeps it from matching "Änderung" in ordinary prose.
_BOLD_CHANGELOG_RE = re.compile(
    r"\*\*[^*\n]{0,60}(?:änderung|zusammenfassung der|wesentliche änderung|"
    r"changes?\b|what changed|edits?\b|überarbeitung|bearbeitung)[^*\n]{0,60}\*\*",
    re.IGNORECASE,
)

_MAX_REWRITE_ATTEMPTS = 4


def _looks_like_failed_rewrite(rewrite: str) -> bool:
    """True when the skill produced no usable rewrite (empty, or commentary-only).

    Detection bias intentionally favours over-catching: an over-caught run
    triggers a cheap retry; an under-caught run corrupts the judge score (~1).

    Returns True if ANY of the following signals fire:
    1. Empty / whitespace-only.
    2. Bold/explicit EN change-log headers (original signal, preserved).
    3. ≥2 edit-arrows (→ or ->) — changelog "X → Y" listing; prose rarely has 2+.
    4. ≥2 lines starting with a rule-ID prefix (#N, pattern #N, §N, regelN).
    5. A line-anchored changelog header word followed by a colon
       (e.g. "Transformationen:", "entfernt:", "changes:", "applied:").
    """
    if not rewrite.strip():
        return True
    if _FAILED_REWRITE_RE.search(rewrite):
        return True
    if len(_EDIT_ARROW_RE.findall(rewrite)) >= 2:
        return True
    if len(_RULE_ID_LINE_RE.findall(rewrite)) >= 2:
        return True
    if _CHANGELOG_HEADER_RE.search(rewrite):
        return True
    if _BOLD_CHANGELOG_RE.search(rewrite):
        return True
    return False


def score_case(
    case: dict, *, runs: int = DEFAULT_RUNS, model: str = "sonnet", judge_model: str = "sonnet"
) -> dict:
    """Run skill+judge `runs` times on one case and aggregate mean+stddev."""
    run_results = []
    for run_idx in range(runs):
        rewrite = ""
        first_attempt_changelog = None
        for _ in range(_MAX_REWRITE_ATTEMPTS):
            skill_out = run_skill(
                case["input"],
                lang=case.get("lang", "en"),
                mode="full",
                domain=case.get("domain"),
                model=model,
                timeout=420,  # E2E inputs (esp. career Anschreiben) run longer than the 180s default
            )
            candidate = skill_out.get("final") or skill_out.get("draft") or ""
            is_changelog = _looks_like_failed_rewrite(candidate)
            if first_attempt_changelog is None:
                first_attempt_changelog = is_changelog
            if not is_changelog:
                rewrite = candidate
                break
        else:
            # All attempts returned commentary-only / empty — skip this run
            # rather than score an extraction failure as meaning ~1.
            continue
        # The judge occasionally returns an empty/truncated tool call (missing
        # scores); _call_judge raises SkillRunError on that — retry it rather
        # than crash the whole batch.
        scores = retry_with_backoff(
            lambda: _call_judge(
                judge_model=judge_model,
                input_text=case["input"],
                rewrite=rewrite,
                domain=case.get("domain", "casual"),
            ),
            max_attempts=4,
            base_delay=2.0,
        )
        scores["rewrite_length_words"] = len(rewrite.split())
        # Persist rewrite text (truncated) so humans can audit guard misses.
        scores["rewrite"] = rewrite[:1500]
        scores["first_attempt_changelog"] = bool(first_attempt_changelog)
        run_results.append(scores)

    if not run_results:
        # Every run failed to produce a usable rewrite — surface, don't crash.
        return {
            "case_id": case["id"],
            "domain": case.get("domain"),
            "runs": [],
            "mean": {k: 0.0 for k in ("human_ness", "meaning", "length")},
            "stddev": {k: 0.0 for k in ("human_ness", "meaning", "length")},
            "error": "no usable rewrite after retries (skill emitted commentary-only output)",
        }

    def _mean(key: str) -> float:
        return round(statistics.fmean(r[key] for r in run_results), 3)

    def _stddev(key: str) -> float:
        if len(run_results) < 2:
            return 0.0
        return round(statistics.stdev(r[key] for r in run_results), 3)

    def _median(key: str) -> float:
        return round(statistics.median(r[key] for r in run_results), 3)

    return {
        "case_id": case["id"],
        "domain": case.get("domain"),
        "runs": run_results,
        "mean": {k: _mean(k) for k in ("human_ness", "meaning", "length")},
        "stddev": {k: _stddev(k) for k in ("human_ness", "meaning", "length")},
        # Median alongside mean: with 3-5 samples a single outlier run can tank
        # the mean; median is more robust. Both are reported; the gate checks both
        # so a case whose median is fine does not fail due to one bad run.
        "median": {k: _median(k) for k in ("human_ness", "meaning", "length")},
    }


PARTIALS_SUBDIR = "_partial"


def _partial_path(lang: str, case_id: str) -> Path:
    """Per-case intermediate report path. Allows resume across sessions."""
    return REPO_ROOT / "evals" / "reports" / PARTIALS_SUBDIR / f"e2e_{lang}_{case_id}.json"


def run(
    lang: str = "en",
    domain: str | None = None,
    runs: int = DEFAULT_RUNS,
    model: str = "sonnet",
    judge_model: str = "sonnet",
    cases: list[str] | None = None,
    force: bool = False,
    aggregate_only: bool = False,
) -> dict:
    """Run E2E eval. Idempotent across sessions: each case's score is written to
    evals/reports/_partial/e2e_<lang>_<case_id>.json immediately after scoring.
    Re-running picks up cached partials and only scores missing cases. Use this
    to split the eval across multiple Claude Pro plan sessions when the daily
    quota would not cover a full run.

    Args:
      cases: comma-separated case IDs to score this session (e.g.
             ["e2e_en_casual_01", "e2e_en_legal_01"]). None = all cases.
      force: re-score cases even if a partial exists.
      aggregate_only: skip API calls; just aggregate existing partials. Use
                      after all sessions are done to emit the final summary.
    """
    if not aggregate_only:
        verify_skill_install()
    corpus_dir = REPO_ROOT / "evals" / "corpus" / lang / "e2e"
    case_files = sorted(corpus_dir.glob("*.json"))
    partial_dir = _partial_path(lang, "_").parent
    partial_dir.mkdir(parents=True, exist_ok=True)

    per_case = []
    skipped_no_partial = []
    for path in case_files:
        case = json.loads(path.read_text(encoding="utf-8"))
        if domain and case.get("domain") != domain:
            continue
        if cases and case["id"] not in cases:
            # Filter applied: load partial if present, otherwise mark as skipped
            partial = _partial_path(lang, case["id"])
            if partial.exists():
                per_case.append(json.loads(partial.read_text(encoding="utf-8")))
            else:
                skipped_no_partial.append(case["id"])
            continue

        partial = _partial_path(lang, case["id"])
        if partial.exists() and not force:
            per_case.append(json.loads(partial.read_text(encoding="utf-8")))
            continue
        if aggregate_only:
            skipped_no_partial.append(case["id"])
            continue

        score = score_case(case, runs=runs, model=model, judge_model=judge_model)
        partial.write_text(json.dumps(score, indent=2, ensure_ascii=False) + "\n")
        per_case.append(score)

    overall = {}
    if per_case:
        for k in ("human_ness", "meaning", "length"):
            overall[k] = round(
                statistics.fmean(c["mean"][k] for c in per_case), 3
            )

    all_runs = [r for c in per_case for r in c.get("runs", [])]
    cl = [r for r in all_runs if "first_attempt_changelog" in r]
    changelog_rate = round(sum(1 for r in cl if r["first_attempt_changelog"]) / len(cl), 3) if cl else 0.0

    return {
        "eval_type": "e2e",
        "lang": lang,
        "model": model,
        "judge_model": judge_model,
        "runs_per_case": runs,
        "thresholds": DEFAULT_THRESHOLDS,
        "summary": {
            "overall_mean": overall,
            "total_cases": len(per_case),
            "skipped_no_partial": skipped_no_partial,
            "below_threshold_count": sum(
                1 for c in per_case
                if c["mean"]["human_ness"] < DEFAULT_THRESHOLDS["human_ness"]
                or c["mean"]["meaning"] < DEFAULT_THRESHOLDS["meaning"]
                or c["mean"]["length"] < DEFAULT_THRESHOLDS["length"]
            ),
            "below_threshold_by_dimension": {
                k: sum(1 for c in per_case if c["mean"][k] < DEFAULT_THRESHOLDS[k])
                for k in ("human_ness", "meaning", "length")
            },
            # Median-based gate: a single outlier run can tank the mean of a 3-5
            # run sample; median is more robust. Both are reported so a case whose
            # median is fine does not silently fail on mean alone.
            "below_threshold_by_dimension_median": {
                k: sum(
                    1 for c in per_case
                    if c.get("median", c["mean"])[k] < DEFAULT_THRESHOLDS[k]
                )
                for k in ("human_ness", "meaning", "length")
            },
            "changelog_first_attempt_rate": changelog_rate,
        },
        "per_case": per_case,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "E2E rewrite-quality eval runner. "
            "Idempotent: per-case partials cached in evals/reports/_partial/ "
            "so you can split the eval across multiple Claude Pro plan sessions."
        )
    )
    parser.add_argument("--lang", default="en")
    parser.add_argument("--domain", default=None)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument(
        "--judge-model", default="sonnet",
        help="Short name (sonnet, opus) or full API ID",
    )
    parser.add_argument(
        "--cases", default=None,
        help="Comma-separated case IDs to score this session (e.g. "
             "'e2e_en_casual_01,e2e_en_legal_01'). Other cases load from "
             "partial cache if available. Use to fit a Pro plan quota.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-score cases even if a partial exists.",
    )
    parser.add_argument(
        "--aggregate-only", action="store_true",
        help="No API calls; just aggregate existing partials into a summary.",
    )
    args = parser.parse_args()

    cases_filter = [c.strip() for c in args.cases.split(",")] if args.cases else None

    report = run(
        lang=args.lang,
        domain=args.domain,
        runs=args.runs,
        model=args.model,
        judge_model=args.judge_model,
        cases=cases_filter,
        force=args.force,
        aggregate_only=args.aggregate_only,
    )
    json_path, md_path = write_report(f"e2e_{args.lang}", report)
    print(f"Wrote {json_path.name} and {md_path.name}")
    print(f"Overall mean: {report['summary']['overall_mean']}")
    print(
        f"Below threshold: {report['summary']['below_threshold_count']}/{report['summary']['total_cases']} "
        f"(by dim: {report['summary']['below_threshold_by_dimension']})"
    )
    if report["summary"]["skipped_no_partial"]:
        print(
            f"Skipped (no partial yet): {report['summary']['skipped_no_partial']} — "
            f"re-run with --cases <id> for these or --aggregate-only after all sessions done."
        )
    # Only fail the build if all cases were scored AND any are below threshold.
    is_complete = not report["summary"]["skipped_no_partial"]
    sys.exit(1 if is_complete and report["summary"]["below_threshold_count"] > 0 else 0)


if __name__ == "__main__":
    main()
