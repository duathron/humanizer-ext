"""Tests for evals/scripts/run_e2e_eval.py — pure helper + aggregation.

Does NOT invoke the live `claude` CLI or Anthropic API.
Monkeypatches run_skill and _call_judge to return canned scores.
"""
from __future__ import annotations

import statistics
from unittest.mock import patch as _patch

import pytest

# ---------------------------------------------------------------------------
# FIX 1 — _looks_like_failed_rewrite: leaked changelog forms + prose safety
# ---------------------------------------------------------------------------

from evals.scripts.run_e2e_eval import _looks_like_failed_rewrite


class TestLooksLikeFailedRewrite:
    """Guard must catch every changelog form; must NOT catch genuine prose."""

    # --- TRUE cases (should be caught) ---

    def test_empty_string_is_caught(self):
        assert _looks_like_failed_rewrite("") is True

    def test_whitespace_only_is_caught(self):
        assert _looks_like_failed_rewrite("   \n\t  ") is True

    def test_bold_english_changelog_header_still_caught(self):
        """Original behaviour must be preserved."""
        assert _looks_like_failed_rewrite("**Changes made:** removed X\n**Summary:**") is True

    def test_bold_german_changelog_header_with_leading_word_caught(self):
        """Signal F: '**Wesentliche Änderungen:**' — a leading adjective inside the
        bold span slipped past Signal A and leaked a meaning~2 score (academic case)."""
        text = '**Wesentliche Änderungen:** Alle drei "Im Rahmen"-Rahmungen (#100) gestrichen; ~42 % kürzer.'
        assert _looks_like_failed_rewrite(text) is True
        assert _looks_like_failed_rewrite("**Änderungen:** entfernt") is True

    def test_prose_mentioning_aenderungen_not_caught(self):
        """Bold wrapper required — ordinary prose mentioning 'Änderungen' must pass."""
        text = "Diese Studie evaluiert die **Ergebnisse**; sie zeigt wichtige Änderungen im Verhalten."
        assert _looks_like_failed_rewrite(text) is False

    # --- Leaking forms (all three from the bug report) ---

    def test_rule_id_changelog_with_arrows_caught(self):
        """Rule-ID + arrow form: '#7 ganzheitlich → entfernt\\n#4 nahtlos → entfernt'"""
        text = "#7 ganzheitlich → entfernt\n#4 nahtlos → entfernt"
        assert _looks_like_failed_rewrite(text) is True

    def test_transformationen_header_changelog_caught(self):
        """Explicit changelog header 'Transformationen:' on its own line."""
        text = "Transformationen:\n- removed X\n- removed Y"
        assert _looks_like_failed_rewrite(text) is True

    def test_entfernt_colon_header_caught(self):
        """Line-anchored 'entfernt: ...' changelog header."""
        text = "entfernt: umfassend, nahtlos"
        assert _looks_like_failed_rewrite(text) is True

    def test_two_arrows_ascii_caught(self):
        """Two ASCII arrow -> occurrences (changelog style)."""
        text = "word1 -> word2\nword3 -> word4"
        assert _looks_like_failed_rewrite(text) is True

    def test_two_arrows_unicode_caught(self):
        """Two Unicode arrow → occurrences."""
        text = "ganzheitlich → passend\nnahtlos → fließend"
        assert _looks_like_failed_rewrite(text) is True

    def test_rule_id_lines_two_or_more_caught(self):
        """Two lines starting with '#N' rule-IDs → changelog."""
        text = "#12 something\n#7 something else"
        assert _looks_like_failed_rewrite(text) is True

    def test_pattern_hash_rule_id_caught(self):
        """'pattern #7' prefix on multiple lines."""
        text = "pattern #7 removed\npattern #4 removed"
        assert _looks_like_failed_rewrite(text) is True

    def test_changes_colon_header_caught(self):
        """Line-anchored 'changes:' header."""
        text = "changes:\n- removed X"
        assert _looks_like_failed_rewrite(text) is True

    def test_applied_colon_header_caught(self):
        """Line-anchored 'applied:' header."""
        text = "applied: pattern 3, pattern 7"
        assert _looks_like_failed_rewrite(text) is True

    # --- FALSE cases (genuine prose must NOT be caught) ---

    def test_genuine_german_prose_with_mid_sentence_entfernt_not_caught(self):
        """'entfernt' appearing mid-sentence in normal German prose must pass."""
        text = (
            "Das Tool entfernt transiente Fehler und nutzt eine Backoff-Strategie. "
            "Es wurde sorgfältig entwickelt und bietet eine robuste Fehlerbehandlung."
        )
        assert _looks_like_failed_rewrite(text) is False

    def test_normal_multi_sentence_rewrite_not_caught(self):
        """A normal English rewrite with no changelog markers must pass."""
        text = (
            "The system processes requests in parallel, which cuts latency by half. "
            "Engineers removed the legacy queue and replaced it with an event bus. "
            "This change makes the architecture easier to maintain."
        )
        assert _looks_like_failed_rewrite(text) is False

    def test_single_arrow_in_prose_not_caught(self):
        """A single arrow (one reference) in prose does not trigger the guard."""
        text = "The process moves from state A → state B smoothly without interruption."
        assert _looks_like_failed_rewrite(text) is False

    def test_german_prose_with_one_rule_id_mention_not_caught(self):
        """A single '#7' mention in prose (not line-starting) is not a changelog."""
        text = (
            "Gemäß Regel #7 der Stilrichtlinien sollte der Text klar und präzise sein. "
            "Diese Anforderung gilt für alle Dokumente."
        )
        assert _looks_like_failed_rewrite(text) is False


