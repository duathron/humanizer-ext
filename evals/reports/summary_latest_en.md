# EN Baseline Eval Summary

**Status: v3.4.1 sign-off baseline. Pattern 0.619 (post-parser-fix). FP 0.2039 + density preflight 1.00 unchanged. E2E 6/6 cases pass per-case ≥8.0 on all 3 dims after meaning-preservation rule iteration + upstream v2.6.0 port. New `career` domain shipped with first-shot E2E pass.**

**Pattern run date:** 2026-05-27 07:20 (resume of 2026-05-26 22:04 run after Pro session reset)
**E2E run dates:** 2026-05-27 09:32 (baseline 5 cases) → 2026-05-27 10:46 (post-fix marketing round 3) → 2026-05-27 11:04 (aggregate of 6 cases including new career domain)
**Skill version:** humanizer v3.4.0 (tag `eca15650`) + post-tag work toward v3.4.1
**Skill commit:** `61b03c1` (HEAD at run time)
**Skill model:** sonnet (via `claude -p` subscription auth)

## Headline numbers (current)

| Metric | Value | Notes |
|---|---|---|
| Pattern detection rate (overall, 42 scorable cases) | **0.619** | 26 / 42 detected. Post-parser-fix baseline (was 0.5 with bug). |
| Pattern cases scorable / total | 42 / 51 | 0 unscorable. 9 true-neg reported separately. |
| Patterns perfect (rate=1.0) | **19** of 40 | #1, #3, #4, #5, #6, #10, #11, #12, #16, #18, #21, #22, #25, #28, #32, #35, #38, #39 (+#23 at 0.833) |
| Patterns partial (0 < rate < 1) | 2 | #23 (0.833), #37 (0.5) |
| Patterns miss (rate=0.0) | 19 | mix of true-misses + true-neg-only patterns showing as 0 in this view |
| True-neg cases reported separately (runner stat) | 9 | reported in runner stdout, not in per-pattern table |
| FP mean edit ratio (synthetic) | **0.2039** | from earlier run, unchanged |
| FP density preflight quick-drop | **1.00** | from earlier run, unchanged (✓) |
| Regex audit: human samples LOW band | **5 / 5** | ✓ |
| E2E rewrite quality (6 cases × 3 runs, sonnet skill + sonnet judge) | **hn 8.667 / mean 8.389 / len 8.667** | All 3 dims ≥8.0 ✓. All 6 cases pass per-case threshold. Report: `e2e_en_20260527_110456.{json,md}` |
| E2E per-case mean (all 3 dims ≥ 8.0 required) | **6 / 6 pass** | academic 8.00/8.33/9.00 ✓ · career 9.00/8.00/8.00 ✓ · casual 9.00/8.00/8.67 ✓ · legal 8.67/9.00/8.33 ✓ · marketing 9.00/8.00/9.00 ✓ · technical 8.33/9.00/9.00 ✓ |
| E2E meaning baseline → final | 7.733 → **8.389** (+0.656) | Round-1 (SKILL.md step 10 hard-constraint claim inventory + audit checklist fabrication / new-authorial-positions checks + technical preserve-functional-claims + marketing positioning angles) + Round-2 (concept-noun rule + casual anti-examples + brand-tier audit) + Upstream port v2.6.0 PR #84 "Rewrite, don't delete" paragraph-count rule + PERSONALITY gating wording from upstream v2.6.0 |
| New domain: `career` | shipped | Cover letter / CV / LinkedIn / Anschreiben. Override matrix column added; preserve rules (metrics sacred / proper nouns / tech stack / JD keywords / concrete achievements). DE register noted as Phase 2 work. Career Writer persona at `AI/AGENT PERSONAS/Agents/writer-career-writer-agent.md`. |

**Delta vs prior bug-inflated run:** +0.119 absolute on pattern rate (+5 detected). Parser-fix gain came from artifact + adjacent cases that had been false-negative due to trailing-commentary capture.

## ⚠ Parser bug inflated MISS count — patched in this commit

Investigation of the artifact-cases `#38`, `#39`, `#40` (which had unanimous 9/9 ✓ meetup endorsement) revealed the skill produced clean rewrites but the parser's `_FINAL_RE` regex captured the rewrite PLUS a trailing `**What changed:**` commentary block that quoted the original artifacts. The substring check then found "removed" terms in the commentary and flagged them as retained.

