"""Tests for evals/scripts/regex_scorer.py — deterministic AI-tell scorer."""
import pytest

from evals.scripts.regex_scorer import (
    PATTERNS_BY_LANG,
    PATTERNS_DE,
    PATTERNS_EN,
    THRESHOLD_PATTERNS,
    UNIVERSAL_MECHANICS_KEYS,
    clean_text,
    compare,
    density,
    get_patterns,
    rhythm_check,
    scan,
    score_text,
    tier1_total,
    word_count,
)


# ---------------------------------------------------------------------------
# Pattern catalogue + language registry
# ---------------------------------------------------------------------------

def test_patterns_en_registered():
    assert "en" in PATTERNS_BY_LANG
    assert PATTERNS_BY_LANG["en"] is PATTERNS_EN


def test_get_patterns_returns_en_pack():
    assert get_patterns("en") is PATTERNS_EN


def test_get_patterns_raises_for_unknown_lang():
    with pytest.raises(KeyError, match="unknown language pack"):
        get_patterns("xx")


def test_universal_mechanics_keys_present_in_en():
    for key in UNIVERSAL_MECHANICS_KEYS:
        assert key in PATTERNS_EN, f"universal mechanic {key} missing from PATTERNS_EN"


def test_threshold_patterns_reference_real_patterns():
    for key in THRESHOLD_PATTERNS:
        assert key in PATTERNS_EN, f"threshold for unknown pattern {key}"


# ---------------------------------------------------------------------------
# scan() — hit counting
# ---------------------------------------------------------------------------

def test_scan_detects_puffery():
    text = "This robust, seamless solution leverages cutting-edge technology."
    hits = scan(text, lang="en")
    assert hits["puffery"] >= 3  # robust, seamless, leverages, cutting-edge


def test_scan_detects_significance_inflation():
    text = "This marks a pivotal moment in the evolving landscape."
    hits = scan(text, lang="en")
    assert hits["significance_inflation"] >= 1


def test_scan_detects_em_dash():
    text = "The report — a long one — concluded."
    hits = scan(text, lang="en")
    assert hits["em_dash_overuse"] >= 2


def test_scan_skip_lang_specific_only_universal_mechanics_counted():
    text = "The report — with **bold** — uses puffery and robust language."
    hits = scan(text, lang="en", skip_lang_specific=True)
    # Universal still counted
    assert hits["em_dash_overuse"] > 0
    assert hits["boldface_overuse"] > 0
    # Language-specific zeroed
    assert hits["puffery"] == 0


# ---------------------------------------------------------------------------
# density() + tier1_total() + threshold logic
# ---------------------------------------------------------------------------

def test_density_zero_words():
    assert density(5, 0) == 0.0


def test_density_basic():
    assert density(3, 100) == 3.0
    assert density(1, 50) == 2.0


def test_tier1_total_threshold_pattern_under_threshold_excluded():
    # boldface_overuse threshold is 0.5/100w. 1 hit in 1000 words = 0.1 density → excluded
    hits = {"boldface_overuse": 1, "puffery": 2}
    assert tier1_total(hits, words=1000) == 2


def test_tier1_total_threshold_pattern_over_threshold_included():
    # 1 hit in 50 words = 2.0/100w → over 0.5 threshold → included
    hits = {"boldface_overuse": 1, "puffery": 2}
    assert tier1_total(hits, words=50) == 3


# ---------------------------------------------------------------------------
# clean_text()
# ---------------------------------------------------------------------------

def test_clean_text_strips_code_fences():
    text = "real text\n```python\ndef foo(): pass\n```\nmore real text"
    cleaned = clean_text(text)
    assert "def foo" not in cleaned
    assert "real text" in cleaned


def test_clean_text_strips_blockquotes():
    text = "real text\n> quoted AI output\n> more quoted\nmore real text"
    cleaned = clean_text(text)
    assert "quoted AI output" not in cleaned
    assert "real text" in cleaned