# ---------------------------------------------------------------------------
# FIX 2 — score_case persists rewrite in each run's scores dict
# ---------------------------------------------------------------------------

E2E_MODULE = "evals.scripts.run_e2e_eval"


def _make_skill_output(final_text: str) -> dict:
    return {"final": final_text, "draft": final_text}


def _make_judge_scores(human_ness: int, meaning: int, length: int) -> dict:
    return {
        "human_ness": human_ness,
        "meaning": meaning,
        "length": length,
        "rationale": {"human_ness": "ok", "meaning": "ok", "length": "ok"},
    }


@_patch(f"{E2E_MODULE}._call_judge")
@_patch(f"{E2E_MODULE}.run_skill")
def test_score_case_persists_rewrite_in_run_results(mock_run_skill, mock_call_judge):
    """Each run's scores dict must contain 'rewrite' key with first 1500 chars."""
    from evals.scripts.run_e2e_eval import score_case

    rewrite_text = "This is the actual rewrite output from the skill."
    mock_run_skill.return_value = _make_skill_output(rewrite_text)
    mock_call_judge.return_value = _make_judge_scores(8, 9, 8)

    case = {
        "id": "e2e_en_casual_01",
        "input": "This is an AI-generated text that needs humanizing.",
        "domain": "casual",
        "lang": "en",
    }
    result = score_case(case, runs=2, model="sonnet", judge_model="sonnet")

    assert len(result["runs"]) == 2
    for run in result["runs"]:
        assert "rewrite" in run, "rewrite key missing from run result"
        assert run["rewrite"] == rewrite_text[:1500]


@_patch(f"{E2E_MODULE}._call_judge")
@_patch(f"{E2E_MODULE}.run_skill")
def test_score_case_rewrite_truncated_to_1500(mock_run_skill, mock_call_judge):
    """Rewrite longer than 1500 chars must be truncated to exactly 1500."""
    from evals.scripts.run_e2e_eval import score_case

    long_rewrite = "x" * 3000
    mock_run_skill.return_value = _make_skill_output(long_rewrite)
    mock_call_judge.return_value = _make_judge_scores(8, 9, 8)

    case = {
        "id": "e2e_en_casual_02",
        "input": "Some AI text.",
        "domain": "casual",
        "lang": "en",
    }
    result = score_case(case, runs=1, model="sonnet", judge_model="sonnet")

    assert result["runs"][0]["rewrite"] == long_rewrite[:1500]
    assert len(result["runs"][0]["rewrite"]) == 1500


