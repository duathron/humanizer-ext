"""Pattern-detection eval runner.

Per pattern in the corpus, run each case through the skill and check whether
the rewrite removes every term in `expected_changes`. Detection rate per
pattern is `len(detected_cases) / len(total_cases)`. The runner fails the
build (exit 1) if any pattern's rate falls below the threshold.
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from evals.scripts._shared import (
    Case,
    SkillRunError,
    aggregate_runs,
    is_refusal,
    load_pattern_corpus,
    run_skill,
    verify_skill_install,
    write_report,
)


DEFAULT_THRESHOLD = 0.85
REPO_ROOT = Path(__file__).resolve().parents[2]


def _score_case_once(case: Case, *, model: str = "sonnet", force_full: bool = False) -> dict:
    """Run one case through the skill and report which expected_changes survived.

    Three case categories:
      - `true_negative=True`: skill should leave the input ~unchanged. Scored
        by edit-distance ratio against input; passes if ratio ≤ 0.10. Reported
        separately from detection rate. Always uses the real pre-flight (never
        forces full) so over-edit restraint is tested accurately.
      - `expected_changes` empty AND not true_negative: unscorable; surfaces a
        corpus gap (case author forgot to populate).
      - `expected_changes` populated: scorable. `detected=True` iff every
        present-in-input term is absent from rewrite. When ``force_full=True``,
        the override directive is passed to run_skill so the Tier-1 density
        pre-flight quick-drop cannot mask a detection miss.

    The returned dict for scorable cases includes three additional keys:
      - ``terms_present``: count of expected_changes terms found in the input
      - ``terms_removed``: count of those terms absent from the rewrite
      - ``preflight``: raw preflight string from the skill response
    These power the per-term removal rate metric in ``run()``.
    """
    if case.true_negative:
        # True-negative: skill should leave human-like input mostly intact.
        # Always keep force_full=False here — these cases test over-edit restraint
        # with the real pre-flight, not detection capability.
        from rapidfuzz.distance import Levenshtein
        result = run_skill(
            case.input,
            lang=case.metadata.get("lang", "en"),
            mode="full",
            domain=case.domain,
            model=model,
            force_full=False,
        )
        rewritten = result.get("final") or result.get("draft") or ""
        if is_refusal(rewritten):
            return None
        edit_distance = Levenshtein.distance(case.input, rewritten)
        edit_ratio = edit_distance / max(1, len(case.input))
        passes = edit_ratio <= 0.10
        return {
            "case_id": case.id,
            "pattern_id": case.metadata.get("pattern_id"),
            "detected": passes,  # for true-neg, "detected" = "skill correctly left it alone"
            "status": "true_negative",
            "edit_ratio": round(edit_ratio, 4),
            "passes_true_negative": passes,
            "removed_terms": [],
            "retained_terms": [],
            "rewrite_preview": rewritten[:200],
        }

    if not case.expected_changes:
        return {
            "case_id": case.id,
            "pattern_id": case.metadata.get("pattern_id"),
            "detected": False,
            "status": "unscorable_empty_expected_changes",
            "removed_terms": [],
            "retained_terms": [],
            "rewrite_preview": "",
        }

    input_lower = case.input.lower()
    present_in_input = [t for t in case.expected_changes if t.lower() in input_lower]
    if not present_in_input:
        return {
            "case_id": case.id,
            "pattern_id": case.metadata.get("pattern_id"),
            "detected": False,
            "status": "unscorable_no_trigger_in_input",
            "expected_changes": case.expected_changes,
            "removed_terms": [],
            "retained_terms": [],
            "rewrite_preview": "",
        }

    result = run_skill(
        case.input,
        lang=case.metadata.get("lang", "en"),
        mode="full",
        domain=case.domain,
        model=model,
        force_full=force_full,
    )
    rewritten_raw = result.get("final") or result.get("draft") or ""
    if is_refusal(rewritten_raw):
        return None
    rewritten = rewritten_raw.lower()

    removed: list[str] = []
    retained: list[str] = []
    for term in present_in_input:
        if term.lower() in rewritten:
            retained.append(term)
        else:
            removed.append(term)

    detected = len(retained) == 0
    return {
        "case_id": case.id,
        "pattern_id": case.metadata.get("pattern_id"),
        "detected": detected,
        "status": "scored",
        "removed_terms": removed,
        "retained_terms": retained,
        "rewrite_preview": rewritten[:200],
        "terms_present": len(present_in_input),
        "terms_removed": len(removed),
        "preflight": result.get("preflight", ""),
    }


def score_case(case: Case, *, model: str = "sonnet", force_full: bool = False, runs: int = 5) -> dict:
    """Multi-run wrapper: run the per-case scoring `runs` times and aggregate.

    Unscorable categories (no run_skill call) are decided once. Scored + true-neg
    categories run N times; each run's run_skill exception is caught EXCEPT a
    session-limit error, which re-raises so run()'s case-level break still fires.
    """
    # Unscorable categories don't call the skill — decide once, no multi-run.
    if not case.true_negative and not case.expected_changes:
        return _score_case_once(case, model=model, force_full=force_full)
    if not case.true_negative:
        input_lower = case.input.lower()
        if not [t for t in case.expected_changes if t.lower() in input_lower]:
            return _score_case_once(case, model=model, force_full=force_full)

    run_dicts: list[dict | None] = []
    for _ in range(runs):
        try:
            run_dicts.append(_score_case_once(case, model=model, force_full=force_full))
        except SkillRunError as exc:
            if _is_session_limit_error(exc):
                raise  # quota guard: propagate so run()'s break fires
            run_dicts.append(None)
        except subprocess.TimeoutExpired:
            run_dicts.append(None)

    if case.true_negative:
        values = [r["edit_ratio"] if r is not None else None for r in run_dicts]
        agg = aggregate_runs(values, kind="continuous", n_target=runs, threshold=0.10)
        present_vals = [r for r in run_dicts if r is not None]
        return {
            "case_id": case.id,
            "pattern_id": case.metadata.get("pattern_id"),
            "status": "true_negative",
            "detected": bool(agg["verdict"]),            # for true-neg, "left it alone"
            "passes_true_negative": bool(agg["verdict"]),
            "edit_ratio": agg["median"],
            "runs": [None if r is None else r["edit_ratio"] for r in run_dicts],
            "aggregate": agg,
            "rewrite_preview": (present_vals[0]["rewrite_preview"] if present_vals else ""),
        }

    # scored detection case
    values = [1.0 if (r is not None and r["detected"]) else (0.0 if r is not None else None)
              for r in run_dicts]
    agg = aggregate_runs(values, kind="binary", n_target=runs)
    present = [r for r in run_dicts if r is not None]
    med_present = round(statistics.median([r["terms_present"] for r in present])) if present else 0
    med_removed = round(statistics.median([r["terms_removed"] for r in present])) if present else 0
    return {
        "case_id": case.id,
        "pattern_id": case.metadata.get("pattern_id"),
        "status": "scored",
        "detected": bool(agg["verdict"]) if agg["verdict"] is not None else False,
        "runs": [None if r is None else r["detected"] for r in run_dicts],
        "aggregate": agg,
        "terms_present": med_present,
        "terms_removed": med_removed,
        "rewrite_preview": (present[0]["rewrite_preview"] if present else ""),
        "preflight": (present[0]["preflight"] if present else ""),  # back-compat: test_score_case_scorable_returns_extra_keys asserts this key
    }


PARTIALS_SUBDIR = "_partial"


def _partial_path(lang: str, case_id: str, *, _partial_dir: Path | None = None) -> Path:
    """Per-case intermediate report path. Allows resume across sessions.

    ``_partial_dir`` overrides the default location; used by tests to avoid
    writing into the real evals/reports/_partial/ directory.
    """
    base_dir = _partial_dir if _partial_dir is not None else REPO_ROOT / "evals" / "reports" / PARTIALS_SUBDIR
    return base_dir / f"pattern_{lang}_{case_id}.json"


def _is_session_limit_error(exc: SkillRunError) -> bool:
    """Return True when the error message indicates a Pro-plan session limit."""
    return "session limit" in str(exc).lower()


def run(
    lang: str = "en",
    pattern: int | None = None,
    model: str = "sonnet",
    threshold: float = DEFAULT_THRESHOLD,
    force: bool = False,
    aggregate_only: bool = False,
    runs: int = 5,
    *,
    _corpus_dir_override: Path | None = None,
    _partial_dir_override: Path | None = None,
) -> dict:
    """Run pattern eval. Idempotent across sessions: each case's score is
    written to evals/reports/_partial/pattern_<lang>_<case_id>.json immediately
    after scoring. Re-running picks up cached partials and only scores missing
    cases — handles claude CLI subscription session-limit interruptions
    without re-burning quota on already-completed cases.

    Per-item error isolation: a single ``subprocess.TimeoutExpired`` or
    non-session-limit ``SkillRunError`` is recorded in ``summary['failed']``
    and the loop continues.  A session-limit error breaks the loop immediately
    (every subsequent call would also fail) and sets
    ``summary['session_limit_hit'] = True``.  Both failure kinds leave
    ``summary['is_complete'] = False`` so the run is resumable.
    """
    if runs < 1:
        raise ValueError(f"runs must be >= 1, got {runs}")
    if not aggregate_only:
        verify_skill_install()
    if _corpus_dir_override is not None:
        corpus_dir = _corpus_dir_override
    else:
        corpus_dir = REPO_ROOT / "evals" / "corpus" / lang / "patterns"
    cases = load_pattern_corpus(corpus_dir)
    if pattern is not None:
        cases = [c for c in cases if c.metadata.get("pattern_id") == pattern]

    if _partial_dir_override is not None:
        partial_dir = _partial_dir_override
    else:
        partial_dir = REPO_ROOT / "evals" / "reports" / PARTIALS_SUBDIR
    partial_dir.mkdir(parents=True, exist_ok=True)

    by_pattern: dict[int, list[dict]] = defaultdict(list)
    skipped_no_partial: list[str] = []
    failed: list[dict] = []
    session_limit_hit = False

    for case in cases:
        partial = _partial_path(lang, case.id, _partial_dir=partial_dir)
        if partial.exists() and not force:
            score = json.loads(partial.read_text(encoding="utf-8"))
            by_pattern[score["pattern_id"]].append(score)
            continue
        if aggregate_only:
            skipped_no_partial.append(case.id)
            continue

        try:
            score = score_case(case, model=model, force_full=True, runs=runs)
        except SkillRunError as exc:
            if _is_session_limit_error(exc):
                print(
                    f"Session limit hit on case {case.id} — stopping; "
                    "re-run after reset to resume from partials."
                )
                session_limit_hit = True
                break
            failed.append({"case_id": case.id, "error": str(exc)[:300]})
            continue
        except subprocess.TimeoutExpired as exc:
            failed.append({"case_id": case.id, "error": f"timeout after {exc.timeout}s"})
            continue

        partial.write_text(json.dumps(score, indent=2, ensure_ascii=False) + "\n")
        by_pattern[score["pattern_id"]].append(score)

    per_pattern_summary = []
    for pid in sorted(by_pattern.keys()):
        scores = by_pattern[pid]
        scorable = [s for s in scores if s.get("status") == "scored"
                    and not s.get("aggregate", {}).get("inconclusive")]
        unscorable = [s for s in scores if s.get("status", "").startswith("unscorable")]
        true_negatives = [s for s in scores if s.get("status") == "true_negative"
                          and not s.get("aggregate", {}).get("inconclusive")]
        detected = sum(1 for s in scorable if s["detected"])
        total = len(scorable)
        rate = detected / total if total else 0.0
        tn_passes = sum(1 for s in true_negatives if s.get("passes_true_negative"))
        per_pattern_summary.append(
            {
                "id": pid,
                "rate": round(rate, 3),
                "detected": detected,
                "total": total,
                "unscorable": len(unscorable),
                "true_negatives": len(true_negatives),
                "true_neg_passes": tn_passes,
                "below_threshold": total > 0 and rate < threshold,
                "misses": [s["case_id"] for s in scorable if not s["detected"]],
                "true_neg_failures": [s["case_id"] for s in true_negatives if not s.get("passes_true_negative")],
            }
        )

    all_scorable = [
        s for ps in by_pattern.values() for s in ps
        if s.get("status") == "scored" and not s.get("aggregate", {}).get("inconclusive")
    ]
    overall = (
        sum(s["detected"] for s in all_scorable) / len(all_scorable)
    ) if all_scorable else 0.0
    total_unscorable = sum(p["unscorable"] for p in per_pattern_summary)

    inconclusive_cases = [
        s["case_id"] for ps in by_pattern.values() for s in ps
        if s.get("aggregate", {}).get("inconclusive")
    ]
    flaky_cases = [
        s["case_id"] for ps in by_pattern.values() for s in ps
        if s.get("aggregate", {}).get("flaky")
    ]
    is_complete = (
        not skipped_no_partial and not failed and not session_limit_hit
        and not inconclusive_cases
    )

    # Per-term removal rate: de-deflated companion to the all-or-nothing
    # overall_detection_rate. Counts individual terms removed vs. present
    # across all scored cases. Old partials lacking the new keys are excluded
    # from both numerator and denominator (not inferred) to avoid silent bias.
    total_terms_present = sum(
        s.get("terms_present", 0) for s in all_scorable
        if "terms_present" in s
    )
    total_terms_removed = sum(
        s.get("terms_removed", 0) for s in all_scorable
        if "terms_present" in s  # only include when both keys came from same scored run
    )
    per_term_removal_rate = (
        round(total_terms_removed / total_terms_present, 3)
        if total_terms_present > 0
        else 0.0
    )

    overall_fraction = (
        sum(s["aggregate"]["fraction"] for s in all_scorable
            if s.get("aggregate", {}).get("fraction") is not None)
        / len([s for s in all_scorable if s.get("aggregate", {}).get("fraction") is not None])
    ) if any(s.get("aggregate", {}).get("fraction") is not None for s in all_scorable) else 0.0

    return {
        "eval_type": "pattern",
        "measures": "detection-logic capability under a forced full pass (force_full=True bypasses the product's real pre-flight routing); NOT shipped-routing fidelity — see run_e2e_eval",
        "lang": lang,
        "model": model,
        "threshold": threshold,
        "summary": {
            "overall_detection_rate": round(overall, 3),
            "overall_detection_fraction": round(overall_fraction, 3),
            "per_term_removal_rate": per_term_removal_rate,
            "forced_full": True,
            "patterns_below_threshold": sum(
                1 for p in per_pattern_summary if p["below_threshold"]
            ),
            "total_patterns": len(per_pattern_summary),
            "total_cases": sum(p["total"] for p in per_pattern_summary),
            "unscorable_cases": total_unscorable,
            "skipped_no_partial": skipped_no_partial,
            "failed": failed,
            "session_limit_hit": session_limit_hit,
            "is_complete": is_complete,
            "flaky_cases": flaky_cases,
            "inconclusive_cases": inconclusive_cases,
            "runs_per_case": runs,
        },
        "per_pattern": per_pattern_summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Pattern-detection eval runner. Idempotent: per-case partials cached "
            "in evals/reports/_partial/ so you can resume across Pro plan sessions."
        )
    )
    parser.add_argument("--lang", default="en")
    parser.add_argument("--pattern", type=int, default=None, help="Filter to one pattern ID")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument(
        "--force", action="store_true",
        help="Re-score cases even if a partial exists.",
    )
    parser.add_argument(
        "--aggregate-only", action="store_true",
        help="No API calls; just aggregate existing partials into a summary.",
    )
    parser.add_argument(
        "--runs", type=int, default=5,
        help="Skill invocations per case; verdict = majority/median over runs.",
    )
    args = parser.parse_args()

    report = run(
        lang=args.lang,
        pattern=args.pattern,
        model=args.model,
        threshold=args.threshold,
        force=args.force,
        aggregate_only=args.aggregate_only,
        runs=args.runs,
    )
    json_path, md_path = write_report(f"pattern_{args.lang}", report)
    print(f"Wrote {json_path.name} and {md_path.name}")
    print(
        f"Overall detection rate: {report['summary']['overall_detection_rate']} "
        f"({report['summary']['patterns_below_threshold']}/{report['summary']['total_patterns']} below {args.threshold})"
    )
    print(
        f"Per-term removal rate: {report['summary'].get('per_term_removal_rate', 'n/a')} "
        f"(de-deflated; forced_full={report['summary'].get('forced_full', False)})"
    )
    if report["summary"].get("skipped_no_partial"):
        print(
            f"Skipped (no partial yet): {len(report['summary']['skipped_no_partial'])} cases — "
            f"re-run without --aggregate-only after next session reset."
        )
    if report["summary"].get("failed"):
        print(
            f"Per-item failures ({len(report['summary']['failed'])} cases — will retry on re-run): "
            + ", ".join(f["case_id"] for f in report["summary"]["failed"])
        )
    if report["summary"].get("session_limit_hit"):
        print(
            "Session limit hit — stopping; re-run after reset to resume from partials."
        )
    if report["summary"].get("inconclusive_cases"):
        print(
            f"Inconclusive ({len(report['summary']['inconclusive_cases'])} cases — "
            "too few successful runs; NOT resumable, needs --force or a corpus/skill fix): "
            + ", ".join(report["summary"]["inconclusive_cases"])
        )
    if report["summary"].get("flaky_cases"):
        print(f"Flaky ({len(report['summary']['flaky_cases'])} cases disagreed run-to-run): "
              + ", ".join(report["summary"]["flaky_cases"]))
    is_complete = report["summary"].get("is_complete", True)
    # Non-zero exit when: run is incomplete (any failures / session limit) OR
    # run is complete but patterns fell below the detection threshold.
    if not is_complete:
        sys.exit(1)
    sys.exit(1 if report["summary"]["patterns_below_threshold"] > 0 else 0)


if __name__ == "__main__":
    main()
