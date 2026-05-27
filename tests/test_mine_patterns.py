"""Unit tests for evals.scripts.mine_patterns.

Pure unit tests over small fixture corpora — no I/O, no API calls, no
external dependencies beyond the stdlib + the module under test.
"""
from __future__ import annotations

import subprocess
import sys


# ---------------------------------------------------------------------------
# tokenize
# ---------------------------------------------------------------------------

def test_tokenize_strips_punctuation_and_lowercases():
    from evals.scripts.mine_patterns import tokenize
    assert tokenize("Hello, World! 2024.") == ["hello", "world"]


def test_tokenize_drops_single_chars_and_digits():
    from evals.scripts.mine_patterns import tokenize
    tokens = tokenize("a quick brown fox born 2024 in berlin")
    assert "a" not in tokens, f"single char 'a' should be dropped, got {tokens}"
    assert "2024" not in tokens, f"digit token '2024' should be dropped, got {tokens}"
    assert "berlin" in tokens


def test_tokenize_handles_empty_string():
    from evals.scripts.mine_patterns import tokenize
    assert tokenize("") == []


def test_tokenize_preserves_hyphenated_compounds():
    """Internal hyphens in compounds are not treated as punctuation boundaries."""
    from evals.scripts.mine_patterns import tokenize
    tokens = tokenize("KI-gestützten state-of-the-art")
    # After lower-casing and stripping edge punctuation these should survive
    assert "ki-gestützten" in tokens
    assert "state-of-the-art" in tokens


# ---------------------------------------------------------------------------
# ngrams
# ---------------------------------------------------------------------------

def test_ngrams_emits_contiguous_joined():
    from evals.scripts.mine_patterns import ngrams
    assert list(ngrams(["the", "quick", "brown", "fox"], n=2)) == [
        "the quick", "quick brown", "brown fox"
    ]
    assert list(ngrams(["the", "quick", "brown"], n=3)) == ["the quick brown"]


def test_ngrams_empty_when_too_short():
    from evals.scripts.mine_patterns import ngrams
    assert list(ngrams(["one", "two"], n=3)) == []
    assert list(ngrams([], n=2)) == []


# ---------------------------------------------------------------------------
# mine — core signal extraction
# ---------------------------------------------------------------------------

def test_mine_patterns_extracts_diff_signal():
    """A token clearly more common in AI corpus surfaces in candidates."""
    from evals.scripts.mine_patterns import mine

    ai = [
        "Im Rahmen von KI-gestützten Systemen wird zunehmend deutlich.",
        "Es lässt sich festhalten, dass im Rahmen dieser Untersuchung gilt.",
        "Im Rahmen der aktuellen Entwicklung steht fest.",
    ]
    human = [
        "Künstliche Intelligenz lernt aus Daten.",
        "Forscher untersuchten den Effekt detailliert.",
        "Die Studie zeigt klare Ergebnisse.",
    ]
    candidates = mine(ai, human, min_n=2, max_n=3, top_k=10, min_ai_count=2)
    ngrams_found = [c.ngram for c in candidates]
    assert any("im rahmen" in n for n in ngrams_found), (
        f"expected 'im rahmen' bigram in candidates, got {ngrams_found}"
    )
    # All candidates with ai_count >= human_count should have positive LLR
    assert all(c.llr > 0 for c in candidates if c.ai_count >= c.human_count)


def test_mine_respects_min_ai_count_filter():
    """Ngrams appearing only once in AI corpus should be filtered out."""
    from evals.scripts.mine_patterns import mine

    ai = ["unique singleton phrase", "common phrase example", "common phrase pattern"]
    human = ["totally different content here"]
    candidates = mine(ai, human, min_n=2, max_n=2, top_k=20, min_ai_count=2)
    ngrams_found = [c.ngram for c in candidates]
    assert "unique singleton" not in ngrams_found, (
        f"singleton ngram should be filtered; got {ngrams_found}"
    )
    assert "common phrase" in ngrams_found, (
        f"'common phrase' (count=2) should survive; got {ngrams_found}"
    )


