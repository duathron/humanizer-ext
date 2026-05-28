"""One-off corpus seeder: convert before/after examples in the pattern packs
into evals/corpus/<lang>/patterns/pattern_NNN.json files.

Run:
    python3 evals/scripts/seed_pattern_corpus.py --lang en
    python3 evals/scripts/seed_pattern_corpus.py --lang de

Commit the resulting JSON files. Re-running overwrites them.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PATTERN_HEADING_RE = re.compile(r"^###\s+(\d+)\.\s+(.+)$", re.MULTILINE)
# Match Before:/Vorher: blockquote blocks (EN + DE labels)
BEFORE_BLOCK_RE = re.compile(
    r"\*\*(?:Before|Vorher)(?:\s*\([^)]*\))?:\*\*\s*\n>\s*(.+?)(?=\n\n|\n\*\*|\Z)",
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


_BLOCKQUOTE_CONT_RE = re.compile(r"\n>\s?")


def extract_before_inputs(body: str) -> list[str]:
    """Return the text of every `**Before:**`/`**Vorher:**` quoted block in a pattern body.

    Strips leading blockquote continuation markers (`> `) from multi-line
    quoted blocks so the captured input is plain prose.
    """
    out: list[str] = []
    for match in BEFORE_BLOCK_RE.finditer(body):
        raw = match.group(1).strip()
        cleaned = _BLOCKQUOTE_CONT_RE.sub(" ", raw)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        out.append(cleaned)
    return out


def trigger_terms_from_body(body: str) -> list[str]:
    """Extract `**Words to watch:** a, b, c` or `**Phrases to watch:** ...` lists.

    Returns a flat list of comma-separated terms. Used as the seed
    `expected_changes` set for each Case. Reviewers can refine after seeding.
    """
    terms: list[str] = []
    for marker in (
        # EN labels
        "Words to watch",
        "Phrases to watch",
        "Signs to watch",
        "Tokens to watch",
        "Trigger words",
        "Trigger words / phrases",
        "Trigger phrases",
        "Trigger pattern",
        # DE labels
        "Häufige DE KI-Wörter",
        "Häufige DE KI-Phrasen",
        "Trigger-Wörter",
        "Trigger-Phrasen",
        "Trigger-Muster",
        "Zu beobachtende Phrasen",
        "Zu beobachtende Wörter",
        "Anzeichen",
    ):
        m = re.search(rf"\*\*{re.escape(marker)}:\*\*\s*([^\n]+)", body)
        if not m:
            continue
        raw = m.group(1)
        terms.extend(t.strip(" .—") for t in re.split(r"[,;|]| \| ", raw) if t.strip())
    return [t for t in terms if t and not t.startswith("`")]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed evals/corpus/<lang>/patterns/ JSON cases from the language pack."
    )
    parser.add_argument("--lang", default="en", help="Language code (en, de, ...). Default: en.")
    args = parser.parse_args()
    lang = args.lang

    pattern_pack_files = [
        REPO_ROOT / "patterns" / "_universal.md",
        REPO_ROOT / "patterns" / f"{lang}.md",
    ]
    corpus_dir = REPO_ROOT / "evals" / "corpus" / lang / "patterns"

    for pack in pattern_pack_files:
        if not pack.is_file():
            raise FileNotFoundError(f"Pattern pack missing: {pack}")

    corpus_dir.mkdir(parents=True, exist_ok=True)
    all_text = "\n\n".join(p.read_text(encoding="utf-8") for p in pattern_pack_files)
    sections = extract_pattern_sections(all_text)
    written = 0
    skipped: list[int] = []
    for pid, name, body in sections:
        inputs = extract_before_inputs(body)
        if not inputs:
            skipped.append(pid)
            continue
        triggers = trigger_terms_from_body(body)
        cases = [
            {
                "id": f"pattern_{pid:03d}_{lang}_{idx + 1:03d}",
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
            "lang": lang,
            "cases": cases,
        }
        out_path = corpus_dir / f"pattern_{pid:03d}.json"
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        written += 1
    print(f"Wrote {written} pattern corpus files to {corpus_dir}")
    if skipped:
        print(f"Skipped (no Before: block found): {sorted(skipped)}")


if __name__ == "__main__":
    main()
