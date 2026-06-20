# v3.6.0 — #42 Aphorism Formulas + #34 staccato extension — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add #42 Aphorism Formulas as a new pattern (41→42) and extend #34 with a mid-text staccato-run sub-tell (lock-free), in EN+DE, validated by a zero-API regex gate + a quota Gate-2 re-baseline.

**Architecture:** Part 1 (#34) edits the existing `### 34.` pack bodies + adds positive/negative Gate-2 corpus cases — no regex key, no lock touched. Part 2 (#42) adds a high-precision `aphorism_formula` regex (2 literal anchors only; recall lives in the Gate-2 full-pass removal check), a new `### 42.` pack section + `pattern_042.json` corpus, and the count/lock edits in one atomic lockstep task. A final quota task runs `--force --runs 5` EN+DE, compares like-for-like to the named baselines, and refreshes both `summary_latest_*` files behind a new gate-test.

**Tech Stack:** Python 3.11, pytest, `re`. Markdown packs. `claude -p` (subscription) for the Gate-2 runs. No new deps.

## Global Constraints

- **Version:** bump `3.5.3 → 3.6.0` (minor — one new pattern). Sites: `SKILL.md:3`, `.claude-plugin/plugin.json:3`, `README.md:3` badge, `README.md:11` table header, + a `## Version History` `3.6.0` entry. Do NOT edit historical 3.5.x version-history entries.
- **Count 41 → 42** (one new pattern). Count sites: `SKILL.md:10/:38/:154`; `README.md:7` ("12 new patterns (41 total)"), `:110`, `:139`, `:212` (heading "## 41 Patterns Detected"), `:214` (the structural sentence). `plugin.json:4` desc, `marketplace.json:11` desc. **Re-verify each at impl time** (`grep -n "41 pattern\|41 total\|41 Patterns\|37 shared"`).
- **"37 shared" is incoherent** — `README.md:214` says "13 universal + 28 English-specific = 41" then "translates all 37 shared." Verified composition: `_universal.md`=13, `en.md`=28 (→29 after #42), `de.md`=28 EN-parallel (→29) + 5 DE-only. Rewrite `:214` to a coherent statement (see Task 3 Step). Do NOT blind-bump 37→38.
- **Three exact-equality locks #42 breaks (edit in the SAME task as the pattern add — Task 3):** `EN_PATTERN_IDS` (`tests/test_skill_structure.py:57`), `DE_PATTERN_IDS` (`:143`), TN-integrity (`tests/test_corpus_true_negative_integrity.py:44`, `tn == {"pattern_019_en_001"}`). **Do NOT touch `UNIVERSAL_PATTERN_IDS`** (#42 goes in the packs, not `_universal.md`).
- **#42 EN regex anchors = 2 literal phrases only:** `is not a tool but a mirror`, `becomes a trap`. DE: `ist kein Werkzeug, sondern ein Spiegel`, `wird zur Falle`. **`the language of` / `the currency of` and the bare `X is the Y of Z` are SOFT tells — NOT regex triggers** (they over-fire on legit idiom). Recall for non-anchor aphorisms rests on the Gate-2 removal check, not the regex.
- **#42 ↔ #9 routing rule** (state in both #42 pack sections): the negation-frame anchor ("not a tool but a mirror" / "kein A sondern B") manufacturing a profundity maxim → #42 (replace with the concrete claim); a bare "not only…but" / "kein [Substantiv]" rhetorical dismissal → #9 (delete the frame).
- **Run tests from repo root:** `PYTHONPATH=. python3 -m pytest <path> -v`. **Never source `ANTHROPIC_API_KEY`** before any skill/eval call.
- **Standing rule:** subagent-driven TDD; every task diff Skeptic-reviewed from primary evidence (no self-review); **never commit or push without explicit user OK** — `git commit` steps are staged for the user's go.
- **Gate-2 baselines (like-for-like, sourced from the dated run JSONs):** all-or-nothing EN **0.938** (`pattern_en_20260612_113505.json`) / DE **0.907** (`pattern_de_20260614_153629.json`); per-term EN **0.971** / DE **0.95** (same runs). The `summary_latest_*` markdown files are stale (EN 0.905/0.619/0.5; DE 0.864/0.907) — things-to-refresh, NOT sources.
- **Hard-coded figures are PRIOR-baseline placeholders.** The literals `0.938 / 0.971 / 0.907 / 0.95` appear in ~5 sites (this list, Task 4 Steps 1-4 acceptance/marker/test). They are the *prior* baseline to compare against (Steps 1-2 acceptance "within noise") AND the *recorded* figure the marker-line/gate-test asserts. After the Gate-2 run, the recorded figures = the ACTUAL new run numbers; `grep -rn "0.938\|0.971\|0.907\|0.95" docs/plans/` is NOT how you reconcile — instead, in Task 4 Step 3/4 write the **actual** new-run figures into the marker line + the test constant (one source of truth: the new dated JSON). A missed site fails SAFE (red build / marker mismatch), never silently green.

---

### Task 1: #34 staccato-run extension (LOCK-FREE — pack bodies + Gate-2 corpus cases)

**Files:**
- Modify: `patterns/en.md:399` (#34 body), `patterns/de.md:757` (#34 body)
- Modify: `evals/corpus/en/patterns/pattern_034.json`, `evals/corpus/de/patterns/pattern_034.json`
- Test: `tests/test_skill_structure.py` (must stay green — no ID change)

**Interfaces:**
- Consumes: nothing.
- Produces: extended #34 prose (consumed by the skill at `claude -p` time) + new pattern_034 corpus cases (consumed by Task 4's Gate-2 run). Adds NO regex key, NO pattern ID.

- [ ] **Step 1: Extend the EN #34 body** — in `patterns/en.md`, **insert** immediately after the existing #34 `**After:**` block (the single-trailing-restate example) — this is a **mid-file insert before `## HEADING PATTERNS` (~line 410), NOT an EOF append**:

```
**Extension — mid-text dramatic staccato runs:** beyond the single trailing restate above, a *run of ≥3 short declarative sentences mid-paragraph* that manufacture drama is the same tell at higher volume. Fix: restructure the run into flowing prose (merge), don't merely clip.

**Before (mid-text run; continuing prose follows):**
> The model shipped on Tuesday. It changed everything. The whole field shifted. The team knew it. Within a month three competitors had rebuilt their pipelines around the same idea.

**After:**
> The model shipped on Tuesday and reshaped the field; within a month three competitors had rebuilt their pipelines around the same idea.

**One-passage-one-pattern rule:** a *single* trailing restate at a paragraph end → #34 (above). A run of *negation* fragments ("No map. No guide. No second chance.") → **#9** (it owns tailing negations) — not here. A run of *≥3 affirmative* short declaratives building drama → this extension.
```

- [ ] **Step 2: Extend the DE #34 body** — in `patterns/de.md`, **insert** after the existing #34 examples and just before/merging the "Weniger verbreitet im Deutschen…" domain note (de.md:787-790) — mid-file, NOT EOF:

```
**Erweiterung — dramatisierende Kurzsatz-Ketten mitten im Text:** über den einzelnen angehängten Betonungssatz hinaus ist eine *Kette von ≥3 kurzen Aussagesätzen mitten im Absatz*, die Dramatik erzeugt, dasselbe Tell in stärkerer Form. Fix: die Kette in fließende Prosa umbauen (zusammenführen), nicht nur kürzen.

**Vorher (Kette mitten im Absatz, danach folgt weiterer Text):**
> Das Modell kam am Dienstag. Es veränderte alles. Das ganze Feld verschob sich. Das Team wusste es. Innerhalb eines Monats hatten drei Wettbewerber ihre Abläufe darauf umgestellt.

**Nachher:**
> Das Modell kam am Dienstag und veränderte das Feld; innerhalb eines Monats stellten drei Wettbewerber ihre Abläufe darauf um.

**Eine-Passage-ein-Muster-Regel:** ein *einzelner* angehängter Betonungssatz am Absatzende → #34 (oben). Eine Kette aus *Verneinungs*-Fragmenten ("Kein X. Kein Y. Keine Z.") → **#9** (angehängte Verneinungen) — nicht hier. Eine Kette aus *≥3 affirmativen* kurzen Aussagesätzen → diese Erweiterung. (Die bestehende Notiz "weniger verbreitet im Deutschen … nur bei besonders auffälligen Fällen flaggen" gilt fort: die ≥3-Kette IST genau so ein auffälliger Fall.)
```

- [ ] **Step 3: Add the EN staccato POSITIVE case ONLY** — append to `cases` in `evals/corpus/en/patterns/pattern_034.json` (next-free EN id = `_en_002`; verify with `grep '"id"' evals/corpus/en/patterns/pattern_034.json` — only `_en_001` should exist; STOP-AND-REPORT if `_en_002` already exists):

```json
    {
      "id": "pattern_034_en_002",
      "input": "The model shipped on Tuesday. It changed everything. The whole field shifted. The team knew it. Within a month three competitors had rebuilt their pipelines around the same idea.",
      "expected_changes": ["It changed everything.", "The whole field shifted.", "The team knew it."],
      "expected_unchanged": [],
      "domain": "casual",
      "source": "upstream_v2.8.0_port_staccato_positive"
    }
```
**Do NOT add the EN staccato *negative* survive-case here.** It carries `true_negative: true`, which lands in the EN TN set locked by `test_corpus_true_negative_integrity.py:44` — so it MUST be added in **Task 3 Step 5**, in lockstep with widening that lock (adding it here would red the build). (The DE negative case below is safe — there is no DE TN lock.)

- [ ] **Step 4: Add the positive + negative Gate-2 cases (DE)** — append to `evals/corpus/de/patterns/pattern_034.json` `cases` (next-free DE id = `_de_004`; DE has NO TN lock, so the negative case is safe here):

```json
    {
      "id": "pattern_034_de_004",
      "input": "Das Modell kam am Dienstag. Es veränderte alles. Das ganze Feld verschob sich. Das Team wusste es. Innerhalb eines Monats hatten drei Wettbewerber ihre Abläufe darauf umgestellt.",
      "expected_changes": ["Es veränderte alles.", "Das ganze Feld verschob sich.", "Das Team wusste es."],
      "expected_unchanged": [],
      "domain": "casual",
      "source": "upstream_v2.8.0_port_staccato_positive"
    },
    {
      "id": "pattern_034_de_005",
      "input": "Der Build schlug fehl. Ich prüfte die Logs. Ein Test lief in einen Timeout. Ich behob es und pushte.",
      "expected_changes": [],
      "expected_unchanged": ["Der Build schlug fehl.", "Ich prüfte die Logs.", "Ein Test lief in einen Timeout."],
      "domain": "casual",
      "source": "staccato_negative_survive_case",
      "true_negative": true
    }
```

- [ ] **Step 5: Run the full suite + corpus-load smoke**

Run: `PYTHONPATH=. python3 -m pytest tests/ -q`
Expected: all pass (no `### N.` heading added → `EN/DE_PATTERN_IDS` unchanged; the DE `_de_005` true_negative is fine — only the EN TN set is locked, and no EN true_negative was added in this task).
Run: `PYTHONPATH=. python3 -c "from pathlib import Path; from evals.scripts._shared import load_pattern_corpus; en=load_pattern_corpus(Path('evals/corpus/en/patterns')); de=load_pattern_corpus(Path('evals/corpus/de/patterns')); print(sum(1 for c in en if c.id=='pattern_034_en_002'), sum(1 for c in de if c.id in ('pattern_034_de_004','pattern_034_de_005')))"`
Expected: prints `1 2`.

- [ ] **Step 6: Stage commit (await user OK)**

```bash
git add patterns/en.md patterns/de.md evals/corpus/en/patterns/pattern_034.json evals/corpus/de/patterns/pattern_034.json
git commit -m "feat(skill): extend #34 with mid-text staccato-run sub-tell (EN+DE, lock-free)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: #42 regex keys + Gate-1 tests (LOCK-FREE — zero-API)

**Files:**
- Modify: `evals/scripts/regex_scorer.py` (`PATTERNS_EN` dict ~`:53`, `PATTERNS_DE` dict ~`:273`)
- Test: `tests/test_regex_scorer.py`

**Interfaces:**
- Consumes: `scan(text, lang) -> dict[str,int]`, `PATTERNS_EN`, `PATTERNS_DE`, `UNIVERSAL_MECHANICS_KEYS` from `evals.scripts.regex_scorer`.
- Produces: `PATTERNS_EN["aphorism_formula"]`, `PATTERNS_DE["de_aphorism_formula"]` — `(compiled_regex, label)` tuples surfaced as counts in `scan(...)`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_regex_scorer.py`)

```python
def test_aphorism_formula_fires_en():
    assert scan("Leadership is not a tool but a mirror of the team.", lang="en")["aphorism_formula"] >= 1
    assert scan("Efficiency becomes a trap when teams forget the human layer.", lang="en")["aphorism_formula"] >= 1

def test_aphorism_formula_silent_on_copula_and_soft_tells_en():
    # adversarial copula facts — must NOT fire (share no anchor substring)
    assert scan("Tuesday is the busiest day of the week.", lang="en")["aphorism_formula"] == 0
    assert scan("The CEO is the head of the company.", lang="en")["aphorism_formula"] == 0
    assert scan("Water is the main component of the body.", lang="en")["aphorism_formula"] == 0
    # SOFT tells (language/currency of) are NOT regex triggers — must stay silent
    assert scan("Diplomacy has a language of its own.", lang="en")["aphorism_formula"] == 0
    assert scan("The euro is the currency of nineteen countries.", lang="en")["aphorism_formula"] == 0

def test_de_aphorism_formula_fires():
    assert scan("Führung ist kein Werkzeug, sondern ein Spiegel des Teams.", lang="de")["de_aphorism_formula"] >= 1
    assert scan("Effizienz wird zur Falle, wenn Teams den Menschen vergessen.", lang="de")["de_aphorism_formula"] >= 1

def test_de_aphorism_formula_silent_on_fachsprache():
    assert scan("Die Sprache der Diplomatie ist subtil.", lang="de")["de_aphorism_formula"] == 0
    assert scan("Aufmerksamkeit ist die Währung der sozialen Medien.", lang="de")["de_aphorism_formula"] == 0

def test_de_aphorism_dont_break_clean_prose():
    text = ("Ich verbrachte den Morgen damit, mein Fahrrad zu reparieren. "
            "Die Kette war gerissen, was mich eine Stunde kostete.")
    assert scan(text, lang="de")["de_aphorism_formula"] == 0
```

- [ ] **Step 2: Run to verify FAIL** — `PYTHONPATH=. python3 -m pytest tests/test_regex_scorer.py -k aphorism -v` → FAIL (KeyError: 'aphorism_formula' / 'de_aphorism_formula').

- [ ] **Step 3: Add the keys** — in `evals/scripts/regex_scorer.py`, inside `PATTERNS_EN = { ... }` (place after `sycophantic_opener`, ~`:118`):

```python
    "aphorism_formula": (
        re.compile(
            r"\b(is not a tool but a mirror|becomes a trap)\b",
            re.I,
        ),
        "manufactured-maxim aphorism (distinctive anchor)",
    ),
```
and inside `PATTERNS_DE = { ... }` (~`:273`):
```python
    "de_aphorism_formula": (
        re.compile(
            r"(ist kein Werkzeug,? sondern ein Spiegel|wird zur Falle)",
            re.I,
        ),
        "manufactured-maxim aphorism (DE distinctive anchor)",
    ),
```

- [ ] **Step 4: Run to verify PASS** — `PYTHONPATH=. python3 -m pytest tests/test_regex_scorer.py -k "aphorism or de_clean_prose" -v` → PASS (6 tests incl. the existing DE clean-prose guard, which still sums to zero with the new key).

- [ ] **Step 5: Full suite** — `PYTHONPATH=. python3 -m pytest tests/ -q` → all pass (adding a scorer key is lock-free: keys are tell-name-keyed, no pattern-ID/count change; `test_threshold_patterns_reference_real_patterns` is a subset check and is not tripped).

- [ ] **Step 6: Stage commit (await user OK)**

```bash
git add evals/scripts/regex_scorer.py tests/test_regex_scorer.py
git commit -m "feat(skill): #42 aphorism_formula regex keys (EN+DE, hard anchors only)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: #42 pattern sections + corpus + the 3 lock edits + counts + version (ATOMIC lockstep)

**Files:**
- Modify: `patterns/en.md` (new `### 42.` section), `patterns/de.md` (new `### 42.` section)
- Create: `evals/corpus/en/patterns/pattern_042.json`, `evals/corpus/de/patterns/pattern_042.json`
- Modify: `tests/test_skill_structure.py:57` (`EN_PATTERN_IDS`), `:143` (`DE_PATTERN_IDS`)
- Modify: `tests/test_corpus_true_negative_integrity.py:44`
- Modify: `evals/corpus/en/patterns/pattern_034.json` (the EN staccato NEGATIVE case deferred from Task 1)
- Modify: `SKILL.md`, `README.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` (counts + version)

**Interfaces:**
- Consumes: `aphorism_formula`/`de_aphorism_formula` keys (Task 2).
- Produces: pattern `#42` in both packs (count 42); `pattern_042.json` corpus; the EN TN set now `{pattern_019_en_001, pattern_042_en_00N…, pattern_034_en_003}`.

- [ ] **Step 1: Write the #42 EN pack section** — append to `patterns/en.md` (after the last EN-pack section; #42 is a new `### 42.` heading):

```
### 42. Aphorism Formulas

**Problem:** An ordinary claim is recast as a reusable-sounding maxim — gravitas, not precision. Replace the formula with the concrete claim it gestures at.

**Hard tells (distinctive):** "X is not a tool but a mirror", "X becomes a trap".
**Soft tells (flag in prose, but they are NOT mechanical triggers — they over-fire on legitimate idiom):** "the language of <abstract>", "the currency of <abstract>", and bare "X is the Y of Z". English uses these non-figuratively ("the language of diplomacy", "the currency of nineteen countries"), so judge by whether the phrase *manufactures a maxim* in place of a concrete claim. Also: "the architecture of" stays #35 (heading debunking-pose), not here.

**Before:**
> Trust is the currency of every healthy team.
**After:**
> Teams work better when members can rely on each other.

**Routing vs #9:** the hard anchor "X is not a tool but a mirror" is a "not X but Y" frame, which #9 also owns — but with a different fix. If the negation frame manufactures a profundity maxim (mirror / trap image) → #42 (replace with the concrete claim). If it is a bare "not only…but" dismissal of an unclaimed alternative → #9 (delete the frame).
```

- [ ] **Step 2: Write the #42 DE pack section** — append to `patterns/de.md` (new `### 42.`, BEFORE the #100-block DE-only patterns to keep ascending order, or after the last EN-parallel section — verify ordering with `grep -n '^### ' patterns/de.md`):

```
### 42. Aphorismus-Formeln

**Problem:** Eine gewöhnliche Aussage wird als wiederverwendbare Maxime verkleidet — Bedeutungsschwere statt Präzision. Durch die konkrete gemeinte Aussage ersetzen.

**Harte Tells (distinktiv):** "X ist kein Werkzeug, sondern ein Spiegel", "X wird zur Falle".
**Weiche Tells (in der Prosa benennen, aber KEINE mechanischen Trigger — sie überfeuern auf legitimem Fachsprache-Idiom):** die bare `die Sprache <Genitiv>` / `die Währung <Genitiv>` ("die Sprache der Diplomatie", "die Währung der Aufmerksamkeit") sind etablierte Fachsprache, kein Tell.

**Vorher:**
> Vertrauen ist die Währung jeder guten Zusammenarbeit.
**Nachher:**
> Zusammenarbeit funktioniert, wenn die Beteiligten einander vertrauen.

**Abgrenzung zu #9:** "X ist kein Werkzeug, sondern ein Spiegel" ist ein "kein A, sondern B"-Rahmen, den #9 ebenfalls besitzt — aber mit anderer Behebung. Erzeugt der Verneinungsrahmen eine Bedeutungsschwere-Maxime (Spiegel/Falle-Bild) → #42 (durch die konkrete Aussage ersetzen). Ist es eine bloße "nicht nur … sondern auch"-Abweisung → #9 (Rahmen streichen).
```

- [ ] **Step 3: Create `pattern_042.json` (EN)** — `evals/corpus/en/patterns/pattern_042.json` (file = `pattern_042.json`; lang/seq in the case id):

```json
{
  "pattern_id": 42,
  "pattern_name": "Aphorism Formulas",
  "lang": "en",
  "cases": [
    {
      "id": "pattern_042_en_001",
      "input": "Leadership is not a tool but a mirror of the team. Efficiency becomes a trap when leaders forget that.",
      "expected_changes": ["is not a tool but a mirror", "becomes a trap"],
      "expected_unchanged": [],
      "domain": "casual",
      "source": "anchor_tp"
    },
    {
      "id": "pattern_042_en_002",
      "input": "Symmetry is the language of trust, and consistency is the currency of good design.",
      "expected_changes": ["is the language of", "is the currency of"],
      "expected_unchanged": [],
      "domain": "casual",
      "source": "held_out_recall_removal_checkable"
    },
    {
      "id": "pattern_042_en_003",
      "input": "Every dashboard is a story waiting to be told about the data behind it.",
      "expected_changes": ["is a story waiting to be told"],
      "expected_unchanged": [],
      "domain": "casual",
      "source": "held_out_recall_removal_checkable"
    },
    {
      "id": "pattern_042_en_004",
      "input": "Tuesday is the busiest day of the week.",
      "expected_changes": [],
      "expected_unchanged": ["Tuesday is the busiest day of the week."],
      "domain": "casual",
      "source": "adversarial_copula_tn",
      "true_negative": true
    },
    {
      "id": "pattern_042_en_005",
      "input": "The CEO is the head of the company.",
      "expected_changes": [],
      "expected_unchanged": ["The CEO is the head of the company."],
      "domain": "casual",
      "source": "adversarial_copula_tn",
      "true_negative": true
    },
    {
      "id": "pattern_042_en_006",
      "input": "The euro is the currency of nineteen countries.",
      "expected_changes": [],
      "expected_unchanged": ["The euro is the currency of nineteen countries."],
      "domain": "casual",
      "source": "adversarial_genitive_idiom_tn",
      "true_negative": true
    }
  ]
}
```
(The held-out cases `_002`/`_003` use aphoristic wording NOT in the regex anchor — their `expected_changes` list the exact aphoristic surface tokens to delete, so the Gate-2 removal check is falsifiable. The regex is NOT expected to fire on them.)

- [ ] **Step 4: Create `pattern_042.json` (DE)** — `evals/corpus/de/patterns/pattern_042.json`:

```json
{
  "pattern_id": 42,
  "pattern_name": "Aphorismus-Formeln",
  "lang": "de",
  "cases": [
    {
      "id": "pattern_042_de_001",
      "input": "Führung ist kein Werkzeug, sondern ein Spiegel des Teams. Effizienz wird zur Falle, wenn man das vergisst.",
      "expected_changes": ["ist kein Werkzeug, sondern ein Spiegel", "wird zur Falle"],
      "expected_unchanged": [],
      "domain": "casual",
      "source": "anchor_tp"
    },
    {
      "id": "pattern_042_de_002",
      "input": "Vertrauen ist die Währung jeder guten Zusammenarbeit.",
      "expected_changes": ["ist die Währung"],
      "expected_unchanged": [],
      "domain": "casual",
      "source": "held_out_recall_removal_checkable"
    },
    {
      "id": "pattern_042_de_003",
      "input": "Die Sprache der Diplomatie ist subtil und oft missverstanden.",
      "expected_changes": [],
      "expected_unchanged": ["Die Sprache der Diplomatie"],
      "domain": "casual",
      "source": "adversarial_fachsprache_tn",
      "true_negative": true
    },
    {
      "id": "pattern_042_de_004",
      "input": "Aufmerksamkeit ist die Währung der sozialen Medien.",
      "expected_changes": [],
      "expected_unchanged": ["die Währung der sozialen Medien"],
      "domain": "casual",
      "source": "adversarial_fachsprache_tn",
      "true_negative": true
    }
  ]
}
```
(NOTE: DE has no TN-integrity lock, so the DE `true_negative` cases need no test edit.)

- [ ] **Step 5: Add the EN staccato NEGATIVE survive-case** (deferred from Task 1 because it carries `true_negative` and must land with the TN-lock widening) — append to `evals/corpus/en/patterns/pattern_034.json` `cases`:

```json
    {
      "id": "pattern_034_en_003",
      "input": "The build failed. I checked the logs. A test timed out. I fixed it and pushed.",
      "expected_changes": [],
      "expected_unchanged": ["The build failed.", "I checked the logs.", "A test timed out."],
      "domain": "casual",
      "source": "staccato_negative_survive_case",
      "true_negative": true
    }
```

- [ ] **Step 6: Update the frozen pattern-ID sets** — in `tests/test_skill_structure.py`, add `42` to `EN_PATTERN_IDS` (`:57`) and `DE_PATTERN_IDS` (`:143`). Do **NOT** touch `UNIVERSAL_PATTERN_IDS`.

- [ ] **Step 7: Widen the TN-integrity lock** — in `tests/test_corpus_true_negative_integrity.py:44`, change `assert tn == {"pattern_019_en_001"}` to the exact new EN true_negative set:

```python
    assert tn == {
        "pattern_019_en_001",
        "pattern_042_en_004", "pattern_042_en_005", "pattern_042_en_006",
        "pattern_034_en_003",
    }, f"unexpected true_negative set: {tn}"
```

- [ ] **Step 8: Bump counts 41→42 + re-derive "37 shared"** — edit the count sites (re-verify line numbers with `grep -n "41 pattern\|41 total\|41 Patterns\|37 shared"` first):
  - `SKILL.md:10` "Detects 41 patterns" → 42; `:38` "All 41 patterns" → 42; `:154` "the 41 patterns above" → 42.
  - `README.md:7` "(41 total)" → "(42 total)"; `:110` "All 41 patterns" → 42; `:139` "All 41 patterns strict" → 42; `:212` heading "## 41 Patterns Detected" → "## 42 Patterns Detected".
  - `README.md:214` — replace the incoherent sentence with: `The 42 patterns are drawn from 13 **universal** patterns (apply in any language; defined in `patterns/_universal.md`) and 29 **English-specific** patterns (defined in `patterns/en.md`). The German pack (`patterns/de.md`) re-expresses the 29 language-specific patterns in German and adds 5 DE-only extension patterns (`#100`–`#104`).`
  - `.claude-plugin/plugin.json:4` desc "41 patterns" → 42; `.claude-plugin/marketplace.json:11` desc "41 patterns" → 42.

- [ ] **Step 9: Bump version 3.5.3→3.6.0** — `SKILL.md:3` `version: 3.5.3` → `3.6.0`; `.claude-plugin/plugin.json:3` → `3.6.0`; `README.md:3` badge `version-3.5.3-blue` → `version-3.6.0-blue`; `README.md:11` header `v3.5.3` → `v3.6.0`; add a `## Version History` `3.6.0` entry above `- **3.5.3**`:

```
- **3.6.0** — Adds **#42 Aphorism Formulas** (manufactured-maxim tell: "X is not a tool but a mirror", "X becomes a trap"; "the language/currency of" kept as soft tells, not mechanical triggers, to avoid over-firing on legit idiom) and extends **#34** with a mid-text dramatic staccato-run sub-tell (≥3 short affirmative declaratives → merge into flowing prose). EN + DE. New deterministic `aphorism_formula`/`de_aphorism_formula` regex anchors (high-precision subset; recall via the Gate-2 full-pass removal check). #42↔#9 routing rule disambiguates the "not X but Y" frame. Count 41→42. Scope vetted by 3 Skeptic rounds + a 2nd MeetUp.
```

- [ ] **Step 10: Run the full suite + smoke**

Run: `PYTHONPATH=. python3 -m pytest tests/ -q`
Expected: all pass — `test_en_pack_contains_expected_patterns` / `test_de_pack_contains_expected_patterns` green with `42` in the sets; `test_corpus_true_negative_integrity` green with the widened set; no count/structure test red.
Run: `grep -rn "41 pattern\|41 total\|41 Patterns\|37 shared" SKILL.md README.md .claude-plugin/`
Expected: NO matches (all bumped/rewritten).

- [ ] **Step 11: Stage commit (await user OK)**

```bash
git add patterns/en.md patterns/de.md evals/corpus/en/patterns/pattern_042.json evals/corpus/de/patterns/pattern_042.json evals/corpus/en/patterns/pattern_034.json tests/test_skill_structure.py tests/test_corpus_true_negative_integrity.py SKILL.md README.md .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "feat(skill): #42 Aphorism Formulas (new pattern, 41->42) + lock/count/version (v3.6.0)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Gate-2 quota re-baseline + summary refresh + baseline gate-tests (QUOTA)

**Files:**
- Run: `evals/scripts/run_pattern_eval.py`
- Modify: `evals/reports/summary_latest_en.{md,json}`, `evals/reports/summary_latest_de.{md,json}`
- Create: `tests/test_baseline_summary.py`

**Interfaces:**
- Consumes: the shipped #42 + #34 (Tasks 1-3).
- Produces: refreshed `summary_latest_*` + two gate-tests.

- [ ] **Step 1: Run the EN re-baseline (quota; strip ANTHROPIC_API_KEY)**

Run: `PYTHONPATH=. python3 evals/scripts/run_pattern_eval.py --lang en --force --runs 5`
Expected: a dated `evals/reports/pattern_en_<ts>.json` with `overall_detection_rate` (all-or-nothing) + `per_term_removal_rate`. **Acceptance:** all-or-nothing within run-to-run noise of **0.938**, per-term of **0.971**; the new `pattern_042_en_001` (anchor) + `_002`/`_003` (held-out) are DETECTED (recall observable); the new #42 adversarial-copula cases are NOT marked detected (they are true_negative — scored by the FP path); `pattern_034_en_002` (staccato positive) detected, `_003` (negative) NOT merged. Resumable via per-case partials; chunk across quota windows if needed.

- [ ] **Step 2: Run the DE re-baseline (quota)**

Run: `PYTHONPATH=. python3 evals/scripts/run_pattern_eval.py --lang de --force --runs 5`
Expected: all-or-nothing within noise of **0.907**, per-term of **0.95**; `pattern_042_de_001` (anchor) + `_002` (held-out) detected; `_003`/`_004` (Fachsprache TN) not detected; `pattern_034_de_004` positive detected, `_de_005` negative not merged.

- [ ] **Step 3: Refresh BOTH summary files with a v3.6.0-DISTINGUISHING marker line** — overwrite the headline figures in `evals/reports/summary_latest_en.md` (currently stale 0.905/0.619/0.5) and `summary_latest_de.md` (currently stale 0.864/0.907) with the v3.6.0 figures from Steps 1-2. **Add to each a single unambiguous marker line that does NOT pre-exist in the stale file**, e.g. at the top:
  - EN: `**v3.6.0 baseline (run <ts>):** all-or-nothing 0.938 · per-term 0.971` (use the ACTUAL Step-1 figures)
  - DE: `**v3.6.0 baseline (run <ts>):** all-or-nothing 0.907 · per-term 0.95` (use the ACTUAL Step-2 figures)
  This matters because a bare float is a **wrong-reason green**: DE's committed all-or-nothing (0.907) ALREADY appears in the stale DE file, and EN's "0.9" prefix matches the stale "0.905" — so a `assert "0.907" in text` / `"0.9" in text` gate would pass even if the refresh were skipped. The gate (Step 4) asserts the full marker line, which is absent until the refresh lands.

- [ ] **Step 4: Write the baseline gate-tests** — create `tests/test_baseline_summary.py`:

```python
"""Gate: the hand-maintained summary_latest_* reports must carry the v3.6.0 marker line (stops silent refresh-skips).

The marker is a v3.6.0-DISTINGUISHING string absent from the stale files — NOT a bare float
(DE's committed 0.907 and EN's 0.905 already appear in the stale files, so a bare-float gate
would pass even on a skipped refresh)."""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# The exact marker substrings written into the summaries in Step 3 (fill from the real run figures):
EN_MARKER = "v3.6.0 baseline (run "   # full line incl. "all-or-nothing 0.938 · per-term 0.971"
DE_MARKER = "v3.6.0 baseline (run "   # full line incl. "all-or-nothing 0.907 · per-term 0.95"

def test_summary_latest_en_matches_current_baseline():
    text = (REPO / "evals" / "reports" / "summary_latest_en.md").read_text(encoding="utf-8")
    assert EN_MARKER in text and "all-or-nothing 0.938" in text, "summary_latest_en.md missing v3.6.0 marker — refresh skipped?"

def test_summary_latest_de_matches_current_baseline():
    text = (REPO / "evals" / "reports" / "summary_latest_de.md").read_text(encoding="utf-8")
    assert DE_MARKER in text and "per-term 0.95" in text, "summary_latest_de.md missing v3.6.0 marker — refresh skipped?"
```
**Assert the v3.6.0 marker line (absent from the stale files), NOT a bare float.** Replace the figure substrings with the ACTUAL Step-1/2 numbers (committed constant ↔ committed file; no live float, no flakiness). For DE, the all-or-nothing 0.907 pre-exists in the stale file, so the gate keys on `per-term 0.95` (which does NOT) + the marker line.

- [ ] **Step 5: Run the full suite**

Run: `PYTHONPATH=. python3 -m pytest tests/ -q`
Expected: all pass, incl. the two new baseline-summary tests.

- [ ] **Step 6: Stage commit (await user OK)**

```bash
git add evals/reports/summary_latest_en.md evals/reports/summary_latest_en.json evals/reports/summary_latest_de.md evals/reports/summary_latest_de.json tests/test_baseline_summary.py evals/reports/pattern_en_*.json evals/reports/pattern_de_*.json
git commit -m "test(eval): v3.6.0 re-baseline + summary refresh (EN+DE) + baseline gate-tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Post-implementation (controller-run after all tasks)
- **Final Skeptic review** of the whole branch diff before any merge/push (standing rule).
- Ship sequence (on explicit user OK): squash-merge to main + tag v3.6.0 + GH release (like v3.5.3); update the marketplace plugin locally; `/freshness` sweep.

## Verification (end-to-end)
1. `PYTHONPATH=. python3 -m pytest tests/ -q` green — `EN/DE_PATTERN_IDS` contain 42, `UNIVERSAL_PATTERN_IDS` unchanged, TN-integrity set widened, baseline gate-tests green.
2. `scan(...)`: `aphorism_formula`/`de_aphorism_formula` fire on the 2 hard anchors each, silent on adversarial copula/Fachsprache + the soft "language/currency of" shapes.
3. `grep -rn "41 pattern\|41 total\|41 Patterns\|37 shared" SKILL.md README.md .claude-plugin/` → empty; version reads 3.6.0 in SKILL.md/plugin.json/README badge+header.
4. Gate-2: #42 anchor + held-out cases detected (recall); #34 staccato positive collapses + negative survives; all-or-nothing EN≈0.938/DE≈0.907 + per-term EN≈0.971/DE≈0.95 within noise (no regression).
5. `git diff --stat main`: only the listed files; no `_universal.md`, no `UNIVERSAL_PATTERN_IDS` edit.
