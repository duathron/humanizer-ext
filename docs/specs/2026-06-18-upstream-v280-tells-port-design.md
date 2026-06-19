# Design — Port upstream blader/humanizer v2.8.0 net-new tells

**Date:** 2026-06-18
**Status:** brainstorm → 3 linear-Skeptic rounds → **MeetUp (2026-06-18, Skeptic-gate
APPROVE) → SPLIT into two deliverables.**
**Current version (verified):** SKILL.md frontmatter + `.claude-plugin/plugin.json`
are at **3.5.2**.

## Split decision (MeetUp 2026-06-18)

The original single-spec v3.6.0 port was split because the #20/#31 extensions are
**mechanically separable** (they add NO new pattern ID and NO count change → do not
trip the frozen ID-sets `test_skill_structure.py:57/:143` or any count string), while
#42/#43 carry confirmed BLOCK-level design issues. Sequence:

- **Deliverable 1 — ACTIVE (this spec, target v3.5.3 patch):** #31 + #20 watch-list
  extensions. Cheap, lock-free, no detection re-baseline. Ready for writing-plans.
- **Deliverable 2 — DEFERRED (target v3.6.0, see "Deferred" section):** #42 Aphorism
  Formulas + #43 Manufactured Punchlines/Staccato as new EN+DE patterns — blocked on
  the MeetUp findings until picked up as separate work.

MeetUp log: `AI/PROJECTS/CODING/humanizer-ext/MeetUp Logs/2026-06-18-upstream-v280-port-spec-review.md`.

---

# DELIVERABLE 1 (ACTIVE) — #31 + #20 extensions (v3.5.3 patch)

## Context

Upstream v2.8.0 (`git show 9600f2b -- SKILL.md`) extended its chatbot-artifact
pattern with offer-to-continue closers and added conversational rhetorical openers.
Mapped onto our diverged catalogue:
- our **#20 Collaborative Communication Artifacts** (`en.md:231`, `de.md:484`) gains
  offer-to-continue closers.
- our **#31 Rhetorical and Self-Answering Questions** (`en.md:355`, `de.md:687`) gains
  the standalone fake-candid discourse-opener hooks (kept as a #31 extension, NOT a
  new pattern — the hook co-occurs with question-ceremony; a separate pattern would
  double-fire).

Both are watch-list additions to **existing** patterns → no new pattern ID, no count
change, no frozen-ID-set edit. This is a patch, not a feature.

## Detection content

### #31 extend (EN + DE) — fake-candid discourse openers
**Add to EN watch:** `Look,`, `Here's the thing`, `The thing is`, `Let's be honest`,
`Real talk`, `Honestly?` as standalone theatrical hooks.
**Add to DE watch:** `Mal ehrlich`, `Ganz ehrlich?`, `Die Sache ist die`
(borderline-colloquial — flag only when clearly a standalone hook).
**DROPPED per MeetUp (German-linguist):** `Sagen wir es so` — it is a calque of "Let's
put it this way" AND carries a real hedging/reformulation function in German, so it
would over-edit legitimate prose. Do NOT add it.
**FP guard:** these words mid-sentence are ordinary; the tell is the standalone
pause-and-reveal opener only.

