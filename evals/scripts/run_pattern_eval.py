"""Pattern-detection eval runner.

Per pattern in the corpus, run each case through the skill and check whether
the rewrite removes every term in `expected_changes`. Detection rate per
pattern is `len(detected_cases) / len(total_cases)`. The runner fails the
build (exit 1) if any pattern's rate falls below the threshold.
"""
from __future__ import annotations

import argparse
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


def run(
    lang: str = "en",
    pattern: int | None = None,
    model: str = "sonnet",
    threshold: float = DEFAULT_THRESHOLD,
) -> dict:
    verify_skill_install()
    corpus_dir = REPO_ROOT / "evals" / "corpus" / lang / "patterns"
    cases = load_pattern_corpus(corpus_dir)
    if pattern is not None:
        cases = [c for c in cases if c.metadata.get("pattern_id") == pattern]

    by_pattern: dict[int, list[dict]] = defaultdict(list)
    for case in cases:
        score = score_case(case, model=model)
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
        },
        "per_pattern": per_pattern_summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Pattern-detection eval runner.")
    parser.add_argument("--lang", default="en")
    parser.add_argument("--pattern", type=int, default=None, help="Filter to one pattern ID")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()

    report = run(
        lang=args.lang, pattern=args.pattern, model=args.model, threshold=args.threshold
    )
    json_path, md_path = write_report(f"pattern_{args.lang}", report)
    print(f"Wrote {json_path.name} and {md_path.name}")
    print(
        f"Overall detection rate: {report['summary']['overall_detection_rate']} "
        f"({report['summary']['patterns_below_threshold']}/{report['summary']['total_patterns']} below {args.threshold})"
    )
    sys.exit(1 if report["summary"]["patterns_below_threshold"] > 0 else 0)


if __name__ == "__main__":
    main()
