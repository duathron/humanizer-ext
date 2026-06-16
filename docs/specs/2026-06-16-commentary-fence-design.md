# Spec — Commentary fence (`<!--HUMANIZER-AUDIT-->`) for reliable rewrite extraction

**Date:** 2026-06-16 (rev 2 — post-Skeptic)
**Status:** design; Skeptic round 1 → REVISE (3 fixes folded in below); pending re-review → user review → writing-plans.
**Sub-project:** commentary-fence (Tier-1 skill-output reliability).

## 1. Problem (empirically grounded)

The skill appends free-form self-notes after the rewrite, which leak into the parsed `final` and corrupt edit-distance/length evals (surfaced in SP3c). **Probe (40 DE Quick-mode runs, existing `--save-rewrites` sidecars, zero quota): 30% (12/40) of clean-input runs append a trailing note**, wildly varied wording, **no fixed opener** — "Text unverändert — kein KI-Signal", "Das ist ein gutes Anschreiben", "Authentisches DACH-Anschreiben. Keine KI-Muster.", "Human-authored.", "Text reads as genuinely human-written". A content-matching regex cannot separate these from legit prose (proven in SP3c — a regex stripper false-stripped "shareholder register", "Der Brief ist beigefügt", "kein Eingriff"; reverted).

**Why the existing fallbacks don't cover it (Skeptic-verified):**
- `_COMMENTARY_RE` (English bold-header openers) catches **0 of 5** of the probe note styles.
- The FP scorer guard (`49aebaa`) fires only on `rewritten.startswith(text)` & longer — the **verbatim-body × FP-eval** quadrant only. On a **partial-edit+note** run it does not fire → the note inflates `edit_ratio` and lands in `final`.
- The e2e judge receives `final` (`run_e2e_eval.py:210`/`:224`), so for ANY unfenced note the **judge sees the note today**, guard or not.
So three of four quadrants (partial-edit×FP, ×e2e, verbatim×e2e) are currently uncaught. The gap is real, not gold-plating. **Goal: eval-parsing robustness.**

## 2. Approach (A, layered, two-phase)

A **single opening sentinel** marks the start of **trailing** (post-rewrite) commentary; the parser cuts from it to end-of-string. Commentary worth fencing is always trailing, so no closing sentinel. **Layered:** the fence gives a clean cut when emitted; existing fallbacks stay for forgotten-fence runs; the eval **measures** emission, doesn't assume it.

Sentinel: `<!--HUMANIZER-AUDIT-->` — never in legit humanised prose, markdown-invisible, collision-proof (not `###` heading-collision, not `[[…]]` wikilink-collision).

