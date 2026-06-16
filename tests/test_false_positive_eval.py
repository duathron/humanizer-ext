"""Tests for evals/scripts/run_false_positive_eval.py — pure helper functions.

Does NOT invoke the live `claude` CLI or the `run()` function directly.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from evals.scripts._shared import SkillRunError
from evals.scripts.run_false_positive_eval import (
    _read_sample,
    _discover_corpus_files,
    _partial_path,
    run,
)


# ---------------------------------------------------------------------------
# _read_sample tests
# ---------------------------------------------------------------------------


def test_read_sample_en_style_top_level_domain(tmp_path):
    """EN-style: domain: at the top level of frontmatter."""
    f = tmp_path / "en_casual.md"
    f.write_text(
        "---\n"
        "domain: casual\n"
        "lang: en\n"
        "---\n\n"
        "Body text here.\n",
        encoding="utf-8",
    )
    domain, body = _read_sample(f)
    assert domain == "casual"
    assert body == "Body text here."


def test_read_sample_en_style_domain_marketing(tmp_path):
    """EN-style top-level domain: marketing."""
    f = tmp_path / "en_marketing.md"
    f.write_text(
        "---\n"
        "domain: marketing\n"
        "lang: en\n"
        "---\n\n"
        "Buy now and save!\n",
        encoding="utf-8",
    )
    domain, body = _read_sample(f)
    assert domain == "marketing"
    assert body == "Buy now and save!"


def test_read_sample_de_style_nested_metadata_domain(tmp_path):
    """DE-style: domain indented under metadata: block."""
    f = tmp_path / "de_nested.md"
    f.write_text(
        "---\n"
        "id: samsung_marketing_smartphones\n"
        "license_class: research_only\n"
        "metadata:\n"
        "  domain: marketing\n"
        "  source: samsung_de\n"
        "---\n\n"
        "Jetzt Galaxy kaufen.\n",
        encoding="utf-8",
    )
    domain, body = _read_sample(f)
    assert domain == "marketing"
    assert body == "Jetzt Galaxy kaufen."


def test_read_sample_de_style_nested_domain_technical(tmp_path):
    """DE-style nested domain: technical."""
    f = tmp_path / "de_tech.md"
    f.write_text(
        "---\n"
        "id: heise_technical_news\n"
        "metadata:\n"
        "  domain: technical\n"
        "---\n\n"
        "Linux 6.9 ist erschienen.\n",
        encoding="utf-8",
    )
    domain, body = _read_sample(f)
    assert domain == "technical"
    assert "Linux 6.9" in body


def test_read_sample_no_frontmatter_defaults_to_casual(tmp_path):
    """File with no YAML frontmatter at all → domain defaults to 'casual'."""
    f = tmp_path / "plain.md"
    f.write_text("Just plain text. No frontmatter.\n", encoding="utf-8")
    domain, body = _read_sample(f)
    assert domain == "casual"
    assert body == "Just plain text. No frontmatter."


def test_read_sample_frontmatter_without_domain_defaults_to_casual(tmp_path):
    """Frontmatter present but no domain key → fallback to 'casual'."""
    f = tmp_path / "no_domain.md"
    f.write_text(
        "---\n"
        "id: some_file\n"
        "lang: de\n"
        "metadata:\n"
        "  source: example\n"
        "---\n\n"
        "Text without domain specified.\n",
        encoding="utf-8",
    )
    domain, body = _read_sample(f)
    assert domain == "casual"
    assert body == "Text without domain specified."


def test_read_sample_body_stripped_of_frontmatter(tmp_path):
    """Body must not contain any frontmatter lines."""
    f = tmp_path / "with_fm.md"
    f.write_text(
        "---\n"
        "domain: academic\n"
        "---\n\n"
        "This is the actual content.\n",
        encoding="utf-8",
    )
    domain, body = _read_sample(f)
    assert "domain:" not in body
    assert "---" not in body
    assert body == "This is the actual content."


# ---------------------------------------------------------------------------
# _discover_corpus_files tests
# ---------------------------------------------------------------------------


def test_discover_finds_flat_md_files(tmp_path):
    """Flat directory (EN layout): all .md files returned, _LICENSE excluded."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "file_a.md").write_text("a")
    (corpus_dir / "file_b.md").write_text("b")
    (corpus_dir / "_LICENSE").write_text("license")
    (corpus_dir / "_SOURCE").write_text("source")

    files = _discover_corpus_files(corpus_dir)
    names = {f.name for f in files}
    assert names == {"file_a.md", "file_b.md"}