# ---------------------------------------------------------------------------
# word_count()
# ---------------------------------------------------------------------------

def test_word_count_basic():
    assert word_count("Hello world, this is five words.") == 6  # five → "five" + 5 visible


def test_word_count_handles_punctuation():
    assert word_count("") == 0
    assert word_count("a") == 1
    assert word_count("don't stop") == 2


# ---------------------------------------------------------------------------
# rhythm_check()
# ---------------------------------------------------------------------------

def test_rhythm_check_short_text_returns_na():
    r = rhythm_check("Short.")
    assert r["verdict"] == "n/a"


def test_rhythm_check_varied_text():
    text = (
        "Short. Then a much longer sentence that takes its time getting where it goes. "
        "Then medium. Tiny. And another sprawling complex one with multiple clauses and ideas."
    )
    r = rhythm_check(text)
    assert r["sentences"] >= 4
    assert "cv" in r


# ---------------------------------------------------------------------------
# score_text() — end-to-end
# ---------------------------------------------------------------------------

def test_score_text_ai_heavy_returns_high_verdict():
    text = (
        "This pivotal moment in the evolving landscape underscores the importance "
        "of leveraging robust, seamless, cutting-edge solutions. Moreover, this "
        "delves into the comprehensive ecosystem."
    )
    report = score_text(text, lang="en")
    assert report["lang"] == "en"
    assert report["tier1_total"] >= 3
    assert report["density_per_100w"] > 6  # HIGH verdict


def test_score_text_clean_human_returns_low_verdict():
    text = (
        "I spent the morning trying to convince my printer that it exists. "
        "The router knows. The printer knows. The laptop has decided otherwise."
    )
    report = score_text(text, lang="en")
    assert report["density_per_100w"] < 3  # LOW verdict
    assert "LOW" in report["verdict"]


def test_score_text_has_dimension_breakdown():
    text = "Pivotal moment in robust ecosystem. Moreover, delves comprehensively."
    report = score_text(text, lang="en")
    assert "dimensions" in report
    assert "Authenticity" in report["dimensions"]


def test_score_text_per_paragraph_breakdown():
    text = "First paragraph with robust language.\n\nSecond clean paragraph here."
    report = score_text(text, lang="en")
    assert len(report["per_paragraph"]) == 2


# ---------------------------------------------------------------------------
# compare()
# ---------------------------------------------------------------------------

def test_compare_detects_cleaning():
    input_text = "This pivotal moment leverages robust solutions."
    output_text = "This is important. We use solid tools."
    diff = compare(input_text, output_text, lang="en")
    assert diff["tier1_removed"] >= 1
    assert "patterns_cleaned" in diff


def test_compare_detects_regression():
    input_text = "Plain text without AI tells."
    output_text = "This pivotal moment leverages robust solutions."
    diff = compare(input_text, output_text, lang="en")
    assert diff["patterns_introduced"]


def test_compare_length_verdict_within_band():
    input_text = "Five words exactly here now."
    output_text = "Five words exactly there now."
    diff = compare(input_text, output_text, lang="en")
    assert "OK" in diff["length_verdict"]


def test_compare_length_verdict_truncated():
    input_text = " ".join(["word"] * 100)
    output_text = " ".join(["word"] * 40)
    diff = compare(input_text, output_text, lang="en")
    assert "TRUNCATED" in diff["length_verdict"]


# ---------------------------------------------------------------------------
# Catalogue extensions (humanizer-ext patterns #17, #19, #29, #34, #38, #39, #40, #6)
# ---------------------------------------------------------------------------

def test_curly_quotes_detected():
    text = "He said “hello” and walked away."
    hits = scan(text, lang="en")
    assert hits["curly_quotes"] >= 2  # opening + closing


def test_curly_quotes_skip_when_only_straight():
    text = 'He said "hello" and walked away.'
    hits = scan(text, lang="en")
    assert hits["curly_quotes"] == 0


