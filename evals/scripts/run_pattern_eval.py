"""Pattern-detection eval runner.

Per pattern in the corpus, run each case through the skill and check whether
the rewrite removes every term in `expected_changes`. Detection rate per
pattern is `len(detected_cases) / len(total_cases)`. The runner fails the
build (exit 1) if any pattern's rate falls below the threshold.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from evals.scripts._shared import (
    Case,
    load_pattern_corpus,
    run_skill,
    verify_skill_install,
    write_report,
)


DEFAULT_THRESHOLD = 0.85
REPO_ROOT = Path(__file__).resolve().parents[2]


def score_case(case: Case, *, model: str = "sonnet") -> dict:
    """Run one case through the skill and report which expected_changes survived.

    A case is `detected` only when every term in `expected_changes` is absent
    from the rewrite AND at least one term was actually present in the input
    (so we are scoring a real change, not vacuously). Cases with an empty or
    inapplicable `expected_changes` list are reported with `status="unscorable"`
    and excluded from detection-rate aggregation by the runner.
    """
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
    )
    rewritten = (result.get("final") or result.get("draft") or "").lower()

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
    }


PARTIALS_SUBDIR = "_partial"


def _partial_path(lang: str, case_id: str) -> Path:
    """Per-case intermediate report path. Allows resume across sessions."""
    return REPO_ROOT / "evals" / "reports" / PARTIALS_SUBDIR / f"pattern_{lang}_{case_id}.json"


def run(
    lang: str = "en",
    pattern: int | None = None,
    model: str = "sonnet",
    threshold: float = DEFAULT_THRESHOLD,
    force: bool = False,
    aggregate_only: bool = False,
) -> dict:
    """Run pattern eval. Idempotent across sessions: each case's score is
    written to evals/reports/_partial/pattern_<lang>_<case_id>.json immediately
    after scoring. Re-running picks up cached partials and only scores missing
    cases — handles claude CLI subscription session-limit interruptions
    without re-burning quota on already-completed cases.
    """
    if not aggregate_only:
        verify_skill_install()
    corpus_dir = REPO_ROOT / "evals" / "corpus" / lang / "patterns"
    cases = load_pattern_corpus(corpus_dir)
    if pattern is not None:
        cases = [c for c in cases if c.metadata.get("pattern_id") == pattern]

    partial_dir = _partial_path(lang, "_").parent
    partial_dir.mkdir(parents=True, exist_ok=True)

    by_pattern: dict[int, list[dict]] = defaultdict(list)
    skipped_no_partial = []
    for case in cases:
        partial = _partial_path(lang, case.id)
        if partial.exists() and not force:
            score = json.loads(partial.read_text(encoding="utf-8"))
            by_pattern[score["pattern_id"]].append(score)
            continue
        if aggregate_only:
            skipped_no_partial.append(case.id)
            continue

        score = score_case(case, model=model)
        partial.write_text(json.dumps(score, indent=2, ensure_ascii=False) + "\n")
        by_pattern[score["pattern_id"]].append(score)

    per_pattern_summary = []
    for pid in sorted(by_pattern.keys()):
        scores = by_pattern[pid]
        scorable = [s for s in scores if s.get("status") == "scored"]
        unscorable = [s for s in scores if s.get("status", "").startswith("unscorable")]
        detected = sum(1 for s in scorable if s["detected"])
        total = len(scorable)
        rate = detected / total if total else 0.0
        per_pattern_summary.append(
            {
                "id": pid,
                "rate": round(rate, 3),
                "detected": detected,
                "total": total,
                "unscorable": len(unscorable),
                "below_threshold": total > 0 and rate < threshold,
                "misses": [s["case_id"] for s in scorable if not s["detected"]],
            }
        )

    all_scorable = [
        s for ps in by_pattern.values() for s in ps if s.get("status") == "scored"
    ]
    overall = (
        sum(s["detected"] for s in all_scorable) / len(all_scorable)
    ) if all_scorable else 0.0
    total_unscorable = sum(p["unscorable"] for p in per_pattern_summary)

    return {
        "eval_type": "pattern",
        "lang": lang,
        "model": model,
        "threshold": threshold,
        "summary": {
            "overall_detection_rate": round(overall, 3),
            "patterns_below_threshold": sum(
                1 for p in per_pattern_summary if p["below_threshold"]
            ),
            "total_patterns": len(per_pattern_summary),
            "total_cases": sum(p["total"] for p in per_pattern_summary),
            "unscorable_cases": total_unscorable,
            "skipped_no_partial": skipped_no_partial,
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
    args = parser.parse_args()

    report = run(
        lang=args.lang,
        pattern=args.pattern,
        model=args.model,
        threshold=args.threshold,
        force=args.force,
        aggregate_only=args.aggregate_only,
    )
    json_path, md_path = write_report(f"pattern_{args.lang}", report)
    print(f"Wrote {json_path.name} and {md_path.name}")
    print(
        f"Overall detection rate: {report['summary']['overall_detection_rate']} "
        f"({report['summary']['patterns_below_threshold']}/{report['summary']['total_patterns']} below {args.threshold})"
    )
    if report["summary"].get("skipped_no_partial"):
        print(
            f"Skipped (no partial yet): {len(report['summary']['skipped_no_partial'])} cases — "
            f"re-run without --aggregate-only after next session reset."
        )
    is_complete = not report["summary"].get("skipped_no_partial")
    sys.exit(1 if is_complete and report["summary"]["patterns_below_threshold"] > 0 else 0)


if __name__ == "__main__":
    main()