def test_mine_handles_empty_corpora():
    from evals.scripts.mine_patterns import mine

    assert mine([], [], min_n=2, max_n=2, top_k=10) == []
    # Mining with only AI corpus (no human) still surfaces candidates.
    # Use min_ai_count=2 and a corpus where "common phrase" appears 3 times.
    ai_only = [
        "common phrase here",
        "common phrase again",
        "common phrase repeated",
    ]
    result = mine(ai_only, [], min_n=2, max_n=2, top_k=10, min_ai_count=2)
    assert result != [], "should mine candidates even when human corpus is empty"


def test_mine_handles_whitespace_only_docs():
    """Documents that tokenize to nothing don't break the miner."""
    from evals.scripts.mine_patterns import mine

    result = mine(["   ", "\n\n", "real content again real content"], [], min_n=2, max_n=2, top_k=5)
    # "real content" appears 2 times in doc 3 → count = 2, satisfies min_ai_count=3? No.
    # Use min_ai_count=2 to get at least one result.
    result2 = mine(["real content real content again content"], [], min_n=2, max_n=2, top_k=5, min_ai_count=2)
    assert isinstance(result2, list)


def test_llr_zero_when_ngram_balanced():
    """If an ngram appears with the same relative frequency, LLR should be ≈ 0."""
    from evals.scripts.mine_patterns import mine

    ai = ["common phrase one", "common phrase two", "common phrase three"]
    human = ["common phrase alpha", "common phrase beta", "common phrase gamma"]
    candidates = mine(ai, human, min_n=2, max_n=2, top_k=5, min_ai_count=2)
    cp = [c for c in candidates if c.ngram == "common phrase"]
    # "common phrase" has identical relative frequency in both corpora
    assert not cp or abs(cp[0].llr) < 1.0, (
        f"balanced ngram should have LLR ≈ 0, got {cp[0].llr if cp else 'not found'}"
    )


def test_mine_top_k_limits_output():
    """top_k correctly caps the output size."""
    from evals.scripts.mine_patterns import mine

    # Generate enough distinct bigrams so top_k matters.
    ai = [f"pattern alpha{i} beta{i} gamma{i}" for i in range(20)]
    human = ["completely different words here now"]
    candidates = mine(ai, human, min_n=2, max_n=2, top_k=5, min_ai_count=2)
    assert len(candidates) <= 5


def test_mine_candidates_sorted_by_llr_descending():
    """Candidates must be sorted by LLR descending."""
    from evals.scripts.mine_patterns import mine

    ai = [
        "im rahmen von systemen wird deutlich festgestellt",
        "im rahmen dieser untersuchung gilt festgestellt",
        "im rahmen der aktuellen entwicklung steht fest",
        "es lässt sich festhalten dass gilt",
        "es lässt sich festhalten dass entwicklung",
    ]
    human = [
        "die studie zeigt klare ergebnisse ohne jede einschränkung",
        "forscher untersuchten den effekt sehr detailliert",
    ]
    candidates = mine(ai, human, min_n=2, max_n=3, top_k=20, min_ai_count=2)
    if len(candidates) >= 2:
        for i in range(len(candidates) - 1):
            assert candidates[i].llr >= candidates[i + 1].llr, (
                f"candidates not sorted: [{i}].llr={candidates[i].llr} "
                f"< [{i+1}].llr={candidates[i+1].llr}"
            )


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

def test_cli_help():
    """CLI --help exits 0 and prints usage."""
    result = subprocess.run(
        [sys.executable, "-m", "evals.scripts.mine_patterns", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"--help exited non-zero: {result.stderr}"
    assert "mine_patterns" in result.stdout.lower() or "ai-corpus" in result.stdout.lower(), (
        f"Expected usage info in stdout, got: {result.stdout[:200]}"
    )