def test_title_case_heading_detected():
    text = "## Strategic Negotiations And Global Partnerships\n\nBody text."
    hits = scan(text, lang="en")
    assert hits["title_case_heading"] >= 1


def test_title_case_heading_skip_sentence_case():
    text = "## Strategic negotiations and global partnerships\n\nBody text."
    hits = scan(text, lang="en")
    assert hits["title_case_heading"] == 0


def test_placeholder_text_detected_bracket():
    text = "Founded in [YEAR], [COMPANY NAME] is a leader."
    hits = scan(text, lang="en")
    assert hits["placeholder_text"] >= 2


def test_placeholder_text_detected_date_placeholder():
    text = "Accessed 2025-xx-xx by the user."
    hits = scan(text, lang="en")
    assert hits["placeholder_text"] >= 1


def test_reference_markup_artifact_chatgpt_token():
    text = "The election turn0search0 was close. Analysts said turn0news5 it was historic."
    hits = scan(text, lang="en")
    assert hits["reference_markup_artifact"] >= 2


def test_reference_markup_artifact_utm_chatgpt():
    text = "See the [report](https://example.com/r?utm_source=chatgpt.com) for details."
    hits = scan(text, lang="en")
    assert hits["reference_markup_artifact"] >= 1


def test_markdown_contamination_meta_prompt():
    text = "Here is the rewritten version. Would you like me to expand it further?"
    hits = scan(text, lang="en")
    assert hits["markdown_contamination"] >= 2


def test_trailing_emphasis_fragment_detected():
    text = "The system processes requests in under 50ms. That matters.\n"
    hits = scan(text, lang="en")
    assert hits["trailing_emphasis_fragment"] >= 1


def test_fragmented_header_detected():
    text = "## Performance\n\nSpeed matters.\n\nWhen users hit a slow page they leave.\n"
    hits = scan(text, lang="en")
    assert hits["fragmented_header"] >= 1


def test_challenges_section_heading_detected():
    text = "## Challenges and Legacy\n\nBody text follows."
    hits = scan(text, lang="en")
    assert hits["challenges_section"] >= 1


def test_challenges_section_despite_phrase_detected():
    text = "Despite these challenges, Korattur continues to thrive as part of Chennai."
    hits = scan(text, lang="en")
    assert hits["challenges_section"] >= 1


def test_new_patterns_registered_in_dimension_map_or_extensions_section():
    """All new pattern keys should be present in PATTERNS_EN (registry consistency)."""
    new_keys = [
        "curly_quotes", "title_case_heading", "placeholder_text",
        "reference_markup_artifact", "markdown_contamination",
        "trailing_emphasis_fragment", "fragmented_header", "challenges_section",
    ]
    for k in new_keys:
        assert k in PATTERNS_EN, f"new key {k} not registered in PATTERNS_EN"


# ---------------------------------------------------------------------------
# DE language pack — catalogue + registry
# ---------------------------------------------------------------------------

def test_patterns_de_registered():
    assert "de" in PATTERNS_BY_LANG
    assert PATTERNS_BY_LANG["de"] is PATTERNS_DE


def test_get_patterns_returns_de_pack():
    assert get_patterns("de") is PATTERNS_DE


def test_universal_mechanics_keys_present_in_de():
    for key in UNIVERSAL_MECHANICS_KEYS:
        assert key in PATTERNS_DE, f"universal mechanic {key} missing from PATTERNS_DE"


def test_threshold_patterns_reference_real_patterns():
    """Every THRESHOLD_PATTERNS key must exist in at least one registered pack."""
    all_keys = set()
    for pack in PATTERNS_BY_LANG.values():
        all_keys.update(pack.keys())
    for key in THRESHOLD_PATTERNS:
        assert key in all_keys, f"threshold for unknown pattern {key}"


# --- DE pattern firing tests ------------------------------------------------

def test_de_significance_inflation_fires():
    text = "Diese Initiative spielt eine entscheidende Rolle in der Entwicklung."
    hits = scan(text, lang="de")
    assert hits["de_significance_inflation"] >= 1


