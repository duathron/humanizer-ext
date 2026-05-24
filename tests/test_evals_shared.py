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


from unittest.mock import patch, MagicMock


@patch("subprocess.run")
def test_run_skill_calls_claude_with_prompt(mock_run):
    from evals.scripts._shared import run_skill

    mock_run.return_value = MagicMock(
        stdout=(
            "Treating this as **casual** writing.\n\n"
            "**Final rewrite:**\n> Cleaned output.\n"
        ),
        stderr="",
        returncode=0,
    )

    result = run_skill("Some input text.", lang="en", mode="full", model="sonnet")

    assert mock_run.called
    cmd = mock_run.call_args[0][0]
    assert "claude" in cmd[0]
    assert "-p" in cmd
    full_prompt = cmd[cmd.index("-p") + 1]
    assert "Some input text." in full_prompt
    assert "/humanizer" in full_prompt or "humanize" in full_prompt.lower()

    assert result["final"] == "> Cleaned output."
    assert result["domain"] == "casual"


@patch("subprocess.run")
def test_run_skill_passes_model_flag(mock_run):
    from evals.scripts._shared import run_skill

    mock_run.return_value = MagicMock(stdout="**Final rewrite:**\n> X.\n", stderr="", returncode=0)
    run_skill("hi", model="claude-opus-4-7")
    cmd = mock_run.call_args[0][0]
    assert "--model" in cmd
    assert cmd[cmd.index("--model") + 1] == "claude-opus-4-7"


@patch("subprocess.run")
def test_run_skill_returncode_nonzero_raises(mock_run):
    from evals.scripts._shared import run_skill, SkillRunError

    mock_run.return_value = MagicMock(stdout="", stderr="boom", returncode=1)
    with pytest.raises(SkillRunError, match="claude CLI exited 1"):
        run_skill("hi")
