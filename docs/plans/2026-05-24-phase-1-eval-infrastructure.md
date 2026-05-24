# Phase 1 (v3.4.0): Evaluation Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Subagent model strategy:**
> - `cavecrew-builder` (Sonnet) for ≤2-file mechanical edits: corpus JSON, sample text files, README, .gitignore tweaks.
> - `general-purpose` agent (Sonnet) for substantive Python module creation (`_shared.py`, three eval runners) — these are 100-300 lines each and exceed cavecrew-builder's "surgical 1-2 edit" comfort zone.
> - Parent (Opus) orchestrates, runs pytest, runs baselines, reviews diffs between tasks.

**Goal:** Add a three-tier eval harness (pattern detection, false-positive rate on human texts, end-to-end rewrite quality scored by a judge LLM) that runs against the v3.3.0 framework + pack files on the existing EN corpus, producing a baseline report committed to `evals/reports/`.

**Architecture:** A small `_shared.py` library wraps the `claude -p` CLI for skill invocations and exposes corpus loaders + report writers. Three runner scripts (one per eval type) sit on top. The judge LLM in E2E uses the Anthropic SDK directly with tool-use for structured scores. Pattern-eval and false-positive-eval are deterministic-ish (single sampling); E2E runs each case 3× for variance. Reports land in `evals/reports/` as paired JSON + Markdown.

**Tech Stack:** Python 3.10+, `claude` CLI (for skill execution), `anthropic` Python SDK (for judge), `rapidfuzz` (edit distance), `pytest`, existing `pyyaml`.

**Spec:** `docs/specs/2026-05-23-humanizer-eval-de-design.md` §4.5, §4.6, §5.2–5.3, §6 Phase 1.

**Out of scope for this plan:** DE corpus (Phase 2), mining script (Phase 2), personal-samples mode (Phase 2 unless trivially added in Task 13), CI integration (Phase 3), README "What's different" rewrite (Phase 3).

---

## Pre-flight (one-time, before any task)

The eval scripts call `claude -p` which loads the installed `humanizer` skill from `~/.claude/skills/humanizer/` or the plugin cache. To test the **current repo's** SKILL.md + pack files (rather than whatever version is installed), the implementer must ensure the local install points at the working repo before running any eval.

This is **not part of the plan tasks** — it's an environmental prerequisite documented in `evals/README.md` (Task 16) and re-verified by the baseline runner (Task 17). The eval `_shared.py` exposes a `verify_skill_install()` helper that compares the loaded SKILL.md byte hash against the repo SKILL.md and raises if they differ.

---

## File Structure

After Phase 1:

```
humanizer-ext/
├── evals/
│   ├── __init__.py
│   ├── corpus/
│   │   └── en/
│   │       ├── patterns/
│   │       │   ├── pattern_001.json     # 28 EN-specific + 12 universal = 40 files
│   │       │   ├── pattern_002.json
│   │       │   └── ... (40 total)
│   │       ├── human/
│   │       │   ├── public_domain/
│   │       │   │   ├── _LICENSE
│   │       │   │   ├── _SOURCE
│   │       │   │   ├── gutenberg_aristotle_nicomachean_excerpt.md
│   │       │   │   └── ... (5 files total)
│   │       │   ├── synthetic/
│   │       │   │   ├── _LICENSE
│   │       │   │   ├── casual_blog_draft_01.md
│   │       │   │   ├── academic_paragraph_01.md
│   │       │   │   ├── legal_brief_excerpt_01.md
│   │       │   │   ├── technical_docs_01.md
│   │       │   │   └── marketing_copy_01.md
│   │       │   └── contributed/
│   │       │       └── README.md
│   │       └── e2e/
│   │           ├── ai_casual_01.json
│   │           ├── ai_academic_01.json
│   │           ├── ai_legal_01.json
│   │           ├── ai_technical_01.json
│   │           └── ai_marketing_01.json
│   ├── scripts/
│   │   ├── __init__.py
│   │   ├── _shared.py
│   │   ├── run_pattern_eval.py
│   │   ├── run_false_positive_eval.py
│   │   ├── run_e2e_eval.py
│   │   ├── judge_prompt.md
│   │   └── seed_pattern_corpus.py       # one-off generator, Task 9
│   ├── reports/
│   │   ├── .gitkeep
│   │   └── (gitignored except summary_latest_en.md after Task 17)
│   └── README.md
├── tests/
│   ├── test_skill_structure.py          # (existing)
│   └── test_evals_shared.py             # new in Task 3
├── pyproject.toml                        # add eval deps
└── .gitignore                            # add evals/reports/*_personal_*
```

---

## Task 1: evals/ scaffolding (no logic)

**Files:**
- Create: `evals/__init__.py` (empty)
- Create: `evals/scripts/__init__.py` (empty)

- [ ] **Step 1.1: Create empty `evals/__init__.py`**

(zero bytes)

- [ ] **Step 1.2: Create empty `evals/scripts/__init__.py`**

(zero bytes)

- [ ] **Step 1.3: Commit**

```bash
git add evals/__init__.py evals/scripts/__init__.py
git commit -m "chore: add evals/ package scaffolding"
```

---

## Task 2: Add eval dependencies to pyproject.toml

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 2.1: Edit `pyproject.toml`**

Replace the existing `[project.optional-dependencies]` block:

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0", "pyyaml>=6.0"]
```

with:

```toml
[project.optional-dependencies]
dev = ["pytest>=8.0", "pyyaml>=6.0"]
evals = ["anthropic>=0.40", "rapidfuzz>=3.5"]
all = ["pytest>=8.0", "pyyaml>=6.0", "anthropic>=0.40", "rapidfuzz>=3.5"]
```

- [ ] **Step 2.2: Install eval deps locally**

```bash
python3 -m pip install --user --quiet 'anthropic>=0.40' 'rapidfuzz>=3.5'
python3 -c "import anthropic, rapidfuzz; print(anthropic.__version__, rapidfuzz.__version__)"
```

Expected: two version strings, no import errors.

- [ ] **Step 2.3: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add eval dependencies (anthropic, rapidfuzz)"
```

---

## Task 3: Case dataclass + corpus loader (TDD)

**Files:**
- Create: `tests/test_evals_shared.py`
- Create: `evals/scripts/_shared.py`

- [ ] **Step 3.1: Write the failing test**

Create `tests/test_evals_shared.py` with:

```python
"""Tests for evals/scripts/_shared.py — repo-side eval utilities."""
import json
from pathlib import Path

import pytest

from evals.scripts._shared import Case, load_pattern_corpus

REPO_ROOT = Path(__file__).parent.parent


def test_case_dataclass_required_fields():
    case = Case(
        id="pattern_007_en_001",
        input="Additionally, the report underscores the pivotal moment.",
        expected_changes=["Additionally", "underscores", "pivotal moment"],
        expected_unchanged=[],
        domain="casual",
        metadata={"pattern_id": 7, "source": "manual_curation"},
    )
    assert case.id == "pattern_007_en_001"
    assert case.metadata["pattern_id"] == 7


def test_load_pattern_corpus_returns_cases(tmp_path):
    corpus_dir = tmp_path / "patterns"
    corpus_dir.mkdir()
    (corpus_dir / "pattern_007.json").write_text(json.dumps({
        "pattern_id": 7,
        "pattern_name": "AI vocabulary",
        "lang": "en",
        "cases": [
            {
                "id": "pattern_007_en_001",
                "input": "Additionally, ...",
                "expected_changes": ["Additionally"],
                "expected_unchanged": [],
                "domain": "casual",
                "source": "manual_curation",
            }
        ],
    }))
    cases = load_pattern_corpus(corpus_dir)
    assert len(cases) == 1
    assert cases[0].id == "pattern_007_en_001"
    assert cases[0].metadata["pattern_id"] == 7
    assert cases[0].metadata["pattern_name"] == "AI vocabulary"


def test_load_pattern_corpus_empty_dir(tmp_path):
    corpus_dir = tmp_path / "patterns"
    corpus_dir.mkdir()
    assert load_pattern_corpus(corpus_dir) == []
```

- [ ] **Step 3.2: Run test to verify it FAILS**

```bash
python3 -m pytest tests/test_evals_shared.py -v
```
Expected: ImportError or ModuleNotFoundError for `evals.scripts._shared`.

- [ ] **Step 3.3: Create `evals/scripts/_shared.py` with Case + loader**

```python
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
```

- [ ] **Step 3.4: Run tests to verify they PASS**

```bash
python3 -m pytest tests/test_evals_shared.py -v
```
Expected: 3 passed.

- [ ] **Step 3.5: Commit**

```bash
git add tests/test_evals_shared.py evals/scripts/_shared.py
git commit -m "feat(evals): Case dataclass + load_pattern_corpus"
```

---

## Task 4: parse_skill_output (regex-based extractor)

**Files:**
- Modify: `tests/test_evals_shared.py`
- Modify: `evals/scripts/_shared.py`

- [ ] **Step 4.1: Append failing tests**

Append to `tests/test_evals_shared.py`:

