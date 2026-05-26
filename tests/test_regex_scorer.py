"""Tests for evals/scripts/regex_scorer.py — deterministic AI-tell scorer."""
import pytest

from evals.scripts.regex_scorer import (
    PATTERNS_BY_LANG,
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
