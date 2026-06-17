# Commentary-fence probe results (Phase 2 Task 4) — PARTIAL, blocked on weekly quota

**Date:** 2026-06-17. **Status:** ON condition partially run; OFF condition + remaining reps **BLOCKED** — `claude -p` weekly limit hit ("You've hit your weekly limit · resets 4am Europe/Berlin"). Resume after the weekly reset.

## ON condition (directive present, SKILL.md @ 1439502) — partial

12 entries logged before the limit (`/tmp/fence_probe_on.log`): `de_clean_pflege` ×5, `en_clean_blog` ×5, `de_dirty_mkt` ×1, `en_dirty_mkt` ×1. (Dirty reps 2–5 failed on the weekly limit.)

**Every one of the 12 runs fenced its commentary** with `<!--HUMANIZER-AUDIT-->` (`is_fenced=True` ×12, across all 4 inputs, EN+DE, clean+dirty).

- `fence_emission_rate` = **12/12 = 1.000**, Wilson 95% CI **[0.757, 1.000]** → lower bound **≥ 0.70 gate (i) MET** on the ON data.
- Probe auto-summary reported 7/7 = 1.000 (CI [0.646,1.000]) because its `has_commentary` detector excluded 5 `de_clean_pflege` runs that were fenced but emitted as a blockquote (the `_trailing_region` rfind missed the de-quoted body). Those runs ARE commentary-bearing-and-fenced (sentinel present), so the sound denominator is 12. **Probe-logic note for follow-up:** treat `is_fenced` as implying commentary-bearing in `_print_summary` (denominator = `is_fenced or has_commentary`).
- Rewrite quality spot-check: dirty inputs correctly de-tell'd (e.g. `de_dirty_mkt` → "Die innovative Plattform macht Teams produktiver: einfachere Zusammenarbeit, stärkere Ergebnisse."); clean inputs preserved.

## Gate status (Task 5)
- (i) `fence_emission_rate` lower-CI ≥ 0.70 → **MET (0.757)** on ON data — but n=12 with the dirty domain under-sampled (rep 1 only); a full ON set would tighten it.
- (ii) off/on rewrite edit-distance ≤0.02 (formatting-only) → **NOT MEASURED** (needs OFF rewrites — blocked).
- (iii) commentary-emission rate not risen vs OFF baseline → **NOT MEASURED** (needs OFF — blocked).
- (iv) pytest green → yes (357).

**Decision: PENDING.** Gate (i) is promising, but (ii)/(iii) require the OFF condition, blocked on the weekly quota. Do NOT bump v3.5.2 / ship the directive until the full gate is measured post-reset. The directive stays committed-unbumped (1439502); Phase 1 (parser) stands regardless.

## Resume plan (after weekly reset)
1. OFF condition: `git checkout 1439502~1 -- SKILL.md` (drop directive) → `PYTHONPATH=. python3 evals/scripts/probe_fence_emission.py --cond off 5` → `git checkout HEAD -- SKILL.md` (restore).
2. Finish ON dirty reps 2–5: `--cond on 5` (resumes).
3. Compute off/on edit-distance (gate ii) + commentary-rate (gate iii, OFF = lower-bound floor per the probe's documented limitation).
4. Skeptic-verify all numbers from the logs, then the Task-5 gate decision + (if pass) v3.5.2 bump on user OK.
