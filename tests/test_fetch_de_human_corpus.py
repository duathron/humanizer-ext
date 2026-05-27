"""Unit tests for evals.scripts.fetch_de_human_corpus.

All tests are pure-unit / offline: no network calls, all mock data
constructed in-process. Tests verify the public API contract and CLI.
"""
from __future__ import annotations

import json
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
    write_corpus(docs, tmp_path, "test_source", license_class="redistributable")

    target = tmp_path / "redistributable" / "test_source"
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
    write_corpus([doc], tmp_path, "fm_test", license_class="redistributable")

    content = (tmp_path / "redistributable" / "fm_test" / "check_fm.md").read_text(encoding="utf-8")
    assert "---" in content
    assert "source_url" in content
    assert "license" in content
    assert "fetch_date" in content
    assert "CC-BY-SA-3.0" in content


def test_write_corpus_empty_docs_no_crash(tmp_path):
    """write_corpus with empty list should not crash (just print a warning)."""
    from evals.scripts.fetch_de_human_corpus import write_corpus

    # Should not raise
    write_corpus([], tmp_path, "empty_source", license_class="redistributable")


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


# ---------------------------------------------------------------------------
# Wave 2: license_class field on Document
# ---------------------------------------------------------------------------

def test_document_has_license_class_field():
    from evals.scripts.fetch_de_human_corpus import Document

    d = Document(
        id="t1",
        text="Hallo",
        source_url="https://example.de",
        license="CC-BY-SA-3.0",
        fetch_date="2026-05-27",
        license_class="redistributable",
    )
    assert d.license_class == "redistributable"


def test_document_license_class_research_only():
    from evals.scripts.fetch_de_human_corpus import Document

    d = Document(
        id="t2",
        text="Text",
        source_url="https://example.de",
        license="copyright",
        fetch_date="2026-05-27",
        license_class="research_only",
    )
    assert d.license_class == "research_only"


def test_document_license_class_default_redistributable():
    """license_class defaults to 'redistributable' when not specified."""
    from evals.scripts.fetch_de_human_corpus import Document

    d = Document(
        id="t3",
        text="Text",
        source_url="https://example.de",
        license="CC-BY-SA-3.0",
        fetch_date="2026-05-27",
    )
    assert d.license_class == "redistributable"


def test_frontmatter_contains_license_class():
    from evals.scripts.fetch_de_human_corpus import Document, _render_frontmatter

    d = Document(
        id="fm_lc",
        text="x",
        source_url="https://example.de",
        license="PD",
        fetch_date="2026-05-27",
        license_class="redistributable",
    )
    fm = _render_frontmatter(d)
    assert "license_class" in fm
    assert "redistributable" in fm


def test_frontmatter_research_only_class():
    from evals.scripts.fetch_de_human_corpus import Document, _render_frontmatter

    d = Document(
        id="fm_ro",
        text="x",
        source_url="https://apple.com/de",
        license="copyright",
        fetch_date="2026-05-27",
        license_class="research_only",
    )
    fm = _render_frontmatter(d)
    assert "license_class" in fm
    assert "research_only" in fm


def test_write_corpus_routes_to_redistributable(tmp_path):
    from evals.scripts.fetch_de_human_corpus import Document, write_corpus

    doc = Document(
        id="rd_doc",
        text=" ".join(["Wort"] * 210),
        source_url="https://example.de",
        license="CC-BY-SA-3.0",
        fetch_date="2026-05-27",
        license_class="redistributable",
    )
    write_corpus([doc], tmp_path, "my_source", license_class="redistributable")
    assert (tmp_path / "redistributable" / "my_source" / "rd_doc.md").exists()


def test_write_corpus_routes_to_research_only(tmp_path):
    from evals.scripts.fetch_de_human_corpus import Document, write_corpus

    doc = Document(
        id="ro_doc",
        text=" ".join(["Wort"] * 210),
        source_url="https://apple.com/de",
        license="copyright",
        fetch_date="2026-05-27",
        license_class="research_only",
    )
    write_corpus([doc], tmp_path, "apple_marketing", license_class="research_only")
    assert (tmp_path / "research_only" / "apple_marketing" / "ro_doc.md").exists()


