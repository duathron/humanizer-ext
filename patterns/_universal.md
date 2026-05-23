# Universal Patterns

These patterns apply identically across all languages. The framework (`SKILL.md`) always loads this file in addition to the language-specific pack.

## STRUCTURAL PATTERNS

### 6. Outline-like "Challenges and Future Prospects" Sections

**Words to watch:** Despite its... faces several challenges..., Despite these challenges, Challenges and Legacy, Future Outlook

**Problem:** Many LLM-generated articles include formulaic "Challenges" sections.

**Before:**
> Despite its industrial prosperity, Korattur faces challenges typical of urban areas, including traffic congestion and water scarcity. Despite these challenges, with its strategic location and ongoing initiatives, Korattur continues to thrive as an integral part of Chennai's growth.

**After:**
> Traffic congestion increased after 2015 when three new IT parks opened. The municipal corporation began a stormwater drainage project in 2022 to address recurring floods.

### 25. Generic Positive Conclusions

**Problem:** Vague upbeat endings.

**Before:**
> The future looks bright for the company. Exciting times lie ahead as they continue their journey toward excellence. This represents a major step in the right direction.

**After:**
> The company plans to open two more locations next year.

**Structural-section note:** A common AI tic is a whole `## Conclusion` (or `## Summary`, `## Final Thoughts`, `## Key Takeaways`, `## Wrapping Up`) section whose only job is to restate the body in slightly different words. The *existence* of the section is the tell — even if the prose inside is clean. Delete the entire section, not just its sentences. If a closing thought is genuinely necessary, write a single sentence with new information ("The same three states will probably decide 2028.") rather than a recap. In modern essay writing, you stop when you have made your point.

### 29. Fragmented Headers

**Signs to watch:** A heading followed by a one-line paragraph that simply restates the heading before the real content begins.

**Problem:** LLMs often add a generic sentence after a heading as a rhetorical warm-up. It usually adds nothing and makes the prose feel padded.

**Before:**
> ## Performance
>
> Speed matters.
>
> When users hit a slow page, they leave.

**After:**
> ## Performance
>
> When users hit a slow page, they leave.

## STYLE PATTERNS

### 14. Em Dash Overuse and Paired Bracketing

**Problem:** LLMs use em dashes (—) more than humans, mimicking "punchy" sales writing. In practice, most of these can be rewritten more cleanly with commas, periods, or parentheses.

A specific sub-pattern is **paired em dash bracketing**: wrapping an elaboration between two dashes (`X — elaboration — continues`). This looks inserted rather than written — like something dropped into an existing sentence rather than composed as part of it.

**Before:**
> The term is primarily promoted by Dutch institutions—not by the people themselves. You don't say "Netherlands, Europe" as an address—yet this mislabeling continues—even in official documents.

**After:**
> The term is primarily promoted by Dutch institutions, not by the people themselves. You don't say "Netherlands, Europe" as an address, yet this mislabeling continues in official documents.

**Before (paired bracketing):**
> The report—which covered three continents and twelve case studies—concluded that demand had shifted.

**After (pick the option that fits the insertion):**
- **If a list:** break into a separate sentence — "The report covered three continents and twelve case studies. It concluded that demand had shifted."
- **If an appositive:** use a comma — "The report, covering three continents and twelve case studies, concluded that demand had shifted."
- **If a true parenthetical aside:** use parentheses — "The report (three continents, twelve case studies) concluded that demand had shifted."
- **If subject expansion:** rewrite as two sentences.

**Exception:** A single, short, earned bracket that does not repeat elsewhere in the passage is fine. The problem is the pattern, not any one instance.

### 15. Overuse of Boldface

**Problem:** AI chatbots emphasize phrases in boldface mechanically.

**Before:**
> It blends **OKRs (Objectives and Key Results)**, **KPIs (Key Performance Indicators)**, and visual strategy tools such as the **Business Model Canvas (BMC)** and **Balanced Scorecard (BSC)**.

**After:**
> It blends OKRs, KPIs, and visual strategy tools like the Business Model Canvas and Balanced Scorecard.

### 17. Title Case in Headings

**Problem:** AI chatbots capitalize all main words in headings.

**Before:**
> ## Strategic Negotiations And Global Partnerships

**After:**
> ## Strategic negotiations and global partnerships

### 18. Emojis

**Problem:** AI chatbots often decorate headings or bullet points with emojis.

**Before:**
> 🚀 **Launch Phase:** The product launches in Q3
> 💡 **Key Insight:** Users prefer simplicity
> ✅ **Next Steps:** Schedule follow-up meeting

**After:**
> The product launches in Q3. User research showed a preference for simplicity. Next step: schedule a follow-up meeting.

