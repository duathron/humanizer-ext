# DE Seed Catalogue — Phase 2 Foundation

**Source:** https://de.wikipedia.org/wiki/Wikipedia:Anzeichen_f%C3%BCr_KI-generierte_Inhalte
**Extracted:** 2026-05-27
**Purpose:** Phase A seed catalogue for `patterns/de.md` curation in v3.5.0. Each DE tell is cross-referenced to the existing EN pack with a categorization decision.

---

## Categorization decisions

For each DE tell, decide:
- **UNIVERSAL** — already covered by `patterns/_universal.md` (e.g., em dashes, curly quotes, emojis, chat-UI artifacts). No DE-specific entry needed; the universal pattern catches it.
- **EN-PARALLEL #N** — has a direct EN equivalent in `patterns/en.md` under pattern #N. DE version goes in `patterns/de.md` under the same number; trigger words + examples translated/adapted.
- **DE-ONLY #100+** — no EN equivalent (typically: Nominalstil-Inflation, Konjunktiv-Stack, Anglizismen-Leakage, German-specific formulaic phrases). Goes in `patterns/de.md` under #100+ per the multi-lingual spec convention.

---

## Tells

---

### Falsche Belege (False / Hallucinated References)

- **Trigger words / phrases:** inexistent DOI, ISBN, URLs that 404, author names that don't exist, quoted assertions not present in cited source
- **DE Wiki example (before):** (none given verbatim; guidance only — verify existence, author, title, year, publisher, DOI/ISBN and that the quoted claim appears in the source)
- **DE Wiki suggested fix (after):** Verify all citations before publication; remove or rewrite any that cannot be confirmed
- **EN cross-reference:** EN-PARALLEL #5 — EN pack pattern #5 covers vague attributions / weasel words, which is the closest EN analogue (unverifiable authority claims). However, the DE Wiki source treats hallucinated citations as a *definitive* hard indicator and puts them in a separate "eindeutig" (definitive) tier above soft signs. In the DE pack this needs its own entry rather than being folded under #5.
- **Notes:** Applies universally across all domains — a hallucinated citation in a legal brief or academic paper is as damaging as in a casual blog post. Flag as DE-ONLY candidate if we need to mark the stricter deletion threshold (Schnelllöschantrag territory). Revisit at Task 6.

---

### Briefartiges Schreiben (Letter-like / Email-style Preamble)

- **Trigger words / phrases:** `Betreff:`, `Liebe Wikipedia-Editoren`, `Ich hoffe, diese Nachricht erreicht Sie wohlauf`, `Vielen Dank für Ihre Zeit`, subject-line formatting mimicking email
- **DE Wiki example (before):** "Betreff: Ergänzung zum Artikel. Liebe Wikipedia-Editoren, ich hoffe, diese Nachricht erreicht Sie wohlauf."
- **DE Wiki suggested fix (after):** Remove entirely; encyclopedia edits and encyclopedic prose never open with a salutation or subject line
- **EN cross-reference:** EN-PARALLEL #20 — EN pack pattern #20 (Collaborative Communication Artifacts) covers "Here is an overview…" and chatbot-correspondence preambles. The DE variant is more formal/letter-style; the EN variant trends more chatbot-helpful. Same root cause, both map to #20.
- **Notes:** More conspicuous in German because German formal letters follow a very specific DIN 5008 structure — the bot mimics letter conventions. Strongest in casual and career domains; irrelevant in technical and legal output.

---

### Kollaborative Kommunikation (Chatbot Collaboration Phrases)

- **Trigger words / phrases:** `Ich hoffe, das hilft`, `Natürlich!`, `Sicherlich!`, `gibt es noch etwas`, `lassen Sie mich wissen`, `detailliertere Aufschlüsselung`, `hier ist ein`
- **DE Wiki example (before):** "Natürlich! Hier ist eine detailliertere Aufschlüsselung. Ich hoffe, das hilft. Lassen Sie mich wissen, wenn Sie mehr möchten."
- **DE Wiki suggested fix (after):** Delete all chatbot-handshake language; begin with the actual content
- **EN cross-reference:** EN-PARALLEL #20 — direct German translation of the EN pattern #20 (Collaborative Communication Artifacts: "I hope this helps!", "Of course!", "Certainly!"). These are the German surface forms of the same underlying LLM behavior.
- **Notes:** The DE Wiki notes that these phrases feel like literal English translations and are foreign to German Wikipedia's traditionally reserved tone. Add the specific German trigger strings to `patterns/de.md` under #20.

---

### Hinweise auf Wissenslücken (Knowledge-Cutoff / Limitation Disclaimers)

- **Trigger words / phrases:** `Stand [Datum]`, `Bis zu meinem letzten Update`, `Obwohl spezifische Details begrenzt/rar sind`, `nicht allgemein verfügbar/dokumentiert`, `basierend auf verfügbaren Informationen`
- **DE Wiki example (before):** "Basierend auf verfügbaren Informationen und bis zu meinem letzten Update stand die Situation wie folgt."
- **DE Wiki suggested fix (after):** If the information genuinely has a cutoff date, state it plainly as a factual note; delete the LLM-disclosure framing entirely
- **EN cross-reference:** EN-PARALLEL #21 — German surface forms of EN pattern #21 (Knowledge-Cutoff Disclaimers and Speculative Gap-Filling). `Stand [Datum]` = "as of [date]"; `bis zu meinem letzten Update` = "up to my last training update".
- **Notes:** Add the specific German trigger strings to `patterns/de.md` under #21.