def test_discover_finds_nested_md_files(tmp_path):
    """DE layout: .md files nested one level deep in source subdirs."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    subdir_a = corpus_dir / "bgbl_legal"
    subdir_a.mkdir()
    (subdir_a / "bgbl_legal_foo.md").write_text("foo")
    (subdir_a / "_LICENSE").write_text("license")
    subdir_b = corpus_dir / "heise_technical"
    subdir_b.mkdir()
    (subdir_b / "heise_technical_news.md").write_text("news")
    (subdir_b / "_SOURCE").write_text("source")

    files = _discover_corpus_files(corpus_dir)
    names = {f.name for f in files}
    assert names == {"bgbl_legal_foo.md", "heise_technical_news.md"}


def test_discover_excludes_underscore_prefixed_files(tmp_path):
    """Files starting with _ must be excluded at all nesting levels."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    subdir = corpus_dir / "source_x"
    subdir.mkdir()
    (subdir / "_LICENSE").write_text("l")
    (subdir / "_SOURCE").write_text("s")
    (subdir / "real_file.md").write_text("content")
    (corpus_dir / "_README.md").write_text("readme")  # top-level _ prefixed

    files = _discover_corpus_files(corpus_dir)
    names = {f.name for f in files}
    assert names == {"real_file.md"}


def test_discover_excludes_non_md_txt_files(tmp_path):
    """Only .md and .txt files are included."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "file.md").write_text("md")
    (corpus_dir / "file.txt").write_text("txt")
    (corpus_dir / "file.json").write_text("{}")
    (corpus_dir / "file.pdf").write_text("pdf")

    files = _discover_corpus_files(corpus_dir)
    names = {f.name for f in files}
    assert names == {"file.md", "file.txt"}


def test_discover_returns_sorted_list(tmp_path):
    """Result must be sorted for deterministic ordering."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    (corpus_dir / "z_file.md").write_text("z")
    (corpus_dir / "a_file.md").write_text("a")
    (corpus_dir / "m_file.md").write_text("m")

    files = _discover_corpus_files(corpus_dir)
    names = [f.name for f in files]
    assert names == sorted(names)


# ---------------------------------------------------------------------------
# _partial_path stem-collision tests
# ---------------------------------------------------------------------------


