# English Patterns

English-specific patterns. Loaded by the framework (`SKILL.md`) when the detected input language is English. Apply alongside `patterns/_universal.md`.

## PERSONALITY AND SOUL

Avoiding AI patterns is only half the job. Sterile, voiceless writing is just as obvious as slop. Good writing has a human behind it.

> **Domain note:** This section applies fully to **casual** writing, lightly to **technical**, and **not at all** to **academic**, **legal**, or **marketing** writing. Academic and legal prose are properly impersonal — adding "soul" makes them worse. Marketing prose has its own register (persuasive, confident) and shouldn't be rewritten in a personal-blog voice. Use this section's guidance only when the domain calls for personal voice.

### Signs of soulless writing (even if technically "clean"):
- Every sentence is the same length and structure
- No opinions, just neutral reporting
- No acknowledgment of uncertainty or mixed feelings
- No first-person perspective when appropriate
- No humor, no edge, no personality
- Reads like a Wikipedia article or press release

### How to add voice:

**Have opinions.** Don't just report facts — react to them. "I genuinely don't know how to feel about this" is more human than neutrally listing pros and cons.

**Vary your rhythm.** Short punchy sentences. Then longer ones that take their time getting where they're going. Mix it up.

**Acknowledge complexity.** Real humans have mixed feelings. "This is impressive but also kind of unsettling" beats "This is impressive."

**Use "I" when it fits.** First person isn't unprofessional — it's honest. "I keep coming back to..." or "Here's what gets me..." signals a real person thinking.

**Let some mess in.** Perfect structure feels algorithmic. Tangents, asides, and half-formed thoughts are human.

**Be specific about feelings.** Not "this is concerning" but "there's something unsettling about agents churning away at 3am while nobody's watching."

### Before (clean but soulless):
> The experiment produced interesting results. The agents generated 3 million lines of code. Some developers were impressed while others were skeptical. The implications remain unclear.

### After (has a pulse):
> I genuinely don't know how to feel about this one. 3 million lines of code, generated while the humans presumably slept. Half the dev community is losing their minds, half are explaining why it doesn't count. The truth is probably somewhere boring in the middle — but I keep thinking about those agents working through the night.


## CONTENT PATTERNS

### 1. Undue Emphasis on Significance, Legacy, and Broader Trends

**Words to watch:** stands/serves as, is a testament/reminder, a vital/significant/crucial/pivotal/key role/moment, underscores/highlights its importance/significance, reflects broader, symbolizing its ongoing/enduring/lasting, contributing to the, setting the stage for, marking/shaping the, represents/marks a shift, key turning point, evolving landscape, focal point, indelible mark, deeply rooted

**Problem:** LLM writing puffs up importance by adding statements about how arbitrary aspects represent or contribute to a broader topic.

**Before:**
> The Statistical Institute of Catalonia was officially established in 1989, marking a pivotal moment in the evolution of regional statistics in Spain. This initiative was part of a broader movement across Spain to decentralize administrative functions and enhance regional governance.

**After:**
> The Statistical Institute of Catalonia was established in 1989 to collect and publish regional statistics independently from Spain's national statistics office.


### 2. Undue Emphasis on Notability and Media Coverage

**Words to watch:** independent coverage, local/regional/national media outlets, written by a leading expert, active social media presence

**Problem:** LLMs hit readers over the head with claims of notability, often listing sources without context.

**Before:**
> Her views have been cited in The New York Times, BBC, Financial Times, and The Hindu. She maintains an active social media presence with over 500,000 followers.

**After:**
> In a 2024 New York Times interview, she argued that AI regulation should focus on outcomes rather than methods.


### 3. Superficial Analyses with -ing Endings

**Words to watch:** highlighting/underscoring/emphasizing..., ensuring..., reflecting/symbolizing..., contributing to..., cultivating/fostering..., encompassing..., showcasing..., resonating with..., aligning with..., providing valuable insights into...

**Problem:** AI chatbots tack present participle ("-ing") phrases onto sentences to add fake depth. The phrases claim meaning without adding any.

**Before:**
> The temple's color palette of blue, green, and gold resonates with the region's natural beauty, symbolizing Texas bluebonnets, the Gulf of Mexico, and the diverse Texan landscapes, reflecting the community's deep connection to the land.

**After:**
> The temple uses blue, green, and gold colors. The architect said these were chosen to reference local bluebonnets and the Gulf coast.


