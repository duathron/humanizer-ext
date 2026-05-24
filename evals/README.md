# humanizer-ext eval infrastructure

Three eval types target the humanizer skill from different angles:

- **`run_pattern_eval.py`** — detection rate per pattern (cheap, deterministic-ish, runs against curated before/after pairs)
- **`run_false_positive_eval.py`** — edit distance ratio on human-written texts (catches over-editing)
- **`run_e2e_eval.py`** — judge-LLM scored rewrite quality on whole AI documents (expensive, holistic)

Reports land in `evals/reports/` as paired JSON + Markdown. Personal-mode reports (`evals/reports/*_personal_*`) are gitignored.

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
```

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