**Two phases (Skeptic #6 — decouple the safe half from the behaviour-risk half):**
- **Phase 1 — parser only (eval-only, zero-quota, no version bump).** Teach the parser to honour the sentinel when present. Provably safe, ships on its own merit (any fenced output — manual, future, or Phase-2-emitted — parses cleanly). Hard-gated by unit tests.
- **Phase 2 — SKILL.md directive + emission probe + version bump.** Only proceed if Phase-2's measured criteria (§4) pass; otherwise Phase 1 stands alone and the directive is dropped/reworked. This avoids bumping a version for a directive that might regress.

## 3. Components

### 3a. Parser (Phase 1) — `evals/scripts/_shared.py` `parse_skill_output`
- After the rewrite region is extracted by the EXISTING chain (`**Final rewrite:**` header, then heuristic fallback, then Quick-direct whole-text), apply the sentinel cut **to that extracted rewrite string**: if it contains `<!--HUMANIZER-AUDIT-->`, drop everything from the FIRST occurrence onward (`rstrip()`).
- **Ordering fix (Skeptic #3 — BLOCKER):** the cut is applied to the *extracted rewrite region*, NOT to the whole raw response. This is critical because Full mode emits "Final AI audit findings" **before** the `**Final rewrite:**` block (`SKILL.md:197-200`, step 3 before step 4). Cutting the raw response at a first/any marker would discard the real rewrite. By applying the sentinel cut only AFTER `**Final rewrite:**`-extraction (or to the Quick-direct body), a pre-rewrite audit marker can never truncate the rewrite. For Quick-direct output (no header, whole response is the rewrite), the cut applies to the trailing portion — correct.
- Keep `_COMMENTARY_RE` (English-header) AND the FP scorer guard unchanged as fallback for forgotten-fence runs.
- Provably safe: the literal `<!--HUMANIZER-AUDIT-->` never appears in legit rewrite output. Negative tests must include: a rewrite with no marker (unchanged); a rewrite whose prose mentions "audit"/"comment"/"HTML comment" inline (no cut); an INPUT that itself contains an HTML comment fed through (the skill would not reproduce our exact sentinel — test that a *different* HTML comment in the body does not trigger the cut, i.e. match the exact literal only).

### 3b. SKILL.md directive (Phase 2) — Output Format section (shared framework, EN+DE)
Add ONE directive, scoped to **trailing** commentary:
> **Commentary fence.** Any notes, audit summary, or commentary you place AFTER the final rewrite text MUST begin with the exact line `<!--HUMANIZER-AUDIT-->` on its own line; everything from that marker to the end is non-rewrite commentary. Do NOT use this marker for the Full-mode pre-rewrite "Final AI audit findings" (those stay where they are, before the `**Final rewrite:**` block). Quick mode: still emit only the rewrite — no commentary — but should any slip in, fence it.
- **Scope guard (Skeptic #3):** the directive explicitly excludes the Full-mode step-3 pre-rewrite audit, matching the parser's "cut only after the rewrite region."
- **Constraint:** formatting-only — must not change which patterns fire or how text is rewritten, and must NOT increase the rate at which commentary is emitted (Skeptic #2 — the "emit none, but if you do, fence it" clause risks legitimising Quick-mode notes).

### 3c. Eval (Phase 2) — `fence_emission_rate` + a real regression guard
- **Emission probe:** run the skill on commentary-prone inputs — N clean (→ Quick preserve-note path) + N change-warranting (→ Full summary), EN and DE — and for each output bearing trailing commentary, record whether it is fenced. Report `fence_emission_rate = fenced / commentary-bearing`, with N and a 95% interval.
- **Regression guard (Skeptic #2 — replaces the vague "spot diff"):** a **paired before/after** run on a fixed seed set (same N): (a) **mean normalized Levenshtein edit-distance between directive-off and directive-on parsed `final` ≤ 0.02, upper-95%-CI ≤ 0.05**, computed AFTER the sentinel/commentary cut (so the marker line itself is excluded — otherwise the marker registers as a spurious edit); on the clean-input/preserve subset, require directive-on `final` byte-identical to directive-off (the model should return input verbatim either way). (b) **commentary-emission rate must NOT rise** vs the pre-directive baseline (the 30% probe is the baseline); (c) existing 346 pytest green.

## 4. Acceptance criteria
- **Phase 1 (hard gate, zero-quota):** unit tests prove (a) fenced rewrite → marker-onward dropped; (b) the ordering fix — a Full-mode response with a pre-rewrite audit + a real `**Final rewrite:**` is parsed to the real rewrite, NOT truncated; (c) negative cases (§3a) → no false cut; (d) forgotten-fence → existing fallback behaviour unchanged; (e) full suite green. Phase 1 ships on this alone (eval-only).
- **Phase 2 ship criterion (Skeptic #4 — concrete, falsifiable):** ship the SKILL.md directive ONLY if ALL hold: (i) `fence_emission_rate` lower-95%-CI **≥ 0.70** on the probe set — rationale: of commentary-bearing runs, ≥70% must be fenced for the fence to beat the ~0%-effective free-form fallback by a worthwhile margin (the fence must actually deliver, not be a no-op dressed as a win); (ii) the §3c(a) edit-distance bar holds (mean normalized ≤0.02 / upper-CI ≤0.05 on post-cut `final`; preserve-subset byte-identical) — formatting-only confirmed; (iii) commentary-emission rate does not rise; (iv) pytest green. If (i) fails → do NOT ship the directive (Phase 1 parser stands; reconsider wording or abandon). If (ii)/(iii) fail → the directive perturbs behaviour → revise or abandon. No escape hatch: a low emission rate is a FAIL, not a "reported number."
- **No meaning/skill-quality regression** from the SKILL.md wording.

## 5. Versioning & rollout
- **Phase 1:** eval-only, **no version bump** (parser change in `evals/`).
- **Phase 2 (only if §4 passes):** patch bump **v3.5.2** (output-format hardening; backward-compatible for EXTERNAL consumers — the marker is additive; the repo's OWN `parse_skill_output` is a deliberately-updated consumer). Bump SKILL.md frontmatter + `plugin.json` + `marketplace.json` + README version history; squash-merge, tag, GH release on explicit user OK.

## 6. Testing
- Phase 1: TDD — fenced / ordering / forgotten / negative-no-false-cut; full pytest green.
- Phase 2: the `fence_emission_rate` probe + the paired regression guard (§3c). Every probe number + diff independent-Skeptic verified.

## 7. Risks & mitigations (Skeptic-corrected)
- **Probabilistic emission (core risk):** the model will forget the fence sometimes. The fence helps **only proportional to its emission rate**; §4(i) gates on that. The fallback (`_COMMENTARY_RE` + scorer guard) catches **0/5** of the free-form note styles on partial-edit runs — so **the forgotten-fence × partial-edit quadrant's residual is UNCHANGED from today** (honest correction: the fallback is largely inert on these notes; the only NEW coverage is the fenced fraction). This is acceptable as a strict improvement (never worse than today), but the spec does not pretend the fallback backstops the free-form notes.
- **Directive perturbs rewriting / raises commentary rate:** §3c(a)/(b) guards + §4(ii)/(iii) gates; the "emit none but fence if you do" clause is the specific suspect — if commentary rate rises, abandon that clause.
- **Parser ordering regression (was a BLOCKER):** fixed by cutting only the extracted rewrite region, after `**Final rewrite:**` extraction; locked by acceptance test §4(b).
- **EN+DE shared framework:** directive is language-neutral; probe includes EN and DE.

## 8. Out of scope
- Suppressing commentary entirely (the "product cleanliness" goal — not chosen).
- Full pattern/FP re-baselines (the directive is formatting-only; not required).
- The paused `wikipedia_career` general-FP run (separate).
