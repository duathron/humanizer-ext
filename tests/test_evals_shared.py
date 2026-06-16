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


# ---------------------------------------------------------------------------
# Phase 1 — commentary-fence tests (eval-only, no skill change)
# ---------------------------------------------------------------------------
from evals.scripts._shared import _strip_trailing_commentary, _AUDIT_SENTINEL


def test_audit_sentinel_value():
    assert _AUDIT_SENTINEL == "<!--HUMANIZER-AUDIT-->"


def test_strip_fence_cuts_trailing_note():
    s = (
        "Sehr geehrte Frau Reichert,\n\n"
        "ich bringe X mit.\n\n"
        "Mit freundlichen Grüßen\n"
        "Daniel\n\n"
        "<!--HUMANIZER-AUDIT-->\n"
        "Text unverändert. kein KI-Signal gefunden. DACH-register passt."
    )
    expected = (
        "Sehr geehrte Frau Reichert,\n\n"
        "ich bringe X mit.\n\n"
        "Mit freundlichen Grüßen\n"
        "Daniel"
    )
    assert _strip_trailing_commentary(s) == expected


def test_strip_fence_no_marker_unchanged():
    s = "A clean rewrite with no marker at all.\n\nSecond paragraph stays."
    assert _strip_trailing_commentary(s) == s


def test_strip_fence_no_false_cut_on_audit_word():
    s = "We reviewed the audit findings and left a comment in the thread.\n\nThe report ships Friday."
    assert _strip_trailing_commentary(s) == s


def test_strip_fence_no_false_cut_on_other_html_comment():
    s = "See the diagram <!-- figure 1 --> below for the flow.\n\nDetails follow."
    assert _strip_trailing_commentary(s) == s


def test_strip_fence_then_existing_header_still_works():
    s = "The rewrite text.\n\n**Changes:** removed two em dashes."
    assert _strip_trailing_commentary(s) == "The rewrite text."


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


# ---------------------------------------------------------------------------
# Bug 1 — parser must strip trailing skill commentary from the rewrite
# ---------------------------------------------------------------------------

# Verbatim köln example from a live DE eval run
_KOELN_QUICK_OUTPUT = (
    "wohnungsmangel und stau kennt köln wie jede andere großstadt. "
    "wirtschaftlich ist die stadt gut aufgestellt.\n\n"
    "**changes:** killed the formulaic double-\"trotz\" structure (universal #6). "
    "cut \"guten Zukunftsaussichten\""
)

def test_parse_skill_output_quick_mode_strips_trailing_commentary():
    """Quick-mode output (no Final rewrite header) must not include trailing **changes:** block."""
    parsed = parse_skill_output(_KOELN_QUICK_OUTPUT)
    # Commentary block must be gone
    assert "changes:" not in parsed["final"].lower()
    assert "Zukunftsaussichten" not in parsed["final"]
    # The rewrite body must be present
    assert "wohnungsmangel und stau" in parsed["final"]
    assert "wirtschaftlich ist die stadt gut aufgestellt" in parsed["final"]


def test_parse_skill_output_final_header_strips_trailing_commentary():
    """**Final rewrite:** block followed by **changes:** — commentary must be stripped."""
    out = (
        "**Final rewrite:**\n"
        "> wohnungsmangel und stau kennt köln wie jede andere großstadt.\n"
        "> wirtschaftlich ist die stadt gut aufgestellt.\n\n"
        "**changes:** cut \"guten Zukunftsaussichten\""
    )
    parsed = parse_skill_output(out)
    assert "changes:" not in parsed["final"].lower()
    assert "Zukunftsaussichten" not in parsed["final"]
    assert "wirtschaftlich ist die stadt gut aufgestellt" in parsed["final"]


def test_parse_skill_output_commentary_mid_sentence_not_truncated():
    """A rewrite that contains the word 'changes' mid-sentence must NOT be truncated."""
    # No newline + **heading** before 'changes' → should not be cut
    out = "Die Anzahl der Änderungen blieb gleich. Das changes nichts an der Lage.\n"
    parsed = parse_skill_output(out)
    assert "Das changes nichts an der Lage" in parsed["final"]


