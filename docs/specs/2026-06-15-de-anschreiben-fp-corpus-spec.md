# Spec — DE synthetic Anschreiben false-positive corpus (SP3c)

**Date:** 2026-06-15
**Status:** drafted after synthesis; the 8 generated files are to be graded **independently** against this spec before any FP eval runs.
**Owner sub-project:** SP3c (career-domain false-positive / over-edit re-baseline).

## 1. Purpose

The false-positive (FP) eval (`run_false_positive_eval.py`) measures whether the humanizer **over-edits clean human text** — text it should largely leave alone. The verdict per case is `edit_ratio` (fraction changed) aggregated over `--runs N` (median); `above_threshold` flags `edit_ratio > 0.10`.

SP3c's question: **does the skill over-edit the DACH career register (Anschreiben)?** The original concern was a ~0.192 career FP figure. That figure was measured on the wrong corpus. This corpus exists to measure it on a **valid** one.

## 2. Why the prior corpora are invalid for this question (motivation)

- **`wikipedia_career` (biographies / lists):** clean prose, but the *encyclopedic* register, not the *Anschreiben* register. Measures general DE over-edit, not the career-letter question. (Kept as a separate general baseline; paused.)
- **"Anschreiben Muster" from template sites:** formulaic template prose full of Floskeln the skill is **designed to edit**. A high edit_ratio there is a *correct* edit, not a false positive. Using them as true-negatives repeats the **SP3b bug** (treating editable AI-tell text as a true-negative). Also copyright-encumbered → not redistributable.

**Therefore:** the FP corpus must be **clean, individualized, well-written Anschreiben** — the kind a strong applicant actually writes — in the exact DACH register the skill's `career` domain is tuned to **preserve**.

## 3. The FP-validity principle (the core acceptance idea)

A case is a valid FP true-negative **iff a correct humanizer pass would leave it (almost) unchanged.** Concretely: the text must contain **no AI-tell the `career` domain is configured to edit**, AND it must contain **substance the preserve-rules protect** (so a low edit_ratio reflects correct restraint, not an empty input).

If a sample contains a real tell, the skill *should* edit it → its edit_ratio is a true positive → it must NOT be in this corpus. This is the single most important rule.

## 4. Register definition (from `domains/de_overrides.md` "career")

DACH Anschreiben register = **formal-modest**: formal "Sie" throughout, first-person active voice ("Ich habe geleitet/entwickelt/umgesetzt"), factual claims with evidence, **understatement over puffery**. US/UK assertive self-promotion is the *opposite* of correct here.

## 5. Tell-absence catalogue (MUST be absent — each = a disqualifying tell)

Drawn from the career cut-list + the universal/DE pattern catalogue. A sample with any of these is FLAGGED:

**Career-specific (de_overrides cut-list):**
- **Chatbot openers:** "Mit großem Interesse habe ich Ihre Stellenanzeige gelesen", "Ich bewerbe mich hiermit auf Ihre Stellenausschreibung".
- **Sycophantic closers (escalated):** "Ich freue mich auf die Gelegenheit, Sie persönlich kennenzulernen", "Ich würde mich **sehr** über eine Einladung … freuen", "es würde mich **außerordentlich** freuen", "Vielen Dank für Ihre Berücksichtigung". *(A bare, un-intensified "Über ein Gespräch würde ich mich freuen" is the conventional minimal DACH closer and is allowed.)*
- **Cliché self-praise (bare buzzwords):** leidenschaftlich, ergebnisorientiert, ganzheitlich denkend, zielorientiert, kommunikationsstark, teamfähig, belastbar, "ich sehe mich als idealen Kandidaten".
- **DE-AI compound Floskeln:** "ich bin davon überzeugt, dass", "im Rahmen meiner bisherigen Tätigkeit", "konnte ich umfassende Erfahrung sammeln", "ein vielfältiges Spektrum an Aufgaben", company flattery ("renommiert/innovativ").

**Universal / DE pattern tells (must also be absent):**
- #9 antithesis / appended-negation rhetorical frames ("Was ich nicht bin: …", "nicht X, sondern Y" used as a *hollow* flourish; "statt [X]"-Abweisung of an unclaimed alternative). *(Literal propositional negation with real content on both sides is allowed.)*
- #14 paired em-dash bracketing (em dash as a matched pair around an aside) — disallowed; a single appositive/pivot em dash is tolerated but watch density.
- #10 rule-of-three / trikolon padding; Doppelpunkt-trikolon.
- Connector-stacking (Darüber hinaus / Zudem / Des Weiteren), "nicht nur … sondern auch".
- Nominalstil (bureaucratic noun-cluster phrasing), Konjunktiv-II stacking ("würde … können").
- Inflated adjectives, vague claims without evidence, uniform paragraph rhythm, empty-enthusiasm affect beats ("und freue mich darauf" with no content).

