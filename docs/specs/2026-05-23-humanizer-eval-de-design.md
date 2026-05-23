# Design: Multi-lingual architecture + evaluation infrastructure (v3.5.0)

**Status:** Draft — under maintainer review
**Date:** 2026-05-23
**Final release:** humanizer-ext v3.5.0 (with intermediate shippable releases v3.3.0 + v3.4.0 — see §6)
**Scope at v3.5.0:** EN + DE shipped. Architecture is multi-lingual (FR / ES / IT / further packs add via the documented recipe without skill changes).
**Authors:** Christian Huhn (`duathron`) with Claude (Opus 4.7)

## 1. Overview

This spec covers a single coordinated change to `humanizer-ext`: refactor the monolithic `SKILL.md` into a layered framework + language packs, then add the first non-English pack (German) and a three-tier evaluation infrastructure that exercises both the existing English skill and the new German skill.

The skill ends up *multi-lingual* by architecture — the framework supports arbitrarily many language packs and the eval recipe is reusable — but ships v3.5.0 *bilingual* in practice (EN + DE). Further packs (FR / ES / IT) ride on the same architecture without further skill changes; they are out of scope for this release (see §3 non-goals).

The two pieces are coupled by design. The eval infrastructure is needed regardless of language support — pattern changes today are made by hand without any regression safety net. The multi-lingual layering is needed because adding a second language to the current monolithic SKILL.md would double the file size and make upstream sync intractable. Doing both in one design lets the German pack be the first user of the eval infrastructure, which proves the infrastructure works on a non-trivial case.

## 2. Goals

1. **Refactor SKILL.md into a framework + language packs without changing observable English behavior.** Existing users notice no difference in skill output.
2. **Add full German support.** Input detection, pattern application, output — fully German-aware. A user can pass a German blog draft and get a German rewrite that respects German register and avoids German-specific AI tells.
3. **Ship an evaluation harness with three eval types:** pattern detection (does the skill fire the right pattern on a known case), false-positive rate (does the skill leave human-written text mostly alone), end-to-end rewrite quality (does a judge LLM rate the rewrite as more human than the input).
4. **Make adding further languages a documented recipe.** Phase A (Wiki seed if available) → Phase B (empirical mining) → Phase C (manual curation) → Phase D (cross-reference). The eval scripts must be language-agnostic.
5. **Keep personal user data out of the repo.** Voice-calibration samples and personal false-positive testing materials live outside the repo, under a documented user-level convention.

## 3. Non-goals

- **Detection-only / audit-only mode.** May be added in v4.1; not part of this design.
- **A web UI or dashboard for eval reports.** JSON + markdown reports written to disk are sufficient.
- **CI integration.** Optional CI workflow may be drafted but is not required for v3.5.0 release.
- **Languages beyond German.** FR, ES, IT, JP are explicitly out of scope for v3.5.0. The architecture must support them; building them does not happen in this release.
- **Replacing the upstream pattern numbering scheme.** Pattern IDs stay stable; DE-only patterns start at #100 to avoid collisions.
- **Reimplementing voice calibration.** The current voice-calibration step works language-agnostically and is preserved as-is.

## 4. Architecture

### 4.1 Layered skill structure

The current `SKILL.md` (~60 KB, 40 patterns inline) splits into:

- **`SKILL.md`** — framework only (~15–20 KB). Mode selector, language detection, domain detection, density preflight, voice-calibration lookup, final audit checklist (universal items only), output format template, instructions to load the relevant pattern + override files.
- **`patterns/_universal.md`** — language-agnostic patterns: #14 em dash, #15 boldface, #17 title case, #18 emojis, #19 curly quotes, #26 hyphenation, #38 reference-markup artifacts, #39 phrasal templates, #40 markdown contamination, structural patterns #6 (challenges section), #25 (conclusion section), #29 (fragmented headers).
- **`patterns/{lang}.md`** — language-specific patterns. Pattern IDs stay continuous across languages; DE-only patterns start at #100. Schema per pattern: `### N. <Name>` → `**Trigger:**` → `**Before:**` → `**After:**` → `**Domain notes:**`.
- **`domains/{lang}_overrides.md`** — per-language domain override matrix. Replaces the inline matrix in current SKILL.md.

The Phase 0 refactor extracts the current SKILL.md content into these files byte-equivalent, with no semantic change. Regression tests confirm identical output before the German work starts.

### 4.2 Runtime flow

