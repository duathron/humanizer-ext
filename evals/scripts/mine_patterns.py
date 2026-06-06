"""Empirical ngram miner for AI-pattern discovery.

Surfaces candidate ngrams that distinguish an AI-generated corpus from a
human-written corpus using log-likelihood-ratio (Dunning 1993). Language-
agnostic: tokenization is whitespace + punctuation splitting; no language-
specific resources required.

Usage (CLI):
    python -m evals.scripts.mine_patterns \\
        --ai-corpus evals/corpus/de/ai \\
        --human-corpus evals/corpus/de/human \\
        --lang de --top 50 [--min-n 2] [--max-n 4] [--min-count 3] \\
        [--format json|tsv]

Public API (importable):
    mine(ai_corpus, human_corpus, ...) -> list[Candidate]
    tokenize(text) -> list[str]
    ngrams(tokens, n) -> Iterator[str]

Python 3.11+, stdlib only (no new deps beyond what pyproject.toml already
lists — rapidfuzz is imported in run_pattern_eval.py, not here).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Punctuation chars to strip from token edges. We use a compiled regex so
# the hot-path (tokenize) avoids repeated re.compile overhead.
_PUNCT_STRIP_RE = re.compile(r"^[^\w]+|[^\w]+$", re.UNICODE)

# Single-char Unicode emoji that *are* meaningful tokens even at length 1.
# We allow these through the single-char filter. This list covers the most
# common AI-tell emojis (same set as the regex_scorer emoji_bullet pattern).
_ALLOWED_SINGLE_CHARS: frozenset[str] = frozenset(
    "✅✨⭐🌟🚀🎉⚡🔍💡🎯📊📝📌🔥👍💯✔️☑️🔹🔸"
)

# Extensions we ingest from corpus directories.
_INGEST_EXTENSIONS: frozenset[str] = frozenset({".md", ".txt", ".json"})


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------

@dataclass
class Candidate:
    """One ranked ngram candidate surfaced by the miner.

    Fields:
        ngram       -- space-joined lowercase tokens (e.g. "im rahmen")
        n           -- ngram order (1 = unigram, 2 = bigram, …)
        ai_count    -- raw count in the AI corpus
        human_count -- raw count in the human corpus
        ai_freq     -- occurrences per million tokens in the AI corpus
        human_freq  -- occurrences per million tokens in the human corpus
        llr         -- signed log-likelihood ratio (Dunning 1993);
                       positive = favors AI corpus, negative = favors human
    """

    ngram: str
    n: int
    ai_count: int
    human_count: int
    ai_freq: float
    human_freq: float
    llr: float


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

def tokenize(text: str) -> list[str]:
    """Lowercase, split on whitespace + punctuation, drop noise tokens.

    Dropped:
    - Pure-digit strings ("2024", "42")
    - Single-character strings unless they are a meaningful Unicode emoji
      in ``_ALLOWED_SINGLE_CHARS``

    The function does NOT require any language-specific resource; it is
    intentionally language-agnostic so the miner can be reused for DE/FR/ES.
    """
    tokens: list[str] = []
    for raw in text.lower().split():
        # Strip leading/trailing punctuation (preserves internal apostrophes,
        # hyphens in compounds, etc.)
        tok = _PUNCT_STRIP_RE.sub("", raw)
        if not tok:
            continue
        # Drop pure-digit tokens
        if tok.isdigit():
            continue
        # Drop single-char tokens unless they are a meaningful emoji
        if len(tok) == 1 and tok not in _ALLOWED_SINGLE_CHARS:
            continue
        tokens.append(tok)
    return tokens


# ---------------------------------------------------------------------------
# Ngram generation
# ---------------------------------------------------------------------------

def ngrams(tokens: list[str], n: int) -> Iterator[str]:
    """Yield contiguous ngrams of order *n* joined by a single space.

    Example::

        list(ngrams(["the", "quick", "brown", "fox"], n=2))
        # -> ["the quick", "quick brown", "brown fox"]
    """
    for i in range(len(tokens) - n + 1):
        yield " ".join(tokens[i : i + n])


# ---------------------------------------------------------------------------
# Log-likelihood ratio (Dunning 1993)
# ---------------------------------------------------------------------------

def _llr_signed(
    a: int,
    b: int,
    total_ai: int,
    total_human: int,
) -> float:
    """Compute signed LLR for a single ngram.

    Parameters
    ----------
    a:            count of ngram in AI corpus
    b:            count of ngram in human corpus
    total_ai:     total token count of AI corpus
    total_human:  total token count of human corpus

    Sign convention (Dunning + direction):
        positive LLR  => ngram favors AI corpus
        negative LLR  => ngram favors human corpus

    Edge cases handled:
    - a == 0: LLR = 0 (we never call this branch, but defined for safety)
    - b == 0: use the one-sided formula  2 * a * log(a / E_ai)
    - E_ai or E_human ≤ 0 (degenerate corpus): returns 0
    """
    N = total_ai + total_human
    if N == 0 or a == 0:
        return 0.0

    c = total_ai - a
    d = total_human - b

    # Clamp to avoid division by zero / log(0) in degenerate corpora.
    # If E_ai <= 0 the formula is undefined; return 0 as a safe fallback.
    E_ai = (a + b) * (a + c) / N
    E_human = (a + b) * (b + d) / N

    if E_ai <= 0:
        return 0.0

    # Unsigned LLR
    if b == 0 or E_human <= 0:
        llr_unsigned = 2.0 * a * math.log(a / E_ai)
    else:
        llr_unsigned = 2.0 * (
            a * math.log(a / E_ai) + b * math.log(b / E_human)
        )

    # Sign: positive when ngram is proportionally more common in AI corpus.
    ai_rate = a / total_ai
    human_rate = b / total_human if total_human > 0 else 0.0
    sign = 1 if ai_rate >= human_rate else -1
    return sign * llr_unsigned


# ---------------------------------------------------------------------------
# Core mining function
# ---------------------------------------------------------------------------

def mine(
    ai_corpus: list[str],
    human_corpus: list[str],
    *,
    min_n: int = 2,
    max_n: int = 4,
    top_k: int = 50,
    min_ai_count: int = 3,
) -> list[Candidate]:
    """Mine candidate ngrams that distinguish *ai_corpus* from *human_corpus*.

    The miner:
    1. Tokenizes every document in each corpus (``tokenize``).
    2. Builds ``Counter``s for every ngram order in ``[min_n, max_n]``.
    3. Computes signed LLR for every ngram that appears at least
       ``min_ai_count`` times in the AI corpus.
    4. Returns the top ``top_k`` candidates ranked by LLR descending
       (most AI-favoring first).

    Calling with empty corpora returns ``[]`` immediately.
    """
    if not ai_corpus and not human_corpus:
        return []

    # Tokenize corpora
    ai_tokens: list[str] = []
    for doc in ai_corpus:
        ai_tokens.extend(tokenize(doc))

    human_tokens: list[str] = []
    for doc in human_corpus:
        human_tokens.extend(tokenize(doc))

    total_ai = len(ai_tokens)
    total_human = len(human_tokens)

    # If both corpora tokenise to nothing, bail out.
    if total_ai == 0 and total_human == 0:
        return []

    # Build ngram counters per order
    ai_counts: Counter[str] = Counter()
    human_counts: Counter[str] = Counter()

    for n in range(min_n, max_n + 1):
        ai_counts.update(ngrams(ai_tokens, n))
        human_counts.update(ngrams(human_tokens, n))

    # Score candidates: only ngrams with ai_count >= min_ai_count
    candidates: list[Candidate] = []

    # Iterate over every ngram that appears in the AI corpus with enough count.
    # We also need to handle the edge case where total_human == 0 (no human
    # corpus given) — the LLR formula still produces a positive value for any
    # ngram present in the AI corpus since b == 0.
    ppm_ai_denom = total_ai / 1_000_000 if total_ai > 0 else 1.0
    ppm_human_denom = total_human / 1_000_000 if total_human > 0 else 1.0

    for gram, ai_c in ai_counts.items():
        if ai_c < min_ai_count:
            continue
        n = gram.count(" ") + 1
        human_c = human_counts.get(gram, 0)
        llr = _llr_signed(ai_c, human_c, total_ai, total_human)
        candidates.append(
            Candidate(
                ngram=gram,
                n=n,
                ai_count=ai_c,
                human_count=human_c,
                ai_freq=round(ai_c / ppm_ai_denom, 2),
                human_freq=round(human_c / ppm_human_denom, 2),
                llr=round(llr, 6),
            )
        )

    # Rank by LLR descending; break ties by ai_count descending
    candidates.sort(key=lambda c: (-c.llr, -c.ai_count))
    return candidates[:top_k]


# ---------------------------------------------------------------------------
# Corpus ingestion from directories
# ---------------------------------------------------------------------------

_YAML_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def _strip_yaml_frontmatter(text: str) -> str:
    """Strip leading YAML frontmatter block (between ``---`` fences at the
    top of the file). Returns text unchanged if no frontmatter is detected.

    Added 2026-05-28: corpus files written by the fetcher / generator scripts
    include rich YAML metadata (id, license_class, source, model, fetch_date,
    etc.). Without stripping, mining surfaces metadata tokens (``redistributable``,
    ``sonnet``, ``model opus``, ``fetch_date 2026-05-28``) as top-ranked
    "AI tells" — which they obviously are not.
    """
    return _YAML_FRONTMATTER_RE.sub("", text, count=1)


def _read_corpus_dir(corpus_dir: Path) -> list[str]:
    """Recursively read text from all eligible files in *corpus_dir*.

    File types:
    - ``.txt`` / ``.md``: returned verbatim (YAML frontmatter stripped if present).
    - ``.json``: if the parsed object has an ``"input"`` key, that value is
      used (matches ``evals/corpus/<lang>/e2e/*.json`` schema); otherwise the
      entire file text is used.

    Files whose name starts with ``_`` (sidecar files like ``_LICENSE``,
    ``_SOURCE``) are skipped.
    """
    docs: list[str] = []
    for path in sorted(corpus_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in _INGEST_EXTENSIONS:
            continue
        if path.name.startswith("_"):
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix == ".json":
            try:
                obj = json.loads(raw)
                if isinstance(obj, dict) and "input" in obj:
                    raw = str(obj["input"])
                # else fall through and use the whole text
            except json.JSONDecodeError:
                pass  # malformed JSON — treat as plain text
        else:
            raw = _strip_yaml_frontmatter(raw)
        docs.append(raw)
    return docs


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def _format_tsv(candidates: list[Candidate]) -> str:
    """Human-readable TSV. Header row + one row per candidate."""
    header = "\t".join(
        ["rank", "ngram", "n", "ai_count", "human_count",
         "ai_freq_ppm", "human_freq_ppm", "llr"]
    )
    rows = [header]
    for rank, c in enumerate(candidates, 1):
        rows.append(
            "\t".join(
                [
                    str(rank),
                    c.ngram,
                    str(c.n),
                    str(c.ai_count),
                    str(c.human_count),
                    str(c.ai_freq),
                    str(c.human_freq),
                    f"{c.llr:.4f}",
                ]
            )
        )
    return "\n".join(rows)


def _format_json(candidates: list[Candidate]) -> str:
    """Structured JSON output with full Candidate fields."""
    payload = [
        {
            "rank": rank,
            "ngram": c.ngram,
            "n": c.n,
            "ai_count": c.ai_count,
            "human_count": c.human_count,
            "ai_freq_ppm": c.ai_freq,
            "human_freq_ppm": c.human_freq,
            "llr": c.llr,
        }
        for rank, c in enumerate(candidates, 1)
    ]
    return json.dumps(payload, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mine_patterns",
        description=(
            "Mine candidate ngrams that distinguish an AI corpus from a human "
            "corpus using log-likelihood ratio (Dunning 1993). Language-agnostic."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  python -m evals.scripts.mine_patterns \\\n"
            "      --ai-corpus evals/corpus/de/ai \\\n"
            "      --human-corpus evals/corpus/de/human \\\n"
            "      --lang de --top 50 --format tsv\n"
        ),
    )
    parser.add_argument(
        "--ai-corpus",
        required=True,
        metavar="DIR",
        help="Directory of AI-generated text files (.md, .txt, .json).",
    )
    parser.add_argument(
        "--human-corpus",
        required=True,
        metavar="DIR",
        help="Directory of human-written text files (.md, .txt, .json).",
    )
    parser.add_argument(
        "--lang",
        default="de",
        help="Language tag for logging/output metadata (default: de).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=50,
        metavar="K",
        help="Number of top candidates to return (default: 50).",
    )
    parser.add_argument(
        "--min-n",
        type=int,
        default=2,
        metavar="N",
        help="Minimum ngram order to mine (default: 2).",
    )
    parser.add_argument(
        "--max-n",
        type=int,
        default=4,
        metavar="N",
        help="Maximum ngram order to mine (default: 4).",
    )
    parser.add_argument(
        "--min-count",
        type=int,
        default=3,
        metavar="C",
        help="Minimum AI corpus count for a candidate to be considered (default: 3).",
    )
    parser.add_argument(
        "--format",
        choices=["tsv", "json"],
        default="tsv",
        help="Output format: tsv (default, human-readable) or json (structured).",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    ai_dir = Path(args.ai_corpus)
    human_dir = Path(args.human_corpus)

    if not ai_dir.is_dir():
        parser.error(f"--ai-corpus is not a directory: {ai_dir}")
    if not human_dir.is_dir():
        parser.error(f"--human-corpus is not a directory: {human_dir}")

    ai_docs = _read_corpus_dir(ai_dir)
    human_docs = _read_corpus_dir(human_dir)

    print(
        f"[mine_patterns] lang={args.lang}  "
        f"ai_docs={len(ai_docs)}  human_docs={len(human_docs)}  "
        f"ngrams={args.min_n}-{args.max_n}  top={args.top}  min_count={args.min_count}",
        file=sys.stderr,
    )

    candidates = mine(
        ai_docs,
        human_docs,
        min_n=args.min_n,
        max_n=args.max_n,
        top_k=args.top,
        min_ai_count=args.min_count,
    )

    print(
        f"[mine_patterns] {len(candidates)} candidates surfaced.",
        file=sys.stderr,
    )

    if args.format == "json":
        print(_format_json(candidates))
    else:
        print(_format_tsv(candidates))


if __name__ == "__main__":
    main()
