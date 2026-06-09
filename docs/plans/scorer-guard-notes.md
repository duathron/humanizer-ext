# Scorer refusal-guard — notes

## What shipped
`is_refusal(text)` (phrase-only, refusal-anchored stubs) in `_shared.py`. In the pattern scorer (`_score_case_once`, both scored + true-neg branches) and the FP scorer (`_score_human_text_once`), a refusal output → `return None` → a `None` run in the SP3a multi-run → excluded by `aggregate_runs` → the case goes `inconclusive` if most runs refuse. A refusal therefore **never** scores `detected=True` (pattern) or as an over-edit (FP/true-neg). No skill change; `force_full` kept. Reports now carry a `"measures"` key (pattern = detection-capability under forced-full; e2e = routing-fidelity).

## Inflation estimate (opportunistic, lower bound — no quota spent)
The refusal-as-detection bug inflated past detection numbers. From the cached `evals/reports/_partial/` previews of the SP3b validation run, **3** stubs scored `detected=True` while being refusals (`pattern_009_en_002/003`, `pattern_013_en_001`). On that sample the headline `overall_detection_rate` corrects by **~0.67pp** (0.898 → 0.891) — a **lower bound**: only run-1 of 5 is cached, so we can't see how many other runs refused, and the cache is from SP3b's *converted* corpus (these IDs are detection cases there; on `main` they are `true_negative`). The honest takeaway: the rate impact is small; the bug's real harm was per-pattern (false "5/5" on refusing cases — already corrected in `sp3b-notes.md`). **No full re-baseline** (non-goal, per the meetup): the fix's value is forward — future runs can't repeat the bug.

## Deferred (filed, not scheduled)
The skill **hallucinates a refusal on short clean text under `force_full`** (real non-empty sentences → "no text provided"). This guard makes the eval HONEST about it (refusals → inconclusive, not fake detections) but does NOT fix the skill behavior. That is a separate product-robustness finding (a properly-powered A/B is the tool if pursued).

## Unblocks SP3b
SP3b (`sp3b-true-neg-corpus`, held) resumes after this merges: rebase on main (drop its stranded `172cdfb` overlap fn — unused, this sub-project went phrase-only), then re-validate the converted cases under the fixed scorer (013/009_003 will now go `inconclusive`, not false-detect), and finish the corpus disposition.
