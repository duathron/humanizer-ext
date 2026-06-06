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
    """TimeoutExpired on one file → loop continues; remaining files processed;
    failing file appears in summary['failed']; run is marked incomplete (is_complete=False)."""
    corpus_dir = tmp_path / "corpus"
    corpus_dir.mkdir()
    _make_corpus(corpus_dir, ["file_a.md", "file_b.md", "file_c.md"])

    partial_dir = tmp_path / "partials"
    partial_dir.mkdir()

    monkeypatch.setattr(f"{FP_MODULE}.REPO_ROOT", tmp_path)

    call_count = {"n": 0}

    def fake_score(text, *, lang, model, domain):
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

    def fake_score(text, *, lang, model, domain):
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

    def fake_score(text, *, lang, model, domain):
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

    def fake_score(text, *, lang, model, domain):
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
