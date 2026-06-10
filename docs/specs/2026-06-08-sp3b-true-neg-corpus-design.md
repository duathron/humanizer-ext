# SP3b — True-negative corpus integrity (design)

**Status:** approved design, 2026-06-08, **Skeptic-reviewed** (design review killed the original "restraint lever" premise; spec review round 1 found pure-deletion leaves 6 EN patterns uncovered → re-scoped to **convert**). Sub-project of SP3 (eval rigor). **No skill change.**

## The finding that re-scoped this

SP1 deferred "true-negative over-editing" as noise-dominated. The SP3b design review did the corpus archaeology SP1 skipped: of the 9 EN true-negative cases (pass = the skill leaves the input ~unchanged, edit_ratio ≤ 0.10), **8 inputs are verbatim the skill's own documented AI-tell "Before" examples** from `patterns/en.md` / `patterns/_universal.md`. The eval asks *"does the skill leave its own AI-tell examples unedited?"* — and the skill "fails" by correctly applying its rules. **Corpus-construction bug, not a skill defect.**

The round-1 spec review then found that **6 of the 8 patterns have ONLY this (bogus) case** — no detection case. So *deleting* would leave 6 EN patterns eval-uncovered. The bogus inputs are the skill's own Before-examples = **perfect detection cases**. So the fix is to **convert** them to detection cases (relabel + add `expected_changes`), which fixes the integrity bug AND adds detection coverage where there currently is none.