### 4. Promotional and Advertisement-like Language

**Words to watch:** boasts a, vibrant, rich (figurative), profound, enhancing its, showcasing, exemplifies, commitment to, natural beauty, nestled, in the heart of, groundbreaking (figurative), renowned, breathtaking, must-visit, stunning, diverse array, featuring

**Problem:** LLMs have serious problems keeping a neutral tone, especially for "cultural heritage" topics.

**Before:**
> Nestled within the breathtaking region of Gonder in Ethiopia, Alamata Raya Kobo stands as a vibrant town with a rich cultural heritage and stunning natural beauty.

**After:**
> Alamata Raya Kobo is a town in the Gonder region of Ethiopia, known for its weekly market and 18th-century church.


### 5. Vague Attributions and Weasel Words

**Words to watch:** Industry reports, Observers have cited, Experts argue, Some critics argue, several sources/publications (when few cited), valuable insights

**Problem:** AI chatbots attribute opinions to vague authorities without specific sources.

**Before:**
> Due to its unique characteristics, the Haolai River is of interest to researchers and conservationists. Experts believe it plays a crucial role in the regional ecosystem.

**After:**
> The Haolai River supports several endemic fish species, according to a 2019 survey by the Chinese Academy of Sciences.


## LANGUAGE AND GRAMMAR PATTERNS

### 7. Overused "AI Vocabulary" Words

**High-frequency AI words:** Actually, additionally, align with, bolstered, comprehensive, crucial, delve, emphasizing, enduring, enhance, fostering, garner, highlight (verb), interplay, intricate/intricacies, intuitive, key (adjective), landscape (abstract noun), meticulous/meticulously, pivotal, robust, seamless, showcase, tapestry (abstract noun), testament, underscore (verb), valuable, vibrant

**Problem:** These words appear far more frequently in post-2023 text and often co-occur — where there's one, there are usually others. One or two in an edit may be coincidence; many in the same passage is one of the strongest tells. "Robust," "meticulous," "seamless," and "comprehensive" have surged particularly in technical and professional AI writing.

**Era-specific clusters** (the vocabulary has shifted over time, useful for dating suspect text):

