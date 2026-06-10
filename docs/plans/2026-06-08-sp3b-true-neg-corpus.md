# SP3b — True-negative corpus integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. **Review rule (maintainer): no self-review — every diff, the reclassification, and every eval number is verified by the independent Skeptic (`AI/AGENT PERSONAS/Agents/independent-review-agent.md`) from primary evidence before acceptance.**

**Goal:** Fix the mislabeled EN true-negative corpus — 8/9 inputs are the skill's own documented AI-tell "Before" examples — by converting the term-scorable ones to detection cases, deleting the one that isn't term-scorable (#17), validating the two doubtful ones, and keeping only the one genuinely-clean row. No skill change.

**Architecture:** Pure corpus-JSON edits (`evals/corpus/en/patterns/*.json`) + doc corrections, locked by a new corpus-state regression test. A bounded `--runs 5` validation run (45 `claude -p`, subscription) confirms the 5 clean conversions detect, arbitrates the 2 doubtful, and confirms the 1 genuine true-neg. No SKILL.md change.

**Tech Stack:** Python 3.11 + pytest; corpus is JSON; eval is `claude -p` (subscription, Task 5 only — Tasks 1–4 are zero-quota).

**Spec:** `docs/specs/2026-06-08-sp3b-true-neg-corpus-design.md` (Skeptic-approved, round 4).

**Branch:** in-place on `sp3b-true-neg-corpus` (off `main`).

---

## File structure

| File | Change | Task |
|---|---|---|
| `evals/corpus/en/patterns/pattern_008.json`, `_014.json`, `_015.json`, `_029.json` | convert TN→detection (5 clean cases; 014 has 2) | 1 |
| `evals/corpus/en/patterns/pattern_013.json`, `_009.json` | convert TN→detection speculatively (validate-or-gap) | 2 |
| `evals/corpus/en/patterns/pattern_017.json` | delete the case (not term-scorable) → `cases: []` | 3 |
| `tests/test_corpus_true_negative_integrity.py` | NEW — lock the corrected corpus state | 1 |
| `docs/plans/sp3b-notes.md` + `summary_latest_en.md` + `sp1-baselines.md` + `sp3a` spec | doc corrections | 4 |

`pattern_019.json` is **unchanged** (the one genuine true-neg).

---

## Task 1: Convert the 5 clean rows + lock with a regression test

**Files:** `evals/corpus/en/patterns/pattern_008.json`, `pattern_014.json`, `pattern_015.json`, `pattern_029.json`; `tests/test_corpus_true_negative_integrity.py`

Each clean row: in the `cases[0]` object, set `"true_negative": false`, populate `"expected_changes"`, and **append** an SP3b provenance line to `notes` (preserve the meetup dissent already recorded there — do not delete it).

- [ ] **Step 1: Write the failing regression test** — create `tests/test_corpus_true_negative_integrity.py` with ONLY the clean-conversions test (the `only_pattern_019` test lands in Task 3, where the last edit makes it pass — so every task commit stays green):

```python
"""Locks the SP3b corpus fix: the EN true-negative set must contain ONLY
genuinely-clean human text, never the skill's own AI-tell Before-examples."""
from pathlib import Path
from evals.scripts._shared import load_pattern_corpus

REPO_ROOT = Path(__file__).parent.parent
EN_PATTERNS = REPO_ROOT / "evals" / "corpus" / "en" / "patterns"


def test_clean_conversions_have_expected_changes():
    """The 5 clean conversions are now scorable detection cases with their tell terms."""
    cases = {c.id: c for c in load_pattern_corpus(EN_PATTERNS)}
    expect = {
        "pattern_008_en_001": ["serves as", "boasts"],
        "pattern_014_en_001": ["—"],
        "pattern_014_en_002": ["—"],
        "pattern_015_en_001": ["(Objectives and Key Results)"],
        "pattern_029_en_001": ["Speed matters"],
    }
    for cid, terms in expect.items():
        assert cid in cases, f"{cid} missing"
        assert cases[cid].true_negative is False
        assert cases[cid].expected_changes == terms
        # each term must be present in the input (else unscorable)
        low = cases[cid].input.lower()
        for t in terms:
            assert t.lower() in low, f"{t!r} not in {cid} input"
```

- [ ] **Step 2: Run it, verify failure** — `PYTHONPATH=. python3 -m pytest tests/test_corpus_true_negative_integrity.py -q` → FAIL (the 5 rows are still `true_negative=true` with empty `expected_changes`).

- [ ] **Step 3: Edit `pattern_008.json`** — in `cases[0]`: `"true_negative": false`, `"expected_changes": ["serves as", "boasts"]`, and append to `notes`: ` | SP3b 2026-06-08: reclassified true_negative→detection — input is the skill's own #8 Before-example (en.md:139, After :142 drops 'serves as'/'boasts'). The meetup true_negative flag contradicted the skill doc.`

- [ ] **Step 4: Edit `pattern_014.json`** — for BOTH cases (`pattern_014_en_001`, `pattern_014_en_002`): `"true_negative": false`, `"expected_changes": ["—"]` (the literal U+2014 em-dash char), append `notes`: ` | SP3b 2026-06-08: reclassified true_negative→detection — input is the skill's own #14 em-dash Before-example (_universal.md:58/64, After replaces — with commas).`

- [ ] **Step 5: Edit `pattern_015.json`** — `cases[0]`: `"true_negative": false`, `"expected_changes": ["(Objectives and Key Results)"]`, append `notes`: ` | SP3b 2026-06-08: reclassified true_negative→detection — skill's own #15 bold-acronym Before-example (_universal.md:103, After drops the parenthetical).`

- [ ] **Step 6: Edit `pattern_029.json`** — `cases[0]`: `"true_negative": false`, `"expected_changes": ["Speed matters"]`, append `notes`: ` | SP3b 2026-06-08: reclassified true_negative→detection — skill's own #29 fragmented-header Before-example (_universal.md:40, After deletes the warm-up). NB the meetup 2/2/5-dissent defended it as craft; the skill doc + actual behavior (SP1 0/5 TN = always edited) treat it as a tell. Skill-design dispute noted, not resolved here.`

- [ ] **Step 7: Run the test + full suite** — `PYTHONPATH=. python3 -m pytest tests/test_corpus_true_negative_integrity.py -q` → PASS (the lone clean-conversions test goes green now). Then `PYTHONPATH=. python3 -m pytest -q` → green (**baseline 329 + 1 new = 330**). Confirm the JSON is valid: `PYTHONPATH=. python3 -c "from evals.scripts._shared import load_pattern_corpus; from pathlib import Path; load_pattern_corpus(Path('evals/corpus/en/patterns')); print('loads OK')"`.

- [ ] **Step 8: Commit**

```bash
git add evals/corpus/en/patterns/pattern_008.json evals/corpus/en/patterns/pattern_014.json evals/corpus/en/patterns/pattern_015.json evals/corpus/en/patterns/pattern_029.json tests/test_corpus_true_negative_integrity.py
git commit -m "fix(corpus): convert 5 mislabeled EN true-neg rows to detection cases (SP3b Task 1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 9: Skeptic review** the diff: are the 5 `expected_changes` terms present-in-input and removed by the doc After (so they'll detect)? Notes preserved (meetup dissent not deleted)? JSON valid? Fix findings.

---

## Task 2: Convert the 2 validate-or-gap rows (speculative)

**Files:** `evals/corpus/en/patterns/pattern_013.json`, `pattern_009.json`

These are converted now but **arbitrated by Task 5's run** (SP1 data predicts they may not detect — the skill mostly leaves them; a non-detect → delete-as-recorded-gap in Task 5).

- [ ] **Step 1: Edit `pattern_013.json`** — `cases[0]` (`pattern_013_en_001`): `"true_negative": false`, `"expected_changes": ["are preserved automatically"]`, append `notes`: ` | SP3b 2026-06-08: speculative true_negative→detection — #13 passive-voice Before-example (en.md:208). Passive is a weak term; Task 5 validates — if it does not majority-detect, delete as a recorded EN gap (#13 not cleanly term-scorable).`

- [ ] **Step 2: Edit `pattern_009.json`** — find the case with `id == "pattern_009_en_003"` in its `cases[]` (the file has 3 cases; edit only that one): `"true_negative": false`, `"expected_changes": ["rather than to impress"]`, append `notes`: ` | SP3b 2026-06-08: speculative true_negative→detection — #9 'rather than' dismissal (en.md:162; on-the-table test: 'impress with complexity' is a strawman, After = 'write clearly'). SP1 TN 4/5 (skill mostly leaves it) → Task 5 validates; non-detect → delete as recorded gap.`

- [ ] **Step 3: Validate JSON loads** — `PYTHONPATH=. python3 -c "from evals.scripts._shared import load_pattern_corpus; from pathlib import Path; cs={c.id:c for c in load_pattern_corpus(Path('evals/corpus/en/patterns'))}; assert cs['pattern_013_en_001'].true_negative is False and cs['pattern_009_en_003'].true_negative is False; print('OK')"`.

- [ ] **Step 4: Commit**

```bash
git add evals/corpus/en/patterns/pattern_013.json evals/corpus/en/patterns/pattern_009.json
git commit -m "fix(corpus): speculatively convert 013+009_003 true-neg rows (validate-or-gap, SP3b Task 2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 5: Skeptic review** the diff: only `pattern_009_en_003` edited in pattern_009 (not 001/002)? notes preserved? JSON valid?

---

## Task 3: Delete the un-term-scorable #17 case

**Files:** `evals/corpus/en/patterns/pattern_017.json`

- [ ] **Step 1: Add the `only_pattern_019` test** — append to `tests/test_corpus_true_negative_integrity.py` (it can pass only after this task's 017 deletion — Tasks 1+2 already removed the other 7 from the TN set, so the last bogus TN is 017, deleted in Step 2):

```python
def test_only_pattern_019_is_true_negative():
    """After SP3b, pattern_019 is the lone genuine true-neg; the 8 skill-own-example
    rows are converted to detection or deleted — none remain true_negative."""
    tn = {c.id for c in load_pattern_corpus(EN_PATTERNS) if c.true_negative}
    assert tn == {"pattern_019_en_001"}, f"unexpected true_negative set: {tn}"
```

- [ ] **Step 2: Edit `pattern_017.json`** — set `"cases": []` (empty array, do NOT remove the `cases` key — `sp1_tn_multirun.py`'s `d.get("cases",[d])` fallback would otherwise treat the file dict as a case). Add a top-level `"note"` field: `"note": "SP3b 2026-06-08: the sole case (pattern_017_en_001) was deleted. Its input was the skill's own #17 Title-Case Before-example (_universal.md:113), but #17's tell is a capitalization-only edit — the term-absence detection scorer lowercases both sides, so any rewrite retains the lowercased term → permanently unscorable. #17 detection is exercised by the regex scorer / DE corpus, not this term-based pattern eval."`

- [ ] **Step 3: Verify loader + run the integrity test + full suite** — `PYTHONPATH=. python3 -c "from evals.scripts._shared import load_pattern_corpus; from pathlib import Path; ids={c.id for c in load_pattern_corpus(Path('evals/corpus/en/patterns'))}; assert 'pattern_017_en_001' not in ids; print('017 gone, loader OK, total', len(ids))"`. Then `PYTHONPATH=. python3 -m pytest tests/test_corpus_true_negative_integrity.py -q` → BOTH functions PASS (019 is the lone true_negative). Then full suite `PYTHONPATH=. python3 -m pytest -q` → green: **baseline 329 + 2 new integrity tests = 331** (paste the real number; the gate is "329 pre-existing still pass + 2 new pass", not a coincidental total).

- [ ] **Step 4: Commit**

```bash
git add evals/corpus/en/patterns/pattern_017.json tests/test_corpus_true_negative_integrity.py
git commit -m "fix(corpus): delete un-term-scorable #17 + lock 'only 019 is true_neg' (SP3b Task 3)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 5: Skeptic review**: `cases:[]` (key present, empty)? note explains why? `only_019` test passes (TN set == {019})? loader/aggregation unaffected by the empty pattern? suite 331?

---

## Task 4: Doc corrections (zero quota)

**Files:** `docs/plans/sp3b-notes.md` (new); `evals/reports/summary_latest_en.md`; `docs/plans/sp1-baselines.md`; `docs/specs/2026-06-08-sp3a-multirun-harness-design.md`

- [ ] **Step 1: Create `docs/plans/sp3b-notes.md`** with:

```markdown
# SP3b notes — true-negative corpus integrity (2026-06-08)

**Finding:** 8 of 9 EN pattern-eval `true_negative` inputs were verbatim the skill's
own documented AI-tell "Before" examples (`patterns/en.md` / `_universal.md`). The
eval asked "does the skill leave its own AI-tells unedited?" — backwards. Fixed:
- Converted to detection cases: 008, 014_001, 014_002, 015, 029 (clean); 013, 009_003 (validate-or-gap, see below).
- Deleted (not term-scorable): 017 (#17 capitalization-only).
- Kept (genuine clean): 019 — the lone genuine pattern-eval true-neg (a 4/5 sanity case).

**Rule going forward:** a pattern-eval `true_negative` case MUST be genuinely-clean
human text, NEVER the skill's own AI-tell Before-example. Locked by
`tests/test_corpus_true_negative_integrity.py`.

**Canonical over-edit measure:** the FALSE-POSITIVE eval (`run_false_positive_eval`,
over `en/human/synthetic/` + `de/human/redistributable/`, multi-run via SP3a `--runs`)
— NOT the pattern-eval true-neg. (Note: the EN human corpus is *synthetic*, not sourced
human prose; populating real human samples is future work.)

**Validate-or-gap outcome (Task 5):** <fill in after the run — which of 013/009_003 detected vs were deleted as recorded EN gaps>.
```

- [ ] **Step 2: Correct `summary_latest_en.md`** — the SP1 block line ~6 says true-neg "5/9 … 008/029 corpus disputes". Append a pointer: ` **[Superseded by SP3b 2026-06-08: 8/9 were the skill's own Before-examples; converted to detection / deleted; 1 genuine true-neg (pattern_019). See docs/plans/sp3b-notes.md.]**`

- [ ] **Step 3: Correct `sp1-baselines.md`** — the file carries TWO stale numbers (line ~32 says "6/9 pass"; lines ~59/61/63 say "5/9 majority / 008+029 corpus disputes"). Insert ONE pointer line **immediately above the 5-run true-neg re-baseline table (~line 59)** so it visibly supersedes BOTH framings: `> **Superseded by SP3b (2026-06-08):** 8/9 of these rows were the skill's own documented Before-examples (a corpus-construction bug), not "2 disputes + noise" and not a "5/9 or 6/9 skill defect". Reclassified to detection/deleted — see docs/plans/sp3b-notes.md.`

- [ ] **Step 4: Flag the SP3d overlap** — in `docs/specs/2026-06-08-sp3a-multirun-harness-design.md` near line 15 (the SP3 decomposition mention) OR in STATUS, add: `> SP3b (2026-06-08) subsumes the planned "SP3d pattern_008/029 corpus disputes" — 008/029 are now detection cases; the over-edit slice is the FP eval, not the 9 true-neg cases.` (If the SP3a spec has no such editable line, put this note in `sp3b-notes.md` instead and say so.)

- [ ] **Step 5: Commit**

```bash
git add docs/plans/sp3b-notes.md evals/reports/summary_latest_en.md docs/plans/sp1-baselines.md docs/specs/2026-06-08-sp3a-multirun-harness-design.md
git commit -m "docs(sp3b): corpus-integrity notes + correct stale 'true-neg 5/9 / 2 disputes' claims (SP3b Task 4)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 6: Skeptic review**: do the stale claims actually get corrected at the cited locations? Is the FP-as-canonical + synthetic caveat honest? Fix.

---

## Task 5: Validation run (quota — subscription, ~45 `claude -p`)

> Subscription `claude -p` only, NO API key. Repoint the install to the worktree skill first (unchanged from main, but verify): `ln -sfn "$(pwd)/SKILL.md" ~/.claude/skills/humanizer/SKILL.md`.

- [ ] **Step 1: Validate the 5 clean + 2 doubtful conversions detect.** Per pattern (8, 9, 13, 14, 15, 29), `--force` re-score multi-run:

```bash
for p in 8 9 13 14 15 29; do
  PYTHONPATH=. python3 -u evals/scripts/run_pattern_eval.py --lang en --pattern $p --runs 5 --force
done
```
(Do NOT run `--pattern 17` (deleted) or `--pattern 19` (Step 3).) For each converted case read its `per_pattern` entry: `detected` (majority) + `aggregate.fraction`. **45 calls total** (9 cases ×5). Record per-case majority-detect.

- [ ] **Step 2: Arbitrate 013 + 009_003.** If a converted case reached majority-detect → keep as a detection case. If NOT → it's a real EN detection gap: **delete that case** (`pattern_013.json` → `cases: []` + a `note`; remove `pattern_009_en_003` from pattern_009's `cases[]` leaving its other 2), and record the gap in `sp3b-notes.md` Step-1 placeholder. The integrity test still passes (those IDs are non-true_negative either way). Commit any deletions:

```bash
git add evals/corpus/en/patterns/pattern_013.json evals/corpus/en/patterns/pattern_009.json docs/plans/sp3b-notes.md
git commit -m "fix(corpus): arbitrate 013/009_003 from Task-5 validation data (SP3b)"
```

- [ ] **Step 3: Confirm pattern_019 still passes** as the genuine true-neg:

```bash
PYTHONPATH=. python3 -u evals/scripts/sp1_tn_multirun.py 5
```
(One arg = N runs; no lang token. After conversion it finds only pattern_019.) Expect ~4/5 majority-pass (the SP1 result; one 1.51 spike is known noise). Record.

- [ ] **Step 4: Record + Skeptic-verify** all Task-5 numbers in `sp3b-notes.md` (fill the placeholder). Skeptic confirms: the 5 clean conversions detect (so the corpus now correctly tests documented behavior); 013/009_003 dispositions match their data; 019 passes; same-config; `--force` used (no stale-partial confound).

---

## Task 6: Close-out

- [ ] **Step 1:** Full suite `PYTHONPATH=. python3 -m pytest -q` green (331); `git diff main -- SKILL.md` empty (no skill change). **Guard:** `grep -rn "fill in after the run" docs/plans/sp3b-notes.md` must return NOTHING — the Task-5 placeholder must be replaced with the real outcome (or, if Task 5 was deferred for quota, with an explicit "Task-5 validation deferred — pending quota" line) before merge.
- [ ] **Step 2: Final Skeptic sign-off** of the whole SP3b (all corpus diffs + the validation numbers + the doc corrections together): is the corpus now internally honest, the FP-canonical claim documented, no goal-seeking, no skill change? Fix anything.
- [ ] **Step 3:** Run `/freshness` — sweep vault STATUS/SESSION_LOG/DECISIONS to the SP3b outcome + the SP3d-subsumed note.
- [ ] **Step 4:** `superpowers:finishing-a-development-branch` — squash-merge `sp3b-true-neg-corpus` → `main` (corpus + test + docs; no skill change → no version bump), push on explicit user OK.

---

## Acceptance criteria (all must hold)

- [ ] `tests/test_corpus_true_negative_integrity.py` passes: pattern_019 is the ONLY EN `true_negative`; the 8 bogus rows are non-true_negative or deleted; the 5 clean conversions have their tabled `expected_changes` (present-in-input).
- [ ] 017 deleted (`cases: []`, key present) with a recorded reason; loader/aggregation unaffected.
- [ ] Validation run (45 calls, `--force`): 5 clean conversions majority-detect; 013/009_003 arbitrated + recorded; pattern_019 majority-pass.
- [ ] Doc note records FP eval = canonical over-edit measure (synthetic, honestly labelled); stale "5/9 / 2 disputes" corrected; SP3d overlap flagged.
- [ ] Full pytest green; **SKILL.md byte-identical to main** (no skill change).
- [ ] Every diff + every eval number Skeptic-verified (no self-review).
