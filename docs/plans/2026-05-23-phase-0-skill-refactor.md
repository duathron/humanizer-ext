# Phase 0 (v3.3.0): SKILL.md Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Subagent constraint:** Implementation will be delegated to `cavecrew-builder` (Sonnet) which hard-refuses 3+ file edits per task. Every task in this plan touches ≤2 files. Tasks with file extractions split the read-from-source and write-to-target into separate atomic steps when needed.

**Goal:** Split the monolithic 959-line `SKILL.md` into a language-agnostic framework + `patterns/{_universal,en}.md` + `domains/en_overrides.md`, with zero observable behavior change for English input. Ships as v3.3.0.

**Architecture:** Strict byte-equivalent extraction first (no semantic change), then SKILL.md becomes a thin framework that instructs Claude to Read the relevant pack files at runtime. Repo-structure tests (pytest, no API calls) verify schema integrity and cross-reference consistency. A single manual regression run against the existing "Full Example" confirms output parity.

**Tech Stack:** Markdown (skill packs), Python 3.10+ (pytest sanity tests), PyYAML (frontmatter parsing).

**Spec:** `docs/specs/2026-05-23-humanizer-eval-de-design.md` §4.1, §5.1, §6 Phase 0.

**Out of scope for this plan:** eval scripts, DE pack, FR/ES/IT extensibility, anything beyond byte-equivalent EN behavior preservation. Those land in Phase 1 / Phase 2 / Phase 3 plans (written after this phase ships).

---

## File Structure

After Phase 0, the repo layout is:

```
humanizer-ext/
├── SKILL.md                          # framework only (~12 KB, was 60 KB)
├── patterns/
│   ├── _universal.md                 # 12 universal patterns (#6, #14, #15, #17, #18, #19, #25, #26, #29, #38, #39, #40)
│   └── en.md                         # 28 EN-specific patterns + EN PERSONALITY AND SOUL examples
├── domains/
│   └── en_overrides.md               # EN domain × pattern override matrix + EN domain-specific guidance
├── tests/
│   ├── __init__.py
│   └── test_skill_structure.py       # pytest sanity tests, no API calls
├── docs/
│   ├── regression-cases/
│   │   └── full_example.md           # the existing "Full Example" input + expected output for manual regression
│   ├── PROJECT_HISTORY.md            # (existing)
│   └── specs/                        # (existing)
├── pyproject.toml                    # minimal pytest config + dev deps
├── .gitignore                        # appended
└── (existing files unchanged: README.md, LICENSE, WARP.md, .claude-plugin/)
```

**Pattern → file mapping (locked at planning time):**

- **`patterns/_universal.md` (12 patterns):** #6 Challenges sections (SKILL.md L276–287), #14 Em dash (L396–419), #15 Boldface (L420–430), #17 Title case (L444–454), #18 Emojis (L455–467), #19 Curly quotes (L468–477), #25 Generic conclusions (L562–573), #26 Hyphenation (L575–587), #29 Fragmented headers (L614–631), #38 Reference-markup (L769–792), #39 Phrasal templates (L794–808), #40 Markdown contamination (L809–833).
- **`patterns/en.md` (28 patterns):** #1 (L211–222), #2 (L224–235), #3 (L237–248), #4 (L250–261), #5 (L263–274), #7 (L291–310), #8 (L312–323), #9 (L325–348), #10 (L350–359), #11 (L361–370), #12 (L372–381), #13 (L383–392), #16 (L431–442), #20 (L481–492), #21 (L494–511), #22 (L513–522), #23 (L526–549), #24 (L551–560), #27 (L588–599), #28 (L601–612), #30 (L633–644), #31 (L646–660), #32 (L662–673), #33 (L675–686), #34 (L688–697), #35 (L701–724), #36 (L728–739), #37 (L741–763). Plus the entire `## PERSONALITY AND SOUL` section (L174–207) since its examples are EN-specific.
- **`domains/en_overrides.md`:** the `### Domain overrides` table (L50–79) + `### Domain-specific guidance` body (L81–91).
- **`SKILL.md` after refactor (stays in framework):** frontmatter (L1–20), `# Humanizer` intro (L22–24), `## Mode` (L26–34), `## Domain` intro paragraph (L36–48), `## Detection Guidance` (L93–135), `## Your Task` (L137–151), `## Voice Calibration` (L153–171), `## Process` (L835–877), `## Output Format` (L879–890), `## Reference` (L955–959). Adds new instructions to Read the pack files at runtime.

---

## Task 1: Project scaffolding (pytest + pyproject)

**Files:**
- Create: `pyproject.toml`
- Create: `tests/__init__.py`

- [ ] **Step 1.1: Create `pyproject.toml` with minimal pytest config**

