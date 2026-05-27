"""DE human corpus fetcher — Phase 2, Task 3.

Fetches real-world German-language text from three high-leverage sources
covering all six eval domains:

    Wikipedia DE  →  casual, academic, marketing, career
    GitHub        →  marketing, career
    ubuntuusers   →  technical

Usage (CLI):
    python -m evals.scripts.fetch_de_human_corpus --source all
    python -m evals.scripts.fetch_de_human_corpus --source wikipedia_casual
    python -m evals.scripts.fetch_de_human_corpus --source wikipedia_academic
    python -m evals.scripts.fetch_de_human_corpus --source wikipedia_marketing
    python -m evals.scripts.fetch_de_human_corpus --source wikipedia_career
    python -m evals.scripts.fetch_de_human_corpus --source github_marketing
    python -m evals.scripts.fetch_de_human_corpus --source github_career
    python -m evals.scripts.fetch_de_human_corpus --source ubuntuusers_technical
    python -m evals.scripts.fetch_de_human_corpus --dry-run

Stdlib only (no new dependencies). Python 3.10+.
"""
from __future__ import annotations

import argparse
import base64
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


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENT = (
    "humanizer-ext/3.4.2 "
    "(Phase 2 DE corpus build; +https://github.com/duathron/humanizer-ext)"
)

WIKI_API = "https://de.wikipedia.org/w/api.php"
UBUNTU_WIKI_API = "https://wiki.ubuntuusers.de/api.php"
GITHUB_API = "https://api.github.com"

# Word-count window for corpus samples (strip to this range)
MIN_WORDS = 200
MAX_WORDS = 800

# Max total GitHub API requests to stay inside unauthenticated rate limit
GITHUB_MAX_REQUESTS = 30

# Pre-2022 cutoff (AI-contamination safety)
WIKI_DATE_CUTOFF = "2022-11-30T00:00:00Z"

TODAY = date.today().isoformat()


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------

@dataclass
class Document:
    """One corpus document."""

    id: str            # filename-safe ID
    text: str          # extracted plain text (200–800 words)
    source_url: str    # canonical URL for attribution
    license: str       # license identifier (CC-BY-SA-3.0, MIT, PD, etc.)
    fetch_date: str    # ISO date (YYYY-MM-DD)
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get(url: str, params: dict | None = None, *, retries: int = 2) -> bytes:
    """Perform a GET request with User-Agent header. Retry once on failure.

    Sleeps 0.6 s after each successful request to respect rate limits.
    """
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
# Wikitext helpers (shared by Wikipedia DE and ubuntuusers)
# ---------------------------------------------------------------------------

def _wiki_category_members(
    api_url: str,
    category: str,
    limit: int = 50,
) -> list[str]:
    """Return page titles in a MediaWiki category."""
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": f"Kategorie:{category}",
        "cmlimit": str(limit),
        "cmtype": "page",
    }
    try:
        data = _get_json(api_url, params)
        return [m["title"] for m in data["query"]["categorymembers"]]
    except Exception:  # noqa: BLE001
        return []


def _wiki_revision_pre_date(
    api_url: str,
    title: str,
    end_iso: str = WIKI_DATE_CUTOFF,
) -> str | None:
    """Fetch the latest revision of *title* before *end_iso*. Returns wikitext or None."""
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "rvprop": "content|timestamp",
        "rvend": end_iso,
        "rvlimit": "1",
        "rvdir": "older",
    }
    try:
        data = _get_json(api_url, params)
        pages = data["query"]["pages"]
        page = next(iter(pages.values()))
        revisions = page.get("revisions", [])
        if not revisions:
            return None
        return revisions[0].get("*") or revisions[0].get("content")
    except Exception:  # noqa: BLE001
        return None