def test_partial_path_flat_file_uses_relative_path(tmp_path):
    """Flat corpus: relative path collapses to just the filename stem."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    file_path = corpus_dir / "casual_blog_draft_01.md"

    key = _partial_path_key(corpus_dir, file_path)
    assert key == "casual_blog_draft_01"


def test_partial_path_nested_file_includes_subdir(tmp_path):
    """Nested file: key encodes subdir to avoid stem collision."""
    corpus_dir = tmp_path / "corpus"
    subdir = corpus_dir / "bgbl_legal"
    subdir.mkdir(parents=True)
    file_path = subdir / "bgbl_legal_foo.md"

    key = _partial_path_key(corpus_dir, file_path)
    assert key == "bgbl_legal_bgbl_legal_foo"


def test_partial_path_no_stem_collision_across_subdirs(tmp_path):
    """Two files with same stem in different subdirs must get different keys."""
    corpus_dir = tmp_path / "corpus"
    (corpus_dir / "src_a").mkdir(parents=True)
    (corpus_dir / "src_b").mkdir(parents=True)
    file_a = corpus_dir / "src_a" / "shared_name.md"
    file_b = corpus_dir / "src_b" / "shared_name.md"

    key_a = _partial_path_key(corpus_dir, file_a)
    key_b = _partial_path_key(corpus_dir, file_b)
    assert key_a != key_b


def test_partial_path_key_replaces_separators_not_dots(tmp_path):
    """Path separators replaced with underscores; suffix stripped."""
    corpus_dir = tmp_path / "corpus"
    subdir = corpus_dir / "sub"
    subdir.mkdir(parents=True)
    file_path = subdir / "my_file.md"

    key = _partial_path_key(corpus_dir, file_path)
    # Should be "sub_my_file", no dots, no slashes
    assert "/" not in key
    assert "\\" not in key
    assert "." not in key


# ---------------------------------------------------------------------------
# Helper: derives the relative-path key that _partial_path should use.
# Mirrors the expected logic from the fix so tests remain implementation-agnostic
# while still being specific about the contract.
# ---------------------------------------------------------------------------


def _partial_path_key(corpus_dir: Path, file_path: Path) -> str:
    """Reference implementation of the stem key: relative path, sep→_, no suffix."""
    rel = file_path.relative_to(corpus_dir)
    return str(rel.with_suffix("")).replace("/", "_").replace("\\", "_")


# ---------------------------------------------------------------------------
# Error isolation in run() — per-item failures and session-limit handling
# ---------------------------------------------------------------------------


def _make_corpus(corpus_dir: Path, filenames: list[str]) -> list[Path]:
    """Write minimal .md corpus files with a 'casual' domain frontmatter."""
    paths = []
    for name in filenames:
        p = corpus_dir / name
        p.write_text(
            "---\ndomain: casual\n---\n\nSome human-written text.\n",
            encoding="utf-8",
        )
        paths.append(p)
    return paths


def _make_run_kwargs(corpus_dir: Path, partial_dir: Path, lang: str = "en") -> dict:
    """Patch targets needed to drive run() without touching the filesystem layout."""
    return {"corpus_dir": corpus_dir, "partial_dir": partial_dir, "lang": lang}


# We need to patch REPO_ROOT inside the module so partial paths land in tmp_path.
FP_MODULE = "evals.scripts.run_false_positive_eval"


def test_fp_run_per_item_timeout_continues_and_records_failure(tmp_path, monkeypatch):
    """Case-level fallback: score_human_text itself raises TimeoutExpired → loop continues;
    failing file in summary['failed']; run marked is_complete=False.

    Under SP3a a realistic per-run timeout becomes a None run inside score_human_text's
    multi-run loop, so this test covers the case-level except that remains for defensive
    coverage (e.g. a monkeypatched score function that propagates, or a regression).
    The realistic per-run path is covered by test_fp_score_runs_n_times_median_verdict
    and test_fp_run_inconclusive_file_own_bucket.
    """
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    _make_corpus(corpus_dir, ["file_a.md", "file_b.md", "file_c.md"])

    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    monkeypatch.setattr(f"{FP_MODULE}.REPO_ROOT", tmp_path)

    call_count = {"n": 0}

    def fake_score(text, *, lang, model, domain, **_):
        call_count["n"] += 1
        # file_b.md is the second call — raise timeout
        if call_count["n"] == 2:
            raise subprocess.TimeoutExpired(cmd="claude", timeout=180)
        return {
            "edit_distance": 0,
            "edit_ratio": 0.0,
            "preflight_message": "",
            "density_preflight_quick_drop": True,
            "rewrite_length_chars": 10,
        }

    monkeypatch.setattr(f"{FP_MODULE}.score_human_text", fake_score)
    # Bypass skill install check
    monkeypatch.setattr(f"{FP_MODULE}.verify_skill_install", lambda: None)

    result = run(
        lang="en",
        corpus="synthetic",
        model="sonnet",
        threshold=0.10,
        force=False,
        aggregate_only=False,
        _corpus_dir_override=corpus_dir,
        _partial_dir_override=partial_dir,
    )

    summary = result["summary"]
    # Two files succeeded, one failed
    assert summary["total_files"] == 2, f"expected 2 successes, got {summary}"
    assert len(summary["failed"]) == 1
    assert "file_b.md" in summary["failed"][0]["file"]
    assert "timeout" in summary["failed"][0]["error"].lower()
    # Run is NOT complete because there were failures
    assert summary.get("is_complete") is False


def test_fp_run_non_session_skill_error_continues_and_records_failure(tmp_path, monkeypatch):
    """Non-session-limit SkillRunError on one file → loop continues; recorded in failed."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    _make_corpus(corpus_dir, ["file_a.md", "file_b.md"])

    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    monkeypatch.setattr(f"{FP_MODULE}.REPO_ROOT", tmp_path)

    call_count = {"n": 0}

    def fake_score(text, *, lang, model, domain, **_):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise SkillRunError("claude CLI exited 1\n  stderr: rate limit\n  stdout: (empty)")
        return {
            "edit_distance": 5,
            "edit_ratio": 0.05,
            "preflight_message": "",
            "density_preflight_quick_drop": False,
            "rewrite_length_chars": 90,
        }

    monkeypatch.setattr(f"{FP_MODULE}.score_human_text", fake_score)
    monkeypatch.setattr(f"{FP_MODULE}.verify_skill_install", lambda: None)

    result = run(
        lang="en",
        corpus="synthetic",
        model="sonnet",
        threshold=0.10,
        force=False,
        aggregate_only=False,
        _corpus_dir_override=corpus_dir,
        _partial_dir_override=partial_dir,
    )

    summary = result["summary"]
    assert summary["total_files"] == 1
    assert len(summary["failed"]) == 1
    assert summary.get("is_complete") is False


