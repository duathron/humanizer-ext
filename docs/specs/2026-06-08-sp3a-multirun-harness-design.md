# SP3a — Multi-run-median eval harness (design)

**Status:** approved design, 2026-06-08, **Skeptic-reviewed** (3 BLOCKERs + 3 MAJOR fixed in this revision). First sub-project of SP3 (eval rigor). Unblocks SP3b (true-neg restraint) and SP3c (career FP) by making the noisy single-run evals produce stable, noise-aware numbers.

## Goal

The pattern and false-positive eval runners are **single-run**, so per-case verdicts are noise-dominated — SP1 proved this (the same clean input passed 5/5 on some cases and 0/5 on others; "true-neg 4/9 → 6/9 → 5/9" were all the same noise). **No skill-behavior fix can be measured on a ruler that swings.** SP3a adds multi-run + median/majority aggregation to both runners so a fix's effect is distinguishable from run-to-run noise.

This is **eval-infrastructure only — no skill behavior change**, no CI wiring (SP2), no corpus/behavior fixes (SP3b/c/d).

## Non-goals (explicitly deferred)

- **`run_e2e_eval` changes** — it already has `--runs` + median (the partial template); SP3a does not touch it.
- **CI wiring** → SP2 (shipwright onboarding) consumes this harness later.
- **Behavior/corpus fixes** — true-neg restraint (SP3b), career FP (SP3c), `pattern_008`/`pattern_029` corpus disputes (SP3d) come after, *using* this harness.

> SP3b (2026-06-08) subsumes the planned "SP3d pattern_008/029 corpus disputes" — 008/029 are now detection cases; the over-edit slice is the FP eval, not the 9 true-neg cases.
- **Per-run resume / top-up** — explicitly NOT built (see Components §resume). Resume stays at **case granularity**: a case writes its partial only after all N runs finish, so an interruption mid-case (session limit on run 3 of 5) loses that case's prior runs and redoes all N next session. **This is a real resumability regression vs the current single-run-per-case partial** — bounded (≤N−1 runs lost per interruption, ~one interruption per session window), accepted as the cost of not building per-run partials. Routine runs should slice to keep a session within budget.
- **Parallelism** — sequential, quota-safe.
- **min/max spread reporting** — redundant with per-case passed-fraction; not built.

## Signal → runner map (corrected from the first design; verified against the corpus)

| Need | Runner | Cases |
|---|---|---|
| EN detection stability | `run_pattern_eval` | 51 EN cases (40 files) |
| EN true-negative (over-edit) stability | `run_pattern_eval` | 9 EN true-neg cases |
| **DE + EN over-editing on clean human text** (incl. **career FP** for SP3c) | `run_false_positive_eval` | EN 5 synthetic + **DE 30 redistributable** (incl. `wikipedia_career/` 8 = SP3c target) |

**Load-bearing fact:** **DE pattern corpus has 0 true-negative cases** (verified). The DE over-edit / true-neg signal SP3b needs lives in the **FP runner over `de/human/redistributable/`**, NOT in pattern true-negs. This is why both runners are in scope.

## Components & edits

### 1. `evals/scripts/_shared.py` — pure aggregation function (the no-drift core)

A pure, unit-tested function so the policy cannot diverge between the two runners (which the user chose to extend in place rather than share wholesale). I/O and the per-case loop stay duplicated per runner; only the math is shared.

```
aggregate_runs(values: list[float | None], *, threshold: float | None = None,
               kind: Literal["continuous", "binary"], n_target: int) -> dict
```
- `values`: per-run outcomes for ONE case. `None` = a failed/timed-out run.
- Drops `None`s → `successes`. **Inconclusive** if `len(successes) < ceil(n_target / 2)`.
- `kind="continuous"` (edit_ratio): `median` = median of successes; `verdict = median <= threshold`; `fraction = None`.
- `kind="binary"` (detection / true-neg-pass as 1.0/0.0): `fraction = mean(successes)` (the stability signal); `verdict = majority = (count(==1.0) >= ceil(len(successes)/2))` (the gateable verdict); `median = None`.
- **Return-dict contract (both kinds populate the same keys; unused ones are `None`):**
  `{"verdict": bool | None, "median": float | None, "fraction": float | None,
  "passed_fraction": "k/n_success", "n_success": int, "n_fail": int,
  "inconclusive": bool, "flaky": bool}`
  where `k` = count of successful runs on the pass side for **both** kinds — binary: `count(==1.0)`; continuous: `count(edit_ratio <= threshold)`. For continuous, `passed_fraction` (count-below) is a reporting field and **may disagree with `verdict`** (median-below) — e.g. 2/5 runs under threshold yet median over it; they are different statistics, `verdict` is the gateable one. Don't treat them as equal.
  `inconclusive = n_success < ceil(n_target/2)` → then `verdict = None`.
  `flaky` = the successful runs disagreed (computed from per-run values, not the verdict): for `binary`, `0 < count(==1.0) < n_success`; for `continuous`, the successes straddle the threshold (`min <= threshold < max`). Inconclusive cases are not separately marked flaky.