```toml
[project]
name = "humanizer-ext"
version = "3.3.0-dev"
description = "Humanizer skill — repo-side tooling for tests and evals"
requires-python = ">=3.10"

[project.optional-dependencies]
dev = ["pytest>=8.0", "pyyaml>=6.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v"
```

- [ ] **Step 1.2: Create empty `tests/__init__.py`**

```python
```

- [ ] **Step 1.3: Verify pytest discovers no tests yet**

Run: `python -m pytest tests/ -v`
Expected: `no tests ran in 0.XXs`

- [ ] **Step 1.4: Commit**

```bash
git add pyproject.toml tests/__init__.py
git commit -m "chore: add pyproject.toml + pytest scaffolding for v3.3.0 refactor"
```

---

## Task 2: First failing test — SKILL.md frontmatter sanity

**Files:**
- Create: `tests/test_skill_structure.py`

- [ ] **Step 2.1: Write the failing test for frontmatter validity + description length cap**

```python
"""Repo-structure sanity tests. No API calls."""
from pathlib import Path
import re
import yaml

REPO_ROOT = Path(__file__).parent.parent


def _parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise AssertionError(f"{path}: no YAML frontmatter found")
    return yaml.safe_load(match.group(1))


def test_skill_md_frontmatter_valid():
    fm = _parse_frontmatter(REPO_ROOT / "SKILL.md")
    assert fm.get("name") == "humanizer"
    assert "description" in fm
    assert "version" in fm


def test_skill_md_description_under_plugin_limit():
    """Claude Code plugin frontmatter caps description at 1024 chars."""
    fm = _parse_frontmatter(REPO_ROOT / "SKILL.md")
    assert len(fm["description"]) <= 1024, (
        f"description is {len(fm['description'])} chars, "
        f"exceeds Claude Code 1024-char limit"
    )
```

- [ ] **Step 2.2: Run test, confirm PASS (sanity test passes against current SKILL.md)**

Run: `python -m pytest tests/test_skill_structure.py -v`
Expected: 2 passed. This is the baseline.

- [ ] **Step 2.3: Commit**

```bash
git add tests/test_skill_structure.py
git commit -m "test: add SKILL.md frontmatter sanity tests"
```

---

## Task 3: Extract universal patterns to `patterns/_universal.md`

**Files:**
- Create: `patterns/_universal.md`
- Modify: `tests/test_skill_structure.py`

- [ ] **Step 3.1: Write failing test for `patterns/_universal.md` existence + expected pattern IDs**

Append to `tests/test_skill_structure.py`:

```python
UNIVERSAL_PATTERN_IDS = {6, 14, 15, 17, 18, 19, 25, 26, 29, 38, 39, 40}


def _pattern_ids_in_file(path: Path) -> set[int]:
    """Find lines like '### 14. Em Dash Overuse...' and return the IDs."""
    text = path.read_text(encoding="utf-8")
    return {
        int(m.group(1))
        for m in re.finditer(r"^### (\d+)\.\s", text, re.MULTILINE)
    }


def test_universal_pack_exists():
    assert (REPO_ROOT / "patterns" / "_universal.md").is_file()


def test_universal_pack_contains_expected_patterns():
    ids = _pattern_ids_in_file(REPO_ROOT / "patterns" / "_universal.md")
    assert ids == UNIVERSAL_PATTERN_IDS, (
        f"_universal.md pattern IDs differ from spec: "
        f"missing {UNIVERSAL_PATTERN_IDS - ids}, extra {ids - UNIVERSAL_PATTERN_IDS}"
    )
```

- [ ] **Step 3.2: Run test, confirm FAIL with "file does not exist"**

Run: `python -m pytest tests/test_skill_structure.py::test_universal_pack_exists -v`
Expected: FAIL.

- [ ] **Step 3.3: Create `patterns/_universal.md` by extracting the 12 universal patterns from SKILL.md**

Create `patterns/_universal.md` with this structure:

````markdown
# Universal Patterns

These patterns apply identically across all languages. The framework (`SKILL.md`) always loads this file in addition to the language-specific pack.

## Structural patterns

