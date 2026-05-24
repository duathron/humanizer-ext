"""One-off corpus seeder: convert before/after examples in the pattern packs
into evals/corpus/en/patterns/pattern_NNN.json files.

Run once: `python3 evals/scripts/seed_pattern_corpus.py`.
Commit the resulting JSON files. Re-running overwrites them.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PATTERN_PACK_FILES = [
    REPO_ROOT / "patterns" / "_universal.md",
    REPO_ROOT / "patterns" / "en.md",
]
CORPUS_DIR = REPO_ROOT / "evals" / "corpus" / "en" / "patterns"

PATTERN_HEADING_RE = re.compile(r"^###\s+(\d+)\.\s+(.+)$", re.MULTILINE)
BEFORE_BLOCK_RE = re.compile(
    r"\*\*Before(?:\s*\([^)]*\))?:\*\*\s*\n>\s*(.+?)(?=\n\n|\n\*\*|\Z)",
    re.DOTALL,
)


def extract_pattern_sections(text: str) -> list[tuple[int, str, str]]:
    """Return [(pattern_id, pattern_name, body_text), ...]."""
    matches = list(PATTERN_HEADING_RE.finditer(text))
    sections = []
    for i, m in enumerate(matches):
        pid = int(m.group(1))
        name = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((pid, name, text[body_start:body_end]))
    return sections


def extract_before_inputs(body: str) -> list[str]:
    """Return the text of every `**Before:**` quoted block in a pattern body."""
    return [match.group(1).strip() for match in BEFORE_BLOCK_RE.finditer(body)]


def trigger_terms_from_body(body: str) -> list[str]:
    """Extract `**Words to watch:** a, b, c` or `**Phrases to watch:** ...` lists.

    Returns a flat list of comma-separated terms. Used as the seed
    `expected_changes` set for each Case. Reviewers can refine after seeding.
    """
    terms: list[str] = []
    for marker in ("Words to watch", "Phrases to watch", "Signs to watch", "Tokens to watch"):
        m = re.search(rf"\*\*{marker}:\*\*\s*([^\n]+)", body)
        if not m:
            continue
        raw = m.group(1)
        terms.extend(t.strip(" .—") for t in re.split(r"[,;|]| \| ", raw) if t.strip())
    return [t for t in terms if t and not t.startswith("`")]


def main() -> None:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    all_text = "\n\n".join(p.read_text(encoding="utf-8") for p in PATTERN_PACK_FILES)
    sections = extract_pattern_sections(all_text)
    written = 0
    for pid, name, body in sections:
        inputs = extract_before_inputs(body)
        if not inputs:
            continue
        triggers = trigger_terms_from_body(body)
        cases = [
            {
                "id": f"pattern_{pid:03d}_en_{idx + 1:03d}",
                "input": input_text,
                "expected_changes": triggers[:8],
                "expected_unchanged": [],
                "domain": "casual",
                "source": "seeded_from_pattern_pack",
            }
            for idx, input_text in enumerate(inputs)
        ]
        payload = {
            "pattern_id": pid,
            "pattern_name": name,
            "lang": "en",
            "cases": cases,
        }
        out_path = CORPUS_DIR / f"pattern_{pid:03d}.json"
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        written += 1
    print(f"Wrote {written} pattern corpus files to {CORPUS_DIR}")


if __name__ == "__main__":
    main()