def test_fp_run_session_limit_stops_loop_and_marks_incomplete(tmp_path, monkeypatch):
    """Session-limit SkillRunError → loop breaks; item not in per-item results;
    run marked session_limit_hit=True; subsequent items not attempted."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    _make_corpus(corpus_dir, ["file_a.md", "file_b.md", "file_c.md"])

    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    monkeypatch.setattr(f"{FP_MODULE}.REPO_ROOT", tmp_path)

    call_count = {"n": 0}

    def fake_score(text, *, lang, model, domain, **_):
        call_count["n"] += 1
        if call_count["n"] == 2:
            raise SkillRunError(
                "claude CLI exited 1\n  stderr: (empty)\n  stdout: You've hit your session limit"
            )
        return {
            "edit_distance": 0,
            "edit_ratio": 0.0,
            "preflight_message": "",
            "density_preflight_quick_drop": True,
            "rewrite_length_chars": 10,
        }

    monkeypatch.setattr(f"{FP_MODULE}.score_human_text", fake_score)
    monkeypatch.setattr(f"{FP_MODULE}.verify_skill_install", lambda: None)

    result = run(
        lang="en",
        corpus="synthetic",
        model="sonnet",
        threshold=0.10,
        force=False,
        aggregate_only=False,
        _corpus_dir_override=corpus_dir,
        _partial_dir_override=partial_dir,
    )

    summary = result["summary"]
    # Only file_a.md succeeded (1 call); file_b.md hit session limit; file_c.md not attempted
    assert summary["total_files"] == 1
    assert call_count["n"] == 2  # file_c never called
    assert summary.get("session_limit_hit") is True
    assert summary.get("is_complete") is False
    # No partial written for the session-limit file
    partials = list(partial_dir.iterdir())
    assert len(partials) == 1  # only file_a's partial


def test_fp_run_success_path_unaffected(tmp_path, monkeypatch):
    """All files succeed → no failed list entries, is_complete True, normal scoring."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    _make_corpus(corpus_dir, ["file_a.md", "file_b.md"])

    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    monkeypatch.setattr(f"{FP_MODULE}.REPO_ROOT", tmp_path)

    def fake_score(text, *, lang, model, domain, **_):
        return {
            "edit_distance": 2,
            "edit_ratio": 0.02,
            "preflight_message": "Pre-flight: 0 Tier-1 patterns",
            "density_preflight_quick_drop": True,
            "rewrite_length_chars": 98,
        }

    monkeypatch.setattr(f"{FP_MODULE}.score_human_text", fake_score)
    monkeypatch.setattr(f"{FP_MODULE}.verify_skill_install", lambda: None)

    result = run(
        lang="en",
        corpus="synthetic",
        model="sonnet",
        threshold=0.10,
        force=False,
        aggregate_only=False,
        _corpus_dir_override=corpus_dir,
        _partial_dir_override=partial_dir,
    )

    summary = result["summary"]
    assert summary["total_files"] == 2
    assert summary.get("failed", []) == []
    assert summary.get("is_complete") is True
    assert summary.get("session_limit_hit") is False