def test_de_puffery_fires():
    text = "Unsere Lösung verfügt über nahtlose und bahnbrechende Funktionen."
    hits = scan(text, lang="de")
    assert hits["de_puffery"] >= 2


def test_de_vague_attribution_fires():
    text = "Laut Experten und Branchenberichten hat die Entwicklung weitreichende Folgen."
    hits = scan(text, lang="de")
    assert hits["de_vague_attribution"] >= 1


def test_de_ai_vocab_fires():
    text = "Darüber hinaus bietet die ganzheitliche Lösung eine nachhaltige Grundlage."
    hits = scan(text, lang="de")
    assert hits["de_ai_vocab"] >= 2


def test_de_copula_avoidance_fires():
    text = "Die Bibliothek fungiert als zentraler Anlaufpunkt und gilt als kulturelles Herz."
    hits = scan(text, lang="de")
    assert hits["de_copula_avoidance"] >= 2


def test_de_sycophancy_fires():
    text = "Natürlich! Das ist eine sehr gute Frage. Vielen Dank für Ihre Frage!"
    hits = scan(text, lang="de")
    assert hits["de_sycophancy"] >= 2


def test_de_filler_fires():
    text = "Es ist wichtig zu beachten, dass die Daten das belegen. Ich hoffe, das hilft."
    hits = scan(text, lang="de")
    assert hits["de_filler"] >= 2


def test_de_signposting_fires():
    text = "Lassen Sie uns eintauchen, wie das System funktioniert."
    hits = scan(text, lang="de")
    assert hits["de_signposting"] >= 1


def test_de_sentence_opener_intensifier_fires():
    text = "Letztendlich, zählt vor allem die Umsetzung.\nTatsächlich, bestätigen die Daten das."
    hits = scan(text, lang="de")
    assert hits["de_sentence_opener_intensifier"] >= 2


def test_de_quantity_vagueness_fires():
    text = "Eine breite Palette von Faktoren trug zum Ergebnis bei. Zahlreiche Studien bestätigen das."
    hits = scan(text, lang="de")
    assert hits["de_quantity_vagueness"] >= 2


def test_de_academic_frame_fires():
    text = "Im Rahmen der vorliegenden Arbeit wird die Implementierung evaluiert."
    hits = scan(text, lang="de")
    assert hits["de_academic_frame"] >= 1


def test_de_impersonal_reflexive_fires():
    text = "Es lässt sich feststellen, dass die Ergebnisse positiv sind. Zusammenfassend lässt sich sagen, dass das System funktioniert."
    hits = scan(text, lang="de")
    assert hits["de_impersonal_reflexive"] >= 2


def test_de_denglisch_fires():
    text = "Wir alignen unsere Stakeholder, um Pain Points zu adressieren und Insights zu liefern."
    hits = scan(text, lang="de")
    assert hits["de_denglisch"] >= 2


def test_de_clean_prose_no_lang_specific_hits():
    """Clean, natural German prose should produce zero DE lang-specific hits."""
    text = (
        "Ich verbrachte den Morgen damit, mein Fahrrad zu reparieren. "
        "Die Kette war gerissen, was mich eine Stunde kostete. "
        "Danach fuhr ich zum Markt und kaufte Gemüse für das Abendessen."
    )
    hits = scan(text, lang="de")
    lang_specific_keys = [k for k in PATTERNS_DE if k not in UNIVERSAL_MECHANICS_KEYS]
    total_lang_specific = sum(hits.get(k, 0) for k in lang_specific_keys)
    assert total_lang_specific == 0, f"False positives on clean German: {hits}"


def test_chatbot_closer_fires_en():
    assert scan("That's the overview. Want me to continue?", lang="en")["chatbot_closer"] >= 1
    assert scan("Should I continue?", lang="en")["chatbot_closer"] >= 1
    assert scan("Want me to give examples?", lang="en")["chatbot_closer"] >= 1


