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

## Adding a new language pack (per the v3.5.0 spec)

1. **Phase A — Wiki seed (if available)** — check whether the target Wikipedia community maintains an "Anzeichen für KI-generierte Inhalte" / "Identifier l'usage d'une IA générative" equivalent.
2. **Phase B — Empirical mining** — generate an AI corpus + human corpus, run `mine_patterns.py` (Phase 2 deliverable) to extract candidate AI tells via log-likelihood divergence.
3. **Phase C — Manual curation** — review candidates, write `patterns/<lang>.md` and `domains/<lang>_overrides.md`.
4. **Phase D — Cross-reference** — public NLP papers, AI-detection tool indicator lists, community PRs after first release.
5. **Build eval corpus** — `evals/corpus/<lang>/{patterns,human,e2e}/` parallel to the EN structure.
6. **Iterate** — run all three evals against the new pack until thresholds pass:
   - Pattern detection: ≥ 0.85 per pattern
   - False-positive rate: ≤ 0.10 mean edit ratio on human samples
   - E2E quality: human-ness mean ≥ 7.5, meaning ≥ 9, length within ±15%

## Personal-mode false-positive testing

To test the skill against your own writing without committing it:

```bash
export HUMANIZER_SAMPLES_DIR=~/.claude/humanizer-samples
python evals/scripts/run_false_positive_eval.py --corpus personal
```

Personal-mode reports go to `evals/reports/*_personal_*.json` (gitignored).