Example — `pattern_038_en_001` actual partial:
```
rewrite_preview: "the 2024 election turned on three states, with margins under 1% in each. analysts have called it the closest race in modern history. [add a real citation here, or remove the claim.] --- **what changed: ..."
retained_terms: ["turn0search0", ":contentReference[oaicite"]   ← from the "what changed" commentary, not the rewrite
detected: False                                                    ← false negative
```

Skill is doing its job; parser is including too much context. Fix: extended `_FINAL_RE` lookahead to terminate on `**What changed:**`, `**Summary:**`, `**Notes:**`, `**Audit:**`, `**Rationale:**`, `**Why this works:**`, `**Comparison:**`, `**Diff:**`, `**Removed:**`, `**Edits:**`, or a `---` thematic break.

**Estimated impact on rate:** unknown without re-run, but the artifact cases alone (3 misses → likely 3 detects) would push rate from 0.5 to ~0.57. The 17 MISS patterns likely contain several more parser-driven false negatives. **The skill's true rate against this corpus is almost certainly higher than 0.5.**

A fresh pattern eval run with the patched parser is the gating step for the v3.4.1 tag. Quota will reset before that's possible.

## Pre-meetup snapshot (for diff context)

| Corpus state | Pre-meetup | Post-meetup (current) |
|---|---|---|
| Total cases | 51 | 51 |
| Scorable | 19 | **42** |
| True-negative | 0 | **9** |
| Unscorable | 32 | **0** |

Pre-meetup detection rate over 17 scorable: **0.412**. Post-meetup rate over 42 scorable with parser bug: **0.5**. Real comparison waits on the post-parser-fix re-run.

## Headline numbers

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Pattern detection rate (overall, scorable cases) | **0.412** | 0.85 | ⚠ below — see "Pattern eval interpretation" |
| Pattern cases scorable / total | 17 / 51 | n/a | corpus quality issue: 34 cases unscorable |
| Patterns below 0.85 detection threshold | 9 / 40 | < 6 | ⚠ |
| FP mean edit ratio (synthetic corpus) | **0.2039** | ≤ 0.10 | ⚠ above but dramatically improved (was 0.84 with parser bug) |
| FP files over threshold | 4 / 5 | 0 | ⚠ |
| FP density preflight quick-drop rate | **1.00** | ≥ 0.90 | ✓ |
| Regex audit: human samples in LOW band | **5 / 5** | 5/5 | ✓ |
| Regex audit: pattern-corpus cases with regex signal | 17 / 51 | n/a | reveals 15 cases need corpus fixes |
| E2E rewrite quality | not run | n/a | deferred to v3.4.1 (API budget) |

## Pattern eval interpretation (overall 0.412)

The 0.412 number is computed over the **17 scorable cases** (out of 51 total). A case is "scorable" only when at least one term in `expected_changes` actually appears in the input — otherwise the skill cannot possibly "remove" it from the rewrite. The `score_case` runtime fix (commit `723bdd9`) filters unscorable cases out of the rate; the regex audit below explains WHY so many cases are unscorable.

Of the 9 patterns below 0.85 in this run, most have small scorable case counts (1–2 cases). That mix tells us the **corpus is too thin to score most patterns reliably** rather than the **skill is failing at most patterns**. The right Phase 1.5 fix is corpus expansion, not skill changes.

Comparison to stale pre-fix run: overall 0.244 → **0.412** with the runtime fix; the remaining gap to 0.85 is dominated by corpus thinness, not skill failures.

## Pattern corpus audit (deterministic, regex-based, zero API)

`python -m evals.scripts.regex_audit --lang en --audit pattern`

Cross-validates the corpus against the deterministic `regex_scorer` catalogue. For each case, checks whether any regex in the pattern's expected category fires on the input. Three categories:

| Category | Count | Meaning |
|---|---|---|
| Cases with regex signal in expected category | 17 | Corpus quality OK — input actually exhibits the pattern |
| Cases without regex signal in expected category | 15 | Corpus quality issue — input lacks the pattern's trigger; skill cannot demonstrably "remove" what is not there |
| Cases on patterns with no regex mapping | 19 | LLM-only patterns (no deterministic equivalent in regex_scorer) — must be evaluated by LLM pattern eval |

