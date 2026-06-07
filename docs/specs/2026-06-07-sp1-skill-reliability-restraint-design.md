# SP1 — True-Negative Restraint (design)

**Status:** approved design, 2026-06-07, **Skeptic-reviewed twice**; **re-scoped 2026-06-07 after measurement** (see "Measurement pivot" below). Sub-project 1 of a 3-part improvement effort (SP2 = CI via shipwright onboarding; SP3 = eval rigor + **preflight calibration / career-FP** — both separate specs).

## Measurement pivot (2026-06-07) — lever 1 dropped

SP1 originally targeted **two** defects. Before building either, we shipped the change-log metric (Task 1) and **measured the change-log defect from outside**: pooled **1 flag / 51 runs** (DE+EN e2e; the one hit was DE-legal). Honest read: 1/51 → 95% CI **[0.35%, 10.3%]** — this **refutes the "~1/3 anecdotal" premise** (33% is far outside the interval) but does NOT establish a precise rate; the true first-attempt rate is **≤~10%** (point 2%). Per the maintainer rule *don't ship a claim the metric contradicts*, **lever 1 (rewrite-first restructure) is dropped** — even at the CI ceiling, a shared-EN+DE Output-Format restructure (EN extraction-regression risk to a parser 306 tests depend on) is a bad trade against a first-attempt blip that the eval's 4× retry already masks. The change-log metric is **retained as a permanent regression sentinel** (it already earned its keep by killing a bad premise). SP1 now ships the **one confirmed defect**: true-negative over-editing.

## Outcome (2026-06-07) — SP1 closes as metric-only; true-neg → SP3

After dropping lever 1, we **re-baselined the true-negative defect properly** (5 runs × 9 EN cases) before building lever 2. Result: **5/9 majority, 51% per-run, noise-dominated** — identical clean inputs yield edit-ratio ~0.0 on some runs and 0.2–2.9 on others (bimodal). The 2 cases that fail every run are **both corpus disputes**, not skill defects: each is verbatim one of the skill's OWN documented AI-tell Before-examples — `pattern_008` (#8 "serves as"/"boasts") and `pattern_029` (#29 fragmented header) — with split/dissenting meetup provenance; the skill flags them per its own rules. The rest is run-to-run noise. **Zero stable behavior defects.** Resolving the disputed rows + measuring any future restraint needs multi-run medians = SP3 eval-rigor tooling. Per the maintainer discipline *don't build on single-run noise*, **lever 2 is also dropped**; the corpus-dispute fixes and the multi-run harness move to **SP3**.

**SP1 ships:** the `changelog_first_attempt_rate` metric (Task 1) as a permanent sentinel, plus two rigorous from-outside findings (change-log defect ≤~10%/not the premised 1/3; true-neg "defect" is two disputed corpus rows + single-run noise, not a stable skill bug). **No skill behavior change.** This is a legitimate scientific outcome — the metric earned its keep by refuting two anecdotal premises before either drove a risky shared-EN+DE skill edit.

---

> ⚠️ **Everything below this line is the ORIGINAL lever-by-lever design, retained for history but SUPERSEDED by the Outcome above.** SP1 makes **no SKILL.md edit**; the "Lever — true-negative restraint", its Components/Validation/Success criteria, and the "4/9" figure below are the pre-measurement plan, not what shipped. Read them as the reasoning that the measurement overturned.

## Goal

Fix the one real, independent-review-confirmed skill defect **without a new language pack**, measured from outside (no model self-check):

1. **True-negative over-editing.** Clean / human-authored text gets rewritten when it should be left alone (EN true-negative cases: only 4/9 pass). The #1 user-facing harm — mangling good writing.

*(Dropped after measurement: output-format / change-log reliability — measured ~2%, premise not reproduced; metric kept as a sentinel.)*

## Non-goals (explicitly deferred)