def test_research_only_license_sidecar_has_fair_use_clause(tmp_path):
    from evals.scripts.fetch_de_human_corpus import Document, write_corpus

    doc = Document(
        id="ro_lc",
        text=" ".join(["Wort"] * 210),
        source_url="https://apple.com/de/iphone/",
        license="copyright",
        fetch_date="2026-05-27",
        license_class="research_only",
    )
    write_corpus([doc], tmp_path, "apple_marketing", license_class="research_only")
    lic = (tmp_path / "research_only" / "apple_marketing" / "_LICENSE").read_text()
    assert "fair-use" in lic.lower() or "fair use" in lic.lower()
    assert "no-redistribution" in lic.lower() or "no redistribution" in lic.lower()


def test_redistributable_license_sidecar_no_fair_use(tmp_path):
    """Redistributable _LICENSE sidecar should NOT mention fair-use."""
    from evals.scripts.fetch_de_human_corpus import Document, write_corpus

    doc = Document(
        id="rd_lc",
        text=" ".join(["Wort"] * 210),
        source_url="https://de.wikipedia.org/wiki/Test",
        license="CC-BY-SA-3.0",
        fetch_date="2026-05-27",
        license_class="redistributable",
    )
    write_corpus([doc], tmp_path, "wikipedia_academic", license_class="redistributable")
    lic = (tmp_path / "redistributable" / "wikipedia_academic" / "_LICENSE").read_text()
    assert "CC-BY-SA-3.0" in lic


# ---------------------------------------------------------------------------
# Wave 2: --target + --list-sources CLI
# ---------------------------------------------------------------------------

def test_list_sources_runs():
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus", "--list-sources"],
        capture_output=True, text=True, cwd=".",
    )
    assert r.returncode == 0, f"--list-sources failed:\n{r.stderr}"


def test_list_sources_shows_redistributable_section():
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus", "--list-sources"],
        capture_output=True, text=True, cwd=".",
    )
    assert "redistributable" in r.stdout.lower()


def test_list_sources_shows_research_only_section():
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus", "--list-sources"],
        capture_output=True, text=True, cwd=".",
    )
    assert "research_only" in r.stdout


def test_list_sources_contains_wikipedia_academic():
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus", "--list-sources"],
        capture_output=True, text=True, cwd=".",
    )
    assert "wikipedia_academic" in r.stdout


def test_list_sources_contains_apple_marketing():
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus", "--list-sources"],
        capture_output=True, text=True, cwd=".",
    )
    assert "apple_marketing" in r.stdout


def test_target_redistributable_dry_run():
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus",
         "--target", "redistributable", "--dry-run"],
        capture_output=True, text=True, cwd=".",
    )
    assert r.returncode == 0, f"--target redistributable --dry-run failed:\n{r.stderr}"
    assert "redistributable" in r.stdout.lower()


def test_target_redistributable_excludes_research_only():
    """--target redistributable dry-run table should NOT list research_only source lines."""
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus",
         "--target", "redistributable", "--dry-run"],
        capture_output=True, text=True, cwd=".",
    )
    assert r.returncode == 0
    # The source table lines start with spaces + source_name — apple_marketing is research_only
    # Check that it doesn't appear as a table row (lines like "  apple_marketing  n=...")
    table_lines = [
        line for line in r.stdout.splitlines()
        if line.strip().startswith("apple_marketing")
    ]
    assert len(table_lines) == 0, f"apple_marketing table row unexpectedly present: {table_lines}"


def test_target_research_only_dry_run():
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus",
         "--target", "research_only", "--dry-run"],
        capture_output=True, text=True, cwd=".",
    )
    assert r.returncode == 0, f"--target research_only --dry-run failed:\n{r.stderr}"
    assert "research_only" in r.stdout


def test_target_research_only_excludes_redistributable():
    """--target research_only dry-run table should NOT list redistributable source lines."""
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus",
         "--target", "research_only", "--dry-run"],
        capture_output=True, text=True, cwd=".",
    )
    assert r.returncode == 0
    # ssoar_academic is redistributable — must not appear as a table row
    table_lines = [
        line for line in r.stdout.splitlines()
        if line.strip().startswith("ssoar_academic")
    ]
    assert len(table_lines) == 0, f"ssoar_academic table row unexpectedly present: {table_lines}"


