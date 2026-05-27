"""DE human corpus fetcher — Phase 2, Task 3 (wave 2).

Fetches real-world German-language text from register-accurate sources
covering all six eval domains:

    Wikipedia DE  →  academic, marketing (retargeted), career, technical
    SSOAR         →  academic
    BGBl / Gesetze-im-Internet / Bundestag / Rechtsprechung → legal
    Linuxwiki / ubuntuusers / GitHub OSS → technical
    Bundesregierung / StackExchange / GitHub profiles → career
    Apple / Samsung / Microsoft / Startnext → marketing (research_only)
    Travel blogs / lifestyle blogs / Reddit r/de → casual (research_only)
    Karrierebibel / Bewerbung.com → career (research_only)
    Heise developer → technical (research_only)

Output is organized under two top-level subdirs:
    evals/corpus/de/human/redistributable/  — CC / PD sources (committed)
    evals/corpus/de/human/research_only/    — fair-use excerpts (gitignored)

Usage (CLI):
    python -m evals.scripts.fetch_de_human_corpus --source all
    python -m evals.scripts.fetch_de_human_corpus --source wikipedia_academic
    python -m evals.scripts.fetch_de_human_corpus --target redistributable
    python -m evals.scripts.fetch_de_human_corpus --target research_only
    python -m evals.scripts.fetch_de_human_corpus --list-sources
    python -m evals.scripts.fetch_de_human_corpus --dry-run

Stdlib only (no new dependencies). Python 3.10+.
"""
from __future__ import annotations

import argparse
import base64
import json
import random
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENT = (
    "humanizer-ext/3.4.2 "
    "(Phase 2 DE corpus build wave 2; +https://github.com/duathron/humanizer-ext)"
)

WIKI_API = "https://de.wikipedia.org/w/api.php"
UBUNTU_WIKI_API = "https://wiki.ubuntuusers.de/api.php"
LINUXWIKI_API = "https://linuxwiki.de/api.php"
GITHUB_API = "https://api.github.com"
SSOAR_OAI_URL = "https://www.ssoar.info/OAIHandler/request"
BUNDESTAG_API = "https://search.dip.bundestag.de/api/v1/plenarprotokoll"
STACKEXCHANGE_API = "https://api.stackexchange.com/2.3/users"
REDDIT_DE_URL = "https://www.reddit.com/r/de/top.json"

# Word-count window for corpus samples (strip to this range)
MIN_WORDS = 200
MAX_WORDS = 800