```python


from evals.scripts._shared import parse_skill_output


SAMPLE_FULL_OUTPUT = """Treating this as **casual** writing.

Pre-flight: 4 Tier-1 tells per 100 words → AI-heavy. Full pass.

**Draft rewrite:**
> AI coding assistants speed up some tasks.
> They are good at boilerplate.

**Final AI audit findings:**
- One em dash retained ("X — Y")
- Rule of three softened

**Final rewrite:**
> AI coding assistants speed up boilerplate.
> They struggle with architecture.
"""


def test_parse_skill_output_extracts_draft_and_final():
    parsed = parse_skill_output(SAMPLE_FULL_OUTPUT)
    assert "AI coding assistants speed up some tasks" in parsed["draft"]
    assert "AI coding assistants speed up boilerplate" in parsed["final"]
    assert parsed["domain"] == "casual"
    assert "4 Tier-1 tells" in parsed["preflight"]


def test_parse_skill_output_handles_missing_sections():
    minimal = "**Final rewrite:**\n> Just a final.\n"
    parsed = parse_skill_output(minimal)
    assert parsed["final"].strip() == "> Just a final."
    assert parsed["draft"] == ""
    assert parsed["domain"] == ""
    assert parsed["preflight"] == ""


def test_parse_skill_output_quick_mode_has_only_final():
    """Quick mode outputs cleaned text only — no Draft/Final headers."""
    quick = "Here is the cleaned text. It removed filler.\n"
    parsed = parse_skill_output(quick)
    assert parsed["final"].strip() == quick.strip()
    assert parsed["draft"] == ""
```

- [ ] **Step 4.2: Run, verify FAIL**

```bash
python3 -m pytest tests/test_evals_shared.py::test_parse_skill_output_extracts_draft_and_final -v
```
Expected: ImportError.

- [ ] **Step 4.3: Append `parse_skill_output` to `evals/scripts/_shared.py`**

```python


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
```

- [ ] **Step 4.4: Run, verify PASS**

```bash
python3 -m pytest tests/test_evals_shared.py -v
```
Expected: 6 passed.

- [ ] **Step 4.5: Commit**

```bash
git add tests/test_evals_shared.py evals/scripts/_shared.py
git commit -m "feat(evals): parse_skill_output for Draft/Final extraction"
```

---

## Task 5: run_skill wrapper (subprocess + claude CLI)

**Files:**
- Modify: `tests/test_evals_shared.py`
- Modify: `evals/scripts/_shared.py`

- [ ] **Step 5.1: Append the failing test (subprocess mocked)**

Append to `tests/test_evals_shared.py`:

```python


from unittest.mock import patch, MagicMock


@patch("subprocess.run")
def test_run_skill_calls_claude_with_prompt(mock_run):
    from evals.scripts._shared import run_skill

    mock_run.return_value = MagicMock(
        stdout=(
            "Treating this as **casual** writing.\n\n"
            "**Final rewrite:**\n> Cleaned output.\n"
        ),
        stderr="",
        returncode=0,
    )

    result = run_skill("Some input text.", lang="en", mode="full", model="sonnet")

    assert mock_run.called
    cmd = mock_run.call_args[0][0]
    assert "claude" in cmd[0]
    assert "-p" in cmd
    full_prompt = cmd[cmd.index("-p") + 1]
    assert "Some input text." in full_prompt
    assert "/humanizer" in full_prompt or "humanize" in full_prompt.lower()

    assert result["final"] == "> Cleaned output."
    assert result["domain"] == "casual"


@patch("subprocess.run")
def test_run_skill_passes_model_flag(mock_run):
    from evals.scripts._shared import run_skill

    mock_run.return_value = MagicMock(stdout="**Final rewrite:**\n> X.\n", stderr="", returncode=0)
    run_skill("hi", model="claude-opus-4-7")
    cmd = mock_run.call_args[0][0]
    assert "--model" in cmd
    assert cmd[cmd.index("--model") + 1] == "claude-opus-4-7"


@patch("subprocess.run")
def test_run_skill_returncode_nonzero_raises(mock_run):
    from evals.scripts._shared import run_skill, SkillRunError

    mock_run.return_value = MagicMock(stdout="", stderr="boom", returncode=1)
    with pytest.raises(SkillRunError, match="claude CLI exited 1"):
        run_skill("hi")
```

- [ ] **Step 5.2: Run, verify FAIL**

```bash
python3 -m pytest tests/test_evals_shared.py -k run_skill -v
```
Expected: ImportError for run_skill / SkillRunError.

- [ ] **Step 5.3: Append `run_skill` + `SkillRunError` to `_shared.py`**

```python


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
) -> dict[str, str]:
    """Invoke the humanizer skill via `claude -p` and return the parsed output.

    Loads whatever humanizer skill is installed in the environment. The caller
    is responsible for verifying that the installed skill is the version under
    test (see `verify_skill_install` below).
    """
    prompt = _build_humanizer_prompt(
        text, lang=lang, mode=mode, domain=domain, samples_dir=samples_dir
    )
    cmd = ["claude", "-p", prompt, "--model", model]
    completed = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout
    )
    if completed.returncode != 0:
        raise SkillRunError(
            f"claude CLI exited {completed.returncode}: {completed.stderr.strip()}"
        )
    return parse_skill_output(completed.stdout)
```

- [ ] **Step 5.4: Run, verify PASS**

```bash
python3 -m pytest tests/test_evals_shared.py -k run_skill -v
```
Expected: 3 passed (no real claude CLI invocation — all mocked).

- [ ] **Step 5.5: Commit**

```bash
git add tests/test_evals_shared.py evals/scripts/_shared.py
git commit -m "feat(evals): run_skill claude-CLI wrapper with SkillRunError"
```

---

## Task 6: retry_with_backoff + write_report

**Files:**
- Modify: `tests/test_evals_shared.py`
- Modify: `evals/scripts/_shared.py`

- [ ] **Step 6.1: Append failing tests**

Append to `tests/test_evals_shared.py`:

```python


from unittest.mock import call


def test_retry_with_backoff_succeeds_on_third_try():
    from evals.scripts._shared import retry_with_backoff

    attempts = {"n": 0}
    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise RuntimeError("transient")
        return "ok"

    result = retry_with_backoff(flaky, max_attempts=3, base_delay=0.01)
    assert result == "ok"
    assert attempts["n"] == 3


def test_retry_with_backoff_raises_after_max():
    from evals.scripts._shared import retry_with_backoff

    def always_fails():
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError, match="nope"):
        retry_with_backoff(always_fails, max_attempts=2, base_delay=0.01)


def test_write_report_creates_json_and_markdown(tmp_path, monkeypatch):
    from evals.scripts._shared import write_report

    monkeypatch.chdir(tmp_path)
    (tmp_path / "evals" / "reports").mkdir(parents=True)

    data = {
        "eval_type": "pattern",
        "lang": "en",
        "summary": {"detection_rate": 0.92},
        "per_pattern": [{"id": 7, "rate": 0.95}],
    }
    json_path, md_path = write_report("pattern_en_demo", data)

    assert json_path.exists()
    assert md_path.exists()
    assert json.loads(json_path.read_text())["summary"]["detection_rate"] == 0.92
    assert "pattern" in md_path.read_text().lower()
    assert "0.92" in md_path.read_text()
```

- [ ] **Step 6.2: Run, verify FAIL**

```bash
python3 -m pytest tests/test_evals_shared.py -k "retry or write_report" -v
```
Expected: ImportError.

- [ ] **Step 6.3: Append `retry_with_backoff` + `write_report` to `_shared.py`**

```python


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
```

- [ ] **Step 6.4: Run, verify PASS**

```bash
python3 -m pytest tests/test_evals_shared.py -v
```
Expected: 11 passed.

- [ ] **Step 6.5: Commit**

```bash
git add tests/test_evals_shared.py evals/scripts/_shared.py
git commit -m "feat(evals): retry_with_backoff + write_report (json+md)"
```

---

## Task 7: verify_skill_install helper

**Files:**
- Modify: `tests/test_evals_shared.py`
- Modify: `evals/scripts/_shared.py`

- [ ] **Step 7.1: Append failing test**

Append to `tests/test_evals_shared.py`:

```python


def test_verify_skill_install_matches(tmp_path, monkeypatch):
    from evals.scripts._shared import verify_skill_install, SkillInstallMismatch

    repo_skill = tmp_path / "SKILL.md"
    installed_skill = tmp_path / "installed_SKILL.md"
    repo_skill.write_text("same content\n")
    installed_skill.write_text("same content\n")

    verify_skill_install(repo_skill_path=repo_skill, installed_skill_path=installed_skill)


def test_verify_skill_install_mismatch_raises(tmp_path):
    from evals.scripts._shared import verify_skill_install, SkillInstallMismatch

    repo_skill = tmp_path / "SKILL.md"
    installed_skill = tmp_path / "installed_SKILL.md"
    repo_skill.write_text("repo version\n")
    installed_skill.write_text("old installed version\n")

    with pytest.raises(SkillInstallMismatch, match="bytes differ"):
        verify_skill_install(repo_skill_path=repo_skill, installed_skill_path=installed_skill)


def test_verify_skill_install_missing_installed(tmp_path):
    from evals.scripts._shared import verify_skill_install, SkillInstallMismatch

    repo_skill = tmp_path / "SKILL.md"
    repo_skill.write_text("repo version\n")
    installed_skill = tmp_path / "nope.md"

    with pytest.raises(SkillInstallMismatch, match="not installed"):
        verify_skill_install(repo_skill_path=repo_skill, installed_skill_path=installed_skill)
```

- [ ] **Step 7.2: Run, verify FAIL**

```bash
python3 -m pytest tests/test_evals_shared.py -k verify_skill_install -v
```
Expected: ImportError.

- [ ] **Step 7.3: Append `verify_skill_install` + `SkillInstallMismatch` to `_shared.py`**

```python


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
```

- [ ] **Step 7.4: Run, verify PASS**

```bash
python3 -m pytest tests/test_evals_shared.py -v
```
Expected: 14 passed.

- [ ] **Step 7.5: Commit**

```bash
git add tests/test_evals_shared.py evals/scripts/_shared.py
git commit -m "feat(evals): verify_skill_install guards against stale installs"
```

---

## Task 8: judge_prompt.md (rubric for E2E eval)

**Files:**
- Create: `evals/scripts/judge_prompt.md`

- [ ] **Step 8.1: Create the rubric file**