def _strip_wikitext(wikitext: str) -> str:
    """Naive wikitext → plain text.

    Strips: [[link|text]] → text, {{templates}}, ==headings==, <tags>,
    <ref>, magic words, infoboxes. Leaves prose-like text intact.
    Perfect reconstruction is not required; the eval pipeline only needs
    prose-like text of reasonable quality.
    """
    text = wikitext

    # Remove <ref> tags and their content
    text = re.sub(r"<ref[^>]*?>.*?</ref>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<ref[^/]*/?>", " ", text, flags=re.IGNORECASE)

    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)

    # Remove <html-tag> and </html-tag>
    text = re.sub(r"<[^>]+?>", " ", text)

    # Remove {{templates}} — greedy inner first, then outer (two passes handles nesting)
    for _ in range(5):
        text = re.sub(r"\{\{[^{}]*?\}\}", " ", text)

    # Collapse [[File:...]] and [[Datei:...]] image links
    text = re.sub(r"\[\[(?:File|Datei|Image|Bild):[^\]]*?\]\]", " ", text, flags=re.IGNORECASE)

    # [[link|display]] → "link display" (keep both so link target — often the
    # canonical term — is not lost; e.g. [[Berlin|Hauptstadt]] → "Berlin Hauptstadt")
    text = re.sub(r"\[\[([^\]|]*?)\|([^\]]*?)\]\]", r"\1 \2", text)

    # [[link]] → link
    text = re.sub(r"\[\[([^\]]*?)\]\]", r"\1", text)

    # External links [url text] → text
    text = re.sub(r"\[https?://\S+\s+([^\]]+?)\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\]", " ", text)

    # Remove == headings == (any level)
    text = re.sub(r"={2,6}[^=]+?={2,6}", " ", text)

    # Remove table markup |, ||, !!, {|, |}
    text = re.sub(r"^\s*(\||\!|{\||\|})", " ", text, flags=re.MULTILINE)

    # Remove bold/italic wiki markup ''', ''
    text = re.sub(r"'{2,3}", "", text)

    # Remove DEFAULTSORT, REDIRECT, magic words
    text = re.sub(r"#\w+:[^\n]*", " ", text)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(l for l in lines if l)

    return text.strip()


def _trim_to_words(text: str, max_words: int = MAX_WORDS, min_words: int = MIN_WORDS) -> str:
    """Trim text to approximately [min_words, max_words] words.

    Takes the first *max_words* words. Returns empty string if fewer than
    *min_words* words remain after trimming.
    """
    words = text.split()
    if len(words) < min_words:
        return ""
    if len(words) > max_words:
        words = words[:max_words]
    return " ".join(words)


