# humanizer-ext — Project History

A maintainer's record of what this fork has changed relative to upstream [blader/humanizer](https://github.com/blader/humanizer), in what order, and why.

This document tracks the *narrative* of the fork. The README's "Version history" section is the user-facing condensed changelog; this document is the long form — design rationale, sources, and decisions — including work that is currently in planning.

---

## 1. What this fork is

`humanizer-ext` is a fork of `blader/humanizer`, a Claude Code / OpenCode skill that rewrites AI-generated text to read more like a human wrote it. The skill is built around [Wikipedia's "Signs of AI writing"](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) guide, maintained by WikiProject AI Cleanup.

The fork started from upstream v2.5.1 (29 patterns, single behavior). Current main is post-v3.4.0 (commits merged, tag pending fresh baseline) — the fork now has 40 patterns, three modes, five domains, density preflight, detection guidance, a layered framework + pattern packs (v3.3.0), and a three-tier eval harness with idempotent per-case partials for resume-across-sessions (v3.4.0). Phase 2 of the v3.5.0 design — the first non-English language pack (German) — is the remaining piece of the design and is documented in §5 below.

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
| 2026-05-23 | (design) | `4bb6e00`, `0540e33`, `6a4b801` | v3.5.0 design spec, PROJECT_HISTORY narrative, Phase 0 implementation plan |
| 2026-05-24 | 3.3.0 | `f973735` (tag pushed) | SKILL.md refactor: split into framework + `patterns/_universal.md` (12 patterns) + `patterns/en.md` (28 + PERSONALITY) + `domains/en_overrides.md`. 15 pytest schema tests added. Pattern #14 (em dash) exception tightened to a 5-condition check with separate audit pass. Zero observable EN behavior change; manual regression recorded in `docs/regression-cases/RESULTS.md` |
| 2026-05-24 | (design) | `b488192` | Phase 1 implementation plan (eval infrastructure) |
| 2026-05-25 | 3.4.0 (tag pending) | `26174c8` (HEAD on origin/main) | Three-tier eval harness: `evals/scripts/run_pattern_eval.py` + `run_false_positive_eval.py` + `run_e2e_eval.py` with judge LLM via Anthropic SDK tool-use. `_shared.py` exports `Case`, `load_pattern_corpus`, `parse_skill_output`, `run_skill` (with retry + API-key-strip), `verify_skill_install` (checks SKILL.md + pack files), `write_report`, `retry_with_backoff`. 22 new pytest tests (37 total). EN corpus: 40/40 patterns seeded (pattern #23 added manually), 5 synthetic human samples, 5 AI E2E cases, judge rubric. E2E batching supports incremental per-case partial caching for split runs across Pro plan sessions. Initial baseline numbers were stale (pre-fix) and are clearly flagged; fresh baseline + v3.4.0 tag pending |

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

### 4.5 v3.3.0 — SKILL.md refactor into framework + language packs (Phase 0 of v3.5.0 design)

**What:**
- Split the 60-KB monolithic `SKILL.md` into a ~15-KB language-agnostic framework plus three pack files: `patterns/_universal.md` (12 universal patterns), `patterns/en.md` (28 EN-specific patterns + the PERSONALITY AND SOUL section), and `domains/en_overrides.md` (the domain override matrix + domain-specific guidance prose).
- Added `tests/test_skill_structure.py` — 15 pytest sanity tests that verify frontmatter validity, pack-file existence, expected pattern-ID sets per pack, disjoint EN/universal pattern IDs, and cross-reference integrity (every pattern ID in `en_overrides.md` resolves to a pack file).
- Added `pyproject.toml` for pytest configuration and dev-dependency declaration.
- Pattern #14 (em-dash) exception tightened during the release: replaced the loose "earned single em dash" allowance with five explicit conjunctive conditions plus a mandatory separate post-rewrite count audit, after both regression runs (pre- and post-refactor) left em dashes the audit should have caught.
- Captured a regression baseline (`docs/regression-cases/full_example.md`) from the v3.2.0 monolithic `## Full Example` and ran a manual regression against the refactored skill; result recorded as PASS in `docs/regression-cases/RESULTS.md`.
- Repo gained Python tooling artifacts in `.gitignore` (`__pycache__/`, `.pytest_cache/`, `.venv/`, `*.pyc`) plus a `writing-samples/` rule to keep personal voice samples out of the repo.

**How:** Phase 0 of the v3.5.0 design (spec at `docs/specs/2026-05-23-humanizer-eval-de-design.md`). Executed via `superpowers:subagent-driven-development`: `cavecrew-builder` (Sonnet) handled the surgical ≤2-file edits per task; the parent (Opus) orchestrated, ran pytest between tasks, and made linguistic judgment calls for the pattern #14 tightening. Implementation done in a `worktree-v3.3.0-refactor` isolated worktree created via `EnterWorktree`, fast-forward merged to `main` after the manual regression passed.

**Why:**
- Adding a second language to the monolithic SKILL.md would double its size and make upstream sync (from `blader/humanizer`) intractable. Layering by responsibility keeps the framework upstream-sync-friendly and makes new language packs additive instead of merge-prone.
- The pytest sanity tests cost nothing per run (no API calls), catch the kinds of structural mistakes that a future refactor or pack addition could silently introduce, and give an objective signal that the cross-reference integrity holds across all packs.
- The pattern #14 tightening landed during the release because both regression runs surfaced the same em-dash-retention behavior; addressing it in the same release as the structural change kept the v3.3.0 changelog narrative coherent.

### 4.6 v3.4.0 — Evaluation infrastructure (Phase 1 of v3.5.0 design)

**What:**
- Three eval runners under `evals/scripts/`:
  - `run_pattern_eval.py` — per-pattern detection rate against curated before/after JSON cases. `score_case` runs the skill via `claude -p` and reports which `expected_changes` substrings survived in the rewrite. Threshold 0.85 per pattern.
  - `run_false_positive_eval.py` — Levenshtein edit ratio between input and rewrite for known-human samples. Threshold ≤ 0.10. Includes a density-preflight signal (did the skill correctly identify the input as human-authored and downgrade to Quick mode). Personal-mode lookup chain (`--samples-dir` flag → `$HUMANIZER_SAMPLES_DIR` → `~/.claude/humanizer-samples/` → `./writing-samples/`) per spec §4.4.
  - `run_e2e_eval.py` — whole-document rewrite quality scored by a judge LLM via the Anthropic SDK using structured tool-use (1–10 on human-ness, meaning preservation, length appropriateness). Default judge model: Sonnet 4.6. Opus 4.7 opt-in via `--judge-model opus`. Each case runs 3× to capture both skill sampling and judge noise.
- Shared utilities in `evals/scripts/_shared.py`: `Case` dataclass, `load_pattern_corpus`, `parse_skill_output` (heuristic fallback chain: `**Final rewrite:**` → alternate headers → last blockquote → text-after-`---` → whole-text-when-no-banners → empty), `run_skill` (subprocess wrapper around `claude -p` with retry, timeout, and `ANTHROPIC_API_KEY` stripped from the CLI's subprocess env), `retry_with_backoff`, `write_report` (paired JSON + Markdown), `verify_skill_install` (SHA-256 hash check on `SKILL.md` AND pack files under the install root). 22 new pytest tests cover the shared utilities (37 tests total in the repo).
- Judge prompt in `evals/scripts/judge_prompt.md` — strict rubric defining the three scoring dimensions and the `report_scores` tool schema.
- EN corpus seeded automatically by `evals/scripts/seed_pattern_corpus.py`: 40/40 patterns covered (39 from auto-extraction of `**Before:**` blocks in the pattern packs; pattern #23 added manually because it uses a `Before → After:` bullet-list format the seeder regex does not match). 5 synthetic human samples (one per domain) under `evals/corpus/en/human/synthetic/`. 5 AI-generated whole-document E2E cases under `evals/corpus/en/e2e/`.
- E2E batching: per-case partials cached under `evals/reports/_partial/e2e_<lang>_<case_id>.json` immediately after scoring. Re-runs skip cases that have a partial. `--cases <ids>` flag scopes a single session to a subset; `--aggregate-only` flag combines cached partials into the final summary without API calls. Supports splitting the E2E eval across multiple Claude Pro plan sessions when the daily quota would not cover a full run.
- `evals/README.md` documents the prerequisites (skill install symlinks for `verify_skill_install`), runner usage, the multi-session batching workflow, and the recipe for adding a new language pack per the v3.5.0 spec.
- Baseline numbers from the initial release run live in `evals/reports/summary_latest_en.{json,md}` but are clearly flagged as STALE — the polish-branch fixes invalidated them (see §4.7). A defensible re-baseline is the gating step for the v3.4.0 tag.

**How:** Phase 1 of the v3.5.0 design. Plan at `docs/plans/2026-05-24-phase-1-eval-infrastructure.md` (20 atomic tasks, each ≤2 files). Same execution pattern as v3.3.0: `cavecrew-builder` subagents (Sonnet) for the per-task surgical edits, parent (Opus) for orchestration and the live baseline runs. `worktree-v3.4.0-eval` worktree merged to `main` after the runner code stabilized; the initial baseline run uncovered three transient/structural CLI issues that were caught and patched mid-run (see "Three patches that landed during the initial run" below).

**Why:**
- Without measurement, every pattern change to the skill is a guess. The three-tier harness gives objective signal at three levels of fidelity: pattern detection (cheap, deterministic-ish), false-positive on human texts (catches over-editing), end-to-end rewrite quality (the actual user-facing signal).
- The judge LLM uses the Anthropic SDK directly (not `claude -p`) because the SDK's structured tool-use guarantees deterministic JSON scores that aggregate cleanly across the 3-run variance. The CLI's free-form text output would require additional parsing layers that introduce their own noise.
- Per-case partials with idempotent resume came from the practical reality that a 5-case × 3-run × (1 skill + 1 judge) E2E eval = 30 API calls, and the Claude Pro subscription session limit can refuse to cover that in a single session. Splitting across sessions without burning quota on re-runs is what makes the eval actually runnable on a Pro plan.

**Three patches that landed during the initial run:**
1. `retry_with_backoff` wrap around `run_skill` (3 attempts, base_delay=2s) — the claude CLI occasionally returns exit 1 with empty stderr in batch use, transient but not rare.
2. `ANTHROPIC_API_KEY` stripped from the claude-CLI subprocess environment — the CLI prefers subscription auth, and an API key in the parent env can interfere with longer-prompt requests (still working through the exact failure mode).
3. `SkillRunError` now includes `stdout` in its message in addition to `stderr` — which is how we discovered the subscription session-limit failure (`stdout: "You've hit your session limit · resets 9pm (Europe/Berlin)"`) instead of staring at empty stderr.

### 4.7 v3.4.0 polish — reviewer + first-run findings addressed

**What:**
- `score_case` (pattern eval) now filters `expected_changes` to only the terms actually present in the input before scoring, and reports an explicit `status: unscorable_*` for cases that can't be meaningfully scored (empty list, or no trigger terms in input). Previously, broad seeded trigger lists dragged scores to 0.0 for most patterns because terms that never appeared in input could never be "removed" from the rewrite. This was the proximate cause of the 24.4% initial baseline.
- `parse_skill_output` gained a heuristic fallback chain — alternate header recognition, last-blockquote extraction, text-after-`---` segment, whole-text only when no banners are present — so Quick-mode and density-dropped Full-mode outputs no longer return the entire skill response (pre-flight + audit + final) as "the rewrite". Was driving the FP eval mean edit ratio to 0.84 (parsing artifact, not skill regression).
- `verify_skill_install` extended to hash-check the pack files (`patterns/_universal.md`, `patterns/en.md`, `domains/en_overrides.md`) under the install root in addition to `SKILL.md` — a stale pack symlink no longer slips past the guard.
- `run_e2e_eval` threshold check now considers all three dimensions (`human_ness`, `meaning`, `length`) instead of only `human_ness`, and `below_threshold_by_dimension` breakdown lands in the summary. `main()` exits non-zero on any threshold failure when all cases are scored.
- `run_false_positive_eval` no longer hardcodes `lang="en"` in `score_human_text` — passes through the `--lang` flag. `--corpus personal` now resolves the personal-samples lookup chain per spec §4.4 instead of a bogus repo path.
- SKILL.md `## Output Format` section got an explicit strict-format spec for Quick mode (entire response IS the rewrite, no banners) and for Full-mode-dropping-to-Quick (preflight banner allowed, rewrite still wrapped in `**Final rewrite:**` block for the parser to extract cleanly).

**How:** Polish branch (`worktree-v3.4.0-polish`) merged to `main` as commits `7b0538c`, `ee77b37`, `0a81dce`, `6273832`, `26174c8`. Reviewer findings from the final cavecrew-reviewer pass on the eval-infra branch drove the runner fixes; the parse-skill-output fix came from observing the FP eval result directly. 22 → 22 pytest tests, with new tests covering the heuristic fallback chain (Quick-with-final-header, last-blockquote fallback, alternate-header recognition, empty-on-banners-only).

**Why:** The initial baseline run was honest evidence that the eval infrastructure had measurement bugs in three places: the seeder produced too-broad expected_changes, the parser conflated commentary with rewrite, and one runner was missing dimensions from its threshold check. Fixing them as a coherent polish pass before the v3.4.0 tag means the tag points at numbers worth interpreting. The v3.4.0 tag is deferred until a fresh baseline run (post-session-reset) replaces the stale numbers; the procedure is documented step-by-step in `evals/reports/summary_latest_en.md`.

### 4.8 v3.4.0 — `regex_scorer.py` (contributed by Asaf Lecht)

**What:** Added `evals/scripts/regex_scorer.py` — a deterministic regex-based AI-tell scorer that counts high-confidence Tier-1 patterns and reports density per 100 words, per-paragraph breakdown, sentence-rhythm coefficient of variation, and (in `--compare` mode) length delta + pattern regressions between input and rewrite. No API calls; stdlib only; runs as `python -m evals.scripts.regex_scorer`. Twenty-seven new pytest cases cover the catalogue, helpers, scoring, and compare-mode logic (64 tests total).

**How:** Contributed by [Asaf Lecht](https://github.com/Seithx); integrated at "medium" level per the integration plan — original `PATTERNS` dict refactored into `PATTERNS_EN` + a `PATTERNS_BY_LANG` registry; `scan` / `score_text` / `compare` / formatters / CLI all take a `lang` kwarg with `--lang en` as default and `choices=sorted(PATTERNS_BY_LANG)` so unknown languages fail fast at argparse. The Hebrew-skip path generalized into "skip language-specific patterns when the paragraph's script does not match the active language pack" (universal mechanics — em-dash, boldface, emoji — still counted). Windows-specific docstring (`py score.py`) replaced with the `python -m` form used by the rest of the eval scripts.

**Why:** The LLM-based `run_pattern_eval.py` answers "did the skill behaviorally remove this pattern from this case?" — a noisier, more expensive question that needs the model. The regex scorer answers "how many high-confidence AI tells survive in this text?" — a deterministic, fast, offline question. They complement each other: regex scorer gives a sub-second density read on any text; LLM pattern eval gives a per-case detection rate against curated before/after pairs. The language registry is the Phase-2-friendly bit: when DE patterns get curated, they plug in as `PATTERNS_DE` + one line in the registry — no refactor of the surrounding scoring + comparison + CLI code.

Author's design note (preserved in source): regexes are conservative; false negatives are preferred over false positives. For the humanizer eval use case that is the right tradeoff — the skill does not get full credit for a clean rewrite (false negative) rather than getting penalized for legitimate prose (false positive). Threshold values (`boldface_overuse > 0.5/100w`, `rule_of_three > 1.5/100w`) are heuristic and should be re-validated against the human-sample corpus over time.

Wiring `regex_scorer` as a fast first-pass that `run_pattern_eval.py` calls before deciding which cases need LLM-level scoring is the "big" integration path; deferred until after Phase 2 so the per-language pattern-pack abstraction is in place first.

## 5. In planning — v3.5.0 Phase 2 (German language pack)

Phases 0 and 1 of the v3.5.0 design are shipped (§4.5, §4.6, §4.7). Phase 2 — the first non-English language pack (German) — is the remaining piece.

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

### 5.4 Build order — status

1. **Phase 0 — Refactor (EN only, behavior-preserving). SHIPPED as v3.3.0** — see §4.5.
2. **Phase 1 — Eval infrastructure (EN). SHIPPED as v3.4.0 (commits merged, tag pending fresh baseline)** — see §4.6, §4.7.
3. **Phase 2 — DE language pack. PENDING.** `mine_patterns.py` → DE candidates from generated AI corpus vs. Wikipedia pre-2022 + Gutenberg. Manual curation → `patterns/de.md`. `domains/de_overrides.md` from DE register knowledge. `evals/corpus/de/`. Iterate until pattern-eval ≥ 0.85, false-positive ≤ 0.10, e2e ≥ EN baseline. Ships as v3.5.0.
4. **Phase 3 — Polish & release. PENDING.** README updates, `evals/README.md` polish (already partly in place), optional CI workflow, v3.5.0 release.

### 5.5 Pre-v3.4.0-tag work (gating the tag, not a separate release)

The v3.4.0 commits are merged to `main` and pushed to `origin`. The tag is intentionally held until a fresh baseline replaces the stale numbers documented in `evals/reports/summary_latest_en.md`. Procedure:

1. After the claude CLI subscription session resets (target: 21:00 Europe/Berlin), re-symlink the install to point at the current `main` checkout (the previous symlinks pointed at since-removed worktrees).
2. Re-run pattern eval (subscription only, ~25 min wall, 40 patterns × ~46 cases).
3. Re-run FP eval (subscription only, ~5 min wall, 5 cases).
4. Run E2E in batches via `--cases` flag (needs `ANTHROPIC_API_KEY`); 2 cases per session × 2–3 sessions to fit the Pro plan.
5. `--aggregate-only` to combine cached partials into the fresh summary.
6. Replace "STALE" banner with "DEFENSIBLE" + the fresh numbers; commit; tag v3.4.0; push tag.

Full command sequence is in `evals/reports/summary_latest_en.md` under "Re-baseline procedure".

### 5.6 Phase 2 open questions

- API budget for mining corpus generation. Need ~500–1000 DE AI texts across five domains via Claude/GPT/Gemini APIs.
- Tagesschau archive / DE news corpus licensing for the human-side of mining (likely fallback: Wikipedia revisions pre-2022 only, which is CC-BY-SA).
- Whether to add a `--audit-only` mode (detect + report without rewriting) as part of v3.5.0 or punt to a later minor release.
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