```
user invokes /humanizer + text
  │
  ▼
SKILL.md (framework)
  │
  ├─ 1. detect mode (Quick / Full / Voice)
  ├─ 2. detect input language → instruct: Read patterns/{lang}.md + domains/{lang}_overrides.md
  ├─ 3. always Read patterns/_universal.md
  ├─ 4. detect domain (casual / academic / legal / technical / marketing)
  ├─ 5. voice-calibration lookup (4-step convention, §4.4)
  ├─ 6. Tier-1 density preflight (sprach-agnostisch)
  ├─ 7. apply patterns respecting domain overrides
  ├─ 8. length audit
  ├─ 9. final audit checklist
  └─ 10. output
```

### 4.3 Pattern-ID continuity

Pattern numbers identify *what is being flagged*, not *what string to match*. Pattern #7 is "AI vocabulary" in every language; the trigger list differs. A user reading the final audit findings sees `Pattern #7 fired: 'darüber hinaus', 'unterstreicht'` and the meaning is consistent.

DE-only patterns (no EN equivalent) start at #100: #100 Anglizismen-Leakage, #101 Nominalstil-Inflation, #102 Konjunktiv-Stack, etc. The exact set is determined during Phase 2 curation.

### 4.4 Personal samples convention (privacy)

Voice-calibration samples and personal false-positive testing materials are never committed to the repo. The skill (and personal-mode eval runner) look in this order:

1. `--samples-dir <path>` (CLI override, both skill and eval runner)
2. `$HUMANIZER_SAMPLES_DIR` (env override)
3. `~/.claude/humanizer-samples/` (user-global default — flat directory)
4. `./writing-samples/` (per-project override — flat directory)

Within whichever directory is resolved:

- If any subfolder named after a known language code (e.g., `de/`, `en/`, `fr/`) exists, the directory is treated as multi-language. Use the subfolder matching the detected input language. Files at the root are ignored *except* `shared.md`.
- If no language-named subfolder exists, the directory is treated as flat (single-language) — all files at the root are used regardless of detected input language.
- A file named `shared.md` at the root of the resolved directory is always included in addition to whatever was selected above.
- If multi-language mode is detected and no subfolder matches the input language, voice calibration is skipped (with an inline warning: "Found samples directory in multi-language mode but no `<lang>/` subfolder — skipping voice calibration").

This means a single-language user only needs one flat folder. A multi-language user opts into the multi-language layout by creating any language-named subfolder.

### 4.5 Eval infrastructure layout

```
evals/
├── corpus/
│   ├── en/
│   │   ├── patterns/           # before/after pairs per pattern (one JSON per pattern)
│   │   ├── human/
│   │   │   ├── public_domain/  # Gutenberg pre-1923, Wikipedia revisions pre-2022
│   │   │   ├── synthetic/      # hand-written for eval, MIT, anonymized
│   │   │   └── contributed/    # PR opt-in with contributor agreement
│   │   └── e2e/                # whole-document AI samples (+ optional reference rewrites)
│   └── de/                     # same structure as en/
├── scripts/
│   ├── _shared.py              # claude CLI wrapper, JSON parsing, corpus loader, retry
│   ├── run_pattern_eval.py     # eval type 1: detection rate per pattern
│   ├── run_false_positive_eval.py  # eval type 2: edit ratio + false fires on human texts
│   ├── run_e2e_eval.py         # eval type 3: judge-LLM rates rewrite quality
│   ├── mine_patterns.py        # TF-IDF / log-likelihood miner for new language packs
│   └── judge_prompt.md         # judge-LLM rubric
├── reports/                    # JSON + markdown; gitignored except latest summary
└── README.md                   # how to add a language pack; how to run evals
```

### 4.6 Eval types

**Type 1 — Pattern detection (unit-style, cheap, deterministic):**
Per pattern ID, run a set of curated input cases through the skill. Check that (a) `patterns_fired` includes the expected pattern, and (b) the rewrite removes the trigger string. Metric: `detection_rate = correct_fires / total_cases`. Threshold: ≥ 0.85 per pattern.

**Type 2 — False-positive rate (medium cost, narrow target):**
Per human-written text, run the skill and measure edit-distance ratio + which patterns falsely fired. Also verify the Tier-1 density preflight correctly drops to Quick mode on human input. Thresholds: edit ratio ≤ 0.10 on human texts, density preflight correctly classifies ≥ 0.90 of cases.

