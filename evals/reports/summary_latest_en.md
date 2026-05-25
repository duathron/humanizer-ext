# EN Baseline Eval Summary

**Date:** 2026-05-25
**Skill version:** humanizer v3.3.0 → about to ship as v3.4.0 (no skill behavior change in v3.4.0; only eval-infra additions)
**Skill commit at run time:** `30a9d08` (worktree-v3.4.0-eval branch, pre-release)
**Skill model:** sonnet (via `claude -p` subscription auth)
**Judge model:** sonnet (via Anthropic SDK) — **E2E NOT YET RUN** (see below)
**Reports run sequence:** pattern → false-positive → e2e

## Pattern detection

- **Overall detection rate: 0.244 (24.4%)**
- 30 of 39 patterns below 0.85 threshold
- 45 cases across 39 patterns (#23 has no seeded case — bullet-list "Before → After" syntax not matched by the seeder regex)
- Detail report: `evals/reports/pattern_en_20260525_091723.{json,md}` (not committed; per `.gitignore`)

**Per-pattern detection rates (all reported as `correct / total` per pattern):**

| 1.0 (passes) | 0.5 | 0.0 (fails) |
|---|---|---|
| #1, #3, #5, #8, #28, #29, #38, #39, #40 | #21 | #2, #4, #6, #7, #9, #10, #11, #12, #13, #14, #15, #16, #17, #18, #19, #20, #22, #24, #25, #26, #27, #30, #31, #32, #33, #34, #35, #36, #37 |

**Interpretation:** the 24.4% number is mostly a **corpus quality artifact**, not a skill quality result. The `seed_pattern_corpus.py` generator extracted `expected_changes` from the full "Words to watch" list in each pattern body — frequently 6–8 candidate terms per case, only one or two of which actually appear in the input. The `score_case` logic treats a pattern as `detected` only when ZERO `expected_changes` substrings remain in the rewrite; trigger terms that never appeared in input cannot be "removed" and silently survive in the rewrite as normal English usage, dragging the rate to 0.0 for most patterns.

The cleanly-passing patterns (#1, #3, #5, #8, #28, #29, #38, #39, #40) are those with either narrow trigger sets or chat-UI-artifact targets that never appear in legitimate prose.

**Phase 1.5 follow-up:** hand-refine `evals/corpus/en/patterns/*.json` so `expected_changes` lists only the trigger terms actually present in each `input`. Expected detection rate after refinement is well above 0.85 for most patterns.

## False-positive rate

- **Mean edit ratio: 0.8379** (target ≤ 0.10)
- 5 of 5 files above threshold
- Density preflight quick-drop rate: 0.60 (3 of 5 cases correctly identified as human-authored)
- Detail report: `evals/reports/false_positive_en_synthetic_20260525_095122.{json,md}` (not committed)

**Per-file:**

| File | Domain | Edit ratio | Density preflight quick-drop |
|---|---|---|---|
| `academic_paragraph_01.md` | academic | 1.085 | ❌ no |
| `casual_blog_draft_01.md` | casual | 0.742 | ✅ yes |
| `legal_brief_excerpt_01.md` | legal | 0.418 | ❌ no |
| `marketing_copy_01.md` | marketing | 1.246 | ✅ yes |
| `technical_docs_01.md` | technical | 0.700 | ✅ yes |

**Interpretation:** the 0.84 mean edit ratio is **dominated by a measurement bug**, not a skill regression. `parse_skill_output` returns the entire skill response (Pre-flight banner + Audit + Final blocks) as `final` when it cannot find a `**Final rewrite:**` sentinel — and in Quick-mode passes the skill writes commentary that the Levenshtein distance counts as "edits" against the input. Several `rewrite_length_chars` values (1500–1900) are nearly double the input length, confirming the parser is including non-rewrite text.

The **density preflight signal is real and useful**: 3 of 5 human-authored cases correctly downgraded to Quick mode (casual, marketing, technical). The two that did not (academic, legal) used formal hedging that the Tier-1 density check counted as inflation-adjacent. Worth investigating whether the preflight should suppress academic/legal hedging from Tier-1 counts.

**Phase 1.5 follow-up:** harden `parse_skill_output` to recognize Quick-mode boundaries (e.g., a `**Final:**` or `**Rewrite:**` line). After that fix, rerun false-positive eval to get a defensible mean edit ratio on Quick output.

## E2E rewrite quality

**Status: NOT RUN — blocked by claude CLI subscription session limit.**

The first attempt failed mid-run with `stdout: "You've hit your session limit · resets 9pm (Europe/Berlin)"`. The pattern eval (39 cases) consumed the daily quota before E2E got to run. Subscription resets nightly; re-run after reset will populate this section.

When run, the eval is `python3 -m evals.scripts.run_e2e_eval --lang en --runs 3 --model sonnet --judge-model sonnet`. Expected ≤$5 in Anthropic SDK judge calls + ~15 claude CLI skill calls (subscription).

## Interpretation

v3.4.0 ships the eval **infrastructure** with a partial baseline. Pattern detection numbers reflect corpus seeding (broad trigger lists), not skill quality. False-positive numbers reflect a known parser bug in Quick-mode output, not skill over-editing. Both follow-ups are mechanical fixes that produce defensible baseline numbers without touching skill behavior.

The infrastructure itself works: 33/33 pytest tests pass, three runners produce JSON+MD reports under `evals/reports/`, `verify_skill_install` blocks runs against stale installs (caught the v3.3.0-refactor-worktree symlink during this session), and the runner now strips `ANTHROPIC_API_KEY` from the CLI's subprocess env so the SDK-using E2E judge does not conflict with the CLI's subscription auth. Three transient/structural issues were caught and patched mid-run (retry wrap, env strip, stdout-in-error).

## Next steps

1. **Phase 1.5 (corpus refinement, before any baseline interpretation):**
   - Hand-refine `evals/corpus/en/patterns/*.json` `expected_changes` lists to terms present in input
   - Patch `parse_skill_output` to handle Quick-mode rewrite boundaries
   - Re-run pattern + FP evals to get defensible baselines
2. **Run E2E once subscription resets** to populate the third row of this summary.
3. **Pattern #23** seeded zero cases — add manually since its bullet-list `Before → After` format does not match the seeder regex.
4. **Phase 2 (DE pack)** can begin once the EN baseline is defensible. Phase 2 spec is unchanged.
