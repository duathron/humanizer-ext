# #20/#31 Extensions (v3.5.3) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend two existing humanizer patterns with upstream-v2.8.0 tells — #20 (chatbot artifacts) gains offer-to-continue closers, #31 (rhetorical questions) gains fake-candid discourse openers — in both EN and DE, shipped as a lock-free v3.5.3 patch.

**Architecture:** Watch-list additions to existing `### 20.`/`### 31.` pattern sections in `patterns/en.md` + `patterns/de.md`, backed by two new literal-phrase keys per language in `evals/scripts/regex_scorer.py` (`chatbot_closer`/`fake_candid_opener`, `de_chatbot_closer`/`de_fake_candid_opener`), TP-only corpus cases in the already-existing `pattern_020.json`/`pattern_031.json`, and FP guards proven by direct `scan(text)[key]==0` silence assertions. No new pattern ID, no pattern-count change, no `true_negative` corpus case → none of the three exact-equality test locks is touched.

**Tech Stack:** Python 3.11, pytest, `re`. Skill packs are Markdown. No new dependencies.

## Global Constraints

- **Version:** bump `3.5.2 → 3.5.3` (patch). Sites: `SKILL.md:3` frontmatter, `.claude-plugin/plugin.json:3`, `README.md:3` badge, `README.md:11` table header, + a `## Version History` `3.5.3` entry. **Do NOT change any "41" pattern-count string** (no count change). **Do NOT edit** historical `v3.5.2` references (`README.md:29`, `:188`, the `:356` version-history entry) or `.claude-plugin/marketplace.json`.
- **Lock-free invariant:** add NO new `### N.` pattern heading; add NO `true_negative: true` corpus case. (This keeps `test_skill_structure.py:57/:143` `EN/DE_PATTERN_IDS` and `test_corpus_true_negative_integrity.py:44` untouched.)
- **DROPPED phrase:** do NOT add `Sagen wir es so` to #31 DE — it is a calque + a real German hedge (MeetUp German-linguist).
- **Run tests from repo root** as `PYTHONPATH=. python3 -m pytest <path> -v`. The skill is invoked via `claude -p`; **never source `ANTHROPIC_API_KEY`** before any skill/eval call.
- **Standing rule:** subagent-driven TDD; every task diff Skeptic-reviewed from primary evidence (no self-review); **never commit or push without explicit user OK** — the `git commit` steps below are staged for the user's go, not executed autonomously.
- **FP-safety bias:** the regexes anchor openers at line start with a trailing `,`/`?` and require closers to end in `?`, so ordinary mid-sentence uses ("I honestly think…", "they continue…") do not match.

---

### Task 1: EN — #20 closers + #31 openers (pack + scorer + tests + corpus)

