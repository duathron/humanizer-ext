"""Shared utilities for the eval runners (pattern, false-positive, E2E).

No I/O at import time. All functions are pure unless they explicitly call
the claude CLI or write reports.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Case:
    """One eval case — an input + the expected effect of the skill on it.

    `expected_changes` are substrings the rewrite should remove or transform.
    `expected_unchanged` are substrings the rewrite must preserve (e.g.,
    technical terms in technical-domain cases).
    """

    id: str
    input: str
    expected_changes: list[str]
    expected_unchanged: list[str]
    domain: str
    metadata: dict[str, Any] = field(default_factory=dict)


def load_pattern_corpus(corpus_dir: Path) -> list[Case]:
    """Load all pattern_*.json files from corpus_dir into a flat list of Cases.

    Each file describes one pattern and contains a `cases` array. Pattern
    metadata (pattern_id, pattern_name, lang) is copied into each Case's
    metadata dict for downstream filtering.
    """
    cases: list[Case] = []
    for path in sorted(corpus_dir.glob("pattern_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        common_meta = {
            "pattern_id": payload["pattern_id"],
            "pattern_name": payload["pattern_name"],
            "lang": payload["lang"],
        }
        for entry in payload["cases"]:
            cases.append(
                Case(
                    id=entry["id"],
                    input=entry["input"],
                    expected_changes=entry["expected_changes"],
                    expected_unchanged=entry.get("expected_unchanged", []),
                    domain=entry["domain"],
                    metadata={**common_meta, "source": entry.get("source", "")},
                )
            )
    return cases


import re


_DOMAIN_RE = re.compile(r"Treating this as \*\*(\w+)\*\* writing", re.IGNORECASE)
_PREFLIGHT_RE = re.compile(r"(Pre-flight:[^\n]+)", re.IGNORECASE)
_DRAFT_RE = re.compile(
    r"\*\*Draft rewrite:\*\*\s*\n(.*?)(?=\n\*\*(?:Final AI audit|Final rewrite|Changes made):|\Z)",
    re.DOTALL,
)
_FINAL_RE = re.compile(
    r"\*\*Final rewrite:\*\*\s*\n(.*?)(?=\n\*\*(?:Changes made):|\Z)",
    re.DOTALL,
)


def parse_skill_output(text: str) -> dict[str, str]:
    """Extract draft + final + domain + preflight from a Full-mode skill response.

    Returns a dict with keys `domain`, `preflight`, `draft`, `final`. Missing
    sections become empty strings. For Quick-mode output (no Draft/Final
    sentinels), the full text is returned as `final` so downstream code can
    always use `parsed["final"]`.
    """
    domain_match = _DOMAIN_RE.search(text)
    preflight_match = _PREFLIGHT_RE.search(text)
    draft_match = _DRAFT_RE.search(text)
    final_match = _FINAL_RE.search(text)

    result = {
        "domain": domain_match.group(1).lower() if domain_match else "",
        "preflight": preflight_match.group(1) if preflight_match else "",
        "draft": draft_match.group(1).strip() if draft_match else "",
        "final": final_match.group(1).strip() if final_match else "",
    }
    if not result["final"] and not result["draft"]:
        # Quick-mode or non-sentinel output — treat entire text as the final.
        result["final"] = text.strip()
    return result
