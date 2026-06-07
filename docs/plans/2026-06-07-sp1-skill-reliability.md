# SP1 — True-Negative Restraint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. **Review rule (maintainer): no self-review — every task diff AND every before/after eval number is verified by the independent Skeptic (`AI/AGENT PERSONAS/Agents/independent-review-agent.md`) from primary evidence before acceptance.**

> **STATUS: SP1 CLOSED as metric-only (2026-06-07).** Both behavior levers were dropped by measurement (lever 1: change-log defect not reproduced; lever 2: true-neg is noise-dominated, 5/9 majority/51% per-run, no single-run-measurable fix). SP1 ships the change-log sentinel metric (Task 1) + two from-outside findings; **no skill behavior change.** True-neg work + the multi-run harness it needs → SP3. See spec "Outcome" + `sp1-baselines.md`. Tasks 3–4 below are DROPPED; Task 5 is the close-out.

**Goal (original):** Stop the skill over-editing already-clean / human-authored text — measured from outside (no model self-check). **Outcome:** the defect proved noise-dominated, not a stable single-run lever → deferred to SP3.

**Architecture:** Originally one SKILL.md behavior lever (true-negative restraint). Measurement closed SP1 to the shipped sentinel only: the `changelog_first_attempt_rate` metric (Task 1). No SKILL.md change.

**Tech Stack:** Python 3.11 stdlib + pytest; the skill is Markdown (`SKILL.md`); evals are `claude -p` (subscription) + Anthropic SDK judge (paid, key needed for e2e measurement only).

**Spec:** `docs/specs/2026-06-07-sp1-skill-reliability-restraint-design.md` (Skeptic-reviewed; re-scoped 2026-06-07 after measurement). Career FP is out of scope (deferred to SP3).

**Measurement pivot (DONE):** The change-log defect that lever 1 would have fixed was measured from outside: **1 flag / 51 runs** (DE+EN e2e). Honest read (Skeptic): this **refutes the ~1/3 premise** (33% is far outside the 95% CI [0.35%, 10.3%]) but does NOT establish a precise rate — true first-attempt rate is **≤~10%** (point 2%). Lever 1 (rewrite-first restructure) is **dropped** (no measured defect worth a shared-EN+DE Output-Format change that 306 parser-dependent tests rest on; retry already masks the residual). The metric is kept as a regression sentinel. *(Then the true-neg defect itself was re-baselined and proved noise-dominated → lever 2 also dropped; see STATUS above. SP1 ships the metric only.)*

**Worktree:** executing in-place on the isolated `sp1-skill-reliability` branch (off `main`).

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `evals/scripts/run_e2e_eval.py` | first-attempt change-log recording + `changelog_first_attempt_rate` (sentinel) | 1 (DONE, shipped) |
| `tests/test_run_e2e_eval.py` | unit-test the change-log counter | 1 (DONE) |
| `evals/scripts/sp1_changelog_probe.py` + `sp1_tn_multirun.py` | from-outside probes used for the measurements that closed SP1 | 2 |
| ~~`SKILL.md` / `tests/test_skill_structure.py`~~ | ~~true-negative restraint lever~~ — DROPPED (Task 3); no skill edit | — |

Measurement closed SP1: change-log defect not reproduced (lever 1 dropped), true-neg noise-dominated (lever 2 dropped → SP3).

---

## Task 1: Change-log sentinel metric (harness) — ✅ DONE

Shipped commit `2b0a998` (306 pytest green; Skeptic-cleared). `score_case` records per-run `first_attempt_changelog`; `run()` aggregates `changelog_first_attempt_rate`; pre-metric partials excluded (not zero-filled). Caveat (LOW, Skeptic): the metric is an *upper bound* (over-catches empty / ≥2-arrow output) — fine, since it's read identically before/after and the baseline already came out ~2%.

---

## Task 2: Baselines (measurement — quota)

**Files:** none (records numbers into `docs/plans/sp1-baselines.md`).