def _make_id(prefix: str, title: str) -> str:
    """Build a filename-safe document ID from prefix + title."""
    slug = re.sub(r"[^\w\-]", "_", title.lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return f"{prefix}_{slug}"[:80]


def _wiki_article_url(title: str, wiki: str = "de.wikipedia") -> str:
    return f"https://{wiki}.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"


# ---------------------------------------------------------------------------
# Wikipedia DE fetchers
# ---------------------------------------------------------------------------

def fetch_wikipedia_de_casual(n: int = 8, *, seed: int = 42) -> list[Document]:
    """Sample n Wikipedia DE Diskussion: pages, revisions before 2022-11-30.

    Diskussion (talk) pages carry informal, varied-register German prose —
    opinion, debate, questions — matching the 'casual' eval domain.
    """
    rng = random.Random(seed)

    # Fetch members from several talk-adjacent categories / namespaces.
    # We use the Wikipedia:Redaktion pages which have editorial discussions.
    candidate_categories = [
        "Wikipedia:Auskunft",
        "Wikipedia:Fragen_zur_Wikipedia",
        "Wikipedia:Café",
        "Wikipedia:Meinungsbilder",
    ]
    # These are not standard categories but we'll also do a search query.
    titles: list[str] = []

    # Use categorymembers from informal project pages
    for cat in ["Diskussion", "Benutzer_Diskussion"]:
        members = _wiki_category_members(WIKI_API, cat, limit=30)
        titles.extend(members)

    # Fallback: search for Diskussion pages via API search
    if len(titles) < n * 3:
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": "intitle:Diskussion",
            "srnamespace": "1",  # Talk namespace
            "srlimit": "50",
        }
        try:
            data = _get_json(WIKI_API, params)
            for item in data.get("query", {}).get("search", []):
                titles.append(item["title"])
        except Exception:  # noqa: BLE001
            pass

    # If still not enough, fall back to main-namespace casual topics
    if len(titles) < n:
        fallback_cats = ["Gesellschaft", "Alltag", "Freizeit"]
        for cat in fallback_cats:
            members = _wiki_category_members(WIKI_API, cat, limit=20)
            titles.extend(members)

    rng.shuffle(titles)
    docs: list[Document] = []
    attempts = 0
    idx = 0

    while len(docs) < n and idx < len(titles):
        title = titles[idx]
        idx += 1
        attempts += 1
        if attempts > n * 6:
            break

        wikitext = _wiki_revision_pre_date(WIKI_API, title)
        if not wikitext:
            continue

        plain = _strip_wikitext(wikitext)
        trimmed = _trim_to_words(plain)
        if not trimmed:
            continue

        doc_id = _make_id("wiki_casual", title)
        docs.append(
            Document(
                id=doc_id,
                text=trimmed,
                source_url=_wiki_article_url(title),
                license="CC-BY-SA-3.0",
                fetch_date=TODAY,
                metadata={
                    "title": title,
                    "wiki": "de.wikipedia",
                    "domain": "casual",
                    "pre_date_cutoff": WIKI_DATE_CUTOFF,
                },
            )
        )

    return docs


def fetch_wikipedia_de_academic(n: int = 8, *, seed: int = 42) -> list[Document]:
    """Sample n Wikipedia DE articles from academic categories, pre-2022."""
    rng = random.Random(seed)

    academic_categories = [
        "Wissenschaft",
        "Mathematik",
        "Physik",
        "Geschichte",
        "Biologie",
        "Chemie",
        "Astronomie",
        "Philosophie",
        "Soziologie",
        "Linguistik",
    ]

    titles: list[str] = []
    for cat in academic_categories:
        members = _wiki_category_members(WIKI_API, cat, limit=20)
        titles.extend(members)

    rng.shuffle(titles)
    docs: list[Document] = []
    idx = 0

    while len(docs) < n and idx < len(titles):
        title = titles[idx]
        idx += 1

        wikitext = _wiki_revision_pre_date(WIKI_API, title)
        if not wikitext:
            continue

        plain = _strip_wikitext(wikitext)
        trimmed = _trim_to_words(plain)
        if not trimmed:
            continue

        doc_id = _make_id("wiki_academic", title)
        docs.append(
            Document(
                id=doc_id,
                text=trimmed,
                source_url=_wiki_article_url(title),
                license="CC-BY-SA-3.0",
                fetch_date=TODAY,
                metadata={
                    "title": title,
                    "wiki": "de.wikipedia",
                    "domain": "academic",
                    "pre_date_cutoff": WIKI_DATE_CUTOFF,
                },
            )
        )

    return docs


