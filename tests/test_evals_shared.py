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
    assert parsed["final"].strip() == "Just a final."  # parser strips `> ` blockquote markers
    assert parsed["draft"] == ""
    assert parsed["domain"] == ""
    assert parsed["preflight"] == ""


def test_parse_skill_output_quick_mode_has_only_final():
    """Quick mode outputs cleaned text only — no Draft/Final headers."""
    quick = "Here is the cleaned text. It removed filler.\n"
    parsed = parse_skill_output(quick)
    assert parsed["final"].strip() == quick.strip()
    assert parsed["draft"] == ""


def test_parse_skill_output_density_drop_with_final_header():
    """Full mode dropping to Quick still wraps the rewrite in Final rewrite header."""
    out = (
        "Pre-flight: 0 Tier-1 tells per 100 words → human-authored. Switching to Quick-mode.\n\n"
        "**Final rewrite:**\n> The original text, mostly unchanged.\n"
    )
    parsed = parse_skill_output(out)
    assert parsed["final"] == "The original text, mostly unchanged."
    assert "0 Tier-1 tells" in parsed["preflight"]


def test_parse_skill_output_extracts_last_blockquote_when_no_header():
    """Fallback heuristic: last blockquote in messy skill output is the rewrite."""
    messy = (
        "**Pre-flight:** 3 Tier-1 tells per 100 words → AI-heavy.\n\n"
        "**Audit notes:**\n- removed `pivotal`\n- removed em dash\n\n"
        "> The rewrite goes here, just one paragraph.\n"
    )
    parsed = parse_skill_output(messy)
    assert parsed["final"] == "The rewrite goes here, just one paragraph."


def test_parse_skill_output_alt_header_cleaned_text():
    """Fallback recognizes **Cleaned text:** as a Final-rewrite synonym."""
    alt = "**Cleaned text:**\n> Clean version.\n"
    parsed = parse_skill_output(alt)
    assert parsed["final"] == "Clean version."


def test_parse_skill_output_banners_no_rewrite_returns_empty_final():
    """If text has banners but no extractable rewrite, return empty rather than polluted text."""
    junk = (
        "**Pre-flight:** scanning...\n"
        "**Audit:** nothing found yet\n"
    )
    parsed = parse_skill_output(junk)
    assert parsed["final"] == ""


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

    assert result["final"] == "Cleaned output."  # parser strips `> ` blockquote markers
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


from unittest.mock import call


def test_retry_with_backoff_succeeds_on_third_try():
    from evals.scripts._shared import retry_with_backoff

    attempts = {"n": 0}
    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    result = retry_with_backoff(flaky, max_attempts=3, base_delay=0.01)
    assert result == "ok"
    assert attempts["n"] == 3


def test_retry_with_backoff_raises_after_max():
    from evals.scripts._shared import retry_with_backoff

    def always_fails():
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError, match="nope"):
        retry_with_backoff(always_fails, max_attempts=2, base_delay=0.01)


def test_write_report_creates_json_and_markdown(tmp_path, monkeypatch):
    from evals.scripts._shared import write_report

    monkeypatch.chdir(tmp_path)
    (tmp_path / "evals" / "reports").mkdir(parents=True)

    data = {
        "eval_type": "pattern",
        "lang": "en",
        "summary": {"detection_rate": 0.92},
        "per_pattern": [{"id": 7, "rate": 0.95}],
    }
    json_path, md_path = write_report("pattern_en_demo", data)

    assert json_path.exists()
    assert md_path.exists()
    assert json.loads(json_path.read_text())["summary"]["detection_rate"] == 0.92
    assert "pattern" in md_path.read_text().lower()
    assert "0.92" in md_path.read_text()


def test_verify_skill_install_matches(tmp_path, monkeypatch):
    from evals.scripts._shared import verify_skill_install, SkillInstallMismatch

    repo_skill = tmp_path / "SKILL.md"
    installed_skill = tmp_path / "installed_SKILL.md"
    repo_skill.write_text("same content\n")
    installed_skill.write_text("same content\n")

    verify_skill_install(repo_skill_path=repo_skill, installed_skill_path=installed_skill)