def test_parse_skill_output_various_commentary_headers_stripped():
    """All known commentary-header variants should be stripped from Quick-mode output."""
    variants = [
        ("**What changed:** removed pivot", "**What changed:**"),
        ("**Summary:** short", "**Summary:**"),
        ("**Notes:** some notes here", "**Notes:**"),
        ("**Rationale:** because reasons", "**Rationale:**"),
        ("concept-noun check: none found", "concept-noun check"),
        ("fabrication check: ok", "fabrication check"),
    ]
    rewrite_body = "Der Rewrite steht hier.\n"
    for commentary, label in variants:
        text = rewrite_body + "\n" + commentary
        parsed = parse_skill_output(text)
        assert label.lower() not in parsed["final"].lower(), (
            f"Commentary header '{label}' leaked into final for variant: {commentary!r}"
        )
        assert "Der Rewrite steht hier" in parsed["final"], (
            f"Rewrite body missing for variant: {commentary!r}"
        )


def test_parse_skill_output_blockquoted_rewrite_strips_commentary():
    """Blockquote-fallback path must also strip trailing commentary."""
    messy = (
        "**Pre-flight:** 3 Tier-1 tells → AI-heavy.\n\n"
        "> The rewrite goes here.\n\n"
        "**changes:** removed 'pivotal'\n"
    )
    parsed = parse_skill_output(messy)
    assert "changes:" not in parsed["final"].lower()
    assert "The rewrite goes here" in parsed["final"]


# ---------------------------------------------------------------------------
# Bug 2 — _PACK_FILES must include DE packs
# ---------------------------------------------------------------------------

def test_pack_files_includes_de_md():
    """_PACK_FILES must include patterns/de.md so stale DE packs are caught."""
    from evals.scripts._shared import _PACK_FILES
    flat = [item for tup in _PACK_FILES for item in tup]
    assert "patterns/de.md" in flat, f"patterns/de.md missing from _PACK_FILES: {flat}"


def test_pack_files_includes_de_overrides():
    """_PACK_FILES must include domains/de_overrides.md so stale DE overrides are caught."""
    from evals.scripts._shared import _PACK_FILES
    flat = [item for tup in _PACK_FILES for item in tup]
    assert "domains/de_overrides.md" in flat, (
        f"domains/de_overrides.md missing from _PACK_FILES: {flat}"
    )


def test_verify_skill_install_detects_stale_de_pack(tmp_path, monkeypatch):
    """verify_skill_install must raise SkillInstallMismatch when de.md differs."""
    import hashlib
    from evals.scripts._shared import verify_skill_install, SkillInstallMismatch, _DEFAULT_INSTALL_ROOT

    # Build a fake install root that mirrors the expected layout
    install_root = tmp_path / "install"
    repo_root = tmp_path / "repo"
    for d in [
        install_root / "patterns",
        install_root / "domains",
        repo_root / "patterns",
        repo_root / "domains",
    ]:
        d.mkdir(parents=True)

    # Matching SKILL.md
    skill_content = b"SKILL content v3.5.0\n"
    (install_root / "SKILL.md").write_bytes(skill_content)
    (repo_root / "SKILL.md").write_bytes(skill_content)

    # Matching EN packs
    for rel in ("patterns/_universal.md", "patterns/en.md", "domains/en_overrides.md"):
        content = f"# {rel}\n".encode()
        (install_root / rel).write_bytes(content)
        (repo_root / rel).write_bytes(content)

    # Matching de_overrides.md but MISMATCHED de.md
    (install_root / "domains" / "de_overrides.md").write_bytes(b"# de overrides\n")
    (repo_root / "domains" / "de_overrides.md").write_bytes(b"# de overrides\n")
    (repo_root / "patterns" / "de.md").write_bytes(b"# de patterns v2\n")
    (install_root / "patterns" / "de.md").write_bytes(b"# de patterns v1 (stale)\n")

    # Monkeypatch the module-level _DEFAULT_INSTALL_ROOT so the pack check runs
    monkeypatch.setattr("evals.scripts._shared._DEFAULT_INSTALL_ROOT", install_root)

    with pytest.raises(SkillInstallMismatch, match="de.md"):
        verify_skill_install(
            repo_skill_path=repo_root / "SKILL.md",
            installed_skill_path=install_root / "SKILL.md",
        )


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
    # Simulate a rewrite that removed all three expected_changes (all 5 runs identical)
    mock_run_skill.return_value = {
        "domain": "casual",
        "preflight": "",
        "draft": "The report flags an important shift.",
        "final": "The report flags an important shift.",
    }

    score = score_case(case, model="sonnet", runs=5)
    assert score["detected"] is True
    # multi-run: terms_present/terms_removed are now medians across runs
    assert score["terms_present"] == 3
    assert score["terms_removed"] == 3


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
    score = score_case(case, model="sonnet", runs=5)
    assert score["detected"] is False  # only 1 of 2 removed (majority across runs)
    assert score["terms_present"] == 2
    assert score["terms_removed"] == 1


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


