# English Domain Overrides

Per-domain override matrix for the English pack. Loaded by the framework (`SKILL.md`) alongside `patterns/en.md` when the detected input language is English. The "casual" column is the strict default; other domains modify specific patterns.

### Domain overrides

Some patterns are softened, suppressed, or skipped per domain. Universal patterns (those not in this table) apply identically across all domains. The "casual" column is **strict** for every pattern — it's the default behavior.

| Pattern | academic | legal | technical | marketing | career |
|---------|----------|-------|-----------|-----------|--------|
| #4 Promotional language | strict | strict | strict | **SKIP** | light |
| #8 Copula avoidance | strict | light | strict | light | strict |
| #10 Rule of three | light | strict | strict | light | light |
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

Patterns #38–#40 (chat-UI artifacts) are **universal** — always stripped, no domain ever preserves them.

**Legend:**
- **strict** — apply the rule fully (default behavior)
- **normal** — apply but allow occasional exceptions when grammatically natural
- **light** — only fix egregious cases (3+ instances in close proximity, or particularly jarring uses)
- **SKIP** — do not flag or fix; this pattern is domain-appropriate

### Domain-specific guidance

**academic** — Hedging ("the results suggest", "appears to indicate") is appropriate register, not AI-style overhedging. Passive voice in methods sections is conventional. Avoid first-person except in fields where it's accepted (humanities, some social sciences). The PERSONALITY AND SOUL section below does NOT apply — academic prose is properly impersonal. Still cut AI buzzword vocabulary (#7): "testament", "tapestry", "landscape", "intricate interplay" mark a passage as AI-generated even in academic writing. Citations should be specific and verifiable.