### 2. `evals/scripts/run_pattern_eval.py` — `--runs N` (default 5)

- `--runs` arg threads to `run()` → `score_case`.
- `score_case` runs the per-case scoring **N times** (preserving the existing `force_full=True` for detection cases / `force_full=False` for true-neg cases — each of the N runs uses the same mode the case already dictates). **Each of the N `run_skill` calls is wrapped in its own try/except** (`subprocess.TimeoutExpired` and `SkillRunError`) with a **mandatory session-limit carve-out:** if `_is_session_limit_error(exc)` is true, **re-raise** (propagate) so `run()`'s existing case-level `_is_session_limit_error` break still fires and stops burning Pro-plan quota. (`run_e2e_eval` lets *all* `run_skill` exceptions propagate, no None-run path; SP3a propagates **only** session-limit and swallows other failures to `None` — a selective carve-out, not an exact copy of e2e.) Note `run_skill`'s internal `retry_with_backoff` retries even a session-limit error 3× before it propagates (pre-existing in the shipped code; SP3a adds no extra retry); the break still fires on the first propagating case, bounding the waste to ~one 3-retry per session window. Moving session-limit detection into `retry_with_backoff` to make it prompt is out of scope (note for SP2). Only a **non-session** timeout/`SkillRunError` appends `None` to that case's run list (the change from today, where any such exception escapes `score_case` and `run()` dumps the whole case into `failed`). Per successful run it collects `detected` / `passes_true_negative`'s underlying `edit_ratio` (true-neg feeds **per-run `edit_ratio`** to `aggregate_runs(kind="continuous")`, never the pass-bool) plus `terms_present`/`terms_removed`.
- Per-case partial gains `runs: [...]` (list of per-run dicts; `None` for failed runs) + the `aggregate_runs` result. **Atomic per case** (all N run inside one `score_case`; partial written once; resumed wholesale unless `--force`).
- **Aggregate summary changes:**
  - `overall_detection_rate` is computed from **majority verdicts** (keeps the old name + a binary all-or-nothing shape) — AND a new **`overall_detection_fraction`** (mean of per-case `fraction`) is the real stability signal. **Honesty note:** the majority rate is a *different, more stable statistic* than the single-run v3.5.0 0.864/0.952 — those were the noisy numbers this harness replaces; **not directly comparable** (a 2/5-flaky case that passed its lone v3.5.0 run flips to a miss under majority).
  - `true_neg_passes` = count of true-neg cases whose **median edit_ratio ≤ 0.10** (the `aggregate_runs(kind="continuous")` verdict).
  - `per_term_removal_rate` (restated to be computable per-case, then aggregated): each case contributes its **median-over-runs `terms_removed`** and **median-over-runs `terms_present`**; the corpus rate = `Σ(median_removed) / Σ(median_present)` across scored cases. (No cross-case run-index alignment — that was not implementable with atomic-per-case partials.)
  - New buckets: `flaky_cases` (case_ids where `flaky`) and **`inconclusive_cases`** — its OWN bucket, distinct from `failed`: an inconclusive case **ran all N, completed, has a partial, and is skipped on resume** (re-running burns N quota for the same unstable result), whereas `failed` means "threw, no partial, retried next run." Both set `is_complete=False` / exit 1, but `inconclusive_cases` is reported separately so the "unstable case" signal isn't laundered into generic failure. The `main()` "will retry on re-run" message applies only to `failed`. **Note `is_complete=False` is now overloaded:** for an inconclusive case it is *terminal* (the case has a partial and won't be re-run without `--force` / a corpus fix), not a resume signal. `main()` must distinguish "resumable (`failed`/`skipped_no_partial`/`session_limit_hit`)" from "terminal-unstable (`inconclusive_cases`)" in its summary so a reader isn't told to "re-run to finish" a run that's as finished as it'll get.

