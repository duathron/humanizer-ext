"""Unit tests for evals.scripts.generate_de_ai_corpus_cli.

All tests are pure-unit / offline: no network calls, no actual claude CLI
subprocess (mocked where needed). Tests verify prompt templates, env stripping,
resume logic, frontmatter, and CLI smoke.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest import mock


# ---------------------------------------------------------------------------
# Prompt template assembly
# ---------------------------------------------------------------------------

def test_build_prompt_casual_contains_topic():
    from evals.scripts.generate_de_ai_corpus_cli import _build_prompt

    result = _build_prompt("casual", "Homeoffice und Work-Life-Balance")
    assert "Homeoffice und Work-Life-Balance" in result
    assert "[TOPIC]" not in result


def test_build_prompt_career_uses_position_placeholder():
    from evals.scripts.generate_de_ai_corpus_cli import _build_prompt

    result = _build_prompt("career", "Softwareentwicklerin")
    assert "Softwareentwicklerin" in result
    assert "[POSITION]" not in result
    assert "[TOPIC]" not in result


def test_build_prompt_all_domains_fill_placeholder():
    """Every domain template must have [TOPIC]/[POSITION] fully replaced."""
    from evals.scripts.generate_de_ai_corpus_cli import _build_prompt, _ALL_DOMAINS, DOMAIN_TOPICS

    for domain in _ALL_DOMAINS:
        topic = DOMAIN_TOPICS[domain][0]
        result = _build_prompt(domain, topic)
        assert "[TOPIC]" not in result, f"[TOPIC] not replaced in domain={domain}"
        assert "[POSITION]" not in result, f"[POSITION] not replaced in domain={domain}"
        assert topic in result, f"topic not in output for domain={domain}"


def test_prompt_templates_keys_match_all_domains():
    from evals.scripts.generate_de_ai_corpus_cli import PROMPT_TEMPLATES, _ALL_DOMAINS

    for domain in _ALL_DOMAINS:
        assert domain in PROMPT_TEMPLATES, f"Missing prompt template for domain={domain}"


def test_domain_topics_keys_match_all_domains():
    from evals.scripts.generate_de_ai_corpus_cli import DOMAIN_TOPICS, _ALL_DOMAINS

    for domain in _ALL_DOMAINS:
        assert domain in DOMAIN_TOPICS, f"Missing topics for domain={domain}"
        assert len(DOMAIN_TOPICS[domain]) >= 5, (
            f"Domain {domain} has only {len(DOMAIN_TOPICS[domain])} topics; need >= 5"
        )


# ---------------------------------------------------------------------------
# Domain × topic × model expansion
# ---------------------------------------------------------------------------

def test_domain_model_topic_expansion_produces_90_combos():
    """Default config: 6 domains × 3 models × 5 topics = 90."""
    from evals.scripts.generate_de_ai_corpus_cli import (
        _ALL_DOMAINS, _ALL_MODELS, DOMAIN_TOPICS,
    )

    samples_per_combo = 5
    total = 0
    for domain in _ALL_DOMAINS:
        topics = DOMAIN_TOPICS[domain][:samples_per_combo]
        for model in _ALL_MODELS:
            for _topic in topics:
                total += 1
    assert total == 90


def test_sample_path_structure():
    from evals.scripts.generate_de_ai_corpus_cli import _sample_path

    out_dir = Path("/tmp/ai_corpus")
    path = _sample_path(out_dir, "casual", "sonnet", 3)
    assert path == out_dir / "casual" / "sonnet" / "sample_03.md"


def test_sample_path_zero_padding():
    from evals.scripts.generate_de_ai_corpus_cli import _sample_path

    path = _sample_path(Path("/tmp/x"), "academic", "haiku", 1)
    assert path.name == "sample_01.md"


# ---------------------------------------------------------------------------
# Env stripping: ANTHROPIC_API_KEY must not reach subprocess
# ---------------------------------------------------------------------------

def test_strip_api_key_env_removes_key():
    from evals.scripts.generate_de_ai_corpus_cli import _strip_api_key_env

    with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-123", "HOME": "/home/user"}):
        cli_env = _strip_api_key_env()

    assert "ANTHROPIC_API_KEY" not in cli_env
    assert "HOME" in cli_env


def test_strip_api_key_env_preserves_other_vars():
    from evals.scripts.generate_de_ai_corpus_cli import _strip_api_key_env

    with mock.patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "sk-secret",
        "PATH": "/usr/bin",
        "MY_VAR": "hello",
    }, clear=True):
        cli_env = _strip_api_key_env()

    assert "ANTHROPIC_API_KEY" not in cli_env
    assert cli_env.get("PATH") == "/usr/bin"
    assert cli_env.get("MY_VAR") == "hello"


def test_strip_api_key_env_ok_when_key_not_set():
    """If ANTHROPIC_API_KEY is absent, _strip_api_key_env must still work."""
    from evals.scripts.generate_de_ai_corpus_cli import _strip_api_key_env

    env_without_key = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
    with mock.patch.dict(os.environ, env_without_key, clear=True):
        cli_env = _strip_api_key_env()

    assert "ANTHROPIC_API_KEY" not in cli_env


# ---------------------------------------------------------------------------
# --continue (resume) skip-existing logic
# ---------------------------------------------------------------------------

def test_resume_skips_existing_sample(tmp_path):
    """generate_corpus with resume=True skips already-written sample files."""
    from evals.scripts.generate_de_ai_corpus_cli import generate_corpus, _sample_path

    # Pre-create the sample file for casual/sonnet/sample_01.md
    out_dir = tmp_path / "claude_cli"
    existing = _sample_path(out_dir, "casual", "sonnet", 1)
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("---\ndomain: casual\n---\n\nPre-existing content.\n")

    # Track subprocess calls
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        class _R:
            returncode = 0
            stdout = "Generated text " * 30
            stderr = ""
        return _R()

    with mock.patch("shutil.which", return_value="/usr/local/bin/claude"), \
         mock.patch("subprocess.run", side_effect=fake_run):
        generate_corpus(
            domains=["casual"],
            models=["sonnet"],
            samples_per_combo=1,
            out_dir=out_dir,
            resume=True,
            dry_run=False,
        )

    # The pre-existing sample must not have triggered a subprocess call
    assert not any("casual" in str(c) and "sonnet" in str(c) for c in calls), (
        f"Expected no subprocess call for pre-existing sample, got calls: {calls}"
    )


def test_resume_false_overwrites_existing(tmp_path):
    """Without --continue, generate_corpus overwrites existing samples."""
    from evals.scripts.generate_de_ai_corpus_cli import generate_corpus, _sample_path

    out_dir = tmp_path / "claude_cli"
    existing = _sample_path(out_dir, "casual", "sonnet", 1)
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("old content")

    generated_texts: list[str] = []

    def fake_run(cmd, **kwargs):
        class _R:
            returncode = 0
            stdout = "Neuer generierter Text " * 15
            stderr = ""
        generated_texts.append(_R.stdout)
        return _R()

    with mock.patch("shutil.which", return_value="/usr/local/bin/claude"), \
         mock.patch("subprocess.run", side_effect=fake_run):
        generate_corpus(
            domains=["casual"],
            models=["sonnet"],
            samples_per_combo=1,
            out_dir=out_dir,
            resume=False,
            dry_run=False,
        )

    content = existing.read_text()
    assert "old content" not in content
    assert "Neuer generierter Text" in content


# ---------------------------------------------------------------------------
# Frontmatter generation
# ---------------------------------------------------------------------------

def test_render_frontmatter_contains_required_fields():
    from evals.scripts.generate_de_ai_corpus_cli import _render_frontmatter

    fm = _render_frontmatter("casual", "sonnet", "Homeoffice", 1, "2026-05-28")
    assert "domain: casual" in fm
    assert "model: sonnet" in fm
    assert "generated_via:" in fm
    assert "subscription" in fm
    assert "generated_date:" in fm
    assert fm.startswith("---")
    # Closing delimiter
    assert fm.count("---") >= 2


def test_render_frontmatter_all_domains_and_models():
    from evals.scripts.generate_de_ai_corpus_cli import (
        _render_frontmatter, _ALL_DOMAINS, _ALL_MODELS,
    )

    for domain in _ALL_DOMAINS:
        for model in _ALL_MODELS:
            fm = _render_frontmatter(domain, model, "TestTopic", 1, "2026-05-28")
            assert f"domain: {domain}" in fm
            assert f"model: {model}" in fm


# ---------------------------------------------------------------------------
# _parse_list_arg
# ---------------------------------------------------------------------------

def test_parse_list_arg_all_expands():
    from evals.scripts.generate_de_ai_corpus_cli import _parse_list_arg, _ALL_DOMAINS

    result = _parse_list_arg("all", _ALL_DOMAINS, "domains")
    assert result == _ALL_DOMAINS


def test_parse_list_arg_subset():
    from evals.scripts.generate_de_ai_corpus_cli import _parse_list_arg, _ALL_DOMAINS

    result = _parse_list_arg("casual,academic", _ALL_DOMAINS, "domains")
    assert result == ["casual", "academic"]


# ---------------------------------------------------------------------------
# CLI smoke tests (no network, no actual claude call)
# ---------------------------------------------------------------------------

def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "evals.scripts.generate_de_ai_corpus_cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "generate_de_ai_corpus_cli" in result.stdout
    assert "--domains" in result.stdout
    assert "--models" in result.stdout
    assert "--samples-per-combo" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--continue" in result.stdout


def test_cli_dry_run():
    result = subprocess.run(
        [sys.executable, "-m", "evals.scripts.generate_de_ai_corpus_cli", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    out = result.stdout
    assert "DRY RUN" in out
    assert "ANTHROPIC_API_KEY" in out  # env strip note
    assert "subscription" in out
    assert "$0" in out


def test_cli_dry_run_subset():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "evals.scripts.generate_de_ai_corpus_cli",
            "--dry-run",
            "--domains",
            "casual,academic",
            "--models",
            "sonnet",
            "--samples-per-combo",
            "2",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    out = result.stdout
    assert "DRY RUN" in out
    # 2 domains × 1 model × 2 samples = 4 total
    assert "4" in out
    assert "casual" in out
    assert "academic" in out
    assert "sonnet" in out