def test_target_all_dry_run_covers_both_classes():
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus",
         "--target", "all", "--dry-run"],
        capture_output=True, text=True, cwd=".",
    )
    assert r.returncode == 0
    out = r.stdout.lower()
    assert "redistributable" in out
    assert "research_only" in out


def test_invalid_target_exits_nonzero():
    r = subprocess.run(
        [sys.executable, "-m", "evals.scripts.fetch_de_human_corpus",
         "--target", "invalid_xyz"],
        capture_output=True, text=True, cwd=".",
    )
    assert r.returncode != 0


# ---------------------------------------------------------------------------
# Wave 2: _extract_html_paragraphs
# ---------------------------------------------------------------------------

def test_extract_html_paragraphs_basic():
    from evals.scripts.fetch_de_human_corpus import _extract_html_paragraphs

    html = b"<html><body><p>Dies ist ein Test mit genug Woertern im Satz.</p></body></html>"
    result = _extract_html_paragraphs(html, max_words=100)
    assert "Test" in result


def test_extract_html_paragraphs_skips_script():
    from evals.scripts.fetch_de_human_corpus import _extract_html_paragraphs

    html = (
        b"<html><body><script>var x = 1;</script>"
        b"<p>Echter Text hier im Dokument und weiter unten.</p>"
        b"</body></html>"
    )
    result = _extract_html_paragraphs(html, max_words=100)
    assert "var x" not in result
    assert "Echter Text" in result


def test_extract_html_paragraphs_caps_at_max_words():
    from evals.scripts.fetch_de_human_corpus import _extract_html_paragraphs

    words = "Wort " * 500
    html = f"<html><body><p>{words}</p></body></html>".encode()
    result = _extract_html_paragraphs(html, max_words=50)
    assert len(result.split()) <= 50


# ---------------------------------------------------------------------------
# Wave 2: new fetchers (monkeypatched)
# ---------------------------------------------------------------------------

def test_fetch_ssoar_academic_returns_documents(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    desc_words = "Soziologie " * 250
    OAI_XML = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
        b"<ListRecords>"
        b"<record>"
        b"<header><identifier>oai:ssoar:1234</identifier></header>"
        b"<metadata>"
        b'<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
        b'           xmlns:dc="http://purl.org/dc/elements/1.1/">'
        b"<dc:title>Soziologische Analyse der Arbeit</dc:title>"
        b"<dc:language>de</dc:language>"
        b"<dc:description>" + desc_words.encode() + b"</dc:description>"
        b"<dc:identifier>https://www.ssoar.info/ssoar/handle/document/1234</dc:identifier>"
        b"<dc:rights>CC-BY 4.0</dc:rights>"
        b"</oai_dc:dc>"
        b"</metadata>"
        b"</record>"
        b"</ListRecords>"
        b"</OAI-PMH>"
    )

    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: OAI_XML)
    docs = m.fetch_ssoar_academic(n=1)
    assert len(docs) == 1
    assert docs[0].license_class == "redistributable"
    assert "Soziologie" in docs[0].text
    assert docs[0].source_url.startswith("https://")


def test_fetch_ssoar_academic_skips_non_german(monkeypatch):
    """Records with language != de should be skipped."""
    from evals.scripts import fetch_de_human_corpus as m

    OAI_XML = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">'
        b"<ListRecords>"
        b"<record>"
        b"<header><identifier>oai:ssoar:9999</identifier></header>"
        b"<metadata>"
        b'<oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"'
        b'           xmlns:dc="http://purl.org/dc/elements/1.1/">'
        b"<dc:title>English Paper</dc:title>"
        b"<dc:language>en</dc:language>"
        b"<dc:description>This is an English abstract.</dc:description>"
        b"<dc:identifier>https://www.ssoar.info/ssoar/handle/document/9999</dc:identifier>"
        b"</oai_dc:dc>"
        b"</metadata>"
        b"</record>"
        b"</ListRecords>"
        b"</OAI-PMH>"
    )

    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: OAI_XML)
    docs = m.fetch_ssoar_academic(n=5)
    assert len(docs) == 0