```markdown
# Humanizer E2E Judge Rubric

You are a senior editor evaluating whether an AI-generated text was successfully rewritten to read as human-authored prose. You receive:

1. The original AI input
2. The skill's final rewrite
3. The detected domain (casual / academic / legal / technical / marketing)

Score the rewrite on three independent dimensions (1–10 each). Return your scores via the `report_scores` tool.

## Dimension 1 — Human-ness (1–10)

How likely is a careful reader to identify this rewrite as human-written rather than AI-generated?

- **10:** Indistinguishable from a competent human writer in this domain.
- **8–9:** Reads human with one or two faint AI tells.
- **5–7:** Mixed — clearly improved over the input but still has detectable AI patterns.
- **3–4:** Most AI tells removed, but rhythm or word choice still feels generated.
- **1–2:** Barely different from the input.

Score against the domain register: a clinical legal brief is not less human than a personal blog post — both are scored against their own conventions.

## Dimension 2 — Meaning preservation (1–10)

How much of the original input's substantive content is retained?

- **10:** Every claim, fact, and structural beat from the input is represented in the rewrite (or correctly dropped per the skill's length-audit rules).
- **8–9:** Minor omissions of secondary points.
- **5–7:** A meaningful claim or two is missing or distorted.
- **3–4:** Significant content loss — the rewrite no longer makes the input's argument.
- **1–2:** Different document entirely.

Removing AI-isms (chatbot artifacts, sycophancy, throat-clearing, padding) is not content loss — that is the skill's job. Score only on substantive content.

## Dimension 3 — Length appropriateness (1–10)

Did the rewrite hit a length suited to the input and domain?

Compute `length_ratio = len(rewrite_words) / len(input_words)`. The skill's length audit aims for 0.70–0.90 (cut 20–30% padding) for casual / marketing, looser for academic / technical / legal.

- **10:** Ratio within the domain-appropriate band.
- **8–9:** Within ±10% of band.
- **5–7:** Notably outside band but defensible.
- **3–4:** Way too long or way too short.
- **1–2:** Egregious — twice as long, or one sentence.

## Reasoning

Before scoring, give one paragraph (≤80 words) reasoning that names specific things you observed (good and bad). Then call `report_scores` once with the three scores and a one-sentence rationale per dimension.

Do not flatter. Do not soften. Score what you see.
```

- [ ] **Step 8.2: Commit**

```bash
git add evals/scripts/judge_prompt.md
git commit -m "feat(evals): judge_prompt.md rubric for E2E eval scoring"
```

---

## Task 9: Seed pattern corpus from SKILL.md examples

**Files:**
- Create: `evals/scripts/seed_pattern_corpus.py` (one-off generator)
- Create: `evals/corpus/en/patterns/pattern_*.json` (40 files, generated)

This task uses a small generator script because hand-writing 40 JSON files is mechanical, error-prone work that the corpus content already documents. The generator parses the before/after blocks already in `patterns/_universal.md` + `patterns/en.md` into seed Cases.

- [ ] **Step 9.1: Create `evals/scripts/seed_pattern_corpus.py`**

```python
"""One-off corpus seeder: convert before/after examples in the pattern packs
into evals/corpus/en/patterns/pattern_NNN.json files.

Run once: `python3 evals/scripts/seed_pattern_corpus.py`.
Commit the resulting JSON files. Re-running overwrites them.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PATTERN_PACK_FILES = [
    REPO_ROOT / "patterns" / "_universal.md",
    REPO_ROOT / "patterns" / "en.md",
]
CORPUS_DIR = REPO_ROOT / "evals" / "corpus" / "en" / "patterns"

PATTERN_HEADING_RE = re.compile(r"^###\s+(\d+)\.\s+(.+)$", re.MULTILINE)
BEFORE_BLOCK_RE = re.compile(
    r"\*\*Before(?:\s*\([^)]*\))?:\*\*\s*\n>\s*(.+?)(?=\n\n|\n\*\*|\Z)",
    re.DOTALL,
)


def extract_pattern_sections(text: str) -> list[tuple[int, str, str]]:
    """Return [(pattern_id, pattern_name, body_text), ...]."""
    matches = list(PATTERN_HEADING_RE.finditer(text))
    sections = []
    for i, m in enumerate(matches):
        pid = int(m.group(1))
        name = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((pid, name, text[body_start:body_end]))
    return sections


def extract_before_inputs(body: str) -> list[str]:
    """Return the text of every `**Before:**` quoted block in a pattern body."""
    return [match.group(1).strip() for match in BEFORE_BLOCK_RE.finditer(body)]


def trigger_terms_from_body(body: str) -> list[str]:
    """Extract `**Words to watch:** a, b, c` or `**Phrases to watch:** ...` lists.

    Returns a flat list of comma-separated terms. Used as the seed
    `expected_changes` set for each Case. Reviewers can refine after seeding.
    """
    terms: list[str] = []
    for marker in ("Words to watch", "Phrases to watch", "Signs to watch", "Tokens to watch"):
        m = re.search(rf"\*\*{marker}:\*\*\s*([^\n]+)", body)
        if not m:
            continue
        raw = m.group(1)
        terms.extend(t.strip(" .—") for t in re.split(r"[,;|]| \| ", raw) if t.strip())
    return [t for t in terms if t and not t.startswith("`")]