**Files:**
- Modify: `evals/scripts/regex_scorer.py` (add 2 keys to `PATTERNS_EN`, dict starts `:53`)
- Modify: `patterns/en.md:233` (#20 watch line), `patterns/en.md:357` (after #31 Problem para)
- Modify: `evals/corpus/en/patterns/pattern_020.json`, `evals/corpus/en/patterns/pattern_031.json`
- Test: `tests/test_regex_scorer.py`

**Interfaces:**
- Consumes: `scan(text, lang="en") -> dict[str,int]` and `PATTERNS_EN` from `evals.scripts.regex_scorer` (already imported in the test module).
- Produces: `PATTERNS_EN["chatbot_closer"]`, `PATTERNS_EN["fake_candid_opener"]` — two `(compiled_regex, label)` tuples, surfaced as integer counts in `scan(...)` output under those keys.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_regex_scorer.py`)

```python
def test_chatbot_closer_fires_en():
    assert scan("That's the overview. Want me to continue?", lang="en")["chatbot_closer"] >= 1
    assert scan("Should I continue?", lang="en")["chatbot_closer"] >= 1
    assert scan("Want me to give examples?", lang="en")["chatbot_closer"] >= 1

def test_chatbot_closer_silent_on_ordinary_continue_en():
    # FP guard: "continue" in normal prose is not a closer (no "?", no "want me to")
    assert scan("Prices continue to climb each year.", lang="en")["chatbot_closer"] == 0

def test_fake_candid_opener_fires_en():
    assert scan("Honestly? It depends on how often you use it.", lang="en")["fake_candid_opener"] >= 1
    assert scan("Look, the data is clear.", lang="en")["fake_candid_opener"] >= 1
    assert scan("Here's the thing, nobody actually checked.", lang="en")["fake_candid_opener"] >= 1

def test_fake_candid_opener_silent_mid_sentence_en():
    # FP guard: the words mid-sentence are ordinary; only the standalone opener is a tell
    assert scan("I honestly think it works.", lang="en")["fake_candid_opener"] == 0
    assert scan("Take a look at the chart.", lang="en")["fake_candid_opener"] == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONPATH=. python3 -m pytest tests/test_regex_scorer.py -k "chatbot_closer or fake_candid_opener" -v`
Expected: FAIL — `KeyError: 'chatbot_closer'` / `'fake_candid_opener'` (keys not yet in `PATTERNS_EN`).

- [ ] **Step 3: Add the two keys to `PATTERNS_EN`** (in `evals/scripts/regex_scorer.py`, inside the `PATTERNS_EN = { ... }` dict — place after the `sycophantic_opener` entry at `:109` for topical grouping)

```python
    "chatbot_closer": (
        re.compile(
            r"(want me to\b[^.?!]*\?|should i continue\?)",
            re.I,
        ),
        "offer-to-continue closer",
    ),
    "fake_candid_opener": (
        re.compile(
            r"(?m)^[ \t>*\-]*"
            r"(Look|Here's the thing|The thing is|Let's be honest|Real talk|Honestly)\b[,?]",
            re.I,
        ),
        "fake-candid discourse opener",
    ),
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONPATH=. python3 -m pytest tests/test_regex_scorer.py -k "chatbot_closer or fake_candid_opener" -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Extend the #20 watch line in `patterns/en.md:233`**

Replace:
```
**Words to watch:** I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like..., let me know, here is a...
```
with:
```
**Words to watch:** I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like..., Want me to...?, Should I continue?, Want me to give examples?, let me know, here is a...
```

- [ ] **Step 6: Add an openers watch line to #31** (in `patterns/en.md`, immediately after the #31 `**Problem:**` paragraph that ends `...just start with the answer.`)

Insert a new paragraph:
```
**Openers to watch:** Look, / Here's the thing / The thing is / Let's be honest / Real talk / Honestly? — used as standalone theatrical hooks before an ordinary point. The words mid-sentence are fine; the tell is the standalone pause-and-reveal opener, which usually disappears when you just state the point.
```

- [ ] **Step 7: Add TP corpus cases** (EN)

In `evals/corpus/en/patterns/pattern_020.json`, append to `cases`:
```json
    {
      "id": "pattern_020_en_002",
      "input": "The French Revolution began in 1789 amid financial crisis and food shortages. Want me to continue? Should I continue?",
      "expected_changes": ["Want me to continue?", "Should I continue?"],
      "expected_unchanged": [],
      "domain": "casual",
      "source": "upstream_v2.8.0_port"
    }
```
In `evals/corpus/en/patterns/pattern_031.json`, append to `cases`:
```json
    {
      "id": "pattern_031_en_002",
      "input": "Honestly? The approach works because it reduces cognitive load. Look, that's the whole point.",
      "expected_changes": ["Honestly?", "Look,"],
      "expected_unchanged": [],
      "domain": "casual",
      "source": "upstream_v2.8.0_port"
    }
```

- [ ] **Step 8: Run the full suite + a corpus-load smoke to verify nothing broke**

Run: `PYTHONPATH=. python3 -m pytest tests/ -q`
Expected: all pass (the frozen ID-set + TN-integrity locks stay green — no new heading, no `true_negative` case).
Run: `PYTHONPATH=. python3 -c "from pathlib import Path; from evals.scripts._shared import load_pattern_corpus; cs=load_pattern_corpus(Path('evals/corpus/en/patterns')); print(sum(1 for c in cs if c.id in ('pattern_020_en_002','pattern_031_en_002')))"`
Expected: prints `2` (both new cases load; no schema error). `load_pattern_corpus(corpus_dir: Path)` (`_shared.py:34`) globs `pattern_*.json` under the given dir and returns `list[Case]`.

- [ ] **Step 9: Stage commit (await user OK before running)**

```bash
git add evals/scripts/regex_scorer.py patterns/en.md evals/corpus/en/patterns/pattern_020.json evals/corpus/en/patterns/pattern_031.json tests/test_regex_scorer.py
git commit -m "feat(skill): EN #20 offer-to-continue closers + #31 fake-candid openers (v3.5.3)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: DE — #20 closers + #31 openers (pack + scorer + tests + corpus)

**Files:**
- Modify: `evals/scripts/regex_scorer.py` (add 2 keys to `PATTERNS_DE`, dict starts `:273`)
- Modify: `patterns/de.md` (#20 Trigger-Wörter block starts `:486`; append after the phrase `Vielen Dank für Ihre Zeit` at `:491`), `patterns/de.md` (after #31 Problem para, "Vorher:" follows at `:701`)
- Modify: `evals/corpus/de/patterns/pattern_020.json`, `evals/corpus/de/patterns/pattern_031.json`
- Test: `tests/test_regex_scorer.py`

**Interfaces:**
- Consumes: `scan(text, lang="de")`, `PATTERNS_DE`, `UNIVERSAL_MECHANICS_KEYS` from `evals.scripts.regex_scorer`.
- Produces: `PATTERNS_DE["de_chatbot_closer"]`, `PATTERNS_DE["de_fake_candid_opener"]` — two `(compiled_regex, label)` tuples surfaced in `scan(..., lang="de")`.

- [ ] **Step 1: Write the failing tests** (append to `tests/test_regex_scorer.py`)

```python
def test_de_chatbot_closer_fires():
    assert scan("Hier ist die Übersicht. Soll ich fortfahren?", lang="de")["de_chatbot_closer"] >= 1
    assert scan("Möchten Sie, dass ich das ausführe?", lang="de")["de_chatbot_closer"] >= 1
    assert scan("Soll ich Beispiele geben?", lang="de")["de_chatbot_closer"] >= 1

def test_de_fake_candid_opener_fires():
    assert scan("Mal ehrlich, das funktioniert selten.", lang="de")["de_fake_candid_opener"] >= 1
    assert scan("Ganz ehrlich? Es kommt darauf an.", lang="de")["de_fake_candid_opener"] >= 1
    assert scan("Die Sache ist die, dass niemand es geprüft hat.", lang="de")["de_fake_candid_opener"] >= 1

def test_de_fake_candid_opener_silent_on_legit_use():
    # FP guard: "Die Sache ist die Lösung..." (no comma hook) and mid-sentence are not tells
    assert scan("Die Sache ist die Lösung des Problems.", lang="de")["de_fake_candid_opener"] == 0
    assert scan("In der Sache ist die Lage komplex.", lang="de")["de_fake_candid_opener"] == 0

def test_de_extension_keys_dont_break_clean_prose():
    # The existing clean-German guard must still sum to zero with the new keys present
    text = ("Ich verbrachte den Morgen damit, mein Fahrrad zu reparieren. "
            "Die Kette war gerissen, was mich eine Stunde kostete.")
    hits = scan(text, lang="de")
    assert hits["de_chatbot_closer"] == 0
    assert hits["de_fake_candid_opener"] == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `PYTHONPATH=. python3 -m pytest tests/test_regex_scorer.py -k "de_chatbot_closer or de_fake_candid_opener or de_extension_keys" -v`
Expected: FAIL — `KeyError: 'de_chatbot_closer'` / `'de_fake_candid_opener'`.

- [ ] **Step 3: Add the two keys to `PATTERNS_DE`** (inside `PATTERNS_DE = { ... }`, `:273`)

```python
    "de_chatbot_closer": (
        re.compile(
            r"(soll ich fortfahren\?|möchten sie,? dass ich\b[^.?!]*\?|soll ich beispiele geben\?)",
            re.I,
        ),
        "Angebot zur Fortsetzung (Chatbot-Schluss)",
    ),
    "de_fake_candid_opener": (
        re.compile(
            r"(?m)^[ \t>*\-]*"
            r"(Mal ehrlich[,?]|Ganz ehrlich\?|Die Sache ist die,)",
            re.I,
        ),
        "vorgetäuschte Offenheit (Eröffnungs-Floskel)",
    ),
```
(Note: `Die Sache ist die,` requires the trailing comma so the hook form fires but "Die Sache ist die Lösung" does not. `Sagen wir es so` is deliberately absent.)

- [ ] **Step 4: Run the tests to verify they pass**

Run: `PYTHONPATH=. python3 -m pytest tests/test_regex_scorer.py -k "de_chatbot_closer or de_fake_candid_opener or de_extension_keys" -v`
Expected: PASS (4 tests). Also re-run the existing guard:
Run: `PYTHONPATH=. python3 -m pytest tests/test_regex_scorer.py -k "de_clean_prose" -v`
Expected: PASS (new keys don't fire on the bike-repair text).

- [ ] **Step 5: Extend the #20 DE Trigger line in `patterns/de.md:486`**

Append to the `**Trigger-Wörter / -Phrasen:**` list at the phrase `Vielen Dank für Ihre Zeit` (`de.md:491`, the end of the list):
```
, Soll ich fortfahren?, Möchten Sie, dass ich …?, Soll ich Beispiele geben?
```

- [ ] **Step 6: Add an openers line to DE #31** (in `patterns/de.md`, immediately after the #31 `**Problem:**` paragraph that ends `...immer in direkte Aussagen umwandeln...`)

Insert:
```
**Eröffnungs-Floskeln (vorgetäuschte Offenheit):** "Mal ehrlich", "Ganz ehrlich?", "Die Sache ist die," — als alleinstehende Eröffnungs-Haken vor einer gewöhnlichen Aussage. Die Wörter mitten im Satz sind unbedenklich; das Tell ist der alleinstehende Haken. (Nicht aufnehmen: "Sagen wir es so" — echte Hecke/Reformulierung im Deutschen, kein KI-Tell.)
```

- [ ] **Step 7: Add TP corpus cases** (DE)

In `evals/corpus/de/patterns/pattern_020.json`, append to `cases`:
```json
    {
      "id": "pattern_020_de_004",
      "input": "Die Französische Revolution begann 1789. Soll ich fortfahren? Soll ich Beispiele geben?",
      "expected_changes": ["Soll ich fortfahren?", "Soll ich Beispiele geben?"],
      "expected_unchanged": [],
      "domain": "casual",
      "source": "upstream_v2.8.0_port"
    }
```
In `evals/corpus/de/patterns/pattern_031.json`, append to `cases`:
```json
    {
      "id": "pattern_031_de_004",
      "input": "Mal ehrlich, der Ansatz funktioniert, weil er die kognitive Last reduziert. Die Sache ist die, dass das den Unterschied macht.",
      "expected_changes": ["Mal ehrlich,", "Die Sache ist die,"],
      "expected_unchanged": [],
      "domain": "casual",
      "source": "upstream_v2.8.0_port"
    }
```
(`evals/corpus/de/patterns/pattern_020.json` and `pattern_031.json` both already exist — verified — so this is an append to `cases`, not a new file.)

- [ ] **Step 8: Run the full suite**

Run: `PYTHONPATH=. python3 -m pytest tests/ -q`
Expected: all pass (frozen ID-set + TN-integrity + DE clean-prose locks green).

- [ ] **Step 9: Stage commit (await user OK)**

```bash
git add evals/scripts/regex_scorer.py patterns/de.md evals/corpus/de/patterns/pattern_020.json evals/corpus/de/patterns/pattern_031.json tests/test_regex_scorer.py
git commit -m "feat(skill): DE #20 offer-to-continue closers + #31 fake-candid openers (v3.5.3)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Version bump 3.5.2 → 3.5.3

**Files:**
- Modify: `SKILL.md:3`, `.claude-plugin/plugin.json:3`, `README.md:3`, `README.md:11`, `README.md` Version-History section (`:354`+)

**Interfaces:** none (metadata only).

- [ ] **Step 1: Bump the SKILL frontmatter** — `SKILL.md:3`

Replace `version: 3.5.2` with `version: 3.5.3`.

- [ ] **Step 2: Bump the plugin manifest** — `.claude-plugin/plugin.json:3`

Replace `"version": "3.5.2",` with `"version": "3.5.3",`. (Leave the `description` "41 patterns" string at `:4` UNCHANGED — no count change.)

- [ ] **Step 3: Bump the README badge + table header**

`README.md:3` — replace `version-3.5.2-blue` with `version-3.5.3-blue`.
`README.md:11` — replace the current-version cell `v3.5.2` with `v3.5.3`. (Do NOT touch the `v3.5.2` strings at `:29`, `:188`, or the `:356` history entry — those describe shipped 3.5.2 work.)

- [ ] **Step 4: Add the Version-History entry** — under `## Version History` (insert above the `- **3.5.2**` line at `:356`)

```
- **3.5.3** — Patch: ports two upstream `blader/humanizer` v2.8.0 tells as extensions to existing patterns (no new pattern, count stays 41). **#20 Collaborative Communication Artifacts** gains offer-to-continue closers ("Want me to…?", "Should I continue?"); **#31 Rhetorical and Self-Answering Questions** gains fake-candid discourse openers ("Look,", "Here's the thing", "Honestly?"). Both in EN + DE; the German calque "Sagen wir es so" was deliberately excluded (it is a real German hedge). New deterministic `regex_scorer` keys (`chatbot_closer`/`fake_candid_opener` + DE) with FP guards proven by scorer-silence assertions; TP corpus cases added. No frozen-ID/count/true-negative-lock change.
```

- [ ] **Step 5: Verify counts untouched + suite green**

Run: `grep -c "41 pattern" SKILL.md README.md`
Expected: unchanged from before this task (no "41"→"43" edits).
Run: `PYTHONPATH=. python3 -m pytest tests/ -q`
Expected: all pass.

- [ ] **Step 6: Stage commit (await user OK)**

```bash
git add SKILL.md .claude-plugin/plugin.json README.md
git commit -m "chore(release): bump 3.5.2 -> 3.5.3 (#20/#31 extensions)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Post-implementation (not a task — controller-run after all tasks)

- **Targeted detection check (quota, optional per spec Gate-2):** `PYTHONPATH=. python3 evals/scripts/run_pattern_eval.py --lang en --pattern 20` then `--pattern 31`, and `--lang de --pattern 20` / `--pattern 31`. Confirms the LLM acts on the new watch-list phrases; NOT a full re-baseline (watch-list patch on existing patterns). Strip `ANTHROPIC_API_KEY` first (subscription auth).
- **Final Skeptic review** of the whole branch diff before any merge/push (standing rule).
- **`/freshness`** vault sweep for v3.5.3 after ship.

## Verification (end-to-end)
1. `PYTHONPATH=. python3 -m pytest tests/ -q` green — including the three exact-equality locks (`EN_PATTERN_IDS`, `DE_PATTERN_IDS`, `pattern_019_en_001` TN set) UNCHANGED.
2. `scan(...)` fires on the new closer/opener TP strings and is silent on the FP-guard strings (EN + DE), proven by the new tests.
3. `git diff --stat main` touches only: `regex_scorer.py`, `patterns/en.md`, `patterns/de.md`, `pattern_020/031.json` (en+de), `tests/test_regex_scorer.py`, `SKILL.md`, `plugin.json`, `README.md`. No `_universal.md`, no `test_skill_structure.py`, no `test_corpus_true_negative_integrity.py`, no count-string edits.
4. Version reads `3.5.3` in `SKILL.md`, `plugin.json`, README badge/header; "41" count strings unchanged.
