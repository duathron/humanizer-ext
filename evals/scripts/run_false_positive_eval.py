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
import json
import subprocess
import sys
from pathlib import Path

from rapidfuzz.distance import Levenshtein

from evals.scripts._shared import (
    SkillRunError,
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
    """Return (domain, body_text) for a sample file with optional YAML frontmatter.

    Handles both EN-style top-level ``domain:`` and DE-style indented
    ``metadata:\\n  domain:`` by stripping leading whitespace before the
    ``startswith`` check.
    """
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---\n"):
        end = raw.find("\n---\n", 4)
        if end >= 0:
            frontmatter = raw[4:end]
            body = raw[end + 5:].strip()
            domain_match = next(
                (line.strip().split(":", 1)[1].strip() for line in frontmatter.splitlines()
                 if line.strip().startswith("domain:")),
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


PARTIALS_SUBDIR = "_partial"


def _discover_corpus_files(corpus_dir: Path) -> list[Path]:
    """Return sorted list of corpus sample files under *corpus_dir*.

    Walks recursively so DE corpora nested under source subdirs
    (e.g. ``redistributable/<source>/<file>.md``) are found just like
    flat EN corpora.  Files whose name starts with ``_`` (``_LICENSE``,
    ``_SOURCE`` sidecars) and non-.md/.txt files are excluded.
    """
    return sorted(
        p for p in corpus_dir.rglob("*")
        if p.is_file() and p.suffix in {".md", ".txt"} and not p.name.startswith("_")
    )


def _partial_path(
    lang: str,
    corpus: str,
    corpus_dir: Path,
    file_path: Path,
    *,
    _partial_dir: Path | None = None,
) -> Path:
    """Per-file intermediate report path. Allows resume across sessions.

    The cache key is derived from the file's path *relative* to *corpus_dir*
    with path separators replaced by ``_`` and the suffix stripped.  This
    avoids stem collisions when two files in different source subdirs share
    the same basename (DE nested layout).

    For flat EN corpora the relative path is just the filename so existing
    partial names are unchanged in practice (though the argument signature
    changed — callers must pass corpus_dir and file_path).

    ``_partial_dir`` overrides the default location; used by tests to avoid
    writing into the real evals/reports/_partial/ directory.
    """
    rel_key = str(file_path.relative_to(corpus_dir).with_suffix("")).replace("/", "_").replace("\\", "_")
    base_dir = _partial_dir if _partial_dir is not None else REPO_ROOT / "evals" / "reports" / PARTIALS_SUBDIR
    return base_dir / f"fp_{lang}_{corpus}_{rel_key}.json"


def _is_session_limit_error(exc: SkillRunError) -> bool:
    """Return True when the error message indicates a Pro-plan session limit."""
    return "session limit" in str(exc).lower()


def run(
    lang: str = "en",
    corpus: str = "synthetic",
    model: str = "sonnet",
    threshold: float = DEFAULT_THRESHOLD,
    force: bool = False,
    aggregate_only: bool = False,
    *,
    _corpus_dir_override: Path | None = None,
    _partial_dir_override: Path | None = None,
) -> dict:
    """Run FP eval. Idempotent across sessions: each file's score is cached to
    evals/reports/_partial/fp_<lang>_<corpus>_<file_stem>.json. Re-runs skip
    files with existing partials — handles claude CLI subscription session-limit
    interruptions without re-burning quota.

    Per-item error isolation: a single ``subprocess.TimeoutExpired`` or
    non-session-limit ``SkillRunError`` is recorded in ``summary['failed']``
    and the loop continues.  A session-limit error breaks the loop immediately
    (every subsequent call would also fail) and sets
    ``summary['session_limit_hit'] = True``.  Both failure kinds leave
    ``summary['is_complete'] = False`` so the run is resumable.
    """
    if not aggregate_only:
        verify_skill_install()
    if _corpus_dir_override is not None:
        corpus_dir = _corpus_dir_override
    elif corpus == "personal":
        corpus_dir = _resolve_personal_samples_dir()
    else:
        corpus_dir = REPO_ROOT / "evals" / "corpus" / lang / "human" / corpus
    files = _discover_corpus_files(corpus_dir)

    if _partial_dir_override is not None:
        partial_dir = _partial_dir_override
    else:
        partial_dir = REPO_ROOT / "evals" / "reports" / PARTIALS_SUBDIR
    partial_dir.mkdir(parents=True, exist_ok=True)

    per_file: list[dict] = []
    skipped_no_partial: list[str] = []
    failed: list[dict] = []
    session_limit_hit = False

    for path in files:
        partial = _partial_path(lang, corpus, corpus_dir, path, _partial_dir=partial_dir)
        if partial.exists() and not force:
            per_file.append(json.loads(partial.read_text(encoding="utf-8")))
            continue
        if aggregate_only:
            skipped_no_partial.append(path.name)
            continue

        domain, body = _read_sample(path)
        try:
            score = score_human_text(body, lang=lang, model=model, domain=domain)
        except SkillRunError as exc:
            if _is_session_limit_error(exc):
                print(
                    f"Session limit hit on {path.name} — stopping; "
                    "re-run after reset to resume from partials."
                )
                session_limit_hit = True
                break
            failed.append({"file": path.name, "error": str(exc)[:300]})
            continue
        except subprocess.TimeoutExpired as exc:
            failed.append({"file": path.name, "error": f"timeout after {exc.timeout}s"})
            continue

        score["file"] = path.name
        score["domain"] = domain
        score["above_threshold"] = score["edit_ratio"] > threshold
        partial.write_text(json.dumps(score, indent=2, ensure_ascii=False) + "\n")
        per_file.append(score)

    total = len(per_file)
    over_edited = sum(1 for s in per_file if s["above_threshold"])
    quick_drops = sum(1 for s in per_file if s["density_preflight_quick_drop"])
    mean_ratio = sum(s["edit_ratio"] for s in per_file) / total if total else 0.0
    is_complete = (
        not skipped_no_partial and not failed and not session_limit_hit
    )

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
            "skipped_no_partial": skipped_no_partial,
            "failed": failed,
            "session_limit_hit": session_limit_hit,
            "is_complete": is_complete,
        },
        "per_file": per_file,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "False-positive rate eval runner. Idempotent: per-file partials cached "
            "in evals/reports/_partial/ so you can resume across Pro plan sessions."
        )
    )
    parser.add_argument("--lang", default="en")
    parser.add_argument(
        "--corpus", default="synthetic",
        choices=["synthetic", "public_domain", "contributed", "personal",
                 "redistributable", "research_only"],
    )
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument(
        "--force", action="store_true",
        help="Re-score files even if a partial exists.",
    )
    parser.add_argument(
        "--aggregate-only", action="store_true",
        help="No API calls; just aggregate existing partials into a summary.",
    )
    args = parser.parse_args()

    report = run(
        lang=args.lang,
        corpus=args.corpus,
        model=args.model,
        threshold=args.threshold,
        force=args.force,
        aggregate_only=args.aggregate_only,
    )
    name = f"false_positive_{args.lang}_{args.corpus}"
    json_path, md_path = write_report(name, report)
    print(f"Wrote {json_path.name} and {md_path.name}")
    print(
        f"Mean edit ratio: {report['summary']['mean_edit_ratio']} "
        f"({report['summary']['files_over_threshold']}/{report['summary']['total_files']} over {args.threshold})"
    )
    if report["summary"].get("skipped_no_partial"):
        print(
            f"Skipped (no partial yet): {report['summary']['skipped_no_partial']} — "
            f"re-run without --aggregate-only after next session reset."
        )
    if report["summary"].get("failed"):
        print(
            f"Per-item failures ({len(report['summary']['failed'])} items — will retry on re-run): "
            + ", ".join(f["file"] for f in report["summary"]["failed"])
        )
    if report["summary"].get("session_limit_hit"):
        print(
            "Session limit hit — stopping; re-run after reset to resume from partials."
        )
    is_complete = report["summary"].get("is_complete", True)
    # Non-zero exit when: run is incomplete (any failures / session limit) OR
    # run is complete but files exceeded the edit-ratio threshold.
    if not is_complete:
        sys.exit(1)
    sys.exit(1 if report["summary"]["files_over_threshold"] > 0 else 0)


if __name__ == "__main__":
    main()