- New language pack.
- **Career-domain FP (DE 0.192) → SP3.** The 2nd Skeptic pass established this is a *preflight-mechanics + corpus* problem, not in-scope here: the density preflight is a mechanical Tier-1 tell count (Bewerbung assertiveness isn't a Tier-1 tell), the documented fix is two-part (raise quick-drop **and** soften `de_overrides` to restrain in Full mode), **and** no human Bewerbung corpus exists (the career FP slice is 10 Wikipedia biographies; real Anschreiben are private/copyrighted vs. the deliberately-CC corpus). It belongs with SP3's preflight + eval-corpus work, with its own sourcing/licensing plan.
  - **Re-run note for the SP3 plan:** a corpus addition *alone* needs only the new files scored (per-file partials) + re-aggregate. But SP3's career fix is a **skill change** (preflight) → it invalidates cached partials for the affected eval, so SP3 must **re-baseline career FP on the new Bewerbung corpus** (the 0.192 on Wikipedia bios is not comparable) and **re-run the affected FP slice + the detection-regression guard** (preflight is shared EN+DE). Scoped + resumable, not the full suite — but budgeted.
- Eval-harness rigor as a *feature* (median-in-gate, ≥5-run default) → SP3. SP1 uses medians only as a validation guardrail, not as a shipped gate.
- **Noise-budgeted detection-regression guard → SP3.** The pattern runner is single-run with no `--runs`/median (verified), so a real noise-budgeted guard needs harness tooling that belongs with SP3's eval rigor. Building a coarse single-run guard in SP1 — then rebuilding the real one in SP3 — is duplicated work, and a ~40-case single-run aggregate (~8pp stderr) cannot see a small drop anyway. **SP1 instead records a single non-gating smoke number** (one forced EN pattern-slice run) whose only job is to catch a *crater* (the skill stops editing AI text), not a small drop. Rationale it's safe to defer: the restraint rule (lever 2) fires only on density-0 / no-tells inputs — by construction it does not touch actual AI text, so the detection-regression risk is low. The rigorous guard is SP3's.
- Pattern-detection consistency, Tier-4 features (voice, explain output, confidence).

## Approach

One **behavior-changing** lever + one **sentinel metric** — no model self-check (maintainer rule: a model checking itself is an unreliable self-check; behavior is verified by *measurement*).

- **Lever — true-negative restraint.** A rule at the density pre-flight: clean / human-authored input (pre-flight density 0, or no clear AI tells) is returned **(near-)verbatim as the rewrite, never as a note**; when uncertain whether something is an AI tell or the author's own voice, **leave it**. This stands alone on the existing Output Format — across the 51 probe runs the harness **extracted a usable rewrite every time** (via the `**Final rewrite:**` header *or* its fallback chain; an empty/failed extraction would have been flagged, so it didn't occur). Note the header is mandated only on the density-drop-to-Quick path, not normal Full mode — but extraction succeeding across 51 runs is sufficient evidence that lever 2's clean-rewrite output parses; no restructure is needed. (The dropped lever 1 would have re-ordered that output; measurement showed it unnecessary.)
- **Sentinel metric — changelog-emission rate (shipped, Task 1).** Independent from-outside measurement. Now a **regression sentinel**, not a fix-driver: the restraint must not *materially* inflate it above the 1/51 baseline (a single extra hit is within the ±8pp CI, not a regression).

## Components & edits

1. **`SKILL.md` — true-negative restraint rule, shared EN+DE (the lever).** At the density pre-flight `0 tells` branch (`SKILL.md:150`), add: *"If the input is already clean / human-authored (pre-flight density 0, or no clear AI tells), return it (near-)verbatim as the rewrite — do not rewrite to 'improve' it, and do not replace it with a note or 'left unchanged' message. When uncertain whether something is an AI tell or the author's own voice, leave it."* The existing density-0 branch already drops to Quick mode "to avoid over-editing voice," but EN true-neg 4/9 shows it still over-edits — this strengthens the restraint explicitly. No Output-Format restructure — extraction succeeded across all 51 probe runs (header or fallback), so clean-rewrite output parses without a new header mandate.
2. **`evals/scripts/run_e2e_eval.py` — changelog-emission metric (SHIPPED, Task 1, commit `2b0a998`).** Records the first attempt's `_looks_like_failed_rewrite` verdict per run + aggregates `changelog_first_attempt_rate`. Now a **sentinel**: it measured the change-log defect at **1/51** (95% CI [0.35%, 10.3%] — refutes ~1/3, true rate ≤~10%; premise not reproduced → lever 1 dropped), and guards that the restraint lever does not materially inflate it.

