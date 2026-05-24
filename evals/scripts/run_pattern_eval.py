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
    """Run one case through the skill and report which expected_changes survived."""
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
    for term in case.expected_changes:
        if term.lower() in rewritten:
            retained.append(term)
        else:
            removed.append(term)

    detected = len(retained) == 0 and len(removed) > 0
    return {
        "case_id": case.id,
        "pattern_id": case.metadata.get("pattern_id"),
        "detected": detected,
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
        detected = sum(1 for s in scores if s["detected"])
        total = len(scores)
        rate = detected / total if total else 0.0
        per_pattern_summary.append(
            {
                "id": pid,
                "rate": round(rate, 3),
                "detected": detected,
                "total": total,
                "below_threshold": rate < threshold,
                "misses": [s["case_id"] for s in scores if not s["detected"]],
            }
        )

    overall = (
        sum(s["detected"] for ps in by_pattern.values() for s in ps)
        / sum(len(ps) for ps in by_pattern.values())
    ) if by_pattern else 0.0

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