# ---------------------------------------------------------------------------
# Task 3: multi-run tests
# ---------------------------------------------------------------------------


def test_fp_score_runs_n_times_median_verdict(monkeypatch):
    import evals.scripts.run_false_positive_eval as fp
    inp = "A clean human paragraph that the skill should leave essentially intact here."
    # 3 near-verbatim (low ratio) + 2 heavy edits -> median low -> NOT over-threshold
    outs = iter([
        {"final": inp}, {"final": inp}, {"final": inp},
        {"final": "completely different text entirely"},
        {"final": "completely different text entirely"},
    ])
    monkeypatch.setattr(fp, "run_skill", lambda *a, **k: next(outs))
    score = fp.score_human_text(inp, lang="en", model="sonnet", domain="casual", runs=5)
    assert len(score["runs"]) == 5
    assert score["above_threshold"] is False          # median edit_ratio <= 0.10
    assert score["aggregate"]["flaky"] is True


def test_fp_score_session_limit_propagates(monkeypatch):
    import evals.scripts.run_false_positive_eval as fp
    from evals.scripts._shared import SkillRunError
    def boom(*a, **k):
        raise SkillRunError("session limit reached")
    monkeypatch.setattr(fp, "run_skill", boom)
    with pytest.raises(SkillRunError):
        fp.score_human_text("clean text", lang="en", model="sonnet", domain="casual", runs=5)


def test_fp_run_inconclusive_file_own_bucket(monkeypatch, tmp_path):
    import evals.scripts.run_false_positive_eval as fp
    from evals.scripts._shared import SkillRunError
    corpus_dir = tmp_path / "human" / "synthetic"; corpus_dir.mkdir(parents=True)
    (corpus_dir / "f1.md").write_text("A clean human sentence left alone.", encoding="utf-8")
    partial_dir = tmp_path / "partial"; partial_dir.mkdir()
    seq = iter([
        {"final": "A clean human sentence left alone."},
        SkillRunError("x"), SkillRunError("x"), SkillRunError("x"), SkillRunError("x"),
    ])
    def maybe(*a, **k):
        x = next(seq)
        if isinstance(x, Exception): raise x
        return x
    monkeypatch.setattr(fp, "run_skill", maybe)
    monkeypatch.setattr(fp, "verify_skill_install", lambda: None)
    monkeypatch.setattr("evals.scripts.run_false_positive_eval.REPO_ROOT", tmp_path)
    report = fp.run(lang="en", corpus="synthetic", runs=5,
                    _corpus_dir_override=corpus_dir, _partial_dir_override=partial_dir)
    s = report["summary"]
    assert "f1.md" in s["inconclusive_files"]
    assert not s["failed"]
    assert s["is_complete"] is False


def test_fp_score_uses_configured_threshold(monkeypatch):
    """flaky/verdict computed at the passed threshold, not hardcoded DEFAULT_THRESHOLD."""
    import evals.scripts.run_false_positive_eval as fp
    # 5 runs with fixed edit_ratios via monkeypatched _score_human_text_once
    ratios = iter([0.05, 0.06, 0.20, 0.30, 0.40])
    monkeypatch.setattr(fp, "_score_human_text_once",
                        lambda *a, **k: {"edit_ratio": next(ratios),
                                         "density_preflight_quick_drop": False,
                                         "rewrite_length_chars": 10, "preflight_message": ""})
    # threshold 0.25: successes straddle (0.05,0.06,0.20 below; 0.30,0.40 above) -> flaky;
    # median 0.20 <= 0.25 -> NOT above_threshold
    score = fp.score_human_text("x", lang="en", model="sonnet", domain="casual",
                                runs=5, threshold=0.25)
    assert score["aggregate"]["flaky"] is True
    assert score["above_threshold"] is False
    assert score["edit_ratio"] == 0.20


def test_fp_run_rejects_runs_below_one():
    import evals.scripts.run_false_positive_eval as fp
    with pytest.raises(ValueError, match="runs must be >= 1"):
        fp.run(lang="en", corpus="synthetic", runs=0)