### 3. `evals/scripts/run_false_positive_eval.py` — `--runs N` (default 5)

- `--runs` arg threads through. Per clean file, run N times, each `run_skill` call wrapped in its own try/except **with the same session-limit carve-out** (`_is_session_limit_error` → re-raise so `run()`'s break fires; only non-session timeout/`SkillRunError` → `None` run); collect per-run `edit_ratio`.
- **One verdict rule (continuous):** `aggregate_runs(kind="continuous", threshold)` → file fails iff **median(edit_ratio) > threshold**. Report per-file `median_edit_ratio`. Keep `mean_edit_ratio` as a **same-name multi-run analog (mean over files of each file's median)** — **NOT directly comparable** to the single-run baselines (DE 0.1376 / EN 0.204); it's the multi-run version, reported for shape continuity, not equivalence.
- `files_over_threshold` counts files whose **median** exceeds threshold. `flaky_files` + **`inconclusive_files`** (own bucket, same semantics as `inconclusive_cases` above: ran all N, has a partial, skipped on resume, exit 1 — distinct from `failed`).
- Per-file partial gains `runs: [...]` (`None` for failed runs); atomic per file; resumed wholesale unless `--force`.

## Data flow

`--runs N` → `run()` per case/file → `score_case` runs skill N times (each run = one `run_skill` call; `run_skill` already internally retries 3× on exception — SP3a adds NO extra retry) → list of per-run outcomes → `aggregate_runs` → per-case partial (`runs:[...]` + aggregate) → `run()` rolls per-case verdicts into the summary.

## Failure handling

- A run that raises a **non-session** `subprocess.TimeoutExpired` (after `run_skill`'s internal 3× retry) or `SkillRunError` is caught **inside `score_case`'s run loop** and recorded as a `None` outcome for that run. **No retry-to-success** — total attempts per case = N, full stop (bounds the worst-case wall-clock: a pathological case is N × up-to-3×timeout, not unbounded).
- **Session-limit exception is the exception to the exception:** if `_is_session_limit_error(exc)` is true, `score_case` **re-raises** it so `run()`'s existing case-level break stops the whole run (Pro-plan quota guard). A session limit mid-case aborts that case with no partial → redone next session (consistent with the per-case-atomic resume in Non-goals). A session-limit error is NEVER recorded as a `None` run.
- Case **inconclusive** if successful runs < ⌈N/2⌉ → goes to the dedicated `inconclusive_cases` bucket (writes a partial, skipped on resume, sets `is_complete=False`, exit 1) — **distinct from `failed`** (which is "threw before any partial, retried"). Never silently pass or fail, and never re-burns N quota on a known-unstable case.

## Quota & slicing (corrected counts)

Full ×5: pattern 191 cases (51 EN + 140 DE) + FP 35 files (5 EN + 30 DE) = ~1130 `claude -p` calls — a budgeted occasional baseline, NOT routine. The runners already support per-case partials + `--lang` + `--pattern`; SP3a adds nothing here but the spec mandates **routine runs use a slice** (e.g. `--lang en --pattern <id>`, or the 9 true-neg cases, or the 8 `wikipedia_career` files). Sequential; resumable across session windows.

## Testing (pytest, zero quota)

- **`aggregate_runs` unit tests** (the core): continuous median + threshold verdict; binary fraction + majority; inconclusive when <⌈N/2⌉ succeed; `None`-run exclusion; flaky detection (3/5 → flaky, 5/5 → not, 0/5 → not); empty/all-failed → inconclusive.
- **Pattern runner tests** (monkeypatch `run_skill` like SP1 Task-1 / `REPO_ROOT=tmp` on-disk corpus): N runs collected; per-case partial carries `runs:[...]`; `overall_detection_rate` (majority) vs `overall_detection_fraction` differ on a 3/5 case; `true_neg_passes` uses median edit_ratio; `per_term_removal_rate` = `Σ(median_removed)/Σ(median_present)`; **a non-session run that raises `TimeoutExpired` becomes a `None` run (case not aborted)**; **a `_is_session_limit_error` mid-case is re-raised (propagates, breaks the run) — NOT a `None` run** (asserts the quota guard survives); a case with <⌈N/2⌉ successes lands in `inconclusive_cases` (own bucket, partial written, skipped on resume) — NOT in `failed`.
- **FP runner tests:** median-per-file verdict; a bimodal file (3×0.04, 2×0.40 → median 0.04 pass; 2×0.04, 3×0.40 → median 0.40 fail); `files_over_threshold` median-based; inconclusive handling.
- **Resume test:** a cached per-case partial (with `runs:[...]`) is reused wholesale; `--force` redoes.
- Existing pattern/FP/e2e tests stay green (306 baseline); e2e untouched. **Re-point/annotate the two stale timeout tests** (`tests/test_run_pattern_eval.py::test_pattern_run_per_item_timeout_continues_and_records_failure` and `tests/test_false_positive_eval.py::test_fp_run_per_item_timeout_continues_and_records_failure`): they monkeypatch the *score* fn to raise `TimeoutExpired` and assert `summary['failed']` — under SP3a a real per-run timeout becomes a `None` run *inside* score, so these now exercise a path multi-run scoring no longer reaches. Update them to assert the new None-run/inconclusive behavior so "306 stay green" isn't over-claiming coverage.

## Success criteria

- Both runners accept `--runs N` (default 5); `score_case` runs the skill N times per case/file.
- `aggregate_runs` is a pure, unit-tested function in `_shared.py`; both runners use it (no policy drift).
- Pattern summary reports majority `overall_detection_rate` + `overall_detection_fraction` + median-based `true_neg_passes` + median `per_term_removal_rate` + `flaky_cases` + `inconclusive_cases`.
- FP summary verdicts on median(edit_ratio) per file; reports `flaky_files` + `inconclusive_files`.
- Inconclusive (<⌈N/2⌉ successful runs) → dedicated `inconclusive_cases`/`inconclusive_files` bucket (own state, partial written, skipped on resume, exit 1), never silent pass/fail and never aliased onto `failed`.
- Full pytest green (≥306 + new); e2e runner + its tests unchanged.
- A demonstrable noise read (structural, not a fixed count): running the 9 EN true-neg cases at `--runs 5` **surfaces and lists the flaky cases** (`flaky_cases` non-empty, per-case `passed_fraction` shown) — proving the harness exposes the run-to-run disagreement single-run scoring hid. *(The exact majority count may vary run-to-run — that IS the noise; the criterion is that flakiness is surfaced, not a specific X/9.)*

## Risks & mitigations

- **Partial-shape change breaks existing consumers.** Pattern/FP partials gain `runs:[...]`; the `by_pattern`/`per_pattern`/`per_file` aggregations must read the new aggregate fields. → tests assert the full summary shape; old single-run partials are incompatible → `--force` (or clear `_partial/`) on first multi-run; document it.
- **Duplication drift (pattern vs FP).** The aggregation math is shared in `_shared.py` (`aggregate_runs`); only I/O loops duplicate. The drift-prone part is centralized + unit-tested.
- **Quota blowout** if someone runs full ×5 routinely. → spec mandates slicing for routine runs; full baseline is budgeted/occasional.
- **`overall_detection_rate` is a renamed-in-place statistic, NOT comparable to v3.5.0.** Keeping the old name avoids breaking report consumers, but a 5-run majority rate ≠ the single-run 0.864/0.952 (those were noisy single samples — the whole reason for SP3a). The spec/reports must state "not directly comparable to the single-run baseline"; the `overall_detection_fraction` is the honest stability signal. Do not claim the new number reproduces/validates the old one.

## Implementation isolation & review discipline

Branch `sp3a-multirun-harness` off `main`; squash-merge when green. **No self-review — every task diff + the `aggregate_runs` semantics + any eval number is verified by the independent Skeptic (`independent-review-agent`) from primary evidence before acceptance.** Self-review steps in any sub-skill are replaced by a Skeptic dispatch.