**legal** — Hedging is mandatory ("may", "shall", "subject to"). Passive voice is conventional. Formal connectors ("notwithstanding", "with respect to", "in the matter of") are appropriate even if they look like filler. The PERSONALITY AND SOUL section does NOT apply — legal prose is properly impersonal. Still cut AI vocabulary (#7). Specific citations to statutes, cases, and section numbers are essential.

**technical** — Lists, code blocks, headings, and bold are scaffolding for scannability — preserve them. Inline-header lists ("**Parameters:** ...") are conventional in documentation, not AI artifacts. Direct address ("you") is fine; "we" can refer to the documented system. Active voice still preferred. The PERSONALITY AND SOUL section applies only lightly — clarity beats personality, but flat tutorial-script prose is still worth fixing. Particularly cut "robust", "seamless", "comprehensive", "intuitive" from #7 — these are the most common AI tells in technical writing. **Preserve functional standing claims:** phrases like "industry best practices", "battle-tested", and "production-grade" describe adoption or reliability status — they are legitimate technical positioning, not pure puffery. Only cut them if they are stacked with other AI adjectives in the same clause; if they stand alone, keep or lightly rephrase (e.g. "follows industry best practices" → "follows established patterns"). **Never introduce implementation specifics not present in the source:** if the original says "backoff strategy", do not rewrite to "exponential backoff"; if the original says "wide range of failure modes", do not narrow it. Fabricating or narrowing technical claims is a content error that outweighs any fluency gain.

**marketing** — Promotional language is the point: "vibrant", "renowned", "boasts", "stunning" are conventional, not AI tells. The skill's job here is narrower than usual: focus on removing AI vocabulary (#7), chatbot artifacts (#20), sycophantic tone (#22), and the most distinct AI buzzwords like "testament", "tapestry", "intricate interplay". Leave the promotional register intact. Rule of three is a classical persuasive device — keep it. Stacked adjectives and sentence-starter intensifiers ("Ultimately, our product...") are conventional.

**Buzzword-in-phrase rule:** Strip an AI buzzword only when it is the *whole* of the rhetorical point. When the buzzword anchors a positioning angle — a product category, use case, or customer identity — rewrite rather than delete. Example: "the evolving landscape of home design" → "landscape" is the AI word, but "where home design is heading" or "the future of home design" preserves the angle. "Seamlessly dimmable warmth" → flag "seamlessly" (#7) but keep the warmth/dimming feature claim in the rewrite. Default: if removing a word also removes a product claim, rewrite around it.

**Preserve positioning angles:** Design-meets-function, personalization, and lifestyle fit are the copy's *meaning*, not decoration. If the input names a positioning angle (form-and-function, personal style, task vs. ambient light), the output must land that same angle even if surface words change. A rewrite that drops an angle is content loss, not improvement, and fails the meaning score regardless of fluency.

**Preserve-everything checklist — marketing copy must retain all of the following:**

1. **Feature claims** — every named capability (dimmability, app control, voice integration, etc.). If the source mentions a feature, the rewrite must name it too.
2. **Tonal/sensory attributes** — words like "warmth", "softness", "crispness", "cool" when used to describe a product's experiential quality (not as filler). "Dimmable warmth" is a feature claim, not decoration — keep it, or rewrite to an equivalent sensory phrase.
3. **Brand-tier descriptors** — "next-generation", "premium", "best-in-class", "classic", "entry-level". These place the product in a competitive tier; dropping or softening them is a positioning error. Anti-example: if the source says "next-generation lamp", do NOT rewrite to "new kind of lamp" — that collapses a premium-tier signal into a generic newness claim. Use "a new generation of lamp" or "a next-gen lamp" instead.
4. **Emotional-fit phrases** — phrases that match the product to the customer's identity or living context ("every room reflects you", "designed around the way you live", "made for how you work"). These are the copy's *hook*, not filler. If the source lands this hook explicitly, the rewrite must land an equivalent hook.
5. **Aspirational/lifestyle tone** — if the source positions the product as aspirational (language of elevation, discovery, self-expression), the rewrite must stay in that register. Flattening aspirational language to functional language is a register error even if every feature survives.

**Brand-tier audit step:** Before finalizing any marketing rewrite, scan the output and ask: "Does this rewrite signal the same competitive tier as the source?" If the source used premium/next-gen/flagship language and the output reads as generic or entry-level, revise upward before finishing.

**career** — Cover letters / Anschreiben, CV / résumé bullets, LinkedIn About + headline, career-narrative drafts. Register sits between **marketing** (self-promotion is allowed, even expected) and **academic** (no puffery, claims must be earned). First-person + active voice are mandatory ("I led", "I delivered", "I shipped" — never "was led by me", never "the team was led"). PERSONALITY AND SOUL applies only **lightly** — voice is fine, but blog-casual tangents and "let some mess in" are not. Cut these career-specific AI tells aggressively (universal across this domain, in addition to #7 vocabulary): "results-driven", "passionate about", "uniquely positioned", "leverage" (as verb), "synergy", "value-add", "team player", "go-getter", "self-starter", "thought leader", "rockstar", "ninja", "unique blend", "perfect candidate", "ideal fit", "uniquely qualified". Also cut chatbot openers ("I am writing to express my interest in...", "I am thrilled to apply for...", "It is with great enthusiasm...") and sycophantic closers ("I would be honored to discuss...", "I look forward to the opportunity to...").

**Career preserve rules — these MUST survive any rewrite:**

1. **Metrics are sacred.** Every number, percentage, dollar amount, team size, time-saving, latency improvement, scale factor, headcount, budget, revenue impact in the source MUST appear verbatim (or with equivalent units) in the rewrite. No rounding, no qualitative substitution ("reduced p99 latency by 40%" never becomes "significantly improved latency").
2. **Proper nouns + dates + titles.** Company names, job titles, product names, dates, schools, certifications — all survive verbatim. Don't rephrase "Senior Software Engineer" to "senior engineering role".
3. **Tech stack / domain vocabulary.** Named frameworks, languages, methodologies, tools, certifications, regulatory bodies — these are ATS-relevant and signal competence. "Kubernetes, Go, PostgreSQL" stays as a list; do not generalize to "modern cloud tooling".
4. **JD-keyword phrases.** If the input or job description uses a phrase like "cloud-native architectures", "real-time data infrastructure", "p99 latency" — keep it. Don't strip industry vocabulary thinking it's AI puffery.
5. **Concrete achievement claims.** "I led the migration of a monolithic application to microservices" — the entire claim survives, including scope (monolith → microservices) and the lead role. Strip surrounding clichés ("consistently demonstrated a results-driven approach"), keep the achievement.

**Cultural-register note:** This guidance reflects **US/UK** norms (confident self-promotion is expected). German / Austrian / Swiss cover letters use a more factual-modest register — "Mit großem Interesse" instead of "I am thrilled". DE career register handling is part of the Phase 2 DE pack (`patterns/de.md` + `domains/de_overrides.md`), not this EN file.

**casual** (default) — All patterns at strict. Personal voice, opinion, varied rhythm, and specific concrete detail are the targets. The PERSONALITY AND SOUL section fully applies.

**Critical casual constraint — concept-noun preservation:** Stripping AI vocabulary from a casual passage does NOT license dropping the ideas that vocabulary named. The following are NOT padding-adjacent and MUST survive a casual rewrite even when they arrive wrapped in AI vocabulary: named concepts like "creativity at scale", "team alignment", "team agility", "collaboration", "software development evolution", "integration", "user impact", and similar noun-phrase ideas. The rule: strip the inflated wrapper, keep the underlying concept. "Unleashing creativity at scale" → cut "unleashing" (AI-flavored verb) + keep "doing creative work at a scale that wasn't possible before". "Fostering team alignment" → cut "fostering" (#3 pattern) + keep "keeping the team on the same page". If the output drops the concept entirely because it was dressed in AI vocabulary, that is a meaning loss — restore it. Concepts ≠ padding. Wrappers = padding.