def fetch_wikipedia_de_marketing(n: int = 8, *, seed: int = 42) -> list[Document]:
    """Sample n Wikipedia DE articles from product/brand categories, pre-2022.

    Product/brand articles carry product-positioning prose — features,
    history, market positioning — matching the 'marketing' eval domain.
    """
    rng = random.Random(seed)

    marketing_categories = [
        "Markenname",
        "Smartphone",
        "Softwareprodukt",
        "App",
        "Konsumgut",
        "Einzelhandelsunternehmen",
        "Elektronikhersteller",
        "Automobilhersteller",
    ]

    titles: list[str] = []
    for cat in marketing_categories:
        members = _wiki_category_members(WIKI_API, cat, limit=20)
        titles.extend(members)

    rng.shuffle(titles)
    docs: list[Document] = []
    idx = 0

    while len(docs) < n and idx < len(titles):
        title = titles[idx]
        idx += 1

        wikitext = _wiki_revision_pre_date(WIKI_API, title)
        if not wikitext:
            continue

        plain = _strip_wikitext(wikitext)
        trimmed = _trim_to_words(plain)
        if not trimmed:
            continue

        doc_id = _make_id("wiki_marketing", title)
        docs.append(
            Document(
                id=doc_id,
                text=trimmed,
                source_url=_wiki_article_url(title),
                license="CC-BY-SA-3.0",
                fetch_date=TODAY,
                metadata={
                    "title": title,
                    "wiki": "de.wikipedia",
                    "domain": "marketing",
                    "pre_date_cutoff": WIKI_DATE_CUTOFF,
                },
            )
        )

    return docs


def fetch_wikipedia_de_career(n: int = 8, *, seed: int = 42) -> list[Document]:
    """Sample n Wikipedia DE Personenartikel from career-relevant categories, pre-2022.

    Person articles contain career-narrative prose in third-person —
    "X studierte in Y, arbeitete bei Z, leitet seit 20XX W" — which mirrors
    the register a humanized DE Lebenslauf/Anschreiben should reach.
    """
    rng = random.Random(seed)

    career_categories = [
        "Deutscher_Unternehmer",
        "Hochschullehrer_(Deutschland)",
        "Manager",
        "Politiker_(Deutschland)",
        "Wissenschaftler",
        "Journalist_(Deutschland)",
        "Ökonom_(Deutschland)",
    ]

    titles: list[str] = []
    for cat in career_categories:
        members = _wiki_category_members(WIKI_API, cat, limit=20)
        titles.extend(members)

    rng.shuffle(titles)
    docs: list[Document] = []
    idx = 0

    while len(docs) < n and idx < len(titles):
        title = titles[idx]
        idx += 1

        wikitext = _wiki_revision_pre_date(WIKI_API, title)
        if not wikitext:
            continue

        plain = _strip_wikitext(wikitext)
        trimmed = _trim_to_words(plain)
        if not trimmed:
            continue

        doc_id = _make_id("wiki_career", title)
        docs.append(
            Document(
                id=doc_id,
                text=trimmed,
                source_url=_wiki_article_url(title),
                license="CC-BY-SA-3.0",
                fetch_date=TODAY,
                metadata={
                    "title": title,
                    "wiki": "de.wikipedia",
                    "domain": "career",
                    "pre_date_cutoff": WIKI_DATE_CUTOFF,
                },
            )
        )

    return docs


# ---------------------------------------------------------------------------
# GitHub fetchers
# ---------------------------------------------------------------------------

# Global counter to cap total GitHub requests (unauthenticated rate limit)
_github_request_count = 0


def _github_get(path: str, params: dict | None = None) -> Any | None:
    """Perform a GitHub API GET. Returns None if rate limit cap is reached."""
    global _github_request_count  # noqa: PLW0603
    if _github_request_count >= GITHUB_MAX_REQUESTS:
        print(
            f"[fetch_de_human_corpus] GitHub request cap ({GITHUB_MAX_REQUESTS}) reached; skipping.",
            file=sys.stderr,
        )
        return None

    url = GITHUB_API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/vnd.github.v3+json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        _github_request_count += 1
        time.sleep(0.7)
        return data
    except Exception as exc:  # noqa: BLE001
        print(f"[fetch_de_human_corpus] GitHub API error: {exc}", file=sys.stderr)
        _github_request_count += 1
        return None


def _github_search_repos(query: str, n: int = 20) -> list[dict]:
    """Search GitHub repositories. Returns list of repo dicts."""
    data = _github_get("/search/repositories", {"q": query, "per_page": str(n)})
    if not data:
        return []
    return data.get("items", [])


