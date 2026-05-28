# German Domain Overrides

Per-domain override matrix for the German pack. Loaded by the framework
(`SKILL.md`) alongside `patterns/de.md` when the detected input language
is German. The "casual" column is the strict default; other domains
modify specific patterns.

> **DE-specific note:** DE academic + legal registers diverge from EN
> more than the other domains do. DE academic prose uses passive voice
> and Nominalstil-Inflation more heavily than EN academic; DE legal uses
> formal connectors ("notwithstanding"-class phrases like "ungeachtet",
> "vorbehaltlich") and Konjunktiv II for indirect speech as standard
> register. The override matrix below softens these patterns in DE
> academic + legal contexts where they would over-flag legitimate prose.

### Domain overrides

Some patterns are softened, suppressed, or skipped per domain. Universal
patterns (those not in this table) apply identically across all domains.
The "casual" column is **strict** for every pattern — it's the default
behavior.

| Pattern | academic | legal | technical | marketing | career |
|---------|----------|-------|-----------|-----------|--------|
| #4 Promotional language | strict | strict | strict | **SKIP** | light |
| #8 Copula avoidance | strict | **light** | strict | light | strict |
| #10 Rule of three | light | strict | strict | light | light |
| #11 Elegant variation | **light** | **light** | **light** | **light** | **light** |
| #13 Passive voice | **SKIP** | **SKIP** | light | strict | strict |
| #15 Boldface overuse | strict | strict | **SKIP** | light | light |
| #16 Inline-header lists | strict | strict | **SKIP** | light | light |
| #23 Filler phrases | light | light | strict | strict | strict |
| #24 Excessive hedging | light | **SKIP** | strict | strict | strict |
| #28 Signposting | light | light | light | light | strict |
| #30 Sentence intensifiers | normal | normal | strict | light | strict |
| #32 Stacked adjectives | strict | strict | strict | light | strict |
| #33 Quantity vagueness | strict | strict | strict | light | strict |
| #34 Trailing fragments | strict | strict | strict | light | light |
| #35 Debunking-pose headings | strict | strict | strict | light | strict |
| #36 Conditional frame stacking | light | light | strict | strict | strict |
| #37 Miscalibrated confidence | strict | strict | strict | light | strict |
| #100 Akademische Rahmen-Floskel | strict | strict | strict | strict | strict |
| #101 Impersonales Reflexiv | light | light | strict | strict | strict |
| #102 Konjunktiv II stacking | light | light | strict | strict | strict |
| #103 Anglizismen-Leakage | strict | strict | light | light | strict |
| #104 Nominalstil-Inflation | light | **SKIP** | strict | strict | strict |

Patterns #38–#40 (chat-UI artifacts) are **universal** — always stripped,
no domain ever preserves them. Pattern #41 (Diff-anchored writing) is
**universal** with explicit skip clauses for CHANGELOGs / release notes
/ migration guides / PR descriptions / refactor blog posts.

**Legend:**
- **strict** — apply the rule fully (default behavior)
- **normal** — apply but allow occasional exceptions when grammatically natural
- **light** — only fix egregious cases (3+ instances in close proximity, or particularly jarring uses)
- **SKIP** — do not flag or fix; this pattern is domain-appropriate

### Domain-specific guidance

