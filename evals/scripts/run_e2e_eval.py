"""End-to-end eval runner — judge-LLM scored rewrite quality.

For each AI input in evals/corpus/{lang}/e2e/, run the skill, then ask a
judge LLM to score the rewrite on human-ness, meaning preservation, and
length appropriateness. Each case is run 3 times to capture both skill
sampling and judge noise; thresholds apply to the mean across runs.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

from anthropic import Anthropic

from evals.scripts._shared import (
    run_skill,
    verify_skill_install,
    write_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
JUDGE_PROMPT_PATH = REPO_ROOT / "evals" / "scripts" / "judge_prompt.md"

DEFAULT_RUNS = 3
DEFAULT_THRESHOLDS = {"human_ness": 7.5, "meaning": 9.0, "length": 7.0}


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
        max_tokens=1024,
        system=system_prompt,
        tools=[_REPORT_SCORES_TOOL],
        tool_choice={"type": "tool", "name": "report_scores"},
        messages=[{"role": "user", "content": user_msg}],
    )
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "report_scores":
            return dict(block.input)
    raise RuntimeError("judge LLM did not call report_scores tool")


def score_case(
    case: dict, *, runs: int = DEFAULT_RUNS, model: str = "sonnet", judge_model: str = "sonnet"
) -> dict:
    """Run skill+judge `runs` times on one case and aggregate mean+stddev."""
    run_results = []
    for run_idx in range(runs):
        skill_out = run_skill(
            case["input"],
            lang=case.get("lang", "en"),
            mode="full",
            domain=case.get("domain"),
            model=model,
        )
        rewrite = skill_out.get("final") or skill_out.get("draft") or ""
        scores = _call_judge(
            judge_model=judge_model,
            input_text=case["input"],
            rewrite=rewrite,
            domain=case.get("domain", "casual"),
        )
        scores["rewrite_length_words"] = len(rewrite.split())
        run_results.append(scores)

    def _mean(key: str) -> float:
        return round(statistics.fmean(r[key] for r in run_results), 3)

    def _stddev(key: str) -> float:
        if runs < 2:
            return 0.0
        return round(statistics.stdev(r[key] for r in run_results), 3)

    return {
        "case_id": case["id"],
        "domain": case.get("domain"),
        "runs": run_results,
        "mean": {k: _mean(k) for k in ("human_ness", "meaning", "length")},
        "stddev": {k: _stddev(k) for k in ("human_ness", "meaning", "length")},
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
