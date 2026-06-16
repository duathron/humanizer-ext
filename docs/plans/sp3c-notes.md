# SP3c notes — career-domain false-positive (over-edit) re-baseline (2026-06-14..16)

**Question:** does the humanizer over-edit the DACH career register (Anschreiben)? The legacy concern was a career FP ≈ 0.192.

**Answer (independent-Skeptic verified, "SP3c-CONCLUSION-SOUND"):** **No.** On a valid clean-Anschreiben corpus the skill preserves the register: **mean-of-medians 0.001, median 0, 0/8 over the 0.10 flag, 0 inconclusive, is_complete.** The 0.192 and the intermediate spikes were **measurement artifacts**, not skill behaviour.

## The arc (each step a measurement artifact dissolving under scrutiny)

1. **Wrong corpus (caught by user).** The first re-baseline ran on `de/human/redistributable/wikipedia_career` — Wikipedia **biographies/lists**, not the Anschreiben register. Mean ≈ 0.15 there is a general-prose over-edit signal, not the career-FP question. (That run was paused at 18/30; partials kept, not the answer.)
2. **"Anschreiben Muster" rejected.** Websearch for cover-letter templates → they are **formulaic Floskel prose the skill SHOULD edit** (high edit_ratio = correct, not a false positive) + copyright-encumbered. Using them as true-negatives would repeat the SP3b trap. Rejected.
3. **Built a valid corpus.** 8 synthetic clean individualized DACH Anschreiben (Opus career-writer), varied role/seniority, Floskel-free, concrete metrics. Spec: `docs/specs/2026-06-15-de-anschreiben-fp-corpus-spec.md`. Independent grade vs the spec → **CORPUS-MEETS-SPEC, 8/8 CLEAN** (2 initially carried tells — #22 escalated closer, #9 antithesis + #14 paired em-dash — revised; re-graded clean). Committed `1d1d60e` (corpus) + `1c1b5f1` (spec + grade fix).
4. **First FP run looked mixed** (mean 0.0576, 2/8 over 0.10) but every file was flaky (near-bimodal: a clean run ~0 OR a run ~0.2). The eval **discarded the rewrite text**, so the outliers couldn't be classified → added `--save-rewrites` (`db188c3`, Skeptic-SHIP: schema byte-identical, captured rewrite == measured text).
5. **Re-ran outliers with capture → root cause found.** In all 10 captured runs the **letter body is byte-identical** to the input; the entire edit distance is a **trailing self-note** the skill appends (e.g. *"Text unverändert — kein einziges KI-Tell, kein Eingriff nötig."*). Not over-editing, not a corpus tell — a **commentary-leak scoring bug**. (Skeptic: BENIGN-VARIANCE.)
6. **Fix location — scorer-side, not the parser.** A regex extension to the shared commentary-stripper was attempted and **reverted** (`74ed2de`/`0367075`/`d10d6c2` dropped): the preservation-note openers ("No changes", "Keine Änderung", "Anschreiben ist gut", …) are legit sentence-starters and the kept "meta" tokens (`Eingriff`, `menschlich`, `register`, `audit`, …) are ordinary words → it false-stripped real prose across ALL evals (Skeptic FIX-FIRST, twice). Replaced with a **provably-safe scorer guard** (`49aebaa`, Skeptic-SHIP): in `_score_human_text_once`, if the rewrite is the **verbatim input + a trailing block**, the body is unedited → score body-only (edit_ratio 0); the real rewrite (incl. note) is kept for the sidecar. Fires ONLY on a byte-identical body prefix → a single changed char restores full distance → cannot mask a real edit. (FP corpus items are 900–1835-char paragraphs, so the accidental-short-prefix worst case is structurally impossible.)
7. **Guarded re-run → the answer.** Mean 0.001, 0/8 over, all medians 0. Former outliers `marketing_senior`/`elektroniker` → 0. The 2 remaining 1/5 flaky spikes (`swe` 0.189, `vertrieb` 0.144) are **~95% the trailing note**; their body changes are **correct #14-mandated em-dash removals** (both originals have 2 em-dashes in ~170 words → fail #14's "no other em-dash within 500 words" exception). Median absorbs them.

## Disposition
- **SP3c career-FP: closed — no over-edit of the DACH career register.** No skill change warranted by this measure.
- **Eval-infra added (eval-only, SKILL.md byte-identical):** the Anschreiben FP corpus, its spec, `--save-rewrites` diagnosis, and the verbatim-plus-commentary scorer guard.
- **Remaining minor artifact (not blocking):** the skill appends a self-note on ~1/5 runs; on a run that ALSO has a real body edit, the guard can't fire and the note inflates that single run's ratio (median absorbs it; mean = 0.001). The durable cure is the skill not emitting notes in Quick mode — the **commentary-fence** backlog sub-project (a SKILL.md change with its own eval).
- **Caveats:** synthetic corpus, N=8, runs=5 — small; same synthetic-origin caveat as the EN synthetic corpus (real anonymized Anschreiben are future work).
- **Not done:** the `wikipedia_career`/redistributable general-FP run (18/30, paused) — a separate general-prose over-edit baseline, not the career question.

## Commits (unpushed at time of writing — held per user)
The held stack is these 4 + this notes commit (5 total on local `main` ahead of origin `c4de878`):
`1d1d60e` corpus · `1c1b5f1` spec+grade · `db188c3` --save-rewrites · `49aebaa` scorer guard · (this) SP3c notes. 346 pytest. (`74ed2de`/`0367075`/`d10d6c2` were the reverted regex attempt — not in history after `git reset --hard db188c3`.)