# ---------------------------------------------------------------------------
# FIX 3 — DEFAULT_THRESHOLDS["meaning"] == 8.0
# ---------------------------------------------------------------------------


def test_default_meaning_threshold_is_8():
    """Acceptance criterion is meaning >= 8.0 (docs/plans/2026-05-27-phase-2-de-pack.md)."""
    from evals.scripts.run_e2e_eval import DEFAULT_THRESHOLDS

    assert DEFAULT_THRESHOLDS["meaning"] == 8.0, (
        f"meaning threshold must be 8.0 (documented acceptance bar), got {DEFAULT_THRESHOLDS['meaning']}"
    )


def test_other_thresholds_unchanged():
    """human_ness and length thresholds must not change."""
    from evals.scripts.run_e2e_eval import DEFAULT_THRESHOLDS

    assert DEFAULT_THRESHOLDS["human_ness"] == 7.5
    assert DEFAULT_THRESHOLDS["length"] == 7.0


# ---------------------------------------------------------------------------
# FIX 4 — median present + correct; outlier doesn't corrupt median while mean is
# ---------------------------------------------------------------------------


@_patch(f"{E2E_MODULE}._call_judge")
@_patch(f"{E2E_MODULE}.run_skill")
def test_score_case_returns_median_block(mock_run_skill, mock_call_judge):
    """score_case must return a 'median' dict parallel to 'mean'."""
    from evals.scripts.run_e2e_eval import score_case

    mock_run_skill.return_value = _make_skill_output("Rewritten text here.")
    mock_call_judge.return_value = _make_judge_scores(8, 9, 8)

    case = {
        "id": "e2e_en_casual_03",
        "input": "Some AI text.",
        "domain": "casual",
        "lang": "en",
    }
    result = score_case(case, runs=3, model="sonnet", judge_model="sonnet")

    assert "median" in result, "median key missing from score_case result"
    assert set(result["median"].keys()) == {"human_ness", "meaning", "length"}


@_patch(f"{E2E_MODULE}._call_judge")
@_patch(f"{E2E_MODULE}.run_skill")
def test_score_case_median_ignores_outlier_while_mean_does_not(mock_run_skill, mock_call_judge):
    """With 3 runs [8, 9, 1] the median (8) is stable; mean (6.0) is pulled by outlier.

    This verifies median is computed correctly and diverges from mean under noise.
    """
    from evals.scripts.run_e2e_eval import score_case

    # Return different scores per call
    call_count = {"n": 0}

    def judge_side_effect(**kwargs):
        call_count["n"] += 1
        if call_count["n"] == 3:
            # Third run: outlier — very low meaning score
            return _make_judge_scores(1, 1, 1)
        return _make_judge_scores(8, 9, 8)

    mock_run_skill.return_value = _make_skill_output("Good rewrite text.")
    mock_call_judge.side_effect = judge_side_effect

    case = {
        "id": "e2e_en_casual_04",
        "input": "Some AI text.",
        "domain": "casual",
        "lang": "en",
    }
    result = score_case(case, runs=3, model="sonnet", judge_model="sonnet")

    # Runs: [8,9,8], [8,9,8], [1,1,1]
    # Mean human_ness = (8+8+1)/3 = 5.667; median = 8
    assert result["mean"]["human_ness"] == pytest.approx(5.667, abs=0.001)
    assert result["median"]["human_ness"] == pytest.approx(8.0, abs=0.001)

    # Mean meaning = (9+9+1)/3 = 6.333; median = 9
    assert result["mean"]["meaning"] == pytest.approx(6.333, abs=0.001)
    assert result["median"]["meaning"] == pytest.approx(9.0, abs=0.001)