---

### Platzhaltertext (Unfilled Placeholder Text)

- **Trigger words / phrases:** `[DATUM]`, `[NAME EINFÜGEN]`, `[QUELLE]`, `[HIER ERGÄNZEN]`, `2025-xx-xx`, `___`, `<Platzhalter>`
- **DE Wiki example (before):** (not given verbatim; general guidance that template blanks are left unfilled)
- **DE Wiki suggested fix (after):** Use correct Wikipedia template structure; fill in or remove placeholders before publishing
- **EN cross-reference:** UNIVERSAL — covered by `patterns/_universal.md` pattern #39 (Phrasal Templates and Placeholder Text). German placeholder tokens are the same artifact class; no separate DE entry needed.
- **Notes:** The specific German token variants (`[DATUM]`, `[NAME EINFÜGEN]`) can be added to #39's token list in `_universal.md` rather than in `patterns/de.md`.

---

### Einbindung nicht existierender Vorlagen (Non-existent Wikitext Templates)

- **Trigger words / phrases:** `{{VorlagenName}}` with parameters that don't exist in German Wikipedia; invalid parameter names inside existing templates
- **DE Wiki example (before):** (no verbatim example given; LLM generates plausible-sounding `{{Infobox Person|...}}` with invented parameters)
- **DE Wiki suggested fix (after):** Verify template existence and all parameters against German Wikipedia's template catalogue
- **EN cross-reference:** DE-ONLY #100 — the EN pack has no equivalent because this is a Wikipedia-editing-specific artifact tied to Wikitext. Outside Wikipedia editing it does not surface. However, within Wikipedia context it is a strong hard indicator. Tag as DE-ONLY with a note that it applies only in wiki-editing domain.
- **Notes:** Wikipedia-domain only. Not relevant to general prose humanization work (casual, academic, legal, technical, marketing, career).

---

### Werbesprache (Promotional / Marketing Language)

- **Trigger words / phrases:** `reiches kulturelles Erbe`, `atemberaubend`, `unbedingt besuchen`, `beeindruckende natürliche Schönheit`, `bleibendes Vermächtnis`, `reicher kultureller Teppich`, `im Herzen von`
- **DE Wiki example (before):** "Im Herzen von Bayern liegt diese atemberaubende Stadt mit einem reichen kulturellen Erbe, die man unbedingt besuchen sollte."
- **DE Wiki suggested fix (after):** Replace with verifiable, neutral encyclopedic claims: population, location, notable facts
- **EN cross-reference:** EN-PARALLEL #4 — direct German equivalents of EN pattern #4 (Promotional and Advertisement-like Language). `atemberaubend` = "breathtaking"; `im Herzen von` = "in the heart of"; `reiches kulturelles Erbe` = "rich cultural heritage".
- **Notes:** DE pack entry under #4 should list these specific German trigger strings. Domain override: SKIP in marketing domain (same as EN). Light in career domain.

---

### Redaktionelle Kommentare (Editorial / Authorial Intrusions)

- **Trigger words / phrases:** `es ist wichtig zu bemerken`, `es ist bemerkenswert`, `keine Diskussion wäre vollständig ohne`
- **DE Wiki example (before):** "Es ist wichtig zu bemerken, dass diese Entwicklung weitreichende Folgen hatte. Keine Diskussion dieses Themas wäre vollständig ohne einen Hinweis auf …"
- **DE Wiki suggested fix (after):** Delete the intrusion and state the fact directly; the authorial voice is inappropriate in encyclopedic prose
- **EN cross-reference:** EN-PARALLEL #23 — German surface forms of EN pattern #23 (Filler Phrases). `es ist wichtig zu bemerken` = "it is important to note that"; `es ist bemerkenswert` = "it is worth noting that".
- **Notes:** The DE Wiki specifically notes that these feel especially out of place given German Wikipedia's traditionally reserved, authorial-voice-free tone. Add specific German trigger strings to `patterns/de.md` under #23.

---

### Bestimmte Konjunktionen / Transitionswörter (Mechanical Transition Words)

- **Trigger words / phrases:** `andererseits`, `darüber hinaus`, `zusätzlich`, `außerdem`, `ferner`, `des Weiteren`, `infolgedessen`
- **DE Wiki example (before):** "Andererseits ist zu beachten, dass … Darüber hinaus zeigt sich … Außerdem ist festzustellen …"
- **DE Wiki suggested fix (after):** Restructure into logical flow that doesn't require mechanical connectors; use one where genuinely needed
- **EN cross-reference:** DE-ONLY #101 — the EN pack has no dedicated pattern for transition-word overuse (EN patterns track other symptoms). German LLM output stacks these connectors more mechanically than English because German prose convention calls for explicit Satzverknüpfung, making the over-use a culture-specific amplification. The specific German tokens need their own DE pattern.
- **Notes:** Applies across all domains. In academic and legal writing, transition words are appropriate — flag only when 3+ appear in close proximity without logical justification (same threshold as EN light-mode patterns).

---

### Abschnitts-Zusammenfassungen (Section-Level Summary Formulas)