**Verified classification (primary evidence — each input grep'd against the doc Before/After):**

| true-neg case | doc Before/After | action | `expected_changes` (present in input, removed in the doc After) |
|---|---|---|---|
| pattern_008_en_001 | en.md:139/142 (#8 copula) | **→ detection (clean)** | `["serves as", "boasts"]` |
| pattern_014_en_001 | _universal.md:58/61 (#14 em-dash) | **→ detection (clean)** | `["—"]` (U+2014; doc After → commas) |
| pattern_014_en_002 | _universal.md:64 (#14 paired em-dash) | **→ detection (clean)** | `["—"]` |
| pattern_015_en_001 | _universal.md:103/106 (#15 bold acronyms) | **→ detection (clean)** | `["(Objectives and Key Results)"]` |
| pattern_029_en_001 | _universal.md:40/45 (#29 fragmented header) | **→ detection (clean)** | `["Speed matters"]` |
| pattern_013_en_001 | en.md:208 (#13 passive) | → detection **(validate-or-gap)** | `["are preserved automatically"]` |
| pattern_009_en_003 | en.md:162/164 (#9 rather-than) | → detection **(validate-or-gap)** | `["rather than to impress"]` |
| pattern_017_en_001 | _universal.md:113/116 (#17 Title Case) | **DELETE — not term-scorable** | — (capitalization-only edit; see Component 1b) |
| pattern_019_en_001 | input is the straight-quote *After* (_universal.md:155) | **KEEP true_negative** | — (genuinely clean) |

**Three tiers (from the scorer + SP1 baseline data):**
- **Clean conversions (5):** 008, 014_001, 014_002, 015, 029 — term-scorable AND SP1 shows the skill substantially edits them (TN pass 0/5–3/5), so the tell is removed → they will detect.
- **Validate-or-gap (2):** 013 (passive — weak term) and 009_003 (SP1 TN 4/5 — the skill mostly *leaves it*, so as a detection case the term likely survives). The validation run (Component 5) decides: majority-detect → keep as a detection case; else **record as a real EN detection gap** (legitimate finding — the skill under-edits this tell) and delete the case with rationale. Not forced.
- **Unscorable (1):** 017 — #17's tell is capitalization only; the scorer lowercases both sides (`run_pattern_eval` `_score_case_once`), so `"and global"` survives any rewrite → `detected=False` on a *perfect* rewrite. It cannot be a detection case under the term-absence scorer. Delete it; record that #17 detection is not term-scorable (it's exercised by the regex scorer / DE corpus, not this eval).

## Goal

Fix the mislabeled true-negative corpus: convert the term-scorable AI-tell rows into valid detection cases (using the skill's own canonical Before/After), delete the one that isn't term-scorable (#17), validate the two doubtful ones, and keep only `pattern_019` as a genuine true-negative. Record that the canonical over-edit measure is the **FP eval** (made multi-run by SP3a). No skill change.

## Non-goals (deferred / out of scope)

- **Skill restraint rule** — the design review showed there is no genuine clean row that stably over-edits to justify it. *Honest caveat:* `pattern_019` (the one genuine-clean row) is **4/5** at `--runs 5`, not 5/5 — one run over-edited at ratio 1.51 (`sp1-baselines.md`). That single intermittent spike is run-to-run **noise** on otherwise-clean text, not a stable defect; the over-edit signal of record is the FP eval, not this one case. No restraint lever.
- **Sourcing NEW true-negative cases** — the FP eval carries the real over-edit coverage; the pattern-eval true-neg becomes a minimal sanity check (`pattern_019`).
- Career FP (SP3c); DE FP (passing); CI (SP2); the SP3a harness (done).
- **DE pattern true-neg:** none exist (verified: 0 DE `true_negative` pattern cases) — so "9 EN" is the whole pattern true-neg set; nothing DE to fold in.

## Components & edits

### 1. Convert the 5 clean rows to detection cases
For pattern_008, 014_001, 014_002, 015, 029: in each pattern file's `cases[]` entry, set `true_negative` to `false` (or remove the key) and add `expected_changes` per the table. Relabels the skill's own Before-example as the detection case it should always have been. JSON-data edits.
- **Term selection is falsifiable, not goal-seeking:** each `expected_changes` term is present in the input (verified) and removed in the doc's own canonical After (verified) — not text hand-picked to pass. These 5 are "clean" because the term is removable AND SP1 shows the skill edits them (so they will detect, confirmed in Component 5).

### 1b. pattern_017 — DELETE (not term-scorable)
#17's tell is a capitalization-only edit (`And`→`and`, `Global`→`global`). The detection scorer lowercases both input and rewrite, so `"and global"` survives even a perfect rewrite → permanent false `detected=False`. It cannot be a valid detection case here. **Delete pattern_017's case** and record in the corpus note that #17 detection is exercised by the regex scorer / DE corpus, not the term-absence pattern eval. (This *empties* pattern_017.json's `cases[]` — see "no-empty-file" note below; the loader tolerates `cases:[]`.)

### 2. validate-or-gap rows (013 passive, 009_003 rather-than)
Both are converted to detection cases speculatively, but SP1 data flags them as likely non-detectors (013 passive isn't a clean term; 009_003 is TN **4/5** — the skill mostly *leaves it*, so the term will likely survive). They are NOT confident conversions.
- **pattern_009_003:** by #9's on-the-table test (`en.md:167`: cut the "rather than Y" dismissal when no one claims Y — "impress with complexity" is a strawman), the doc treats it as the AI dismissal (After = "The goal is to write clearly"), so `expected_changes=["rather than to impress"]`. BUT the skill leaves it alone 4/5, so it may not detect — that itself is a signal (the skill under-edits this tell, or the contrast reads as legit).
- **Component 5 arbitrates both:** majority-detect at `--runs 5` → keep as a detection case; else **record as a real EN detection gap** (legitimate finding) and **delete the case with a recorded rationale**. Do NOT force a pass. (Deleting 013 empties pattern_013.json; deleting 009_003 leaves pattern_009's other 2 detection cases intact.)

### 3. Keep pattern_019_en_001 (genuinely clean)
Input is the straight-quote *After* (`_universal.md:155`) — real human text the skill should leave alone. Stays `true_negative`. It is the lone genuine pattern-eval true-neg sanity case.

### 4. Document the over-edit signal of record + correct stale claims
- Add a note (`docs/plans/sp3b-notes.md`): pattern-eval `true_negative` cases must be **genuinely-clean human text, never the skill's own AI-tell examples** (the bug SP3b fixed); the **canonical over-edit measure is the FP eval** over the **synthetic** FP corpus `en/human/synthetic/` + `de/human/redistributable/` (multi-run via SP3a `--runs`). *(Note: the EN human corpus is synthetic, not sourced human prose — state that honestly; populating a real human corpus is future work.)*
- Correct the stale "true-neg 5/9, 2 corpus disputes (008+029)" framing to the real picture — **8/9 were the skill's own Before-examples** (revising SP1's "2 disputes" count to 8); now 5 converted to detection, 2 validate-or-gap, 1 deleted (017), 1 genuine true-neg (`pattern_019`, 4/5). Update at least `evals/reports/summary_latest_en.md:6` and `docs/plans/sp1-baselines.md` (lines 32/59/61/63 carry it). These are historical close-out docs — a one-line "superseded by SP3b" pointer at each is enough, not a rewrite.
- **Flag the SP3d overlap:** `docs/specs/2026-06-08-sp3a-multirun-harness-design.md:15` plans an "SP3d for pattern_008/pattern_029 corpus disputes" and treats "9 EN true-neg cases" as the over-edit slice — SP3b **obsoletes that** (008/029 are now detection cases; the over-edit slice is the FP eval). Add a one-line note in the SP3b doc/STATUS that SP3d's 008/029 item is subsumed here.

### 5. Validate the conversions + confirm the genuine case (quota, bounded)
Validate the **7 converted cases** (5 clean + 2 validate-or-gap; 017 is deleted, not validated) and confirm **pattern_019**, at `--runs 5`, targeted (NOT a goal — measure the conversions):
- **Mechanics:** `run_pattern_eval`'s only case filter is `--pattern <id>` (by integer pattern_id), which re-scores ALL of that pattern's cases — there is no case-level filter in the existing CLI. Per-pattern `--pattern <id> --runs 5 --force` for patterns **8, 9, 13, 14, 15, 29**. Case count actually re-scored: patterns 8, 13, 15, 29 = **1 case each** (each holds only the now-converted case — no other cases); 14 = **2** (both converted); 9 = **3** (1 converted + 2 pre-existing detection cases). Total **9 cases × 5 runs = 45 `claude -p` calls**. `--force` is mandatory (stale single-run partials for these IDs would be reused). Do NOT loop `--pattern 17` (deleted) or `--pattern 19` (true-neg, validated separately below — avoids double-scoring).
- **The validation run is a measurement, not a merge gate:** a validate-or-gap miss makes `run_pattern_eval` exit 1 (`patterns_below_threshold > 0`). That exit 1 is the *expected arbitration signal* (this tell under-detects → record-as-gap + delete), NOT a failure. The merge gate for SP3b is the **pytest suite (331 = 329 baseline + 2 new integrity tests; all green)**, independent of the eval's exit code.
- **Pass per converted case:** majority-detect (≥3/5). Clean 5 expected to pass; the 2 validate-or-gap arbitrated per Component 2.
- **pattern_019:** confirm majority-pass as true-neg (expected 4/5). Use `sp1_tn_multirun.py 5` (TN-only; reads raw corpus JSON and calls `run_skill` directly → bypasses the `_partial/` cache; after conversion it finds only pattern_019 as `true_negative`). The script takes ONE arg (N runs) — do NOT pass a lang token.

## Data flow / mechanics

True-neg cases are entries in `evals/corpus/en/patterns/pattern_0NN.json` `cases[]`. Converting = editing that entry in place (flag + `expected_changes`). **Deletions DO empty two files:** pattern_017 (1b) and pattern_013 *if* its validation fails — both have a single case, so `cases:[]` results. **A deletion must leave `"cases": []` (empty array), NOT remove the `cases` key** — `sp1_tn_multirun.py`'s `d.get("cases", [d])` fallback would otherwise treat the whole file dict as a case. The loader tolerates `cases:[]` (verified — returns 0 cases, no crash; the empty pattern is simply absent from `by_pattern`/`per_pattern`, no div-by-zero), so this is acceptable; #17 and (if dropped) #13 simply have no EN pattern-eval case, documented as not-term-scorable / a recorded gap. EN scorable-detection count rises by up to 7 (the converted cases now count toward `overall_detection_rate`), so the **EN detection baseline shifts** — post-SP3b `overall_detection_rate` is over a larger, more honest case set and is NOT comparable to v3.5.0's 0.905 (additive consequence; a full EN detection re-baseline is optional follow-up, not required to close SP3b).

## Testing (pytest, zero quota)

- No corpus-schema validator exists; validation = `load_pattern_corpus` round-trips the edited files and the **full suite stays green (331 = 329 baseline + 2 new integrity tests)**. Confirm no test asserts a specific true-neg case ID or the "9 true-neg" count (grep verified in round-1 review: none do — tests use synthetic fixtures).
- No new skill tests (no skill change). **SKILL.md byte-identical to main.**

## Success criteria

- 5 clean rows (008, 014_001, 014_002, 015, 029) converted to detection cases with the tabled `expected_changes`; pattern_017 deleted (not term-scorable); pattern_013 + pattern_009_003 resolved by their validation data (kept-as-detection OR deleted-as-recorded-gap); pattern_019 kept true_negative.
- Validation run (`--runs 5`, `--force`, per-pattern for 8/9/13/14/15/29, **45 calls** = 9 cases × 5): the 5 clean conversions reach majority-detect; the 2 doubtful arbitrated + recorded; pattern_019 majority-pass via `sp1_tn_multirun.py 5`.
- Doc note records true-neg=sanity-only + **FP eval = canonical over-edit measure** (synthetic corpus, honestly labelled); stale "5/9 / 2 disputes" claims corrected (revised to 8); SP3d 008/029 overlap flagged.
- Full pytest green (331 = 329 baseline + 2 new); SKILL.md byte-identical to main.

## Risks & mitigations

- **Goal-seeking** → avoided: conversion terms are present-in-input AND removed-in-the-doc's-own-After (falsifiable), not hand-picked passing text. The one judgment (009_003) follows the doc's on-the-table test, recorded.
- **A converted case doesn't detect** (esp. #13 passive) → not forced: recorded as a real EN detection gap or term fixed; #13 falls back to delete-with-rationale. The validation run is the arbiter.
- **EN detection baseline shifts** → expected and honest (more coverage); flagged as not-comparable to 0.905; full re-baseline is optional follow-up.
- **Stale-partial confound** in validation → `--force` on `run_pattern_eval`; `sp1_tn_multirun.py` bypasses the cache for the TN check.
- **A test asserts a converted/kept case** → grep verified none do; re-grep before editing.

## Implementation isolation & review discipline

Branch `sp3b-true-neg-corpus` off `main`; squash-merge when green. **No self-review — every diff, the reclassification, and every eval number is Skeptic-verified from primary evidence before acceptance.**
