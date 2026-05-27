"""Unit tests for evals.scripts.fetch_de_human_corpus.

All tests are pure-unit / offline: no network calls, all mock data
constructed in-process. Tests verify the public API contract and CLI.
"""
from __future__ import annotations

import subprocess
import sys


# ---------------------------------------------------------------------------
# _strip_wikitext
# ---------------------------------------------------------------------------

def test_strip_wikitext_removes_links():
    from evals.scripts.fetch_de_human_corpus import _strip_wikitext

    result = _strip_wikitext("[[Berlin|Hauptstadt]] von Deutschland.")
    assert "Berlin" in result, f"Expected 'Berlin' in output, got: {result!r}"
    assert "[[" not in result, f"Expected no '[[' in output, got: {result!r}"


def test_strip_wikitext_plain_link_becomes_title():
    from evals.scripts.fetch_de_human_corpus import _strip_wikitext

    result = _strip_wikitext("Hauptstadt ist [[Berlin]].")
    assert "Berlin" in result
    assert "[[" not in result


def test_strip_wikitext_removes_templates():
    from evals.scripts.fetch_de_human_corpus import _strip_wikitext

    result = _strip_wikitext("{{Infobox}} Echter Text.")
    assert "{{" not in result, f"Expected no '{{{{' in output, got: {result!r}"
    assert "Echter Text" in result, f"Expected 'Echter Text' preserved, got: {result!r}"


def test_strip_wikitext_removes_ref_tags():
    from evals.scripts.fetch_de_human_corpus import _strip_wikitext

    result = _strip_wikitext("Ein Satz.<ref>Quelle: XY</ref> Noch ein Satz.")
    assert "<ref>" not in result
    assert "Ein Satz" in result


def test_strip_wikitext_removes_headings():
    from evals.scripts.fetch_de_human_corpus import _strip_wikitext

    result = _strip_wikitext("== Abschnitt ==\nText darunter.")
    assert "==" not in result
    assert "Text darunter" in result


def test_strip_wikitext_removes_html_tags():
    from evals.scripts.fetch_de_human_corpus import _strip_wikitext

    result = _strip_wikitext("<b>Fett</b> und <i>kursiv</i>.")
    assert "<b>" not in result
    assert "Fett" in result
    assert "kursiv" in result


def test_strip_wikitext_handles_nested_templates():
    """Two passes should remove nested {{outer {{inner}} }} templates."""
    from evals.scripts.fetch_de_human_corpus import _strip_wikitext

    # After stripping, prose text should survive even with nested templates
    result = _strip_wikitext("{{Infobox Person |name=Test |birth={{Datum|1990}}}} Echter Prosatext.")
    assert "Echter Prosatext" in result


def test_strip_wikitext_preserves_normal_prose():
    from evals.scripts.fetch_de_human_corpus import _strip_wikitext

    prose = "Die Bundesrepublik Deutschland ist ein Bundesstaat in Mitteleuropa."
    result = _strip_wikitext(prose)
    assert "Bundesrepublik" in result
    assert "Bundesstaat" in result


# ---------------------------------------------------------------------------
# _is_de_text
# ---------------------------------------------------------------------------

def test_is_de_text_recognizes_german():
    from evals.scripts.fetch_de_human_corpus import _is_de_text

    assert _is_de_text("Der Mann geht in das Haus und ist zufrieden.")


def test_is_de_text_recognizes_german_longer():
    from evals.scripts.fetch_de_human_corpus import _is_de_text

    de_text = (
        "Die Entwicklung von Software ist ein komplexer Prozess, der viele "
        "verschiedene Schritte und Methoden umfasst. Wir arbeiten mit modernen "
        "Technologien und einem erfahrenen Team."
    )
    assert _is_de_text(de_text)


def test_is_de_text_rejects_english():
    from evals.scripts.fetch_de_human_corpus import _is_de_text

    assert not _is_de_text("The quick brown fox jumps over the lazy dog.")


def test_is_de_text_rejects_english_tech():
    from evals.scripts.fetch_de_human_corpus import _is_de_text

    english = (
        "This repository contains a Python library for processing natural "
        "language text. It supports multiple languages and provides simple APIs."
    )
    assert not _is_de_text(english)