- **Trigger words / phrases:** `zusammenfassend`, `abschließend`, `insgesamt`, `alles in allem`, `im Großen und Ganzen`
- **DE Wiki example (before):** "Zusammenfassend lässt sich sagen, dass dieser Abschnitt gezeigt hat, dass …" (mid-article, not at article end)
- **DE Wiki suggested fix (after):** Delete the summary sentence; each section should end with its last substantive point, not a recap
- **EN cross-reference:** EN-PARALLEL #25 — German surface forms of EN pattern #25 (Generic Positive Conclusions / Summary Sections). The DE Wiki flags these in mid-article positions too, not just at the end; same underlying behavior.
- **Notes:** Domain override: in academic papers, a genuine section summary is conventional — only flag when it is purely repetitive with no new information. In casual, marketing, career writing: flag strictly.

---

### Fazit-Überschrift (Explicit "Fazit" / Conclusion Heading)

- **Trigger words / phrases:** `## Fazit`, `## Schluss`, `## Zusammenfassung`, `## Abschließende Bemerkungen`, `## Schlussfolgerung`
- **DE Wiki example (before):** An encyclopedia article that ends with a `## Fazit` section restating the preceding body
- **DE Wiki suggested fix (after):** Delete the section entirely; encyclopedic articles end with their last substantive paragraph
- **EN cross-reference:** UNIVERSAL — covered by `patterns/_universal.md` pattern #25's structural-section note ("A common AI tic is a whole `## Conclusion`… section whose only job is to restate the body"). The German heading variants (`Fazit`, `Schluss`, `Schlussfolgerung`) should be added to the universal pattern's token list.
- **Notes:** Exception: in German medical and scientific journal articles, a `Fazit` section is conventional. Apply the same academic-domain SKIP logic as in EN.

---

### Schlussfolgerungen mit Formelstruktur (Formulaic Conclusion Structure)

- **Trigger words / phrases:** `Trotz seiner Erfolge`, `Trotz dieser Herausforderungen`, `steht vor mehreren Herausforderungen`, `Vermächtnis`, `Zukunftsaussichten`, `Blick in die Zukunft`
- **DE Wiki example (before):** "Trotz seiner bemerkenswerten Erfolge steht [Thema] vor mehreren Herausforderungen. Das Vermächtnis bleibt jedoch unbestreitbar. Die Zukunftsaussichten sind vielschichtig."
- **DE Wiki suggested fix (after):** If challenges are real and sourced, state them with specifics; delete the speculation about legacy and future outlook unless grounded in cited fact
- **EN cross-reference:** UNIVERSAL — covered by `patterns/_universal.md` pattern #6 (Outline-like "Challenges and Future Prospects" Sections). `Trotz seiner Erfolge … steht vor mehreren Herausforderungen … Zukunftsaussichten` is the German surface form of the "Despite its … faces challenges … Future Outlook" universal pattern.
- **Notes:** Add the German trigger strings to the universal pattern's "Words to watch" list.

---

### Negative Parallelismen (Negative Parallelisms)

- **Trigger words / phrases:** `nicht nur …, sondern auch`, `es geht nicht nur um …, sondern`, `nicht lediglich …, sondern vielmehr`
- **DE Wiki example (before):** "Es geht nicht nur um wirtschaftliche Faktoren, sondern auch um kulturelle und soziale Dimensionen."
- **DE Wiki suggested fix (after):** Cut the rhetorical frame; state the actual claim directly
- **EN cross-reference:** EN-PARALLEL #9 — German surface form of EN pattern #9 (Negative Parallelisms, Tailing Negations, and "Rather Than" Dismissals). `nicht nur … sondern auch` = "not only … but also"; same structural AI pattern.
- **Notes:** Add the German trigger strings to `patterns/de.md` under #9.

---

### Trikolon (Rule of Three / Rhetorical Tripling)

- **Trigger words / phrases:** Three-part adjectival or noun strings; `sowohl … als auch … und`; `erstens … zweitens … drittens` used formulaically
- **DE Wiki example (before):** "Die Region ist bekannt für ihre atemberaubende Landschaft, ihr reiches kulturelles Erbe und ihre herzliche Gastfreundschaft." (every sentence structured as a triad)
- **DE Wiki suggested fix (after):** Break the formula; use the number of points the content actually warrants
- **EN cross-reference:** EN-PARALLEL #10 — German surface form of EN pattern #10 (Rule of Three Overuse). `sowohl … als auch … und` is the German structural equivalent.
- **Notes:** In German, the `sowohl … als auch` construction is a natural conjunction, so flag only when tripling is excessive and formulaic rather than for every instance. Domain override: light in marketing and casual domains (same as EN).

---

### Oberflächliche Analysen mit Partizip-I (Superficial Analyses via Present Participles)