@_patch(f"{E2E_MODULE}._call_judge")
@_patch(f"{E2E_MODULE}.run_skill")
def test_score_case_mean_still_present(mock_run_skill, mock_call_judge):
    """Adding median must not remove 'mean' from the result."""
    from evals.scripts.run_e2e_eval import score_case

    mock_run_skill.return_value = _make_skill_output("Some rewrite.")
    mock_call_judge.return_value = _make_judge_scores(8, 9, 8)

    case = {
        "id": "e2e_en_casual_05",
        "input": "AI text.",
        "domain": "casual",
        "lang": "en",
    }
    result = score_case(case, runs=2, model="sonnet", judge_model="sonnet")

    assert "mean" in result
    assert "stddev" in result
    assert "median" in result


# ---------------------------------------------------------------------------
# FIX 4 — run() summary includes median-based below_threshold check
# ---------------------------------------------------------------------------


@_patch(f"{E2E_MODULE}.score_case")
@_patch(f"{E2E_MODULE}.verify_skill_install")
def test_run_summary_includes_below_threshold_by_dimension_median(
    mock_verify, mock_score_case, tmp_path
):
    """run() summary must include 'below_threshold_by_dimension_median' alongside the mean-based one."""
    import json
    from evals.scripts.run_e2e_eval import run

    # Set up corpus dir with one case.
    # run() resolves as REPO_ROOT/evals/corpus/{lang}/e2e/ — match that structure.
    corpus_dir = tmp_path / "evals" / "corpus" / "en" / "e2e"
    corpus_dir.mkdir(parents=True)
    case_data = {
        "id": "e2e_en_casual_01",
        "input": "Some AI text to rewrite.",
        "domain": "casual",
        "lang": "en",
    }
    (corpus_dir / "e2e_en_casual_01.json").write_text(
        json.dumps(case_data), encoding="utf-8"
    )

    # Score with an outlier-skewed mean but solid median
    mock_score_case.return_value = {
        "case_id": "e2e_en_casual_01",
        "domain": "casual",
        "runs": [
            {"human_ness": 8, "meaning": 9, "length": 8, "rewrite": "Good text.", "rewrite_length_words": 2},
            {"human_ness": 8, "meaning": 9, "length": 8, "rewrite": "Good text.", "rewrite_length_words": 2},
            {"human_ness": 1, "meaning": 1, "length": 1, "rewrite": "Bad.", "rewrite_length_words": 1},
        ],
        "mean": {"human_ness": 5.667, "meaning": 6.333, "length": 5.667},
        "stddev": {"human_ness": 4.041, "meaning": 4.619, "length": 4.041},
        "median": {"human_ness": 8.0, "meaning": 9.0, "length": 8.0},
    }

    # Patch REPO_ROOT to point at tmp_path so corpus/partial dirs resolve correctly
    import evals.scripts.run_e2e_eval as mod
    original_root = mod.REPO_ROOT
    mod.REPO_ROOT = tmp_path
    partial_dir = tmp_path / "evals" / "reports" / "_partial"
    partial_dir.mkdir(parents=True)

    try:
        result = run(lang="en", runs=3, model="sonnet", judge_model="sonnet")
    finally:
        mod.REPO_ROOT = original_root

    summary = result["summary"]
    assert "below_threshold_by_dimension_median" in summary, (
        "below_threshold_by_dimension_median missing from run() summary"
    )
    # Mean is below threshold (5.667 < 7.5), but median is fine (8.0 >= 7.5)
    assert summary["below_threshold_by_dimension"]["human_ness"] == 1  # mean fails
    assert summary["below_threshold_by_dimension_median"]["human_ness"] == 0  # median passes


# ---------------------------------------------------------------------------
# SP1 Task 1 — changelog_first_attempt_rate metric
# ---------------------------------------------------------------------------


