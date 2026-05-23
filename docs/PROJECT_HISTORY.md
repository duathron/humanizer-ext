# humanizer-ext — Project History

A maintainer's record of what this fork has changed relative to upstream [blader/humanizer](https://github.com/blader/humanizer), in what order, and why.

This document tracks the *narrative* of the fork. The README's "Version history" section is the user-facing condensed changelog; this document is the long form — design rationale, sources, and decisions — including work that is currently in planning.

---

## 1. What this fork is

`humanizer-ext` is a fork of `blader/humanizer`, a Claude Code / OpenCode skill that rewrites AI-generated text to read more like a human wrote it. The skill is built around [Wikipedia's "Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) guide, maintained by WikiProject AI Cleanup.

The fork started from upstream v2.5.1 (29 patterns, single behavior). Current release is v3.2.0 (40 patterns, three modes, five domains, density preflight, detection guidance). A v3.5.0 design — multi-lingual architecture (EN + DE shipped, further packs via documented recipe) and an evaluation infrastructure — is in active planning and documented in §5 below.

## 2. Why this fork exists

Upstream `blader/humanizer` is a well-curated skill but moves slowly and treats every text the same way: every pattern applies in every context, with no opt-out. That produces over-editing in several cases:

- **Domain mismatch.** Passive voice is a real AI tell in a blog post but is conventional in a legal brief and required in an academic methods section. Applying the same rule everywhere flattens domain-appropriate prose into something worse than the input.
- **Over-edits on human writing.** When a real person writes something a little formal, a little tidy, or hits one rule-of-three by accident, the skill can rewrite it into a different voice entirely.
- **Pattern gaps.** New AI tells emerge as models update. Heading patterns ("the X actually", "demystified"), conditional frame stacking, miscalibrated confidence, chat-UI artifacts (`turn0search0`, `oaicite`, `?utm_source=chatgpt.com`) — these are not in upstream as of v2.5.1.
- **No measurement.** Pattern changes are made by hand without a test corpus, so regressions and false positives are caught only by user feedback.
- **English only.** A skill grounded in a Wikipedia community-curated list misses that other Wikipedia communities (DE, FR) maintain equivalent lists for their own languages, and that AI tells are language-specific.

The fork's purpose: address these without losing upstream-sync ability.

## 3. Timeline (factual changes shipped)

| Date | Version | Commit | Summary |
|------|---------|--------|---------|
| 2026-05-21 | 3.1.0 | `5c63234` | Domain-aware overrides (5 domains × 13 patterns) + v3.0.0 pattern expansion (#30–34, expanded vocabulary, mode selector, length audit) |
| 2026-05-21 | (docs) | `979e078` | README "What's different" table; maintainer copyright |
| 2026-05-22 | 3.2.0 | `db2b035` | Detection guidance (false positives + signs of human writing + LLM idiolects); Tier-1 density preflight; 6 new patterns (#35–40); audit checklist 9→13 points |
| 2026-05-22 | (build) | `81b0dec` | Trim SKILL.md `description` under Claude Code 1024-char frontmatter limit |
| 2026-05-22 | (plugin) | `cd6dac0` | `.claude-plugin/plugin.json` — repo installable as Claude Code plugin |
| 2026-05-22 | (plugin) | `074d392` | `.claude-plugin/marketplace.json` — repo doubles as `duathron-skills` marketplace |

## 4. What we changed, how, and why

### 4.1 v3.0.0 / v3.1.0 — Domain awareness + pattern expansion + mode selector

**What:**
- Added a five-domain matrix: casual (default), academic, legal, technical, marketing.
- 13 patterns gained per-domain overrides (SKIP / light / normal / strict).
- Mode selector: Quick (4 universal patterns), Full (all + audit), Voice (Full + sample matching).
- Added patterns #30–34: sentence-starter intensifiers, rhetorical questions, stacked adjectives, quantity vagueness, trailing emphasis fragments.
- Expanded #7 (AI vocabulary), #8 (copula avoidance), #3 (-ing endings), #23 (filler phrases).

**How:** Re-read the Wikipedia source article end-to-end and cross-referenced it against the upstream pattern list to find gaps. The five-domain split came from observing that upstream over-edits in domains where its rules don't apply (legal passives, technical lists, marketing puffery).

**Why:** The single biggest source of user friction with the upstream skill is over-editing in legitimate domains. A domain-aware override matrix solves the largest class of false positives without removing patterns. The mode selector exists because Full mode is overkill for short cleanup tasks; users wanted a lighter pass.

### 4.2 v3.2.0 — Detection guidance, density preflight, six new patterns

**What:**
- **Detection Guidance section.** Three subsections: (a) what NOT to flag (false positives a clean human writer can hit naturally), (b) signs of human writing to preserve (specific detail, mixed feelings, dated references, varied rhythm, parentheticals), (c) per-model LLM idiolects (ChatGPT / Grok / Gemini / Claude tendencies).
- **Tier-1 density preflight.** In Full mode, count Tier-1 dead-giveaway tells (#1, #4, #7, #20, #21, #22, #25) per 100 words *before* the full pass. If density = 0, auto-drop to Quick mode and announce the decision. If 1–2, proceed but preserve voice aggressively. If 3+, full Full pass.
- **Six new patterns:** #35 debunking-pose headings, #36 conditional frame stacking, #37 miscalibrated epistemic confidence, #38 reference-markup artifacts, #39 phrasal templates / placeholder text, #40 markdown / wikitext contamination.
- **Expanded six existing patterns:** #7 (era-specific vocabulary clusters for GPT-4 / GPT-4o / GPT-5 + figurative-vs-literal caveat), #9 ("rather than" dismissals + on-the-table test), #14 (paired em-dash bracketing + four fix options), #21 (speculative gap-filling), #23 (three more didactic disclaimers), #25 (structural `## Conclusion` section deletion).
- **Audit checklist:** grew from 9 to 13 points, each annotated with per-domain exceptions.

**How:** Cherry-picked five upstream PRs (#113, #112, #111, #116, #85) and adapted PR #115. Integrated with the existing domain override matrix — patterns #35–#37 got per-domain overrides; #38–#40 are universal (always strip).

**Why:**
- *Detection guidance:* even with domain overrides, the skill was still over-editing legitimate prose. The fix was to teach Claude what *not* to flag, not just what to flag less. Signs of human writing and per-model idiolects help disambiguate AI vs. polished-human at the inference level.
- *Density preflight:* the worst over-editing happens when a human-first draft enters Full mode. A cheap upfront check that detects "this is already mostly human" avoids the expensive failure mode of rewriting voice quirks into AI-style neutrality.
- *New patterns:* (#35–#37) target the most recent generation of AI tells; (#38–#40) target chat-UI copy-paste contamination which is essentially proof of AI involvement and was missing entirely.

### 4.3 Plugin + marketplace integration

**What:**
- `.claude-plugin/plugin.json` makes the repo a one-line installable Claude Code plugin.
- `.claude-plugin/marketplace.json` makes the same repo a marketplace (`duathron-skills`) so future forks of community skills can ship from the same URL.

**How:** Followed the Claude Code plugin schema. The marketplace structure is intended to accumulate forks over time — humanizer-ext is the first entry.

**Why:** Two install paths are friction (manual clone vs. plugin). The plugin path lowers the install bar to a single command. The marketplace structure is forward-looking: each future fork ships without requiring users to re-add a new marketplace URL.

### 4.4 SKILL.md description trim

**What:** Trimmed the `description:` frontmatter field to fit Claude Code's 1024-character limit.

**Why:** Discovered during plugin packaging that Claude Code rejects skill descriptions over 1024 chars. Trimmed without losing the description's triggering signal.

## 5. In planning — v3.5.0 (multi-lingual architecture + eval infrastructure)

Status: **design phase, not implemented**. Spec is being developed; this section will be updated as decisions are locked in or implementation begins.

### 5.1 Goals

Two parallel goals in a single design:

1. **Multi-lingual architecture (DE shipped first, FR/ES/IT/further packs added via recipe).** Full input + output support, not just detection. Each new language adds isolated files; the framework stays sprach-agnostisch. v3.5.0 itself ships EN + DE; further packs are out of scope for this release but require no framework changes to add.
2. **Eval infrastructure.** Three eval types: pattern detection (unit-style), false-positive rate on human texts, end-to-end rewrite quality (judge-LLM scored).

### 5.2 Architectural decisions made so far

- **Layered SKILL.md + language packs.** SKILL.md becomes the framework only (modes, language detection, domain detection, density preflight, audit, output format, voice-calibration lookup). Pattern lists move to `patterns/{en,de}.md` + `patterns/_universal.md`. Domain overrides move to `domains/{en,de}_overrides.md`.
  - *Rejected alternatives:* inline multi-lingual (single SKILL.md balloons, upstream-sync becomes merge hell), two separate skills per language (bad UX for mixed-language texts, duplicates framework).
- **Universal vs. language-specific pattern split.** Em-dash, boldface, title case, emojis, curly quotes, hyphenation, chat-UI artifacts, placeholders, markdown contamination, structural patterns (challenges section, conclusion section, fragmented headers) live in `patterns/_universal.md` — pflegt man einmal, gilt für jede Sprache. Vocabulary-heavy patterns (#1, #3, #4, #5, #7, #8, #9, #20, #21, #23, #27, #28, #30, #31, #35, #37) live per language.
- **Pattern-ID continuity.** Pattern numbers stay stable across languages (#7 is always "AI vocabulary" in every pack). DE-only patterns start at #100 (Anglizismen-Leakage, Nominalstil-Inflation, Konjunktiv-Stack).
- **Pattern-source strategy per language:**
  - **Phase A — Wiki seed.** EN: [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). DE: [Anzeichen für KI-generierte Inhalte](https://de.wikipedia.org/wiki/Wikipedia:Anzeichen_f%C3%BCr_KI-generierte_Inhalte). FR: [Aide:Identifier l'usage d'une IA générative](https://fr.wikipedia.org/wiki/Aide:Identifier_l'usage_d'une_IA_g%C3%A9n%C3%A9rative). ES + IT: no equivalent dedicated guide found; mining-first path.
  - **Phase B — Empirical mining.** TF-IDF / log-likelihood-ratio script (`evals/scripts/mine_patterns.py`) comparing an AI-generated corpus vs. a human corpus per language. Reusable for any new language.
  - **Phase C — Manual curation.** Linguist-style review of candidates, era-clustering, domain applicability.
  - **Phase D — Cross-reference.** NLP papers, public AI-detection tools, community PRs.
- **Personal samples convention (privacy).** Maintainer/user writing samples (e.g., the maintainer's bachelor thesis) are *not* committed to this repo. Skill lookup chain: `--samples-dir` CLI flag → `$HUMANIZER_SAMPLES_DIR` → `~/.claude/humanizer-samples/` (flat default, single-language) → `./writing-samples/` (per-project). Language subfolders within any of these are optional for multi-language users. Eval mode `--personal` exists for false-positive testing against personal samples without writing artifacts to committed reports.
- **Eval corpus content rules.** `evals/corpus/{lang}/human/` only ships `public_domain/` (Project Gutenberg pre-1923, Wikipedia revisions pre-2022), `synthetic/` (maintainer hand-written, MIT-licensed, anonymized), and `contributed/` (PR-only, opt-in). No third-party personal writing.
- **Eval runner stack.** Python + `claude` CLI, matched to `skill-creator`'s existing eval stack (`run_eval.py`, `aggregate_benchmark.py`). Judge LLM is a CLI flag, defaults to Sonnet, Opus opt-in.
- **Implementation model split.** Spec is being written by Opus. Implementation will be delegated to `cavecrew-builder` / `cavecrew-investigator` / `cavecrew-reviewer` agents running Sonnet, orchestrated by Opus. Each task scoped to ≤2 files (cavecrew-builder limit).

### 5.3 Repo layout (post-refactor target)

```
humanizer-ext/
├── SKILL.md                          # Framework only (~15-20 KB, was 60 KB)
├── README.md
├── patterns/
│   ├── _universal.md                 # language-agnostic patterns
│   ├── en.md                         # current 40 patterns extracted (byte-equivalent at Phase 0)
│   └── de.md                         # new
├── domains/
│   ├── en_overrides.md
│   └── de_overrides.md
├── evals/
│   ├── corpus/{en,de}/{patterns,human,e2e}/
│   ├── scripts/
│   │   ├── _shared.py
│   │   ├── run_pattern_eval.py
│   │   ├── run_false_positive_eval.py
│   │   ├── run_e2e_eval.py
│   │   └── mine_patterns.py
│   ├── reports/                      # gitignored except latest
│   └── README.md
├── tests/                            # pytest sanity (structure only, no API calls)
├── .claude-plugin/
└── docs/
    └── PROJECT_HISTORY.md            # this file
```

### 5.4 Build order

1. **Phase 0 — Refactor (EN only, behavior-preserving).** Split SKILL.md into framework + `patterns/en.md` + `patterns/_universal.md` + `domains/en_overrides.md`. Add `tests/test_skill_structure.py`. Regression-test against existing examples: output must be unchanged.
2. **Phase 1 — Eval infrastructure (EN).** `evals/scripts/_shared.py`, three eval runners, seed `evals/corpus/en/` from existing SKILL.md before/after pairs. Produce EN baseline report.
3. **Phase 2 — DE language pack.** `mine_patterns.py` → DE candidates from generated AI corpus vs. Wikipedia pre-2022 + Gutenberg. Manual curation → `patterns/de.md`. `domains/de_overrides.md` from DE register knowledge. `evals/corpus/de/`. Iterate until pattern-eval ≥ 0.85, false-positive ≤ 0.10, e2e ≥ EN baseline.
4. **Phase 3 — Polish & release.** README updates, `evals/README.md` (how to add a language pack, how to use personal samples), optional CI workflow, v3.5.0 release. Intermediate ships: Phase 0 → v3.3.0 (refactor only, EN behavior unchanged). Phase 1 → v3.4.0 (eval-infra, EN only). Phase 2 → v3.5.0 (DE pack added).

### 5.5 Open questions (not yet decided)

- API budget for mining corpus generation (Phase 2). Need ~500–1000 DE AI texts across five domains via Claude/GPT/Gemini APIs.
- Tagesschau archive / DE news corpus licensing for the human-side of mining (likely fallback: Wikipedia revisions pre-2022 only, which is CC-BY-SA).
- Whether to add a `--audit-only` mode (detect + report without rewriting) as part of v4.0 or punt to v4.1.
- Pattern-coverage gap between EN (40 patterns) and DE (initial ~30 from DE Wiki + mining). Acceptable as long as universal patterns cover the gap and EN-IDs without DE equivalents are documented in `patterns/de.md` as "no DE equivalent".

## 6. Sources of authority

- [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) — original guide; basis for the EN pattern list.
- [Wikipedia:WikiProject AI Cleanup](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup) — maintainers of the EN guide.
- [Wikipedia:Anzeichen für KI-generierte Inhalte (DE)](https://de.wikipedia.org/wiki/Wikipedia:Anzeichen_f%C3%BCr_KI-generierte_Inhalte) — DE Wiki equivalent; Phase A seed for `patterns/de.md`.
- [Aide:Identifier l'usage d'une IA générative (FR)](https://fr.wikipedia.org/wiki/Aide:Identifier_l'usage_d'une_IA_g%C3%A9n%C3%A9rative) — FR Wiki equivalent; future Phase A seed for `patterns/fr.md`.
- Upstream PRs cherry-picked in v3.2.0: #113, #112, #111, #116, #85 from [blader/humanizer](https://github.com/blader/humanizer). PR #115 was adapted rather than merged verbatim.

## 7. Contributing

- **New patterns for an existing language pack:** open a PR against `patterns/{lang}.md` (or `patterns/_universal.md` if the pattern is language-agnostic). Include 5+ before/after cases and a domain-override recommendation.
- **New language pack:** see `evals/README.md` (will be added in v4.0). The 5-step recipe is: Wiki-seed if available → mine candidates → curate manually → build eval corpus → iterate until eval thresholds met.
- **Personal writing samples (Voice mode):** never PR these. Use `~/.claude/humanizer-samples/` locally.
- **Contributed human samples for the eval corpus:** PRs to `evals/corpus/{lang}/human/contributed/` are welcome with a contributor agreement file in the same PR.

## 8. License

MIT. See `LICENSE`.