## 6. Positive requirements (MUST be present — so low edit_ratio means restraint, not emptiness)

- **Concrete metrics** (≥1 real number/percentage/Eurobetrag/Teamgröße/Zeitersparnis), stated verbatim — the preserve-rule "Metriken sind heilig" needs something to preserve.
- **Named specifics:** at least some Eigennamen/tools/methods/dates/role titles (Fachvokabular).
- **A concrete achievement or project narrative** (not generic duties).
- **Genuine motivation substance** (why this role) expressed in understated form — an Anschreiben with zero motivation is incomplete.
- **Individual voice:** each of the 8 reads as a *different person* (distinct rhythm, hook, and where fitting an honest "what I can't do yet" admission). Not one template with swapped nouns.

## 7. Coverage matrix (8 cases, vary register breadth)

| # | Role | Seniority/situation |
|---|------|---------------------|
| 1 | Softwareentwickler:in | Berufseinsteiger (nach Studium) |
| 2 | Projektmanager:in | erfahren, Stellenwechsel |
| 3 | Pflegefachkraft | erfahren |
| 4 | Vertrieb | Quereinsteiger:in |
| 5 | Industriekaufmann/-frau | Ausbildung (Schulabgänger:in) |
| 6 | Marketing-Manager:in | Senior |
| 7 | Elektroniker:in / Facharbeiter:in | Handwerk/Industrie |
| 8 | Data Analyst:in / wiss. Mitarbeiter:in | Quereinstieg/Wissenschaft |

## 8. File format & provenance

- Path: `evals/corpus/de/human/synthetic/anschreiben_<role>_01.md` (8 files) + `_SOURCE.md` sidecar.
- Frontmatter (matches `_read_sample`): `domain: career`, `lang: de`, `notes:` describing synthetic-clean origin. Body = Betreff, Anrede, paragraphs, Gruß; ~160–240 words.
- `_SOURCE.md`: synthetic Opus-generated; **not** scraped from Muster sites (no third-party copyright); placed in the `synthetic` bucket (mirrors EN synthetic).
- Discovered by `_discover_corpus_files` (the `_`-prefixed sidecar is excluded).

## 9. Known caveats (state honestly)

- **Synthetic, not sourced human prose.** Same caveat as the EN synthetic corpus (STATUS notes it). An LLM wrote these; subtle AI-tells are possible → §5 grading is the guard. Real anonymized Anschreiben are future work.
- **Self-referential risk:** the corpus is written by an LLM and graded against the same skill's catalogue; the independent grade (§11) mitigates but does not eliminate this. A genuinely-human-sourced set would be stronger.

## 10. Acceptance criteria

**Per sample (all must hold):** correct frontmatter (§8); ≥1 concrete metric (§6); a concrete achievement/narrative (§6); expressed motivation (§6); **zero** §5 tells; distinct voice (§6).

**Corpus-level:** 8/8 samples pass; coverage matrix (§7) filled; `_SOURCE.md` present and honest; runner discovers exactly 8.

**A sample failing any per-sample criterion is FLAGGED and must be revised or dropped before the FP eval runs.**

## 11. Independent validation (required before any eval)

A reviewer with **no stake in the synthesis** grades all 8 files against §5/§6/§10, quoting evidence per sample, against the actual `patterns/de.md` + `_universal.md` + `de_overrides.md`. Verdict per sample CLEAN/FLAGGED; corpus CORPUS-VALID only if 8/8 CLEAN. (Done iteratively: round 1 flagged 2 — escalated closer #22, #9 antithesis + #14 bracket — revised; re-grade required against THIS spec.)

## 12. Usage & interpretation (after validation passes)

- Run: `run_false_positive_eval.py --lang de --corpus synthetic --runs 5`.
- **LOW mean edit_ratio = desired** (skill correctly preserves clean career prose). `above_0.10` / `above_0.15` counts reported.
- A HIGH mean = the skill over-edits the DACH career register → the real, validly-measured version of the original 0.192 concern → would trigger its **own** brainstorm→spec→plan for a skill/override change (NOT done reflexively).
- Numbers independent-Skeptic verified from per-case partials before any conclusion. Eval-only; SKILL.md unchanged; nothing pushed without explicit user OK.