def _github_fetch_readme(repo_full_name: str) -> str | None:
    """Fetch the decoded README text of a repo. Returns None on failure."""
    data = _github_get(f"/repos/{repo_full_name}/readme")
    if not data:
        return None
    content = data.get("content", "")
    encoding = data.get("encoding", "")
    if encoding == "base64":
        try:
            return base64.b64decode(content).decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            return None
    return content or None


def _is_de_text(text: str) -> bool:
    """Heuristic German-language detector.

    Returns True if >= 4 distinct common DE function words appear in the
    first 500 characters. Cheap, no external dependencies.
    """
    sample = text[:500].lower()
    de_words = {"der", "die", "das", "und", "ist", "in", "zu", "ein", "eine",
                "ich", "wir", "mit", "von", "auf", "für", "den", "des", "dem",
                "nicht", "auch", "an", "es", "war", "sind"}
    hits = {w for w in de_words if re.search(r"\b" + re.escape(w) + r"\b", sample)}
    return len(hits) >= 4


def fetch_github_de_marketing(n: int = 6, *, seed: int = 42) -> list[Document]:
    """GitHub repo READMEs with DE-language content + stars >= 50.

    README files are first-party product-positioning copy by definition —
    feature lists, audience hook, installation pitch — matching the
    'marketing' eval domain.
    """
    rng = random.Random(seed)

    # Multiple queries to diversify; results deduplicated by repo name
    queries = [
        "stars:>50 language:Python README deutsch",
        "stars:>100 language:JavaScript README deutsche",
        "stars:>50 topic:documentation language:de",
        "stars:>50 README Entwicklung Dokumentation",
    ]

    repos: dict[str, dict] = {}
    for q in queries:
        found = _github_search_repos(q, n=15)
        for r in found:
            repos[r["full_name"]] = r
        if len(repos) >= n * 4:
            break

    repo_list = list(repos.values())
    rng.shuffle(repo_list)

    docs: list[Document] = []
    for repo in repo_list:
        if len(docs) >= n:
            break

        readme = _github_fetch_readme(repo["full_name"])
        if not readme:
            continue
        if not _is_de_text(readme):
            continue

        plain = re.sub(r"```.*?```", " ", readme, flags=re.DOTALL)  # strip code blocks
        plain = re.sub(r"`[^`]+`", " ", plain)  # strip inline code
        plain = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", plain)  # strip images
        plain = re.sub(r"\[[^\]]*\]\([^)]*\)", lambda m: m.group(0).split("]")[0][1:], plain)  # links → text
        plain = re.sub(r"#{1,6}\s+", " ", plain)  # strip headings
        plain = re.sub(r"<[^>]+?>", " ", plain)  # strip HTML tags
        plain = re.sub(r"\s+", " ", plain).strip()

        trimmed = _trim_to_words(plain)
        if not trimmed:
            continue

        repo_url = repo.get("html_url", f"https://github.com/{repo['full_name']}")
        doc_id = _make_id("github_marketing", repo["full_name"].replace("/", "_"))
        license_info = (repo.get("license") or {}).get("spdx_id") or "per-repo"

        docs.append(
            Document(
                id=doc_id,
                text=trimmed,
                source_url=repo_url + "/blob/main/README.md",
                license=license_info,
                fetch_date=TODAY,
                metadata={
                    "repo": repo["full_name"],
                    "stars": repo.get("stargazers_count", 0),
                    "domain": "marketing",
                    "language": repo.get("language", ""),
                },
            )
        )

    return docs