**Type 3 — End-to-end rewrite quality (expensive, holistic):**
Per AI-generated whole-document input, run the skill, then ask a judge LLM to score the rewrite on (a) human-ness 1–10, (b) meaning preservation 1–10, (c) length appropriateness 1–10. To capture both kinds of variance, each case is run end-to-end 3× (skill-rewrite + judge-score together) — this surfaces variance from the skill's own sampling as well as from judge noise. Default judge model: Sonnet 4.6. Opus 4.7 opt-in via `--judge-model claude-opus-4-7`. Thresholds apply to the mean across the 3 runs: mean human-ness ≥ 7.5, mean meaning ≥ 9, mean length within ±15% of input. Stddev is reported alongside but does not gate.

### 4.7 Pattern-source strategy per language

Four-phase recipe, reused for every new language pack:

- **Phase A — Wiki seed (if available).** EN: [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). DE: [Anzeichen für KI-generierte Inhalte](https://de.wikipedia.org/wiki/Wikipedia:Anzeichen_f%C3%BCr_KI-generierte_Inhalte). FR: [Aide:Identifier l'usage d'une IA générative](https://fr.wikipedia.org/wiki/Aide:Identifier_l'usage_d'une_IA_g%C3%A9n%C3%A9rative). ES + IT: no equivalent dedicated guide found, skip to Phase B.
- **Phase B — Empirical mining.** Generate ~500–1000 AI texts in the target language via API across all 5 domains. Assemble a human corpus (Wikipedia revisions pre-2022 + public-domain literature). Run `mine_patterns.py` with TF-IDF / log-likelihood-ratio scoring to surface top divergent tokens / bigrams / trigrams.
- **Phase C — Manual curation.** Review candidates linguist-style. Filter false positives (technical terms, domain vocabulary). Cluster by era (which words are GPT-4 era vs. GPT-4o vs. GPT-5). Decide domain applicability.
- **Phase D — Cross-reference.** Existing NLP papers on AI detection in the target language, public AI-detection tools' indicator lists, community PR feedback after release.

## 5. Components

### 5.1 Skill layer

| File | Responsibility | Size target |
|------|----------------|-------------|
| `SKILL.md` | Framework orchestration: modes, lang/domain detection, pipeline order, output format, audit checklist universal items, voice-calibration lookup logic | ~15–20 KB |
| `patterns/_universal.md` | Language-agnostic patterns with full before/after | ~10 KB |
| `patterns/en.md` | EN-specific pattern subset (Phase 0 byte-equivalent extraction from current SKILL.md) | ~25 KB |
| `patterns/de.md` | DE-specific pattern subset including DE-only #100+ patterns | ~20 KB |
| `domains/en_overrides.md` | EN domain × pattern override matrix extracted from current SKILL.md | ~3 KB |
| `domains/de_overrides.md` | DE domain × pattern override matrix, including #100+ | ~3 KB |

SKILL.md frontmatter `description` stays ≤ 1024 chars to fit Claude Code's plugin frontmatter limit.

### 5.2 Eval layer

| File | Responsibility |
|------|----------------|
| `evals/scripts/_shared.py` | `run_skill(text, *, lang, mode, domain, samples_dir, model, timeout) -> dict`. `parse_skill_output(stdout) -> dict`. `load_corpus(lang, kind) -> list[Case]`. `Case` dataclass (`id, input, expected_changes, expected_unchanged, metadata`). `retry_with_backoff`. `write_report(name, data)`. |
| `evals/scripts/run_pattern_eval.py` | CLI: `--lang`, `--pattern <id>` (optional, default all), `--model`. Per case, run skill, check expected pattern fired + trigger removed. Output per-pattern detection rate + miss examples. Exit non-zero if any pattern < threshold. |
| `evals/scripts/run_false_positive_eval.py` | CLI: `--lang`, `--corpus {public_domain,synthetic,contributed,personal}`, `--model`. Per text, run skill, measure edit ratio + false-fire count + density preflight classification. `--personal` flag uses the personal-samples lookup chain; reports go to `evals/reports/personal_*` (gitignored). |
| `evals/scripts/run_e2e_eval.py` | CLI: `--lang`, `--judge-model`, `--domain <name>` (optional). Per AI text, run skill, then judge-LLM scores rewrite on 3 dimensions. Run 3× for variance. Mean + stddev per domain. |
| `evals/scripts/mine_patterns.py` | CLI: `--ai-corpus <dir>`, `--human-corpus <dir>`, `--lang`, `--top-n 50`, `--ngram-range 1,3`. TF-IDF vectorize both corpora; log-likelihood ratio per token/bigram/trigram; filter by stopword list + min frequency; output CSV `term, ll_ratio, ai_freq, human_freq, sample_contexts`. |
| `evals/scripts/judge_prompt.md` | Strict rubric used by `run_e2e_eval.py`. |

### 5.3 Corpus schemas

**`evals/corpus/{lang}/patterns/<id>.json`:**

```json
{
  "pattern_id": 7,
  "pattern_name": "AI vocabulary",
  "lang": "de",
  "cases": [
    {
      "id": "pattern_7_de_001",
      "input": "Darüber hinaus unterstreicht ...",
      "expected_changes": ["unterstreicht", "darüber hinaus"],
      "expected_unchanged": [],
      "domain": "casual",
      "source": "manual_curation"
    }
  ]
}
```

Minimum 5–10 cases per pattern. AI-generated stress-test cases added from Phase B mining output.

**`evals/corpus/{lang}/human/<subdir>/<file>`:**

Plain text or markdown. Sidecar files:

- `_LICENSE` (per file or per subdirectory) — license identifier.
- `_SOURCE` (per file or per subdirectory) — provenance URL or description.
- Synthetic files: YAML frontmatter `lang`, `domain`, `notes`.
- Contributed files: paired `<file>.contributor.txt` with contributor agreement.

**`evals/corpus/{lang}/e2e/<file>.json`:**

```json
{
  "id": "e2e_de_blog_001",
  "lang": "de",
  "domain": "casual",
  "input": "...full AI-generated blog post...",
  "reference_rewrite": "...optional gold-standard human rewrite...",
  "source": "generated_by: gpt-4o, prompt: ..."
}
```

### 5.4 Tooling layer

| File | Responsibility |
|------|----------------|
| `tests/test_skill_structure.py` | pytest sanity tests — no API calls. SKILL.md frontmatter is valid YAML with description ≤ 1024 chars. All `patterns/*.md` files have schema-compliant sections. All pattern IDs referenced in `domains/{lang}_overrides.md` exist in matching `patterns/{lang}.md` or `patterns/_universal.md`. Corpus JSON schema is valid. No orphan pattern files. |
| `.gitignore` additions | `evals/reports/personal_*`, `evals/reports/*_latest_personal*`, `writing-samples/`, `.venv/`, `__pycache__/`. |
| `README.md` updates | Multi-lingual architecture (EN + DE shipped) + eval-infra mention in "What's different" table. Voice-samples convention in quickstart. Eval-runner usage examples. Pointer to `evals/README.md` for contributor recipes. |
| `evals/README.md` | How to add a new language pack (5-step recipe). How to add personal samples. Threshold rationale. Optional CI integration hints. |

## 6. Build phases

### Phase 0 — Refactor (EN only, behavior-preserving)

Split SKILL.md into `SKILL.md` (framework) + `patterns/_universal.md` + `patterns/en.md` + `domains/en_overrides.md`. Add `tests/test_skill_structure.py`. Regression test: run the existing skill examples through the refactored skill and confirm output is identical. No semantic change.

Deliverables: 4 files split + 1 test file + green regression. Ships as v3.3.0 (refactor-only).

### Phase 1 — Eval infrastructure (EN baseline)

Build `evals/scripts/_shared.py` first, then the three runners. Seed `evals/corpus/en/patterns/` from the before/after examples already in `patterns/en.md`. Add 5–10 synthetic human samples to `evals/corpus/en/human/synthetic/` covering all 5 domains. Add 5–10 AI samples to `evals/corpus/en/e2e/` likewise.

Deliverables: working eval runners, EN baseline report committed to `evals/reports/`. Ships as v3.4.0 (eval-infra, EN only).

### Phase 2 — DE language pack

Run `mine_patterns.py` against a generated DE AI corpus + DE human corpus (Wikipedia DE revisions pre-2022 + public-domain DE literature). Curate `patterns/de.md` from the DE Wikipedia seed + mining candidates + DE-only patterns (#100+). Build `domains/de_overrides.md` from DE register knowledge. Build `evals/corpus/de/` parallel to `en/`. Iterate on patterns and overrides until: pattern detection ≥ 0.85, false-positive ≤ 0.10, e2e quality ≥ EN baseline.

Deliverables: `patterns/de.md`, `domains/de_overrides.md`, full DE corpus, passing DE eval reports. Ships as v3.5.0 (EN + DE release on the multi-lingual architecture).

### Phase 3 — Polish & release

README updates, `evals/README.md` finalization, optional GitHub Actions CI workflow draft, v3.5.0 changelog and release notes, marketplace metadata refresh.

## 7. Success criteria

- **Refactor (Phase 0):** zero observable EN behavior change. Regression test green.
- **Eval infra (Phase 1):** all three eval runners produce reports on EN corpus. EN pattern detection rate published as baseline (target ≥ 0.85 per pattern but baseline can be lower if it surfaces real gaps).
- **DE pack (Phase 2):** DE pattern detection ≥ 0.85, false-positive rate ≤ 0.10, e2e quality mean ≥ 7.5 with stddev reported. DE Wiki seed coverage documented (which Wiki patterns we adopted, which we skipped and why).
- **Recipe reusability:** the `evals/README.md` recipe for adding a new language is concrete enough that a contributor could start a third language pack (e.g., FR) from it without reading the rest of the docs.
- **Privacy:** no personal writing samples in the repo. `git log -p -- evals/corpus/` shows only public-domain, synthetic, or contributed-with-agreement content.

## 8. Implementation model

The spec is authored by Opus 4.7. Implementation will be delegated to caveman-style subagents running Sonnet 4.6:

- `cavecrew-investigator` (Sonnet) — pre-refactor mapping and post-change verification.
- `cavecrew-builder` (Sonnet) — atomic ≤2-file edits. The implementation plan (produced after this spec is approved) breaks the work into tasks small enough to respect this limit.
- `cavecrew-reviewer` (Sonnet) — per-chunk review before merge.

The Opus parent thread orchestrates spawns, validates output, and handles linguistic judgment calls during pattern curation. Each subagent returns caveman-compressed output to preserve main context budget.

## 9. Open questions

- **API budget for Phase 2 corpus mining.** Generating ~500–1000 DE AI texts across 5 domains via multiple model families (Claude / GPT / Gemini) needs a budget cap. Estimate ≈ $10–30 depending on model mix and output lengths. Decide before Phase 2 starts.
- **DE human corpus license.** Tagesschau archive looks tempting but licensing is unclear. Default fallback: Wikipedia DE revisions pre-2022 (CC-BY-SA) + Project Gutenberg DE pre-1923. Confirm fallback is sufficient or pursue Tagesschau permission.
- **Pattern coverage gap between EN (40) and DE (~30 seeded + mining).** Acceptable as long as universal patterns close the gap and EN IDs without DE equivalents are documented in `patterns/de.md` as "no DE equivalent — universal patterns and EN context apply if mixing languages".
- **`--audit-only` mode** (detect + report without rewriting) — punted to v4.1 unless trivially cheap to add during Phase 0.
- **CI workflow** — optional draft in Phase 3 or punt to v4.1.

## 10. Risks

- **Refactor introduces hidden behavior change.** Mitigated by the Phase 0 regression test requirement.
- **DE pattern curation drifts into subjective territory.** Mitigated by Phase A (Wiki seed) and Phase B (empirical mining) producing a defensible candidate list before manual curation.
- **Judge-LLM scoring is noisy.** Mitigated by 3× sampling per case + variance reporting + threshold based on mean+stddev, not single scores.
- **Personal-samples convention confuses users.** Mitigated by clear `evals/README.md` documentation and skill-side warnings when sample directories are detected with content language mismatching the input.
- **Plugin frontmatter description limit (1024 chars).** SKILL.md is shrinking, not growing, so this risk is lower than at v3.2.0. Verified in `tests/test_skill_structure.py`.

## 11. References

- [Wikipedia:Signs of AI writing (EN)](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- [Wikipedia:Anzeichen für KI-generierte Inhalte (DE)](https://de.wikipedia.org/wiki/Wikipedia:Anzeichen_f%C3%BCr_KI-generierte_Inhalte)
- [Aide:Identifier l'usage d'une IA générative (FR)](https://fr.wikipedia.org/wiki/Aide:Identifier_l'usage_d'une_IA_g%C3%A9n%C3%A9rative)
- [Wikipedia:WikiProject AI Cleanup](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup)
- Upstream: [blader/humanizer](https://github.com/blader/humanizer)
- skill-creator eval runner (Python + claude CLI pattern reference): `~/.claude/plugins/cache/claude-plugins-official/skill-creator/.../scripts/run_eval.py`
- Project history (this fork): `docs/PROJECT_HISTORY.md`
