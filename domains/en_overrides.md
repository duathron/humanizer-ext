# English Domain Overrides

Per-domain override matrix for the English pack. Loaded by the framework (`SKILL.md`) alongside `patterns/en.md` when the detected input language is English. The "casual" column is the strict default; other domains modify specific patterns.

### Domain overrides

Some patterns are softened, suppressed, or skipped per domain. Universal patterns (those not in this table) apply identically across all domains. The "casual" column is **strict** for every pattern — it's the default behavior.

| Pattern | academic | legal | technical | marketing |
|---------|----------|-------|-----------|-----------|
| #4 Promotional language | strict | strict | strict | **SKIP** |
| #8 Copula avoidance | strict | light | strict | light |
| #10 Rule of three | light | strict | strict | light |
| #13 Passive voice | **SKIP** | **SKIP** | light | strict |
| #15 Boldface overuse | strict | strict | **SKIP** | light |
| #16 Inline-header lists | strict | strict | **SKIP** | light |
| #23 Filler phrases | light | light | strict | strict |
| #24 Excessive hedging | light | **SKIP** | strict | strict |
| #28 Signposting | light | light | light | light |
| #30 Sentence intensifiers | normal | normal | strict | light |
| #32 Stacked adjectives | strict | strict | strict | light |
| #33 Quantity vagueness | strict | strict | strict | light |
| #34 Trailing fragments | strict | strict | strict | light |
| #35 Debunking-pose headings | strict | strict | strict | light |
| #36 Conditional frame stacking | light | light | strict | strict |
| #37 Miscalibrated confidence | strict | strict | strict | light |

Patterns #38–#40 (chat-UI artifacts) are **universal** — always stripped, no domain ever preserves them.

**Legend:**
- **strict** — apply the rule fully (default behavior)
- **normal** — apply but allow occasional exceptions when grammatically natural
- **light** — only fix egregious cases (3+ instances in close proximity, or particularly jarring uses)
- **SKIP** — do not flag or fix; this pattern is domain-appropriate

### Domain-specific guidance

**academic** — Hedging ("the results suggest", "appears to indicate") is appropriate register, not AI-style overhedging. Passive voice in methods sections is conventional. Avoid first-person except in fields where it's accepted (humanities, some social sciences). The PERSONALITY AND SOUL section below does NOT apply — academic prose is properly impersonal. Still cut AI buzzword vocabulary (#7): "testament", "tapestry", "landscape", "intricate interplay" mark a passage as AI-generated even in academic writing. Citations should be specific and verifiable.

**legal** — Hedging is mandatory ("may", "shall", "subject to"). Passive voice is conventional. Formal connectors ("notwithstanding", "with respect to", "in the matter of") are appropriate even if they look like filler. The PERSONALITY AND SOUL section does NOT apply — legal prose is properly impersonal. Still cut AI vocabulary (#7). Specific citations to statutes, cases, and section numbers are essential.

**technical** — Lists, code blocks, headings, and bold are scaffolding for scannability — preserve them. Inline-header lists ("**Parameters:** ...") are conventional in documentation, not AI artifacts. Direct address ("you") is fine; "we" can refer to the documented system. Active voice still preferred. The PERSONALITY AND SOUL section applies only lightly — clarity beats personality, but flat tutorial-script prose is still worth fixing. Particularly cut "robust", "seamless", "comprehensive", "intuitive" from #7 — these are the most common AI tells in technical writing.

**marketing** — Promotional language is the point: "vibrant", "renowned", "boasts", "stunning" are conventional, not AI tells. The skill's job here is narrower than usual: focus on removing AI vocabulary (#7), chatbot artifacts (#20), sycophantic tone (#22), and the most distinct AI buzzwords like "testament", "tapestry", "landscape", "intricate interplay". Leave the promotional register intact. Rule of three is a classical persuasive device — keep it. Stacked adjectives and sentence-starter intensifiers ("Ultimately, our product...") are conventional.

**casual** (default) — All patterns at strict. Personal voice, opinion, varied rhythm, and specific concrete detail are the targets. The PERSONALITY AND SOUL section fully applies.