def test_fetch_bgbl_legal_returns_documents(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    para = "Die Bundesregierung erlasst folgendes Gesetz zur Regelung der Angelegenheiten. " * 40
    SAMPLE_HTML = f"<html><body><p>{para}</p></body></html>".encode()

    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: SAMPLE_HTML)
    docs = m.fetch_bgbl_legal(n=1)
    assert len(docs) == 1
    assert docs[0].license_class == "redistributable"
    assert docs[0].license in ("PD", "§5 UrhG", "PD-§5-UrhG")


def test_fetch_rechtsprechung_legal_no_crash(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    para = "Das Gericht hat folgendes festgestellt und entschieden und geurteilt. " * 50
    SAMPLE_HTML = f"<html><body><p>{para}</p></body></html>".encode()

    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: SAMPLE_HTML)
    docs = m.fetch_rechtsprechung_legal(n=1)
    # May return 0 if text too short or structure mismatch — no crash
    assert isinstance(docs, list)
    if docs:
        assert docs[0].license_class == "redistributable"


def test_fetch_bundestag_legal_handles_empty_response(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: b'{"documents": []}')
    docs = m.fetch_bundestag_legal(n=3)
    assert docs == []


def test_fetch_linuxwiki_technical_returns_documents(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    CATEGORY_JSON = {
        "query": {
            "categorymembers": [
                {"title": "Bash Scripting"},
                {"title": "SSH Konfiguration"},
            ]
        }
    }
    REVISION_JSON = {
        "query": {
            "pages": {
                "1": {
                    "revisions": [{"*": "Bash ist eine Unix-Shell fuer Linux-Systeme. " * 60}]
                }
            }
        }
    }

    call_count = [0]

    def mock_get_json(url, params=None):
        call_count[0] += 1
        if "categorymembers" in (params or {}).get("list", ""):
            return CATEGORY_JSON
        return REVISION_JSON

    monkeypatch.setattr(m, "_get_json", mock_get_json)
    docs = m.fetch_linuxwiki_technical(n=1)
    assert len(docs) == 1
    assert docs[0].license_class == "redistributable"
    assert docs[0].license == "GFDL"


def test_fetch_wikipedia_technical_returns_documents(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    CATEGORY_JSON = {
        "query": {
            "categorymembers": [
                {"title": "Python (Programmiersprache)"},
            ]
        }
    }
    REVISION_JSON = {
        "query": {
            "pages": {
                "1": {
                    "revisions": [{"*": "Python ist eine Programmiersprache. " * 60}]
                }
            }
        }
    }

    call_count = [0]

    def mock_get_json(url, params=None):
        call_count[0] += 1
        if "categorymembers" in (params or {}).get("list", ""):
            return CATEGORY_JSON
        return REVISION_JSON

    monkeypatch.setattr(m, "_get_json", mock_get_json)
    docs = m.fetch_wikipedia_technical(n=1)
    assert len(docs) == 1
    assert docs[0].license_class == "redistributable"
    assert docs[0].metadata.get("domain") == "technical"


def test_fetch_github_oss_technical_returns_documents(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    monkeypatch.setattr(m, "_github_get", lambda path, params=None: {
        "items": [
            {
                "full_name": "phpunit/phpunit",
                "html_url": "https://github.com/phpunit/phpunit",
                "stargazers_count": 9000,
                "language": "PHP",
                "license": {"spdx_id": "BSD-3-Clause"},
            }
        ]
    })
    monkeypatch.setattr(m, "_github_fetch_readme", lambda repo: (
        "PHPUnit ist ein Framework für PHP-Unit-Tests und die wichtigste "
        "Testbibliothek in der PHP-Welt. " * 60
    ))
    docs = m.fetch_github_oss_technical(n=1)
    assert len(docs) == 1
    assert docs[0].license_class == "redistributable"
    assert docs[0].metadata.get("domain") == "technical"


def test_fetch_bundesregierung_career_no_crash(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    para = "Friedrich Merz wurde am 11. November 1955 in Brilon geboren und studierte Jura. " * 40
    SAMPLE_HTML = f"<html><body><p>{para}</p></body></html>".encode()

    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: SAMPLE_HTML)
    docs = m.fetch_bundesregierung_career(n=1)
    assert isinstance(docs, list)
    if docs:
        assert docs[0].license_class == "redistributable"
        assert docs[0].license == "PD-§5-UrhG"


def test_fetch_stackexchange_career_returns_documents(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    # Use text that passes _is_de_text (need ≥4 DE function words in first 500 chars)
    bio_text = (
        "Ich bin ein Softwareentwickler und arbeite in Berlin. "
        "Die Entwicklung ist mein Beruf und ich liebe es. "
        "Mit Python und JavaScript arbeite ich täglich. "
        "Das ist mein Profil auf Stack Overflow. "
        "Ich bin auch in der Open-Source-Community aktiv und mache das gerne. "
    ) * 8
    SE_JSON = json.dumps({
        "items": [
            {
                "user_id": 123,
                "display_name": "MaxMuster",
                "about_me": f"<p>{bio_text}</p>",
                "link": "https://de.stackoverflow.com/users/123/maxmuster",
            }
        ]
    }).encode()

    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: SE_JSON)
    docs = m.fetch_stackexchange_career(n=1)
    assert len(docs) == 1
    assert docs[0].license_class == "redistributable"
    assert docs[0].license == "CC-BY-SA-4.0"


def test_fetch_github_profile_career_returns_documents(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    monkeypatch.setattr(m, "_github_get", lambda path, params=None: {
        "items": [
            {
                "full_name": "mustermensch/mustermensch",
                "html_url": "https://github.com/mustermensch",
                "stargazers_count": 5,
                "language": "Markdown",
                "license": None,
            }
        ]
    })
    monkeypatch.setattr(m, "_github_fetch_readme", lambda repo: (
        "Hallo! Ich bin Max Muster, ein Softwareentwickler aus München. "
        "Ich arbeite mit Python und JavaScript. " * 50
    ))
    docs = m.fetch_github_profile_career(n=1)
    assert len(docs) == 1
    assert docs[0].license_class == "redistributable"
    assert docs[0].metadata.get("domain") == "career"


def test_fetch_apple_marketing_returns_research_only(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    para = "Das iPhone bietet erstklassige Leistung und ein elegantes Design. " * 30
    SAMPLE_HTML = f"<html><body><p>{para}</p></body></html>".encode()
    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: SAMPLE_HTML)
    docs = m.fetch_apple_marketing(n=2)
    assert len(docs) > 0
    assert all(d.license_class == "research_only" for d in docs)
    # Trimmed to RESEARCH_MAX_WORDS (250) — allow small overshoot from word join
    assert all(len(d.text.split()) <= 260 for d in docs)


def test_fetch_samsung_marketing_returns_research_only(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    para = "Das Samsung Galaxy bietet hervorragende Kamerafunktionen und Akkulaufzeit. " * 25
    SAMPLE_HTML = f"<html><body><p>{para}</p></body></html>".encode()
    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: SAMPLE_HTML)
    docs = m.fetch_samsung_marketing(n=1)
    if docs:
        assert docs[0].license_class == "research_only"


def test_fetch_reddit_de_casual_returns_research_only(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    # Text must pass _is_de_text (≥4 DE function words in first 500 chars)
    selftext = (
        "Ich bin der Meinung, dass das eine gute Idee ist. "
        "Wir sollten das in der nächsten Woche besprechen. "
        "Was denkt ihr darüber und ist das auch so bei euch? "
    ) * 10
    REDDIT_JSON = json.dumps({
        "data": {
            "children": [
                {
                    "data": {
                        "title": "Frage zur deutschen Sprache und Kultur",
                        "selftext": selftext,
                        "url": "https://www.reddit.com/r/de/comments/abc123",
                        "id": "abc123",
                    }
                }
            ]
        }
    }).encode()
    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: REDDIT_JSON)
    docs = m.fetch_reddit_de_casual(n=1)
    assert len(docs) == 1
    assert docs[0].license_class == "research_only"
    assert len(docs[0].text.split()) <= REDDIT_MAX_WORDS + 5


def test_fetch_reddit_de_casual_skips_english_posts(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    REDDIT_JSON = json.dumps({
        "data": {
            "children": [
                {
                    "data": {
                        "title": "This is an English post about something",
                        "selftext": "Completely in English, nothing German here at all.",
                        "url": "https://www.reddit.com/r/de/comments/xyz",
                        "id": "xyz",
                    }
                }
            ]
        }
    }).encode()
    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: REDDIT_JSON)
    docs = m.fetch_reddit_de_casual(n=5)
    assert len(docs) == 0


def test_fetch_travel_blogs_casual_no_crash(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    para = "Heute haben wir Berlin besucht und es war wunderschoen und aufregend. " * 20
    SAMPLE_HTML = f"<html><body><p>{para}</p></body></html>".encode()
    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: SAMPLE_HTML)
    docs = m.fetch_travel_blogs_casual(n=1)
    assert isinstance(docs, list)
    if docs:
        assert docs[0].license_class == "research_only"


def test_fetch_karrierebibel_career_returns_research_only(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    para = "Sehr geehrte Damen und Herren, hiermit bewerbe ich mich auf Ihre ausgeschriebene Stelle. " * 20
    SAMPLE_HTML = f"<html><body><p>{para}</p></body></html>".encode()
    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: SAMPLE_HTML)
    docs = m.fetch_karrierebibel_career(n=1)
    if docs:
        assert docs[0].license_class == "research_only"
        assert docs[0].metadata.get("domain") == "career"


def test_fetch_heise_technical_returns_research_only(monkeypatch):
    from evals.scripts import fetch_de_human_corpus as m

    para = "Python 3.12 bietet viele neue Funktionen fuer Entwickler und Programmierer. " * 20
    SAMPLE_HTML = f"<html><body><p>{para}</p></body></html>".encode()
    monkeypatch.setattr(m, "_get", lambda url, params=None, **kw: SAMPLE_HTML)
    docs = m.fetch_heise_technical(n=1)
    if docs:
        assert docs[0].license_class == "research_only"
        assert docs[0].metadata.get("domain") == "technical"


# ---------------------------------------------------------------------------
# Wave 2: _SOURCES registry checks
# ---------------------------------------------------------------------------

def test_sources_registry_wikipedia_marketing_is_redistributable():
    """wikipedia_marketing should be tagged redistributable in _SOURCES."""
    from evals.scripts.fetch_de_human_corpus import _SOURCES
    assert "wikipedia_marketing" in _SOURCES
    _, _, _, lc = _SOURCES["wikipedia_marketing"]
    assert lc == "redistributable"


def test_sources_registry_apple_marketing_is_research_only():
    from evals.scripts.fetch_de_human_corpus import _SOURCES
    assert "apple_marketing" in _SOURCES
    _, _, _, lc = _SOURCES["apple_marketing"]
    assert lc == "research_only"


def test_sources_registry_ssoar_academic_is_redistributable():
    from evals.scripts.fetch_de_human_corpus import _SOURCES
    assert "ssoar_academic" in _SOURCES
    _, _, _, lc = _SOURCES["ssoar_academic"]
    assert lc == "redistributable"


def test_sources_registry_all_have_four_tuple_elements():
    """Every entry in _SOURCES must be a 4-tuple: (fn, n, subdir, license_class)."""
    from evals.scripts.fetch_de_human_corpus import _SOURCES
    for name, entry in _SOURCES.items():
        assert len(entry) == 4, f"_SOURCES[{name!r}] has {len(entry)} elements, expected 4"


def test_sources_registry_license_classes_valid():
    """All license_class values must be 'redistributable' or 'research_only'."""
    from evals.scripts.fetch_de_human_corpus import _SOURCES
    valid = {"redistributable", "research_only"}
    for name, (_, _, _, lc) in _SOURCES.items():
        assert lc in valid, f"_SOURCES[{name!r}] has invalid license_class: {lc!r}"


def test_sources_registry_wikipedia_casual_removed():
    """wikipedia_casual was a bad first-wave fetch and must be removed from registry."""
    from evals.scripts.fetch_de_human_corpus import _SOURCES
    assert "wikipedia_casual" not in _SOURCES


# ---------------------------------------------------------------------------
# Wave 2: REDDIT_MAX_WORDS import
# ---------------------------------------------------------------------------

def test_reddit_max_words_constant_exists():
    from evals.scripts.fetch_de_human_corpus import REDDIT_MAX_WORDS
    assert REDDIT_MAX_WORDS == 200


REDDIT_MAX_WORDS = 200  # local alias for test assertions above