# ---------------------------------------------------------------------------
# CHANGE 1 — force_full option in _build_humanizer_prompt and run_skill
# ---------------------------------------------------------------------------

def test_build_humanizer_prompt_force_full_false_unchanged():
    """force_full=False (default) produces byte-identical output to previous behaviour."""
    from evals.scripts._shared import _build_humanizer_prompt

    result_no_flag = _build_humanizer_prompt("Hello world.", lang="en", mode="full", domain="casual", samples_dir=None)
    result_false = _build_humanizer_prompt("Hello world.", lang="en", mode="full", domain="casual", samples_dir=None, force_full=False)
    assert result_no_flag == result_false


def test_build_humanizer_prompt_force_full_contains_override_directive():
    """force_full=True appends the override directive on its own line before the text."""
    from evals.scripts._shared import _build_humanizer_prompt

    result = _build_humanizer_prompt("Hello world.", lang="en", mode="full", domain="casual", samples_dir=None, force_full=True)
    assert "(Run a full pass" in result
    assert "do NOT switch to Quick mode" in result
    assert "explicit user override" in result


def test_build_humanizer_prompt_force_full_directive_before_text():
    """The override directive and 'Text to humanize:' label appear between header and body (V1)."""
    from evals.scripts._shared import _build_humanizer_prompt

    text = "Some AI-generated prose here."
    result = _build_humanizer_prompt(text, lang="en", mode="full", domain=None, samples_dir=None, force_full=True)
    directive_pos = result.index("do NOT switch to Quick mode")
    label_pos = result.index("Text to humanize:")
    text_pos = result.index(text)
    header_pos = result.index("/humanizer")
    assert header_pos < directive_pos < label_pos < text_pos, (
        "Expected: header ... directive ... 'Text to humanize:' label ... text body"
    )
    # V1: the label must be present in force_full=True prompts
    assert "Text to humanize:" in result


def test_build_humanizer_prompt_force_full_false_has_no_directive():
    """force_full=False must not insert the override directive anywhere in the prompt."""
    from evals.scripts._shared import _build_humanizer_prompt

    result = _build_humanizer_prompt("Some text.", lang="en", mode="full", domain=None, samples_dir=None, force_full=False)
    assert "do NOT switch to Quick mode" not in result
    assert "explicit user override" not in result


@patch("subprocess.run")
def test_run_skill_force_full_true_injects_directive(mock_run):
    """run_skill(force_full=True) passes the override directive into the prompt."""
    from evals.scripts._shared import run_skill

    mock_run.return_value = MagicMock(
        stdout="**Final rewrite:**\n> Cleaned.\n",
        stderr="",
        returncode=0,
    )
    run_skill("Some text.", lang="en", mode="full", domain="casual", force_full=True)
    cmd = mock_run.call_args[0][0]
    full_prompt = cmd[cmd.index("-p") + 1]
    assert "do NOT switch to Quick mode" in full_prompt


