"""Tests for evals/scripts/_shared.py — repo-side eval utilities."""
import json
from pathlib import Path

import pytest

from evals.scripts._shared import Case, load_pattern_corpus

REPO_ROOT = Path(__file__).parent.parent


def test_case_dataclass_required_fields():
    case = Case(
        id="pattern_007_en_001",
        input="Additionally, the report underscores the pivotal moment.",
        expected_changes=["Additionally", "underscores", "pivotal moment"],
        expected_unchanged=[],
        domain="casual",
        metadata={"pattern_id": 7, "source": "manual_curation"},
    )
    assert case.id == "pattern_007_en_001"
    assert case.metadata["pattern_id"] == 7


def test_load_pattern_corpus_returns_cases(tmp_path):
    corpus_dir = tmp_path / "patterns"
    corpus_dir.mkdir()
    (corpus_dir / "pattern_007.json").write_text(json.dumps({
        "pattern_id": 7,
        "pattern_name": "AI vocabulary",
        "lang": "en",
        "cases": [
            {
                "id": "pattern_007_en_001",
                "input": "Additionally, ...",
                "expected_changes": ["Additionally"],
                "expected_unchanged": [],
                "domain": "casual",
                "source": "manual_curation",
            }
        ],
    }))
    cases = load_pattern_corpus(corpus_dir)
    assert len(cases) == 1
    assert cases[0].id == "pattern_007_en_001"
    assert cases[0].metadata["pattern_id"] == 7
    assert cases[0].metadata["pattern_name"] == "AI vocabulary"


def test_load_pattern_corpus_empty_dir(tmp_path):
    corpus_dir = tmp_path / "patterns"
    corpus_dir.mkdir()
    assert load_pattern_corpus(corpus_dir) == []


from evals.scripts._shared import parse_skill_output


SAMPLE_FULL_OUTPUT = """Treating this as **casual** writing.

Pre-flight: 4 Tier-1 tells per 100 words → AI-heavy. Full pass.

**Draft rewrite:**
> AI coding assistants speed up some tasks.
> They are good at boilerplate.

**Final AI audit findings:**
- One em dash retained ("X — Y")
- Rule of three softened

**Final rewrite:**
> AI coding assistants speed up boilerplate.
> They struggle with architecture.
"""


def test_parse_skill_output_extracts_draft_and_final():
    parsed = parse_skill_output(SAMPLE_FULL_OUTPUT)
    assert "AI coding assistants speed up some tasks" in parsed["draft"]
    assert "AI coding assistants speed up boilerplate" in parsed["final"]
    assert parsed["domain"] == "casual"
    assert "4 Tier-1 tells" in parsed["preflight"]


def test_parse_skill_output_handles_missing_sections():
    minimal = "**Final rewrite:**\n> Just a final.\n"
    parsed = parse_skill_output(minimal)
    assert parsed["final"].strip() == "> Just a final."
    assert parsed["draft"] == ""
    assert parsed["domain"] == ""
    assert parsed["preflight"] == ""


def test_parse_skill_output_quick_mode_has_only_final():
    """Quick mode outputs cleaned text only — no Draft/Final headers."""
    quick = "Here is the cleaned text. It removed filler.\n"
    parsed = parse_skill_output(quick)
    assert parsed["final"].strip() == quick.strip()
    assert parsed["draft"] == ""