def fetch_github_de_career(n: int = 6, *, seed: int = 42) -> list[Document]:
    """GitHub user profile READMEs (<user>/<user> convention) with DE content.

    Developer profile READMEs are first-person career self-positioning —
    tech stack, role description, interests — matching the 'career' domain.
    """
    rng = random.Random(seed)

    # Profile repos follow the <user>/<user> naming convention.
    # GitHub search doesn't directly filter for this but "is:public" +
    # same-name pattern is common in profile READMEs.
    queries = [
        "in:readme Ich bin Entwickler language:Markdown",
        "in:readme Hallo ich bin language:Markdown stars:>1",
        "in:readme Software-Entwickler Kenntnisse language:Markdown",
        "in:readme Willkommen auf meinem Profil language:Markdown",
    ]

    repos: dict[str, dict] = {}
    for q in queries:
        found = _github_search_repos(q, n=15)
        for r in found:
            repos[r["full_name"]] = r
        if len(repos) >= n * 4:
            break

    repo_list = list(repos.values())
    rng.shuffle(repo_list)

    docs: list[Document] = []
    for repo in repo_list:
        if len(docs) >= n:
            break

        readme = _github_fetch_readme(repo["full_name"])
        if not readme:
            continue
        if not _is_de_text(readme):
            continue

        # Strip markdown formatting
        plain = re.sub(r"```.*?```", " ", readme, flags=re.DOTALL)
        plain = re.sub(r"`[^`]+`", " ", plain)
        plain = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", plain)
        plain = re.sub(r"\[[^\]]*\]\([^)]*\)", lambda m: m.group(0).split("]")[0][1:], plain)
        plain = re.sub(r"#{1,6}\s+", " ", plain)
        plain = re.sub(r"<[^>]+?>", " ", plain)
        plain = re.sub(r"\s+", " ", plain).strip()

        trimmed = _trim_to_words(plain)
        if not trimmed:
            continue

        repo_url = repo.get("html_url", f"https://github.com/{repo['full_name']}")
        doc_id = _make_id("github_career", repo["full_name"].replace("/", "_"))
        license_info = (repo.get("license") or {}).get("spdx_id") or "per-repo"

        docs.append(
            Document(
                id=doc_id,
                text=trimmed,
                source_url=repo_url + "/blob/main/README.md",
                license=license_info,
                fetch_date=TODAY,
                metadata={
                    "repo": repo["full_name"],
                    "stars": repo.get("stargazers_count", 0),
                    "domain": "career",
                    "language": repo.get("language", ""),
                },
            )
        )

    return docs


# ---------------------------------------------------------------------------
# ubuntuusers.de fetcher
# ---------------------------------------------------------------------------

def fetch_ubuntuusers_technical(n: int = 8, *, seed: int = 42) -> list[Document]:
    """ubuntuusers.de wiki articles (MediaWiki). Technical docs register.

    The ubuntuusers wiki is a large German-language Linux documentation
    resource. Articles are step-by-step technical instruction, command-
    line reference, and troubleshooting guides — matching the 'technical'
    eval domain.
    """
    rng = random.Random(seed)

    # ubuntuusers categories for technical docs
    ubuntu_categories = [
        "Terminal",
        "Paketverwaltung",
        "Netzwerk",
        "Datei",
        "System",
        "Installation",
        "Konfiguration",
        "Sicherheit",
        "Multimedia",
        "Drucken",
    ]

    titles: list[str] = []
    for cat in ubuntu_categories:
        members = _wiki_category_members(UBUNTU_WIKI_API, cat, limit=15)
        titles.extend(members)

    # Fallback: try querying the allpages list if categories are empty
    if len(titles) < n:
        params = {
            "action": "query",
            "format": "json",
            "list": "allpages",
            "aplimit": "50",
            "apnamespace": "0",
        }
        try:
            data = _get_json(UBUNTU_WIKI_API, params)
            for page in data.get("query", {}).get("allpages", []):
                titles.append(page["title"])
        except Exception:  # noqa: BLE001
            pass

    rng.shuffle(titles)
    docs: list[Document] = []
    idx = 0

    while len(docs) < n and idx < len(titles):
        title = titles[idx]
        idx += 1

        # ubuntuusers wiki: fetch without date filter (pre-2022 cutoff less
        # critical for technical docs since Linux commands don't evolve as fast)
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": title,
            "rvprop": "content",
            "rvlimit": "1",
        }
        try:
            data = _get_json(UBUNTU_WIKI_API, params)
            pages = data["query"]["pages"]
            page = next(iter(pages.values()))
            revisions = page.get("revisions", [])
            if not revisions:
                continue
            wikitext = revisions[0].get("*") or revisions[0].get("content", "")
        except Exception:  # noqa: BLE001
            continue

        if not wikitext:
            continue

        plain = _strip_wikitext(wikitext)

        # ubuntuusers has a lot of template-heavy content; require actual prose
        if plain.count(" ") < 50:
            continue

        trimmed = _trim_to_words(plain)
        if not trimmed:
            continue

        doc_id = _make_id("ubuntuusers_technical", title)
        article_url = f"https://wiki.ubuntuusers.de/{urllib.parse.quote(title.replace(' ', '_'))}"

        docs.append(
            Document(
                id=doc_id,
                text=trimmed,
                source_url=article_url,
                license="CC-BY-SA-3.0",
                fetch_date=TODAY,
                metadata={
                    "title": title,
                    "wiki": "wiki.ubuntuusers.de",
                    "domain": "technical",
                },
            )
        )

    return docs


