# humanizer-ext eval infrastructure

Three LLM-based eval types target the humanizer skill from different angles:

- **`run_pattern_eval.py`** — detection rate per pattern (LLM-based, runs against curated before/after pairs)
- **`run_false_positive_eval.py`** — edit distance ratio on human-written texts (catches over-editing)
- **`run_e2e_eval.py`** — judge-LLM scored rewrite quality on whole AI documents (expensive, holistic)

Plus one deterministic regex-based scorer:

- **`regex_scorer.py`** — counts high-confidence Tier-1 AI-writing patterns by regex; reports per-100w density, per-paragraph breakdown, sentence-rhythm CV, and (`--compare` mode) length delta + pattern regressions between input and rewrite. No API calls. Useful standalone for quick offline scoring, and as a deterministic complement to the LLM-based pattern eval. Pack registry: `PATTERNS_BY_LANG` in the source — `--lang en` available now; DE pack will land with Phase 2 of the v3.5.0 design.

Reports land in `evals/reports/` as paired JSON + Markdown. Personal-mode reports (`evals/reports/*_personal_*`) and per-case partials (`evals/reports/_partial/`) are gitignored.

## Prerequisites

Eval scripts call the `claude` CLI to invoke the skill. The CLI loads whatever humanizer skill is installed at `~/.claude/skills/humanizer/`. Before running an eval against the repo's current SKILL.md, point the install at the repo:

```bash
# From the humanizer-ext repo root
ln -sfn "$PWD/SKILL.md" ~/.claude/skills/humanizer/SKILL.md
mkdir -p ~/.claude/skills/humanizer/patterns ~/.claude/skills/humanizer/domains
ln -sfn "$PWD/patterns/_universal.md" ~/.claude/skills/humanizer/patterns/_universal.md
ln -sfn "$PWD/patterns/en.md" ~/.claude/skills/humanizer/patterns/en.md
ln -sfn "$PWD/domains/en_overrides.md" ~/.claude/skills/humanizer/domains/en_overrides.md
```

The eval `_shared.py` exposes `verify_skill_install()` which is called at the start of every runner. If the installed SKILL.md bytes differ from the repo's SKILL.md, the run aborts with a clear error before any API calls.

## Install dependencies

```bash
pip install '.[evals]'   # or: pip install anthropic rapidfuzz
```

Set `ANTHROPIC_API_KEY` in your environment for `run_e2e_eval.py`'s judge calls.

## Running the evals

```bash
# Pattern detection (all patterns)
python evals/scripts/run_pattern_eval.py --lang en --model sonnet

# Pattern detection (single pattern)
python evals/scripts/run_pattern_eval.py --lang en --pattern 7

# False-positive rate (synthetic corpus)
python evals/scripts/run_false_positive_eval.py --lang en --corpus synthetic

# E2E rewrite quality (3 runs per case, Sonnet judge)
python evals/scripts/run_e2e_eval.py --lang en --runs 3 --judge-model sonnet

# E2E with Opus judge (more expensive, more discriminating)
python evals/scripts/run_e2e_eval.py --lang en --judge-model opus

# Regex scorer (deterministic, no API)
python -m evals.scripts.regex_scorer text.txt
python -m evals.scripts.regex_scorer --compare input.txt rewrite.txt
python -m evals.scripts.regex_scorer text.txt --json --lang en
```

### Splitting E2E across multiple Pro plan sessions

The E2E runner is idempotent. Each case's score is cached to `evals/reports/_partial/e2e_<lang>_<case_id>.json` as soon as it lands. Re-running skips cases that already have a partial. Use this when the Claude Pro subscription session limit cannot cover all cases at once (5 cases × 3 runs ≈ 15 skill calls per language).

```bash
# Session 1 — run two cases
python evals/scripts/run_e2e_eval.py --lang en --cases e2e_en_casual_01,e2e_en_academic_01

# Session 2 — run two more
python evals/scripts/run_e2e_eval.py --lang en --cases e2e_en_legal_01,e2e_en_technical_01

# Session 3 — run last
python evals/scripts/run_e2e_eval.py --lang en --cases e2e_en_marketing_01

# Aggregate all cached partials into the final summary (no API calls)
python evals/scripts/run_e2e_eval.py --lang en --aggregate-only
```

`--force` re-scores a case even if a partial exists (use when corpus changes). Partials are gitignored — they are user-session artifacts, not canonical records. The aggregated `summary_latest_en.{json,md}` is the committed baseline.

## Adding a new language pack (validated against the DE pack, v3.5.0)

1. **Phase A — Wiki seed (if available)** — check whether the target Wikipedia community maintains an "Anzeichen für KI-generierte Inhalte" / "Identifier l'usage d'une IA générative" equivalent.
2. **Phase B — Empirical mining** — assemble an AI corpus + human corpus (per-domain real sources beat synthesis; pre-2022 / clear-license for AI-contamination safety), run `mine_patterns.py` to extract candidate tells via log-likelihood divergence.
3. **Phase C — Manual curation** — write `patterns/<lang>.md` and `domains/<lang>_overrides.md`. Translate the universal/EN patterns with native examples; put **language-only tells at IDs #100+** (DE used #100–104; FR would use #200+, ES #300+, … — keep this convention so packs never collide). Adapt every domain override to the target register (e.g. DE academic is more passive-heavy; DACH career rewards understatement, the opposite of US/UK).
4. **Register the deterministic scorer** — add `regex_scorer.PATTERNS_<LANG>` and register it in `PATTERNS_BY_LANG`. Reuse the universal-mechanics keys (`em_dash_overuse`, `boldface_overuse`, `emoji_bullet`) **by reference** so they can't drift from EN.
5. **Build eval corpus** — `evals/corpus/<lang>/{patterns,human,e2e}/` parallel to EN. Pattern cases: aim for **≥3 cases/pattern** (single-case-per-pattern is too noisy — a stable rate needs the redundancy); every `expected_changes` entry MUST be a verbatim substring of its `input`; keep inputs at realistic fluff density (a ~50%-fluff input is an unwinnable strawman for the length-anchored E2E judge). The FP human corpus reader walks nested source dirs and reads `metadata.domain` frontmatter; trim human samples to ~200–350 words so the skill stays under the CLI timeout.
6. **Install the packs so `claude -p` can load them** — the runtime reads `patterns/<lang>.md` + `domains/<lang>_overrides.md` from the *installed* skill dir. Symlink (or copy) the new packs into `~/.claude/skills/humanizer/{patterns,domains}/`, and add them to `_PACK_FILES` in `evals/scripts/_shared.py` so `verify_skill_install` fails on a stale/missing pack instead of silently running zero patterns.
7. **Run + iterate** — `--lang <lang>` on each runner (`run_pattern_eval`, `run_false_positive_eval`, `run_e2e_eval`); runs are resumable across session limits via per-case partials. Targets (relaxed for a first language vs EN's mature 0.85):
   - Pattern detection: **≥ 0.70** overall (force-full method measures detection, not pre-flight routing)
   - False-positive: **≤ 0.15** mean edit ratio on human samples
   - E2E: per-case **meaning ≥ 8.0** (+ human-ness ≥ 7.5, length ≥ 7.0); run ≥5 and report the **median** — judge scores are noisy at n=3.

## Personal-mode false-positive testing

To test the skill against your own writing without committing it:

```bash
export HUMANIZER_SAMPLES_DIR=~/.claude/humanizer-samples
python evals/scripts/run_false_positive_eval.py --corpus personal
```

Personal-mode reports go to `evals/reports/*_personal_*.json` (gitignored).