- **Trigger words / phrases:** `gewährleistend`, `hervorhebend`, `betonend`, `widerspiegelnd`, `untermauernd`, `verdeutlichend`, `veranschaulichend`, `aufzeigend`
- **DE Wiki example (before):** "Die Maßnahmen, die kulturelle Vielfalt hervorhebend und gleichzeitig gesellschaftliche Werte betonend, spiegeln das Engagement wider."
- **DE Wiki suggested fix (after):** Rewrite with finite verbs: "Die Maßnahmen heben die kulturelle Vielfalt hervor und betonen gesellschaftliche Werte."
- **EN cross-reference:** EN-PARALLEL #3 — German grammatical surface form of EN pattern #3 (Superficial Analyses with -ing Endings). In English the tell is tacked-on gerund/present-participle clauses; in German the parallel construction is dangling Partizip-I phrases. Same LLM behavior, different surface.
- **Notes:** DE-SPECIFIC SEVERITY NOTE: The DE Wiki marks this as "als pretentiös geltend" (considered pretentious) in German Wikipedia — it carries a slightly stronger social stigma than in English Wikipedia. Flag in all domains; no override.

---

### Vage Autoritäten / Weasel Words (Vague Attributions)

- **Trigger words / phrases:** `Branchenberichte`, `Beobachter haben zitiert`, `Einige Kritiker argumentieren`, `laut Experten`, `wie Beobachter festgestellt haben`, `Quellen zufolge`
- **DE Wiki example (before):** "Laut Experten und Branchenberichten hat die Entwicklung weitreichende Folgen. Einige Kritiker argumentieren, dass …"
- **DE Wiki suggested fix (after):** Name the specific expert, report, or critic with a verifiable citation
- **EN cross-reference:** EN-PARALLEL #5 — German surface form of EN pattern #5 (Vague Attributions and Weasel Words). `Branchenberichte` = "Industry reports"; `Einige Kritiker argumentieren` = "Some critics argue".
- **Notes:** Add German trigger strings to `patterns/de.md` under #5.

---

### Falsche Erweiterung mit "von … bis" (False Range / "Von X bis Y" Constructions)

- **Trigger words / phrases:** `von … bis`, `von A bis Z`, `von Kultur bis Wissenschaft`, `von lokalen bis globalen Themen`
- **DE Wiki example (before):** "Das Werk umfasst Themen von der individuellen Erfahrung bis hin zu gesellschaftlichen Strukturen, von der lokalen Gemeinschaft bis zur globalen Vernetzung."
- **DE Wiki suggested fix (after):** List the actual topics concretely; remove the X-to-Y rhetorical spanning frame
- **EN cross-reference:** EN-PARALLEL #12 — German surface form of EN pattern #12 (False Ranges). `von … bis hin zu` = "from X to Y". Same LLM rhetorical habit.
- **Notes:** Add the German construction `von … bis (hin zu)` to `patterns/de.md` under #12.

---

### Übermäßige Fettschrift (Excessive Bold Formatting)

- **Trigger words / phrases:** Heavy use of `'''bold'''` in Wikitext or `**bold**` in Markdown for emphasis throughout body text
- **DE Wiki example (before):** Prose with multiple bolded words per paragraph, copied from chatbot FAQ-style output
- **DE Wiki suggested fix (after):** Remove bold except for the article's subject at first mention (standard German Wikipedia convention)
- **EN cross-reference:** UNIVERSAL — covered by `patterns/_universal.md` pattern #15 (Overuse of Boldface). No separate DE entry needed.
- **Notes:** The German Wikipedia convention for bold is even narrower than general usage (subject name at first mention only), making violations more visible. No new DE pattern entry needed; the universal pattern covers it.

---

### Listen-Formatierung (List Formatting from Chatbot)

- **Trigger words / phrases:** Raw bullet characters `•` or dash `-` instead of Wikitext `*`; numbered lists `1.` instead of `#`; mismatched indentation levels
- **DE Wiki example (before):** Prose pasted from chatbot with `•` bullets or `-` dashes preserved
- **DE Wiki suggested fix (after):** Convert to proper Wikitext list syntax or restructure as prose
- **EN cross-reference:** UNIVERSAL — partially covered by `patterns/_universal.md` pattern #40 (Markdown / Wikitext Contamination). The specific raw-bullet artifact (`•`, `-`) is a subset of that pattern.
- **Notes:** Not a standalone new DE entry; add `•` and `-` as raw-bullet tokens to the universal #40 pattern if not already present.

---

### Emojis

- **Trigger words / phrases:** Emojis preceding headings (`🔹 Abschnitt`), emojis in bullet points, emoji-decorated titles
- **DE Wiki example (before):** "🌍 Geschichte. 📚 Kultur. ✅ Fazit."
- **DE Wiki suggested fix (after):** Remove all emojis from encyclopedic and Wikipedia prose
- **EN cross-reference:** UNIVERSAL — covered by `patterns/_universal.md` pattern #18 (Emojis). No DE entry needed.
- **Notes:** The DE Wiki calls emojis "grundsätzlich ungewöhnlich" (fundamentally unusual) in German Wikipedia, echoing the universal pattern. No new entry.

---

### Gedankenstriche / Halbgeviertstriche (Em-Dash Overuse)

- **Trigger words / phrases:** Halbgeviertstrich `–` (U+2013) used where a simple Bindestrich `-` is correct; typographically correct but contextually wrong
- **DE Wiki example (before):** "Die Stadt – mit ihrer langen Geschichte – gilt als bedeutendes Zentrum." (or simpler cases where a plain hyphen suffices)
- **DE Wiki suggested fix (after):** Replace with comma or period; only use Gedankenstrich for genuine parenthetical interruption
- **EN cross-reference:** UNIVERSAL — covered by `patterns/_universal.md` pattern #14 (Em Dash Overuse and Paired Bracketing). The German convention also distinguishes Gedankenstrich (–, parenthetical) from Bindestrich (-), making violations doubly conspicuous.
- **Notes:** German adds a layer: the DE Wiki flags the Halbgeviertstrich (–, U+2013) specifically rather than the EN Geviertstrich (—, U+2014). Both are covered by the universal pattern, but the DE pack entry under #14 should note both characters and explain the German typographic distinction.