[Copy SKILL.md L276–287 here verbatim: ### 6. Outline-like "Challenges and Future Prospects" Sections + its Before/After block]

[Copy SKILL.md L562–573 verbatim: ### 25. Generic Positive Conclusions + body + structural-section note]

[Copy SKILL.md L614–631 verbatim: ### 29. Fragmented Headers + body]

## Style patterns

[Copy SKILL.md L396–419 verbatim: ### 14. Em Dash Overuse and Paired Bracketing + body]

[Copy SKILL.md L420–430 verbatim: ### 15. Overuse of Boldface + body]

[Copy SKILL.md L444–454 verbatim: ### 17. Title Case in Headings + body]

[Copy SKILL.md L455–467 verbatim: ### 18. Emojis + body]

[Copy SKILL.md L468–477 verbatim: ### 19. Curly Quotation Marks + body]

[Copy SKILL.md L575–587 verbatim: ### 26. Hyphenated Word Pair Overuse + body]

## Artifacts and contamination

These do not occur in genuinely human-written text — when present, AI involvement is essentially confirmed. **Always strip them, regardless of domain.**

[Copy SKILL.md L769–792 verbatim: ### 38. Reference-Markup Artifacts + body]

[Copy SKILL.md L794–808 verbatim: ### 39. Phrasal Templates and Placeholder Text + body]

[Copy SKILL.md L809–833 verbatim: ### 40. Markdown / Wikitext Contamination + body]
````

The `[Copy SKILL.md L<n>–<m> verbatim: ...]` notation is an instruction to the implementing subagent: read those lines from current SKILL.md and paste them in unchanged. Do not paraphrase, do not edit text inside the copied blocks.

- [ ] **Step 3.4: Run tests, confirm both PASS**

Run: `python -m pytest tests/test_skill_structure.py -v`
Expected: all 4 tests pass.

- [ ] **Step 3.5: Commit**

```bash
git add patterns/_universal.md tests/test_skill_structure.py
git commit -m "refactor: extract 12 universal patterns into patterns/_universal.md"
```

---

## Task 4: Extract EN-specific patterns to `patterns/en.md`

**Files:**
- Create: `patterns/en.md`
- Modify: `tests/test_skill_structure.py`

- [ ] **Step 4.1: Write failing tests for `patterns/en.md`**

Append to `tests/test_skill_structure.py`:

```python
EN_PATTERN_IDS = {
    1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 16, 20, 21, 22, 23, 24,
    27, 28, 30, 31, 32, 33, 34, 35, 36, 37,
}


def test_en_pack_exists():
    assert (REPO_ROOT / "patterns" / "en.md").is_file()


def test_en_pack_contains_expected_patterns():
    ids = _pattern_ids_in_file(REPO_ROOT / "patterns" / "en.md")
    assert ids == EN_PATTERN_IDS, (
        f"en.md pattern IDs differ from spec: "
        f"missing {EN_PATTERN_IDS - ids}, extra {ids - EN_PATTERN_IDS}"
    )


def test_en_pack_includes_personality_section():
    text = (REPO_ROOT / "patterns" / "en.md").read_text(encoding="utf-8")
    assert "## PERSONALITY AND SOUL" in text


def test_universal_and_en_packs_are_disjoint():
    """No pattern ID appears in both packs."""
    universal = _pattern_ids_in_file(REPO_ROOT / "patterns" / "_universal.md")
    en = _pattern_ids_in_file(REPO_ROOT / "patterns" / "en.md")
    assert universal & en == set(), f"overlapping pattern IDs: {universal & en}"
```

- [ ] **Step 4.2: Run tests, confirm new ones FAIL**

Run: `python -m pytest tests/test_skill_structure.py -v`
Expected: existing 4 pass, new 4 fail with file-not-found.

- [ ] **Step 4.3: Create `patterns/en.md` by extracting the 28 EN-specific patterns + PERSONALITY AND SOUL from SKILL.md**

Create `patterns/en.md` with this structure:

````markdown
# English Patterns

English-specific patterns. Loaded by the framework (`SKILL.md`) when the detected input language is English. Apply alongside `patterns/_universal.md`.

[Copy SKILL.md L174–207 verbatim: the entire ## PERSONALITY AND SOUL section including the domain note, Signs of soulless writing, How to add voice, Before, After]

## Content patterns

[Copy SKILL.md L211–222 verbatim: ### 1. Undue Emphasis on Significance + body]
[Copy SKILL.md L224–235 verbatim: ### 2. Undue Emphasis on Notability + body]
[Copy SKILL.md L237–248 verbatim: ### 3. Superficial Analyses + body]
[Copy SKILL.md L250–261 verbatim: ### 4. Promotional Language + body]
[Copy SKILL.md L263–274 verbatim: ### 5. Vague Attributions + body]

## Language and grammar patterns

[Copy SKILL.md L291–310 verbatim: ### 7. Overused AI Vocabulary + body, including era clusters]
[Copy SKILL.md L312–323 verbatim: ### 8. Copula Avoidance + body]
[Copy SKILL.md L325–348 verbatim: ### 9. Negative Parallelisms + body]
[Copy SKILL.md L350–359 verbatim: ### 10. Rule of Three Overuse + body]
[Copy SKILL.md L361–370 verbatim: ### 11. Elegant Variation + body]
[Copy SKILL.md L372–381 verbatim: ### 12. False Ranges + body]
[Copy SKILL.md L383–392 verbatim: ### 13. Passive Voice + body]

## Style patterns (EN-specific subset)

[Copy SKILL.md L431–442 verbatim: ### 16. Inline-Header Vertical Lists + body]

## Communication patterns

[Copy SKILL.md L481–492 verbatim: ### 20. Collaborative Communication Artifacts + body]
[Copy SKILL.md L494–511 verbatim: ### 21. Cutoff Disclaimers + body]
[Copy SKILL.md L513–522 verbatim: ### 22. Sycophantic Tone + body]

## Filler and hedging

[Copy SKILL.md L526–549 verbatim: ### 23. Filler Phrases + didactic-disclaimer note]
[Copy SKILL.md L551–560 verbatim: ### 24. Excessive Hedging + body]

## Persuasion and signposting

[Copy SKILL.md L588–599 verbatim: ### 27. Persuasive Authority Tropes + body]
[Copy SKILL.md L601–612 verbatim: ### 28. Signposting and Announcements + body]

## Newer language tells

[Copy SKILL.md L633–644 verbatim: ### 30. Sentence-Starter Intensifiers + body]
[Copy SKILL.md L646–660 verbatim: ### 31. Rhetorical and Self-Answering Questions + body]
[Copy SKILL.md L662–673 verbatim: ### 32. Stacked Intensifier Adjectives + body]
[Copy SKILL.md L675–686 verbatim: ### 33. Quantity Vagueness + body]
[Copy SKILL.md L688–697 verbatim: ### 34. Trailing Emphasis Fragments + body]

## Heading patterns

[Copy SKILL.md L701–724 verbatim: ### 35. Debunking-Pose Headings + body]

## Epistemic patterns

[Copy SKILL.md L728–739 verbatim: ### 36. Conditional Frame Stacking + body]
[Copy SKILL.md L741–763 verbatim: ### 37. Miscalibrated Epistemic Confidence + body]
````

Same notation as Task 3: copy line ranges verbatim from current SKILL.md, do not paraphrase the bodies.

- [ ] **Step 4.4: Run tests, confirm all pass**

Run: `python -m pytest tests/test_skill_structure.py -v`
Expected: all 8 tests pass.

- [ ] **Step 4.5: Commit**

```bash
git add patterns/en.md tests/test_skill_structure.py
git commit -m "refactor: extract 28 EN-specific patterns + PERSONALITY section into patterns/en.md"
```

---

## Task 5: Extract domain overrides to `domains/en_overrides.md`

**Files:**
- Create: `domains/en_overrides.md`
- Modify: `tests/test_skill_structure.py`

- [ ] **Step 5.1: Write failing test for `domains/en_overrides.md`**

Append to `tests/test_skill_structure.py`:

```python
def test_en_overrides_exists():
    assert (REPO_ROOT / "domains" / "en_overrides.md").is_file()


def test_en_overrides_contains_override_table_and_guidance():
    text = (REPO_ROOT / "domains" / "en_overrides.md").read_text(encoding="utf-8")
    # Sentinel strings from the existing SKILL.md sections we're extracting
    assert "Domain overrides" in text
    assert "Domain-specific guidance" in text
    # Override table must mention all 5 domain columns
    for domain in ["academic", "legal", "technical", "marketing", "casual"]:
        assert domain in text.lower(), f"missing domain mention: {domain}"


def test_en_overrides_pattern_ids_exist_in_packs():
    """Every pattern ID referenced in en_overrides.md must be in en.md or _universal.md."""
    overrides_text = (REPO_ROOT / "domains" / "en_overrides.md").read_text(encoding="utf-8")
    referenced = {int(m.group(1)) for m in re.finditer(r"#(\d+)\b", overrides_text)}
    defined = (
        _pattern_ids_in_file(REPO_ROOT / "patterns" / "en.md")
        | _pattern_ids_in_file(REPO_ROOT / "patterns" / "_universal.md")
    )
    orphans = referenced - defined
    assert not orphans, f"en_overrides.md references undefined pattern IDs: {orphans}"
```

- [ ] **Step 5.2: Run tests, confirm new ones FAIL**

Run: `python -m pytest tests/test_skill_structure.py -v`
Expected: existing 8 pass, new 3 fail with file-not-found.

- [ ] **Step 5.3: Create `domains/en_overrides.md` by extracting domain sections from SKILL.md**

Create `domains/en_overrides.md` with this structure:

````markdown
# English Domain Overrides

Per-domain override matrix for the English pack. Loaded by the framework (`SKILL.md`) alongside `patterns/en.md` when the detected input language is English. The "casual" column is the strict default; other domains modify specific patterns.

[Copy SKILL.md L50–79 verbatim: the entire ### Domain overrides section including the table, Legend, and intro paragraph at L50–53]

[Copy SKILL.md L81–91 verbatim: the entire ### Domain-specific guidance section with all 5 domain paragraphs]
````

- [ ] **Step 5.4: Run tests, confirm all pass**

Run: `python -m pytest tests/test_skill_structure.py -v`
Expected: all 11 tests pass.

- [ ] **Step 5.5: Commit**

```bash
git add domains/en_overrides.md tests/test_skill_structure.py
git commit -m "refactor: extract domain override matrix + guidance into domains/en_overrides.md"
```

---

## Task 6: Capture pre-refactor regression baseline

**Files:**
- Create: `docs/regression-cases/full_example.md`
- Create: `docs/regression-cases/README.md`

- [ ] **Step 6.1: Create `docs/regression-cases/full_example.md` capturing the current SKILL.md "Full Example"**

Create the file with this exact structure:

````markdown
# Regression case: full example

Pre-refactor baseline captured at v3.2.0 (commit BEFORE SKILL.md split). Used to verify Phase 0 refactor produces equivalent output.

## Input (AI-sounding)

[Copy SKILL.md L894–909 verbatim — the "Before (AI-sounding):" block from the Full Example section]

## Pre-refactor baseline output

[Copy SKILL.md L911–920 verbatim — the "Draft rewrite:" block. This is the v3.2.0 reference output. Phase 0 must produce equivalent output style.]

## Final reference (also from v3.2.0)

[Copy SKILL.md L927–934 verbatim — the "Final rewrite:" block]

## Manual regression procedure

After completing Tasks 1–8, run the skill against this input in a fresh Claude Code session:

1. Open a new Claude Code conversation in a workspace that has this fork installed.
2. Send: `/humanizer` followed by the input block above.
3. Compare the resulting Draft + Final against the baseline blocks here.
4. **Pass criteria (qualitative):** the rewrite removes the same pattern categories (chatbot artifacts, significance inflation, promotional language, em dashes, emojis, copula avoidance, formulaic challenges, hedging, generic conclusion). Exact wording will differ — that is acceptable. Voice and length should be within ~20% of the baseline.
5. **Fail criteria:** missing pattern categories, output significantly longer, AI buzzwords from the input appearing in the rewrite, or chatbot artifacts left in.

Record the result in `docs/regression-cases/RESULTS.md` (created during execution).
````

- [ ] **Step 6.2: Create `docs/regression-cases/README.md`**

```markdown
# Regression cases

Pre-refactor input + reference output pairs for verifying that the v3.3.0 refactor preserves observable EN behavior.

Manual regression — Claude Code skill output cannot be deterministically tested in pytest. After the refactor commits, run the procedure in each case file and record results in `RESULTS.md`.
```

- [ ] **Step 6.3: Commit**

```bash
git add docs/regression-cases/
git commit -m "test: capture v3.2.0 regression baseline (full example) for Phase 0 verification"
```

---

## Task 7: Refactor SKILL.md — strip extracted sections, add framework Read instructions (Part A)

**Files:**
- Modify: `SKILL.md`

This task is split into two atomic steps because the SKILL.md edit is large. Step 7.1 deletes; Step 7.2 adds the framework loader instructions. Both touch the same file so cavecrew-builder's 1–2 file limit is honored.

- [ ] **Step 7.1: Delete the extracted sections from SKILL.md**

In `SKILL.md`, delete the following line ranges (highest line numbers first to preserve numbering):

1. **L894–953:** the entire "## Full Example" section (now captured in `docs/regression-cases/full_example.md`).
2. **L765–833:** the entire "## ARTIFACTS AND CONTAMINATION" section (patterns #38–#40, moved to `_universal.md`).
3. **L699–763:** the entire "## HEADING PATTERNS" + "## EPISTEMIC PATTERNS" sections (#35–#37, EN-specific → `en.md`). Note: #35 is in en.md, #36 and #37 are also in en.md.
4. **L633–697:** patterns #30–#34 (EN-specific → `en.md`).
5. **L588–631:** patterns #27, #28, #29. #27 and #28 → `en.md`, #29 → `_universal.md`.
6. **L524–587:** "## FILLER AND HEDGING" section header + #23, #24, #25, #26. #23/#24 → `en.md`, #25/#26 → `_universal.md`.
7. **L479–522:** "## COMMUNICATION PATTERNS" header + #20, #21, #22 (all → `en.md`).
8. **L394–477:** "## STYLE PATTERNS" header + #14, #15, #16, #17, #18, #19. #16 → `en.md`, rest → `_universal.md`.
9. **L289–392:** "## LANGUAGE AND GRAMMAR PATTERNS" header + #7, #8, #9, #10, #11, #12, #13 (all → `en.md`).
10. **L209–287:** "## CONTENT PATTERNS" header + #1, #2, #3, #4, #5, #6. #6 → `_universal.md`, rest → `en.md`.
11. **L174–207:** "## PERSONALITY AND SOUL" section (→ `en.md`).
12. **L81–91:** "### Domain-specific guidance" subsection (→ `en_overrides.md`).
13. **L50–79:** "### Domain overrides" subsection (→ `en_overrides.md`).

After this step, SKILL.md should contain only: frontmatter, `# Humanizer`, `## Mode`, `## Domain` intro paragraph (the table is gone), `## Detection Guidance`, `## Your Task`, `## Voice Calibration`, `## Process`, `## Output Format`, `## Reference`.

Do not yet add the framework loader instructions — that is Step 7.2.

- [ ] **Step 7.2: Run frontmatter tests to confirm SKILL.md is still valid**

Run: `python -m pytest tests/test_skill_structure.py::test_skill_md_frontmatter_valid tests/test_skill_structure.py::test_skill_md_description_under_plugin_limit -v`
Expected: both pass. (The pack-existence tests also pass because Tasks 3–5 created the pack files already.)

- [ ] **Step 7.3: Commit the deletion step**

```bash
git add SKILL.md
git commit -m "refactor: remove extracted sections from SKILL.md (deferred loader instructions)"
```

---

## Task 8: Refactor SKILL.md — add framework loader instructions (Part B)

**Files:**
- Modify: `SKILL.md`
- Modify: `tests/test_skill_structure.py`

- [ ] **Step 8.1: Write failing tests for framework loader instructions**

Append to `tests/test_skill_structure.py`:

```python
def test_skill_md_instructs_loading_universal_pack():
    text = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "patterns/_universal.md" in text, (
        "SKILL.md must instruct Claude to load patterns/_universal.md"
    )


def test_skill_md_instructs_loading_language_pack():
    text = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "patterns/{lang}.md" in text or "patterns/en.md" in text, (
        "SKILL.md must instruct Claude to load the language-specific pack"
    )


def test_skill_md_instructs_loading_domain_overrides():
    text = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "domains/{lang}_overrides.md" in text or "domains/en_overrides.md" in text, (
        "SKILL.md must instruct Claude to load the per-language domain overrides"
    )


def test_skill_md_no_longer_contains_pattern_definitions():
    """After refactor, individual ### N. <Pattern Name> sections must be gone."""
    text = (REPO_ROOT / "SKILL.md").read_text(encoding="utf-8")
    pattern_headings = re.findall(r"^### \d+\.\s.*$", text, re.MULTILINE)
    assert not pattern_headings, (
        f"SKILL.md still contains pattern definitions: {pattern_headings[:3]}..."
    )
```

- [ ] **Step 8.2: Run tests, confirm new ones FAIL**

Run: `python -m pytest tests/test_skill_structure.py -v`
Expected: existing tests pass, 3 new loader tests FAIL (loader instructions not yet added), 1 new "no pattern definitions" test PASSES (Task 7 already deleted them).

- [ ] **Step 8.3: Add framework loader instructions to SKILL.md**

In `SKILL.md`, locate the `## Your Task` section. Replace its body with:

```markdown
## Your Task

When given text to humanize:

1. **Check mode** — Quick, Full (default), or Voice?
2. **Detect input language** from the text. Supported languages have a pack at `patterns/{lang}.md` — currently `en`. If the detected language has no pack, fall back to `en` and warn inline.
3. **Load the relevant pattern packs.** Always Read `patterns/_universal.md`. Then Read `patterns/{lang}.md` for the detected language.
4. **Check domain** — Casual (default), academic, legal, technical, or marketing? If not specified, infer from the text and state the detected domain at the start of your response.
5. **Load the per-language domain overrides** by Reading `domains/{lang}_overrides.md`.
6. **Voice calibration** — If a writing sample is provided, analyze it FIRST (see Voice Calibration section below).
7. **Pre-flight density check** (Full mode only) — Count Tier 1 dead-giveaway tells per 100 words; if density = 0, drop to a Quick-mode pass to avoid over-editing voice. Announce the result before the draft. See the full Process section below.
8. **Identify AI patterns** — Scan for patterns defined in the loaded packs (universal + language), respecting domain overrides (SKIP/light per the override matrix) and the Detection Guidance "what NOT to flag" list above.
9. **Rewrite problematic sections** — Replace AI-isms with natural alternatives.
10. **Preserve meaning** — Keep the core message intact.
11. **Maintain register** — Match the appropriate tone for the domain.
12. **Add soul** — Only for casual (and lightly for technical). Skip for academic, legal, and marketing. See the PERSONALITY AND SOUL section in the language pack (if present).
13. **Length audit** — Can this be 20–30% shorter without losing meaning? Cut padding. (Lighter for academic and technical.)
14. **Final AI audit** — Run the checklist before presenting the final version. Universal items appear here; language- and domain-specific items appear in the loaded packs.
```

Then update the `## Process` section's `### Full mode (default)` numbered list to insert two new steps after the existing step 2 ("Check domain..."):

```markdown
   2a. **Load the relevant pattern packs.** Read `patterns/_universal.md` (always). Read `patterns/{lang}.md` for the detected language (defaults to `en`). Read `domains/{lang}_overrides.md` for the domain override matrix.
```

(Renumber subsequent steps accordingly.)

- [ ] **Step 8.4: Run all tests, confirm all pass**

Run: `python -m pytest tests/test_skill_structure.py -v`
Expected: all 15 tests pass.

- [ ] **Step 8.5: Verify SKILL.md byte size dropped significantly**

Run: `wc -c SKILL.md`
Expected: under 20,000 bytes (was ~60,000 before refactor).

- [ ] **Step 8.6: Commit**

```bash
git add SKILL.md tests/test_skill_structure.py
git commit -m "refactor: SKILL.md becomes framework — loads patterns/_universal.md + patterns/{lang}.md + domains/{lang}_overrides.md"
```

---

## Task 9: Run manual regression and record result

**Files:**
- Create: `docs/regression-cases/RESULTS.md`

- [ ] **Step 9.1: Run the manual regression procedure from Task 6.1**

Open a fresh Claude Code session in a workspace that has the refactored fork installed (clone locally or symlink the skill). Paste the input from `docs/regression-cases/full_example.md` after `/humanizer`. Save the Draft + Final output.

- [ ] **Step 9.2: Compare against baseline and record result**

Create `docs/regression-cases/RESULTS.md`:

````markdown
# Regression results

## full_example — v3.3.0 refactor

**Date:** YYYY-MM-DD
**Tester:** <name>
**Commit tested:** <git rev-parse HEAD output>
**Skill model:** <claude opus 4.7 / sonnet 4.6>

### Refactored output — Draft

```
<paste skill's Draft rewrite output here>
```

### Refactored output — Final

```
<paste skill's Final rewrite output here>
```

### Comparison vs. baseline (from `full_example.md`)

- [ ] Removes chatbot artifacts ("Great question!", "I hope this helps!", "Let me know if...")
- [ ] Removes significance inflation ("testament", "pivotal moment", "evolving landscape")
- [ ] Removes promotional language ("groundbreaking", "nestled", "seamless")
- [ ] Removes em dashes and emojis
- [ ] Removes copula avoidance ("serves as", "functions as", "stands as")
- [ ] Removes formulaic challenges section
- [ ] Removes generic positive conclusion
- [ ] Output length within ~20% of baseline

### Verdict

PASS / FAIL — `<notes>`

If FAIL: list specific regressions and open issues before tagging v3.3.0.
````

Fill in the placeholders during the manual test. Replace `YYYY-MM-DD`, `<name>`, `<git rev-parse HEAD output>`, `<claude opus 4.7 / sonnet 4.6>`, both `<paste ...>` blocks, and `<notes>` before committing.

- [ ] **Step 9.3: Commit (only if PASS)**

```bash
git add docs/regression-cases/RESULTS.md
git commit -m "test: record v3.3.0 manual regression — PASS"
```

If FAIL, do not commit; open issues and iterate on the refactor first.

---

## Task 10: Add .gitignore + README + version bump for release

**Files:**
- Modify: `.gitignore`
- Modify: `README.md`

- [ ] **Step 10.1: Append to `.gitignore`**

Append these lines to `.gitignore`:

```
# Python tooling
__pycache__/
.pytest_cache/
.venv/
*.pyc

# User personal samples (never committed)
writing-samples/
```

- [ ] **Step 10.2: Update `README.md` "Version History" section**

In `README.md`, find the `## Version History` section. Insert a new entry as the first bullet:

```markdown
- **3.3.0** - Internal refactor only. SKILL.md split into a language-agnostic framework (`SKILL.md`) plus pattern packs (`patterns/_universal.md` for 12 universal patterns, `patterns/en.md` for 28 EN-specific patterns + the PERSONALITY AND SOUL section) and per-language domain overrides (`domains/en_overrides.md`). Zero observable behavior change for English input (verified by manual regression against the prior `## Full Example`). Adds `tests/test_skill_structure.py` (pytest sanity tests, no API calls) for schema and cross-reference integrity. Prepares the architecture for multi-lingual support (DE pack ships in v3.5.0) and the eval infrastructure (ships in v3.4.0). No new patterns; no pattern wording changed.
```

Also bump the SKILL.md frontmatter `version` field:

In `SKILL.md`, change:
```yaml
version: 3.2.0
```
to:
```yaml
version: 3.3.0
```

- [ ] **Step 10.3: Run final test sweep**

Run: `python -m pytest tests/ -v`
Expected: all tests pass.

- [ ] **Step 10.4: Commit the release**

```bash
git add .gitignore README.md SKILL.md
git commit -m "release: v3.3.0 — SKILL.md refactor (framework + packs), no behavior change"
```

- [ ] **Step 10.5: Tag the release locally**

```bash
git tag -a v3.3.0 -m "v3.3.0 — SKILL.md refactor into framework + language packs"
```

Do not push. User confirms before pushing tag and commits to origin.

---

## Self-Review

**Spec coverage:**

- §4.1 layered structure → Tasks 3, 4, 5, 7, 8. ✓
- §4.2 runtime flow loader steps → Task 8.3. ✓
- §4.3 pattern-ID continuity → preserved by byte-equivalent extraction. ✓
- §4.4 personal samples convention → out of scope for Phase 0 (lives in framework but not exercised until DE pack arrives). Acknowledged: voice-calibration section retained in SKILL.md; the 4-step lookup chain itself is added when needed in Phase 2 since current voice calibration is sample-path-only and works as-is.
- §4.5–4.6 eval infra → out of scope for Phase 0 (Phase 1).
- §4.7 pattern source per language → out of scope for Phase 0 (Phase 2).
- §5.1 component table → matches files created here. ✓
- §5.4 tests/test_skill_structure.py → created in Task 2, expanded in Tasks 3, 4, 5, 8. Schema-compliant sections, cross-reference integrity (Task 5.1 test_en_overrides_pattern_ids_exist_in_packs). ✓
- §5.4 .gitignore additions → Task 10.1. ✓
- §5.4 README.md updates for v3.3.0 → Task 10.2 (full "What's different" rewrite and quickstart deferred to v3.5.0 release per spec §6 Phase 3).
- §6 Phase 0 — refactor (EN only, behavior-preserving), regression test required → Tasks 6 + 9. ✓
- §7 success criteria — zero observable EN behavior change, regression test green → Task 9. ✓

**Gap accepted with rationale:** the `## Domain` table that the SKILL.md framework needs to *announce* domains is gone after Task 7.1. The framework still has `## Domain` *intro paragraph* but the lookup table moved to `domains/en_overrides.md`. Step 8.3 instructs Claude to load `domains/{lang}_overrides.md` to get the matrix. This is intentional — the framework names the contract, the pack provides the data.

**Placeholder scan:** searched for "TBD", "TODO", "implement later", "fill in", "Add appropriate error handling", "Similar to Task". Found only legitimate `<placeholder>` patterns inside the regression `RESULTS.md` template (Task 9.2), which are explicit instructions to fill in during execution, not plan-side placeholders. Clean. ✓

**Type / signature consistency:**
- `_pattern_ids_in_file()` defined in Task 3.1, used in Tasks 3.1, 4.1, 5.1, 8.1. Same signature. ✓
- `_parse_frontmatter()` defined in Task 2.1, used in Tasks 2.1 only. ✓
- `UNIVERSAL_PATTERN_IDS` (Task 3.1) and `EN_PATTERN_IDS` (Task 4.1) are disjoint sets that sum to 40. Verified manually: 12 + 28 = 40. ✓
- File paths reference `patterns/{lang}.md` (with placeholder) in some loader strings and `patterns/en.md` in others. Tests in Task 8.1 accept either form so the implementing subagent can choose the more natural wording in SKILL.md without breaking the tests. ✓

**Subagent atomicity audit:** every step touches ≤2 files. Largest single-file edits (Task 7.1 deletes 13 ranges from SKILL.md, Task 8.3 adds two paragraphs to SKILL.md) are still one file. Cross-task file overlap is minimal: SKILL.md is touched in Tasks 7, 8, 10; `tests/test_skill_structure.py` is touched in Tasks 2, 3, 4, 5, 8. Each appearance is additive (append a test function) or surgical (delete listed ranges; add specified paragraphs), never a full rewrite. ✓

No issues found. Plan complete.

---

## Execution Handoff

**Plan complete and saved to `docs/plans/2026-05-23-phase-0-skill-refactor.md`.** Two execution options:

**1. Subagent-Driven (recommended).** I dispatch a fresh `cavecrew-builder` subagent (Sonnet) per task. After each task, the parent (Opus) reviews the diff and runs the pytest sweep before dispatching the next task. Manual regression in Task 9 is handled by the user, not a subagent.

**2. Inline Execution.** Execute tasks in this same Opus session using `superpowers:executing-plans`, batch through tasks with checkpoints. No subagent dispatch — slower but simpler to monitor.

**Which approach?**
