# Humanizer

A skill for Claude Code and OpenCode that removes signs of AI-generated writing from text, making it sound more natural and human.

## Installation

### Claude Code

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
| **Full** | All 34 patterns, a length audit (cut 20–30% padding), and a final AI audit checklist. Default. |
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
| **casual** (default) | All 34 patterns strict; personal voice encouraged |
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

## 34 Patterns Detected (with Before/After Examples)

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
| 7 | **AI vocabulary** | “robust... meticulous... bolstered... seamless... testament” | plain synonyms or cut |
| 8 | **Copula avoidance** | “serves as... features... maintains... offers” | “is... has” |
| 9 | **Negative parallelisms / tailing negations** | “It's not just X, it's Y”, “..., no guessing” | State the point directly |
| 10 | **Rule of three** | “innovation, inspiration, and insights” | Use natural number of items |
| 11 | **Synonym cycling** | “protagonist... main character... central figure... hero” | “protagonist” (repeat when clearest) |
| 12 | **False ranges** | “from the Big Bang to dark matter” | List topics directly |
| 13 | **Passive voice / subjectless fragments** | “No configuration file needed” | Name the actor when it helps clarity |

### Style Patterns

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 14 | **Em dash overuse** | “institutions—not the people—yet this continues—“ | Prefer commas or periods |
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
| 21 | **Cutoff disclaimers** | “While details are limited in available sources...” | Find sources or remove |
| 22 | **Sycophantic tone** | “Great question! You're absolutely right!” | Respond directly |

### Filler and Hedging

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 23 | **Filler phrases** | “In order to”, “It is worth noting that”, “Going forward” | Cut or rewrite directly |
| 24 | **Excessive hedging** | “could potentially possibly” | “may” |
| 25 | **Generic conclusions** | “The future looks bright” | Specific plans or facts |

### New in v3.0

| # | Pattern | Before | After |
|---|---------|--------|-------|
| 30 | **Sentence-starter intensifiers** | “Ultimately... Indeed... Clearly... Essentially...” | Cut; state the claim directly |
| 31 | **Rhetorical / self-answering questions** | “What makes this effective? The way it reduces...” | “It works because it reduces...” |
| 32 | **Stacked intensifier adjectives** | “innovative, comprehensive, and forward-thinking” | One specific adjective or none |
| 33 | **Quantity vagueness** | “a wide range of factors... numerous studies” | Specific count or named examples |
| 34 | **Trailing emphasis fragments** | “That's the key. And that matters.” | Delete; the previous sentence said it |

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

## License

MIT