# ---------------------------------------------------------------------------
# Corpus writer
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
    """Render YAML frontmatter block for a Document."""
    lines = ["---"]
    lines.append(f"id: {_yaml_str(doc.id)}")
    lines.append(f"source_url: {_yaml_str(doc.source_url)}")
    lines.append(f"license: {_yaml_str(doc.license)}")
    lines.append(f"fetch_date: {_yaml_str(doc.fetch_date)}")
    if doc.metadata:
        lines.append("metadata:")
        for k, v in doc.metadata.items():
            lines.append(f"  {k}: {_yaml_str(v)}")
    lines.append("---")
    return "\n".join(lines)


def write_corpus(docs: list[Document], out_dir: Path, source_name: str) -> None:
    """Write docs to out_dir/<source_name>/ as <id>.md with YAML frontmatter.

    Also writes _LICENSE and _SOURCE sidecar files.
    """
    target = out_dir / source_name
    target.mkdir(parents=True, exist_ok=True)

    for doc in docs:
        fm = _render_frontmatter(doc)
        content = f"{fm}\n\n{doc.text}\n"
        (target / f"{doc.id}.md").write_text(content, encoding="utf-8")

    # Write sidecar files based on first doc (they share source + license)
    if docs:
        first = docs[0]
        (target / "_LICENSE").write_text(
            f"{first.license}\n"
            f"Source: {first.source_url}\n"
            f"Fetched: {first.fetch_date}\n",
            encoding="utf-8",
        )
        (target / "_SOURCE").write_text(
            f"source_name: {source_name}\n"
            f"license: {first.license}\n"
            f"fetch_date: {first.fetch_date}\n"
            f"doc_count: {len(docs)}\n"
            f"url: {first.source_url}\n",
            encoding="utf-8",
        )
        print(
            f"[fetch_de_human_corpus] Wrote {len(docs)} docs → {target}",
            file=sys.stderr,
        )
    else:
        print(
            f"[fetch_de_human_corpus] WARNING: no docs written for {source_name}",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# Source registry
# ---------------------------------------------------------------------------

# Map from --source name → (fetcher_fn, n, out_subdir_name)
_SOURCES: dict[str, tuple] = {
    "wikipedia_casual": (
        fetch_wikipedia_de_casual,
        8,
        "wikipedia_casual",
    ),
    "wikipedia_academic": (
        fetch_wikipedia_de_academic,
        8,
        "wikipedia_academic",
    ),
    "wikipedia_marketing": (
        fetch_wikipedia_de_marketing,
        8,
        "wikipedia_marketing",
    ),
    "wikipedia_career": (
        fetch_wikipedia_de_career,
        8,
        "wikipedia_career",
    ),
    "github_marketing": (
        fetch_github_de_marketing,
        6,
        "github_marketing",
    ),
    "github_career": (
        fetch_github_de_career,
        6,
        "github_career",
    ),
    "ubuntuusers_technical": (
        fetch_ubuntuusers_technical,
        8,
        "ubuntuusers_technical",
    ),
}

# Default output root (can be overridden via --out-dir)
_DEFAULT_OUT_DIR = Path("evals") / "corpus" / "de" / "human"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fetch_de_human_corpus",
        description=(
            "Fetch real-world DE human corpus from Wikipedia DE, GitHub, "
            "and ubuntuusers.de. Writes markdown files + sidecar files to "
            "evals/corpus/de/human/<source>/."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m evals.scripts.fetch_de_human_corpus --source all\n"
            "  python -m evals.scripts.fetch_de_human_corpus --source wikipedia_casual\n"
            "  python -m evals.scripts.fetch_de_human_corpus --dry-run\n"
        ),
    )
    parser.add_argument(
        "--source",
        choices=list(_SOURCES.keys()) + ["all"],
        default="all",
        help=(
            "Which source to fetch. 'all' fetches all 7 sub-categories (default: all).\n"
            f"Choices: {', '.join(list(_SOURCES.keys()) + ['all'])}"
        ),
    )
    parser.add_argument(
        "--out-dir",
        default=str(_DEFAULT_OUT_DIR),
        metavar="DIR",
        help=f"Root output directory (default: {_DEFAULT_OUT_DIR})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible sampling (default: 42)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned fetches without hitting the network.",
    )
    return parser