---

### Markdown-Syntax statt Wikitext (Markdown Contamination)

- **Trigger words / phrases:** `*fett*` or `**fett**` instead of `'''fett'''`; `#Überschrift` instead of `== Überschrift ==`; `[text](url)` instead of `[[text|url]]`; `---` thematic breaks; ` ``` ` fenced code blocks
- **DE Wiki example (before):** "**Hintergrund**\n---\nDie Stadt wurde 1243 gegründet." (Markdown heading+divider format)
- **DE Wiki suggested fix (after):** Convert to correct Wikitext; no Markdown in German Wikipedia
- **EN cross-reference:** UNIVERSAL — covered by `patterns/_universal.md` pattern #40 (Markdown / Wikitext Contamination). No separate DE entry needed; the universal pattern fully covers it.
- **Notes:** The DE Wiki provides a detailed Markdown-vs-Wikitext comparison (stars vs. apostrophes for bold/italic, hash vs. equals for headings, parentheses vs. brackets for links) — these specifics can be added as a German-context note to the universal #40 pattern.

---

### "Gehe zu Suche Nr." Artefakt (Search-Link Placeholder Artifact)

- **Trigger words / phrases:** `(Gehe zu Suche Nr.)freimaurerei+1` (increments through text), `(Gehe zu Suche Nr.)topic+N`
- **DE Wiki example (before):** "Simmel, Georg: _Die Ritualdimensionen der Freimaurerei_ (Gehe zu Suche Nr.)freimaurerei+1"
- **DE Wiki suggested fix (after):** Delete artifact; verify and replace with a real Wikitext citation if the source is real
- **EN cross-reference:** UNIVERSAL — this is the German-language chatbot's version of the EN `turn0search0` / `citeturn0search0` reference-markup artifacts covered by `patterns/_universal.md` pattern #38 (Reference-Markup Artifacts). The German string `(Gehe zu Suche Nr.)topic+N` should be added as a token to the universal #38 pattern.
- **Notes:** Observed starting February 2025 per DE Wiki. The token pattern `(Gehe zu Suche Nr.)` is highly distinctive — add to #38's token list in `_universal.md`.

---

### Inkorrekte Referenzformatierung (Wrong Citation Format)

- **Trigger words / phrases:** EN Wikipedia `{{cite web}}` syntax used in DE context; `{{Literatur}}` with English-language parameter names; `access-date` instead of `abruf`
- **DE Wiki example (before):** (no verbatim example; guidance notes EN citation templates applied to DE Wikipedia)
- **DE Wiki suggested fix (after):** Use DE Wikipedia citation templates (`{{Literatur}}`, `{{Internetquelle}}`) with correct German parameter names
- **EN cross-reference:** DE-ONLY #102 — Wikipedia-specific; reflects that DE Wikipedia has its own citation template system that differs from EN Wikipedia's. Not surfaced in general prose.
- **Notes:** Wikipedia-domain only. No applicability to general prose humanization.

---

### Nicht existierende Kategorien (Non-existent Categories)

- **Trigger words / phrases:** `[[Kategorie:NichtVorhandeneKategorie]]`; red-link categories from outdated training data
- **DE Wiki example (before):** `[[Kategorie:Natürliche Person (Nordrhein-Westfalen)]]` (doesn't exist or was renamed)
- **DE Wiki suggested fix (after):** Verify category existence before adding; remove or correct red-link categories
- **EN cross-reference:** DE-ONLY #103 — Wikipedia-specific; DE Wikipedia category names are entirely different from EN. Not applicable outside wiki editing.
- **Notes:** Wikipedia-domain only. Mirrors the non-existent templates tell (#100) in class of error.

---

### Wechsel im Schreibstil (Style-Register Shift)

- **Trigger words / phrases:** Sudden switch from colloquial to highly formal register within a user's edits; adoption of English-typical constructions (`es gibt`, `Anglizismen`) in otherwise German prose; flawless prose from a user who typically has errors
- **DE Wiki example (before):** A user who previously wrote "hab das kurz geändert" suddenly submits perfectly formatted, academic-style prose with no errors
- **DE Wiki suggested fix (after):** (Meta-guidance for Wikipedia editors, not a text-rewriting fix) — flag for review; check edit history
- **EN cross-reference:** DE-ONLY #104 — this is a user-behavior / edit-history indicator for Wikipedia editors, not a prose-level text pattern. Not applicable to the humanizer skill's prose-editing work.
- **Notes:** Wikipedia-editor-behavior signal only. Do not include in `patterns/de.md` as a prose pattern. Mention in open questions for scoping.

---

### Produktivitätsschub (Productivity Spike)

- **Trigger words / phrases:** Unusually high article creation or edit rate vs. a user's historical baseline
- **DE Wiki example (before):** User creates 20 articles in a day when their average is 1–2 per week
- **DE Wiki suggested fix (after):** (Editor-behavior check) — review edits for other AI indicators
- **EN cross-reference:** DE-ONLY #105 — editor-behavior signal only; not applicable to prose-level humanization work.
- **Notes:** Wikipedia-editor-behavior signal only. Do not include as a prose pattern.

---

### Ausführliche Bearbeitungszusammenfassungen (Verbose Edit Summaries)

- **Trigger words / phrases:** Edit summary is unusually long, written in first-person voice, lacks standard German Wikipedia abbreviations (`erg.`, `korr.`, `AWB`)
- **DE Wiki example (before):** "Ich habe den Artikel überarbeitet und dabei die wichtigsten Informationen ergänzt sowie den Stil verbessert, um eine bessere Lesbarkeit zu gewährleisten."
- **DE Wiki suggested fix (after):** Use short conventional summaries ("erg.", "korr.", "Formatierung") per DE Wikipedia convention
- **EN cross-reference:** DE-ONLY #106 — Wikipedia-editor-behavior / interface artifact. Not applicable to general prose.
- **Notes:** Wikipedia-domain only. The verbosity of the summary is itself produced by an LLM, so the formulas (`zu gewährleisten`, `um eine bessere Lesbarkeit`) overlap with the Partizip-I and editorial-commentary patterns — cross-reference #3 and redaktionelle Kommentare.

---

### UTM-Parameter / utm_source=chatgpt.com (URL Pollution)

- **Trigger words / phrases:** `?utm_source=chatgpt.com` in Wikilinks; `?utm_source=openai`; `?utm_source=copilot.com`
- **DE Wiki example (before):** `[https://example.com/article?utm_source=chatgpt.com Quellartikel]`
- **DE Wiki suggested fix (after):** Strip the UTM parameter from all URLs
- **EN cross-reference:** UNIVERSAL — covered by `patterns/_universal.md` pattern #38 (Reference-Markup Artifacts), which already lists `?utm_source=chatgpt.com` and `referrer=grok.com` as tokens to watch.
- **Notes:** The DE Wiki reports this is logged by Filter 453 ("Mutmaßliche KI-Bearbeitung"). The token is already in the universal pattern; no new entry needed.

---

## DE-only candidates (#100+)

The following entries are categorized as DE-ONLY. They will become new pattern entries in `patterns/de.md` under IDs starting at #100. Each has no direct EN equivalent.

---

### #100 — Einbindung nicht existierender Vorlagen (Non-existent Wikitext Templates)

**Candidate ID:** #100
**Scope:** Wikipedia-editing domain only
**Summary:** LLMs generate syntactically plausible `{{VorlagenName|parameter=wert}}` calls that reference templates that do not exist in German Wikipedia or use invented parameter names on real templates.
**Trigger tokens:** `{{` followed by an unknown template name; known templates with non-existent parameters
**Fix:** Verify against German Wikipedia's template catalogue before publishing; remove or replace with the correct template
**Domain applicability:** Wikipedia-editing only; does not surface in casual, academic, legal, technical, marketing, or career domains

---

### #101 — Bestimmte Konjunktionen / Transitionswörter (Mechanical Transition Word Stacking)

**Candidate ID:** #101
**Scope:** All domains; flag at light threshold in academic and legal
**Summary:** LLM-generated German prose stacks logical connectors mechanically — `andererseits`, `darüber hinaus`, `zusätzlich`, `außerdem`, `ferner`, `des Weiteren`, `infolgedessen` — producing a stiff, formulaic rhythm. The EN pack has no dedicated transition-overuse pattern. German convention expects explicit Satzverknüpfung, so the over-use is a culturally amplified tell.
**Trigger tokens:** `andererseits`, `darüber hinaus`, `zusätzlich`, `außerdem`, `ferner`, `des Weiteren`, `infolgedessen`, `gleichwohl`, `nichtsdestoweniger`
**Before:** "Andererseits ist zu beachten, dass … Darüber hinaus zeigt sich … Außerdem ist festzustellen … Ferner ist zu erwähnen …"
**After:** Restructure into one coherent paragraph with logical flow; use at most one connector per paragraph unless content genuinely requires more
**Domain applicability:** All domains; academic + legal: light threshold (3+ in close proximity); casual + marketing + career: strict

---

### #102 — Inkorrekte DE-Wikipedia-Referenzformatierung (Wrong DE Citation Template Usage)

**Candidate ID:** #102
**Scope:** Wikipedia-editing domain only
**Summary:** LLMs trained primarily on English Wikipedia apply EN citation templates (`{{cite web}}`, `{{cite book}}`) instead of correct DE Wikipedia templates (`{{Internetquelle}}`, `{{Literatur}}`), or use English-language parameter names (`access-date` instead of `abruf`, `author` instead of `autor`).
**Fix:** Replace with correct DE Wikipedia citation templates and German parameter names
**Domain applicability:** Wikipedia-editing only

---

### #103 — Nicht existierende Kategorien (Non-existent DE Wikipedia Categories)

**Candidate ID:** #103
**Scope:** Wikipedia-editing domain only
**Summary:** LLMs add categories that were renamed, never existed, or are English-Wikipedia-only categories transliterated into German.
**Fix:** Verify category existence; remove red-link categories
**Domain applicability:** Wikipedia-editing only

---

### #104 — Wechsel im Schreibstil (Style-Register Shift as Editor-Behavior Tell)

**Candidate ID:** #104
**Scope:** Wikipedia-editor-behavior signal; NOT a prose pattern
**Summary:** A user's editing register suddenly shifts from colloquial or error-prone to flawlessly formal. Or the text adopts English syntactic constructions (`es gibt + Anglizismen`) atypical for the user's prior work.
**Note:** This is a meta-indicator for Wikipedia editors reviewing edit histories, not a prose-level pattern for the humanizer skill. Recommend excluding from `patterns/de.md`; document as a detection-workflow note only.
**Domain applicability:** Wikipedia-editor-workflow only

---

### #105 — Produktivitätsschub (Productivity Spike as Editor-Behavior Tell)

**Candidate ID:** #105
**Scope:** Wikipedia-editor-behavior signal; NOT a prose pattern
**Note:** Same as #104 — meta-indicator only. Recommend excluding from `patterns/de.md`.
**Domain applicability:** Wikipedia-editor-workflow only

---

### #106 — Ausführliche Bearbeitungszusammenfassungen (Verbose Edit Summaries)

**Candidate ID:** #106
**Scope:** Wikipedia-editor-behavior / interface artifact
**Summary:** LLMs generate unusually long, first-person, full-sentence edit summaries that violate German Wikipedia's convention of short abbreviations. The summary prose itself often contains the Partizip-I (#3 / EN-PARALLEL) and redaktionelle Kommentare (#23 / EN-PARALLEL) tells.
**Note:** The pattern is DE-ONLY in the sense that it is a Wikipedia-interface artifact; the prose-level sub-patterns (Partizip-I, filler phrases) are already covered by existing patterns.
**Domain applicability:** Wikipedia-editor-workflow only

---

## Patterns from EN that have no DE equivalent in this Wiki source

The following EN patterns from `patterns/en.md` are not mentioned by the DE Wiki source. They still apply to DE writing (LLMs produce them in German too) but are not flagged by the German Wikipedia community — useful signal about which tells are language-neutral LLM behaviors vs. culturally-noticed concerns.

| EN Pattern | Name | Why DE Wiki probably doesn't flag it |
|------------|------|--------------------------------------|
| #1 | Undue Emphasis on Significance, Legacy, Broader Trends | Overlaps with Werbesprache (#4); DE Wiki folds it there |
| #2 | Undue Emphasis on Notability and Media Coverage | Not flagged separately; possibly seen as an editorial-tone issue subsumed under Werbesprache |
| #7 | Overused "AI Vocabulary" Words | DE Wiki does not enumerate a German-language equivalent list (e.g., `gewährleisten`, `nachhaltig`, `ermöglichen`); this is a major gap — the DE pack needs its own vocabulary list |
| #8 | Copula Avoidance ("serves as", "stands as") | DE surface forms (`gilt als`, `dient als`, `fungiert als`) not flagged by DE Wiki; gap in DE community awareness |
| #11 | Elegant Variation / Synonym Cycling | Not flagged; possibly because German has a richer synonym system and variation is more expected |
| #13 | Passive Voice and Subjectless Fragments | DE Wiki does not flag passive voice; German academic register heavily uses passive, making it a poor tell in most DE domains |
| #16 | Inline-Header Vertical Lists | Not flagged as a DE Wikipedia concern; possibly because the community focuses on Wikitext formatting correctness rather than prose structure |
| #22 | Sycophantic / Servile Tone | Subsumed under kollaborative Kommunikation in the DE source; not treated as a separate pattern |
| #23 Filler phrases (subset) | "Moving forward", "Going forward" | DE equivalents (`vorausblickend`, `zukünftig`) not specifically flagged |
| #24 | Excessive Hedging | Not flagged separately; possibly because German academic register legitimizes hedging |
| #26 | Hyphenated Word Pair Overuse | Not flagged; German compound words are always written as one word (Komposita), so the hyphenation over-use pattern doesn't translate |
| #27 | Persuasive Authority Tropes ("The real question is") | DE equivalents (`Die eigentliche Frage ist`, `im Kern geht es um`) not flagged |
| #28 | Signposting / Announcements ("Let's dive in") | DE equivalents (`Lassen Sie uns nun`, `Im Folgenden wird`) not specifically flagged |
| #29 | Fragmented Headers | Not flagged by DE Wiki |
| #30 | Sentence-Starter Intensifiers ("Ultimately", "Indeed") | DE equivalents (`Letztendlich`, `Tatsächlich`, `Offensichtlich`) not flagged |
| #31 | Rhetorical and Self-Answering Questions | Not flagged |
| #32 | Stacked Intensifier Adjectives | Partially overlaps with Trikolon (#10 / EN-PARALLEL); not separately flagged |
| #33 | Quantity Vagueness ("numerous", "various") | DE equivalents (`zahlreich`, `vielfältig`, `verschiedene`) not flagged |
| #34 | Trailing Emphasis Fragments | Not flagged |
| #35 | Debunking-Pose Headings | Not flagged |
| #36 | Conditional Frame Stacking | Not flagged; German academic register uses Konjunktiv II for hedging — this intersects but is different |
| #37 | Miscalibrated Epistemic Confidence | Not flagged separately |
| #41 | Diff-Anchored Writing | Not flagged |

**Key gap identified:** EN pattern #7 (AI Vocabulary Words) has no DE equivalent list in this source. The DE pack will need its own German-language AI vocabulary list. Candidate German AI vocabulary words to research for Task 6: `gewährleisten`, `ermöglichen`, `nachhaltig`, `umfassend`, `maßgeblich`, `wegweisend`, `prägend`, `vielfältig`, `bedeutsam`, `zukunftsweisend`, `robust` (borrowed directly), `nahtlos` (from "seamlessly"), `ganzheitlich`.

**Second key gap:** EN pattern #8 (Copula Avoidance) has no DE Wiki entry. German surface forms — `gilt als`, `dient als`, `fungiert als`, `erweist sich als` — are likely LLM tells but not yet flagged by the German Wikipedia community.

---

## Open questions

1. **Hallucinated citations as DE-ONLY vs. EN-PARALLEL:** The DE Wiki places false references (`Falsche Belege`) in a hard "eindeutig" (definitive) category — triggering Schnelllöschantrag. EN pack #5 (vague attributions) is the closest analogue but much softer. Should DE pack have a separate high-severity `#false-citations` entry distinct from #5, or should the severity escalation be handled in `domains/de_overrides.md` as an override on #5?

2. **DE AI vocabulary list (gap at EN #7):** This source does not enumerate a German equivalent of the EN AI vocabulary list (#7). For Task 6, the maintainer will need to either (a) run corpus analysis on LLM DE output to identify over-represented German words, or (b) adapt the EN list by translation. Candidate list in the "Patterns from EN" section above is a starting point, not a verified list.

3. **Konjunktiv II as a potential DE-ONLY pattern:** The DE Wiki mentions Konjunktiv II as a hedging convention in German academic writing but does not flag it as an AI tell. However, LLMs may stack Konjunktiv II constructions (`könnte`, `würde`, `dürfte`, `schiene`) in non-academic contexts where indicative is appropriate. This would be a DE-ONLY pattern not covered by EN #36 (Conditional Frame Stacking). Worth investigating in Task 6.

4. **Anglizismen-Leakage as a potential DE-ONLY pattern:** The DE Wiki notes that AI-generated German sometimes adopts English syntactic constructions or anglicized vocabulary. This is a major DE-ONLY tell (`downloaden`, `updaten`, `managen`, `featuren`) that has no EN parallel. Should this be its own pattern (#107)? The DE Wiki only mentions it in the context of user-behavior shifts, not as a systematic prose pattern.

5. **Nominalstil-Inflation as a potential DE-ONLY pattern:** German LLM output tends toward heavy nominalization (`die Gewährleistung von`, `die Ermöglichung einer`, `die Sicherstellung des`) where a verb would be more natural (`gewährleisten`, `ermöglichen`, `sicherstellen`). The DE Wiki does not explicitly flag this, but it is a well-known German bureaucratic register tell that LLMs amplify. Should this be pattern #108? No EN equivalent.

6. **Wikipedia-only patterns (#100, #102, #103, #104, #105, #106):** Six of the DE-ONLY candidates are Wikipedia-editor-behavior or Wikitext-specific signals that have no applicability to general prose humanization. Recommend: document them in a separate `docs/de-wikipedia-specific-tells.md` file and exclude from `patterns/de.md` entirely, OR add them to `patterns/de.md` under a `## Wikipedia-context only` section that the framework skips for non-Wikipedia domains.

7. **`_universal.md` additions needed:** Several tells from this source should be added as tokens to existing universal patterns rather than new DE entries:
   - Pattern #38: Add `(Gehe zu Suche Nr.)topic+N` token
   - Pattern #38: Confirm `?utm_source=chatgpt.com` already present (it is)
   - Pattern #6 / #25: Add German trigger strings (`Trotz seiner Erfolge`, `steht vor mehreren Herausforderungen`, `Zukunftsaussichten`)
   - Pattern #25: Add German conclusion-heading variants (`Fazit`, `Schluss`, `Schlussfolgerung`, `Abschließende Bemerkungen`)
   - Pattern #40: Add Markdown-vs-Wikitext specific German comparison notes
   These should be done in a separate task to avoid scope creep here.

8. **Detection-workflow meta-guidance:** The DE Wiki emphasizes that no single indicator is definitive (except clear LLM self-references or verifiably false citations), and that detection tools like GPTZero are unreliable. The humanizer skill's Tier-1 density pre-flight aligns with this philosophy. Worth documenting explicitly in `SKILL.md` or the DE pack header.

9. **Post-ChatGPT timeline indicator:** The DE Wiki notes that texts predating November 30, 2022 (ChatGPT public launch) are unlikely to be LLM-generated. This is a useful context note for the humanizer when asked to evaluate whether text needs humanization at all — but not a pattern to apply in rewriting.

10. **`domains/de_overrides.md` matrix pre-work:** Based on this catalogue, the following pattern/domain intersections need special handling in the DE overrides file (for Task 6 curation):
    - #3 (Partizip-I / Superficial Analyses): No SKIP in any domain — DE Wiki marks as universally pretentious
    - #4 (Werbesprache): SKIP in marketing (same as EN)
    - #13 (Passive voice): SKIP in academic AND legal (same as EN, but German academic use is even heavier)
    - #25 (Fazit section): SKIP in academic and scientific domains
    - #101 (Transition words): light in academic and legal; strict in all others