@patch("subprocess.run")
def test_run_skill_force_full_false_no_directive(mock_run):
    """run_skill(force_full=False) (default) does NOT inject the override directive."""
    from evals.scripts._shared import run_skill

    mock_run.return_value = MagicMock(
        stdout="**Final rewrite:**\n> Cleaned.\n",
        stderr="",
        returncode=0,
    )
    run_skill("Some text.", lang="en", mode="full", domain="casual", force_full=False)
    cmd = mock_run.call_args[0][0]
    full_prompt = cmd[cmd.index("-p") + 1]
    assert "do NOT switch to Quick mode" not in full_prompt


def test_aggregate_runs_continuous_median_verdict():
    from evals.scripts._shared import aggregate_runs
    r = aggregate_runs([0.02, 0.05, 0.08, 0.40, 0.50], threshold=0.10,
                       kind="continuous", n_target=5)
    assert r["verdict"] is True
    assert r["median"] == 0.08
    assert r["fraction"] is None
    assert r["passed_fraction"] == "3/5"
    assert r["inconclusive"] is False
    assert r["flaky"] is True


def test_aggregate_runs_continuous_passed_fraction_can_disagree_with_verdict():
    from evals.scripts._shared import aggregate_runs
    r = aggregate_runs([0.05, 0.06, 0.11, 0.12, 0.13], threshold=0.10,
                       kind="continuous", n_target=5)
    assert r["verdict"] is False
    assert r["median"] == 0.11
    assert r["passed_fraction"] == "2/5"


def test_aggregate_runs_continuous_not_flaky_when_all_one_side():
    from evals.scripts._shared import aggregate_runs
    r = aggregate_runs([0.02, 0.03, 0.04, 0.05, 0.06], threshold=0.10,
                       kind="continuous", n_target=5)
    assert r["flaky"] is False
    assert r["verdict"] is True


def test_aggregate_runs_binary_majority_and_fraction():
    from evals.scripts._shared import aggregate_runs
    r = aggregate_runs([1.0, 1.0, 1.0, 0.0, 0.0], kind="binary", n_target=5)
    assert r["verdict"] is True
    assert r["fraction"] == 0.6
    assert r["median"] is None
    assert r["passed_fraction"] == "3/5"
    assert r["flaky"] is True


def test_aggregate_runs_binary_even_split_is_majority_not_fraction_mean():
    """2/4 detected: majority (k>=ceil(4/2)=2) is True even though fraction is 0.5.
    Pins that verdict is majority, not fraction>0.5 (which would be False)."""
    from evals.scripts._shared import aggregate_runs
    r = aggregate_runs([1.0, 1.0, 0.0, 0.0], kind="binary", n_target=4)
    assert r["verdict"] is True
    assert r["fraction"] == 0.5
    assert r["flaky"] is True


def test_aggregate_runs_binary_unanimous_not_flaky():
    from evals.scripts._shared import aggregate_runs
    r = aggregate_runs([1.0, 1.0, 1.0, 1.0, 1.0], kind="binary", n_target=5)
    assert r["verdict"] is True
    assert r["fraction"] == 1.0
    assert r["flaky"] is False


def test_aggregate_runs_inconclusive_when_too_few_succeed():
    from evals.scripts._shared import aggregate_runs
    r = aggregate_runs([0.02, 0.05, None, None, None], threshold=0.10,
                       kind="continuous", n_target=5)
    assert r["inconclusive"] is True
    assert r["verdict"] is None
    assert r["flaky"] is False
    assert r["n_success"] == 2
    assert r["n_fail"] == 3


def test_aggregate_runs_all_failed_is_inconclusive():
    from evals.scripts._shared import aggregate_runs
    r = aggregate_runs([None, None, None, None, None], threshold=0.10,
                       kind="continuous", n_target=5)
    assert r["inconclusive"] is True
    assert r["verdict"] is None
    assert r["median"] is None
    assert r["passed_fraction"] == "0/0"


