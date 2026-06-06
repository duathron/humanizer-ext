# DE Mined Patterns — Phase 2 Task 5 Consolidated Output

**Source:** `mine_patterns.py` LLR run over DE corpus on 2026-05-28
- AI corpus: 132 docs (Wikipedia AI-tagged + Claude CLI gen + Opus inline synthesis)
- Human corpus: 46 docs (Wikipedia academic / career / marketing / technical + research-only Apple/Samsung/Microsoft/Heise/karrierebibel/lifestyle)
- Top 100 candidates; this doc consolidates top 50 after 3-voice persona meetup.

**Persona panel (votes per ngram):** Academic + Marketing Copywriter + Journalist (full responses in conversation transcript).

**Vote legend:**
- ✓ APPLY (unanimous or 2/3) — into `patterns/de.md`
- ◐ ADJUST (cluster threshold or register-specific)
- ✗ SKIP (artifact or common DE word)

Mining report raw: `evals/reports/mine_de_20260528.tsv`

---

## Consolidated keep list (mined → patterns/de.md)

Grouped by pattern target. Each entry includes mining rank + persona vote summary.

### #7 DE AI Vocabulary (extends EN #7 with DE-specific tokens)

Unanimous ✓ from all 3 personas — these are clear DE AI vocabulary tells:

| Token / phrase | Mining rank | LLR | AI:human ratio | Notes |
|----------------|-------------|-----|----------------|-------|
| `darüber hinaus` | #3 | 97.77 | 104:1 | DE equivalent of EN "furthermore"; classic additive-transition filler |
| `zusammenfassend` | #12 | 47.44 | 46:0 | Standalone summary opener; no journalist / copywriter uses this word |
| `ganzheitliche` / `ganzheitlich` | #47 | 26.81 | 26:0 | Management-speak buzzword; abstract use without product anchor = AI |
| `vorliegenden` / `der vorliegenden` | #20, #28 | 38.16, 34.03 | 37:0, 33:0 | "Die vorliegende Arbeit/Studie" academic-AI self-reference |
| `umfassende` | #39 | 28.77 | 35:1 | Cluster only — flag when stacked with `ganzheitlich` / `nachhaltig` / `vielfältig` |
| `darstellt` | #50 | 25.78 | 25:0 | Sentence-final bureaucratic copula in place of `ist` / direct verb |

Cluster-only (◐ ADJUST, threshold needed):

| Token | Cluster trigger | Notes |
|-------|----------------|-------|
| `zentrale` | `zentrale Rolle spielen` | Bare `zentrale` OK; the formulaic phrase is the tell |
| `rolle` | same as above | Subsumed in `zentrale Rolle` collocation |
| `wichtig` | `wichtig zu beachten` / `wichtig zu betonen` | See `#12 meta-commentary` below |
| `implementierung` | non-tech contexts | Legitimate in software docs; tells in management/HR contexts |
| `überzeugt` | unanchored | Legitimate in product copy when product-anchored; AI tells when floating |

### #100 / #101 (NEW DE-ONLY) — DE AI canonical phrase families

These have no EN equivalent and are highest-value DE-specific additions per all 3 personas. Reserved IDs #100 and #101 per maintainer decision (2026-05-27).

**#100 DE academic-frame boilerplate ("Im Rahmen der vorliegenden ...")** — unanimous ✓:

| Phrase | Mining rank | LLR | AI:human ratio |
|--------|-------------|-----|----------------|
| `im Rahmen der vorliegenden` (canonical 4-gram) | #32 | 31.97 | 31:0 |
| `rahmen der vorliegenden` | #31 | 31.97 | 31:0 |
| `im Rahmen der` | #27 | 34.65 | 41:1 |
| `im Rahmen` | #10 | 54.52 | 72:3 |

Anchor string for the pattern: **`im Rahmen der vorliegenden [Arbeit / Studie / Untersuchung / Analyse]`** — pure academic-AI self-reference; a journalist writes "in diesem Bericht", a copywriter writes nothing of the sort.

**#101 DE impersonal-reflexive AI hedge ("Es / zusammenfassend lässt sich ...")** — unanimous ✓ in canonical form:

| Phrase | Mining rank | LLR | AI:human ratio |
|--------|-------------|-----|----------------|
| `zusammenfassend lässt sich sagen` (canonical 4-gram) | #29 | 33.00 | 32:0 |
| `lässt sich feststellen` | #36 | 30.94 | 30:0 |
| `lässt sich sagen` | #23 | 36.09 | 35:0 |
| `es lässt sich` | #19 | 39.19 | 38:0 |
| `lässt sich` (bare bigram) | #5 | 93.73 | 100:1 |

Anchor string: **`[es / zusammenfassend] lässt sich [sagen / feststellen / festhalten / zeigen]`** — DE equivalent of EN "it can be said" / "it is to be noted". No real DE journalist or copywriter uses this construction. Structural Nominalstil-Inflation pattern.

### #12 DE meta-commentary / conclusion markers (extends EN #12)

Cluster of conclusion-flagging phrases (academic + journalist both flagged); marketing-copywriter mapped these to "meta-commentary":

- `wichtig zu` (opener of `wichtig zu beachten/betonen/bedenken`) — rank #48, LLR 26.81
- `feststellen` / `sich feststellen` (subsumed by `lässt sich feststellen` → #101)
- `zusammenfassend lässt sich sagen` (subsumed by #101)

---

## Skip list (mining artifacts + common DE)

**Confirmed mining-corpus artifacts** (all 3 personas agree — drop entirely):

| Token | Mining rank | Why artifact |
|-------|-------------|--------------|
| `hedging` | #13 | English term from Source C `tells_targeted` metadata (despite frontmatter strip — likely leaks via plain-text mentions in synthesis bodies) |
| `queens` | #16 | English proper noun — bleed from Wikipedia AI-tagged Queens-neighborhood articles in the Source A corpus |
| `substantivketten` | #25 | DE linguistics metalanguage; corpus artifact from Source C synthesis bodies that reference the term |
| `übergänge` | #30 | Likely artifact from Source B prompts mentioning "Überleitungswörter"; ambiguous in real prose |

**Volume artifacts** (high LLR but driven by corpus-size imbalance, not signal):

- `dass` (#1), `es` (#40), `sich` (#43), `ihre` (#41) — common DE function words

**Common DE words with insufficient discriminative power**:

- `ich` (#4), `meine` (#8), `bin` (#17), `mich` (#21) — first-person pronouns; corpus genre artifact (career/casual synthesis is heavy first-person), not structural AI tell. Journalist flagged `meine` for an attribution-discipline angle (DE-02 "AI performs first-person ownership where humans attribute"); academic + marketing both ✗. Maintainer: defer to v3.6.0 if needed.
- `dass die` (#11), `dass eine` (#35) — generic subordinator opener
- `es ist` (#37) — ubiquitous expletive
- `position` (#45), `bietet` (#49) — too generic in DE

---

## Maintainer follow-up

For Task 6 (`patterns/de.md` curation):

1. **#7 (DE AI Vocabulary)** entries from the mined top 6 above + the OQ1 manual Opus/Wikipedia-AI-Cleanup-Editor pass that builds out the full DE #7 trigger list (per maintainer decision OQ1 = "Manual curation by Opus + Wikipedia-AI-Cleanup-Editor persona").

2. **#100** anchor: `im Rahmen der vorliegenden [Arbeit/Studie/Untersuchung/Analyse]` + the prepositional variants. Distinct from the user's pre-approved DE-only pattern reservation (Konjunktiv II / Anglizismen / Nominalstil at #102/#103/#104). Mining proved this is the strongest DE-only AI tell — reserve #100 for it.

3. **#101** anchor: `[es/zusammenfassend] lässt sich [sagen/feststellen/festhalten/zeigen]`. Pair with #104 Nominalstil-Inflation as a sub-pattern (impersonales Reflexiv = canonical Nominalstil form for AI hedging).

4. **#12 (DE meta-commentary)** — extend the EN #12 entry with DE trigger list: `zusammenfassend`, `wichtig zu beachten/betonen`, the full #101 family.

5. **OQ4 sanity check passed:** mining confirms `gilt als` / `fungiert als` / `dient als` would extend EN #8 — they didn't surface in top 50 because corpus volume is smaller, but qualitatively present.

6. **Mining-script bug to fix in v3.6.0**: `tells_targeted` synthesis metadata still leaks despite frontmatter strip — likely the YAML metadata values appear in the body too because Opus inline synthesis demonstrably uses them. Workaround: drop the `tells_targeted` field from synthesis frontmatter in next pass, OR add a stopword list per-corpus.