### #20 extend (EN + DE) — offer-to-continue closers
**Add to EN watch:** `Want me to…?`, `Should I continue?`, `Want me to give examples?`.
**Add to DE watch:** `Soll ich fortfahren?`, `Möchten Sie, dass ich …?`, `Soll ich
Beispiele geben?` (MeetUp German-linguist: all four idiomatic, genuine DE chatbot
artifacts in the Sie-register #20 already uses — no concern).

## Recipe — files touched (verified)

- `patterns/en.md` — #20 (`:231`) + #31 (`:355`) watch-list lines extended.
- `patterns/de.md` — #20 (`:484`) + #31 (`:687`) watch-list lines extended.
- `evals/scripts/regex_scorer.py` — add the new **literal trigger phrases** to
  `PATTERNS_EN` / `PATTERNS_DE` (these phrases are literal, fully regex-expressible).
- `evals/corpus/en/patterns/pattern_020.json`, `pattern_031.json` and the DE
  equivalents (`evals/corpus/de/patterns/pattern_020.json`, `pattern_031.json`) —
  **already exist**; add new TP cases only, carrying the new closer/opener phrases as
  `expected_changes`. **Do NOT add a `true_negative: true` corpus case** — that would
  trip the exact-equality EN TN-integrity lock (`test_corpus_true_negative_integrity
  .py:44` asserts `tn == {"pattern_019_en_001"}`) and make D1 no longer lock-free. The
  FP guard is validated in the scorer test instead (next bullet).
- `tests/test_regex_scorer.py` — assert the new phrases fire on TP; AND add **direct
  scorer-silence assertions** for the FP guards (e.g. `scan("I honestly think it
  works")[<opener-key>] == 0` for the mid-sentence `honestly`, and a legitimate
  German-hedge string for `Die Sache ist die`). This validates the FP guard with zero
  corpus `true_negative` cases, so no TN-integrity lock is touched.
- **Version (PATCH — counts stay at 41, NO frozen-ID-set edit, NO "41→43"):**
  `SKILL.md` frontmatter `3.5.2 → 3.5.3`; `.claude-plugin/plugin.json` version
  `3.5.2 → 3.5.3` (description pattern-count unchanged); `README.md` version badge
  (`:3`) + table header (`:11`) → 3.5.3 + a `## Version History` `3.5.3` entry.
  **Do NOT touch historical `v3.5.2` references** that describe the shipped
  commentary-fence feature (`README.md:29/:188` + the 3.5.2 version-history entry `:356`)
  — bump only the current-version badge/header/frontmatter, not a blanket find/replace.

**Lock-free confirmation:** D1 adds NO new `### N.` pattern heading (so
`EN_PATTERN_IDS`/`DE_PATTERN_IDS` at `test_skill_structure.py:57/:143` are untouched),
NO pattern-count change (the "41" strings stay), and — with the FP guard moved to a
scorer-silence assertion — NO `true_negative:true` corpus case (so the TN-integrity
lock at `test_corpus_true_negative_integrity.py:44` is untouched). D1 is genuinely
lock-free.

## Validation

- **Gate 1 (zero-API hard gate):** full `pytest` green; `regex_scorer` fires on the
  new #20/#31 TP phrases and stays silent on the FP-guard strings (the direct
  scorer-silence assertions above).