def test_aggregate_runs_verdict_boundary_median_equals_threshold():
    """median == threshold must PASS (verdict uses <=, not <)."""
    from evals.scripts._shared import aggregate_runs
    r = aggregate_runs([0.10, 0.10, 0.10], threshold=0.10, kind="continuous", n_target=5)
    assert r["verdict"] is True       # 0.10 <= 0.10
    assert r["flaky"] is False        # all equal -> no straddle


def test_aggregate_runs_inconclusive_boundary_exactly_half():
    """n_success == ceil(n_target/2) is NOT inconclusive (uses <, not <=)."""
    from evals.scripts._shared import aggregate_runs
    r = aggregate_runs([0.02, 0.03, 0.04, None, None], threshold=0.10,
                       kind="continuous", n_target=5)
    assert r["n_success"] == 3        # ceil(5/2) == 3
    assert r["inconclusive"] is False
    assert r["verdict"] is True


def test_is_refusal_flags_real_refusal_stubs():
    from evals.scripts._shared import is_refusal
    assert is_refusal("no text provided. what should I humanize?") is True
    assert is_refusal("Paste the text to humanize and I'll run a full casual pass.") is True
    assert is_refusal("No text to humanize was provided.") is True
    assert is_refusal("") is True
    assert is_refusal("   \n  ") is True


def test_is_refusal_does_not_flag_aggressive_rewrite():
    """Load-bearing (round-1 BLOCKER): a legit heavy rewrite has NO refusal phrase."""
    from evals.scripts._shared import is_refusal
    assert is_refusal("It works better.") is False
    assert is_refusal("This approach simply works better than before.") is False
    # "can't help" appears in legit prose and is NOT a refusal phrase
    assert is_refusal("You can't help noticing the difference.") is False


def test_is_refusal_passes_real_short_rewrites():
    from evals.scripts._shared import is_refusal
    # real SP3b conversion rewrites (skill actually rewrote)
    assert is_refusal("Gallery 825 is LAAA's exhibition space; it has four rooms.") is False
    assert is_refusal("The goal is to write clearly.") is False
    assert is_refusal("The report, which covered three continents, concluded demand had shifted.") is False


def test_is_refusal_phrases_are_refusal_anchored_not_bare():
    """Anchored phrases ('no text provided', not bare 'no text') so a legit rewrite
    that merely mentions text/forms is NOT mis-flagged (Skeptic round-3)."""
    from evals.scripts._shared import is_refusal
    assert is_refusal("There's no text-message etiquette anymore.") is False
    assert is_refusal("Paste the text into the box and hit submit.") is False
    assert is_refusal("What text editor do you use?") is False
    assert is_refusal("We provide the text editor for free.") is False
    # but the full refusal stubs still match
    assert is_refusal("No text to humanize was provided. Paste the text you want processed.") is True
    assert is_refusal("What text do you want humanized?") is True


# ---------------------------------------------------------------------------
# Phase 1, Task 2 — integration: fence cut composes correctly with extraction
# ---------------------------------------------------------------------------

def test_parse_fullmode_pre_rewrite_audit_not_truncated_trailing_fence_cut():
    resp = (
        "**Final AI audit findings:**\n- em dash count: 0\n- concept coverage: 7/8\n\n"
        "**Final rewrite:**\n"
        "Der Brief ist fertig und sachlich.\n\n"
        "<!--HUMANIZER-AUDIT-->\nText unverändert. Authentisches DACH-Anschreiben."
    )
    assert parse_skill_output(resp)["final"] == "Der Brief ist fertig und sachlich."

def test_parse_quick_direct_trailing_fence_cut():
    resp = "Just the clean rewrite.\n\n<!--HUMANIZER-AUDIT-->\nNo edits made. human-authored."
    assert parse_skill_output(resp)["final"] == "Just the clean rewrite."

def test_parse_no_fence_unchanged():
    resp = "**Final rewrite:**\nA rewrite with no fence and no commentary."
    assert parse_skill_output(resp)["final"] == "A rewrite with no fence and no commentary."
