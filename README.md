# Humanizer (extended)

A skill for Claude Code and OpenCode that removes signs of AI-generated writing from text, making it sound more natural and human.

**Extended fork of [blader/humanizer](https://github.com/blader/humanizer), actively maintained.** Adds domain-aware overrides, 11 new patterns (40 total), a Quick/Full/Voice mode selector, a Tier-1 AI-iness density pre-flight, a Detection Guidance section (false positives + signs of human writing + LLM idiolects), a length audit, and an extended 13-point final AI audit checklist.

## What's different from upstream

| Area | Upstream (v2.5.1) | This fork (v3.5.0) |
|------|-------------------|--------------------|
| Language support | English only | **English + German**, auto-detected — German pack (`patterns/de.md`) adds DE-only tells (Nominalstil, Konjunktiv-II stacking, Denglisch, academic Rahmen-Floskeln) + a DACH career register for Anschreiben / Lebenslauf; per-language domain overrides (`domains/de_overrides.md`) |
| Total patterns | 29 | **41** — adds sentence-starter intensifiers, rhetorical questions, stacked adjectives, quantity vagueness, trailing fragments, debunking-pose headings, conditional frame stacking, miscalibrated epistemic confidence, reference-markup artifacts, placeholder text, markdown contamination, diff-anchored writing |
| AI vocabulary list | base set | **expanded** with bolstered, meticulous, robust, seamless, intuitive, comprehensive, plus **era-specific clusters** (GPT-4 / GPT-4o / GPT-5 eras) for dating suspect text |
| Modes | single behavior | **Quick / Full / Voice** selector |
| Domain awareness | none — same rules everywhere | **6 domains** (casual, academic, legal, technical, marketing, career) with per-pattern override matrix — passive voice preserved in legal briefs, lists preserved in technical docs, promotional language preserved in marketing, metrics/proper-nouns preserved in cover letters |
| Detection guidance | none | **dedicated section** — what NOT to flag (false positives), signs of human writing to preserve, per-model LLM idiolects (ChatGPT / Grok / Gemini / Claude) |
| Density pre-flight | none | **Tier-1 dead-giveaway density check** before any Full pass; auto-drops to Quick when density = 0 so human-first drafts aren't over-edited |
| Length audit | none | explicit step to cut 20–30% padding |
| Final AI audit | vague self-prompt | **specific 13-point checklist** annotated with per-domain exceptions |
| Pattern #9 ("not just X") | base | extended to "rather than" dismissals + on-the-table test |
| Pattern #14 (em dash) | base | extended to paired bracketing with 4 fix options by insertion type |
| Pattern #16 (inline-header lists) | convert all | convert only fake bullets; preserve genuine lists |
| Pattern #19 (curly quotes) | example rendered identically | explanation references U+201C/U+201D Unicode code points |
| Pattern #21 (cutoff disclaimers) | base | extended to speculative gap-filling ("maintains a low profile" template) |
| Pattern #25 (generic conclusions) | base | extended to structural `## Conclusion` sections (delete the whole section) |
| Pattern #26 (hyphenation) | strip all common pairs | use judgment; preserve technical compounds |

See the [version history](#version-history) for the full changelog.

## Installation

### Claude Code via marketplace (recommended)

```bash
/plugin marketplace add duathron/humanizer-ext
/plugin install humanizer-ext@duathron-skills
```

The `duathron-skills` marketplace is hosted in this repo and will accumulate additional forks of community skills over time. After installing, the skill becomes available as `/humanizer` in Claude Code.

### Claude Code (manual clone)

Clone directly into Claude Code's skills directory:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/duathron/humanizer-ext.git ~/.claude/skills/humanizer
```

Or copy the skill file manually if you already have this repo cloned:

```bash
mkdir -p ~/.claude/skills/humanizer
cp SKILL.md ~/.claude/skills/humanizer/
```

### OpenCode

Clone directly into OpenCode's skills directory:

```bash
mkdir -p ~/.config/opencode/skills
git clone https://github.com/duathron/humanizer-ext.git ~/.config/opencode/skills/humanizer
```

Or copy the skill file manually if you already have this repo cloned:

```bash
mkdir -p ~/.config/opencode/skills/humanizer
cp SKILL.md ~/.config/opencode/skills/humanizer/
```

> **Note:** OpenCode also scans `~/.claude/skills/` for compatibility, so a single clone into `~/.claude/skills/humanizer/` works for both tools.

## Usage

### Claude Code

```
/humanizer

[paste your text here]
```

### OpenCode

```
/humanizer

[paste your text here]
```

Or ask the model to humanize text directly in either tool:

```
Please humanize this text: [your text]
```

### Modes

The skill runs in one of three modes. If you don't specify, it defaults to **Full**.

| Mode | What it does |
|------|-------------|
| **Quick** | Strips AI vocabulary, chatbot artifacts, sycophancy, and filler only. Fast cleanup for short texts. |
| **Full** | All 40 patterns, a Tier-1 AI-iness density pre-flight, a length audit (cut 20–30% padding), and a 13-point final AI audit checklist. Default. |
| **Voice** | Full pass plus mandatory voice matching from a writing sample you provide. |

Specify a mode by including it in your prompt:

```
/humanizer quick

[paste your text here]
```

```
/humanizer voice

Here's a sample of my writing:
[paste 2-3 paragraphs of your own writing]

Now humanize this:
[paste AI text to humanize]
```

The Voice mode analyzes your sentence rhythm, word choices, and quirks, then applies them to the rewrite instead of producing generic "clean" output.

### Domains

The skill detects (or accepts) a domain and adjusts which patterns are enforced. Different writing contexts have different norms — what's "AI slop" in a blog post is appropriate convention in a legal brief.

| Domain | What changes |
|--------|-------------|
| **casual** (default) | All 40 patterns strict; personal voice encouraged |
| **academic** | Passive voice and hedging preserved; first-person discouraged; "soul" section disabled |
| **legal** | Passive voice, hedging, and formal connectors preserved; precise impersonal register |
| **technical** | Lists, bold, and inline-header lists preserved for scannability; direct active voice |
| **marketing** | Promotional register preserved; only AI buzzwords, chatbot artifacts, and sycophancy removed |

If you don't specify, the skill infers the domain from the text and tells you which one it picked. To set it explicitly, name it alongside the mode:

```
/humanizer technical

[paste your text here]
```

```
/humanizer academic full

[paste your text here]
```

## Overview

Based on [Wikipedia's "Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) guide, maintained by WikiProject AI Cleanup. This comprehensive guide comes from observations of thousands of instances of AI-generated text.

The skill runs a length audit to cut 20–30% of padding, then a specific 9-point final AI audit checklist to catch lingering AI-isms before presenting the final version.

### Key Insight from Wikipedia

> "LLMs use statistical algorithms to guess what should come next. The result tends toward the most statistically likely result that applies to the widest variety of cases."

## 41 Patterns Detected (with Before/After Examples)

### Content Patterns

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 1 | **Significance inflation** | “marking a pivotal moment in the evolution of...” | “was established in 1989 to collect regional statistics” |
| 2 | **Notability name-dropping** | “cited in NYT, BBC, FT, and The Hindu” | “In a 2024 NYT interview, she argued...” |
| 3 | **Superficial -ing analyses** | “symbolizing... reflecting... resonating with...” | Remove or expand with actual sources |
| 4 | **Promotional language** | “nestled within the breathtaking region” | “is a town in the Gonder region” |
| 5 | **Vague attributions** | “Experts believe it plays a crucial role” | “according to a 2019 survey by...” |
| 6 | **Formulaic challenges** | “Despite challenges... continues to thrive” | Specific facts about actual challenges |

### Language Patterns

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 7 | **AI vocabulary** (with era clusters) | “robust... meticulous... bolstered... seamless... testament”; GPT-4 / GPT-4o / GPT-5 era lists | plain synonyms or cut (flag figurative use, not literal) |
| 8 | **Copula avoidance** | “serves as... features... maintains... offers” | “is... has” |
| 9 | **Negative parallelisms / tailing negations / “rather than” dismissals** | “It's not just X, it's Y”, “..., no guessing”, “X rather than Y (where Y is unstated)” | State the point directly; cut dismissed alternatives nobody claimed |
| 10 | **Rule of three** | “innovation, inspiration, and insights” | Use natural number of items |
| 11 | **Synonym cycling** | “protagonist... main character... central figure... hero” | “protagonist” (repeat when clearest) |
| 12 | **False ranges** | “from the Big Bang to dark matter” | List topics directly |
| 13 | **Passive voice / subjectless fragments** | “No configuration file needed” | Name the actor when it helps clarity |

### Style Patterns

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 14 | **Em dash overuse / paired bracketing** | “institutions—not the people—yet this continues—”, “report—covering three continents—concluded” | Prefer commas or periods; break paired brackets into appositives or separate sentences |
| 15 | **Boldface overuse** | “**OKRs**, **KPIs**, **BMC**” | “OKRs, KPIs, BMC” |
| 16 | **Inline-header lists** | “**Performance:** Performance improved” | Convert to prose (preserve genuine lists) |
| 17 | **Title Case Headings** | “Strategic Negotiations And Partnerships” | “Strategic negotiations and partnerships” |
| 18 | **Emojis** | “🚀 Launch Phase: 💡 Key Insight:” | Remove emojis |
| 19 | **Curly quotes** | U+201C/U+201D typographic quotes | Straight ASCII quotes |
| 26 | **Hyphenated word pairs** | “cross-functional, data-driven, client-facing” | Drop hyphens on common pairs (use judgment) |
| 27 | **Persuasive authority tropes** | “At its core, what matters is...”, “In essence...” | State the point directly |
| 28 | **Signposting announcements** | “Let's dive in”, “Here's what you need to know” | Start with the content |
| 29 | **Fragmented headers** | “## Performance” + “Speed matters.” | Let the heading do the work |

### Communication Patterns

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 20 | **Chatbot artifacts** | “I hope this helps! Let me know if...” | Remove entirely |
| 21 | **Cutoff disclaimers / speculative gap-filling** | “While details are limited...”; “she maintains a low profile” | Find sources or remove |
| 22 | **Sycophantic tone** | “Great question! You're absolutely right!” | Respond directly |

### Filler and Hedging

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 23 | **Filler phrases / didactic disclaimers** | “In order to”, “It is worth noting that”, “Going forward”, “It is important to note”, “Keep in mind”, “consult a professional” | Cut or rewrite directly |
| 24 | **Excessive hedging** | “could potentially possibly” | “may” |
| 25 | **Generic conclusions / structural `## Conclusion` sections** | “The future looks bright”; a whole `## Conclusion` that restates the body | Specific plans or facts; delete the whole section |

### New in v3.0

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 30 | **Sentence-starter intensifiers** | “Ultimately... Indeed... Clearly... Essentially...” | Cut; state the claim directly |
| 31 | **Rhetorical / self-answering questions** | “What makes this effective? The way it reduces...” | “It works because it reduces...” |
| 32 | **Stacked intensifier adjectives** | “innovative, comprehensive, and forward-thinking” | One specific adjective or none |
| 33 | **Quantity vagueness** | “a wide range of factors... numerous studies” | Specific count or named examples |
| 34 | **Trailing emphasis fragments** | “That's the key. And that matters.” | Delete; the previous sentence said it |

### Heading Patterns (new in v3.2)

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 35 | **Debunking-pose headings** | “What the research actually says”, “X: the long game”, “demystified” | Cut “actually / the real / that lands”; audit headings as a separate pass |

### Epistemic Patterns (new in v3.2)

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 36 | **Conditional frame stacking** | “If the argument holds, and if the reading is right, then perhaps...” | State the conclusion; reserve “if” for real analytical branches |
| 37 | **Miscalibrated epistemic confidence** | Over: “decisively demonstrates fundamentally”; Over-hedge: “appears to have arguably may have somewhat” | Narrow the claim to what the evidence supports; don't swap one extreme for the other |

### Artifacts and Contamination (new in v3.2)

These do not occur in genuinely human-written text — when present, AI involvement is essentially confirmed. **Always strip them, regardless of domain.**

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 38 | **Reference-markup artifacts** | “...modern history `turn0search0`”, `?utm_source=chatgpt.com`, `<grok_card>`, `:contentReference[oaicite:0]` | Strip the markup; add a real citation if needed |
| 39 | **Phrasal templates / placeholder text** | “Founded in [YEAR], [COMPANY] is...”, `2025-xx-xx`, `XXXX`, `___` | Fill in or delete the sentence |
| 40 | **Markdown / wikitext contamination** | ```` ```markdown ```` fences left in prose, “Would you like me to convert...” meta-prompts | Remove the fence and meta-prompt |

## Full Example

**Before (AI-sounding):**
> Great question! Here is an essay on this topic. I hope this helps!
>
> AI-assisted coding serves as an enduring testament to the transformative potential of large language models, marking a pivotal moment in the evolution of software development. In today's rapidly evolving technological landscape, these groundbreaking tools—nestled at the intersection of research and practice—are reshaping how engineers ideate, iterate, and deliver, underscoring their vital role in modern workflows.
>
> At its core, the value proposition is clear: streamlining processes, enhancing collaboration, and fostering alignment. It's not just about autocomplete; it's about unlocking creativity at scale, ensuring that organizations can remain agile while delivering seamless, intuitive, and powerful experiences to users. The tool serves as a catalyst. The assistant functions as a partner. The system stands as a foundation for innovation.
>
> Industry observers have noted that adoption has accelerated from hobbyist experiments to enterprise-wide rollouts, from solo developers to cross-functional teams. The technology has been featured in The New York Times, Wired, and The Verge. Additionally, the ability to generate documentation, tests, and refactors showcases how AI can contribute to better outcomes, highlighting the intricate interplay between automation and human judgment.
>
> - 💡 **Speed:** Code generation is significantly faster, reducing friction and empowering developers.
> - 🚀 **Quality:** Output quality has been enhanced through improved training, contributing to higher standards.
> - ✅ **Adoption:** Usage continues to grow, reflecting broader industry trends.
>
> While specific details are limited based on available information, it could potentially be argued that these tools might have some positive effect. Despite challenges typical of emerging technologies—including hallucinations, bias, and accountability—the ecosystem continues to thrive. In order to fully realize this potential, teams must align with best practices.
>
> In conclusion, the future looks bright. Exciting times lie ahead as we continue this journey toward excellence. Let me know if you’d like me to expand on any section!

**After (Humanized):**
> AI coding assistants can speed up the boring parts of the job. They're great at boilerplate: config files and the little glue code you don't want to write. They can also help you sketch a test, but you still have to read it.
>
> The dangerous part is how confident the suggestions look. I've accepted code that compiled and passed lint, then discovered later it missed the point because I stopped paying attention.
>
> If you treat it like autocomplete and review every line, it's useful. If you use it to avoid thinking, it will help you ship bugs faster.
>
> The only real backstop is tests. Without them, you're mostly judging vibes.

## References

- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) - Primary source
- [WikiProject AI Cleanup](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup) - Maintaining organization

## Version History

- **3.5.0** - **German (DE) language pack.** The skill now works in English and German, auto-detected; the framework loads `patterns/{lang}.md` + `domains/{lang}_overrides.md` per detected language (English byte-unchanged). New `patterns/de.md` translates the universal/EN patterns to German with DE examples and adds **DE-only tells** (#100 academic Rahmen-Floskel "im Rahmen der vorliegenden Arbeit", #101 impersonal reflexive "es lässt sich …", #102 Konjunktiv-II stacking, #103 Denglisch/Anglizismen-Leakage, #104 Nominalstil-Inflation). New `domains/de_overrides.md` adapts all six domains to DE register, including a **DACH career register** for Anschreiben / Lebenslauf (formal-modest understatement — the opposite of US/UK puffery — with preserve-rules for metrics, proper nouns, tech stack, and the candidate's motivation/soft-skill substance). New `regex_scorer.PATTERNS_DE` (16 keys) registered in `PATTERNS_BY_LANG`, and a DE eval corpus (140 pattern cases @ 3/pattern, German human + AI corpora, 6 E2E cases). **Trustworthy DE baseline** (after a Skeptic-driven measurement overhaul that found the early numbers were artifacts — parser-commentary leak, pre-flight routing vs detection, brittle corpus substrings — none fixed by weakening the judge): **pattern detection 0.864** (force-full method, per-term 0.907), **false-positive edit ratio 0.138**, **E2E 6/6 domains pass** meaning / human-ness / length (5-run medians). EN parity re-run confirms **no regression** (EN pattern 0.952 under the same method). Eval infrastructure hardened: force-full pattern eval + per-term metric, per-item resilience (session-limit/timeout safe + resumable), robust E2E non-rewrite guard + judge retry + median reporting, FP reads the DE corpus layout, parser strips trailing skill commentary, `verify_skill_install` covers the DE packs. New-language pack convention documented (DE-only IDs start at #100; FR would use #200, etc.). 302 pytest pass.
- **3.4.2** - Patch release: adds **pattern #41 Diff-Anchored Writing** to `patterns/_universal.md` (ported from upstream `blader/humanizer` v2.7.0 pattern #30). The pattern flags documentation, comments, or prose written as if narrating a change rather than describing the thing as it is — "this function was added to replace", "the CLI now uses YAML (previously it used...)" — when the document is not a CHANGELOG / release notes / migration guide / PR description / refactor blog post. Skip clause is explicit so version-scoped writing isn't over-flagged. Bumps total pattern count from 40 to 41. SKILL.md description updated to surface the `career` domain alongside the other five. Tests: `UNIVERSAL_PATTERN_IDS` extended to include `41`; domain-existence assertion extended to include `career`. No skill behavior change beyond the new pattern.
- **3.4.1** - Meaning-preservation overhaul and new `career` domain. Closes the v3.4.0 E2E meaning-dimension breach (baseline 5/5 cases below 8.0 threshold → 6/6 cases pass per-case ≥8.0 on all 3 dims; aggregate human_ness 8.667 / meaning 8.389 / length 8.667). SKILL.md step 9 ports the "Rewrite, don't delete" paragraph-count rule from upstream `blader/humanizer` v2.6.0 PR #84. SKILL.md step 10 elevates "Preserve meaning" to a hard-constraint claim-inventory pass — list every claim in the source, verify each appears in the rewrite, restore any missing. SKILL.md final audit gains two new universal checks: a **fabrication check** (no new claims/details/specs introduced, no inventing "exponential backoff" when source said "backoff strategy") and a **new authorial positions check** (no added hedges, skepticism, endorsements, or qualifications not in source). Per-domain overrides extended: technical gets a "preserve functional standing claims" rule (`industry best practices`, `battle-tested`, `production-grade` are positioning, not pure puffery); marketing gets a buzzword-in-phrase rule + 5-point preserve-everything checklist (feature claims, tonal attributes, brand-tier descriptors, emotional-fit phrases, aspirational tone) + brand-tier audit step; casual gets a concept-noun preservation rule with named anti-examples (`creativity at scale`, `team alignment`, `team agility`, `collaboration`, `software-development-evolution`, `integration`, `user impact`). `patterns/en.md` PERSONALITY AND SOUL gains a "Do not invent the author's opinions" rule + the domain note is strengthened with upstream v2.6.0 wording ("neutral and plain *is* the correct human voice for encyclopedic/technical/legal/reference text"). Adds a sixth **`career` domain** for cover letter / CV / LinkedIn / Anschreiben work, sitting between marketing (self-promotion is allowed) and academic (claims must be earned) — first-person + active voice are mandatory, metrics + proper nouns + tech stack + JD keywords + concrete achievement claims are preserved verbatim, career-specific AI tells (`results-driven`, `passionate about`, `uniquely positioned`, etc.) are stripped aggressively. Override matrix column + 3-paragraph guidance + corpus case `evals/corpus/en/e2e/ai_career_01.json` (first-shot E2E pass: hn 9.00 / mean 8.00 / len 8.00). DE career register noted as Phase 2 DE-pack work. Pattern detection rate 0.619 (post-parser-fix `_FINAL_RE` from `61b03c1`), FP edit ratio 0.2039, density preflight 1.00, regex audit 5/5 LOW (all unchanged from v3.4.0 sign-off run). 78/78 pytest pass.
- **3.4.0** - Adds the evaluation infrastructure from the v3.5.0 design spec. Three runners ship under `evals/scripts/`: `run_pattern_eval.py` (per-pattern detection rate against curated before/after JSON cases), `run_false_positive_eval.py` (Levenshtein edit ratio on known-human samples), and `run_e2e_eval.py` (whole-document rewrite quality scored by a judge LLM via the Anthropic SDK, with `--judge-model {sonnet,opus}`). Shared utilities live in `evals/scripts/_shared.py` and are unit-tested in `tests/test_evals_shared.py` (18 new pytest tests, no API calls). `verify_skill_install()` guards each runner against running against a stale installed SKILL.md. The EN corpus seeds cover 39 of 40 patterns (auto-extracted from the pattern packs by `seed_pattern_corpus.py`; pattern #23 uses a bullet-list `Before → After` format the seeder regex does not match — manual entry pending), five synthetic human samples (one per domain) under `evals/corpus/en/human/synthetic/`, and five AI-generated whole-document E2E cases under `evals/corpus/en/e2e/`. The judge LLM uses Anthropic's tool-use API for structured 1–10 scores on human-ness, meaning preservation, and length appropriateness, defined in `evals/scripts/judge_prompt.md`. Partial baseline numbers are recorded in `evals/reports/summary_latest_en.{json,md}`; the E2E run was blocked by a claude CLI subscription session limit during the release run and will be re-run after the next reset. Three transient/structural issues were caught and patched mid-run: retry-with-backoff around `run_skill`, ANTHROPIC_API_KEY stripped from the CLI subprocess env (CLI uses subscription auth, SDK uses API key), and full stdout included in `SkillRunError`. Also ships `evals/scripts/regex_scorer.py` — a deterministic regex-based AI-tell scorer contributed by [Asaf Lecht](https://github.com/Seithx) — with per-paragraph density, sentence-rhythm CV, and a `--compare` rewrite-diff mode. Integrated with a `PATTERNS_BY_LANG` registry and `--lang` flag so future language packs (DE in Phase 2) plug in without further refactor. 27 new pytest cases cover the scorer (64 tests total). No skill behavior change in this release — only repo-side eval tooling.
- **3.3.0** - Internal refactor. `SKILL.md` split into a language-agnostic framework (~15 KB, down from ~60 KB) plus pattern packs: `patterns/_universal.md` (12 universal patterns: #6, #14, #15, #17, #18, #19, #25, #26, #29, #38, #39, #40), `patterns/en.md` (28 EN-specific patterns + the PERSONALITY AND SOUL section), and `domains/en_overrides.md` (override matrix + domain-specific guidance). The framework instructs Claude to Read the relevant pack files at runtime based on detected language and domain. Zero observable English-behavior change confirmed by a manual regression against the prior `## Full Example` (recorded in `docs/regression-cases/RESULTS.md`). Adds `tests/test_skill_structure.py` (15 pytest sanity tests, no API calls) for schema and cross-reference integrity. Pattern #14 (em dash) tightened during this release: the "earned single em dash" exception now requires five explicit conjunctive conditions and a separate post-rewrite count audit, after both regression runs left em dashes the audit should have caught. Prepares the architecture for multi-lingual support (DE pack ships in v3.5.0) and the eval infrastructure (ships in v3.4.0). No new patterns; no pattern wording changed beyond #14's exception clause.
- **3.2.0** - Cherry-picked five upstream PRs and integrated them with the fork's domain system. Added a new **Detection Guidance** section (false positives, signs of human writing to preserve, per-model LLM idiolects — ChatGPT / Grok / Gemini / Claude) so editors know what NOT to flag. Added a **Tier-1 AI-iness density pre-flight** in Full mode: counts dead-giveaway tells per 100 words and auto-drops to Quick when density = 0, so human-first drafts aren't over-edited. Expanded six existing patterns: #7 with era-specific vocabulary clusters (GPT-4 / GPT-4o / GPT-5 eras) and a figurative-vs-literal caveat; #9 with "rather than" dismissals + on-the-table test; #14 with paired em dash bracketing and four fix options; #21 with speculative gap-filling ("maintains a low profile" template); #23 with three more didactic disclaimers; #25 with structural `## Conclusion` section deletion. Added six new patterns (35–40) in three new themed sections: **Heading Patterns** (#35 Debunking-Pose Headings), **Epistemic Patterns** (#36 Conditional Frame Stacking, #37 Miscalibrated Epistemic Confidence), and **Artifacts and Contamination** (#38 Reference-Markup Artifacts, #39 Phrasal Templates / Placeholder Text, #40 Markdown / Wikitext Contamination). Domain overrides extended for #35–37; #38–40 are universal. Final AI audit checklist grew from 9 to 13 points. Sources: PRs #113, #112, #111, #116, #85, and #115 (adapted) from blader/humanizer.
- **3.1.0** - Added domain awareness: skill now detects (or accepts) a domain — casual, academic, legal, technical, or marketing — and applies per-domain overrides to 13 patterns. Passive voice is preserved in academic/legal; bold and inline-header lists in technical; promotional language in marketing. The PERSONALITY AND SOUL section now applies only to casual (and lightly to technical). Process and audit checklist updated to reference domain. Output format adds a domain announcement before the draft.
- **3.0.0** - Added 5 new patterns (sentence-starter intensifiers, rhetorical questions, stacked adjectives, quantity vagueness, trailing emphasis fragments), raising the total to 34; expanded AI vocabulary list (bolstered, meticulous, robust, seamless, intuitive, comprehensive); added copula words (maintains, offers); expanded superficial -ing list; added filler phrases (as such, it is worth noting that, going forward, a wide range of, the fact that); added mode selector (Quick/Full/Voice); restructured process with length audit and specific final AI audit checklist; fixed inline-header list rule to preserve genuine lists; clarified hyphenation rule; fixed curly quotes explanation; sourced additional patterns from re-read of Wikipedia Signs of AI Writing article
- **2.5.1** - Added a passive-voice / subjectless-fragment rule, raising the total to 29 patterns
- **2.5.0** - Added patterns for persuasive framing, signposting, and fragmented headers; expanded negative parallelisms to cover tailing negations; tightened wording around em dash overuse; fixed frontmatter wording to use "filler phrases"
- **2.4.0** - Added voice calibration: match the user's personal writing style from samples
- **2.3.0** - Added pattern #25: hyphenated word pair overuse
- **2.2.0** - Added a final "obviously AI generated" audit + second-pass rewrite prompts
- **2.1.1** - Fixed pattern #18 example (curly quotes vs straight quotes)
- **2.1.0** - Added before/after examples for all 24 patterns
- **2.0.0** - Complete rewrite based on raw Wikipedia article content
- **1.0.0** - Initial release

## Contributors

See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the full list. The v3.4.0 deterministic regex scorer (`evals/scripts/regex_scorer.py`) was contributed by [Asaf Lecht](https://github.com/Seithx).

## License

MIT