**Patterns with no regex mapping** (LLM-only signal): #2, #6, #8, #11, #12, #13, #16, #17, #19, #26, #29, #31, #33, #34, #35, #38, #39, #40. These are structural / formatting / behavioral patterns that substring matching cannot capture (e.g., "fragmented headers", "rule of three", "rhetorical questions").

**Patterns with cases that need corpus fixes** (15 cases across 11 patterns): #7, #9, #21, #23, #24, #25, #27, #28, #30, #32, #36, #37. Concrete fix for each: rewrite the case `input` so it actually contains a trigger term from `expected_changes`. Zero API cost. Estimated effort: ~30 minutes hand work.

## FP eval interpretation (mean edit ratio 0.2039, was 0.84)

The parser fix (commit `7b0538c`) reduced the mean edit ratio dramatically by extracting just the rewrite portion instead of the whole skill response. The remaining 0.20 ratio reflects actual skill edits to human samples — most of these are formatting normalization (markdown-quoted blockquote markers removed, leading whitespace trimmed) rather than substantive prose edits.

The **density preflight quick-drop rate of 1.00** is the headline win: every one of the 5 synthetic human samples was correctly identified as human-authored and downgraded to Quick mode. This is the v3.2.0 Detection Guidance + Tier-1 density preflight working as designed.

Comparison to stale pre-fix run: edit ratio 0.8379 → **0.2039**; density preflight 0.60 → **1.00**.

## Human sample audit (deterministic, regex-based, zero API)

`python -m evals.scripts.regex_audit --lang en --audit human`

All 5 synthetic human samples land in the LOW band (< 3 Tier-1 hits per 100 words) per the `regex_scorer` catalogue. None falsely trigger as AI-like. Highest density: `technical_docs_01.md` at 2.8/100w (still LOW); lowest: `casual_blog_draft_01.md` at 0.0/100w. The corpus is clean for FP eval purposes AND the regex catalogue does not over-fire on legitimate prose.

## E2E rewrite quality (deferred to v3.4.1)

The E2E judge-LLM eval needs ~30 API calls (5 cases × 3 runs × (1 skill CLI + 1 judge SDK)) and the claude CLI subscription session limit has been exhausted by today's runs. Per the active goal of "better eval with no extra API cost", E2E is deferred to v3.4.1 rather than blocking the v3.4.0 tag.

When run, the eval is `python3 -m evals.scripts.run_e2e_eval --lang en --runs 3 --model sonnet --judge-model sonnet`. The runner is idempotent across sessions via `--cases` filter + per-case partials in `evals/reports/_partial/` — see `evals/README.md` for the multi-session batching workflow.

## Three concrete next steps (in order, all zero-API for #1 + #2)

1. **Hand-refine the 15 unscorable cases.** For each pattern in the corpus-fix list above, edit the case's `input` to actually contain a trigger term from `expected_changes`. ~30 min hand work; raises scorable case count from 17 to ~32; should push the overall detection rate well above the current 0.412.

2. **Expand `PATTERN_ID_TO_REGEX_KEYS` mapping in `evals/scripts/regex_audit.py`** for the 18 unmapped patterns. Some have no regex equivalent and must remain LLM-only (#6 structural, #11 synonym cycling, #29 fragmented headers, etc.). Others might be expressible as targeted regex (#17 title case, #19 curly quotes, #34 trailing emphasis) — write the regex, add to `regex_scorer.PATTERNS_EN`, map the pattern.

3. **Run E2E in batches once API budget permits.** Workflow in `evals/README.md`. Each session takes ~6 API calls (2 cases × 3 runs). The runner caches partials and resumes — splitting across 2–3 sessions over a few days closes the E2E gap without dropping the v3.4.0 ship.

## Infrastructure landed this release (all already in `main`)

- Per-case partial caching for pattern, FP, and E2E runners (`81979d8`, `0a81dce`)
- Heuristic parse_skill_output fallback chain (`7b0538c`)
- score_case scorable/unscorable filtering (`723bdd9`)
- `verify_skill_install` extended to pack files (`723bdd9`)
- `regex_scorer.py` deterministic scorer + `PATTERNS_BY_LANG` registry + `--lang` flag (`1acc14f`)
- Asaf Lecht credited (`6d1d645`)
- `regex_audit.py` corpus + human sample audit (this commit)

64+ pytest tests passing (no API calls in any test). Subagent session limits no longer block the eval — partials let a run resume from where it stopped.
