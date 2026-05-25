"""False-positive rate eval runner.

For each known-human text in the corpus, run the skill and measure:
  - `edit_ratio`: Levenshtein distance / len(input). Should stay low.
  - `density_preflight_quick_drop`: did the skill correctly detect this as
    human-written and downgrade to Quick mode?

A high edit ratio on human text means the skill is over-editing legitimate
prose — that is the failure mode the v3.2.0 Detection Guidance + Tier-1
density preflight were designed to prevent. This runner is how we measure
whether that design works.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rapidfuzz.distance import Levenshtein

from evals.scripts._shared import (
    run_skill,
    verify_skill_install,
    write_report,
)


DEFAULT_THRESHOLD = 0.10  # edit ratio above this = over-editing
REPO_ROOT = Path(__file__).resolve().parents[2]


def score_human_text(
    text: str, *, lang: str = "en", model: str = "sonnet", domain: str = "casual"
) -> dict:
    result = run_skill(text, lang=lang, mode="full", domain=domain, model=model)
    rewritten = result.get("final") or result.get("draft") or ""
    edit_distance = Levenshtein.distance(text, rewritten)
    edit_ratio = edit_distance / max(1, len(text))
    preflight = (result.get("preflight") or "").lower()
    quick_drop = "quick" in preflight and ("0 tier-1" in preflight or "0/100" in preflight or "human-authored" in preflight)
    return {
        "edit_distance": edit_distance,
        "edit_ratio": round(edit_ratio, 4),
        "preflight_message": result.get("preflight", ""),
        "density_preflight_quick_drop": quick_drop,
        "rewrite_length_chars": len(rewritten),
    }


def _read_sample(path: Path) -> tuple[str, str]:
    """Return (domain, body_text) for a sample file with optional YAML frontmatter."""
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---\n"):
        end = raw.find("\n---\n", 4)
        if end >= 0:
            frontmatter = raw[4:end]
            body = raw[end + 5:].strip()
            domain_match = next(
                (line.split(":", 1)[1].strip() for line in frontmatter.splitlines()
                 if line.startswith("domain:")),
                "casual",
            )
            return domain_match, body
    return "casual", raw.strip()


def _resolve_personal_samples_dir() -> Path:
    """Personal-mode lookup chain (per spec §4.4):
    $HUMANIZER_SAMPLES_DIR → ~/.claude/humanizer-samples/ → ./writing-samples/.
    Returns the first existing dir, or raises FileNotFoundError if none."""
    import os
    candidates: list[Path] = []
    if env := os.environ.get("HUMANIZER_SAMPLES_DIR"):
        candidates.append(Path(env).expanduser())
    candidates.append(Path.home() / ".claude" / "humanizer-samples")
    candidates.append(Path.cwd() / "writing-samples")
    for c in candidates:
        if c.is_dir():
            return c
    raise FileNotFoundError(
        "Personal samples dir not found. Set $HUMANIZER_SAMPLES_DIR or create "
        f"one of: {', '.join(str(c) for c in candidates)}"
    )


def run(
    lang: str = "en",
    corpus: str = "synthetic",
    model: str = "sonnet",
    threshold: float = DEFAULT_THRESHOLD,
) -> dict:
    verify_skill_install()
    if corpus == "personal":
        corpus_dir = _resolve_personal_samples_dir()
    else:
        corpus_dir = REPO_ROOT / "evals" / "corpus" / lang / "human" / corpus
    files = sorted(
        p for p in corpus_dir.iterdir()
        if p.is_file() and p.suffix in {".md", ".txt"} and not p.name.startswith("_")
    )

    per_file = []
    for path in files:
        domain, body = _read_sample(path)
        score = score_human_text(body, lang=lang, model=model, domain=domain)
        score["file"] = path.name
        score["domain"] = domain
        score["above_threshold"] = score["edit_ratio"] > threshold
        per_file.append(score)

    total = len(per_file)
    over_edited = sum(1 for s in per_file if s["above_threshold"])
    quick_drops = sum(1 for s in per_file if s["density_preflight_quick_drop"])
    mean_ratio = sum(s["edit_ratio"] for s in per_file) / total if total else 0.0

    return {
        "eval_type": "false_positive",
        "lang": lang,
        "corpus": corpus,
        "model": model,
        "threshold": threshold,
        "summary": {
            "mean_edit_ratio": round(mean_ratio, 4),
            "files_over_threshold": over_edited,
            "total_files": total,
            "density_preflight_quick_drop_rate": (
                round(quick_drops / total, 2) if total else 0.0
            ),
        },
        "per_file": per_file,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="False-positive rate eval runner.")
    parser.add_argument("--lang", default="en")
    parser.add_argument(
        "--corpus", default="synthetic",
        choices=["synthetic", "public_domain", "contributed", "personal"],
    )
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()

    report = run(
        lang=args.lang, corpus=args.corpus, model=args.model, threshold=args.threshold
    )
    name = f"false_positive_{args.lang}_{args.corpus}"
    json_path, md_path = write_report(name, report)
    print(f"Wrote {json_path.name} and {md_path.name}")
    print(
        f"Mean edit ratio: {report['summary']['mean_edit_ratio']} "
        f"({report['summary']['files_over_threshold']}/{report['summary']['total_files']} over {args.threshold})"
    )
    sys.exit(1 if report["summary"]["files_over_threshold"] > 0 else 0)


if __name__ == "__main__":
    main()
