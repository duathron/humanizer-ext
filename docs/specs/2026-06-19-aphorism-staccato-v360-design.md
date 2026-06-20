# Design — v3.6.0: #42 Aphorism Formulas + #34 staccato-run extension

**Date:** 2026-06-19
**Status:** brainstorm → 2 Skeptic rounds → **MeetUp #2 (2026-06-20, Skeptic-gate APPROVE) → rev2** (8 fixes folded) → writing-plans next
**Current version (verified):** SKILL.md frontmatter + `.claude-plugin/plugin.json` at **3.5.3**. Target **3.6.0** (minor — one new pattern).

## Context

This resumes DELIVERABLE 2 of `docs/specs/2026-06-18-upstream-v280-tells-port-design.md` — the heavier half of the upstream-v2.8.0 port, deferred from the v3.5.3 split after a MeetUp (`AI/PROJECTS/CODING/humanizer-ext/MeetUp Logs/2026-06-18-upstream-v280-port-spec-review.md`) surfaced 5 BLOCK-level design issues in the original "#42 + #43 both new patterns" plan. This spec **resolves** them, with two scope changes decided in brainstorm:

1. **#43 is NOT a new pattern.** Its genuinely-new tell (a mid-text *run* of short declaratives manufacturing drama) is folded into **#34** as a lock-free extension — the same shape as the shipped v3.5.3 #20/#31 extensions. This dissolves the two #43 blockers: the #9/#13 cross-pattern collision (negation-fragment runs stay #9; #34 already owns the trailing-emphasis family) and the no-zero-API-Gate-1 problem (the extension is prose-rule-only, validated by Gate-2, so no structural-run regex is needed).
2. **#42 Aphorism Formulas is the only new pattern** — the only count-changing piece.

So **v3.6.0 = #42 (new) + #34 (extension)**.

## What good looks like

#42 catches manufactured-maxim aphorisms without over-firing on ordinary copula facts; its recall is observable (held-out aphorisms, not just anchor-derived TP). #34 also flags dramatic staccato runs without a FP-risky structural regex. EN + DE parity. Existing detection does not regress against a named baseline. The 41→42 count bump and the three exact-equality test locks are edited in lockstep so the build never goes red.

---

## Part 1 — #34 staccato-run extension (LOCK-FREE)

### Detection content
**Existing #34** = a *single* short emphatic sentence tacked at a paragraph END that restates the prior sentence. **Extension** = a *run of ≥3* short declarative sentences mid-text that manufacture drama. Fix for the run: **restructure into flowing prose (merge)** — do not merely clip.