def test_fp_run_all_failed_file_no_crash_none_median(monkeypatch, tmp_path):
    """All N runs fail -> median None. run() must NOT crash on `None > threshold`."""
    import evals.scripts.run_false_positive_eval as fp
    from evals.scripts._shared import SkillRunError
    corpus_dir = tmp_path / "human" / "synthetic"; corpus_dir.mkdir(parents=True)
    (corpus_dir / "f1.md").write_text("A clean human sentence.", encoding="utf-8")
    partial_dir = tmp_path / "partial"; partial_dir.mkdir()
    monkeypatch.setattr(fp, "run_skill",
                        lambda *a, **k: (_ for _ in ()).throw(SkillRunError("transient")))
    monkeypatch.setattr(fp, "verify_skill_install", lambda: None)
    monkeypatch.setattr("evals.scripts.run_false_positive_eval.REPO_ROOT", tmp_path)
    report = fp.run(lang="en", corpus="synthetic", runs=5,
                    _corpus_dir_override=corpus_dir, _partial_dir_override=partial_dir)
    s = report["summary"]
    assert "f1.md" in s["inconclusive_files"]      # 0 successes -> inconclusive
    # the per-file record exists with above_threshold False (None-median guarded), no crash
    rec = next(r for r in report["per_file"] if r["file"] == "f1.md")
    assert rec["above_threshold"] is False
    assert rec["edit_ratio"] is None


# ---------------------------------------------------------------------------
# Task 3: refusal guard in _score_human_text_once (defensive)
# ---------------------------------------------------------------------------


def test_fp_score_refusal_run_becomes_none(monkeypatch):
    """A refusal on an FP file → None run → excluded from median; all-refuse → inconclusive
    (FP uses force_full=False and shouldn't refuse, but this closes the inverse bug:
    a refusal = huge edit_ratio = false 'over-edit')."""
    import evals.scripts.run_false_positive_eval as fp
    monkeypatch.setattr(fp, "run_skill",
                        lambda *a, **k: {"final": "No text provided. Paste the text to humanize."})
    score = fp.score_human_text("A clean human paragraph left alone.", lang="en",
                                model="sonnet", domain="casual", runs=5)
    assert score["runs"] == [None, None, None, None, None]
    assert score["aggregate"]["inconclusive"] is True
    assert score["above_threshold"] is False                  # NOT a false over-edit


# ---------------------------------------------------------------------------
# --save-rewrites flag: sidecar capture (new feature)
# ---------------------------------------------------------------------------


def test_fp_save_rewrites_writes_sidecar(monkeypatch, tmp_path):
    """When save_rewrites=True, run() writes a JSON sidecar next to the partial
    containing the original text and per-run (index, edit_ratio, rewrite) entries.
    The scored partial itself must NOT gain a 'rewrite' key.
    """
    import json as _json
    import evals.scripts.run_false_positive_eval as fp

    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    # One sample file with known content
    sample_text = "A perfectly clean human-written paragraph about coffee."
    (corpus_dir / "sample_01.md").write_text(
        f"---\ndomain: casual\n---\n\n{sample_text}\n",
        encoding="utf-8",
    )
    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    # Stub _score_human_text_once to return a fixed rewrite + ratio
    call_idx = {"n": 0}

    def fake_once(text, *, lang, model, domain):
        call_idx["n"] += 1
        rewrite = f"A clean human-written paragraph about coffee (run {call_idx['n']})."
        edit_distance = abs(len(rewrite) - len(text))
        ratio = round(edit_distance / max(1, len(text)), 4)
        return {
            "edit_ratio": ratio,
            "edit_distance": edit_distance,
            "density_preflight_quick_drop": True,
            "preflight_message": "Pre-flight: 0 Tier-1 patterns",
            "rewrite_length_chars": len(rewrite),
            "rewrite": rewrite,
        }

    monkeypatch.setattr(fp, "_score_human_text_once", fake_once)
    monkeypatch.setattr(fp, "verify_skill_install", lambda: None)
    monkeypatch.setattr("evals.scripts.run_false_positive_eval.REPO_ROOT", tmp_path)

    report = fp.run(
        lang="en",
        corpus="synthetic",
        model="sonnet",
        threshold=0.10,
        force=False,
        aggregate_only=False,
        runs=3,
        save_rewrites=True,
        _corpus_dir_override=corpus_dir,
        _partial_dir_override=partial_dir,
    )

    # --- sidecar must exist ---
    sidecar_files = list(partial_dir.glob("*__rewrites.json"))
    assert len(sidecar_files) == 1, f"Expected 1 sidecar, got: {sidecar_files}"
    sidecar = _json.loads(sidecar_files[0].read_text(encoding="utf-8"))

    # original text captured once at top level
    assert sidecar["original"] == sample_text

    # per-run entries: index, edit_ratio, rewrite
    assert len(sidecar["runs"]) == 3
    for i, entry in enumerate(sidecar["runs"]):
        assert "run_index" in entry
        assert entry["run_index"] == i
        assert "edit_ratio" in entry
        assert "rewrite" in entry
        assert len(entry["rewrite"]) > 0

    # --- scored partial must NOT contain 'rewrite' key ---
    partial_files = [p for p in partial_dir.glob("*.json") if "__rewrites" not in p.name]
    assert len(partial_files) == 1
    scored = _json.loads(partial_files[0].read_text(encoding="utf-8"))
    assert "rewrite" not in scored, f"Scored partial must not contain 'rewrite', got keys: {list(scored.keys())}"

    # --- sidecar path follows naming convention ---
    # fp_<lang>_<corpus>_<rel_key>__rewrites.json
    assert sidecar_files[0].name.startswith("fp_en_synthetic_")
    assert sidecar_files[0].name.endswith("__rewrites.json")