def test_chatbot_closer_silent_on_ordinary_continue_en():
    assert scan("Prices continue to climb each year.", lang="en")["chatbot_closer"] == 0


def test_fake_candid_opener_fires_en():
    assert scan("Honestly? It depends on how often you use it.", lang="en")["fake_candid_opener"] >= 1
    assert scan("Look, the data is clear.", lang="en")["fake_candid_opener"] >= 1
    assert scan("Here's the thing, nobody actually checked.", lang="en")["fake_candid_opener"] >= 1


def test_fake_candid_opener_silent_mid_sentence_en():
    assert scan("I honestly think it works.", lang="en")["fake_candid_opener"] == 0
    assert scan("Take a look at the chart.", lang="en")["fake_candid_opener"] == 0


def test_de_chatbot_closer_fires():
    assert scan("Hier ist die Übersicht. Soll ich fortfahren?", lang="de")["de_chatbot_closer"] >= 1
    assert scan("Möchten Sie, dass ich das ausführe?", lang="de")["de_chatbot_closer"] >= 1
    assert scan("Soll ich Beispiele geben?", lang="de")["de_chatbot_closer"] >= 1

def test_de_fake_candid_opener_fires():
    assert scan("Mal ehrlich, das funktioniert selten.", lang="de")["de_fake_candid_opener"] >= 1
    assert scan("Ganz ehrlich? Es kommt darauf an.", lang="de")["de_fake_candid_opener"] >= 1
    assert scan("Die Sache ist die, dass niemand es geprüft hat.", lang="de")["de_fake_candid_opener"] >= 1

def test_de_fake_candid_opener_silent_on_legit_use():
    assert scan("Die Sache ist die Lösung des Problems.", lang="de")["de_fake_candid_opener"] == 0
    assert scan("In der Sache ist die Lage komplex.", lang="de")["de_fake_candid_opener"] == 0

def test_de_extension_keys_dont_break_clean_prose():
    text = ("Ich verbrachte den Morgen damit, mein Fahrrad zu reparieren. "
            "Die Kette war gerissen, was mich eine Stunde kostete.")
    hits = scan(text, lang="de")
    assert hits["de_chatbot_closer"] == 0
    assert hits["de_fake_candid_opener"] == 0


def test_aphorism_formula_fires_en():
    assert scan("Leadership is not a tool but a mirror of the team.", lang="en")["aphorism_formula"] >= 1
    assert scan("Efficiency becomes a trap when teams forget the human layer.", lang="en")["aphorism_formula"] >= 1

def test_aphorism_formula_silent_on_copula_and_soft_tells_en():
    assert scan("Tuesday is the busiest day of the week.", lang="en")["aphorism_formula"] == 0
    assert scan("The CEO is the head of the company.", lang="en")["aphorism_formula"] == 0
    assert scan("Water is the main component of the body.", lang="en")["aphorism_formula"] == 0
    assert scan("Diplomacy has a language of its own.", lang="en")["aphorism_formula"] == 0
    assert scan("The euro is the currency of nineteen countries.", lang="en")["aphorism_formula"] == 0

def test_de_aphorism_formula_fires():
    assert scan("Führung ist kein Werkzeug, sondern ein Spiegel des Teams.", lang="de")["de_aphorism_formula"] >= 1
    assert scan("Effizienz wird zur Falle, wenn Teams den Menschen vergessen.", lang="de")["de_aphorism_formula"] >= 1

def test_de_aphorism_formula_silent_on_fachsprache():
    assert scan("Die Sprache der Diplomatie ist subtil.", lang="de")["de_aphorism_formula"] == 0
    assert scan("Aufmerksamkeit ist die Währung der sozialen Medien.", lang="de")["de_aphorism_formula"] == 0

def test_de_aphorism_dont_break_clean_prose():
    text = ("Ich verbrachte den Morgen damit, mein Fahrrad zu reparieren. "
            "Die Kette war gerissen, was mich eine Stunde kostete.")
    assert scan(text, lang="de")["de_aphorism_formula"] == 0
