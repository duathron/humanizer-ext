"""SP1 widen-probe: measure first-attempt change-log rate WITHOUT the judge.

Mirrors run_e2e_eval.score_case's first-attempt candidate extraction + verdict
(skill_out.get('final') or .get('draft'); _looks_like_failed_rewrite), but never
calls the judge -> zero API spend, pure `claude -p` subscription. Probes every
e2e case across the given langs, N runs each, and reports per-case + pooled rate.
"""
import json
import sys
from pathlib import Path

REPO = Path("/Users/christianhuhn/Library/Mobile Documents/iCloud~md~obsidian/"
            "Documents/duathron.github.io/__obsidian_vault/AI/SKILLS/humanizer-ext")
sys.path.insert(0, str(REPO))

from evals.scripts.run_e2e_eval import run_skill, _looks_like_failed_rewrite  # noqa: E402

RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
LANGS = sys.argv[2].split(",") if len(sys.argv) > 2 else ["de", "en"]

pooled_total = 0
pooled_flag = 0
for lang in LANGS:
    cdir = REPO / "evals" / "corpus" / lang / "e2e"
    for path in sorted(cdir.glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        flags = []
        for _ in range(RUNS):
            out = run_skill(case["input"], lang=case.get("lang", lang),
                            mode="full", domain=case.get("domain"),
                            model="sonnet", timeout=420)
            cand = out.get("final") or out.get("draft") or ""
            flags.append(bool(_looks_like_failed_rewrite(cand)))
        n_flag = sum(flags)
        pooled_total += len(flags)
        pooled_flag += n_flag
        print(f"{lang:2} {case['id']:24} domain={case.get('domain',''):10} "
              f"flags={['T' if f else 'F' for f in flags]} rate={n_flag}/{len(flags)}",
              flush=True)

rate = round(pooled_flag / pooled_total, 3) if pooled_total else 0.0
print(f"\nPOOLED change-log first-attempt rate: {pooled_flag}/{pooled_total} = {rate}")
