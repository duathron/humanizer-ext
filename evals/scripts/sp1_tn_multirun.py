"""Re-baseline the 9 EN true-negative cases over N runs each (default 5).
Pass = Levenshtein edit_ratio <= 0.10 (same criterion as run_pattern_eval).
Also flags 'leak' = the output looks like it carries audit/commentary (a proxy
for the intermittent Quick-mode trailer that bloats edit-ratio).
Subscription-only (claude -p), no judge, no API key. Prints per-run so progress
survives interruption."""
import glob
import json
import sys
from pathlib import Path
REPO = Path("/Users/christianhuhn/Library/Mobile Documents/iCloud~md~obsidian/"
            "Documents/duathron.github.io/__obsidian_vault/AI/SKILLS/humanizer-ext")
sys.path.insert(0, str(REPO))
from evals.scripts.run_e2e_eval import run_skill, _looks_like_failed_rewrite  # noqa
from rapidfuzz.distance import Levenshtein  # noqa

N = int(sys.argv[1]) if len(sys.argv) > 1 else 5

cases = []
for f in sorted(glob.glob(str(REPO / "evals/corpus/en/patterns/*.json"))):
    d = json.load(open(f))
    for c in d.get("cases", [d]):
        if c.get("true_negative"):
            cases.append((c["id"], c["input"],
                          c.get("metadata", {}).get("lang", "en"),
                          c.get("domain")))

LEAK_TOKENS = ("em dash", "em-dash", "remaining", "**change", "pre-flight",
               "tier-1", "→", " -> ", "audit", "removed #", "wesentliche")
tot_pass = tot = 0
for cid, inp, lang, dom in cases:
    passes = leaks = 0
    ratios = []
    for _ in range(N):
        out = run_skill(inp, lang=lang, mode="full", domain=dom,
                        model="sonnet", force_full=False, timeout=300)
        final = out.get("final") or out.get("draft") or ""
        er = Levenshtein.distance(inp, final) / max(1, len(inp))
        ratios.append(round(er, 3))
        if er <= 0.10:
            passes += 1
        low = final.lower()
        if len(final) > len(inp) * 1.15 or any(t in low for t in LEAK_TOKENS) \
                or _looks_like_failed_rewrite(final):
            leaks += 1
    tot_pass += passes
    tot += N
    print(f"{cid:22} pass={passes}/{N} leak={leaks}/{N} ratios={ratios}", flush=True)

print(f"\nSTABLE true-neg pass-rate: {tot_pass}/{tot} runs "
      f"({tot_pass/tot:.2%}); per-case majority-pass count is the 'X/9' figure.")
