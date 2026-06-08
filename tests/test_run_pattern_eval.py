"""Tests for evals/scripts/run_pattern_eval.py — error-isolation behaviour.

Does NOT invoke the live `claude` CLI. Monkeypatches `score_case` to raise
on specific cases so we can verify the loop continues / breaks correctly.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from evals.scripts._shared import Case, SkillRunError
from evals.scripts.run_pattern_eval import run

PATTERN_MODULE = "evals.scripts.run_pattern_eval"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_pattern_file(corpus_dir: Path, pattern_id: int, cases: list[dict]) -> None:
    """Write a minimal pattern_<id>.json corpus file."""
    corpus_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "pattern_id": pattern_id,
        "pattern_name": f"Test pattern {pattern_id}",
        "lang": "en",
        "cases": cases,
    }
    (corpus_dir / f"pattern_{pattern_id:02d}.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )


def _case(case_id: str, *, pattern_id: int = 1) -> dict:
    """Minimal scorable case dict."""
    return {
        "id": case_id,
        "input": f"This is a test input for {case_id}. It showcases a pattern.",
        "expected_changes": ["showcases"],
        "expected_unchanged": [],
        "domain": "casual",
        "source": "",
    }


# ---------------------------------------------------------------------------
# Per-item timeout → loop continues, remaining items processed
# ---------------------------------------------------------------------------


def test_pattern_run_per_item_timeout_continues_and_records_failure(tmp_path, monkeypatch):
    """Case-level fallback: a score_case() that itself raises TimeoutExpired (e.g. a bug or
    a monkeypatched test) still lets the loop continue and lands in summary['failed'].
    Under SP3a the realistic per-run timeout path is covered by
    test_pattern_score_case_nonsession_failure_becomes_none_run; this test covers the
    defensive case-level except that remains in run() for propagated session-limit and
    other unexpected raises from score_case itself."""
    corpus_dir = tmp_path / "patterns"
    _write_pattern_file(
        corpus_dir,
        pattern_id=1,
        cases=[_case("case_a"), _case("case_b"), _case("case_c")],
    )

    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    monkeypatch.setattr(f"{PATTERN_MODULE}.REPO_ROOT", tmp_path)

    call_count = {"n": 0}

    def fake_score_case(case: Case, *, model: str = "sonnet", force_full: bool = False, **_) -> dict:
        call_count["n"] += 1
        if case.id == "case_b":
            raise subprocess.TimeoutExpired(cmd="claude", timeout=180)
        return {
            "case_id": case.id,
            "pattern_id": case.metadata.get("pattern_id"),
            "detected": True,
            "status": "scored",
            "removed_terms": ["showcases"],
            "retained_terms": [],
            "rewrite_preview": "rewritten",
        }

    monkeypatch.setattr(f"{PATTERN_MODULE}.score_case", fake_score_case)
    monkeypatch.setattr(f"{PATTERN_MODULE}.verify_skill_install", lambda: None)

    result = run(
        lang="en",
        pattern=None,
        model="sonnet",
        threshold=0.85,
        force=False,
        aggregate_only=False,
        _corpus_dir_override=corpus_dir,
        _partial_dir_override=partial_dir,
    )

    summary = result["summary"]
    assert summary["total_cases"] == 2, f"expected 2 scored cases, got {summary}"
    assert len(summary["failed"]) == 1
    assert summary["failed"][0]["case_id"] == "case_b"
    assert "timeout" in summary["failed"][0]["error"].lower()
    assert summary.get("is_complete") is False


# ---------------------------------------------------------------------------
# Per-item non-session SkillRunError → loop continues
# ---------------------------------------------------------------------------


def test_pattern_run_non_session_skill_error_continues(tmp_path, monkeypatch):
    """Non-session-limit SkillRunError on case_a → case_b still processed;
    failed list has one entry."""
    corpus_dir = tmp_path / "patterns"
    _write_pattern_file(
        corpus_dir,
        pattern_id=2,
        cases=[_case("case_a", pattern_id=2), _case("case_b", pattern_id=2)],
    )

    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    monkeypatch.setattr(f"{PATTERN_MODULE}.REPO_ROOT", tmp_path)

    def fake_score_case(case: Case, *, model: str = "sonnet", force_full: bool = False, **_) -> dict:
        if case.id == "case_a":
            raise SkillRunError("claude CLI exited 1\n  stderr: some transient error\n  stdout: (empty)")
        return {
            "case_id": case.id,
            "pattern_id": case.metadata.get("pattern_id"),
            "detected": True,
            "status": "scored",
            "removed_terms": ["showcases"],
            "retained_terms": [],
            "rewrite_preview": "rewritten",
        }

    monkeypatch.setattr(f"{PATTERN_MODULE}.score_case", fake_score_case)
    monkeypatch.setattr(f"{PATTERN_MODULE}.verify_skill_install", lambda: None)

    result = run(
        lang="en",
        pattern=None,
        model="sonnet",
        threshold=0.85,
        force=False,
        aggregate_only=False,
        _corpus_dir_override=corpus_dir,
        _partial_dir_override=partial_dir,
    )

    summary = result["summary"]
    assert summary["total_cases"] == 1
    assert len(summary["failed"]) == 1
    assert summary["failed"][0]["case_id"] == "case_a"
    assert summary.get("is_complete") is False


# ---------------------------------------------------------------------------
# Session-limit → loop breaks, subsequent items not attempted
# ---------------------------------------------------------------------------


def test_pattern_run_session_limit_breaks_loop(tmp_path, monkeypatch):
    """Session-limit error on case_b → loop breaks; case_c never called;
    session_limit_hit=True; is_complete=False."""
    corpus_dir = tmp_path / "patterns"
    _write_pattern_file(
        corpus_dir,
        pattern_id=3,
        cases=[_case("case_a", pattern_id=3), _case("case_b", pattern_id=3), _case("case_c", pattern_id=3)],
    )

    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    monkeypatch.setattr(f"{PATTERN_MODULE}.REPO_ROOT", tmp_path)

    call_count = {"n": 0}

    def fake_score_case(case: Case, *, model: str = "sonnet", force_full: bool = False, **_) -> dict:
        call_count["n"] += 1
        if case.id == "case_b":
            raise SkillRunError(
                "claude CLI exited 1\n  stderr: (empty)\n  stdout: You've hit your session limit"
            )
        return {
            "case_id": case.id,
            "pattern_id": case.metadata.get("pattern_id"),
            "detected": True,
            "status": "scored",
            "removed_terms": ["showcases"],
            "retained_terms": [],
            "rewrite_preview": "rewritten",
        }

    monkeypatch.setattr(f"{PATTERN_MODULE}.score_case", fake_score_case)
    monkeypatch.setattr(f"{PATTERN_MODULE}.verify_skill_install", lambda: None)

    result = run(
        lang="en",
        pattern=None,
        model="sonnet",
        threshold=0.85,
        force=False,
        aggregate_only=False,
        _corpus_dir_override=corpus_dir,
        _partial_dir_override=partial_dir,
    )

    summary = result["summary"]
    # Only case_a succeeded; case_b broke the loop; case_c never ran
    assert summary["total_cases"] == 1
    assert call_count["n"] == 2  # case_c never attempted
    assert summary.get("session_limit_hit") is True
    assert summary.get("is_complete") is False
    # No partial for the session-limit case
    partials = list(partial_dir.iterdir())
    assert len(partials) == 1  # only case_a's partial


# ---------------------------------------------------------------------------
# Success path — all cases succeed, clean run
# ---------------------------------------------------------------------------


def test_pattern_run_success_path_unaffected(tmp_path, monkeypatch):
    """All cases succeed → failed=[], is_complete=True, session_limit_hit=False."""
    corpus_dir = tmp_path / "patterns"
    _write_pattern_file(
        corpus_dir,
        pattern_id=4,
        cases=[_case("case_a", pattern_id=4), _case("case_b", pattern_id=4)],
    )

    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    monkeypatch.setattr(f"{PATTERN_MODULE}.REPO_ROOT", tmp_path)

    def fake_score_case(case: Case, *, model: str = "sonnet", force_full: bool = False, **_) -> dict:
        return {
            "case_id": case.id,
            "pattern_id": case.metadata.get("pattern_id"),
            "detected": True,
            "status": "scored",
            "removed_terms": ["showcases"],
            "retained_terms": [],
            "rewrite_preview": "rewritten",
        }

    monkeypatch.setattr(f"{PATTERN_MODULE}.score_case", fake_score_case)
    monkeypatch.setattr(f"{PATTERN_MODULE}.verify_skill_install", lambda: None)

    result = run(
        lang="en",
        pattern=None,
        model="sonnet",
        threshold=0.85,
        force=False,
        aggregate_only=False,
        _corpus_dir_override=corpus_dir,
        _partial_dir_override=partial_dir,
    )

    summary = result["summary"]
    assert summary["total_cases"] == 2
    assert summary.get("failed", []) == []
    assert summary.get("is_complete") is True
    assert summary.get("session_limit_hit") is False


# ---------------------------------------------------------------------------
# CHANGE 2 — force_full threading in score_case + per-term removal rate in run()
# ---------------------------------------------------------------------------

from unittest.mock import patch as _patch, call as _call


@_patch("evals.scripts.run_pattern_eval.run_skill")
def test_score_case_scorable_passes_force_full_true(mock_run_skill):
    """score_case(..., force_full=True) on a scorable case calls run_skill with force_full=True."""
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
    mock_run_skill.return_value = {
        "domain": "casual",
        "preflight": "Pre-flight: 5 Tier-1 tells per 100 words → AI-heavy. Full pass.",
        "draft": "The report flags an important shift.",
        "final": "The report flags an important shift.",
    }

    score_case(case, model="sonnet", force_full=True)

    _kwargs = mock_run_skill.call_args[1]
    assert _kwargs.get("force_full") is True


@_patch("evals.scripts.run_pattern_eval.run_skill")
def test_score_case_scorable_returns_extra_keys(mock_run_skill):
    """score_case(..., force_full=True) on a scorable case returns terms_present, terms_removed, preflight."""
    from evals.scripts.run_pattern_eval import score_case
    from evals.scripts._shared import Case

    preflight_msg = "Pre-flight: 5 Tier-1 tells per 100 words → AI-heavy. Full pass."
    case = Case(
        id="pattern_007_en_001",
        input="Additionally, the report underscores the pivotal moment.",
        expected_changes=["Additionally", "underscores", "pivotal moment"],
        expected_unchanged=[],
        domain="casual",
        metadata={"pattern_id": 7, "pattern_name": "AI vocabulary", "lang": "en"},
    )
    mock_run_skill.return_value = {
        "domain": "casual",
        "preflight": preflight_msg,
        "draft": "The report flags an important shift.",
        "final": "The report flags an important shift.",
    }

    score = score_case(case, model="sonnet", force_full=True)

    assert "terms_present" in score, "terms_present missing from scored result"
    assert "terms_removed" in score, "terms_removed missing from scored result"
    assert "preflight" in score, "preflight missing from scored result"
    assert score["terms_present"] == 3
    assert score["terms_removed"] == 3
    assert score["preflight"] == preflight_msg


@_patch("evals.scripts.run_pattern_eval.run_skill")
def test_score_case_partial_removal_terms_counts(mock_run_skill):
    """terms_present=2, terms_removed=1 when only one of two terms is removed."""
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

    score = score_case(case, model="sonnet", force_full=True)
    assert score["terms_present"] == 2
    assert score["terms_removed"] == 1


@_patch("evals.scripts.run_pattern_eval.run_skill")
def test_score_case_true_negative_does_not_force_full(mock_run_skill):
    """score_case on a true_negative case does NOT pass force_full=True to run_skill."""
    from evals.scripts.run_pattern_eval import score_case
    from evals.scripts._shared import Case

    case = Case(
        id="pattern_007_en_tn_01",
        input="This is clearly human-written text with natural flow.",
        expected_changes=[],
        expected_unchanged=[],
        domain="casual",
        metadata={"pattern_id": 7, "pattern_name": "AI vocabulary", "lang": "en"},
        true_negative=True,
    )
    mock_run_skill.return_value = {
        "domain": "casual",
        "preflight": "Pre-flight: 0 Tier-1 tells → human-authored. Quick mode.",
        "draft": "",
        "final": "This is clearly human-written text with natural flow.",
    }

    score_case(case, model="sonnet", force_full=True)

    # run_skill must be called with force_full=False (or not passed, i.e. default False)
    _kwargs = mock_run_skill.call_args[1]
    assert _kwargs.get("force_full", False) is False


def test_run_aggregates_per_term_removal_rate(tmp_path, monkeypatch):
    """run() computes per_term_removal_rate = total_removed / total_present across scored cases."""
    corpus_dir = tmp_path / "patterns"
    corpus_dir.mkdir(parents=True)
    payload = {
        "pattern_id": 1,
        "pattern_name": "Test",
        "lang": "en",
        "cases": [
            {
                "id": "case_a",
                "input": "Additionally, showcases the pivotal moment.",
                "expected_changes": ["showcases", "pivotal moment"],
                "expected_unchanged": [],
                "domain": "casual",
                "source": "",
            },
            {
                "id": "case_b",
                "input": "This showcases something.",
                "expected_changes": ["showcases"],
                "expected_unchanged": [],
                "domain": "casual",
                "source": "",
            },
        ],
    }
    (corpus_dir / "pattern_01.json").write_text(json.dumps(payload), encoding="utf-8")

    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    monkeypatch.setattr(f"{PATTERN_MODULE}.REPO_ROOT", tmp_path)

    def fake_score_case(case: Case, *, model: str = "sonnet", force_full: bool = False, **_) -> dict:
        if case.id == "case_a":
            # 1 of 2 terms removed
            return {
                "case_id": case.id,
                "pattern_id": 1,
                "detected": False,
                "status": "scored",
                "removed_terms": ["showcases"],
                "retained_terms": ["pivotal moment"],
                "rewrite_preview": "...",
                "terms_present": 2,
                "terms_removed": 1,
                "preflight": "",
            }
        else:
            # 1 of 1 term removed
            return {
                "case_id": case.id,
                "pattern_id": 1,
                "detected": True,
                "status": "scored",
                "removed_terms": ["showcases"],
                "retained_terms": [],
                "rewrite_preview": "...",
                "terms_present": 1,
                "terms_removed": 1,
                "preflight": "",
            }

    monkeypatch.setattr(f"{PATTERN_MODULE}.score_case", fake_score_case)
    monkeypatch.setattr(f"{PATTERN_MODULE}.verify_skill_install", lambda: None)

    result = run(
        lang="en",
        pattern=None,
        model="sonnet",
        threshold=0.85,
        force=False,
        aggregate_only=False,
        _corpus_dir_override=corpus_dir,
        _partial_dir_override=partial_dir,
    )

    summary = result["summary"]
    # 2 terms removed out of 3 present = 0.667
    assert "per_term_removal_rate" in summary, "per_term_removal_rate missing from summary"
    assert summary["per_term_removal_rate"] == pytest.approx(0.667, abs=0.001)
    assert summary.get("forced_full") is True


def test_run_per_term_removal_rate_old_partial_no_crash(tmp_path, monkeypatch):
    """Old partial lacking terms_present/terms_removed must not crash aggregation."""
    corpus_dir = tmp_path / "patterns"
    corpus_dir.mkdir(parents=True)
    payload = {
        "pattern_id": 5,
        "pattern_name": "Test",
        "lang": "en",
        "cases": [
            {
                "id": "case_old",
                "input": "This showcases something.",
                "expected_changes": ["showcases"],
                "expected_unchanged": [],
                "domain": "casual",
                "source": "",
            },
        ],
    }
    (corpus_dir / "pattern_05.json").write_text(json.dumps(payload), encoding="utf-8")

    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    # Write an old-style partial WITHOUT the new keys
    old_partial = {
        "case_id": "case_old",
        "pattern_id": 5,
        "detected": True,
        "status": "scored",
        "removed_terms": ["showcases"],
        "retained_terms": [],
        "rewrite_preview": "Something.",
        # NOTE: NO terms_present or terms_removed keys
    }
    (partial_dir / "pattern_en_case_old.json").write_text(
        json.dumps(old_partial), encoding="utf-8"
    )

    monkeypatch.setattr(f"{PATTERN_MODULE}.REPO_ROOT", tmp_path)
    monkeypatch.setattr(f"{PATTERN_MODULE}.verify_skill_install", lambda: None)

    # Should not crash; per_term_removal_rate should be 0.0 or absent (either is fine, no crash)
    result = run(
        lang="en",
        pattern=None,
        model="sonnet",
        threshold=0.85,
        force=False,
        aggregate_only=True,
        _corpus_dir_override=corpus_dir,
        _partial_dir_override=partial_dir,
    )
    summary = result["summary"]
    # Must not raise; per_term_removal_rate present
    assert "per_term_removal_rate" in summary


def test_run_per_term_removal_rate_divide_by_zero_guard(tmp_path, monkeypatch):
    """per_term_removal_rate is 0.0 (not a crash) when no scored cases have terms_present."""
    corpus_dir = tmp_path / "patterns"
    corpus_dir.mkdir(parents=True)
    # Use a true_negative case so no scorable cases run
    payload = {
        "pattern_id": 6,
        "pattern_name": "Test",
        "lang": "en",
        "cases": [
            {
                "id": "case_tn",
                "input": "Naturally flowing human prose.",
                "expected_changes": [],
                "expected_unchanged": [],
                "domain": "casual",
                "source": "",
                "true_negative": True,
            },
        ],
    }
    (corpus_dir / "pattern_06.json").write_text(json.dumps(payload), encoding="utf-8")

    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    monkeypatch.setattr(f"{PATTERN_MODULE}.REPO_ROOT", tmp_path)

    def fake_score_case(case: Case, *, model: str = "sonnet", force_full: bool = False, **_) -> dict:
        return {
            "case_id": case.id,
            "pattern_id": 6,
            "detected": True,
            "status": "true_negative",
            "edit_ratio": 0.0,
            "passes_true_negative": True,
            "removed_terms": [],
            "retained_terms": [],
            "rewrite_preview": "Naturally flowing human prose.",
        }

    monkeypatch.setattr(f"{PATTERN_MODULE}.score_case", fake_score_case)
    monkeypatch.setattr(f"{PATTERN_MODULE}.verify_skill_install", lambda: None)

    result = run(
        lang="en",
        pattern=None,
        model="sonnet",
        threshold=0.85,
        force=False,
        aggregate_only=False,
        _corpus_dir_override=corpus_dir,
        _partial_dir_override=partial_dir,
    )

    summary = result["summary"]
    assert "per_term_removal_rate" in summary
    assert summary["per_term_removal_rate"] == 0.0


# ---------------------------------------------------------------------------
# Task 2: multi-run score_case + run() aggregation (SP3a)
# ---------------------------------------------------------------------------


def test_pattern_run_rejects_runs_below_one():
    import evals.scripts.run_pattern_eval as pat
    with pytest.raises(ValueError, match="runs must be >= 1"):
        pat.run(lang="en", runs=0)


def test_pattern_score_case_runs_n_times_and_aggregates_detection(monkeypatch):
    """score_case runs the skill N times; detected = majority; partial carries runs[]."""
    import evals.scripts.run_pattern_eval as pat
    from evals.scripts._shared import Case
    # 3 of 5 runs remove the tell -> majority detected True, fraction 0.6
    outs = iter([
        {"final": "clean"},            # removed -> detected
        {"final": "clean"},            # removed
        {"final": "clean"},            # removed
        {"final": "still aiword here"},# retained -> not detected
        {"final": "still aiword here"},# retained
    ])
    monkeypatch.setattr(pat, "run_skill", lambda *a, **k: next(outs))
    case = Case(id="p1_en_001", input="aiword here", expected_changes=["aiword"],
                domain="casual", true_negative=False, expected_unchanged=[], metadata={"pattern_id": 1, "lang": "en"})
    score = pat.score_case(case, model="sonnet", force_full=True, runs=5)
    assert len(score["runs"]) == 5
    assert score["detected"] is True                  # majority verdict
    assert score["aggregate"]["fraction"] == 0.6      # stability signal
    assert score["status"] == "scored"


def test_pattern_score_case_true_negative_uses_median_edit_ratio(monkeypatch):
    import evals.scripts.run_pattern_eval as pat
    from evals.scripts._shared import Case
    inp = "This is a clean human sentence that should be left alone entirely."
    # 3 runs ~unchanged (low ratio), 2 heavily edited -> median low -> passes
    outs = iter([
        {"final": inp}, {"final": inp}, {"final": inp},
        {"final": "totally different rewritten text"},
        {"final": "totally different rewritten text"},
    ])
    monkeypatch.setattr(pat, "run_skill", lambda *a, **k: next(outs))
    case = Case(id="p8_en_001", input=inp, expected_changes=[], expected_unchanged=[],
                domain="casual", true_negative=True, metadata={"pattern_id": 8, "lang": "en"})
    score = pat.score_case(case, model="sonnet", force_full=False, runs=5)
    assert score["status"] == "true_negative"
    assert score["passes_true_negative"] is True      # median edit_ratio <= 0.10
    assert score["aggregate"]["flaky"] is True         # runs straddled the threshold


def test_pattern_score_case_session_limit_propagates(monkeypatch):
    """A session-limit error mid-case must propagate (quota guard), not become a None run."""
    import evals.scripts.run_pattern_eval as pat
    from evals.scripts._shared import Case, SkillRunError
    def boom(*a, **k):
        raise SkillRunError("Claude usage limit reached — session limit")
    monkeypatch.setattr(pat, "run_skill", boom)
    case = Case(id="p1_en_001", input="aiword here", expected_changes=["aiword"],
                domain="casual", true_negative=False, expected_unchanged=[], metadata={"pattern_id": 1, "lang": "en"})
    with pytest.raises(SkillRunError):
        pat.score_case(case, model="sonnet", force_full=True, runs=5)


def test_pattern_score_case_nonsession_failure_becomes_none_run(monkeypatch):
    """A non-session failure on one run becomes a None run; the case is NOT aborted."""
    import evals.scripts.run_pattern_eval as pat
    from evals.scripts._shared import Case, SkillRunError
    seq = iter([
        {"final": "clean"},                      # detected
        SkillRunError("transient CLI exit 1"),   # non-session -> None run
        {"final": "clean"},                      # detected
        {"final": "clean"},                      # detected
        {"final": "clean"},                      # detected
    ])
    def maybe(*a, **k):
        x = next(seq)
        if isinstance(x, Exception):
            raise x
        return x
    monkeypatch.setattr(pat, "run_skill", maybe)
    case = Case(id="p1_en_001", input="aiword here", expected_changes=["aiword"],
                domain="casual", true_negative=False, expected_unchanged=[], metadata={"pattern_id": 1, "lang": "en"})
    score = pat.score_case(case, model="sonnet", force_full=True, runs=5)
    assert score["runs"].count(None) == 1
    assert score["aggregate"]["n_fail"] == 1
    assert score["detected"] is True             # 4/4 successful detected


def test_pattern_run_inconclusive_case_own_bucket_not_failed(monkeypatch, tmp_path):
    """A case with <ceil(N/2) successful runs lands in inconclusive_cases, not failed."""
    import evals.scripts.run_pattern_eval as pat
    corpus_dir = tmp_path / "corpus"; corpus_dir.mkdir()
    partial_dir = tmp_path / "partial"; partial_dir.mkdir()
    _write_pattern_file(corpus_dir, 1, [
        {"id": "p1_en_001", "input": "aiword here", "expected_changes": ["aiword"],
         "domain": "casual", "metadata": {"pattern_id": 1, "lang": "en"}},
    ])
    from evals.scripts._shared import SkillRunError
    # 4 of 5 runs fail (non-session) -> only 1 success < ceil(5/2)=3 -> inconclusive
    seq = iter([
        {"final": "clean"},
        SkillRunError("x"), SkillRunError("x"), SkillRunError("x"), SkillRunError("x"),
    ])
    def maybe(*a, **k):
        x = next(seq)
        if isinstance(x, Exception):
            raise x
        return x
    monkeypatch.setattr(pat, "run_skill", maybe)
    monkeypatch.setattr(pat, "verify_skill_install", lambda: None)
    monkeypatch.setattr(f"{PATTERN_MODULE}.REPO_ROOT", tmp_path)
    report = pat.run(lang="en", runs=5, _corpus_dir_override=corpus_dir,
                     _partial_dir_override=partial_dir)
    s = report["summary"]
    assert "p1_en_001" in s["inconclusive_cases"]
    assert not s["failed"]                        # NOT laundered into failed
    assert s["is_complete"] is False              # terminal-unstable, exit 1


def test_pattern_multirun_partial_reused_wholesale(monkeypatch, tmp_path):
    """A cached multi-run partial (with runs[]) is reused without re-scoring; --force redoes."""
    import evals.scripts.run_pattern_eval as pat
    corpus_dir = tmp_path / "corpus"; corpus_dir.mkdir()
    partial_dir = tmp_path / "partial"; partial_dir.mkdir()
    _write_pattern_file(corpus_dir, 1, [
        {"id": "p1_en_001", "input": "aiword here", "expected_changes": ["aiword"],
         "domain": "casual", "metadata": {"pattern_id": 1, "lang": "en"}},
    ])
    calls = {"n": 0}
    def counting(*a, **k):
        calls["n"] += 1
        return {"final": "clean"}
    monkeypatch.setattr(pat, "run_skill", counting)
    monkeypatch.setattr(pat, "verify_skill_install", lambda: None)
    monkeypatch.setattr(f"{PATTERN_MODULE}.REPO_ROOT", tmp_path)
    pat.run(lang="en", runs=5, _corpus_dir_override=corpus_dir, _partial_dir_override=partial_dir)
    first = calls["n"]
    assert first == 5                       # 5 runs for the one case
    pat.run(lang="en", runs=5, _corpus_dir_override=corpus_dir, _partial_dir_override=partial_dir)
    assert calls["n"] == first              # second run reused the partial, no new skill calls
    pat.run(lang="en", runs=5, force=True, _corpus_dir_override=corpus_dir, _partial_dir_override=partial_dir)
    assert calls["n"] == first + 5          # --force re-scored
