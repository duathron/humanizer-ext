"""DE AI corpus fetcher — Source A: Wikipedia DE articles tagged with Vorlage:KI-generiert.

Fetches articles that Wikipedia DE editors have flagged as AI-suspected content.
These are real-world AI output already human-verified as AI-generated — the highest
signal source available at $0 API cost.

Discovery endpoint (verified 2026-05-27):
  https://de.wikipedia.org/w/api.php?action=query&list=embeddedin&eititle=Vorlage:KI-generiert
  &eilimit=50&einamespace=0&format=json

Returns pages including: Sara Noxx, Ablaichbürste, Alternaria tenuissima,
Hybridtechnik, Tatarisches Reich, Rochdale Village, etc.

Output: evals/corpus/de/ai/wikipedia_tagged/
Per-doc: YAML frontmatter + _LICENSE + _SOURCE sidecars

Usage:
    python -m evals.scripts.fetch_de_wikipedia_ai_tagged --n 30 [--dry-run]
    python -m evals.scripts.fetch_de_wikipedia_ai_tagged --n 30 --seed 99
    python -m evals.scripts.fetch_de_wikipedia_ai_tagged --help

Stdlib only. Python 3.10+.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

# Re-use shared helpers from human corpus fetcher where available at import time.
# We import lazily inside functions to keep this module independently importable.

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENT = (
    "humanizer-ext/3.5.0 "
    "(Phase 2 DE AI corpus build; +https://github.com/duathron/humanizer-ext)"
)

WIKI_API = "https://de.wikipedia.org/w/api.php"

#: MediaWiki template that DE editors apply to AI-suspected articles.
KI_TEMPLATE = "Vorlage:KI-generiert"

#: Embeddedin API limit (max 500 for registered; 50 for anon — we use 500 to
#: get the full tagged set, then sample from it).
EMBEDDEDIN_LIMIT = 500

#: Word-count window for corpus samples — match human corpus conventions.
MIN_WORDS = 200
MAX_WORDS = 800

TODAY = date.today().isoformat()

# Default output root
_DEFAULT_OUT_DIR = Path("evals") / "corpus" / "de" / "ai"


# ---------------------------------------------------------------------------
# Public dataclass (mirrors fetch_de_human_corpus.Document)
# ---------------------------------------------------------------------------

@dataclass
class Document:
    """One AI corpus document."""

    id: str               # filename-safe ID
    text: str             # extracted plain text (200–800 words)
    source_url: str       # canonical URL for attribution
    license: str          # license identifier
    license_class: str    # "redistributable" | "research_only"
    fetch_date: str       # ISO date (YYYY-MM-DD)
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get(url: str, params: dict | None = None, *, retries: int = 2) -> bytes:
    """GET with User-Agent, retry, and polite sleep between requests."""
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            time.sleep(0.6)
            return data
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < retries:
                time.sleep(1.5)
    assert last_exc is not None
    raise last_exc


def _get_json(url: str, params: dict | None = None) -> Any:
    return json.loads(_get(url, params))


# ---------------------------------------------------------------------------
# Wikitext helpers (independent copies — avoids circular import from human corpus)
# ---------------------------------------------------------------------------

def _strip_wikitext(wikitext: str) -> str:
    """Naive wikitext → plain text.

    Strips: [[link|text]] → text, {{templates}}, ==headings==, <tags>,
    <ref>, magic words. Leaves prose intact.

    Matches the implementation in fetch_de_human_corpus._strip_wikitext so
    both scripts produce comparable plain-text quality.
    """
    text = wikitext

    # Remove <ref> tags and their content
    text = re.sub(r"<ref[^>]*?>.*?</ref>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<ref[^/]*/?>", " ", text, flags=re.IGNORECASE)

    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)

    # Remove HTML tags
    text = re.sub(r"<[^>]+?>", " ", text)

    # Remove {{templates}} — multiple passes for nesting
    for _ in range(5):
        text = re.sub(r"\{\{[^{}]*?\}\}", " ", text)

    # Collapse [[File:...]] image links
    text = re.sub(r"\[\[(?:File|Datei|Image|Bild):[^\]]*?\]\]", " ", text, flags=re.IGNORECASE)

    # [[link|display]] → "link display"
    text = re.sub(r"\[\[([^\]|]*?)\|([^\]]*?)\]\]", r"\1 \2", text)

    # [[link]] → link
    text = re.sub(r"\[\[([^\]]*?)\]\]", r"\1", text)

    # External links [url text] → text
    text = re.sub(r"\[https?://\S+\s+([^\]]+?)\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\]", " ", text)

    # Remove == headings ==
    text = re.sub(r"={2,6}[^=]+?={2,6}", " ", text)

    # Remove table markup
    text = re.sub(r"^\s*(\||\!|{\||\|})", " ", text, flags=re.MULTILINE)

    # Remove bold/italic wiki markup
    text = re.sub(r"'{2,3}", "", text)

    # Remove DEFAULTSORT, REDIRECT, magic words
    text = re.sub(r"#\w+:[^\n]*", " ", text)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(l for l in lines if l)

    return text.strip()


def _trim_to_words(text: str, max_words: int = MAX_WORDS, min_words: int = MIN_WORDS) -> str:
    """Trim to [min_words, max_words] word range.

    Returns empty string if fewer than min_words words remain.
    """
    words = text.split()
    if len(words) < min_words:
        return ""
    if len(words) > max_words:
        words = words[:max_words]
    return " ".join(words)


def _make_id(prefix: str, title: str) -> str:
    """Build a filename-safe document ID."""
    slug = re.sub(r"[^\w\-]", "_", title.lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return f"{prefix}_{slug}"[:80]


def _wiki_article_url(title: str) -> str:
    return f"https://de.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"


# ---------------------------------------------------------------------------
# Wikipedia embeddedin API (finds all pages that transclude the KI template)
# ---------------------------------------------------------------------------

def _fetch_ki_tagged_titles(limit: int = EMBEDDEDIN_LIMIT) -> list[str]:
    """Return all article titles in DE Wikipedia that transclude Vorlage:KI-generiert.

    Uses the MediaWiki `embeddedin` API list, namespace=0 (main articles only).
    Handles pagination via `eicontinue` to collect up to *limit* titles.

    Returns titles sorted for determinism before caller shuffles with seed.
    """
    titles: list[str] = []
    continue_token: str | None = None

    while len(titles) < limit:
        params: dict[str, str] = {
            "action": "query",
            "format": "json",
            "list": "embeddedin",
            "eititle": KI_TEMPLATE,
            "eilimit": str(min(500, limit - len(titles))),
            "einamespace": "0",
        }
        if continue_token:
            params["eicontinue"] = continue_token

        try:
            data = _get_json(WIKI_API, params)
        except Exception as exc:  # noqa: BLE001
            print(
                f"[fetch_de_wikipedia_ai_tagged] embeddedin API error: {exc}",
                file=sys.stderr,
            )
            break

        for page in data.get("query", {}).get("embeddedin", []):
            titles.append(page["title"])

        # Pagination
        cont = data.get("continue", {})
        continue_token = cont.get("eicontinue")
        if not continue_token:
            break

    return sorted(set(titles))  # sort + dedup for reproducibility


# ---------------------------------------------------------------------------
# Per-article revision fetcher
# ---------------------------------------------------------------------------

def _wiki_revision_latest(title: str) -> str | None:
    """Fetch the current (latest) revision wikitext for *title*.

    We do NOT apply the pre-2022 date cutoff used by the human corpus — these
    articles are specifically flagged as AI-generated, so post-2022 content is
    exactly what we want. The KI-generiert tag was only introduced in ~2023.
    """
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "rvprop": "content",
        "rvlimit": "1",
    }
    try:
        data = _get_json(WIKI_API, params)
        pages = data["query"]["pages"]
        page = next(iter(pages.values()))
        revisions = page.get("revisions", [])
        if not revisions:
            return None
        return revisions[0].get("*") or revisions[0].get("content")
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Main corpus builder
# ---------------------------------------------------------------------------

def fetch_wikipedia_ai_tagged(n: int = 30, *, seed: int = 42) -> list[Document]:
    """Fetch *n* DE Wikipedia articles tagged with Vorlage:KI-generiert.

    Steps:
    1. Call embeddedin API to get up to 500 tagged page titles.
    2. Shuffle with fixed *seed* for reproducibility; take first *n*.
    3. Fetch latest revision wikitext + strip + trim per article.
    4. Return list[Document] — caller writes via write_ai_corpus().

    Returns fewer than *n* documents if the tag set is smaller or if
    individual articles produce < MIN_WORDS of prose after stripping.
    """
    print(
        f"[fetch_de_wikipedia_ai_tagged] Fetching KI-tagged titles from embeddedin API …",
        file=sys.stderr,
    )
    all_titles = _fetch_ki_tagged_titles(limit=EMBEDDEDIN_LIMIT)
    print(
        f"[fetch_de_wikipedia_ai_tagged] Found {len(all_titles)} KI-tagged articles.",
        file=sys.stderr,
    )

    rng = random.Random(seed)
    shuffled = all_titles[:]
    rng.shuffle(shuffled)
    candidates = shuffled[:max(n * 3, n + 20)]  # over-sample to absorb empties

    docs: list[Document] = []
    for title in candidates:
        if len(docs) >= n:
            break

        print(
            f"[fetch_de_wikipedia_ai_tagged] Fetching '{title}' …",
            file=sys.stderr,
        )
        wikitext = _wiki_revision_latest(title)
        if not wikitext:
            continue

        plain = _strip_wikitext(wikitext)
        trimmed = _trim_to_words(plain)
        if not trimmed:
            print(
                f"[fetch_de_wikipedia_ai_tagged] '{title}' skipped (< {MIN_WORDS} words after strip)",
                file=sys.stderr,
            )
            continue

        doc_id = _make_id("wiki_ki", title)
        docs.append(
            Document(
                id=doc_id,
                text=trimmed,
                source_url=_wiki_article_url(title),
                license="CC-BY-SA-3.0",
                license_class="redistributable",
                fetch_date=TODAY,
                metadata={
                    "source": "wikipedia_de_ki_generiert_tagged",
                    "title": title,
                    "wiki": "de.wikipedia",
                    "template": KI_TEMPLATE,
                },
            )
        )

    print(
        f"[fetch_de_wikipedia_ai_tagged] Collected {len(docs)} documents.",
        file=sys.stderr,
    )
    return docs


# ---------------------------------------------------------------------------
# Corpus writer (AI-specific — writes to evals/corpus/de/ai/)
# ---------------------------------------------------------------------------

_YAML_SPECIAL = re.compile(r'[:\-{}\[\],&*#?|<>=!%@`]')


def _yaml_str(v: Any) -> str:
    """Minimal YAML value serializer (no external dep)."""
    s = str(v)
    if _YAML_SPECIAL.search(s) or "\n" in s or s.startswith(("'", '"')):
        s = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{s}"'
    return s


def _render_frontmatter(doc: Document) -> str:
    """Render YAML frontmatter for a Document."""
    lines = ["---"]
    lines.append(f"id: {_yaml_str(doc.id)}")
    lines.append(f"source_url: {_yaml_str(doc.source_url)}")
    lines.append(f"license: {_yaml_str(doc.license)}")
    lines.append(f"license_class: {_yaml_str(doc.license_class)}")
    lines.append(f"fetch_date: {_yaml_str(doc.fetch_date)}")
    if doc.metadata:
        lines.append("metadata:")
        for k, v in doc.metadata.items():
            lines.append(f"  {k}: {_yaml_str(v)}")
    lines.append("---")
    return "\n".join(lines)


def write_ai_corpus(docs: list[Document], out_dir: Path, source_subdir: str) -> None:
    """Write *docs* to *out_dir*/<source_subdir>/ as <id>.md with YAML frontmatter.

    Also writes _LICENSE and _SOURCE sidecar files (CC-BY-SA-3.0 attribution
    to DE Wikipedia per redistribution requirements).
    """
    target = out_dir / source_subdir
    target.mkdir(parents=True, exist_ok=True)

    for doc in docs:
        fm = _render_frontmatter(doc)
        content = f"{fm}\n\n{doc.text}\n"
        (target / f"{doc.id}.md").write_text(content, encoding="utf-8")

    if docs:
        first = docs[0]
        lic_text = (
            f"{first.license}\n"
            f"Source: https://de.wikipedia.org/wiki/Vorlage:KI-generiert\n"
            f"Fetched: {first.fetch_date}\n"
            f"License class: {first.license_class}\n"
            f"Attribution: Content from DE Wikipedia — Vorlage:KI-generiert tagged articles.\n"
            f"License: CC-BY-SA 3.0 — https://creativecommons.org/licenses/by-sa/3.0/\n"
        )
        (target / "_LICENSE").write_text(lic_text, encoding="utf-8")
        (target / "_SOURCE").write_text(
            f"source_name: {source_subdir}\n"
            f"license_class: {first.license_class}\n"
            f"license: {first.license}\n"
            f"fetch_date: {first.fetch_date}\n"
            f"doc_count: {len(docs)}\n"
            f"url: https://de.wikipedia.org/wiki/Vorlage:KI-generiert\n"
            f"template: {KI_TEMPLATE}\n",
            encoding="utf-8",
        )
        print(
            f"[fetch_de_wikipedia_ai_tagged] Wrote {len(docs)} docs → {target}",
            file=sys.stderr,
        )
    else:
        print(
            f"[fetch_de_wikipedia_ai_tagged] WARNING: no docs written for {source_subdir}",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fetch_de_wikipedia_ai_tagged",
        description=(
            "Fetch DE Wikipedia articles tagged with Vorlage:KI-generiert into "
            "evals/corpus/de/ai/wikipedia_tagged/. "
            "These are real-world AI-suspected texts already human-verified by "
            "DE Wikipedia editors — Source A of the zero-budget AI corpus."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m evals.scripts.fetch_de_wikipedia_ai_tagged\n"
            "  python -m evals.scripts.fetch_de_wikipedia_ai_tagged --n 30\n"
            "  python -m evals.scripts.fetch_de_wikipedia_ai_tagged --dry-run\n"
            "  python -m evals.scripts.fetch_de_wikipedia_ai_tagged --n 50 --seed 99\n"
        ),
    )
    parser.add_argument(
        "--n",
        type=int,
        default=30,
        metavar="N",
        help="Number of articles to fetch (default: 30).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible sampling (default: 42).",
    )
    parser.add_argument(
        "--out-dir",
        default=str(_DEFAULT_OUT_DIR),
        metavar="DIR",
        help=f"Root AI corpus output directory (default: {_DEFAULT_OUT_DIR}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Print what would be fetched without making network calls or writing files."
        ),
    )
    return parser


def _dry_run_report(n: int, seed: int, out_dir: Path) -> None:
    print("=== fetch_de_wikipedia_ai_tagged — DRY RUN ===")
    print()
    print(f"Source:   DE Wikipedia — Vorlage:KI-generiert tagged articles")
    print(f"API:      {WIKI_API}")
    print(f"Template: {KI_TEMPLATE}")
    print(f"n:        {n} documents")
    print(f"seed:     {seed}")
    print(f"Out dir:  {out_dir / 'wikipedia_tagged'}/")
    print()
    print("Steps (if run live):")
    print(f"  1. GET embeddedin API (eilimit={EMBEDDEDIN_LIMIT}, einamespace=0)")
    print(f"  2. Shuffle with seed={seed}, take first n×3 candidates")
    print(f"  3. For each candidate: GET latest revision, strip wikitext, trim to 200-800 words")
    print(f"  4. Write <id>.md + _LICENSE + _SOURCE to out_dir/wikipedia_tagged/")
    print()
    print("License: CC-BY-SA-3.0 (redistributable — committed to git)")
    print("API cost: $0 — MediaWiki API, no authentication required")
    print()
    print("Known tagged articles (sample from 2026-05-27 discovery):")
    sample = [
        "Sara Noxx", "Ablaichbürste", "Alternaria tenuissima",
        "Hybridtechnik", "Tatarisches Reich", "Rochdale Village",
    ]
    for title in sample:
        print(f"  - {title}")
    print("  … (up to 500 total via embeddedin API)")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    out_dir = Path(args.out_dir)

    if args.dry_run:
        _dry_run_report(n=args.n, seed=args.seed, out_dir=out_dir)
        return

    docs = fetch_wikipedia_ai_tagged(n=args.n, seed=args.seed)
    write_ai_corpus(docs, out_dir, "wikipedia_tagged")


if __name__ == "__main__":
    main()
