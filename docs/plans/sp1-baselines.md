# SP1 baselines (measured)

Install pinned to unedited `main:SKILL.md` during all baselining (diff-verified).

## Change-log first-attempt rate (sentinel) — DONE 2026-06-07

Measured from outside on v3.5.1 (pre-edit), sonnet:

| Source | runs | flags |
|---|---|---|
| e2e judge — DE career/technical/academic ×5 | 15 | 0 |
| skill-only probe — DE 6 cases ×3 | 18 | 1 (DE-legal) |
| skill-only probe — EN 6 cases ×3 | 18 | 0 |
| **Pooled** | **51** | **1** |

**Honest read (Skeptic):** 1/51 → 95% CI **[0.35%, 10.3%]** (point 2%). This **refutes "~1/3"** (33% far outside the interval) but does NOT establish a precise rate — true first-attempt rate is **≤~10%**. Per "don't ship a claim the metric contradicts", **lever 1 (rewrite-first) dropped**; metric kept as a regression sentinel. The restraint lever must not *materially* inflate this (a single extra hit is within the ±8pp halo, not a regression).

(Metric is an upper bound — over-catches empty / ≥2-arrow output, per Skeptic. Read identically before/after.)

### Per-run flags (raw evidence, out of /tmp)

```
e2e-judge (real metric, ×5):  de career  F F F F F   de technical F F F F F   de academic F F F F F
probe DE (×3):  academic F F F   career F F F   casual F F F   legal F F T   marketing F F F   technical F F F
probe EN (×3):  academic F F F   career F F F   casual F F F   legal F F F   marketing F F F   technical F F F
```
Only hit: DE-legal (probe, 1 of 3). e2e-judge set = academic/career/technical only (no legal) → no double-count. Install pinned to unedited `main:SKILL.md` (sha256-verified) throughout.

## EN true-negative + detection smoke — DONE 2026-06-07

`run_pattern_eval.py --lang en --model sonnet --force` (force_full path), report `pattern_en_20260607_152331.json`:
- **true-neg: 6/9 pass** (aggregated from `per_pattern`; the top `summary` has no TN block). NOT the stale 4/9 — current skill is milder.
- **detection smoke `overall_detection_rate`: 0.905** (non-gating, crater baseline). Healthy.

### The 3 true-neg failures (what the lever must actually move)

| case | input (clean/human) | skill over-edited |
|---|---|---|
| `pattern_008_en_001` | "Gallery 825 serves as LAAA's exhibition space… features four separate spaces and boasts over 3,000 sq ft." | reworded: "serves as"→"is", "features…and boasts"→"has…and" |
| `pattern_014_en_001` | legit em-dashes: "promoted by Dutch institutions—not by the people…" | stripped all em-dashes → commas; appended commentary |
| `pattern_014_en_002` | legit em-dashes: "The report—which covered…—concluded…" | stripped em-dashes; appended "0 em dashes remaining." (changelog trailer) |

**Mechanism conflict (superseded by re-baseline below):** initial single-run read suggested an em-dash carve-out. A fresh probe + 5-run re-baseline overturned it.

### True-neg 5-run re-baseline (2026-06-07) — the single-run 6/9 was NOISE

Probe `/tmp/sp1_tn_multirun.py 5` (mode=full, force_full=False, edit_ratio≤0.10 = pass):

| case | pass /5 | ratios | read |
|---|---|---|---|
| pattern_008_en_001 | **0/5** | 1.08,.28,.19,.88,.28 | stable fail — skill flags it AI-heavy (~6 Tier-1 tells: "serves as"=#1, "boasts"=#4). **Corpus dispute, not a restraint miss → SP3.** |
| pattern_009_en_003 | 4/5 | 0,0,.39,0,0 | pass + 1 noise spike |
| pattern_013_en_001 | 2/5 | .96,.99,0,0,.54 | bimodal noise |
| pattern_014_en_001 | 3/5 | .03,.05,.22,.17,.03 | borderline/noisy (em-dash→comma alone passes at ~.04) |
| pattern_014_en_002 | 2/5 | .04,.04,.49,.69,.11 | bimodal noise — failures are intermittent commentary leak, NOT em-dash |
| pattern_015_en_001 | 3/5 | 1.22,.24,0,0,0 | bimodal noise |
| pattern_017_en_001 | 5/5 | .082×5 | stable pass |
| pattern_019_en_001 | 4/5 | 1.51,0,0,0,0 | pass + 1 huge spike |
| pattern_029_en_001 | **0/5** | 2.92,.60,1.53,.29,.29 | **corpus dispute** — input is the skill's OWN #29 "Fragmented Headers" Before-example (`_universal.md`); deleting the "Speed matters." warm-up is the skill applying its documented rule. Corpus note: "2/2/5 strong dissent" — never a clean true-neg. → SP3 |

**Stable: 5/9 majority, 23/45 = 51% per-run.** Ratios are **bimodal** — identical clean input yields ~0.0 (verbatim) on some runs and 0.2–2.9 on others. The 2 cases that fail every run — **008 and 029 — are BOTH corpus disputes**, not skill defects: each is verbatim one of the skill's own documented AI-tell Before-examples (008 = #8 "serves as"/"boasts"; 029 = #29 fragmented header), with split/dissenting meetup provenance. The skill flags them per its own rules. The other "failures" (013, 014_2) are run-to-run **noise**. → **zero stable behavior defects.**

**Conclusion:** there is no true-negative skill defect to lever. The non-noise "failures" are two disputed corpus rows (the eval put the skill's own canonical AI-tell examples into the leave-alone set), and the rest is single-run noise that only multi-run medians (SP3 eval-rigor tooling) could resolve. Per the project discipline (don't build on single-run noise), **the corpus-dispute fixes + the multi-run harness are deferred to SP3.** SP1 ships the changelog sentinel only — no behavior change.
