# Scorer refusal-guard (eval rigor) — design

**Status:** approved design via the **2026-06-09 meetup** (3 advocates + Skeptic adjudication; consensus + dissent recorded in vault `DECISIONS.md`). Eval-rigor sub-project; **no skill change**. Unblocks the held SP3b.

## Problem (primary-evidence-confirmed)

The pattern detection scorer (`run_pattern_eval._score_case_once`) computes `detected = (every expected_changes term is absent from the rewrite)`. A skill **refusal** ("no text provided…", "what should I humanize?") contains none of the tell terms → scores `detected=True`. Three cached partials proved it (`pattern_009_en_002/003`, `pattern_013_en_001`, all `[T,T,T,T,T]`). This **inflates** detection numbers and produced a false SP3b conclusion (since corrected).

**Scope of harm (Skeptic-measured):** small on the headline rate (~0.67pp; 0.898→0.891) but real on per-pattern coverage. The refusal itself is a `force_full=True`-only artifact (the override line crowds short inputs — A/B-confirmed); FP/true-neg (`force_full=False`) do not refuse. **The skill hallucinating a refusal on short clean text is a separate, deferred product-robustness finding** — this sub-project fixes the EVAL's mis-scoring of it, not the skill.

## Non-goals (per the meetup)

- **Prompt reshape / re-baseline** — rejected as disproportionate to a ~0.67pp effect + confounding. (Recovering #9/#13 coverage is a corpus task, handled in SP3b, not here.)
- **Dropping `force_full`** — rejected; it was added (commit `5b6bf0e`) to disambiguate "pattern missed" vs "case quick-dropped". KEEP it.
- **Fixing the skill's refusal behavior** — deferred product-robustness finding (B's powered A/B is the tool if pursued).
- New SKILL.md change of any kind.

## Components & edits