- [x] **Step 0: Pin install to the UNEDITED skill** — `ln -sfn "$(pwd)/SKILL.md" ~/.claude/skills/humanizer/SKILL.md`; assert `diff <(git show main:SKILL.md) ~/.claude/skills/humanizer/SKILL.md` is empty + `verify_skill_install()` OK. (DONE — install == unedited main.)
- [x] **Step 1: Change-log baseline — ✅ DONE.** Measured from outside: e2e judge runs (DE career/technical/academic ×5 = 0/15) + skill-only probe (DE 6 cases ×3 = 1/18, the hit was DE-legal; EN 6 cases ×3 = 0/18). **Pooled 1/51** → 95% CI [0.35%, 10.3%]; refutes ~1/3, true rate ≤~10% (point 2%). Premise not reproduced → lever 1 dropped (see pivot). Sentinel baseline; restraint must not *materially* inflate it (per-run flags recorded in `docs/plans/sp1-baselines.md`).
- [ ] **Step 2: EN true-negative + detection-smoke baseline (one run).** `run_pattern_eval.py` hardcodes `force_full=True` (line 213) and scores both true-negatives and detection in one pass — subscription `claude -p`, NO API key:

```bash
PYTHONPATH=. python3 -u evals/scripts/run_pattern_eval.py --lang en --model sonnet --force
# record summary.true_neg_passes  (the 9 true-neg cases; baseline ~4/9)
# record summary.overall_detection_rate  (detection SMOKE — non-gating, crater-only)
```
Resumable via per-case partials; chunk if the session limit bites. (Note: the 27-May EN partials are stale v3.4.x — `--force` re-scores them.)

- [ ] **Step 3: Record + Skeptic-verify** both numbers in `docs/plans/sp1-baselines.md` (the change-log 2% is already recorded). Confirm same-config (install pinned to unedited skill, `force_full` path). Commit the baseline note.

> Quota: sequential, resumable. Do NOT run in parallel (contention burns session limits).

---

## Task 3: SKILL.md true-negative restraint rule — ❌ DROPPED (measurement)

Not built. The 5-run re-baseline (`sp1-baselines.md`) showed the true-negative metric is **noise-dominated** (5/9 majority, 51% per-run, bimodal edit-ratios) with **zero stable behavior defects** — the 2 always-failing cases (008, 029) are both **corpus disputes** (each is the skill's own documented AI-tell Before-example; the skill flags them per its own rules), and the rest is run-to-run noise. A SKILL.md restraint rule cannot be shown to fix a metric this noisy without multi-run medians (SP3 tooling), and the fresh probe disproved the em-dash-carve-out hypothesis (em-dash→comma alone passes at ~0.04). Per *don't build on single-run noise*, deferred to SP3.

## Task 4: Measure restraint — ❌ DROPPED (no lever to measure).

---

## Task 5: Close-out, sign-off, ship the sentinel

**Files:** `evals/reports/summary_latest_*.md`, vault `STATUS.md`/`SESSION_LOG.md`/`DECISIONS.md`.

- [ ] **Step 1:** Write the SP1 result block into `evals/reports/summary_latest_de.md` (+ EN): change-log defect 1/51 (CI [0.35%,10.3%], premise refuted) → lever 1 dropped; true-neg re-baseline 5/9 majority/51% noise-dominated → lever 2 dropped → SP3. SP1 ships the change-log sentinel metric only; no behavior change.
- [ ] **Step 2: Final Skeptic sign-off** of the whole SP1 close (the two findings + the Task-1 metric diff together): is the close honest, is the noise-dominated conclusion supported by the data, no gaming? Fix anything found. *(In progress — dispatched before merge.)*
- [ ] **Step 3:** Run `/freshness` — sweep vault STATUS/SESSION_LOG/DECISIONS to the SP1 close + seed an SP3 note (true-neg + multi-run harness + career FP + corpus-dispute pattern_008 + pattern_029).
- [ ] **Step 4:** Use `superpowers:finishing-a-development-branch` — squash-merge the branch to `main` (ships: the `changelog_first_attempt_rate` harness metric + the two probe scripts + the SP1 spec/plan/baseline docs), bump patch version (plugin.json + marketplace.json; SKILL.md frontmatter only if changed — it isn't), tag, push (on explicit user OK), GH release. *Note: this is a harness/docs release, not a skill-behavior release.*

---

## Acceptance criteria (SP1 close)

- [ ] Change-log defect measured from outside (1/51, CI-honest) — premise refuted, lever 1 dropped. ✅
- [ ] True-neg re-baselined ≥5 runs — noise-dominated (5/9 majority), lever 2 dropped → SP3, conclusion Skeptic-verified.
- [ ] Change-log sentinel metric (Task 1) shipped, Skeptic-cleared, 306 pytest green. ✅
- [ ] No skill behavior change (SKILL.md unedited vs `main`); `_FINAL_RE`/parser tests green.
- [ ] SP3 hand-off seeded (true-neg + multi-run harness + career FP + pattern_008 + pattern_029 corpus disputes).
- [ ] Every finding + the metric diff Skeptic-verified (no self-review).