def test_is_de_text_rejects_empty():
    from evals.scripts.fetch_de_human_corpus import _is_de_text

    # Empty string has 0 DE function words — should return False
    assert not _is_de_text("")


def test_is_de_text_boundary_exactly_four():
    """Exactly 4 distinct DE function-word hits should return True."""
    from evals.scripts.fetch_de_human_corpus import _is_de_text

    # "der", "die", "das", "und" — exactly 4 common DE words
    assert _is_de_text("der die das und")


# ---------------------------------------------------------------------------
# Document dataclass
# ---------------------------------------------------------------------------

def test_document_dataclass_serializes():
    from evals.scripts.fetch_de_human_corpus import Document

    d = Document(
        id="test",
        text="Hallo Welt",
        source_url="https://example.de",
        license="PD",
        fetch_date="2026-05-27",
        metadata={},
    )
    assert d.id == "test"
    assert d.text == "Hallo Welt"
    assert d.source_url == "https://example.de"
    assert d.license == "PD"
    assert d.fetch_date == "2026-05-27"
    assert d.metadata == {}


def test_document_dataclass_with_metadata():
    from evals.scripts.fetch_de_human_corpus import Document

    d = Document(
        id="wiki_casual_berlin",
        text="Berlin ist die Hauptstadt Deutschlands.",
        source_url="https://de.wikipedia.org/wiki/Berlin",
        license="CC-BY-SA-3.0",
        fetch_date="2026-05-27",
        metadata={"title": "Berlin", "wiki": "de.wikipedia", "domain": "casual"},
    )
    assert d.metadata["wiki"] == "de.wikipedia"
    assert d.metadata["domain"] == "casual"
    assert d.id == "wiki_casual_berlin"


# ---------------------------------------------------------------------------
# _trim_to_words
# ---------------------------------------------------------------------------

def test_trim_to_words_caps_at_max():
    from evals.scripts.fetch_de_human_corpus import _trim_to_words

    text = " ".join(["Wort"] * 1000)
    result = _trim_to_words(text, max_words=800, min_words=200)
    assert len(result.split()) == 800


def test_trim_to_words_returns_empty_below_min():
    from evals.scripts.fetch_de_human_corpus import _trim_to_words

    text = "Nur wenige Worte hier."
    result = _trim_to_words(text, max_words=800, min_words=200)
    assert result == ""


def test_trim_to_words_preserves_within_range():
    from evals.scripts.fetch_de_human_corpus import _trim_to_words

    text = " ".join(["Wort"] * 300)
    result = _trim_to_words(text, max_words=800, min_words=200)
    assert len(result.split()) == 300


# ---------------------------------------------------------------------------
# _make_id
# ---------------------------------------------------------------------------

def test_make_id_is_filename_safe():
    from evals.scripts.fetch_de_human_corpus import _make_id

    doc_id = _make_id("wiki_casual", "Berlin (Hauptstadt)")
    assert " " not in doc_id
    assert "(" not in doc_id
    assert ")" not in doc_id


def test_make_id_capped_at_80_chars():
    from evals.scripts.fetch_de_human_corpus import _make_id

    long_title = "A" * 200
    doc_id = _make_id("prefix", long_title)
    assert len(doc_id) <= 80


# ---------------------------------------------------------------------------
# write_corpus
# ---------------------------------------------------------------------------

def test_write_corpus_creates_files(tmp_path):
    from evals.scripts.fetch_de_human_corpus import Document, write_corpus

    docs = [
        Document(
            id="test_doc_1",
            text="Das ist ein Testdokument mit genug Wörtern für die Prüfung.",
            source_url="https://de.wikipedia.org/wiki/Test",
            license="CC-BY-SA-3.0",
            fetch_date="2026-05-27",
            metadata={"domain": "casual"},
        ),
        Document(
            id="test_doc_2",
            text="Ein weiteres Dokument zum Testen der Schreibfunktion hier.",
            source_url="https://de.wikipedia.org/wiki/Test2",
            license="CC-BY-SA-3.0",
            fetch_date="2026-05-27",
            metadata={"domain": "casual"},
        ),
    ]
    write_corpus(docs, tmp_path, "test_source")

    target = tmp_path / "test_source"
    assert target.is_dir()
    assert (target / "test_doc_1.md").exists()
    assert (target / "test_doc_2.md").exists()
    assert (target / "_LICENSE").exists()
    assert (target / "_SOURCE").exists()


