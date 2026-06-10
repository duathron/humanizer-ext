"""Locks the SP3b corpus fix: the EN true-negative set must contain ONLY
genuinely-clean human text, never the skill's own AI-tell Before-examples."""
from pathlib import Path
from evals.scripts._shared import load_pattern_corpus

REPO_ROOT = Path(__file__).parent.parent
EN_PATTERNS = REPO_ROOT / "evals" / "corpus" / "en" / "patterns"


def test_converted_detection_cases_have_expected_changes():
    """The converted true-neg rows are scorable detection cases with their tell terms.
    Task-5 validation (--runs 5): 008/014_001 majority-detect 5/5; 014_002/015 4/5.
    013 + 009_003 are KEPT detection cases but the skill REFUSES these short inputs
    (the deferred force_full-short-input bug), so under the scorer-refusal-guard they
    score `inconclusive` (refusal→None run), NOT a false detection — their earlier
    "5/5" was a refusal artifact (see docs/plans/sp3b-notes.md "RESOLVED 2026-06-10").
    pattern_029_en_001 was DELETED (1/5 — contested #29 tell, see pattern_029.json note).
    This test locks corpus SHAPE (label + expected_changes + term-in-input), not runtime detection."""
    cases = {c.id: c for c in load_pattern_corpus(EN_PATTERNS)}
    expect = {
        "pattern_008_en_001": ["serves as", "boasts"],
        "pattern_009_en_003": ["rather than to impress"],
        "pattern_013_en_001": ["are preserved automatically"],
        "pattern_014_en_001": ["—"],
        "pattern_014_en_002": ["—"],
        "pattern_015_en_001": ["(Objectives and Key Results)"],
    }
    # pattern_029_en_001 deleted (Task-5 1/5 miss, contested tell) — must be gone
    assert "pattern_029_en_001" not in cases
    for cid, terms in expect.items():
        assert cid in cases, f"{cid} missing"
        assert cases[cid].true_negative is False
        assert cases[cid].expected_changes == terms
        # each term must be present in the input (else unscorable)
        low = cases[cid].input.lower()
        for t in terms:
            assert t.lower() in low, f"{t!r} not in {cid} input"


def test_only_pattern_019_is_true_negative():
    """After SP3b, pattern_019 is the lone genuine true-neg; the 8 skill-own-example
    rows are converted to detection or deleted — none remain true_negative."""
    tn = {c.id for c in load_pattern_corpus(EN_PATTERNS) if c.true_negative}
    assert tn == {"pattern_019_en_001"}, f"unexpected true_negative set: {tn}"