def test_verify_skill_install_mismatch_raises(tmp_path):
    from evals.scripts._shared import verify_skill_install, SkillInstallMismatch

    repo_skill = tmp_path / "SKILL.md"
    installed_skill = tmp_path / "installed_SKILL.md"
    repo_skill.write_text("repo version\n")
    installed_skill.write_text("old installed version\n")

    with pytest.raises(SkillInstallMismatch, match="bytes differ"):
        verify_skill_install(repo_skill_path=repo_skill, installed_skill_path=installed_skill)


def test_verify_skill_install_missing_installed(tmp_path):
    from evals.scripts._shared import verify_skill_install, SkillInstallMismatch

    repo_skill = tmp_path / "SKILL.md"
    repo_skill.write_text("repo version\n")
    installed_skill = tmp_path / "nope.md"

    with pytest.raises(SkillInstallMismatch, match="not installed"):
        verify_skill_install(repo_skill_path=repo_skill, installed_skill_path=installed_skill)


@patch("evals.scripts.run_pattern_eval.run_skill")
def test_pattern_eval_scores_detection(mock_run_skill, tmp_path, monkeypatch):
    from evals.scripts.run_pattern_eval import score_case
    from evals.scripts._shared import Case

    case = Case(
        id="pattern_007_en_001",
        input="Additionally, the report underscores the pivotal moment.",
        expected_changes=["Additionally", "underscores", "pivotal moment"],
        expected_unchanged=[],
        domain="casual",
        metadata={"pattern_id": 7, "pattern_name": "AI vocabulary", "lang": "en"},
    )
    # Simulate a rewrite that removed all three expected_changes
    mock_run_skill.return_value = {
        "domain": "casual",
        "preflight": "",
        "draft": "The report flags an important shift.",
        "final": "The report flags an important shift.",
    }

    score = score_case(case, model="sonnet")
    assert score["detected"] is True
    assert score["removed_terms"] == ["Additionally", "underscores", "pivotal moment"]
    assert score["retained_terms"] == []


@patch("evals.scripts.run_pattern_eval.run_skill")
def test_pattern_eval_partial_removal(mock_run_skill):
    from evals.scripts.run_pattern_eval import score_case
    from evals.scripts._shared import Case

    case = Case(
        id="pattern_007_en_002",
        input="Additionally, this is a pivotal moment.",
        expected_changes=["Additionally", "pivotal moment"],
        expected_unchanged=[],
        domain="casual",
        metadata={"pattern_id": 7, "pattern_name": "AI vocabulary", "lang": "en"},
    )
    mock_run_skill.return_value = {
        "domain": "casual",
        "preflight": "",
        "draft": "This is a pivotal moment.",
        "final": "This is a pivotal moment.",
    }
    score = score_case(case, model="sonnet")
    assert score["detected"] is False  # only 1 of 2 removed
    assert score["removed_terms"] == ["Additionally"]
    assert score["retained_terms"] == ["pivotal moment"]


@patch("evals.scripts.run_e2e_eval._call_judge")
@patch("evals.scripts.run_e2e_eval.run_skill")
def test_e2e_eval_aggregates_three_runs(mock_run_skill, mock_judge):
    from evals.scripts.run_e2e_eval import score_case

    mock_run_skill.return_value = {
        "domain": "casual", "preflight": "", "draft": "Draft.", "final": "Cleaner final."
    }
    # Judge returns three runs of slightly varying scores
    mock_judge.side_effect = [
        {"human_ness": 8, "meaning": 9, "length": 8, "rationale": {"human_ness": "ok", "meaning": "ok", "length": "ok"}},
        {"human_ness": 7, "meaning": 9, "length": 9, "rationale": {"human_ness": "ok", "meaning": "ok", "length": "ok"}},
        {"human_ness": 9, "meaning": 10, "length": 7, "rationale": {"human_ness": "ok", "meaning": "ok", "length": "ok"}},
    ]

    case = {
        "id": "e2e_en_casual_01",
        "lang": "en",
        "domain": "casual",
        "input": "AI input.",
        "reference_rewrite": None,
        "source": "test",
    }
    score = score_case(case, runs=3, model="sonnet", judge_model="sonnet")

    assert score["case_id"] == "e2e_en_casual_01"
    assert score["mean"]["human_ness"] == pytest.approx(8.0, abs=0.01)
    assert score["mean"]["meaning"] == pytest.approx(9.333, abs=0.01)
    assert score["mean"]["length"] == pytest.approx(8.0, abs=0.01)
    assert score["stddev"]["human_ness"] > 0
    assert len(score["runs"]) == 3