## Validation (measured, not free)

The change-log baseline is already measured (1/51 ≈ 2%; lever-1 dropped). Remaining validation is the restraint lever:

- **True-negative restraint (the lever):** EN true-negative cases (9), same frozen pass criterion, before/after → more pass (target ≥ 7/9). Baseline ~4/9.
- **Change-log sentinel (non-regression):** re-measure `changelog_first_attempt_rate` on the lever skill — restraint must not *materially* inflate it above the 1/51 baseline (the risk: "leave it" yields a note instead of the text). Noise-aware: a single extra hit is within the ±8pp CI; FAIL only on a clear jump of genuine notes.
- **Detection smoke (non-gating; rigorous guard deferred to SP3):** this project's single-case/3-run noise produced false 0.557↔0.667 swings, and the pattern runner is single-run with no median (verified) — so a small single-run slice cannot adjudicate a *small* detection drop, and building the multi-run/median harness to do so is SP3 scope. SP1 records **one forced EN pattern-slice run** (`overall_detection_rate`) before and after the lever, as a **smoke observation, not a gate**: it flags only a *crater* (rate collapses → the skill stopped editing AI text). A small within-noise movement is NOT a fail and is NOT claimed as a result. If the smoke craters → soften the restraint and re-run. The noise-budgeted guard (≥40 cases, multi-run, medians) is SP3's.
- Total ≈ one–two chunked session windows; sequential, resumable.

## Testing (pytest, zero quota)

- Changelog-counter logic — unit-tested + Skeptic-cleared (SHIPPED Task 1).
- **Structural test (anti-drift):** `SKILL.md` contains the true-negative-restraint rule (the `already clean` → `return (near-)verbatim` / `when in doubt leave it` wording), routed through the rewrite, not a note. Prevents the rule-drift class that bit v3.5.0.
- Existing `_looks_like_failed_rewrite` + `_FINAL_RE` parser tests (`test_evals_shared.py`) stay green — no Output-Format change is made, so they must not move.
- No live-skill tests — those are the evals above.

## Success criteria

- EN true-negative pass-rate ↑ (≥ 7/9), same frozen cases/criterion.
- Change-log sentinel: `changelog_first_attempt_rate` not *materially* inflated above the 1/51 baseline (±8pp CI — a single extra hit is within noise) by the restraint.
- Detection smoke (non-gating): the forced EN pattern-slice `overall_detection_rate` did not *crater* after the lever (rigorous noise-budgeted guard deferred to SP3).
- Full pytest suite green (≥ 306); `_FINAL_RE`/parser tests still green (no extraction regression — none expected, no Output-Format edit).

## Risks & mitigations

- **Restraint yields a note instead of the text** — "leave it" could produce "left unchanged because…" instead of returning the rewrite → the rule explicitly says *return it as the rewrite, never as a note*; the change-log sentinel measures it.
- **Restraint over-suppresses detection** (the v3.5.0 tension) → the SP1 detection smoke catches a crater; a *small* drop is below SP1's single-run resolution and is adjudicated by SP3's noise-budgeted guard. The restraint fires only on density-0 / no-tells inputs, bounding the risk.
- **SKILL.md change is shared EN+DE** → EN must not regress; the EN true-neg validation + the EN detection smoke + full pytest include EN.

## Implementation isolation & review discipline

A dedicated branch/worktree (per `superpowers:using-git-worktrees`) off `main`; merged via squash-to-main + tag when validation passes. **No self-review — every artifact (this spec, each task diff, each before/after eval number) is verified by the independent Skeptic (`independent-review-agent`) from primary evidence before acceptance.** Self-review steps in any sub-skill are replaced by a Skeptic dispatch.