def test_fp_save_rewrites_false_no_sidecar_and_partial_unchanged(monkeypatch, tmp_path):
    """When save_rewrites=False (default), no sidecar is written and the scored
    partial dict is byte-identical in schema to pre-feature behaviour.
    """
    import json as _json
    import evals.scripts.run_false_positive_eval as fp

    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    sample_text = "Another clean human paragraph about tea."
    (corpus_dir / "sample_02.md").write_text(
        f"---\ndomain: casual\n---\n\n{sample_text}\n",
        encoding="utf-8",
    )
    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    EXPECTED_SCORED_PARTIAL_KEYS = {
        "edit_ratio", "median_edit_ratio", "runs", "aggregate",
        "above_threshold", "density_preflight_quick_drop",
        "rewrite_length_chars", "preflight_message", "file", "domain",
    }

    def fake_once(text, *, lang, model, domain):
        rewrite = text  # identity — zero edit
        return {
            "edit_ratio": 0.0,
            "edit_distance": 0,
            "density_preflight_quick_drop": True,
            "preflight_message": "Pre-flight: 0 Tier-1 patterns",
            "rewrite_length_chars": len(rewrite),
            "rewrite": rewrite,   # key present in once-return; must NOT bleed into partial
        }

    monkeypatch.setattr(fp, "_score_human_text_once", fake_once)
    monkeypatch.setattr(fp, "verify_skill_install", lambda: None)
    monkeypatch.setattr("evals.scripts.run_false_positive_eval.REPO_ROOT", tmp_path)

    report = fp.run(
        lang="en",
        corpus="synthetic",
        model="sonnet",
        threshold=0.10,
        force=False,
        aggregate_only=False,
        runs=3,
        # save_rewrites defaults to False — not passed
        _corpus_dir_override=corpus_dir,
        _partial_dir_override=partial_dir,
    )

    # No sidecar files
    sidecar_files = list(partial_dir.glob("*__rewrites.json"))
    assert sidecar_files == [], f"Expected no sidecars, got: {sidecar_files}"

    # Scored partial has exactly the expected keys
    partial_files = list(partial_dir.glob("*.json"))
    assert len(partial_files) == 1
    scored = _json.loads(partial_files[0].read_text(encoding="utf-8"))
    assert set(scored.keys()) == EXPECTED_SCORED_PARTIAL_KEYS, (
        f"Scored partial key drift.\n"
        f"  Expected: {sorted(EXPECTED_SCORED_PARTIAL_KEYS)}\n"
        f"  Got:      {sorted(scored.keys())}"
    )


# ---------------------------------------------------------------------------
# Verbatim-plus-commentary guard in _score_human_text_once
# ---------------------------------------------------------------------------