### 19. Curly Quotation Marks

**Problem:** ChatGPT outputs typographic/curly quotes (" ") instead of straight ASCII quotes (" "). The characters look nearly identical in most renderers but are different Unicode code points (U+201C/U+201D vs U+0022). Replace all curly quote characters with straight double quotes.

**Before:**
> He said "the project is on track" but others disagreed.

**After:**
> He said "the project is on track" but others disagreed.

### 26. Hyphenated Word Pair Overuse

**Words to watch:** cross-functional, client-facing, data-driven, decision-making, well-known, high-quality, real-time, long-term, end-to-end

**Problem:** AI hyphenates common compound modifiers with perfect consistency. Use judgment: drop hyphens on the most familiar compound modifiers where meaning is unambiguous without them. Less common or technical compounds are fine to keep hyphenated — don't strip blindly.

**Before:**
> The cross-functional team delivered a high-quality, data-driven report on our client-facing tools. Their decision-making process was well-known for being thorough and detail-oriented.

**After:**
> The cross functional team delivered a high quality, data driven report on our client facing tools. Their decision making process was known for being thorough and detail oriented.

## ARTIFACTS AND CONTAMINATION

These patterns appear when someone copies text out of a chat UI and pastes it without scrubbing. They do not occur in genuinely human-written text — when present, AI involvement is essentially confirmed. **Always strip them entirely, regardless of domain.**

### 38. Reference-Markup Artifacts

**Tokens to watch:**
- ChatGPT: `turn0search0`, `citeturn0search0`, `citeturn0news0`, `iturn0image0`, `0`, `:contentReference[oaicite:0]{index=0}`, `oai_citation`, `Example+1`
- Perplexity: `[web:1]`, `[attached_file:1]`
- Grok: `<grok_card>` XML tags, `referrer=grok.com`
- Microsoft Copilot: `utm_source=copilot.com`
- ChatGPT URL parameters: `?utm_source=chatgpt.com`, `?utm_source=openai`
- Cite escapes: `({"attribution":{"attributableIndex":"X-Y"}})`

**Problem:** When a chatbot inlines a citation into its rendered output and the user copies the visible text, the citation becomes broken markup pointing at a chat-internal search index. These artifacts are dead giveaways.

**Before:**
> The 2024 election turned on three states turn0search0, with margins under 1% in each0. Analysts have called it the closest race in modern history :contentReference[oaicite:2]{index=2}.

**After:**
> The 2024 election turned on three states, with margins under 1% in each. Analysts have called it the closest race in modern history. [Add a real citation here, or remove the claim.]

**Before (utm_source pollution):**
> See the [official report](https://example.com/report?utm_source=chatgpt.com) for details.

**After:**
> See the [official report](https://example.com/report) for details.

### 39. Phrasal Templates and Placeholder Text

**Tokens to watch:** `[INSERT NAME]`, `[YOUR BRAND HERE]`, `[ADD CITATION]`, `[Year]`, `2025-xx-xx`, `XXXX`, `___`, `<placeholder>`, "fill in the blank"

**Problem:** LLMs often produce Mad-Libs-style templates with placeholders meant to be replaced. Users sometimes paste them in raw. Date placeholders like `2025-xx-xx` are especially common in citation `access-date` fields.

**Before:**
> Founded in [YEAR], [COMPANY NAME] is a leading provider of [INDUSTRY] solutions. Accessed 2025-xx-xx.

**After:**
> Founded in 2014, Acme Robotics builds warehouse automation systems. Accessed 1 May 2026.

If you do not know the value, delete the sentence rather than ship the placeholder.

### 40. Markdown / Wikitext Contamination

**Signs to watch:**
- Triple-backtick fences left in prose: ` ```markdown `, ` ```wikitext `, ` ``` `
- Meta-prompts the chatbot wrote to *itself*: "Would you like me to convert this to ___?", "Here is the formatted version:", "I have rewritten the section as requested"
- Mixed `##` headings inside what should be a Wikipedia / wiki / plain-text document
- Lone `---` thematic breaks placed before every heading (Markdown export habit)
- Triple backticks around inline content that wasn't supposed to be code

**Problem:** The chat UI rendered the Markdown; the underlying text the user copied still has the syntax characters. When that gets pasted into a non-Markdown destination (or into a Markdown destination with a different convention), it shows up as literal junk or unwanted formatting.

**Before:**
> ```markdown
> ## Background
> ---
> The company was founded in 1994.
> ```
> Would you like me to expand the Background section, add citations, or convert this into wikitext?

**After:**
> ## Background
>
> The company was founded in 1994.