- **2023 to mid-2024 (GPT-4 era):** *additionally*, *boasts*, *bolstered*, *crucial*, *delve*, *emphasizing*, *enduring*, *garner*, *intricate/intricacies*, *interplay*, *key*, *landscape*, *meticulous/meticulously*, *pivotal*, *underscore*, *tapestry*, *testament*, *valuable*, *vibrant*
- **Mid-2024 to mid-2025 (GPT-4o era):** *align with*, *bolstered*, *crucial*, *emphasizing*, *enhance*, *enduring*, *fostering*, *highlighting*, *pivotal*, *showcasing*, *underscore*, *vibrant*
- **Mid-2025 onward (GPT-5 era):** *emphasizing*, *enhance*, *highlighting*, *showcasing* (plus heavier reliance on notability/media-coverage padding — see #2)

**Caveat:** Keep context in mind. *Underscore* can mean a literal underline; *delve* may be a perfectly fine verb in geology; *landscape* is the actual term in painting and design. Flag the figurative, throat-clearing use, not the literal one.

**Before:**
> Additionally, a distinctive feature of Somali cuisine is the incorporation of camel meat. An enduring testament to Italian colonial influence is the widespread adoption of pasta in the local culinary landscape, showcasing how these dishes have integrated into the traditional diet.

**After:**
> Somali cuisine also includes camel meat, which is considered a delicacy. Pasta dishes, introduced during Italian colonization, remain common, especially in the south.


### 8. Avoidance of "is"/"are" (Copula Avoidance)

**Words to watch:** serves as/stands as/marks/represents [a], boasts/features/offers/maintains [a]

**Problem:** LLMs substitute elaborate constructions for simple copulas.

**Before:**
> Gallery 825 serves as LAAA's exhibition space for contemporary art. The gallery features four separate spaces and boasts over 3,000 square feet.

**After:**
> Gallery 825 is LAAA's exhibition space for contemporary art. The gallery has four rooms totaling 3,000 square feet.


### 9. Negative Parallelisms, Tailing Negations, and "Rather Than" Dismissals

**Problem:** Constructions like "Not only...but..." or "It's not just about..., it's..." are overused. So are clipped tailing-negation fragments such as "no guessing" or "no wasted motion" tacked onto the end of a sentence instead of written as a real clause. A third form of the same pattern is "rather than" used to stage a contrast by dismissing an alternative that nobody was claiming in the first place.

**Before:**
> It's not just about the beat riding under the vocals; it's part of the aggression and atmosphere. It's not merely a song, it's a statement.

**After:**
> The heavy beat adds to the aggressive tone.

**Before (tailing negation):**
> The options come from the selected item, no guessing.

**After:**
> The options come from the selected item without forcing the user to guess.

**Before ("rather than" dismissal):**
> The goal is to write clearly rather than to impress the reader with complexity.

**After:**
> The goal is to write clearly.

**On-the-table test:** Ask whether the discarded alternative (Y in "X rather than Y") is actually something anyone was claiming. If no one was claiming Y, cut the dismissal and just say X.


### 10. Rule of Three Overuse

**Problem:** LLMs force ideas into groups of three to appear comprehensive.

**Before:**
> The event features keynote sessions, panel discussions, and networking opportunities. Attendees can expect innovation, inspiration, and industry insights.

**After:**
> The event includes talks and panels. There's also time for informal networking between sessions.


### 11. Elegant Variation (Synonym Cycling)

**Problem:** AI has repetition-penalty code causing excessive synonym substitution.

**Before:**
> The protagonist faces many challenges. The main character must overcome obstacles. The central figure eventually triumphs. The hero returns home.

**After:**
> The protagonist faces many challenges but eventually triumphs and returns home.


### 12. False Ranges

**Problem:** LLMs use "from X to Y" constructions where X and Y aren't on a meaningful scale.

**Before:**
> Our journey through the universe has taken us from the singularity of the Big Bang to the grand cosmic web, from the birth and death of stars to the enigmatic dance of dark matter.

**After:**
> The book covers the Big Bang, star formation, and current theories about dark matter.


### 13. Passive Voice and Subjectless Fragments

**Problem:** LLMs often hide the actor or drop the subject entirely with lines like "No configuration file needed" or "The results are preserved automatically." Rewrite these when active voice makes the sentence clearer and more direct.

**Before:**
> No configuration file needed. The results are preserved automatically.

**After:**
> You do not need a configuration file. The system preserves the results automatically.


## STYLE PATTERNS

### 16. Inline-Header Vertical Lists

**Problem:** AI outputs lists where items start with bolded headers followed by colons. Convert to prose — but only when the items are genuinely prose broken into fake bullets. Preserve lists when content is truly list-like (step-by-step instructions, feature comparisons, data tables).

**Before (fake bullets — convert to prose):**
> - **User Experience:** The user experience has been significantly improved with a new interface.
> - **Performance:** Performance has been enhanced through optimized algorithms.
> - **Security:** Security has been strengthened with end-to-end encryption.

**After:**
> The update improves the interface, speeds up load times through optimized algorithms, and adds end-to-end encryption.


## COMMUNICATION PATTERNS

### 20. Collaborative Communication Artifacts

**Words to watch:** I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like..., let me know, here is a...

**Problem:** Text meant as chatbot correspondence gets pasted as content.

**Before:**
> Here is an overview of the French Revolution. I hope this helps! Let me know if you'd like me to expand on any section.

**After:**
> The French Revolution began in 1789 when financial crisis and food shortages led to widespread unrest.


### 21. Knowledge-Cutoff Disclaimers and Speculative Gap-Filling

**Words to watch:** as of [date], Up to my last training update, While specific details are limited/scarce..., based on available information, not extensively documented, not publicly available, maintains a low profile, keeps personal details private, prefers to keep [X] out of the spotlight, likely [verb], it is believed that

**Problem:** Two related patterns. (a) Older models leave hard knowledge-cutoff disclaimers in the text. (b) Newer retrieval-augmented models, when they can't find a source, write a paragraph *about not having found one*, then speculate about what the missing information "likely" is. When the gap is about a private person, the speculation almost always settles on the same template: this person "maintains a low profile" or "keeps personal details private" — neither claim is sourced; both are face-saving filler.

**Before (cutoff disclaimer):**
> While specific details about the company's founding are not extensively documented in readily available sources, it appears to have been established sometime in the 1990s.

**After:**
> The company was founded in 1994, according to its registration documents.

**Before (speculative gap-fill about a person):**
> Information about her early life is not publicly available, suggesting she maintains a low profile and keeps personal details private. She likely grew up in a middle-class household, which would have shaped her later interest in education reform.

**After:**
> Her early life is not documented in the sources used here. (Or simply omit the section.)


### 22. Sycophantic/Servile Tone

**Problem:** Overly positive, people-pleasing language.

**Before:**
> Great question! You're absolutely right that this is a complex topic. That's an excellent point about the economic factors.

**After:**
> The economic factors you mentioned are relevant here.


## FILLER AND HEDGING

### 23. Filler Phrases

**Before → After:**
- "In order to achieve this goal" → "To achieve this"
- "Due to the fact that it was raining" → "Because it was raining"
- "At this point in time" → "Now"
- "In the event that you need help" → "If you need help"
- "The system has the ability to process" → "The system can process"
- "It is important to note that the data shows" → "The data shows"
- "Keep in mind that the system requires..." → "The system requires..."
- "It should be remembered that..." → delete; state the thing directly
- "As always, please consult a professional" → delete unless legally required, then move to a footer
- "As such, the results confirm..." → "So the results confirm..." or restructure
- "It is worth noting that..." → delete; state the thing directly
- "It goes without saying that..." → delete; state the thing directly
- "Moving forward, we will..." → "We will..." or give a specific date
- "Going forward, the plan is..." → "The plan is..."
- "In terms of performance..." → rewrite the sentence
- "A wide range of factors" → "[specific count] factors" or name them
- "A variety of approaches" → name the approaches or give a count
- "The fact that X is true" → "X is true" or restructure

**Didactic-disclaimer note:** "It is important to note", "Keep in mind", "It should be remembered", and "as always, consult a professional" were a GPT-3.5 / early-GPT-4 signature. Newer models leak them too, especially in health, law, finance, or controversy. Skip the disclaimer unless the document genuinely requires it (regulatory filing, terms of service, literal advice column) — and even then, it belongs in a footer or sidebar, not woven through the body.


### 24. Excessive Hedging

**Problem:** Over-qualifying statements.

**Before:**
> It could potentially possibly be argued that the policy might have some effect on outcomes.

**After:**
> The policy may affect outcomes.


## PERSUASION AND SIGNPOSTING

### 27. Persuasive Authority Tropes

**Phrases to watch:** The real question is, at its core, in reality, what really matters, fundamentally, the deeper issue, the heart of the matter, in essence, essentially (as a framing device), what it comes down to

**Problem:** LLMs use these phrases to pretend they are cutting through noise to some deeper truth, when the sentence that follows usually just restates an ordinary point with extra ceremony.

**Before:**
> The real question is whether teams can adapt. At its core, what really matters is organizational readiness.

**After:**
> The question is whether teams can adapt. That mostly depends on whether the organization is ready to change its habits.


### 28. Signposting and Announcements

**Phrases to watch:** Let's dive in, let's explore, let's break this down, here's what you need to know, now let's look at, without further ado, in this section we'll cover

**Problem:** LLMs announce what they are about to do instead of doing it. This meta-commentary slows the writing down and gives it a tutorial-script feel.

**Before:**
> Let's dive into how caching works in Next.js. Here's what you need to know.

**After:**
> Next.js caches data at multiple layers, including request memoization, the data cache, and the router cache.


## NEWER LANGUAGE TELLS

### 30. Sentence-Starter Intensifiers

**Words to watch:** Ultimately, Indeed, Clearly, Essentially, Fundamentally, Obviously, Naturally, Notably, Importantly, Significantly (as sentence openers)

**Problem:** AI uses these to sound authoritative or add emphasis without adding content. As sentence openers they almost always just pad the claim that follows.

**Before:**
> Ultimately, what matters most is execution. Indeed, the data confirms this. Clearly, the old approach was flawed.

**After:**
> What matters most is execution. The data confirms this. The old approach was flawed.


### 31. Rhetorical and Self-Answering Questions

**Problem:** LLMs set up questions and then immediately answer them, creating a fake sense of depth or drama. The question adds ceremony without adding content. Also watch for questions that exist only to introduce a section — the question disappears when you just start with the answer.

**Before:**
> What makes this approach effective? The way it reduces cognitive load. Why does that matter? Because users abandon tools that are hard to use.

**After:**
> The approach works because it reduces cognitive load — a key reason users abandon complex tools.

**Variant:**
> Why should you care? Because X is critical to Y.

**Fix:** Just state the claim directly: "X is critical to Y."


### 32. Stacked Intensifier Adjectives

**Problem:** AI stacks multiple positive adjectives to sound comprehensive, when one specific adjective (or none) would be stronger.

**Before:**
> This innovative, comprehensive, and forward-thinking solution addresses the needs of modern organizations.

**After:**
> This solution addresses the needs of modern organizations.

If an adjective genuinely applies, use one: "This modular solution..."


### 33. Quantity Vagueness

**Words to watch:** a wide range of, a variety of, numerous, countless, various, many different, a number of, several different, multiple (when count is knowable)

**Problem:** AI avoids committing to specifics, using vague quantity phrases instead of actual numbers or named examples.

**Before:**
> A wide range of factors contributed to the outcome. Numerous studies have confirmed these findings across various contexts.

**After:**
> Three factors drove the outcome: funding cuts, staff turnover, and delayed permits. Four independent studies confirmed the effect in school, hospital, and corporate settings.


### 34. Trailing Emphasis Fragments

**Problem:** AI tacks short emphatic sentences onto the end of a paragraph for dramatic effect. They almost always restate what was just said and add nothing.

**Before:**
> The system processes requests in under 50ms. That's the key. And that matters.

**After:**
> The system processes requests in under 50ms.


## HEADING PATTERNS

### 35. Debunking-Pose Headings

**Phrases to watch (in headings):** actually, really, the real X, that lands, that works, that matters, the truth about X, what X really means, the death of, the long game, demystified, explained, decoded, rethought, reimagined

**Problem:** LLMs write headings that pose against an implied wrong version of the topic: "actually," "the real," "that lands," "the truth about." The pose announces *everyone else has it slightly wrong, but I'll give you the truth* — without delivering anything different than a plain heading would. This is pattern #27 (Persuasive Authority Tropes) operating at the heading level, and a sibling of pattern #1 (Significance Inflation): the heading promises a reveal it cannot keep.

The pattern is hardest to see because headings read as structure rather than copy, and editors instinctively leave them alone. **Audit headings explicitly as a separate pass.**

**Before:**
> ## What the research actually says
> ## Why your adult child cut you off (the real map)
> ## The architecture of a letter that lands
> ## Grandchildren: the long game
> ## The truth about pricing models, explained

**After:**
> ## What the research says
> ## Why your adult child cut you off
> ## The architecture of an amends letter
> ## Grandchildren
> ## How pricing models work

Keep the pose only when the section genuinely overturns a specific received view, and name that view in the opening paragraph. Otherwise cut the pose and let the content do the work.


## EPISTEMIC PATTERNS

### 36. Conditional Frame Stacking

**Problem:** AI hedges its own conclusions by stacking multiple "if" clauses in the same passage — "if the argument holds," "if the reading is right," "if this interpretation is correct." One conditional at a genuine analytical branching point is fine. A cluster of them in a conclusion or summary signals the writer is not standing behind their own work.

**Before:**
> If the argument holds, and if the evidence supports this reading, then the policy may have had some effect — if, that is, the context was as described.

**After:**
> The evidence supports the argument that the policy had an effect in this context.

**Fix:** In a conclusion or summary, state what the argument found. Reserve "if" for real analytical branches where the outcome genuinely differs depending on the condition — not as a repeated hedge against being wrong.


### 37. Miscalibrated Epistemic Confidence

**Problem:** A two-sided pattern. AI swings between over-asserting and over-hedging, sometimes in the same passage.

- **Over-assertion:** Loading claims with words like "decisively," "fundamentally," "completely," "unquestionably," "clearly demonstrates" when the evidence is more limited.
- **Over-hedging:** Layering qualifiers such as "appears to have arguably," "may have somewhat," "could potentially suggest" when the evidence actually supports a more direct statement.

Both are tells. The fix is not to replace one extreme with the other — it is to narrow the claim to what the evidence actually supports.

**Before (over-assertion):**
> The data decisively demonstrates that remote work fundamentally transformed productivity across all sectors.

**After:**
> In the surveyed companies, productivity rose an average of 8% in the first year of remote work.

**Before (over-hedging):**
> It appears that the policy may have arguably had some effect on outcomes, potentially suggesting a modest shift.

**After:**
> The policy was associated with a modest improvement in outcomes in two of the three cases studied.

**Critical rule:** Do not fix over-assertion by adding hedges. Fix it by narrowing the claim.