# Hard cap for research_only fair-use excerpts
RESEARCH_MAX_WORDS = 250
REDDIT_MAX_WORDS = 200

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
    license_class: str = "redistributable"  # "redistributable" | "research_only"


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
    """Sample n Wikipedia DE articles from current brand/product categories, pre-2022.

    Re-targeted from wave 1 (which pulled historical company articles at wrong register).
    Brand articles with Produktportfolio / Beschreibung sections carry product-
    positioning prose matching the 'marketing' eval domain.
    """
    rng = random.Random(seed)

    marketing_categories = [
        "Markenname",
        "Konsumgut",
        "Smartphone",
        "Softwareprodukt",
        "App",
        "Elektronikhersteller",
        "Automobilhersteller",
        "Marke_(Wirtschaft)",
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
                license_class="redistributable",
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
    lines.append(f"license_class: {_yaml_str(doc.license_class)}")
    lines.append(f"fetch_date: {_yaml_str(doc.fetch_date)}")
    if doc.metadata:
        lines.append("metadata:")
        for k, v in doc.metadata.items():
            lines.append(f"  {k}: {_yaml_str(v)}")
    lines.append("---")
    return "\n".join(lines)


def write_corpus(
    docs: list[Document],
    out_dir: Path,
    source_name: str,
    license_class: str = "redistributable",
) -> None:
    """Write docs to out_dir/<license_class>/<source_name>/ as <id>.md with YAML frontmatter.

    Also writes _LICENSE and _SOURCE sidecar files.
    research_only _LICENSE includes fair-use clause + no-redistribution statement.
    """
    target = out_dir / license_class / source_name
    target.mkdir(parents=True, exist_ok=True)

    for doc in docs:
        fm = _render_frontmatter(doc)
        content = f"{fm}\n\n{doc.text}\n"
        (target / f"{doc.id}.md").write_text(content, encoding="utf-8")

    # Write sidecar files based on first doc (they share source + license)
    if docs:
        first = docs[0]
        if license_class == "research_only":
            lic_text = (
                f"{first.license}\n"
                f"Source: {first.source_url}\n"
                f"Fetched: {first.fetch_date}\n"
                f"License class: research_only\n"
                f"Fair-use research excerpt — eval use only.\n"
                f"No-redistribution clause: do not publish these excerpts.\n"
                f"Attribution required; source URL above.\n"
            )
        else:
            lic_text = (
                f"{first.license}\n"
                f"Source: {first.source_url}\n"
                f"Fetched: {first.fetch_date}\n"
            )
        (target / "_LICENSE").write_text(lic_text, encoding="utf-8")
        (target / "_SOURCE").write_text(
            f"source_name: {source_name}\n"
            f"license_class: {license_class}\n"
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
# HTML paragraph extractor (stdlib html.parser — no external deps)
# ---------------------------------------------------------------------------

class _ParagraphExtractor(HTMLParser):
    """Extract visible <p> text from HTML, skipping script/style/nav."""

    _SKIP_TAGS = {"script", "style", "nav", "header", "footer", "aside", "noscript"}

    def __init__(self) -> None:
        super().__init__()
        self.paragraphs: list[str] = []
        self._current: list[str] = []
        self._in_p = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
        if tag == "p" and self._skip_depth == 0:
            self._in_p = True
            self._current = []

    def handle_endtag(self, tag: str) -> None:
        if tag in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag == "p" and self._in_p:
            text = " ".join(self._current).strip()
            if len(text.split()) >= 8:
                self.paragraphs.append(text)
            self._in_p = False
            self._current = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and self._in_p:
            stripped = data.strip()
            if stripped:
                self._current.append(stripped)


def _extract_html_paragraphs(html_bytes: bytes, max_words: int = 400) -> str:
    """Extract visible paragraph text from HTML. Returns at most max_words words."""
    try:
        html_str = html_bytes.decode("utf-8", errors="replace")
    except Exception:
        return ""

    extractor = _ParagraphExtractor()
    try:
        extractor.feed(html_str)
    except Exception:
        pass

    combined = " ".join(extractor.paragraphs)
    words = combined.split()[:max_words]
    return " ".join(words)


# ---------------------------------------------------------------------------
# Generic research_only URL-list fetcher
# ---------------------------------------------------------------------------

def _fetch_url_list_as_research(
    urls: list[str],
    prefix: str,
    domain: str,
    n: int,
    *,
    seed: int = 42,
    source_name: str = "",
    max_words: int = RESEARCH_MAX_WORDS,
    min_words: int = 50,
) -> list[Document]:
    """Fetch a hardcoded list of URLs as research_only fair-use excerpts."""
    rng = random.Random(seed)
    urls_shuffled = urls[:]
    rng.shuffle(urls_shuffled)
    docs: list[Document] = []

    for url in urls_shuffled:
        if len(docs) >= n:
            break
        try:
            raw = _get(url)
        except Exception as exc:
            print(f"[fetch_de_human_corpus] {prefix} skip {url}: {exc}", file=sys.stderr)
            continue

        text = _extract_html_paragraphs(raw, max_words=max_words)
        trimmed = _trim_to_words(text, max_words=max_words, min_words=min_words)
        if not trimmed:
            continue

        doc_id = _make_id(prefix, url.rstrip("/").split("/")[-1] or url.split("/")[-2])
        docs.append(Document(
            id=doc_id,
            text=trimmed,
            source_url=url,
            license="copyright",
            fetch_date=TODAY,
            license_class="research_only",
            metadata={"domain": domain, "source": source_name or prefix},
        ))

    return docs


# ---------------------------------------------------------------------------
# SSOAR academic fetcher (redistributable)
# ---------------------------------------------------------------------------

def fetch_ssoar_academic(n: int = 5, *, seed: int = 42) -> list[Document]:
    """SSOAR OAI-PMH ListRecords — DE-language CC-BY social science abstracts."""
    OAI_NS = "http://www.openarchives.org/OAI/2.0/"
    DC_NS = "http://purl.org/dc/elements/1.1/"
    OAI_DC_NS = "http://www.openarchives.org/OAI/2.0/oai_dc/"

    params = {
        "verb": "ListRecords",
        "metadataPrefix": "oai_dc",
        "set": "collection:open_access",
    }
    try:
        raw = _get(SSOAR_OAI_URL, params)
    except Exception as exc:
        print(f"[fetch_de_human_corpus] SSOAR fetch failed: {exc}", file=sys.stderr)
        return []

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        print(f"[fetch_de_human_corpus] SSOAR XML parse error: {exc}", file=sys.stderr)
        return []

    docs: list[Document] = []

    for record in root.iter(f"{{{OAI_NS}}}record"):
        if len(docs) >= n:
            break

        metadata_el = record.find(f"{{{OAI_NS}}}metadata")
        if metadata_el is None:
            continue
        dc = metadata_el.find(f"{{{OAI_DC_NS}}}dc")
        if dc is None:
            continue

        lang_el = dc.find(f"{{{DC_NS}}}language")
        if lang_el is None or (lang_el.text or "").strip().lower() not in ("de", "ger", "deu"):
            continue

        title_el = dc.find(f"{{{DC_NS}}}title")
        desc_el = dc.find(f"{{{DC_NS}}}description")
        id_el = dc.find(f"{{{DC_NS}}}identifier")
        rights_el = dc.find(f"{{{DC_NS}}}rights")

        title = (title_el.text or "").strip() if title_el is not None else ""
        description = (desc_el.text or "").strip() if desc_el is not None else ""
        url = (id_el.text or "").strip() if id_el is not None else SSOAR_OAI_URL
        if not url.startswith("http"):
            url = f"https://www.ssoar.info/ssoar/handle/document/{url}"
        rights = (rights_el.text or "CC-BY").strip() if rights_el is not None else "CC-BY"

        text = f"{title}\n\n{description}".strip() if title else description
        trimmed = _trim_to_words(text)
        if not trimmed:
            continue

        doc_id = _make_id("ssoar_academic", title or url.split("/")[-1])
        docs.append(Document(
            id=doc_id,
            text=trimmed,
            source_url=url,
            license=rights,
            fetch_date=TODAY,
            license_class="redistributable",
            metadata={"domain": "academic", "source": "ssoar"},
        ))

    return docs


# ---------------------------------------------------------------------------
# BGBl / Gesetze-im-Internet legal fetcher (redistributable, PD §5 UrhG)
# ---------------------------------------------------------------------------

_BGBL_URLS = [
    "https://www.gesetze-im-internet.de/gg/art_1.html",
    "https://www.gesetze-im-internet.de/gg/art_20.html",
    "https://www.gesetze-im-internet.de/bgb/__242.html",
    "https://www.gesetze-im-internet.de/bgb/__1.html",
    "https://www.gesetze-im-internet.de/stgb/__1.html",
    "https://www.gesetze-im-internet.de/stvo_2013/__1.html",
]

_BGBL_LICENSE = "PD-§5-UrhG"


def fetch_bgbl_legal(n: int = 5, *, seed: int = 42) -> list[Document]:
    """Fetch BGBl / Gesetze-im-Internet paragraphs (PD per §5 UrhG)."""
    rng = random.Random(seed)
    urls = _BGBL_URLS[:]
    rng.shuffle(urls)
    docs: list[Document] = []

    for url in urls:
        if len(docs) >= n:
            break
        try:
            raw = _get(url)
        except Exception as exc:
            print(f"[fetch_de_human_corpus] bgbl skip {url}: {exc}", file=sys.stderr)
            continue

        text = _extract_html_paragraphs(raw, max_words=600)
        trimmed = _trim_to_words(text)
        if not trimmed:
            continue

        slug = url.rstrip("/").rsplit("/", 2)
        doc_id = _make_id("bgbl_legal", "_".join(slug[-2:]))
        docs.append(Document(
            id=doc_id,
            text=trimmed,
            source_url=url,
            license=_BGBL_LICENSE,
            fetch_date=TODAY,
            license_class="redistributable",
            metadata={"domain": "legal", "source": "bgbl"},
        ))

    return docs


# ---------------------------------------------------------------------------
# Rechtsprechung-im-Internet legal fetcher (redistributable, PD §5 UrhG)
# ---------------------------------------------------------------------------

_RECHT_URLS = [
    "https://www.bundesverfassungsgericht.de/SharedDocs/Entscheidungen/DE/"
    "2023/03/rs20230328_1bvr251822.html",
    "https://www.bundesverfassungsgericht.de/SharedDocs/Entscheidungen/DE/"
    "2022/11/rs20221116_1bvr124222.html",
    "https://www.bundesverfassungsgericht.de/SharedDocs/Entscheidungen/DE/"
    "2021/10/rs20211026_1bvr178215.html",
]


def fetch_rechtsprechung_legal(n: int = 3, *, seed: int = 42) -> list[Document]:
    """Fetch court decision excerpts (BVerfG — PD §5 UrhG)."""
    rng = random.Random(seed)
    urls = _RECHT_URLS[:]
    rng.shuffle(urls)
    docs: list[Document] = []

    for url in urls:
        if len(docs) >= n:
            break
        try:
            raw = _get(url)
        except Exception as exc:
            print(f"[fetch_de_human_corpus] rechtsprechung skip {url}: {exc}", file=sys.stderr)
            continue

        text = _extract_html_paragraphs(raw, max_words=600)
        trimmed = _trim_to_words(text)
        if not trimmed:
            continue

        doc_id = _make_id("rechtsprechung_legal", url.rstrip("/").split("/")[-1][:40])
        docs.append(Document(
            id=doc_id,
            text=trimmed,
            source_url=url,
            license="PD-§5-UrhG",
            fetch_date=TODAY,
            license_class="redistributable",
            metadata={"domain": "legal", "source": "rechtsprechung"},
        ))

    return docs


# ---------------------------------------------------------------------------
# Bundestag plenary protocol fetcher (redistributable, PD §5 UrhG)
# ---------------------------------------------------------------------------

def fetch_bundestag_legal(n: int = 3, *, seed: int = 42) -> list[Document]:
    """Fetch Bundestag plenary protocol excerpts via DIP API (PD §5 UrhG)."""
    params = {
        "format": "json",
        "rows": "10",
        "cursor": "*",
    }
    try:
        raw = _get(BUNDESTAG_API, params)
        data = json.loads(raw)
    except Exception as exc:
        print(f"[fetch_de_human_corpus] Bundestag API failed: {exc}", file=sys.stderr)
        return []

    docs: list[Document] = []
    items = data.get("documents", data.get("items", []))

    for item in items:
        if len(docs) >= n:
            break

        title = item.get("titel", item.get("title", ""))
        text_raw = item.get("text", item.get("inhalt", ""))
        fundstelle = item.get("fundstelle", {})
        if isinstance(fundstelle, dict):
            url = fundstelle.get("pdf_url", "")
        else:
            url = ""
        if not url:
            url = item.get("downloadUrl", BUNDESTAG_API)

        combined = f"{title}\n\n{text_raw}".strip() if title else text_raw
        trimmed = _trim_to_words(combined)
        if not trimmed:
            continue

        doc_id = _make_id("bundestag_legal", title or url.split("/")[-1])
        docs.append(Document(
            id=doc_id,
            text=trimmed,
            source_url=url or BUNDESTAG_API,
            license="PD-§5-UrhG",
            fetch_date=TODAY,
            license_class="redistributable",
            metadata={"domain": "legal", "source": "bundestag"},
        ))

    return docs


# ---------------------------------------------------------------------------
# Linuxwiki.de technical fetcher (redistributable, GFDL)
# ---------------------------------------------------------------------------

_LINUXWIKI_CATEGORIES = [
    "Befehle",
    "Konfiguration",
    "Netzwerk",
    "Sicherheit",
    "Paketmanager",
]


def fetch_linuxwiki_technical(n: int = 5, *, seed: int = 42) -> list[Document]:
    """Linuxwiki.de MediaWiki articles — DE technical docs register (GFDL)."""
    rng = random.Random(seed)

    titles: list[str] = []
    for cat in _LINUXWIKI_CATEGORIES:
        members = _wiki_category_members(LINUXWIKI_API, cat, limit=20)
        titles.extend(members)

    if not titles:
        # Fallback: allpages query
        params = {
            "action": "query",
            "format": "json",
            "list": "allpages",
            "aplimit": "50",
            "apnamespace": "0",
        }
        try:
            data = _get_json(LINUXWIKI_API, params)
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

        # Try with date filter first, then without (linuxwiki is small)
        wikitext = _wiki_revision_pre_date(LINUXWIKI_API, title, end_iso=WIKI_DATE_CUTOFF)
        if not wikitext:
            params = {
                "action": "query",
                "format": "json",
                "prop": "revisions",
                "titles": title,
                "rvprop": "content",
                "rvlimit": "1",
            }
            try:
                data = _get_json(LINUXWIKI_API, params)
                pages = data["query"]["pages"]
                page = next(iter(pages.values()))
                revs = page.get("revisions", [])
                wikitext = (revs[0].get("*") or revs[0].get("content", "")) if revs else ""
            except Exception:  # noqa: BLE001
                continue

        if not wikitext:
            continue

        plain = _strip_wikitext(wikitext)
        trimmed = _trim_to_words(plain)
        if not trimmed:
            continue

        doc_id = _make_id("linuxwiki_technical", title)
        article_url = (
            f"https://linuxwiki.de/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
        )
        docs.append(Document(
            id=doc_id,
            text=trimmed,
            source_url=article_url,
            license="GFDL",
            fetch_date=TODAY,
            license_class="redistributable",
            metadata={"title": title, "wiki": "linuxwiki.de", "domain": "technical"},
        ))

    return docs


# ---------------------------------------------------------------------------
# Wikipedia DE technical articles fetcher (redistributable, CC-BY-SA-3.0)
# ---------------------------------------------------------------------------

_WIKI_TECHNICAL_CATEGORIES = [
    "Informatik",
    "Programmiersprache",
    "Betriebssystem",
    "Computernetzwerk",
    "Datenbank",
    "Softwareentwicklung",
]


def fetch_wikipedia_technical(n: int = 6, *, seed: int = 42) -> list[Document]:
    """Wikipedia DE technical articles (Kategorie:Informatik etc.) — CC-BY-SA-3.0."""
    rng = random.Random(seed)

    titles: list[str] = []
    for cat in _WIKI_TECHNICAL_CATEGORIES:
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

        doc_id = _make_id("wiki_technical", title)
        docs.append(Document(
            id=doc_id,
            text=trimmed,
            source_url=_wiki_article_url(title),
            license="CC-BY-SA-3.0",
            fetch_date=TODAY,
            license_class="redistributable",
            metadata={
                "title": title,
                "wiki": "de.wikipedia",
                "domain": "technical",
                "pre_date_cutoff": WIKI_DATE_CUTOFF,
            },
        ))

    return docs


# ---------------------------------------------------------------------------
# GitHub OSS technical README fetcher (redistributable — fixed from wave 1)
# ---------------------------------------------------------------------------

# Curated well-known DE-documented OSS projects
_GITHUB_OSS_REPOS = [
    "sebastianbergmann/phpunit",
    "nikic/FastRoute",
    "symfony/symfony",
    "doctrine/orm",
    "guzzle/guzzle",
    "laravel/laravel",
    "composer/composer",
    "nextcloud/server",
    "friendica/friendica",
    "kimai2/kimai",
    "wger-project/wger",
]


def fetch_github_oss_technical(n: int = 6, *, seed: int = 42) -> list[Document]:
    """GitHub OSS project READMEs with DE-language content — technical register."""
    rng = random.Random(seed)

    repos_to_try = _GITHUB_OSS_REPOS[:]

    # Also try topic search
    search_result = _github_get("/search/repositories", {
        "q": "topic:deutsch stars:>20",
        "per_page": "15",
    })
    if search_result:
        for r in search_result.get("items", []):
            repos_to_try.append(r["full_name"])

    rng.shuffle(repos_to_try)
    docs: list[Document] = []

    for repo_name in repos_to_try:
        if len(docs) >= n:
            break

        repo_data = _github_get(f"/repos/{repo_name}")
        if not repo_data:
            continue

        readme = _github_fetch_readme(repo_name)
        if not readme:
            continue
        if not _is_de_text(readme):
            continue

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

        repo_url = repo_data.get("html_url", f"https://github.com/{repo_name}")
        license_info = (repo_data.get("license") or {}).get("spdx_id") or "per-repo"
        doc_id = _make_id("github_oss_technical", repo_name.replace("/", "_"))

        docs.append(Document(
            id=doc_id,
            text=trimmed,
            source_url=repo_url + "/blob/main/README.md",
            license=license_info,
            fetch_date=TODAY,
            license_class="redistributable",
            metadata={
                "repo": repo_name,
                "stars": repo_data.get("stargazers_count", 0),
                "domain": "technical",
            },
        ))

    return docs


# ---------------------------------------------------------------------------
# Bundesregierung career fetcher (redistributable, PD §5 UrhG)
# ---------------------------------------------------------------------------

_BUNDESREGIERUNG_URLS = [
    "https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett/"
    "bundesminister-fuer-finanzen",
    "https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett/"
    "bundesministerin-fuer-bildung-und-forschung",
    "https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett/"
    "bundesminister-des-auswaertigen",
    "https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett/"
    "bundesminister-fuer-wirtschaft-und-klimaschutz",
    "https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett/"
    "bundesministerin-der-justiz",
    "https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett/"
    "bundesminister-der-verteidigung",
]


def fetch_bundesregierung_career(n: int = 5, *, seed: int = 42) -> list[Document]:
    """Bundesregierung minister biography pages (PD §5 UrhG)."""
    rng = random.Random(seed)
    urls = _BUNDESREGIERUNG_URLS[:]
    rng.shuffle(urls)
    docs: list[Document] = []

    for url in urls:
        if len(docs) >= n:
            break
        try:
            raw = _get(url)
        except Exception as exc:
            print(f"[fetch_de_human_corpus] bundesregierung skip {url}: {exc}", file=sys.stderr)
            continue

        text = _extract_html_paragraphs(raw, max_words=600)
        trimmed = _trim_to_words(text)
        if not trimmed:
            continue

        slug = url.rstrip("/").split("/")[-1]
        doc_id = _make_id("bundesregierung_career", slug)
        docs.append(Document(
            id=doc_id,
            text=trimmed,
            source_url=url,
            license="PD-§5-UrhG",
            fetch_date=TODAY,
            license_class="redistributable",
            metadata={"domain": "career", "source": "bundesregierung"},
        ))

    return docs


# ---------------------------------------------------------------------------
# Stack Exchange DE career fetcher (redistributable, CC-BY-SA-4.0)
# ---------------------------------------------------------------------------

class _HTMLTextExtractor(HTMLParser):
    """Strip HTML tags, collect text."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def fetch_stackexchange_career(n: int = 5, *, seed: int = 42) -> list[Document]:
    """Stack Exchange DE users' 'About me' bios — CC-BY-SA-4.0."""
    params = {
        "order": "desc",
        "sort": "reputation",
        "site": "de.stackoverflow",
        "filter": "!9_bDDxJY5",  # filter that includes about_me field
        "pagesize": "30",
        "page": "1",
    }
    try:
        raw = _get(STACKEXCHANGE_API, params)
        data = json.loads(raw)
    except Exception as exc:
        print(f"[fetch_de_human_corpus] StackExchange fetch failed: {exc}", file=sys.stderr)
        return []

    docs: list[Document] = []
    for item in data.get("items", []):
        if len(docs) >= n:
            break

        about_me = item.get("about_me", "")
        if not about_me:
            continue

        extractor = _HTMLTextExtractor()
        try:
            extractor.feed(about_me)
        except Exception:  # noqa: BLE001
            pass
        plain = " ".join(extractor.parts).strip()
        plain = re.sub(r"\s+", " ", plain)

        if not _is_de_text(plain):
            continue

        trimmed = _trim_to_words(plain)
        if not trimmed:
            continue

        user_id = item.get("user_id", "unknown")
        name = item.get("display_name", str(user_id))
        url = item.get("link", f"https://de.stackoverflow.com/users/{user_id}")
        doc_id = _make_id("stackexchange_career", str(user_id))

        docs.append(Document(
            id=doc_id,
            text=trimmed,
            source_url=url,
            license="CC-BY-SA-4.0",
            fetch_date=TODAY,
            license_class="redistributable",
            metadata={"domain": "career", "source": "stackexchange_de", "user": name},
        ))

    return docs


# ---------------------------------------------------------------------------
# GitHub profile career fetcher (redistributable — fixed from wave 1)
# ---------------------------------------------------------------------------

_GITHUB_PROFILE_QUERIES = [
    "in:readme Ich bin Softwareentwickler language:Markdown",
    "in:readme Hallo ich bin Entwickler language:Markdown",
    "in:readme Software-Entwickler Kenntnisse language:Markdown",
    "in:readme Willkommen auf meinem GitHub-Profil language:Markdown",
    "in:readme ich studiere Informatik language:Markdown",
]


def fetch_github_profile_career(n: int = 6, *, seed: int = 42) -> list[Document]:
    """GitHub user profile READMEs (<user>/<user>) with DE career content."""
    rng = random.Random(seed)

    repos: dict[str, dict] = {}
    for q in _GITHUB_PROFILE_QUERIES:
        found = _github_search_repos(q, n=15)
        for r in found:
            repos[r["full_name"]] = r
        if len(repos) >= n * 5:
            break

    repo_list = list(repos.values())
    # Prefer profile repos: owner == repo_name (case-insensitive)
    profile_repos = [
        r for r in repo_list
        if r["full_name"].split("/")[0].lower() == r["full_name"].split("/")[1].lower()
    ]
    if len(profile_repos) < n:
        profile_repos = repo_list

    rng.shuffle(profile_repos)
    docs: list[Document] = []

    for repo in profile_repos:
        if len(docs) >= n:
            break

        readme = _github_fetch_readme(repo["full_name"])
        if not readme:
            continue
        if not _is_de_text(readme):
            continue

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
        license_info = (repo.get("license") or {}).get("spdx_id") or "per-repo"
        doc_id = _make_id("github_profile_career", repo["full_name"].replace("/", "_"))

        docs.append(Document(
            id=doc_id,
            text=trimmed,
            source_url=repo_url + "/blob/main/README.md",
            license=license_info,
            fetch_date=TODAY,
            license_class="redistributable",
            metadata={
                "repo": repo["full_name"],
                "stars": repo.get("stargazers_count", 0),
                "domain": "career",
            },
        ))

    return docs


# ---------------------------------------------------------------------------
# Research-only marketing fetchers (Apple, Samsung, Microsoft, Startnext)
# ---------------------------------------------------------------------------

_APPLE_URLS = [
    "https://www.apple.com/de/iphone/",
    "https://www.apple.com/de/macbook-air/",
    "https://www.apple.com/de/ipad-pro/",
    "https://www.apple.com/de/apple-watch/",
    "https://www.apple.com/de/airpods-pro/",
]

_SAMSUNG_URLS = [
    "https://www.samsung.com/de/smartphones/",
    "https://www.samsung.com/de/tvs/all-tvs/",
    "https://www.samsung.com/de/tablets/",
    "https://www.samsung.com/de/monitors/",
]

_MICROSOFT_URLS = [
    "https://www.microsoft.com/de-de/surface/",
    "https://www.microsoft.com/de-de/microsoft-365/",
    "https://www.microsoft.com/de-de/windows/",
    "https://azure.microsoft.com/de-de/",
]

_STARTNEXT_URLS = [
    "https://www.startnext.com/projekte/aktuell",
    "https://www.startnext.com/entdecken",
    "https://www.startnext.com/projekte/soziales",
]


def fetch_apple_marketing(n: int = 4, *, seed: int = 42) -> list[Document]:
    """Apple DE product pages — fair-use research excerpts (copyright)."""
    return _fetch_url_list_as_research(
        _APPLE_URLS, "apple_marketing", "marketing", n, seed=seed, source_name="apple_de"
    )


def fetch_samsung_marketing(n: int = 3, *, seed: int = 42) -> list[Document]:
    """Samsung DE product pages — fair-use research excerpts (copyright)."""
    return _fetch_url_list_as_research(
        _SAMSUNG_URLS, "samsung_marketing", "marketing", n, seed=seed, source_name="samsung_de"
    )


def fetch_microsoft_marketing(n: int = 3, *, seed: int = 42) -> list[Document]:
    """Microsoft DE product pages — fair-use research excerpts (copyright)."""
    return _fetch_url_list_as_research(
        _MICROSOFT_URLS, "microsoft_marketing", "marketing", n, seed=seed, source_name="microsoft_de"
    )


def fetch_startnext_marketing(n: int = 3, *, seed: int = 42) -> list[Document]:
    """Startnext crowdfunding campaign pages — fair-use research excerpts."""
    return _fetch_url_list_as_research(
        _STARTNEXT_URLS, "startnext_marketing", "marketing", n, seed=seed, source_name="startnext"
    )


# ---------------------------------------------------------------------------
# Research-only casual fetchers (Reddit, travel blogs, lifestyle blogs)
# ---------------------------------------------------------------------------

def fetch_reddit_de_casual(n: int = 5, *, seed: int = 42) -> list[Document]:
    """Reddit r/de top posts — fair-use research excerpts (small selftext excerpts)."""
    params = {"t": "all", "limit": "25"}
    try:
        raw = _get(REDDIT_DE_URL, params)
        data = json.loads(raw)
    except Exception as exc:
        print(f"[fetch_de_human_corpus] Reddit fetch failed: {exc}", file=sys.stderr)
        return []

    docs: list[Document] = []
    for child in data.get("data", {}).get("children", []):
        if len(docs) >= n:
            break

        post = child.get("data", {})
        title = post.get("title", "")
        selftext = post.get("selftext", "")
        post_id = post.get("id", "unknown")
        url = post.get("url", f"https://www.reddit.com/r/de/comments/{post_id}")

        combined = f"{title}. {selftext}".strip() if selftext else title
        if not combined or not _is_de_text(combined):
            continue

        words = combined.split()[:REDDIT_MAX_WORDS]
        trimmed = " ".join(words)
        if len(trimmed.split()) < 30:
            continue

        doc_id = _make_id("reddit_de_casual", post_id)
        docs.append(Document(
            id=doc_id,
            text=trimmed,
            source_url=url,
            license="copyright",
            fetch_date=TODAY,
            license_class="research_only",
            metadata={"domain": "casual", "source": "reddit_r_de", "post_id": post_id},
        ))

    return docs


_TRAVEL_BLOG_URLS = [
    "https://www.fernweh-aktuell.de",
    "https://abenteuer-und-reisen.de",
    "https://www.reisereporter.de",
    "https://www.urlaubsguru.de/reiseblog/",
]

_LIFESTYLE_BLOG_URLS = [
    "https://lilies-diary.com",
    "https://journelles.com",
    "https://www.luziapimpinella.com",
]


def fetch_travel_blogs_casual(n: int = 3, *, seed: int = 42) -> list[Document]:
    """German travel blogs — fair-use research excerpts (copyright)."""
    return _fetch_url_list_as_research(
        _TRAVEL_BLOG_URLS, "travel_blogs_casual", "casual", n,
        seed=seed, source_name="travel_blogs",
    )


def fetch_lifestyle_blogs_casual(n: int = 3, *, seed: int = 42) -> list[Document]:
    """German lifestyle blogs — fair-use research excerpts (copyright)."""
    return _fetch_url_list_as_research(
        _LIFESTYLE_BLOG_URLS, "lifestyle_blogs_casual", "casual", n,
        seed=seed, source_name="lifestyle_blogs",
    )


# ---------------------------------------------------------------------------
# Research-only career fetchers (Karrierebibel, Bewerbung.com)
# ---------------------------------------------------------------------------

_KARRIEREBIBEL_URLS = [
    "https://karrierebibel.de/anschreiben-muster/",
    "https://karrierebibel.de/lebenslauf-muster/",
    "https://karrierebibel.de/motivationsschreiben/",
    "https://karrierebibel.de/selbstpraesentation/",
]

_BEWERBUNG_URLS = [
    "https://www.bewerbung.com/anschreiben/muster/",
    "https://www.bewerbung.com/lebenslauf/muster/",
    "https://www.bewerbung.com/bewerbungsschreiben/",
]


def fetch_karrierebibel_career(n: int = 3, *, seed: int = 42) -> list[Document]:
    """Karrierebibel.de Anschreiben sample pages — research_only (copyright)."""
    return _fetch_url_list_as_research(
        _KARRIEREBIBEL_URLS, "karrierebibel_career", "career", n,
        seed=seed, source_name="karrierebibel",
    )


def fetch_bewerbung_career(n: int = 3, *, seed: int = 42) -> list[Document]:
    """Bewerbung.com sample Anschreiben pages — research_only (copyright)."""
    return _fetch_url_list_as_research(
        _BEWERBUNG_URLS, "bewerbung_career", "career", n,
        seed=seed, source_name="bewerbung_com",
    )


# ---------------------------------------------------------------------------
# Research-only technical fetcher (Heise developer)
# ---------------------------------------------------------------------------

_HEISE_URLS = [
    "https://www.heise.de/developer/",
    "https://www.heise.de/news/",
    "https://www.heise.de/ct/",
    "https://www.heise.de/ix/",
]


def fetch_heise_technical(n: int = 4, *, seed: int = 42) -> list[Document]:
    """Heise developer / c't article pages — research_only (copyright)."""
    return _fetch_url_list_as_research(
        _HEISE_URLS, "heise_technical", "technical", n,
        seed=seed, source_name="heise_de",
    )


# ---------------------------------------------------------------------------
# Legacy directory migration helper
# ---------------------------------------------------------------------------

_LEGACY_MOVES: list[tuple[str, str, str]] = [
    # (old_flat_subdir, new_license_class, new_subdir)
    ("wikipedia_academic",    "redistributable", "wikipedia_academic"),
    ("wikipedia_career",      "redistributable", "wikipedia_career"),
    ("ubuntuusers_technical", "redistributable", "ubuntuusers_technical"),
]

_LEGACY_DELETES: list[str] = [
    "wikipedia_casual",
    "wikipedia_marketing",   # flat — re-fetched into redistributable/wikipedia_marketing/
    "github_marketing",
    "github_career",
]


def _migrate_legacy_dirs(corpus_root: Path) -> None:
    """One-time migration: move flat legacy subdirs to redistributable/ subdirs.

    Also deletes known bad first-wave directories.
    Idempotent — each operation is skipped if source no longer exists.
    """
    for old_sub, lc, new_sub in _LEGACY_MOVES:
        src = corpus_root / old_sub
        dst = corpus_root / lc / new_sub
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            print(f"[fetch_de_human_corpus] Migrated {src} → {dst}", file=sys.stderr)

    for del_sub in _LEGACY_DELETES:
        target = corpus_root / del_sub
        if target.exists():
            shutil.rmtree(target)
            print(f"[fetch_de_human_corpus] Deleted legacy dir {target}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Source registry
# ---------------------------------------------------------------------------

# Map from --source name → (fetcher_fn, n, subdir_name, license_class)
_SOURCES: dict[str, tuple] = {
    # --- academic ---
    "wikipedia_academic":    (fetch_wikipedia_de_academic,   8, "wikipedia_academic",    "redistributable"),
    "ssoar_academic":        (fetch_ssoar_academic,          5, "ssoar_academic",         "redistributable"),
    # --- legal ---
    "bgbl_legal":            (fetch_bgbl_legal,              5, "bgbl_legal",             "redistributable"),
    "rechtsprechung_legal":  (fetch_rechtsprechung_legal,    3, "rechtsprechung_legal",   "redistributable"),
    "bundestag_legal":       (fetch_bundestag_legal,         3, "bundestag_legal",        "redistributable"),
    # --- technical (redistributable) ---
    "ubuntuusers_technical": (fetch_ubuntuusers_technical,   8, "ubuntuusers_technical",  "redistributable"),
    "linuxwiki_technical":   (fetch_linuxwiki_technical,     5, "linuxwiki_technical",    "redistributable"),
    "wikipedia_technical":   (fetch_wikipedia_technical,     6, "wikipedia_technical",    "redistributable"),
    "github_oss_technical":  (fetch_github_oss_technical,    6, "github_oss_technical",   "redistributable"),
    # --- marketing (redistributable) ---
    "wikipedia_marketing":   (fetch_wikipedia_de_marketing,  8, "wikipedia_marketing",    "redistributable"),
    # --- career (redistributable) ---
    "wikipedia_career":      (fetch_wikipedia_de_career,     8, "wikipedia_career",       "redistributable"),
    "bundesregierung_career":(fetch_bundesregierung_career,  5, "bundesregierung_career", "redistributable"),
    "stackexchange_career":  (fetch_stackexchange_career,    5, "stackexchange_career",   "redistributable"),
    "github_profile_career": (fetch_github_profile_career,   6, "github_profile_career",  "redistributable"),
    # --- marketing (research_only) ---
    "apple_marketing":       (fetch_apple_marketing,         4, "apple_marketing",        "research_only"),
    "samsung_marketing":     (fetch_samsung_marketing,       3, "samsung_marketing",      "research_only"),
    "microsoft_marketing":   (fetch_microsoft_marketing,     3, "microsoft_marketing",    "research_only"),
    "startnext_marketing":   (fetch_startnext_marketing,     3, "startnext_marketing",    "research_only"),
    # --- casual (research_only) ---
    "reddit_de_casual":      (fetch_reddit_de_casual,        5, "reddit_casual",          "research_only"),
    "travel_blogs_casual":   (fetch_travel_blogs_casual,     3, "travel_blogs_casual",    "research_only"),
    "lifestyle_blogs_casual":(fetch_lifestyle_blogs_casual,  3, "lifestyle_blogs_casual", "research_only"),
    # --- career (research_only) ---
    "karrierebibel_career":  (fetch_karrierebibel_career,    3, "karrierebibel_career",   "research_only"),
    "bewerbung_career":      (fetch_bewerbung_career,        3, "bewerbung_career",        "research_only"),
    # --- technical (research_only) ---
    "heise_technical":       (fetch_heise_technical,         4, "heise_technical",        "research_only"),
}

# Default output root (can be overridden via --out-dir)
_DEFAULT_OUT_DIR = Path("evals") / "corpus" / "de" / "human"


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _list_sources_report() -> None:
    """Print sources grouped by license_class."""
    print("=== fetch_de_human_corpus — Available Sources ===")
    print()
    for lc in ("redistributable", "research_only"):
        print(f"[{lc}]")
        for name, (fn, n, subdir, source_lc) in _SOURCES.items():
            if source_lc == lc:
                print(f"  --source {name:<35}  n={n}  → {lc}/{subdir}/")
        print()


def _dry_run_report(target: str = "all") -> None:
    """Print a plan of what would be fetched."""
    print("=== fetch_de_human_corpus — DRY RUN ===")
    print(f"Output root: {_DEFAULT_OUT_DIR}")
    print(f"Target: {target}")
    print()
    total = 0
    for name, (fn, n, subdir, lc) in _SOURCES.items():
        if target != "all" and lc != target:
            continue
        print(f"  {name:<40}  n={n}  [{lc}] → {lc}/{subdir}/")
        total += n
    print()
    print(f"Total target documents: {total}")
    print()
    print("License classes:")
    print("  redistributable — CC / PD sources; committed to git")
    print("  research_only   — fair-use excerpts; gitignored (evals/corpus/de/human/research_only/)")
    print()
    print("Domain coverage:")
    print("  academic    → wikipedia_academic, ssoar_academic")
    print("  legal       → bgbl_legal, rechtsprechung_legal, bundestag_legal")
    print("  technical   → ubuntuusers_technical, linuxwiki_technical, wikipedia_technical,")
    print("                github_oss_technical, heise_technical")
    print("  marketing   → wikipedia_marketing, apple_marketing, samsung_marketing,")
    print("                microsoft_marketing, startnext_marketing")
    print("  career      → wikipedia_career, bundesregierung_career, stackexchange_career,")
    print("                github_profile_career, karrierebibel_career, bewerbung_career")
    print("  casual      → reddit_de_casual, travel_blogs_casual, lifestyle_blogs_casual")
    print()
    print(f"Network etiquette: 0.6-0.7 s sleep between requests, retry once.")
    print(f"GitHub request cap: {GITHUB_MAX_REQUESTS} total (unauthenticated limit).")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fetch_de_human_corpus",
        description=(
            "Fetch real-world DE human corpus from register-accurate sources. "
            "Writes markdown files + sidecar files to "
            "evals/corpus/de/human/{redistributable,research_only}/<source>/."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m evals.scripts.fetch_de_human_corpus --source all\n"
            "  python -m evals.scripts.fetch_de_human_corpus --target redistributable\n"
            "  python -m evals.scripts.fetch_de_human_corpus --list-sources\n"
            "  python -m evals.scripts.fetch_de_human_corpus --dry-run\n"
        ),
    )
    parser.add_argument(
        "--source",
        choices=list(_SOURCES.keys()) + ["all"],
        default="all",
        help=(
            "Which source to fetch. 'all' fetches all sources (default: all). "
            "Use --list-sources to see all choices."
        ),
    )
    parser.add_argument(
        "--target",
        choices=["redistributable", "research_only", "all"],
        default="all",
        help="Filter sources by license class (default: all).",
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="Print available sources grouped by license_class and exit.",
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


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.list_sources:
        _list_sources_report()
        return

    if args.dry_run:
        _dry_run_report(target=args.target)
        return

    out_dir = Path(args.out_dir)
    seed = args.seed

    # One-time migration of legacy flat dirs
    _migrate_legacy_dirs(out_dir)

    if args.source != "all":
        sources_to_run = [args.source]
    else:
        sources_to_run = [
            name for name, (_, _, _, lc) in _SOURCES.items()
            if args.target == "all" or lc == args.target
        ]

    for name in sources_to_run:
        fn, n, subdir, lc = _SOURCES[name]
        print(f"[fetch_de_human_corpus] Fetching {name} (n={n}) …", file=sys.stderr)
        try:
            docs = fn(n=n, seed=seed)
            write_corpus(docs, out_dir, subdir, license_class=lc)
        except Exception as exc:  # noqa: BLE001
            print(
                f"[fetch_de_human_corpus] ERROR fetching {name}: {exc}",
                file=sys.stderr,
            )


if __name__ == "__main__":
    main()