- **Gate 2 (light, targeted — NOT the full 330-call re-baseline):** since these are
  watch-list adds to two existing patterns, validate with a **targeted**
  `run_pattern_eval.py --lang en --pattern 20` / `--pattern 31` (and `--lang de`),
  confirming the new phrases are detected and the patterns don't regress. Full-suite
  re-baseline is NOT required for a watch-list patch (MeetUp Outsider/First-Principles:
  don't burn a quota window confirming untouched patterns).

## Risks (Deliverable 1)

- **DE opener idiomaticity:** `Die Sache ist die` is borderline (real but very
  colloquial). Mitigated by flagging only standalone-hook use + a DE true_negative.
- **`Honestly?` vs `honestly` mid-sentence:** the FP guard (standalone only) + a
  mid-sentence true_negative case covers it.

---

# DELIVERABLE 2 (DEFERRED to v3.6.0) — #42 Aphorism Formulas + #43 Staccato

**Do NOT start without picking this up as separate work.** The two patterns are real,
distinct AI tells (MeetUp: Wikipedia-editor + AI-specialist confirm), but the MeetUp
surfaced BLOCK-level design issues the 3 linear Skeptic rounds missed. When resumed,
the spec for #42/#43 MUST resolve ALL of the following before writing-plans:

### Must-fix BLOCKs
1. **#43 cross-pattern collision.** #43's canonical examples are negation-fragment
   runs that collide with existing patterns: EN #9 owns "clipped tailing-negation
   fragments" (`en.md:147`); DE #9 triggers on `kein [Substantiv] (als angehängte
   Verneinung)` (`de.md:293`); DE #13 owns subjectless noun-phrase fragments
   (`de.md:407`) — the DE example "Keine Vorliebe… Kein Bauchgefühl. Keine Geschichte."
   triple-fires #9/#13/#43. **Fix:** use affirmative-staccato canonical examples (not
   negation runs); add #43↔#9 (EN+DE) and DE #43↔#13 non-overlap clauses (the spec
   must deconflict more than just #34); resolve the fix-rule contradiction — #43 says
   "merge, don't delete" while DE #9 says "immer streichen" (DE #34 already permits
   merge, so only #9 is a hard contradiction).
2. **#43 has no clean zero-API Gate-1.** `regex_scorer` is flat `(compiled_regex,
   label)` substring `findall`; a "≥3 consecutive short fragments" run is structural,
   not a substring. **Decide:** extend the scorer with a structural run-detector, OR
   route #43 to Gate-2 (LLM) only and write the gate honestly (do NOT claim "Gate-1
   fires on #43").

### Must-fix CONCERNs
3. **#42 false-negative / circularity.** The escalation clause routes to option B
   (`run_false_positive_eval.py`, a false-POSITIVE probe), but the gap is false-
   NEGATIVE: TP cases authored to match the anchor can't show "misses real aphorisms."
   Add held-out, non-anchor-derived aphorism TP cases.
4. **DE #42 Genitiv over-flag.** `die Sprache/die Währung <Genitiv>` risks flagging
   legitimate Fachsprache idiom ("die Sprache der Diplomatie"). Mirror the EN
   bare-copula exclusion; add DE-specific adversarial true_negative cases; the
   escalation clause (currently EN-only worded) must apply symmetrically to DE.
5. **Gate-2 regression baseline.** Name the exact baseline report file + figure +
   tolerance band — `summary_latest_en.md` carries 0.905, 0.619, AND 0.412; "no
   regression" is unfalsifiable without naming which.
6. **Lossy DE #43 after-example.** The DE #43 "after" rewrite must **merge** the
   fragments (per the #43 "restructure, don't delete" fix-rule), NOT amputate content
   — the draft DE after-example dropped "Bauchgefühl/Geschichte", which both teaches
   the wrong move and contradicts the fix-rule. Re-author the DE before/after as a
   true merge when #43 is picked up.

### Carried design decisions (still valid for #42/#43)
- New patterns go in the **language packs** (`en.md` + `de.md`, paired) as **#42**/
  **#43** (verified free), NOT `_universal.md`.
- #42 EN anchor uses distinctive lexicon only — exclude bare "X is the Y of Z" (copula
  facts) and "the architecture of" (collides with #35 example headings `en.md:421/428`).
- #43 DE title = "Inszenierte Pointe / dramatisierende Kurzsatz-Kette" (avoid the
  "Staccato" wording already in DE #34 `de.md:765/787`).
- FP discipline = regex true_negative gate (option A), incl. **≥3 adversarial copula
  TN cases** for #42; escalate to option B only if the #42 regex can't separate.

### Test/count locks #42/#43 WILL break (edit in the same task)
- `test_skill_structure.py:57` `EN_PATTERN_IDS` + `:143` `DE_PATTERN_IDS` — add 42, 43
  (exact-equality sets).
- `test_corpus_true_negative_integrity.py:44` — widen `tn == {"pattern_019_en_001"}` to
  the **exact** new TN case ids (enumerate, no glob), since the FP-gate cases carry
  `true_negative: true`.
- Count strings → 43: `SKILL.md:10/:38/:154`; `README.md:7/:14/:110/:139/:212/:214`
  (re-derive the "37 shared" figure from the real `_universal.md` + `de.md` sets — it
  does NOT cleanly reconcile today; do not perpetuate it); `plugin.json:4`;
  `marketplace.json:11`. Corpus files = `pattern_042.json` / `pattern_043.json` (en +
  de dirs); case ids `pattern_042_en_001` etc. Note: EN has no `pattern_041.json`
  (universal #41 has no EN corpus file) — don't assume an EN #41 baseline.

### Optional same-cut upside (Expansionist)
Capture the upstream-sync procedure (add remote → fetch → `git show <tip> -- SKILL.md`
→ map IDs onto our diverged catalogue → record divergences) + the standing divergence
list (em-dash exception, our #30–#43 numbering) as a durable `docs/UPSTREAM-SYNC.md`
Divergence Ledger, so future bumps are cheap.

## Out of scope (both deliverables)
- `_universal.md` changes; SKILL framework/mode/preflight changes; Wikipedia
  conduct-tells, citation/DOI validity; upstream's em-dash hard-cut (we keep the
  5-condition exception).