**EN before (fully affirmative staccato — no negation, so no #9 overlap; the run is mid-paragraph, continuing prose follows, so it is NOT the single-trailing-restate the original #34 owns — resolves MeetUp#2 BLOCK-6):**
> The model shipped on Tuesday. It changed everything. The whole field shifted. The team knew it. Within a month three competitors had rebuilt their pipelines around the same idea.
**EN after:**
> The model shipped on Tuesday and reshaped the field; within a month three competitors had rebuilt their pipelines around the same idea.

**DE before (fully affirmative, mitten im Absatz — keine Verneinung):**
> Das Modell kam am Dienstag. Es veränderte alles. Das ganze Feld verschob sich. Das Team wusste es. Innerhalb eines Monats hatten drei Wettbewerber ihre Abläufe darauf umgestellt.
**DE after:**
> Das Modell kam am Dienstag und veränderte das Feld; innerhalb eines Monats stellten drei Wettbewerber ihre Abläufe darauf um.

**One-passage-one-pattern rule (stated in #34, both packs):**
- A *single* trailing restate at paragraph end → #34 (original).
- A run of *negation* fragments ("No X. No Y. No Z." / "Kein X. Kein Y.") → **#9** (it owns angehängte Verneinungen) — NOT #34.
- A run of *≥3 affirmative* short declaratives building drama → #34 (this extension).

**Reconciling the existing DE #34 guidance:** DE #34 (`de.md:787-788`) says staccato is "weniger verbreitet im Deutschen … nur bei besonders auffälligen Fällen flaggen" (less common in German; flag only conspicuous cases). The extension does NOT contradict this — a **run of ≥3 affirmative drama-fragments IS exactly such a conspicuous case**. The DE #34 wording must be extended to say so explicitly (the ≥3-run is the conspicuous trigger the existing note already gates on), not left to read as two opposing rules.

(Analogy note: this "add a sub-tell to an existing pattern section, no new ID" shape matches the shipped v3.5.3 #20/#31 watch-list extensions — same lock-free mechanism, applied to a structural sub-tell instead of a literal phrase.)

### Validation
- **Prose-rule only — NO `regex_scorer` key, NO corpus regex case.** "Manufactured drama" is a semantic judgment a regex cannot make, and a bare short-sentence-run regex over-fires on legitimate terse prose.
- **Positive Gate-2 case** on a staccato run (EN + DE) — the rewrite MUST collapse the run into flowing prose.
- **Negative Gate-2 survive-case (resolves MeetUp#2 BLOCK-3):** legitimate terse prose that is NOT manufactured drama (e.g. EN: *"The build failed. I checked the logs. A test timed out. I fixed it and pushed."*; DE: *"Der Build schlug fehl. Ich prüfte die Logs. Ein Test lief in einen Timeout. Ich behob es und pushte."*) — the rewrite MUST NOT merge/flatten it. Over-merging legitimate terse prose is the extension's ONLY failure mode and has zero coverage without this case; the positive case alone proves only that it fires, never that it stays its hand.
- **Both cases MUST actually run for v3.6.0** (not deferred like a paid E2E) — they are the only validation the #34 staccato extension has.

### Lock-free confirmation
No new `### N.` heading (edits the existing `### 34.` body), no pattern-count change, no `true_negative` corpus case from this part → none of the three exact-equality locks touched by Part 1.

---

## Part 2 — #42 Aphorism Formulas (NEW pattern)

### Why a new pattern, not a fold (MeetUp#2-resolved)
#42 *could* technically fold into an existing host's watch-list (scorer keys are tell-name-keyed; corpus carries `pattern_id`), the same lock-free mechanism #43 used to fold into #34 — avoiding the 41→42 bump and the lock edits. **Rejected:** unlike #43 (a genuine *sub-shape* of #34's trailing-emphasis family), the aphorism-maxim tell is **not a sub-shape of any existing pattern** (#1 is broad-trend significance inflation; #27 is authority-connective tropes; neither is "ordinary claim recast as a coined maxim"). Folding would forfeit **per-#42 held-out-recall observability** — the one thing the slot buys. New slot justified. (Recorded MeetUp dissent: the Outsider argued to defer #42 until a real-world miss is observed; countered as an unfalsifiable gate — you cannot observe a miss for a pattern you never shipped.)

### Detection content
**Tell:** an ordinary claim recast as a reusable-sounding maxim — gravitas, not precision. Replace the formula with the concrete claim it gestures at.

**EN regex anchors (hard, distinctive only):** `X is not a tool but a mirror`, `X becomes a trap`.
**EN soft tells (named in prose, NOT regex triggers — symmetric with the DE Genitiv exclusion; resolves MeetUp#2 BLOCK-1):** `the language of <abstract>`, `the currency of <abstract>` — English has the SAME non-figurative idiom ("the language of diplomacy", "the currency of nineteen countries"), so a literal regex anchor over-fires; the LLM/Gate-2 catches the figurative cases. Also soft-only: bare `X is the Y of Z` (countless literal copula facts) and `the architecture of` (collides with #35 example headings `en.md:423/:430`).
**EN before:** *Trust is the currency of every healthy team.* (NB: this uses the *soft* "currency of" shape → it is an LLM/Gate-2 TP, NOT a regex-fire case.)
**EN after:** *Teams work better when members can rely on each other.*
**EN regex-anchor before (fires `aphorism_formula`):** *Leadership is not a tool but a mirror of the team.*

**DE regex anchors (hard, distinctive only):** `X ist kein Werkzeug, sondern ein Spiegel`, `X wird zur Falle`.
**DE soft tells (NOT regex triggers):** bare `die Sprache <Genitiv>` / `die Währung <Genitiv>` — established **Fachsprache idiom** ("die Sprache der Diplomatie", "die Währung der Aufmerksamkeit"); over-flag legitimate German.
**DE before:** *Vertrauen ist die Währung jeder guten Zusammenarbeit.* (uses the *excluded* Genitiv shape → LLM/Gate-2 TP, NOT a `de_aphorism_formula` regex-fire case.)
**DE after:** *Zusammenarbeit funktioniert, wenn die Beteiligten einander vertrauen.*

**#42 ↔ #9 routing rule (resolves MeetUp#2 BLOCK-2; state in both packs):** the hard anchor `X is not a tool but a mirror` / `X ist kein Werkzeug, sondern ein Spiegel` is structurally #9's "not X but Y" / "kein A sondern B" frame (`en.md:147`, `de.md:295-297`), but with a DIFFERENT remediation. Route by intent: a negation-frame that **manufactures a profundity maxim** (mirror / trap / Spiegel image) → **#42** (replace with the concrete claim); a bare rhetorical "not only…but" / "kein [Substantiv]" dismissal of an unclaimed alternative → **#9** (delete the frame). Applies ONLY to the negation-frame anchor; affirmative aphorisms ("becomes a trap", "wird zur Falle") don't touch #9.

### Placement
Language packs, paired: `patterns/en.md` #42 + `patterns/de.md` #42 (NOT `_universal.md`). #42 is the next free number (highest in use = #41; #100-block is DE-only).

### Validation — two gates (no self-review; Skeptic on primary evidence)

**Gate 1 — zero-API (precision side):**
- Full `pytest` green.
- `regex_scorer` keys `aphorism_formula` (PATTERNS_EN) + `de_aphorism_formula` (PATTERNS_DE) **fire on the named-anchor TP** AND **stay silent on**:
  - **≥3 adversarial copula TN** (EN): *Tuesday is the busiest day of the week.* / *The CEO is the head of the company.* / *Water is the main component of the body.*
  - **DE Fachsprache-idiom TN**: *Die Sprache der Diplomatie ist subtil.* / *Aufmerksamkeit ist die Währung der sozialen Medien.* (must NOT fire — the bare Genitiv is excluded from the anchor).
- **Acknowledged precision floor (MeetUp#2 CONCERN):** after demoting "the language/currency of", the EN hard regex anchor is just **2 literal phrases** ("is not a tool but a mirror" — also #9-routed — + "becomes a trap"); the DE anchor is likewise 2. This is deliberate (the precision-subset/recall-LLM split): Gate-1's deterministic TP-fire coverage is intentionally thin, and **recall rests entirely on the ≥2 held-out Gate-2 removal-check cases**, not the regex. Do not "thicken" the anchor to chase recall — that re-introduces the copula over-fire.

**Gate 2 — recall + no-regression (resolves BLOCK #3 + #5):**
- **Recall — the "Gate-2 full-pass removal check" (NOT an LLM judge; resolves BLOCK #3 + MeetUp#2 BLOCK-4):** `run_pattern_eval.py` runs the real `claude -p` full-pass rewrite, then scores by **literal `expected_changes` string-removal** (`detected` iff every present-in-input term is absent from the rewrite). So #42's corpus TP set includes **≥2 held-out aphorisms whose wording is NOT in the regex anchor lexicon** (from upstream's real examples / independently authored), and **each held-out case's `expected_changes` MUST list the exact aphoristic surface tokens the rewrite has to delete** (e.g. for "Symmetry is the language of trust" → `["is the language of"]`), NOT an incidental noun — otherwise the removal check is trivially passable and the circularity returns. The regex is a high-precision *subset* (mechanics); the full-pass removal check owns recall (semantics). This makes the false-negative side observable.
- **No-regression (BLOCK #5 + MeetUp#2 BLOCK-5 — like-for-like metrics):** `run_pattern_eval.py --lang en --force --runs 5` then `--lang de --force --runs 5`. The runner emits **two** metrics (`overall_detection_rate` = all-or-nothing per case; `per_term_removal_rate` = per term) — compare EACH to its OWN-metric prior figure, never cross-metric:
  - **all-or-nothing:** EN **0.938** (`pattern_en_20260612_113505.json`, 45/48 — latest complete EN run) · DE **0.907** (`pattern_de_20260614_153629.json`, `summary.overall_detection_rate` — latest complete DE run).
  - **per-term:** EN **0.971** (same EN run) · DE **0.95** (same DE run, `per_term_removal_rate`).
  - **Source the baselines from the dated run JSONs, NOT the `summary_latest_*` markdown** (MeetUp#2 BLOCKER-rev2): `summary_latest_de.md:21` shows **0.864 / 0.907** which matches **no committed JSON** and is superseded by the 2026-06-14 run (0.907 / 0.95); `summary_latest_en.md` shows superseded 0.905/0.619/0.5. Both `summary_latest_*` files are **things-to-refresh, not sources of truth**. (The spec's pre-rev2 "EN 0.938 vs DE 0.907" was both cross-metric AND DE-stale-sourced — fixed here.)
  - **Refresh of record + gate (MeetUp#2 BLOCK-8, BOTH languages):** the `summary_latest_{en,de}.{md,json}` are **hand-maintained, no script writes them** — overwrite BOTH with the v3.6.0 dated-run figures. To stop the 100%-skip history, **add `test_summary_latest_en_matches_current_baseline` AND `test_summary_latest_de_matches_current_baseline`** (cheap committed-file-vs-committed-constant equality tests — not live floats, so no flakiness) so neither refresh can silently skip again.
  - Tolerance: each metric stays within run-to-run noise of its own prior figure; no previously-passing pattern drops its majority verdict.

### FP discipline
Option A (regex true_negative gate) + the ≥3 adversarial copula TN (EN) + DE Fachsprache TN. Escalation fallback: if the #42 regex cannot pass the adversarial TN without also failing to fire on its own named anchors, narrow to literal phrases only; a dedicated `run_false_positive_eval.py` pass for #42 is the last resort (not expected — the anchor is already literal-distinctive).

### Recipe — files touched (#42 + #34 ext)
- `patterns/en.md` — new #42 section; extend #34 body (staccato run + one-passage rule).
- `patterns/de.md` — new #42 section; extend #34 body.
- `evals/scripts/regex_scorer.py` — `aphorism_formula` (PATTERNS_EN) + `de_aphorism_formula` (PATTERNS_DE). (No key for the #34 staccato run.)
- `evals/corpus/en/patterns/pattern_042.json` + `evals/corpus/de/patterns/pattern_042.json` — TP (anchor + held-out) + adversarial-copula `true_negative` cases. Case ids `pattern_042_en_001`…, `pattern_042_de_001`… (filename is `pattern_042.json`; lang/seq live in the case `id`).
- Gate-2 staccato cases: add to the EN + DE pattern-034 corpus (or e2e) BOTH a **positive** drama-run case (must collapse) AND a **negative survive-case** (legit terse prose that must NOT merge — MeetUp#2 BLOCK-3). (Verify existing pattern_034 corpus shape + next-free id before writing — DE corpus has more cases than EN; EN was `_en_001` only, DE went `_de_001..003`.)
- **New test module `tests/test_baseline_summary.py`** (the named `test_eval_reports.py` does NOT exist — create this, or extend `tests/test_skill_structure.py`) — add `test_summary_latest_en_matches_current_baseline` AND `test_summary_latest_de_matches_current_baseline`: each asserts the respective `summary_latest_{lang}.md` headline detection figure equals the committed v3.6.0 constant, so neither hand-refresh can silently skip (MeetUp#2 BLOCK-8; 100% skip history).
- `evals/reports/summary_latest_en.{md,json}` AND `summary_latest_de.{md,json}` — **hand-maintained narrative reports; NO script writes them** (verified: `run_pattern_eval.py` produces dated raw reports, not the `summary_latest_*` file). After the v3.6.0 `--runs 5` re-baseline, **manually overwrite BOTH** so the files of record finally match (EN currently shows superseded 0.905/0.619/0.5; DE shows 0.864/0.907 which matches no committed JSON, superseded by the 2026-06-14 run 0.907/0.95) — closes BLOCK #5 at the file-of-record level for both languages.
- `tests/test_regex_scorer.py` — `aphorism_formula`/`de_aphorism_formula` fire-on-TP + silent-on-adversarial-TN assertions.
- `tests/test_skill_structure.py` — add `42` to **`EN_PATTERN_IDS` (:57)** and **`DE_PATTERN_IDS` (:143)** (exact-equality sets — break otherwise).
- `tests/test_corpus_true_negative_integrity.py:44` — widen `tn == {"pattern_019_en_001"}` to the **exact** new #42 EN adversarial-copula TN ids (enumerate, no glob).
- Counts 41→**42**: `SKILL.md:10/:38/:154`; `README.md:7/:14/:110/:139/:212/:214` + a `## Version History` `3.6.0` entry; `plugin.json:4` desc; `marketplace.json:11` desc. **"37 shared" correction (MeetUp#2 BLOCK-7) — re-derive against the real sets, don't blind-bump.** `README.md:214` is incoherent: it says "13 universal + 28 English-specific = 41" then "translates all 37 shared." Verified composition: `_universal.md` = 13 patterns; `en.md` = 28; `de.md` re-lists **28 EN-parallel** (NOT the 13 universal — those apply from `_universal.md` without re-listing) + **5 DE-only** (#100-104). So none of 28/37/41 is cleanly "shared", and "37" reconciles to no rule. The implementer MUST **rewrite `README.md:214` to a coherent statement** — e.g. "**42** patterns = 13 universal + 29 English-specific; the DE pack translates the 29 language-specific patterns into German and adds 5 DE-only" — computed against the actual pack headings at impl time (`grep -c '^### [0-9]' patterns/*.md`), NOT a blind 37→38 bump. **Open item for the count task: state the verified numbers, do not perpetuate "37 shared".**
- Version 3.5.3→3.6.0: `SKILL.md:3`, `plugin.json:3`, `README.md:3` badge + `:11` header. Do NOT touch historical 3.5.x version-history entries.

## Risks
- **#42 recall is intentionally regex-limited** — the deterministic scorer only catches the named anchors; broad aphorism detection rests on the Gate-2 LLM. Stated, not a defect: regex = mechanics, LLM = semantics. The held-out TP cases keep the LLM honest.
- **DE surface author-supplied** — the DE #42 anchors + #34 staccato example + the Fachsprache TN are author intuition; Gate-2 DE `--force` + the DE adversarial TN are the validation. Fix before ship if over-fire shows.
- **#34 staccato over-merge** — the LLM might merge legitimate terse prose. Mitigated by the prose-rule wording ("built for drama", ≥3 run) + the one-passage rule + **the mandatory negative Gate-2 survive-case** (legit terse prose must NOT merge); the FP runner / human-sample audit is the further backstop.
- **Count re-derivation** — "37 shared" must be re-derived against real pack sets, not blind-bumped to 38.

## Out of scope
- A standalone #43 pattern (folded into #34).
- A structural staccato-run regex (prose-rule only).
- `_universal.md` / SKILL framework changes (only the count + version strings).
- em-dash hard-cut; Wikipedia conduct-tells.