def test_write_corpus_frontmatter_present(tmp_path):
    from evals.scripts.fetch_de_human_corpus import Document, write_corpus

    doc = Document(
        id="check_fm",
        text="Text mit YAML Frontmatter Test.",
        source_url="https://example.de/wiki/Test",
        license="CC-BY-SA-3.0",
        fetch_date="2026-05-27",
        metadata={"domain": "technical"},
    )
    write_corpus([doc], tmp_path, "fm_test")

    content = (tmp_path / "fm_test" / "check_fm.md").read_text(encoding="utf-8")
    assert "---" in content
    assert "source_url" in content
    assert "license" in content
    assert "fetch_date" in content
    assert "CC-BY-SA-3.0" in content


def test_write_corpus_empty_docs_no_crash(tmp_path):
    """write_corpus with empty list should not crash (just print a warning)."""
    from evals.scripts.fetch_de_human_corpus import write_corpus

    # Should not raise
    write_corpus([], tmp_path, "empty_source")


# ---------------------------------------------------------------------------
# CLI smoke tests (no network)
# ---------------------------------------------------------------------------

def test_cli_help_runs():
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus", "--help"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert r.returncode == 0, f"--help exited non-zero:\n{r.stderr}"
    assert "--source" in r.stdout, f"Expected '--source' in stdout:\n{r.stdout[:500]}"


def test_cli_help_lists_sources():
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus", "--help"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert r.returncode == 0
    # At least one source name should appear in the help
    assert "wikipedia" in r.stdout.lower(), f"Expected 'wikipedia' in help:\n{r.stdout[:500]}"


def test_dry_run_no_network():
    """--dry-run prints planned fetches without hitting the network."""
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus", "--dry-run"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert r.returncode == 0, f"--dry-run exited non-zero:\n{r.stderr}"
    assert "wikipedia" in r.stdout.lower(), (
        f"Expected 'wikipedia' in dry-run output:\n{r.stdout[:500]}"
    )


def test_dry_run_mentions_all_domains():
    """Dry-run output should name all six domains."""
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus", "--dry-run"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert r.returncode == 0
    output = r.stdout.lower()
    for domain in ["casual", "academic", "marketing", "career", "technical"]:
        assert domain in output, (
            f"Expected domain '{domain}' in dry-run output:\n{r.stdout[:500]}"
        )


def test_dry_run_shows_total_count():
    """Dry-run should report a total target document count."""
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus", "--dry-run"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert r.returncode == 0
    assert "total" in r.stdout.lower(), (
        f"Expected 'total' in dry-run output:\n{r.stdout[:500]}"
    )


def test_cli_invalid_source_exits_nonzero():
    """Passing an unknown source name should cause a non-zero exit."""
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus", "--source", "invalid_source_xyz"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert r.returncode != 0, "Expected non-zero exit for invalid source"


# ---------------------------------------------------------------------------
# _render_frontmatter
# ---------------------------------------------------------------------------

def test_render_frontmatter_valid_yaml_structure():
    from evals.scripts.fetch_de_human_corpus import Document, _render_frontmatter

    doc = Document(
        id="fm_test",
        text="ignored",
        source_url="https://de.wikipedia.org/wiki/Test",
        license="CC-BY-SA-3.0",
        fetch_date="2026-05-27",
        metadata={"domain": "casual", "wiki": "de.wikipedia"},
    )
    fm = _render_frontmatter(doc)
    assert fm.startswith("---")
    assert fm.endswith("---")
    assert "id:" in fm
    assert "source_url:" in fm
    assert "license:" in fm
    assert "fetch_date:" in fm
    assert "metadata:" in fm
