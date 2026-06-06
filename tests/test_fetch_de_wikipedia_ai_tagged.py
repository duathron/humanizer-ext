"""Unit tests for evals.scripts.fetch_de_wikipedia_ai_tagged.

All tests are pure-unit / offline: no network calls, no file I/O unless
testing the writer itself (which uses tmp_path). Tests verify the public API
contract, helper purity, and CLI smoke.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# _strip_wikitext (independent copy in the ai-tagged script)
# ---------------------------------------------------------------------------

def test_strip_wikitext_removes_links():
    from evals.scripts.fetch_de_wikipedia_ai_tagged import _strip_wikitext

    result = _strip_wikitext("[[Berlin|Hauptstadt]] von Deutschland.")
    assert "Berlin" in result
    assert "[[" not in result


def test_strip_wikitext_plain_link():
    from evals.scripts.fetch_de_wikipedia_ai_tagged import _strip_wikitext

    result = _strip_wikitext("Hauptstadt ist [[Berlin]].")
    assert "Berlin" in result
    assert "[[" not in result


def test_strip_wikitext_removes_templates():
    from evals.scripts.fetch_de_wikipedia_ai_tagged import _strip_wikitext

    result = _strip_wikitext("{{Infobox}} Echter Text.")
    assert "{{" not in result
    assert "Echter Text" in result


def test_strip_wikitext_removes_ref_tags():
    from evals.scripts.fetch_de_wikipedia_ai_tagged import _strip_wikitext

    result = _strip_wikitext("Ein Satz.<ref>Quelle: XY</ref> Noch ein Satz.")
    assert "<ref>" not in result
    assert "Ein Satz" in result


def test_strip_wikitext_removes_headings():
    from evals.scripts.fetch_de_wikipedia_ai_tagged import _strip_wikitext

    result = _strip_wikitext("== Abschnitt ==\nText darunter.")
    assert "==" not in result
    assert "Text darunter" in result


# ---------------------------------------------------------------------------
# _trim_to_words
# ---------------------------------------------------------------------------

def test_trim_to_words_returns_empty_if_too_short():
    from evals.scripts.fetch_de_wikipedia_ai_tagged import _trim_to_words

    short = " ".join(["Wort"] * 50)  # 50 words < MIN_WORDS (200)
    result = _trim_to_words(short)
    assert result == ""


def test_trim_to_words_caps_at_max():
    from evals.scripts.fetch_de_wikipedia_ai_tagged import _trim_to_words

    long_text = " ".join(["Wort"] * 1000)
    result = _trim_to_words(long_text, max_words=800)
    assert len(result.split()) == 800


def test_trim_to_words_passes_within_range():
    from evals.scripts.fetch_de_wikipedia_ai_tagged import _trim_to_words

    text = " ".join(["Wort"] * 300)  # 300 words — within 200–800
    result = _trim_to_words(text)
    assert len(result.split()) == 300


# ---------------------------------------------------------------------------
# Document dataclass
# ---------------------------------------------------------------------------

def test_document_fields_exist():
    from evals.scripts.fetch_de_wikipedia_ai_tagged import Document

    doc = Document(
        id="test_id",
        text="Testtext.",
        source_url="https://de.wikipedia.org/wiki/Test",
        license="CC-BY-SA-3.0",
        license_class="redistributable",
        fetch_date="2026-05-28",
        metadata={"source": "wikipedia_de_ki_generiert_tagged", "title": "Test"},
    )
    assert doc.id == "test_id"
    assert doc.license == "CC-BY-SA-3.0"
    assert doc.license_class == "redistributable"
    assert doc.metadata["source"] == "wikipedia_de_ki_generiert_tagged"


# ---------------------------------------------------------------------------
# _render_frontmatter + write_ai_corpus (offline, tmp_path)
# ---------------------------------------------------------------------------

def test_render_frontmatter_contains_required_fields():
    from evals.scripts.fetch_de_wikipedia_ai_tagged import Document, _render_frontmatter

    doc = Document(
        id="wiki_ki_testseite",
        text="Prosatext über KI.",
        source_url="https://de.wikipedia.org/wiki/Testseite",
        license="CC-BY-SA-3.0",
        license_class="redistributable",
        fetch_date="2026-05-28",
        metadata={"source": "wikipedia_de_ki_generiert_tagged", "title": "Testseite"},
    )
    fm = _render_frontmatter(doc)
    assert fm.startswith("---")
    assert "id:" in fm
    assert "source_url:" in fm
    assert "license:" in fm
    assert "fetch_date:" in fm
    assert "---" in fm


def test_write_ai_corpus_creates_files(tmp_path):
    from evals.scripts.fetch_de_wikipedia_ai_tagged import Document, write_ai_corpus

    # Generate enough words for MIN_WORDS=200
    prose = " ".join(["Wort"] * 210)
    docs = [
        Document(
            id="wiki_ki_test_artikel",
            text=prose,
            source_url="https://de.wikipedia.org/wiki/Test_Artikel",
            license="CC-BY-SA-3.0",
            license_class="redistributable",
            fetch_date="2026-05-28",
            metadata={"source": "wikipedia_de_ki_generiert_tagged", "title": "Test Artikel"},
        )
    ]
    write_ai_corpus(docs, tmp_path, "wikipedia_tagged")

    out = tmp_path / "wikipedia_tagged"
    assert out.is_dir()
    assert (out / "wiki_ki_test_artikel.md").exists()
    assert (out / "_LICENSE").exists()
    assert (out / "_SOURCE").exists()

    # LICENSE must reference CC-BY-SA
    lic = (out / "_LICENSE").read_text()
    assert "CC-BY-SA" in lic

    # SOURCE must have doc_count
    src = (out / "_SOURCE").read_text()
    assert "doc_count: 1" in src


def test_write_ai_corpus_empty_docs_no_crash(tmp_path):
    from evals.scripts.fetch_de_wikipedia_ai_tagged import write_ai_corpus

    # Should not raise; should print warning instead
    write_ai_corpus([], tmp_path, "wikipedia_tagged")
    # No files created
    out = tmp_path / "wikipedia_tagged"
    if out.exists():
        assert not (out / "_LICENSE").exists()


def test_write_ai_corpus_frontmatter_in_file(tmp_path):
    """Each written .md file starts with YAML frontmatter."""
    from evals.scripts.fetch_de_wikipedia_ai_tagged import Document, write_ai_corpus

    prose = " ".join(["Wort"] * 210)
    docs = [
        Document(
            id="wiki_ki_probe",
            text=prose,
            source_url="https://de.wikipedia.org/wiki/Probe",
            license="CC-BY-SA-3.0",
            license_class="redistributable",
            fetch_date="2026-05-28",
            metadata={"source": "wikipedia_de_ki_generiert_tagged", "title": "Probe"},
        )
    ]
    write_ai_corpus(docs, tmp_path, "wikipedia_tagged")

    content = (tmp_path / "wikipedia_tagged" / "wiki_ki_probe.md").read_text()
    assert content.startswith("---\n")
    assert "---" in content[4:]  # closing frontmatter delimiter


# ---------------------------------------------------------------------------
# CLI smoke tests (no network)
# ---------------------------------------------------------------------------

def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_wikipedia_ai_tagged", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "fetch_de_wikipedia_ai_tagged" in result.stdout
    assert "--n" in result.stdout
    assert "--dry-run" in result.stdout


def test_cli_dry_run():
    result = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_wikipedia_ai_tagged", "--dry-run"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    out = result.stdout
    assert "DRY RUN" in out
    assert "wikipedia_tagged" in out
    assert "CC-BY-SA" in out
    assert "$0" in out


def test_cli_dry_run_n_flag():
    """--n flag appears in dry-run output."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "evals.scripts.fetch_de_wikipedia_ai_tagged",
            "--dry-run",
            "--n",
            "10",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "10" in result.stdout