### 1. `_shared.py` — refusal detector (PHRASE-ONLY)
**Decision (round-1 Skeptic):** the overlap backstop is DROPPED. Content-word overlap cannot distinguish a refusal (≈0 overlap) from a legitimate *aggressive* rewrite (also ≈0 overlap on a short input — e.g. "The utilization of synergistic methodologies…" → "It works better."). Any overlap threshold that catches refusals also kills good heavy rewrites. So `is_refusal_or_nonrewrite` is NOT re-added; the detector is phrase-only, which **never false-flags a real rewrite** (the spec's own previously-stated fallback). This refines the meetup's "phrase + overlap-backstop" consensus on round-1 evidence — recorded as resolved dissent.

- **Add `is_refusal(text)`** (input-independent, pure):
  - empty / whitespace-only → True;
  - lowercased `text` contains any **refusal-anchored stub** (anchored to the refusal CONTEXT, not bare keywords — Skeptic round-3): `"no text provided"`, `"no text to humanize"`, `"what should i humanize"`, `"what text do you want"`, `"paste the text to humanize"`, `"paste the text you want"`, `"provide the text to humanize"`, `"provide the text you want"`, `"what do you want me to humanize"`, `"text to humanize?"`.
  - Anchoring (e.g. `"no text provided"`, not bare `"no text"`) prevents mis-flagging a legit rewrite that merely mentions text/forms ("There's no text-message etiquette anymore."). **NOT** included: `"can't help"` / generic decline phrases.
- Pure, unit-tested. **Two failure directions, both safe:** a false NEGATIVE (novel/DE refusal not listed) → scored detected/miss (one bad data point); a false POSITIVE (a rewrite containing a stub substring) → that run → `None` → the case goes **`inconclusive`** (surfaced, NOT a silent false detection). The "NEVER false-flags" claim is wrong — it's *rare* (anchored phrases) and *safe-surfaced*. Tighten further if it ever fires on a real rewrite.

### 2. `run_pattern_eval` — a refusal run becomes a `None` run (reuse SP3a)
Post-SP3a, `score_case` is a multi-run wrapper: a shared loop calls `_score_case_once` N times into `run_dicts`, mapping exceptions → `None`, and `aggregate_runs` already **excludes `None` runs** (→ `inconclusive` if `< ⌈N/2⌉` succeed). The fix rides that machinery:
- **In `_score_case_once`** (BOTH the scored branch AND the true_negative branch call `run_skill`): after the raw rewrite is obtained — `rewritten_raw = result.get("final") or result.get("draft") or ""` — and **before** any lowercasing/scoring, if `is_refusal(rewritten_raw)` → **`return None`** directly (not a marker dict). Checking the FULL raw rewrite, not the 200-char/​lowercased preview (addresses MINOR-2 + truncation). *Returning `None` (vs a `{"refusal":True}` marker) is strictly safer — no caller can KeyError on `r["edit_ratio"]`/`r["detected"]`, and the multi-run loop already collects whatever `_score_case_once` returns.*
- **In `score_case`'s loop**: no change needed — the loop already does `run_dicts.append(_score_case_once(...))` inside its try/except, so a `None` return is appended as a `None` run exactly like a caught failure. (The unscorable short-circuit paths return BEFORE `run_skill`, so they never return `None` — only a real `run_skill`+refusal yields `None`.)
- **Result, both case categories handled by one change:** a detection-case refusal → `None` run → excluded from the binary majority (not a false `detected`); a true-neg-case refusal → `None` run → excluded from the median edit_ratio (not a false over-edit "fail"). If most runs of a case refuse → the case is **`inconclusive`** (SP3a's own bucket — own partial, exit 1, surfaced) — which is exactly the honest outcome: the eval could not get a usable rewrite. No new status needed; refusals are visible via the existing `inconclusive_cases` + per-run `None`s.
- The unscorable short-circuit branches (no `run_skill` call) are untouched.

### 3. `run_false_positive_eval` — same `None`-run treatment (defensive)
FP's `score_human_text` is the analogous multi-run wrapper. In `_score_human_text_once`, if `is_refusal(raw_rewrite)` → **`return None`** (same shape as pattern); the wrapper's loop appends it as a `None` run (excluded from the median edit_ratio, → `inconclusive_files` if most refuse). FP uses `force_full=False` and does NOT refuse in practice (A/B-confirmed), so this is defense-in-depth expected never to fire — but it closes the inverse bug (a refusal = huge edit_ratio = false "over-edit") and keeps both runners consistent.

### 4. Report naming (the meetup's cheap honesty win)
In the pattern + e2e report headers / a doc note: state plainly that the **pattern eval measures detection-logic capability under a forced full pass** (`force_full=True`, bypasses the product's real pre-flight routing), while the **e2e eval measures shipped-routing fidelity**. Resolves the recurring "but real users never hit force_full" objection.

## Inflation quantification (secondary, opportunistic — zero API)
If cached run-1 `rewrite_preview`s for detection cases are available in `evals/reports/_partial/`, count how many scored `detected=True` while being refusal stubs, and report the corrected rate. **Caveat (Skeptic):** only run-1 is cached, so this is a lower bound, not a full re-measure. Do NOT spend quota on a re-baseline (non-goal). If the cache is ambiguous (cross-branch corpus states), state the inflation as "~0.67pp on the SP3b-run sample" and move on — the fix's value is forward (future runs can't repeat the bug), not retroactive.

## Testing (pytest, zero quota)
- **`is_refusal(text)` units** (signature takes only the output — phrase-only, input-independent):
  - real refusal stubs ("no text provided. what should I humanize?", "paste the text to humanize…") → True;
  - empty/whitespace → True;
  - **legit aggressive rewrite NOT flagged (load-bearing):** "It works better." / "This approach simply works better than before." → **False** (no refusal phrase). Phrase-only makes this pass — there is no overlap backstop to false-flag it. THIS is the test the round-1 detector failed; it must pass now.
  - the 5 real SP3b conversion inputs' real rewrites → False; the 3 real refusal stubs → True;
  - a legit rewrite containing "can't help" ("You can't help noticing the difference.") → **False** (confirms "can't help" is NOT in the list).
- **`run_pattern_eval` test (scored branch):** a refusal output makes that run a `None` run → excluded from the binary majority (not `detected`); a case whose runs all refuse → `inconclusive_cases`, never `detected=True`.
- **`run_pattern_eval` test (true_negative branch):** a refusal output → `None` run → excluded from the median edit_ratio (not a false over-edit `passes_true_negative=False`); all-refuse → inconclusive.
- **FP test:** a refusal run → `None` → excluded from the median edit_ratio; all-refuse → `inconclusive_files`.
- Full suite green (current main baseline 329; + new tests).

## Success criteria
- `is_refusal(text)` is pure + unit-tested, **phrase-only**; a legit aggressive rewrite is NOT flagged (the round-1 load-bearing test passes).
- A refusal run → `None` run in both pattern branches (scored + true-neg) and FP → excluded from majority/median, → `inconclusive` if most runs refuse. Refusals never score `detected` or over-edited; surfaced via existing `inconclusive_cases`/`None`s (not silent).
- `force_full` kept; report naming states detection-capability (pattern) vs routing-fidelity (e2e).
- Full pytest green (329 + new); **SKILL.md byte-identical to main** (no skill change).
- Inflation noted (~0.67pp, lower bound from cached SP3b-run previews) without a quota re-baseline.

## Risks & mitigations
- **Phrase-only misses a novel/DE refusal wording** (not in the list) → it scores as detected/miss (one bad data point). Accepted as the SAFE failure direction (vs false-flagging a good rewrite, which corrupts the rate by exclusion). Extend the phrase list if new stubs are observed.
- **Refusal text exceeds 200 chars / preview truncation** → AVOIDED: `is_refusal` runs on the FULL raw rewrite inside `_score_case_once`, before truncation/lowercasing.
- **Hides the skill bug** → explicitly filed as a deferred product-robustness finding; the `inconclusive_cases` count + per-run `None`s surface how often refusals fire, so it's visible not silent.

## Implementation isolation & review
Branch `scorer-refusal-guard` off `main`; squash-merge when green. SP3b later rebases on the merged result (dropping its stranded `172cdfb` dup). **No self-review — every diff + the detector logic is Skeptic-verified from primary evidence.**