def _dry_run_report() -> None:
    """Print a plan of what would be fetched."""
    print("=== fetch_de_human_corpus — DRY RUN ===")
    print(f"Output root: {_DEFAULT_OUT_DIR}")
    print()
    total = 0
    for name, (fn, n, subdir) in _SOURCES.items():
        print(f"  --source {name:<30}  n={n}  → {_DEFAULT_OUT_DIR}/{subdir}/")
        total += n
    print()
    print(f"Total target documents: {total}")
    print()
    print("Sources:")
    print(f"  wikipedia (de.wikipedia.org)  — CC-BY-SA-3.0  — pre-{WIKI_DATE_CUTOFF[:10]}")
    print(f"  github (api.github.com)       — per-repo      — current")
    print(f"  ubuntuusers (wiki.ubuntuusers.de) — CC-BY-SA-3.0  — current")
    print()
    print("Domain coverage:")
    print("  casual      → wikipedia_casual")
    print("  academic    → wikipedia_academic")
    print("  marketing   → wikipedia_marketing, github_marketing")
    print("  career      → wikipedia_career, github_career")
    print("  technical   → ubuntuusers_technical")
    print()
    print("Network etiquette: 0.6-0.7 s sleep between requests, retry once.")
    print(f"GitHub request cap: {GITHUB_MAX_REQUESTS} total (unauthenticated limit).")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.dry_run:
        _dry_run_report()
        return

    out_dir = Path(args.out_dir)
    seed = args.seed

    sources_to_run: list[str]
    if args.source == "all":
        sources_to_run = list(_SOURCES.keys())
    else:
        sources_to_run = [args.source]

    for name in sources_to_run:
        fn, n, subdir = _SOURCES[name]
        print(f"[fetch_de_human_corpus] Fetching {name} (n={n}) …", file=sys.stderr)
        try:
            docs = fn(n=n, seed=seed)
            write_corpus(docs, out_dir, subdir)
        except Exception as exc:  # noqa: BLE001
            print(
                f"[fetch_de_human_corpus] ERROR fetching {name}: {exc}",
                file=sys.stderr,
            )


if __name__ == "__main__":
    main()