def test_first_attempt_changelog_recorded(monkeypatch):
    """score_case records whether the FIRST skill attempt was a change-log."""
    import evals.scripts.run_e2e_eval as e2e
    outs = iter([
        {"final": "**Wesentliche Änderungen:** #7 entfernt"},  # changelog -> retried
        {"final": "Eine saubere, menschliche Umschreibung des Textes."},  # clean
    ])
    monkeypatch.setattr(e2e, "run_skill", lambda *a, **k: next(outs))
    monkeypatch.setattr(e2e, "_call_judge",
                        lambda **k: {"human_ness": 8, "meaning": 8, "length": 8})
    res = e2e.score_case({"id": "t", "input": "x", "domain": "casual"}, runs=1)
    assert res["runs"][0]["first_attempt_changelog"] is True


def test_first_attempt_clean_not_flagged(monkeypatch):
    import evals.scripts.run_e2e_eval as e2e
    monkeypatch.setattr(e2e, "run_skill",
                        lambda *a, **k: {"final": "Sauberer menschlicher Text."})
    monkeypatch.setattr(e2e, "_call_judge",
                        lambda **k: {"human_ness": 8, "meaning": 8, "length": 8})
    res = e2e.score_case({"id": "t", "input": "x", "domain": "casual"}, runs=1)
    assert res["runs"][0]["first_attempt_changelog"] is False


def test_changelog_rate_aggregated_in_run(monkeypatch, tmp_path):
    """run() reports changelog_first_attempt_rate across all scored runs.
    run() globs REPO_ROOT/evals/corpus/<lang>/e2e/*.json and returns the report
    dict directly (no corpus-loader, no write_report)."""
    import json
    import evals.scripts.run_e2e_eval as e2e
    corpus_dir = tmp_path / "evals" / "corpus" / "de" / "e2e"
    corpus_dir.mkdir(parents=True)
    (corpus_dir / "a.json").write_text(json.dumps(
        {"id": "a", "input": "x", "domain": "casual", "lang": "de"}), encoding="utf-8")
    (corpus_dir / "b.json").write_text(json.dumps(
        {"id": "b", "input": "y", "domain": "casual", "lang": "de"}), encoding="utf-8")
    outs = iter([
        {"final": "**Changes:** x"},             # a, attempt 1 -> flagged, retried
        {"final": "saubere Umschreibung"},        # a, attempt 2 -> clean
        {"final": "zweite saubere Umschreibung"}, # b, attempt 1 -> clean
    ])
    monkeypatch.setattr(e2e, "run_skill", lambda *a, **k: next(outs))
    monkeypatch.setattr(e2e, "_call_judge",
                        lambda **k: {"human_ness": 8, "meaning": 8, "length": 8})
    monkeypatch.setattr(e2e, "verify_skill_install", lambda: None)
    monkeypatch.setattr(e2e, "REPO_ROOT", tmp_path)
    report = e2e.run(lang="de", runs=1)
    assert report["summary"]["changelog_first_attempt_rate"] == 0.5


def test_partial_persists_first_attempt_changelog(monkeypatch, tmp_path):
    """The per-case partial written to disk must carry first_attempt_changelog."""
    import json
    import evals.scripts.run_e2e_eval as e2e
    corpus_dir = tmp_path / "evals" / "corpus" / "de" / "e2e"
    corpus_dir.mkdir(parents=True)
    (corpus_dir / "a.json").write_text(json.dumps(
        {"id": "a", "input": "x", "domain": "casual", "lang": "de"}), encoding="utf-8")
    monkeypatch.setattr(e2e, "run_skill",
                        lambda *a, **k: {"final": "saubere Umschreibung"})
    monkeypatch.setattr(e2e, "_call_judge",
                        lambda **k: {"human_ness": 8, "meaning": 8, "length": 8})
    monkeypatch.setattr(e2e, "verify_skill_install", lambda: None)
    monkeypatch.setattr(e2e, "REPO_ROOT", tmp_path)
    e2e.run(lang="de", runs=1)
    partial = json.loads((tmp_path / "evals" / "reports" / "_partial"
                          / "e2e_de_a.json").read_text(encoding="utf-8"))
    assert partial["runs"][0]["first_attempt_changelog"] is False