**academic** — DE academic prose uses passive voice + Nominalstil-Inflation
+ Konjunktiv II for indirect speech (Konjunktiv I) more heavily than EN
academic. Hedging ("die Ergebnisse legen nahe", "es zeichnet sich ab") is
appropriate register, not AI-style overhedging. Cut AI buzzword vocabulary
(#7): "darüber hinaus", "im Hinblick auf", "vor diesem Hintergrund", "es
lässt sich festhalten", "vielfältig", "facettenreich", "ganzheitlich" mark
a passage as AI-generated even in academic writing. The PERSONALITY AND
SOUL section does NOT apply — academic DE prose is properly impersonal.
Citations should follow DE academic conventions (Zitierweise; specific
page numbers; primary sources). **Note:** #101 Impersonales Reflexiv
+ #104 Nominalstil-Inflation are softened to `light` because DE academic
register conventionally uses these forms; flag only egregious clusters.

**legal** — Hedging is mandatory ("kann", "soll", "darf", "vorbehaltlich",
"ungeachtet", "sofern", "insbesondere"). Passive voice is conventional
(SKIP). Konjunktiv II for indirect reported speech ("könne", "würde") is
standard legal register; soften #102 to `light`. Formal connectors
("ungeachtet dessen", "mit Bezug auf", "im Sinne des"). DE legal also
uses Nominalstil-Inflation heavily ("Durchführung der Beweisaufnahme",
"Geltendmachung des Anspruchs") — SKIP #104 entirely. The PERSONALITY
AND SOUL section does NOT apply. Still cut AI vocabulary (#7). Specific
citations to Paragraphen, Aktenzeichen, BGB-/StGB-/Verordnungs-Stellen.
**Note:** "gilt als" / "fungiert als" can be legitimate legal terms of
art ("als geltend gemacht", "fungiert als Erbe"); #8 set to `light` to
catch genuine AI overuse without flagging legal-register correct usage.

**technical** — Lists, code blocks, headings, and bold are scaffolding
for scannability — preserve them. Inline-header lists ("**Parameter:**
...") are conventional in DE documentation. Direct address with "Sie"
or imperative ("Konfigurieren Sie", "Führen Sie aus") is fine. Active
voice still preferred. The PERSONALITY AND SOUL section applies only
lightly — clarity beats personality, but flat tutorial-script prose is
still worth fixing. Particularly cut "robust", "nahtlos", "umfassend",
"intuitiv", "ganzheitlich", "transformativ" from #7 — these are the
most common AI tells in DE technical writing. Anglizismen-Leakage
softened to `light` since English tech terms (API, Token, Deployment,
Pipeline, Container) are unavoidable; flag denglisch verb constructions
("scalen", "leveragen", "alignen", "performen") strictly.

**marketing** — Promotional language is the point: "innovativ", "modern",
"hochwertig", "elegant", "kraftvoll", "vielseitig" are conventional, not
AI tells. The skill's job here is narrower than usual: focus on removing
AI vocabulary (#7), chatbot artifacts (#20), sycophantic tone (#22), and
the most distinct AI buzzwords like "ganzheitlich", "transformativ",
"facettenreich", "im Rahmen", "darüber hinaus", "es lässt sich
festhalten". Leave the promotional register intact. Rule of three is a
classical persuasive device — keep it. Stacked adjectives ("modern,
elegant, kraftvoll") and sentence-starter intensifiers ("Erleben Sie...",
"Entdecken Sie...") are conventional. Denglisch in marketing is a
register marker ("smartes Design", "intuitive Customer Experience") —
soften #103 to `light`.

**Buzzword-in-phrase rule (DE):** Strip an AI buzzword only when it is
the *whole* of the rhetorical point. When the buzzword anchors a
positioning angle — a product category, use case, or customer identity
— rewrite rather than delete. Example: "im Rahmen modernster Audio-
Technologie" → "im Rahmen" is the AI phrase, but "modernste Audio-
Technologie" preserves the angle. "Ganzheitliche Klangerfahrung" → flag
"ganzheitlich" (#7) but keep the Klangerfahrung feature claim. Default:
if removing a word also removes a product claim, rewrite around it.

**Preserve positioning angles (DE):** Premium-Anspruch ("der Premium-
Standard", "die nächste Generation"), Lifestyle-Fit ("für deinen
Alltag", "passt zu deinem Leben"), Brand-Tier-Marker ("Flaggschiff",
"Einsteiger-Modell", "Pro-Linie") are the copy's *meaning*, not
decoration. If the input names a positioning angle, the output must
land that same angle even if surface words change.

**Preserve-everything checklist — DE marketing copy must retain all of
the following:**

1. **Feature claims** — every named capability (dimmbar, App-Integration,
   Sprachsteuerung, etc.). If the source mentions a feature, the rewrite
   must name it too.
2. **Tonal/sensory attributes** — "warm", "weich", "klar", "dynamisch",
   "präsent" as experiential qualities. Keep or rewrite to equivalent.
3. **Brand-tier descriptors** — "Premium", "die nächste Generation",
   "Flaggschiff", "Pro-Linie", "Einsteiger-Modell". Anti-example: source
   says "die nächste Generation der Audio-Technologie" → do NOT rewrite
   to "neuer Audio-Standard". Use "ein neuer Generation Audio-Standard"
   or "die nächste Audio-Generation" instead.
4. **Emotional-fit phrases** — "für deinen Alltag entwickelt", "passt
   zu deinem Leben", "gemacht für die Art, wie du arbeitest". Hook
   phrases, not filler.
5. **Aspirational/lifestyle tone** — if the source positions the
   product aspirationally (language of Entdeckung, Selbstausdruck,
   Premium-Erfahrung), the rewrite must stay in that register.

**Brand-tier audit step (DE):** Before finalizing any marketing rewrite,
scan the output and ask: "Signalisiert diese Übersetzung den gleichen
Wettbewerbsrang wie das Original?" If the source used Premium /
next-gen / Flaggschiff language and the output reads as Einsteiger or
generisch, revise upward before finishing.

**career** — Cover letters / Anschreiben, CV / Lebenslauf, LinkedIn DE
About / Headline, Karriere-Narrativ-Drafts. **DE career register is
fundamentally different from US/UK career register.** Where US/UK cover
letters expect confident self-promotion ("results-driven", "uniquely
positioned"), DE Anschreiben culture rewards **formal-modest** tone:
formal "Sie" address throughout, factual claims with evidence,
understatement preferred over puffery. The persona "Career Writer"
calibration that EN career uses (assertive achievement framing) is the
**opposite** of what DE career needs.

First-person + active voice are mandatory ("Ich habe geleitet", "Ich
habe entwickelt", "Ich habe umgesetzt" — never "Es wurde geleitet von
mir"). PERSONALITY AND SOUL applies only **lightly** — voice is fine
but blog-casual tangents and "let some mess in" are not. Cut these
DE-career-specific AI tells aggressively (universal across this domain,
in addition to #7 vocabulary):

- Chatbot openers: "Mit großem Interesse habe ich Ihre Stellenanzeige
  gelesen" (formulaic when uncombined with specific reference),
  "Ich bewerbe mich hiermit auf Ihre Stellenausschreibung"
- Sycophantic closers: "Ich freue mich auf die Gelegenheit, Sie persönlich
  kennenzulernen", "Ich würde mich sehr über eine Einladung zu einem
  Vorstellungsgespräch freuen", "Vielen Dank für Ihre Berücksichtigung"
- AI-cliché self-praise: "leidenschaftlich", "ergebnisorientiert",
  "ganzheitlich denkend", "zielorientiert", "kommunikationsstark",
  "teamfähig", "belastbar" (all of these are CV-cliché AI Schaubild
  vocabulary, not real differentiators)
- DE-AI compound phrases: "ich bin davon überzeugt, dass", "es würde
  mich außerordentlich freuen", "im Rahmen meiner bisherigen Tätigkeit",
  "konnte ich umfassende Erfahrung sammeln", "ein vielfältiges Spektrum
  an Aufgaben"

**Career preserve rules (DE) — these MUST survive any rewrite:**

1. **Metriken sind heilig.** Every number, percentage, Eurobetrag,
   Teamgröße, Zeitersparnis, Latenzreduktion, Skalierungsfaktor in the
   source MUST appear verbatim (or with equivalent units) in the rewrite.
   No rounding, no qualitative substitution ("p99-Latenz um 40 % reduziert"
   never becomes "Latenz signifikant verbessert").
2. **Eigennamen + Daten + Titel.** Firmennamen, Stellentitel,
   Produktnamen, Daten, Hochschulen, Zertifizierungen — all survive
   verbatim. Don't rephrase "Senior Software Engineer" to "leitende
   Entwickler-Rolle".
3. **Fachvokabular / Domänenwissen.** Named Frameworks, Sprachen,
   Methoden, Tools, Zertifikate, Regulatorische Stellen — these are
   ATS-relevant and signal competence. "Kubernetes, Go, PostgreSQL"
   stays as a list; do not generalize to "moderne Cloud-Werkzeuge".
4. **Stellenausschreibungs-Schlüsselphrasen.** If the input or
   Stellenausschreibung uses a phrase like "Cloud-native Architekturen",
   "Echtzeit-Datenverarbeitung", "p99-Latenz" — keep it. Don't strip
   industry vocabulary thinking it's AI puffery.
5. **Konkrete Achievement-Aussagen.** "Ich habe die Migration einer
   monolithischen Anwendung zu Microservices geleitet" — the entire
   claim survives, including scope (monolith → microservices) and the
   lead role. Strip surrounding clichés ("im Rahmen meiner ergebnis-
   orientierten Tätigkeit"), keep the achievement.

**Cultural-register note (DE-specific):** This guidance reflects
**DACH** norms (DE/AT/CH — formal-modest self-presentation expected).
US/UK career conventions (assertive confidence + superlatives) would
be perceived as arrogant in DE professional context. The EN career
override matrix and persona calibration assume US/UK norms; this DE
override deliberately inverts that. If a DE Anschreiben sounds like
a translated US cover letter (overclaiming + formulaic enthusiasm),
the rewrite should bring it back to DE-modest factual claims.

**casual** (default) — All patterns at strict. Personal voice, opinion,
varied rhythm, and specific concrete detail are the targets. The
PERSONALITY AND SOUL section fully applies. **DE casual note:** "Ich"
in DE casual is more weighty than EN "I" — use sparingly. "Man"
constructions are acceptable in DE casual where they would be
impersonal in EN.

**Critical casual constraint — concept-noun preservation:** Stripping
AI vocabulary from a DE casual passage does NOT license dropping the
ideas that vocabulary named. The following are NOT padding-adjacent
and MUST survive a DE casual rewrite even when they arrive wrapped in
AI vocabulary: named concepts like "Kreativität in großem Maßstab",
"Teamabstimmung", "Agilität", "Zusammenarbeit", "die Entwicklung der
Softwareentwicklung", "Integration", "Nutzerwirkung", and similar
noun-phrase ideas. The rule: strip the inflated wrapper, keep the
underlying concept. Concepts ≠ padding. Wrappers = padding.

> **Cross-reference — #36 + #102:** Conditional frame stacking (#36)
> and Konjunktiv II stacking (#102) overlap in domain effect. Both are
> softened to `light` in academic + legal, where hypothetical reasoning
> and indirect reported speech are legitimate register. The difference:
> #36 targets the logical-argumentative "wenn … dann … wenn" cascade;
> #102 targets the morphological cluster of Konjunktiv II forms (würde,
> wäre, hätte, könnte) regardless of whether they appear in if-clauses.
> A passage can trigger both; apply the more specific rule per context.
