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
