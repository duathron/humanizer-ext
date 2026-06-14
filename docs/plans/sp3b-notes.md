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

**Task-5 validation outcome (2026-06-09, `--runs 5`, `--force`, subscription):**

| case | detected | runs | disposition |
|---|---|---|---|
| pattern_008_en_001 | 5/5 | TTTTT | KEPT detection (clean ✓) |
| pattern_009_en_003 | refusal (2/3 re-probe) | — | **RESOLVED 2026-06-10: KEPT as detection case → now honestly `inconclusive`** under the scorer-guard (refusal→None). Was a false "5/5" pre-guard. Recovery = deferred skill-refusal fix. |
| pattern_013_en_001 | refusal (3/3 re-probe) | — | **RESOLVED 2026-06-10: KEPT as detection case → now honestly `inconclusive`** under the scorer-guard. Was a false "5/5" pre-guard. #13 has no scorable EN data until the skill fix. |
| pattern_014_en_001 | 5/5 | TTTTT | KEPT detection (clean ✓) |
| pattern_014_en_002 | 4/5 | TFTTT | KEPT detection — majority (the 8/1/0-endorsed row; 1 miss = noise, now confirmed) |
| pattern_015_en_001 | 4/5 | TTTTF | KEPT detection — majority |
| **pattern_029_en_001** | **1/5** | FTFFF | **DELETED** — contested #29 tell (doc says edit; meetup 2/2/5 + skill behavior 1/5 say leave). Skill-design/doc question deferred — see `pattern_029.json` note. |
| pattern_019_en_001 | (true-neg) 4/5 pass | 0,0,1.745,0,0 | KEPT true-neg — majority-pass; 1 spike = known noise |

**Net (CORRECTED 2026-06-09):** Only 4 conversions are confirmed real detections (008, 014_001, 014_002, 015 — verified real rewrites). The 2 "validate-or-gap" rows (013, 009_003) "5/5" were **refusal artifacts** — the skill refused and the detection scorer counts an absent tell as detection (a real **scorer bug**). 029 deleted (contested). 019 true-neg kept.

## RESOLVED (2026-06-10) — closed after the scorer-refusal-guard merged

The scorer-refusal-guard (`29702db`, merged to main) fixed the root scorer bug: a refusal output → `None` run → the case goes **`inconclusive`**, never a false detection. SP3b rebased on main (dropped its stranded overlap-fn commit `172cdfb` — the guard went phrase-only). **Final disposition of 013/009_003: KEPT as detection cases — NOT deleted.**

- Why keep, not delete: they ARE the skill's own documented Before-examples (013 = #13 passive, 009_003 = #9 rather-than) — *valid* detection inputs. The skill refuses them only because they're SHORT and the `force_full` override crowds the input (the deferred skill-hallucination bug). Under the fixed scorer they now correctly score **inconclusive** (the eval honestly says "couldn't get a usable rewrite"), not a false 5/5. Deleting would HIDE the skill bug; keeping SURFACES it (the EN pattern eval will show 013 + 009_003 as inconclusive until the skill-refusal-on-short-input is fixed). Recovery = the deferred skill fix, NOT a corpus edit.
- **Consequence:** the EN pattern eval will report 013 + 009_003 in `inconclusive_cases` (→ `is_complete=False`, exit 1) until the deferred skill bug lands. This is honest, not a regression — those cases genuinely cannot be scored while the skill refuses them. **[SUPERSEDED 2026-06-14: bug fixed; both now score 5/5, `inconclusive_cases=[]`, `is_complete=True`.]**
- **Coverage:** #9 keeps 2 real detection cases (009_001/002). #13's only case (013) was inconclusive at the time of this note → #13 had no *scorable* EN detection data until the skill fix. **[SUPERSEDED 2026-06-14: the fix landed (commit `d8c5aa5`); 013 now scores 5/5 detect — see the "RESOLVED (2026-06-14)" section below.]** #17 deleted (Title-Case not term-scorable). #29 deleted (contested). 019 = lone genuine true-neg.

**Net: SP3b closes as a corpus-integrity fix** — 8 mislabeled true-neg rows reclassified (5 detect, 2 honestly-inconclusive, 1 deleted-unscorable[017]), 029 deleted (contested), 019 kept. No skill change. The integrity test (`tests/test_corpus_true_negative_integrity.py`) locks the corrected state (only 019 is true_negative; the conversions have their expected_changes).

**Open skill-design question (for a future sub-project, NOT SP3b):** is a one-sentence-paragraph warm-up ("Speed matters.") a #29 fragmented-header tell? The doc says yes; the meetup (5/9) and the skill's actual behavior (1/5 removal) say no. Resolve by deciding the #29 rule + reconciling `_universal.md:40`, then re-add a corpus case matching the decision.

## RESOLVED (2026-06-14) — the deferred short-input refusal is fixed; 013 + 009_003 recovered

The deferred skill-refusal-on-short-input was traced to the **eval-only** prompt builder `_build_humanizer_prompt`: on `force_full=True` the ~140-char override line crowded short inputs, so the skill hallucinated a refusal. A powered A/B (15 EN short cases) picked variant **V1** (add a `Text to humanize:` label before the body, override line kept in place): V0 current 15.6% refusal → V1 0/45 observed (≤8% 95% CI); the two refusing cases driven 5/5→0/5. Fix = commit `d8c5aa5` (one line in the force_full branch; `force_full=False` byte-identical; SKILL.md/patterns/domains unchanged — **no skill behavior change**). Both the diff and the A/B numbers were independent-Skeptic verified.

**Recovery (re-baseline runs=5, --force, subscription; Skeptic-verified from per-case partials 2026-06-14):**
- `pattern_013_en_001` → **scored, detected 5/5, NOT inconclusive** (real rewrite). #13 has scorable EN detection data again.
- `pattern_009_en_003` → **scored, detected 5/5, NOT inconclusive**.
- **EN pattern eval: `is_complete=True`, `inconclusive_cases=[]`** — the permanent exit-1 from these two is gone. Overall detection 0.938 (45/48 true-positive; 019 the lone true-neg). 3 patterns <0.85, 15 flaky (run-to-run variance, each still a definite majority verdict — flaky ≠ inconclusive).
- **DE pattern eval (140 cases): `is_complete=True`, `inconclusive_cases=[]`**, detection 0.907 (127/140). 10 patterns <0.85, 39 flaky. No new refusals introduced by V1.

**Not comparable to pre-fix numbers (acknowledged confound):** the reshape can shift *how* the skill rewrites, not only *whether* it refuses — these are the new honest baseline, superseding (not "correcting") the prior figures. The old "5/5" for 013/009_003 were refusal artifacts; these new 5/5 are genuine rewrites.