def test_fp_score_once_verbatim_plus_commentary_guard_fires(monkeypatch):
    """POSITIVE: skill returns <input verbatim> + trailing 'no changes' note.

    Guard must:
    - set edit_ratio 0.0  (body unedited, distance measured as 0)
    - set verbatim_plus_commentary True
    - keep the FULL rewrite (incl. note) in the 'rewrite' key (for sidecars)
    """
    import evals.scripts.run_false_positive_eval as fp

    input_text = "This is a clean human paragraph that requires no editing at all."
    note = "\n\nText unverändert — kein Eingriff nötig."
    skill_output = input_text + note

    monkeypatch.setattr(fp, "run_skill", lambda *a, **k: {"final": skill_output})

    result = fp._score_human_text_once(
        input_text, lang="de", model="sonnet", domain="casual"
    )

    assert result is not None
    assert result["edit_ratio"] == 0.0, (
        f"Guard should set edit_ratio to 0.0 when body is verbatim, got {result['edit_ratio']}"
    )
    assert result["verbatim_plus_commentary"] is True, (
        "Guard must set verbatim_plus_commentary=True when it fires"
    )
    # Full rewrite (incl. note) must be preserved for sidecar
    assert note.strip() in result["rewrite"], (
        f"'rewrite' key must retain the note text; got: {result['rewrite']!r}"
    )
    assert result["rewrite"] == skill_output, (
        f"'rewrite' must be the full skill output, not the stripped body"
    )


def test_fp_score_once_genuine_edit_guard_does_not_fire(monkeypatch):
    """NEGATIVE: skill changes a word in the body AND appends a note.

    The body is NOT a startswith-match of the input → guard must NOT fire →
    real edit_distance/edit_ratio are preserved.
    """
    import evals.scripts.run_false_positive_eval as fp

    input_text = "This is a clean human paragraph that requires no editing at all."
    # Body differs from input (word changed): startswith will be False
    changed_body = "This is a clean human paragraph that requires some editing now."
    note = "\n\nNote: minor adjustment applied."
    skill_output = changed_body + note

    monkeypatch.setattr(fp, "run_skill", lambda *a, **k: {"final": skill_output})

    result = fp._score_human_text_once(
        input_text, lang="en", model="sonnet", domain="casual"
    )

    assert result is not None
    assert result["edit_ratio"] > 0.0, (
        f"Real edit must not be masked; expected edit_ratio > 0, got {result['edit_ratio']}"
    )
    assert result["verbatim_plus_commentary"] is False, (
        "Guard must NOT fire when body differs from input"
    )


def test_fp_score_once_clean_preserve_no_note(monkeypatch):
    """NEGATIVE (edge): skill returns input exactly (no appended note).

    edit_ratio must be 0.0 regardless of guard (rewrite == input, no trailing block).
    verbatim_plus_commentary may be False (len not strictly greater).
    No crash.
    """
    import evals.scripts.run_false_positive_eval as fp

    input_text = "A perfectly preserved paragraph."

    monkeypatch.setattr(fp, "run_skill", lambda *a, **k: {"final": input_text})

    result = fp._score_human_text_once(
        input_text, lang="en", model="sonnet", domain="casual"
    )

    assert result is not None
    assert result["edit_ratio"] == 0.0, (
        f"Clean preserve must yield 0.0 edit_ratio; got {result['edit_ratio']}"
    )
    # Guard should NOT fire when len(rewrite.strip()) == len(input.strip())
    assert result["verbatim_plus_commentary"] is False


def test_fp_score_once_refusal_path_unaffected_by_guard(monkeypatch):
    """NEGATIVE: refusal response → _score_human_text_once returns None (unchanged).

    The verbatim-commentary guard must not interfere with the refusal path.
    """
    import evals.scripts.run_false_positive_eval as fp

    input_text = "Clean human text."
    refusal_text = "No text provided. Paste the text to humanize."

    monkeypatch.setattr(fp, "run_skill", lambda *a, **k: {"final": refusal_text})

    result = fp._score_human_text_once(
        input_text, lang="en", model="sonnet", domain="casual"
    )

    assert result is None, (
        f"Refusal must still return None; got {result!r}"
    )