def main() -> None:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    all_text = "\n\n".join(p.read_text(encoding="utf-8") for p in PATTERN_PACK_FILES)
    sections = extract_pattern_sections(all_text)
    written = 0
    for pid, name, body in sections:
        inputs = extract_before_inputs(body)
        if not inputs:
            continue
        triggers = trigger_terms_from_body(body)
        cases = [
            {
                "id": f"pattern_{pid:03d}_en_{idx + 1:03d}",
                "input": input_text,
                "expected_changes": triggers[:8],
                "expected_unchanged": [],
                "domain": "casual",
                "source": "seeded_from_pattern_pack",
            }
            for idx, input_text in enumerate(inputs)
        ]
        payload = {
            "pattern_id": pid,
            "pattern_name": name,
            "lang": "en",
            "cases": cases,
        }
        out_path = CORPUS_DIR / f"pattern_{pid:03d}.json"
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        written += 1
    print(f"Wrote {written} pattern corpus files to {CORPUS_DIR}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 9.2: Run the seeder**

```bash
cd "/Users/christianhuhn/Library/Mobile Documents/iCloud~md~obsidian/Documents/duathron.github.io/__obsidian_vault/AI/SKILLS/humanizer-ext"
python3 evals/scripts/seed_pattern_corpus.py
```

Expected output: `Wrote 40 pattern corpus files to .../evals/corpus/en/patterns`

- [ ] **Step 9.3: Sanity-check generated files**

```bash
ls evals/corpus/en/patterns/ | wc -l
# Expected: 40

python3 -c "
import json, glob
from pathlib import Path
files = sorted(Path('evals/corpus/en/patterns').glob('pattern_*.json'))
print(f'{len(files)} files')
for f in files[:3]:
    data = json.loads(f.read_text())
    print(f'  {f.name}: pattern_id={data[\"pattern_id\"]}, cases={len(data[\"cases\"])}')
"
```

If any file has zero cases, that pattern's body in `patterns/*.md` does not have a `**Before:**` block — note it as a corpus gap to fill manually later; do not block on it.

- [ ] **Step 9.4: Commit seeder + generated corpus**

```bash
git add evals/scripts/seed_pattern_corpus.py evals/corpus/en/patterns/
git commit -m "feat(evals): seed pattern corpus from SKILL.md before/after examples"
```

---

## Task 10: run_pattern_eval.py runner + integration test

**Files:**
- Create: `evals/scripts/run_pattern_eval.py`
- Modify: `tests/test_evals_shared.py`

- [ ] **Step 10.1: Append integration test (skill mocked)**

Append to `tests/test_evals_shared.py`:

```python


@patch("evals.scripts._shared.run_skill")
@patch("evals.scripts._shared.verify_skill_install")
def test_pattern_eval_scores_detection(mock_verify, mock_run_skill, tmp_path, monkeypatch):
    from evals.scripts.run_pattern_eval import score_case
    from evals.scripts._shared import Case

    case = Case(
        id="pattern_007_en_001",
        input="Additionally, the report underscores the pivotal moment.",
        expected_changes=["Additionally", "underscores", "pivotal moment"],
        expected_unchanged=[],
        domain="casual",
        metadata={"pattern_id": 7, "pattern_name": "AI vocabulary", "lang": "en"},
    )
    # Simulate a rewrite that removed all three expected_changes
    mock_run_skill.return_value = {
        "domain": "casual",
        "preflight": "",
        "draft": "The report flags an important shift.",
        "final": "The report flags an important shift.",
    }

    score = score_case(case, model="sonnet")
    assert score["detected"] is True
    assert score["removed_terms"] == ["Additionally", "underscores", "pivotal moment"]
    assert score["retained_terms"] == []


@patch("evals.scripts._shared.run_skill")
def test_pattern_eval_partial_removal(mock_run_skill):
    from evals.scripts.run_pattern_eval import score_case
    from evals.scripts._shared import Case

    case = Case(
        id="pattern_007_en_002",
        input="Additionally, this is a pivotal moment.",
        expected_changes=["Additionally", "pivotal moment"],
        expected_unchanged=[],
        domain="casual",
        metadata={"pattern_id": 7, "pattern_name": "AI vocabulary", "lang": "en"},
    )
    mock_run_skill.return_value = {
        "domain": "casual",
        "preflight": "",
        "draft": "This is a pivotal moment.",
        "final": "This is a pivotal moment.",
    }
    score = score_case(case, model="sonnet")
    assert score["detected"] is False  # only 1 of 2 removed
    assert score["removed_terms"] == ["Additionally"]
    assert score["retained_terms"] == ["pivotal moment"]
```

- [ ] **Step 10.2: Run, verify FAIL**

```bash
python3 -m pytest tests/test_evals_shared.py -k pattern_eval -v
```
Expected: ImportError.

- [ ] **Step 10.3: Create `evals/scripts/run_pattern_eval.py`**

```python
"""Pattern-detection eval runner.

Per pattern in the corpus, run each case through the skill and check whether
the rewrite removes every term in `expected_changes`. Detection rate per
pattern is `len(detected_cases) / len(total_cases)`. The runner fails the
build (exit 1) if any pattern's rate falls below the threshold.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from evals.scripts._shared import (
    Case,
    load_pattern_corpus,
    run_skill,
    verify_skill_install,
    write_report,
)


DEFAULT_THRESHOLD = 0.85
REPO_ROOT = Path(__file__).resolve().parents[2]


def score_case(case: Case, *, model: str = "sonnet") -> dict:
    """Run one case through the skill and report which expected_changes survived."""
    result = run_skill(
        case.input,
        lang=case.metadata.get("lang", "en"),
        mode="full",
        domain=case.domain,
        model=model,
    )
    rewritten = (result.get("final") or result.get("draft") or "").lower()

    removed: list[str] = []
    retained: list[str] = []
    for term in case.expected_changes:
        if term.lower() in rewritten:
            retained.append(term)
        else:
            removed.append(term)

    detected = len(retained) == 0 and len(removed) > 0
    return {
        "case_id": case.id,
        "pattern_id": case.metadata.get("pattern_id"),
        "detected": detected,
        "removed_terms": removed,
        "retained_terms": retained,
        "rewrite_preview": rewritten[:200],
    }


def run(
    lang: str = "en",
    pattern: int | None = None,
    model: str = "sonnet",
    threshold: float = DEFAULT_THRESHOLD,
) -> dict:
    verify_skill_install()
    corpus_dir = REPO_ROOT / "evals" / "corpus" / lang / "patterns"
    cases = load_pattern_corpus(corpus_dir)
    if pattern is not None:
        cases = [c for c in cases if c.metadata.get("pattern_id") == pattern]

    by_pattern: dict[int, list[dict]] = defaultdict(list)
    for case in cases:
        score = score_case(case, model=model)
        by_pattern[score["pattern_id"]].append(score)

    per_pattern_summary = []
    for pid in sorted(by_pattern.keys()):
        scores = by_pattern[pid]
        detected = sum(1 for s in scores if s["detected"])
        total = len(scores)
        rate = detected / total if total else 0.0
        per_pattern_summary.append(
            {
                "id": pid,
                "rate": round(rate, 3),
                "detected": detected,
                "total": total,
                "below_threshold": rate < threshold,
                "misses": [s["case_id"] for s in scores if not s["detected"]],
            }
        )

    overall = (
        sum(s["detected"] for ps in by_pattern.values() for s in ps)
        / sum(len(ps) for ps in by_pattern.values())
    ) if by_pattern else 0.0

    return {
        "eval_type": "pattern",
        "lang": lang,
        "model": model,
        "threshold": threshold,
        "summary": {
            "overall_detection_rate": round(overall, 3),
            "patterns_below_threshold": sum(
                1 for p in per_pattern_summary if p["below_threshold"]
            ),
            "total_patterns": len(per_pattern_summary),
            "total_cases": sum(p["total"] for p in per_pattern_summary),
        },
        "per_pattern": per_pattern_summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Pattern-detection eval runner.")
    parser.add_argument("--lang", default="en")
    parser.add_argument("--pattern", type=int, default=None, help="Filter to one pattern ID")
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()

    report = run(
        lang=args.lang, pattern=args.pattern, model=args.model, threshold=args.threshold
    )
    json_path, md_path = write_report(f"pattern_{args.lang}", report)
    print(f"Wrote {json_path.name} and {md_path.name}")
    print(
        f"Overall detection rate: {report['summary']['overall_detection_rate']} "
        f"({report['summary']['patterns_below_threshold']}/{report['summary']['total_patterns']} below {args.threshold})"
    )
    sys.exit(1 if report["summary"]["patterns_below_threshold"] > 0 else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 10.4: Run, verify PASS**

```bash
python3 -m pytest tests/test_evals_shared.py -v
```
Expected: 16 passed (no real CLI invocation in tests).

- [ ] **Step 10.5: Commit**

```bash
git add evals/scripts/run_pattern_eval.py tests/test_evals_shared.py
git commit -m "feat(evals): run_pattern_eval.py — per-pattern detection rate"
```

---

## Task 11: Synthetic human samples (5 files, one per domain)

**Files:**
- Create: `evals/corpus/en/human/synthetic/_LICENSE`
- Create: 5 sample files under `evals/corpus/en/human/synthetic/`

Single task batches these because each file is short (~150 words) and the cavecrew-builder limit applies per-file-modified, not per-file-created. To stay within the limit, this task creates the `_LICENSE` and ONE sample file; Tasks 11b–11e create one sample each.

- [ ] **Step 11.1: Create `evals/corpus/en/human/synthetic/_LICENSE`**

```
All files in this directory are original prose written for the humanizer-ext
eval corpus by the maintainer. They are released under MIT (same as the
parent project).

Each file's frontmatter declares its domain. These are intentionally human-
written examples — the false-positive eval verifies that the skill leaves
them substantially unchanged.

If you contribute additional synthetic samples via PR, include a
contributor.txt file alongside agreeing to MIT licensing.
```

- [ ] **Step 11.2: Create `evals/corpus/en/human/synthetic/casual_blog_draft_01.md`**

```markdown
---
domain: casual
lang: en
notes: First-person blog draft. Varied sentence rhythm; one parenthetical; specific named detail.
---

I spent the morning trying to convince my router that yes, the printer really does exist. It's been on the same network for four years. The router knows. The printer knows. Somehow the laptop has decided otherwise.

What I keep coming back to is how much modern troubleshooting is just restarting things in different orders. Restart the router. Restart the printer. Restart the laptop. Restart all three in sequence, ascending alphabetically, while holding your tongue at the correct angle.

(My partner says I sound like someone summoning a minor deity. They are not wrong.)

The thing that fixed it, eventually, was unplugging the printer for ninety seconds. Not eighty. Not a hundred. Some weirdly specific duration that I can only assume corresponds to a capacitor draining somewhere inside the machine. I don't know. I'm not an electrical engineer. I just want to print a boarding pass.
```

- [ ] **Step 11.3: Commit**

```bash
git add evals/corpus/en/human/synthetic/_LICENSE evals/corpus/en/human/synthetic/casual_blog_draft_01.md
git commit -m "feat(evals): seed casual synthetic human sample"
```

---

## Task 12: Synthetic samples — 4 more domains

**Files:**
- Create: `evals/corpus/en/human/synthetic/academic_paragraph_01.md`
- Create: `evals/corpus/en/human/synthetic/legal_brief_excerpt_01.md`

(Each pair of two files is one cavecrew-builder task. After this finishes, Task 12b creates the remaining two — technical + marketing.)

- [ ] **Step 12.1: Create `academic_paragraph_01.md`**

```markdown
---
domain: academic
lang: en
notes: Methods-section excerpt. Passive voice and hedging are domain-appropriate.
---

Participants (N = 84, ages 19–32) were recruited via the departmental subject pool and assigned to one of three conditions. The assignment procedure used a stratified random scheme that balanced for self-reported handedness, on the basis that prior work (Smith & Yamamoto, 2018) has suggested an effect of handedness on task latency in this paradigm. Power analysis indicated that this sample size would detect an effect of d = 0.4 with 0.8 power at α = 0.05; we acknowledge that smaller effects would require further recruitment, and we report below the bounds within which our conclusions hold.

Stimuli were presented on a calibrated 27-inch monitor at a viewing distance of 60 cm, with eye position monitored using an SR Research EyeLink 1000 sampling at 500 Hz. Trials in which fixation deviated more than 1.5° from the central fixation cross at stimulus onset were excluded from analysis (4.2% of trials).
```

- [ ] **Step 12.2: Create `legal_brief_excerpt_01.md`**

```markdown
---
domain: legal
lang: en
notes: Brief excerpt. Passive voice and formal connectors are conventional.
---

The Plaintiff respectfully submits that the District Court erred in granting summary judgment, as material questions of fact remain unresolved with respect to the Defendant's knowledge of the alleged defect at the time of sale. Notwithstanding the Defendant's contention that internal communications produced in discovery were privileged, several such communications were disclosed without privilege assertion and form the evidentiary basis for the present appeal.

Specifically, in an email dated March 14, 2024 (Exhibit 7), the Defendant's Director of Engineering states that "the issue with the secondary latch has been documented in three prior service bulletins" and proposes that "we should consider a recall before this turns into something worse." Such language is plainly inconsistent with the Defendant's later sworn declaration that no internal awareness of the latch issue existed prior to July 2024. The question of which account is credible is, on its face, one for the trier of fact.
```

- [ ] **Step 12.3: Commit**

```bash
git add evals/corpus/en/human/synthetic/academic_paragraph_01.md evals/corpus/en/human/synthetic/legal_brief_excerpt_01.md
git commit -m "feat(evals): seed academic + legal synthetic human samples"
```

---

## Task 13: run_false_positive_eval.py + technical + marketing samples

**Files:**
- Create: `evals/corpus/en/human/synthetic/technical_docs_01.md`
- Create: `evals/scripts/run_false_positive_eval.py`

This batches the technical sample with the runner so the false-positive eval has at least one technical-domain target to score. Marketing sample is added in Task 13b.

- [ ] **Step 13.1: Create `technical_docs_01.md`**

```markdown
---
domain: technical
lang: en
notes: Inline-header lists are conventional in technical docs; preserved.
---

## Configuring the retry policy

The `RetryPolicy` struct controls how the client recovers from transient failures.

**Constructor:** `RetryPolicy::new(max_attempts: u32, base_delay: Duration)`

- `max_attempts`: total number of attempts, including the initial call. Setting this to 1 disables retry.
- `base_delay`: delay before the second attempt. Subsequent delays double until `max_delay` is reached.

**Default:** Three attempts, 100 ms base delay, 5 s cap.

You typically pass an instance to `Client::with_retry_policy()` before any request methods are called. The policy is immutable after that — to change retry behavior at runtime, construct a new client.

```rust
let policy = RetryPolicy::new(5, Duration::from_millis(200));
let client = Client::new(api_key).with_retry_policy(policy);
```

If `max_attempts` is 0, `RetryPolicy::new` panics. Use `max_attempts = 1` to disable retry while keeping a valid policy.
```

- [ ] **Step 13.2: Create `evals/scripts/run_false_positive_eval.py`**

```python
"""False-positive rate eval runner.

For each known-human text in the corpus, run the skill and measure:
  - `edit_ratio`: Levenshtein distance / len(input). Should stay low.
  - `density_preflight_quick_drop`: did the skill correctly detect this as
    human-written and downgrade to Quick mode?

A high edit ratio on human text means the skill is over-editing legitimate
prose — that is the failure mode the v3.2.0 Detection Guidance + Tier-1
density preflight were designed to prevent. This runner is how we measure
whether that design works.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rapidfuzz.distance import Levenshtein

from evals.scripts._shared import (
    run_skill,
    verify_skill_install,
    write_report,
)


DEFAULT_THRESHOLD = 0.10  # edit ratio above this = over-editing
REPO_ROOT = Path(__file__).resolve().parents[2]


def score_human_text(text: str, *, model: str = "sonnet", domain: str = "casual") -> dict:
    result = run_skill(text, lang="en", mode="full", domain=domain, model=model)
    rewritten = result.get("final") or result.get("draft") or ""
    edit_distance = Levenshtein.distance(text, rewritten)
    edit_ratio = edit_distance / max(1, len(text))
    preflight = (result.get("preflight") or "").lower()
    quick_drop = "quick" in preflight and ("0 tier-1" in preflight or "0/100" in preflight or "human-authored" in preflight)
    return {
        "edit_distance": edit_distance,
        "edit_ratio": round(edit_ratio, 4),
        "preflight_message": result.get("preflight", ""),
        "density_preflight_quick_drop": quick_drop,
        "rewrite_length_chars": len(rewritten),
    }


def _read_sample(path: Path) -> tuple[str, str]:
    """Return (domain, body_text) for a sample file with optional YAML frontmatter."""
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---\n"):
        end = raw.find("\n---\n", 4)
        if end >= 0:
            frontmatter = raw[4:end]
            body = raw[end + 5:].strip()
            domain_match = next(
                (line.split(":", 1)[1].strip() for line in frontmatter.splitlines()
                 if line.startswith("domain:")),
                "casual",
            )
            return domain_match, body
    return "casual", raw.strip()


def run(
    lang: str = "en",
    corpus: str = "synthetic",
    model: str = "sonnet",
    threshold: float = DEFAULT_THRESHOLD,
) -> dict:
    verify_skill_install()
    corpus_dir = REPO_ROOT / "evals" / "corpus" / lang / "human" / corpus
    files = sorted(
        p for p in corpus_dir.iterdir()
        if p.is_file() and p.suffix in {".md", ".txt"} and not p.name.startswith("_")
    )

    per_file = []
    for path in files:
        domain, body = _read_sample(path)
        score = score_human_text(body, model=model, domain=domain)
        score["file"] = path.name
        score["domain"] = domain
        score["above_threshold"] = score["edit_ratio"] > threshold
        per_file.append(score)

    total = len(per_file)
    over_edited = sum(1 for s in per_file if s["above_threshold"])
    quick_drops = sum(1 for s in per_file if s["density_preflight_quick_drop"])
    mean_ratio = sum(s["edit_ratio"] for s in per_file) / total if total else 0.0

    return {
        "eval_type": "false_positive",
        "lang": lang,
        "corpus": corpus,
        "model": model,
        "threshold": threshold,
        "summary": {
            "mean_edit_ratio": round(mean_ratio, 4),
            "files_over_threshold": over_edited,
            "total_files": total,
            "density_preflight_quick_drop_rate": (
                round(quick_drops / total, 2) if total else 0.0
            ),
        },
        "per_file": per_file,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="False-positive rate eval runner.")
    parser.add_argument("--lang", default="en")
    parser.add_argument(
        "--corpus", default="synthetic",
        choices=["synthetic", "public_domain", "contributed", "personal"],
    )
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()

    report = run(
        lang=args.lang, corpus=args.corpus, model=args.model, threshold=args.threshold
    )
    name = f"false_positive_{args.lang}_{args.corpus}"
    json_path, md_path = write_report(name, report)
    print(f"Wrote {json_path.name} and {md_path.name}")
    print(
        f"Mean edit ratio: {report['summary']['mean_edit_ratio']} "
        f"({report['summary']['files_over_threshold']}/{report['summary']['total_files']} over {args.threshold})"
    )
    sys.exit(1 if report["summary"]["files_over_threshold"] > 0 else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 13.3: Run pytest sweep (no new tests; sanity check)**

```bash
python3 -m pytest tests/ -v
```
Expected: all existing tests still pass.

- [ ] **Step 13.4: Commit**

```bash
git add evals/corpus/en/human/synthetic/technical_docs_01.md evals/scripts/run_false_positive_eval.py
git commit -m "feat(evals): run_false_positive_eval.py + technical synthetic sample"
```

---

## Task 14: Marketing synthetic sample + 5 AI samples for E2E

**Files:**
- Create: `evals/corpus/en/human/synthetic/marketing_copy_01.md`
- Create: `evals/corpus/en/e2e/ai_casual_01.json`

(Each subsequent task creates one more AI sample. Task 14b through 14e.)

- [ ] **Step 14.1: Create `marketing_copy_01.md`**

```markdown
---
domain: marketing
lang: en
notes: Genuine promotional voice. Stacked adjectives + rule-of-three are conventional here.
---

The HX-7 isn't a stove. It's the answer to every winter morning you've ever dreaded.

Engineered in Vermont, built to last three generations, and rated for a tenth of the firewood of your old box stove — the HX-7 takes the cold seriously so you don't have to. The catalytic combustor hits 1,200°F within eight minutes of a cold start. The cast-iron firebox holds eighteen hours of low burn on a single load of dense hardwood. The cooktop, glass-paneled and edge-banded in steel, can hold a stockpot, a kettle, and a cast-iron skillet all at once.

Every HX-7 is hand-finished in our Bennington shop. Every weld is inspected. Every door is squared by a person, not a jig. You don't buy three of these in a lifetime. You buy one, and you pass it on.

Order yours by November 1st for delivery before the season turns.
```

- [ ] **Step 14.2: Create `evals/corpus/en/e2e/ai_casual_01.json`**

```json
{
  "id": "e2e_en_casual_01",
  "lang": "en",
  "domain": "casual",
  "source": "manual_synthesis: prototypical AI casual blog opening",
  "input": "Great question! Here is an essay on this topic. I hope this helps!\n\nAI-assisted coding serves as an enduring testament to the transformative potential of large language models, marking a pivotal moment in the evolution of software development. In today's rapidly evolving technological landscape, these groundbreaking tools—nestled at the intersection of research and practice—are reshaping how engineers ideate, iterate, and deliver, underscoring their vital role in modern workflows.\n\nAt its core, the value proposition is clear: streamlining processes, enhancing collaboration, and fostering alignment. It's not just about autocomplete; it's about unlocking creativity at scale, ensuring that organizations can remain agile while delivering seamless, intuitive, and powerful experiences to users.",
  "reference_rewrite": null
}
```

- [ ] **Step 14.3: Commit**

```bash
git add evals/corpus/en/human/synthetic/marketing_copy_01.md evals/corpus/en/e2e/ai_casual_01.json
git commit -m "feat(evals): marketing synthetic sample + first E2E casual case"
```

---

## Task 15: 4 more E2E AI samples (one per remaining domain)

**Files:**
- Create: `evals/corpus/en/e2e/ai_academic_01.json`
- Create: `evals/corpus/en/e2e/ai_legal_01.json`

(Tasks 15b creates the technical + marketing E2E cases.)

- [ ] **Step 15.1: Create `ai_academic_01.json`**

```json
{
  "id": "e2e_en_academic_01",
  "lang": "en",
  "domain": "academic",
  "source": "manual_synthesis: AI-generated academic abstract with vocabulary tells",
  "input": "Recent advances in transformer-based architectures have ushered in a transformative paradigm shift in natural language processing, underscoring the pivotal role of attention mechanisms in capturing the intricate interplay of long-range dependencies. This paper delves into a comprehensive examination of how these robust, meticulously designed models contribute to the evolving landscape of cross-lingual transfer learning, foregrounding the seamless integration of multilingual corpora that bolster downstream task performance. We propose a novel framework that, fundamentally, redefines how these models can be fine-tuned for low-resource languages.",
  "reference_rewrite": null
}
```

- [ ] **Step 15.2: Create `ai_legal_01.json`**

```json
{
  "id": "e2e_en_legal_01",
  "lang": "en",
  "domain": "legal",
  "source": "manual_synthesis: AI-generated brief excerpt with vocabulary tells around appropriate legal register",
  "input": "Plaintiff respectfully submits that the District Court's order serves as a pivotal moment in this protracted litigation, underscoring the importance of adhering to well-established precedent. It is important to note that, fundamentally, the court below failed to delve into the comprehensive record before it, instead relying on a superficial reading that ultimately undermines the robust analytical framework this Court has consistently applied. In conclusion, Plaintiff submits that reversal is not only warranted but, indeed, essential to preserving the integrity of summary judgment proceedings going forward.",
  "reference_rewrite": null
}
```

- [ ] **Step 15.3: Commit**

```bash
git add evals/corpus/en/e2e/ai_academic_01.json evals/corpus/en/e2e/ai_legal_01.json
git commit -m "feat(evals): E2E academic + legal AI samples"
```

---

## Task 16: Last 2 E2E samples + run_e2e_eval.py

**Files:**
- Create: `evals/corpus/en/e2e/ai_technical_01.json`
- Create: `evals/corpus/en/e2e/ai_marketing_01.json`

- [ ] **Step 16.1: Create `ai_technical_01.json`**

```json
{
  "id": "e2e_en_technical_01",
  "lang": "en",
  "domain": "technical",
  "source": "manual_synthesis: AI-generated technical docs intro with vocabulary tells",
  "input": "The new RetryPolicy module represents a robust, comprehensive solution that fundamentally transforms how our SDK handles transient failures, underscoring the seamless integration of resilience patterns into the core request pipeline. This intuitive, meticulously engineered API leverages a sophisticated backoff strategy that contributes to higher success rates across a wide range of failure modes. Additionally, the module's design fosters alignment with industry best practices, ensuring that clients benefit from a battle-tested implementation. - **Configuration:** Simple, intuitive setup. - **Performance:** Significantly enhanced reliability. - **Compatibility:** Seamless integration.",
  "reference_rewrite": null
}
```

- [ ] **Step 16.2: Create `ai_marketing_01.json`**

```json
{
  "id": "e2e_en_marketing_01",
  "lang": "en",
  "domain": "marketing",
  "source": "manual_synthesis: AI-generated product page copy. Promotional register is OK; chatbot artifacts + AI vocabulary tells are not.",
  "input": "Of course! Here's some copy for your homepage. I hope this helps!\n\nThe Aurora X1 stands as a vibrant testament to the transformative potential of next-generation lighting, marking a pivotal moment in the evolving landscape of home design. Nestled at the intersection of form and function, this groundbreaking, meticulously crafted lamp boasts a comprehensive suite of intuitive features that fundamentally redefine how you illuminate your space — from seamlessly dimmable warmth to a robust app integration that ensures every room reflects your unique style. Let me know if you'd like a longer version!",
  "reference_rewrite": null
}
```

- [ ] **Step 16.3: Commit (samples only — runner is next task)**

```bash
git add evals/corpus/en/e2e/ai_technical_01.json evals/corpus/en/e2e/ai_marketing_01.json
git commit -m "feat(evals): E2E technical + marketing AI samples"
```

---

## Task 17: run_e2e_eval.py (judge LLM via Anthropic SDK)

**Files:**
- Create: `evals/scripts/run_e2e_eval.py`
- Modify: `tests/test_evals_shared.py`

- [ ] **Step 17.1: Append failing test for judge invocation (mocked)**

Append to `tests/test_evals_shared.py`:

```python


@patch("evals.scripts.run_e2e_eval._call_judge")
@patch("evals.scripts._shared.run_skill")
def test_e2e_eval_aggregates_three_runs(mock_run_skill, mock_judge):
    from evals.scripts.run_e2e_eval import score_case

    mock_run_skill.return_value = {
        "domain": "casual", "preflight": "", "draft": "Draft.", "final": "Cleaner final."
    }
    # Judge returns three runs of slightly varying scores
    mock_judge.side_effect = [
        {"human_ness": 8, "meaning": 9, "length": 8, "rationale": {"human_ness": "ok", "meaning": "ok", "length": "ok"}},
        {"human_ness": 7, "meaning": 9, "length": 9, "rationale": {"human_ness": "ok", "meaning": "ok", "length": "ok"}},
        {"human_ness": 9, "meaning": 10, "length": 7, "rationale": {"human_ness": "ok", "meaning": "ok", "length": "ok"}},
    ]

    case = {
        "id": "e2e_en_casual_01",
        "lang": "en",
        "domain": "casual",
        "input": "AI input.",
        "reference_rewrite": None,
        "source": "test",
    }
    score = score_case(case, runs=3, model="sonnet", judge_model="sonnet")

    assert score["case_id"] == "e2e_en_casual_01"
    assert score["mean"]["human_ness"] == pytest.approx(8.0, abs=0.01)
    assert score["mean"]["meaning"] == pytest.approx(9.333, abs=0.01)
    assert score["mean"]["length"] == pytest.approx(8.0, abs=0.01)
    assert score["stddev"]["human_ness"] > 0
    assert len(score["runs"]) == 3
```

- [ ] **Step 17.2: Run, verify FAIL**

```bash
python3 -m pytest tests/test_evals_shared.py -k e2e -v
```
Expected: ImportError.

- [ ] **Step 17.3: Create `evals/scripts/run_e2e_eval.py`**

```python
"""End-to-end eval runner — judge-LLM scored rewrite quality.

For each AI input in evals/corpus/{lang}/e2e/, run the skill, then ask a
judge LLM to score the rewrite on human-ness, meaning preservation, and
length appropriateness. Each case is run 3 times to capture both skill
sampling and judge noise; thresholds apply to the mean across runs.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

from anthropic import Anthropic

from evals.scripts._shared import (
    run_skill,
    verify_skill_install,
    write_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
JUDGE_PROMPT_PATH = REPO_ROOT / "evals" / "scripts" / "judge_prompt.md"

DEFAULT_RUNS = 3
DEFAULT_THRESHOLDS = {"human_ness": 7.5, "meaning": 9.0, "length": 7.0}


# Anthropic tool schema for structured judge scoring
_REPORT_SCORES_TOOL = {
    "name": "report_scores",
    "description": "Report the three judge scores for one rewrite.",
    "input_schema": {
        "type": "object",
        "properties": {
            "human_ness": {"type": "integer", "minimum": 1, "maximum": 10},
            "meaning": {"type": "integer", "minimum": 1, "maximum": 10},
            "length": {"type": "integer", "minimum": 1, "maximum": 10},
            "rationale": {
                "type": "object",
                "properties": {
                    "human_ness": {"type": "string"},
                    "meaning": {"type": "string"},
                    "length": {"type": "string"},
                },
                "required": ["human_ness", "meaning", "length"],
            },
        },
        "required": ["human_ness", "meaning", "length", "rationale"],
    },
}


def _model_to_api_id(model: str) -> str:
    """Map short names ('sonnet', 'opus') to current API IDs per repo conventions."""
    mapping = {
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-7",
        "haiku": "claude-haiku-4-5-20251001",
    }
    return mapping.get(model, model)


def _call_judge(
    *,
    judge_model: str,
    input_text: str,
    rewrite: str,
    domain: str,
) -> dict:
    """Single judge call. Returns parsed scores dict."""
    client = Anthropic()
    system_prompt = JUDGE_PROMPT_PATH.read_text(encoding="utf-8")
    user_msg = (
        f"Domain: {domain}\n\n"
        f"## ORIGINAL AI INPUT\n\n{input_text}\n\n"
        f"## SKILL REWRITE\n\n{rewrite}\n\n"
        "Reason briefly, then call report_scores."
    )
    response = client.messages.create(
        model=_model_to_api_id(judge_model),
        max_tokens=1024,
        system=system_prompt,
        tools=[_REPORT_SCORES_TOOL],
        tool_choice={"type": "tool", "name": "report_scores"},
        messages=[{"role": "user", "content": user_msg}],
    )
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "report_scores":
            return dict(block.input)
    raise RuntimeError("judge LLM did not call report_scores tool")


def score_case(
    case: dict, *, runs: int = DEFAULT_RUNS, model: str = "sonnet", judge_model: str = "sonnet"
) -> dict:
    """Run skill+judge `runs` times on one case and aggregate mean+stddev."""
    run_results = []
    for run_idx in range(runs):
        skill_out = run_skill(
            case["input"],
            lang=case.get("lang", "en"),
            mode="full",
            domain=case.get("domain"),
            model=model,
        )
        rewrite = skill_out.get("final") or skill_out.get("draft") or ""
        scores = _call_judge(
            judge_model=judge_model,
            input_text=case["input"],
            rewrite=rewrite,
            domain=case.get("domain", "casual"),
        )
        scores["rewrite_length_words"] = len(rewrite.split())
        run_results.append(scores)

    def _mean(key: str) -> float:
        return round(statistics.fmean(r[key] for r in run_results), 3)

    def _stddev(key: str) -> float:
        if runs < 2:
            return 0.0
        return round(statistics.stdev(r[key] for r in run_results), 3)

    return {
        "case_id": case["id"],
        "domain": case.get("domain"),
        "runs": run_results,
        "mean": {k: _mean(k) for k in ("human_ness", "meaning", "length")},
        "stddev": {k: _stddev(k) for k in ("human_ness", "meaning", "length")},
    }


def run(
    lang: str = "en",
    domain: str | None = None,
    runs: int = DEFAULT_RUNS,
    model: str = "sonnet",
    judge_model: str = "sonnet",
) -> dict:
    verify_skill_install()
    corpus_dir = REPO_ROOT / "evals" / "corpus" / lang / "e2e"
    case_files = sorted(corpus_dir.glob("*.json"))

    per_case = []
    for path in case_files:
        case = json.loads(path.read_text(encoding="utf-8"))
        if domain and case.get("domain") != domain:
            continue
        per_case.append(score_case(case, runs=runs, model=model, judge_model=judge_model))

    overall = {}
    if per_case:
        for k in ("human_ness", "meaning", "length"):
            overall[k] = round(
                statistics.fmean(c["mean"][k] for c in per_case), 3
            )

    return {
        "eval_type": "e2e",
        "lang": lang,
        "model": model,
        "judge_model": judge_model,
        "runs_per_case": runs,
        "thresholds": DEFAULT_THRESHOLDS,
        "summary": {
            "overall_mean": overall,
            "total_cases": len(per_case),
            "below_threshold_count": sum(
                1 for c in per_case
                if c["mean"]["human_ness"] < DEFAULT_THRESHOLDS["human_ness"]
            ),
        },
        "per_case": per_case,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="E2E rewrite-quality eval runner.")
    parser.add_argument("--lang", default="en")
    parser.add_argument("--domain", default=None)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument(
        "--judge-model", default="sonnet",
        help="Short name (sonnet, opus) or full API ID",
    )
    args = parser.parse_args()

    report = run(
        lang=args.lang,
        domain=args.domain,
        runs=args.runs,
        model=args.model,
        judge_model=args.judge_model,
    )
    json_path, md_path = write_report(f"e2e_{args.lang}", report)
    print(f"Wrote {json_path.name} and {md_path.name}")
    print(f"Overall mean: {report['summary']['overall_mean']}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 17.4: Run, verify PASS**

```bash
python3 -m pytest tests/test_evals_shared.py -v
```
Expected: 17 passed.

- [ ] **Step 17.5: Commit**

```bash
git add evals/scripts/run_e2e_eval.py tests/test_evals_shared.py
git commit -m "feat(evals): run_e2e_eval.py with judge LLM via Anthropic SDK"
```

---

## Task 18: evals/README.md + .gitignore updates

**Files:**
- Create: `evals/README.md`
- Modify: `.gitignore`

- [ ] **Step 18.1: Create `evals/README.md`**

```markdown
# humanizer-ext eval infrastructure

Three eval types target the humanizer skill from different angles:

- **`run_pattern_eval.py`** — detection rate per pattern (cheap, deterministic-ish, runs against curated before/after pairs)
- **`run_false_positive_eval.py`** — edit distance ratio on human-written texts (catches over-editing)
- **`run_e2e_eval.py`** — judge-LLM scored rewrite quality on whole AI documents (expensive, holistic)

Reports land in `evals/reports/` as paired JSON + Markdown. Personal-mode reports (`evals/reports/*_personal_*`) are gitignored.

## Prerequisites

Eval scripts call the `claude` CLI to invoke the skill. The CLI loads whatever humanizer skill is installed at `~/.claude/skills/humanizer/`. Before running an eval against the repo's current SKILL.md, point the install at the repo:

```bash
# From the humanizer-ext repo root
ln -sfn "$PWD/SKILL.md" ~/.claude/skills/humanizer/SKILL.md
mkdir -p ~/.claude/skills/humanizer/patterns ~/.claude/skills/humanizer/domains
ln -sfn "$PWD/patterns/_universal.md" ~/.claude/skills/humanizer/patterns/_universal.md
ln -sfn "$PWD/patterns/en.md" ~/.claude/skills/humanizer/patterns/en.md
ln -sfn "$PWD/domains/en_overrides.md" ~/.claude/skills/humanizer/domains/en_overrides.md
```

The eval `_shared.py` exposes `verify_skill_install()` which is called at the start of every runner. If the installed SKILL.md bytes differ from the repo's SKILL.md, the run aborts with a clear error before any API calls.

## Install dependencies

```bash
pip install '.[evals]'   # or: pip install anthropic rapidfuzz
```

Set `ANTHROPIC_API_KEY` in your environment for `run_e2e_eval.py`'s judge calls.

## Running the evals

```bash
# Pattern detection (all patterns)
python evals/scripts/run_pattern_eval.py --lang en --model sonnet

# Pattern detection (single pattern)
python evals/scripts/run_pattern_eval.py --lang en --pattern 7

# False-positive rate (synthetic corpus)
python evals/scripts/run_false_positive_eval.py --lang en --corpus synthetic

# E2E rewrite quality (3 runs per case, Sonnet judge)
python evals/scripts/run_e2e_eval.py --lang en --runs 3 --judge-model sonnet

# E2E with Opus judge (more expensive, more discriminating)
python evals/scripts/run_e2e_eval.py --lang en --judge-model opus
```

## Adding a new language pack (per the v3.5.0 spec)

1. **Phase A — Wiki seed (if available)** — check whether the target Wikipedia community maintains an "Anzeichen für KI-generierte Inhalte" / "Identifier l'usage d'une IA générative" equivalent.
2. **Phase B — Empirical mining** — generate an AI corpus + human corpus, run `mine_patterns.py` (Phase 2 deliverable) to extract candidate AI tells via log-likelihood divergence.
3. **Phase C — Manual curation** — review candidates, write `patterns/<lang>.md` and `domains/<lang>_overrides.md`.
4. **Phase D — Cross-reference** — public NLP papers, AI-detection tool indicator lists, community PRs after first release.
5. **Build eval corpus** — `evals/corpus/<lang>/{patterns,human,e2e}/` parallel to the EN structure.
6. **Iterate** — run all three evals against the new pack until thresholds pass:
   - Pattern detection: ≥ 0.85 per pattern
   - False-positive rate: ≤ 0.10 mean edit ratio on human samples
   - E2E quality: human-ness mean ≥ 7.5, meaning ≥ 9, length within ±15%

## Personal-mode false-positive testing

To test the skill against your own writing without committing it:

```bash
export HUMANIZER_SAMPLES_DIR=~/.claude/humanizer-samples
python evals/scripts/run_false_positive_eval.py --corpus personal
```

Personal-mode reports go to `evals/reports/*_personal_*.json` (gitignored).
```

- [ ] **Step 18.2: Append to `.gitignore`**

Append at the end:

```
# Personal-mode eval reports — never committed
evals/reports/*_personal_*
evals/reports/personal_*

# Eval report archive (keep only the most recent summary in tree)
evals/reports/*.json
evals/reports/*.md
!evals/reports/.gitkeep
!evals/reports/summary_latest_en.md
!evals/reports/summary_latest_en.json
```

- [ ] **Step 18.3: Create `evals/reports/.gitkeep`**

```bash
mkdir -p evals/reports
touch evals/reports/.gitkeep
```

- [ ] **Step 18.4: Commit**

```bash
git add evals/README.md .gitignore evals/reports/.gitkeep
git commit -m "docs(evals): README + .gitignore for personal-mode reports"
```

---

## Task 19: Run EN baseline (live API calls)

**Files:**
- Create: `evals/reports/summary_latest_en.md`
- Create: `evals/reports/summary_latest_en.json`

This task makes real API calls (estimated cost ≤$5 with Sonnet judge across 5 E2E cases × 3 runs + 40 pattern cases + 5 false-positive cases). The runner outputs the per-eval reports; this task aggregates them into the single committed "latest" summary.

**Before running:** ensure the symlink setup from the prerequisites section is done and `ANTHROPIC_API_KEY` is set.

- [ ] **Step 19.1: Verify the install is symlinked to the repo**

```bash
cd "/Users/christianhuhn/Library/Mobile Documents/iCloud~md~obsidian/Documents/duathron.github.io/__obsidian_vault/AI/SKILLS/humanizer-ext"
diff -q SKILL.md ~/.claude/skills/humanizer/SKILL.md && echo "OK installed matches repo" || echo "MISMATCH — fix before running"
```

If MISMATCH, run the symlink commands from `evals/README.md` then re-verify.

- [ ] **Step 19.2: Run pattern eval**

```bash
python3 evals/scripts/run_pattern_eval.py --lang en --model sonnet 2>&1 | tee /tmp/pattern_run.log
```

Expected: per-pattern detection rates + overall rate. Exit non-zero if any pattern below threshold — that's the report's main signal, not a fail-the-task condition. Capture the report filename from the output.

- [ ] **Step 19.3: Run false-positive eval**

```bash
python3 evals/scripts/run_false_positive_eval.py --lang en --corpus synthetic --model sonnet 2>&1 | tee /tmp/fp_run.log
```

Expected: mean edit ratio across 5 synthetic human samples. Capture report filename.

- [ ] **Step 19.4: Run E2E eval (5 cases × 3 runs = 15 skill calls + 15 judge calls)**

```bash
python3 evals/scripts/run_e2e_eval.py --lang en --runs 3 --model sonnet --judge-model sonnet 2>&1 | tee /tmp/e2e_run.log
```

Expected: overall mean per dimension across 5 cases. This is the most expensive step — runs in ~5 minutes depending on API latency.

- [ ] **Step 19.5: Aggregate into committed summary**

Create `evals/reports/summary_latest_en.md` with this template (fill in numbers from the three runs):

```markdown
# EN Baseline Eval Summary

**Date:** 2026-05-24 (or whichever date the runs were executed)
**Skill version:** humanizer v3.3.0 (commit f973735) — see `git rev-parse HEAD`
**Skill model:** sonnet
**Judge model:** sonnet
**Runs:** pattern (1 sample), false-positive (1 sample), e2e (3 samples per case)

## Pattern detection
- Overall detection rate: **{rate from /tmp/pattern_run.log}**
- Patterns below 0.85 threshold: **{count}** of **{total}**
- Detail report: `evals/reports/pattern_en_<timestamp>.{json,md}`

## False-positive rate (synthetic corpus)
- Mean edit ratio: **{ratio from /tmp/fp_run.log}**
- Files above 0.10 threshold: **{count}** of **{total}**
- Detail report: `evals/reports/false_positive_en_synthetic_<timestamp>.{json,md}`

## E2E rewrite quality
- Overall mean human_ness: **{value}** (threshold 7.5)
- Overall mean meaning: **{value}** (threshold 9.0)
- Overall mean length: **{value}** (threshold 7.0)
- Cases below human_ness threshold: **{count}** of **{total}**
- Detail report: `evals/reports/e2e_en_<timestamp>.{json,md}`

## Interpretation

{One paragraph: what passed, what didn't, what the gaps tell us about the
skill's current weakness profile. This is the human read of the numbers.}

## Next steps

- {Specific pattern IDs below 0.85, if any, deserve corpus expansion or
  pattern body refinement before v3.4.0 ships.}
- {Files above the false-positive threshold, if any, may indicate the
  density preflight needs tuning.}
- {E2E dimensions below threshold, if any, point at specific skill weak spots.}
```

Also create `evals/reports/summary_latest_en.json` with the structured equivalent:

```json
{
  "date": "2026-05-24",
  "skill_version": "v3.3.0",
  "skill_commit": "f973735",
  "skill_model": "sonnet",
  "judge_model": "sonnet",
  "pattern": {
    "overall_rate": null,
    "below_threshold": null,
    "total_patterns": null,
    "report_filename": null
  },
  "false_positive": {
    "mean_edit_ratio": null,
    "files_over_threshold": null,
    "total_files": null,
    "report_filename": null
  },
  "e2e": {
    "overall_mean": {"human_ness": null, "meaning": null, "length": null},
    "cases_below_threshold": null,
    "total_cases": null,
    "report_filename": null
  }
}
```

Fill in all `null` values from the three runs.

- [ ] **Step 19.6: Commit baseline summary**

```bash
git add evals/reports/summary_latest_en.md evals/reports/summary_latest_en.json
git commit -m "test(evals): record v3.3.0 EN baseline (pattern + fp + e2e)"
```

---

## Task 20: README updates + version bump + tag v3.4.0

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`

- [ ] **Step 20.1: Bump SKILL.md frontmatter version**

In `SKILL.md` line 3, change:
```yaml
version: 3.3.0
```
to:
```yaml
version: 3.4.0
```

- [ ] **Step 20.2: Add v3.4.0 entry to README "Version History"**

Insert immediately above the existing `- **3.3.0** -` line:

```markdown
- **3.4.0** - Adds the evaluation infrastructure described in the v3.5.0 design spec. Three eval runners ship as part of the repo tooling: `evals/scripts/run_pattern_eval.py` (per-pattern detection rate; threshold 0.85), `evals/scripts/run_false_positive_eval.py` (edit distance ratio on known-human texts; threshold 0.10), and `evals/scripts/run_e2e_eval.py` (whole-document rewrite quality scored by a judge LLM via the Anthropic SDK, with `--judge-model {sonnet,opus}` opt-in). Shared utilities live in `evals/scripts/_shared.py` and are unit-tested in `tests/test_evals_shared.py`. The EN corpus seeds at `evals/corpus/en/{patterns,human,e2e}/` cover all 40 patterns (auto-extracted from the pattern packs), 5 synthetic human samples (one per domain), and 5 AI-generated whole-document cases (one per domain). A v3.3.0 EN baseline report is committed at `evals/reports/summary_latest_en.{json,md}`. No skill behavior changes ship in this release — the skill itself is identical to v3.3.0; only the repo-side eval tooling is new. The `verify_skill_install()` guard ensures evals always run against the repo's current SKILL.md, not a stale install.
```

- [ ] **Step 20.3: Run final test sweep**

```bash
python3 -m pytest tests/ -v
```
Expected: all 32 tests pass (15 skill structure + 17 eval shared).

- [ ] **Step 20.4: Commit release + tag**

```bash
git add SKILL.md README.md
git commit -m "release: v3.4.0 — eval infrastructure (pattern + fp + e2e)"
git tag -a v3.4.0 -m "v3.4.0 — three-tier eval harness against EN baseline"
```

Do not push. User confirms before push.

---

## Self-Review

**Spec coverage:**

- §4.5 eval infra layout → Tasks 1, 8, 18 (scripts dir, judge rubric, README). ✓
- §4.6 type 1 (pattern detection) → Tasks 9, 10. ✓
- §4.6 type 2 (false-positive) → Tasks 11, 12, 13, 14 (samples) + Task 13 (runner). ✓
- §4.6 type 3 (E2E judge-scored, 3× variance) → Tasks 14, 15, 16 (samples) + Task 17 (runner). ✓
- §4.7 phase-A wiki seed (DE/FR/ES/IT path) → documented in Task 18 README, not built (Phase 2 scope). ✓
- §5.2 `_shared.py` exports — `run_skill`, `parse_skill_output`, `load_pattern_corpus`, `Case`, `retry_with_backoff`, `write_report` → Tasks 3, 4, 5, 6. ✓
- §5.2 `--personal` flag → Task 13 includes `personal` as a corpus choice but the personal-samples lookup chain itself is documented in spec §4.4 and deferred to Phase 2 build (Task 18 README documents the user-side env var convention; the runner reads `HUMANIZER_SAMPLES_DIR` in Phase 2). Gap accepted with rationale: Phase 2 personal-samples lookup chain is non-trivial (4-step convention + lang subfolder logic) and belongs with the DE pack work.
- §5.2 judge prompt at `evals/scripts/judge_prompt.md` → Task 8. ✓
- §5.3 corpus JSON schema for patterns → Task 3 (loader) + Task 9 (seed files). ✓
- §5.3 human/ subdirectory split (public_domain, synthetic, contributed) → Tasks 11–14 create `synthetic/`. `public_domain/` is empty in v3.4.0 (Phase 3 work; the EN baseline runs against synthetic only). `contributed/` exists per Task 18 README mention but no PR template yet. Gap accepted: synthetic is sufficient for the v3.4.0 baseline.
- §5.3 e2e JSON schema → Tasks 14, 15, 16. ✓
- §5.4 README updates + .gitignore → Tasks 18, 20. ✓
- §6 Phase 1 baseline report → Task 19. ✓
- §7 success criteria for Phase 1 (all three eval runners produce reports) → Task 19. ✓

**Gap acknowledgements:**

- Personal-samples mode is wired *as a CLI argument* (Task 13) but the lookup chain implementation lives with Phase 2. Tagged in Task 18 README under "Personal-mode false-positive testing" with a note that the runner reads `HUMANIZER_SAMPLES_DIR`; the actual chain (CLI flag → env → `~/.claude/humanizer-samples/` → `./writing-samples/`) is one Phase-2 task to add to `_shared.py`. Acceptable.
- `public_domain/` corpus subdirectory is empty in v3.4.0. Filling it from Project Gutenberg + Wikipedia pre-2022 revisions is mechanical but tedious work that does not gate baseline numbers — the synthetic samples are sufficient signal. Phase 3 cleanup.
- `mine_patterns.py` is Phase 2 scope (DE pack); not in this plan.

**Placeholder scan:** Searched for "TBD", "TODO", "fill in", "implement later", "similar to Task". Found only one legitimate `{fill in numbers from the three runs}` template instruction in Task 19.5 — that is an explicit instruction to the implementer to fill in the baseline metrics during the live run, not a plan-side placeholder. Clean. ✓

**Type / signature consistency:**

- `Case` dataclass defined Task 3 with fields `id, input, expected_changes, expected_unchanged, domain, metadata`. Used in Tasks 5 (run_skill takes `text` not Case — `Case.input` is the field), 10 (`score_case(case: Case)`), 17 (`score_case(case: dict)` — note: e2e uses raw dict from JSON, not Case). The Case/dict inconsistency is intentional: pattern eval has the seed corpus generator already producing JSON-loaded-to-Case via `load_pattern_corpus`; E2E corpus files are single-document JSON and don't go through the same loader. Acceptable but worth a follow-up to unify (Phase 2). ✓
- `run_skill` signature `(text, *, lang, mode, domain, samples_dir, model, timeout)` consistent across Tasks 5 + 10 + 13 + 17 calls. ✓
- `verify_skill_install` (Task 7) called by all three runners (Tasks 10, 13, 17). ✓
- `write_report(name, data) -> (json_path, md_path)` defined Task 6, called Tasks 10, 13, 17. ✓
- `parse_skill_output` returns dict with keys `domain, preflight, draft, final`. Consumed in Tasks 5 (test), 10 (`result.get("final")`), 13 (same), 17 (same). ✓
- Judge tool name `report_scores` (Task 8 + Task 17). Schema keys `human_ness, meaning, length, rationale`. Consistent. ✓
- Anthropic model IDs (Task 17): `_model_to_api_id` returns the IDs from the harness environment block (Opus 4.7 / Sonnet 4.6 / Haiku 4.5). Correct as of plan date. ✓

**Subagent atomicity audit:** Every task touches ≤2 files. Largest single-file new content: `run_e2e_eval.py` (~150 lines) and `run_pattern_eval.py` (~110 lines) — both within general-purpose subagent comfort. Cavecrew-builder is suited for the small mechanical tasks (corpus JSON, sample markdown, READMEs, version bumps). The plan header explicitly notes which subagent type fits which task class.

No issues found.

---

## Execution Handoff

**Plan complete and saved to `docs/plans/2026-05-24-phase-1-eval-infrastructure.md`.** Two execution options:

**1. Subagent-Driven (recommended)** — Same approach as Phase 0: dispatch fresh `cavecrew-builder` (Sonnet) for mechanical tasks and `general-purpose` agent (Sonnet) for the Python runners. Parent (Opus) verifies pytest between tasks and runs the live API baseline (Task 19) directly since it needs `ANTHROPIC_API_KEY` + symlink-verified install in the parent's environment.

**2. Inline Execution** — Run tasks in this Opus session via `superpowers:executing-plans`. Slower but you see every step. Tasks 11–16 (corpus content creation) and Task 19 (baseline run) are equally fast either way.

**Which approach?**
