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


import subprocess


class SkillRunError(RuntimeError):
    """Raised when the claude CLI subprocess fails or returns non-zero."""


def _build_humanizer_prompt(
    text: str, *, lang: str | None, mode: str, domain: str | None, samples_dir: str | None
) -> str:
    """Compose the user prompt that invokes the humanizer skill on `text`."""
    parts = ["/humanizer"]
    if mode and mode != "full":
        parts.append(mode)
    if domain:
        parts.append(domain)
    if lang and lang != "en":
        parts.append(f"language: {lang}")
    if samples_dir:
        parts.append(f"--samples-dir {samples_dir}")
    header = " ".join(parts)
    return f"{header}\n\n{text}"


def run_skill(
    text: str,
    *,
    lang: str | None = None,
    mode: str = "full",
    domain: str | None = None,
    samples_dir: str | None = None,
    model: str = "sonnet",
    timeout: int = 180,
    max_attempts: int = 3,
) -> dict[str, str]:
    """Invoke the humanizer skill via `claude -p` and return the parsed output.

    Loads whatever humanizer skill is installed in the environment. The caller
    is responsible for verifying that the installed skill is the version under
    test (see `verify_skill_install` below).

    Retries up to `max_attempts` times on SkillRunError to absorb intermittent
    claude CLI hiccups (occasional exit 1 with empty stderr, seen in practice).
    """
    prompt = _build_humanizer_prompt(
        text, lang=lang, mode=mode, domain=domain, samples_dir=samples_dir
    )
    cmd = ["claude", "-p", prompt, "--model", model]

    def _one_attempt() -> dict[str, str]:
        completed = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        if completed.returncode != 0:
            raise SkillRunError(
                f"claude CLI exited {completed.returncode}: {completed.stderr.strip()}"
            )
        return parse_skill_output(completed.stdout)

    return retry_with_backoff(_one_attempt, max_attempts=max_attempts, base_delay=2.0)


import time
from datetime import datetime
from typing import Callable, TypeVar


T = TypeVar("T")


def retry_with_backoff(
    fn: Callable[[], T], *, max_attempts: int = 3, base_delay: float = 1.0
) -> T:
    """Call fn() with exponential backoff. Reraises the last exception on failure."""
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt == max_attempts - 1:
                break
            time.sleep(base_delay * (2 ** attempt))
    assert last_exc is not None
    raise last_exc


def write_report(name: str, data: dict[str, Any]) -> tuple[Path, Path]:
    """Write paired JSON + Markdown reports under evals/reports/.

    Filenames include a timestamp so consecutive runs do not overwrite each
    other. The MD file is a human-readable summary; the JSON is the full
    structured payload for diffing.
    """
    reports_dir = Path.cwd() / "evals" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = reports_dir / f"{name}_{timestamp}.json"
    md_path = reports_dir / f"{name}_{timestamp}.md"

    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    md_path.write_text(_render_report_md(name, data))
    return json_path, md_path


import hashlib


class SkillInstallMismatch(RuntimeError):
    """Raised when the installed humanizer skill differs from the repo version."""


_DEFAULT_INSTALLED_SKILL = Path.home() / ".claude" / "skills" / "humanizer" / "SKILL.md"


def verify_skill_install(
    *,
    repo_skill_path: Path | None = None,
    installed_skill_path: Path | None = None,
) -> None:
    """Confirm the skill `claude -p` will load matches the repo SKILL.md.

    Raises SkillInstallMismatch with a clear message if the installed file is
    missing or has different bytes than the repo's SKILL.md. The eval runners
    call this before running so a stale install does not silently invalidate
    the report.
    """
    repo_skill_path = repo_skill_path or (Path.cwd() / "SKILL.md")
    installed_skill_path = installed_skill_path or _DEFAULT_INSTALLED_SKILL

    if not installed_skill_path.exists():
        raise SkillInstallMismatch(
            f"humanizer skill not installed at {installed_skill_path} — "
            f"symlink or install the repo's SKILL.md before running evals"
        )

    repo_hash = hashlib.sha256(repo_skill_path.read_bytes()).hexdigest()
    installed_hash = hashlib.sha256(installed_skill_path.read_bytes()).hexdigest()
    if repo_hash != installed_hash:
        raise SkillInstallMismatch(
            f"installed SKILL.md bytes differ from repo SKILL.md "
            f"(installed={installed_hash[:8]}, repo={repo_hash[:8]}) — "
            f"the eval would test a stale skill version"
        )


def _render_report_md(name: str, data: dict[str, Any]) -> str:
    """Render a minimal Markdown summary of a report payload."""
    lines = [f"# Eval report: {name}", ""]
    lines.append(f"- type: `{data.get('eval_type', '?')}`")
    lines.append(f"- lang: `{data.get('lang', '?')}`")
    summary = data.get("summary", {})
    if summary:
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        for k, v in summary.items():
            lines.append(f"- **{k}**: {v}")
    per_pattern = data.get("per_pattern", [])
    if per_pattern:
        lines.append("")
        lines.append("## Per-pattern")
        lines.append("")
        lines.append("| pattern | metric |")
        lines.append("|---|---|")
        for entry in per_pattern:
            lines.append(f"| #{entry.get('id', '?')} | {entry.get('rate', '?')} |")
    return "\n".join(lines) + "\n"
