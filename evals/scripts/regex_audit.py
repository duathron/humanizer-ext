"""Deterministic corpus audit using regex_scorer.

Two audits, both zero-API:

1. PATTERN CORPUS audit — for each `evals/corpus/{lang}/patterns/*.json` case,
   runs regex_scorer on the `input` field and asks: do any of the regexes
   in the pattern's expected category hit this input? If not, the case is
   structurally unscorable for that pattern by any method that depends on
   the pattern actually being present in the text. Surfaces concrete fixes
   (which inputs to rewrite or which trigger terms to add).

2. HUMAN SAMPLE audit — for each `evals/corpus/{lang}/human/*/<file>`,
   runs regex_scorer and reports density. Human samples should land in the
   LOW band (< 3 hits / 100w). Any human sample that lands MEDIUM or HIGH
   is either not actually clean or surfaces a regex that fires too eagerly.

This complements the LLM-based pattern + FP evals: regex is fast and
deterministic but limited to substring matching; the LLM evals catch
behavioral patterns the regex misses. Cross-validation is where the
two methods disagree.

Usage:
    python -m evals.scripts.regex_audit --lang en
    python -m evals.scripts.regex_audit --lang en --audit pattern
    python -m evals.scripts.regex_audit --lang en --audit human
    python -m evals.scripts.regex_audit --lang en --json

No API calls. No dependencies beyond stdlib + regex_scorer.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from evals.scripts.regex_scorer import (
    DIMENSION_MAP,
    PATTERNS_BY_LANG,
    get_patterns,
    scan,
    score_text,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Pattern ID → regex_scorer category map
# Maps humanizer-ext pattern IDs (#1-#40, #100+) to regex_scorer dimension
# names. Used to decide which regex hits "count" for a given pattern case.
# ---------------------------------------------------------------------------

# Patterns #1-#40 from the EN pack; maps each to one or more regex_scorer
# pattern keys (not dimensions, since multiple patterns per dimension).
PATTERN_ID_TO_REGEX_KEYS = {
    # Content patterns
    1: ["significance_inflation", "puffery"],            # significance inflation
    2: [],                                                # notability — no regex catalogue match
    3: ["fake_ing_analysis"],                            # superficial -ing endings
    4: ["puffery"],                                       # promotional language
    5: ["vague_attribution"],                            # vague attributions
    6: ["challenges_section"],                           # challenges section
    # Language patterns
    7: ["puffery", "vocabulary_tells"],                  # AI vocabulary
    8: [],                                                # copula avoidance — needs POS
    9: ["not_just_X_its_Y"],                             # negative parallelisms
    10: ["rule_of_three"],                               # rule of three
    11: [],                                              # synonym cycling — semantic
    12: [],                                              # false ranges — semantic
    13: [],                                              # passive voice — would need POS tagger
    # Style patterns
    14: ["em_dash_overuse"],                             # em dash
    15: ["boldface_overuse"],                            # boldface
    16: [],                                              # inline-header lists — structural
    17: ["title_case_heading"],                          # title case headings
    18: ["emoji_bullet"],                                # emojis
    19: ["curly_quotes"],                                # curly quotes
    # Communication patterns
    20: ["sycophantic_opener", "filler_phrases"],        # chatbot artifacts
    21: ["hedging"],                                     # cutoff disclaimers
    22: ["sycophantic_opener"],                          # sycophantic tone
    # Filler/hedging
    23: ["filler_phrases", "hedging"],                   # filler phrases
    24: ["hedging"],                                     # excessive hedging
    25: ["summary_loop"],                                # generic conclusions
    26: [],                                              # hyphenation — context
    27: ["explainer_voice"],                             # persuasive authority tropes
    28: ["explainer_voice", "transitional_cliche"],      # signposting
    29: ["fragmented_header"],                           # fragmented headers
    30: ["ultimately_starter", "transitional_cliche"],   # sentence-starter intensifiers
    31: [],                                              # rhetorical questions — semantic
    32: ["puffery"],                                     # stacked adjectives
    33: [],                                              # quantity vagueness — context
    34: ["trailing_emphasis_fragment"],                  # trailing emphasis fragments
    35: [],                                              # debunking headings — semantic
    36: ["hedging"],                                     # conditional frame stacking
    37: ["hedging"],                                     # miscalibrated confidence
    # Artifacts
    38: ["reference_markup_artifact"],                   # ref markup artifacts
    39: ["placeholder_text"],                            # placeholder text
    40: ["markdown_contamination"],                      # markdown contamination
}


def audit_pattern_corpus(lang: str = "en") -> dict:
    """For each pattern case, check whether regex_scorer fires on the input."""
    corpus_dir = REPO_ROOT / "evals" / "corpus" / lang / "patterns"
    files = sorted(corpus_dir.glob("pattern_*.json"))

    per_pattern: list[dict] = []
    cases_with_regex_signal = 0
    cases_without_regex_signal = 0
    cases_pattern_unmapped = 0

    for path in files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        pid = payload["pattern_id"]
        regex_keys = PATTERN_ID_TO_REGEX_KEYS.get(pid, [])
        case_audits = []

        for case in payload["cases"]:
            hits = scan(case["input"], lang=lang)
            relevant_hits = {k: hits[k] for k in regex_keys if hits.get(k, 0) > 0}
            if not regex_keys:
                cases_pattern_unmapped += 1
                signal = "unmapped"
            elif relevant_hits:
                cases_with_regex_signal += 1
                signal = "regex_fires"
            else:
                cases_without_regex_signal += 1
                signal = "no_regex_signal"
            case_audits.append({
                "case_id": case["id"],
                "signal": signal,
                "relevant_regex_hits": relevant_hits,
                "all_regex_hits": {k: v for k, v in hits.items() if v > 0},
            })

        per_pattern.append({
            "pattern_id": pid,
            "pattern_name": payload["pattern_name"],
            "regex_keys": regex_keys,
            "cases": case_audits,
        })

    total_cases = cases_with_regex_signal + cases_without_regex_signal + cases_pattern_unmapped
    return {
        "audit_type": "pattern_corpus",
        "lang": lang,
        "summary": {
            "total_patterns": len(per_pattern),
            "total_cases": total_cases,
            "cases_with_regex_signal": cases_with_regex_signal,
            "cases_without_regex_signal": cases_without_regex_signal,
            "cases_pattern_unmapped": cases_pattern_unmapped,
            "patterns_with_no_regex_mapping": [
                p["pattern_id"] for p in per_pattern if not p["regex_keys"]
            ],
        },
        "per_pattern": per_pattern,
    }


def audit_human_samples(lang: str = "en") -> dict:
    """For each human sample, run regex_scorer and report density verdict."""
    human_dir = REPO_ROOT / "evals" / "corpus" / lang / "human"
    if not human_dir.is_dir():
        return {"audit_type": "human_samples", "lang": lang, "per_file": []}

    per_file = []
    over_threshold_count = 0
    for path in sorted(human_dir.rglob("*.md")):
        if path.name.startswith("_"):
            continue
        text = path.read_text(encoding="utf-8")
        # Strip YAML frontmatter if present so it does not skew density
        if text.startswith("---\n"):
            end = text.find("\n---\n", 4)
            if end >= 0:
                text = text[end + 5:]
        report = score_text(text, lang=lang)
        verdict_band = "LOW" if "LOW" in report["verdict"] else (
            "MEDIUM" if "MEDIUM" in report["verdict"] else "HIGH"
        )
        if verdict_band != "LOW":
            over_threshold_count += 1
        per_file.append({
            "file": str(path.relative_to(human_dir)),
            "words": report["words"],
            "tier1_total": report["tier1_total"],
            "density_per_100w": report["density_per_100w"],
            "verdict_band": verdict_band,
            "verdict": report["verdict"],
            "top_hits": {
                k: v for k, v in
                sorted(
                    ((p, count) for dim in report["dimensions"].values()
                     for p, count in dim["patterns"].items()),
                    key=lambda x: -x[1],
                )[:5]
            },
        })

    return {
        "audit_type": "human_samples",
        "lang": lang,
        "summary": {
            "total_files": len(per_file),
            "files_over_low_band": over_threshold_count,
            "files_in_low_band": len(per_file) - over_threshold_count,
        },
        "per_file": per_file,
    }


def format_pattern_audit(audit: dict) -> str:
    s = audit["summary"]
    lines = [
        "=" * 60,
        f"PATTERN CORPUS AUDIT (lang={audit['lang']}) — deterministic regex check",
        "=" * 60,
        f"Total patterns:               {s['total_patterns']}",
        f"Total cases:                  {s['total_cases']}",
        f"Cases with regex signal:      {s['cases_with_regex_signal']}",
        f"Cases without regex signal:   {s['cases_without_regex_signal']}",
        f"Cases on unmapped pattern:    {s['cases_pattern_unmapped']}",
        "",
        "Patterns with no regex_scorer mapping (signal must come from LLM):",
        f"  #{', #'.join(str(p) for p in s['patterns_with_no_regex_mapping'])}",
        "",
        "-" * 60,
        "PER-PATTERN DETAIL (cases where regex does not fire on input):",
        "-" * 60,
    ]
    for p in audit["per_pattern"]:
        misses = [c for c in p["cases"] if c["signal"] == "no_regex_signal"]
        if not misses:
            continue
        lines.append(f"#{p['pattern_id']:2d} {p['pattern_name']}")
        lines.append(f"     expected regex keys: {p['regex_keys']}")
        for m in misses:
            lines.append(f"     - {m['case_id']}: input has no regex hit in expected keys")
            if m["all_regex_hits"]:
                lines.append(f"       (other regex hits: {m['all_regex_hits']})")
        lines.append("")
    return "\n".join(lines)


def format_human_audit(audit: dict) -> str:
    s = audit["summary"]
    lines = [
        "=" * 60,
        f"HUMAN SAMPLE AUDIT (lang={audit['lang']}) — should all land LOW",
        "=" * 60,
        f"Total files:           {s['total_files']}",
        f"In LOW band (good):    {s['files_in_low_band']}",
        f"Over LOW band (flag):  {s['files_over_low_band']}",
        "",
        "-" * 60,
        "PER-FILE",
        "-" * 60,
    ]
    for f in audit["per_file"]:
        marker = "✓" if f["verdict_band"] == "LOW" else "⚠"
        lines.append(
            f"{marker} {f['file']:60s}  {f['words']:4d}w  "
            f"{f['tier1_total']:3d} hits  {f['density_per_100w']:5.1f}/100w  → {f['verdict_band']}"
        )
        if f["verdict_band"] != "LOW" and f["top_hits"]:
            for hit, count in f["top_hits"].items():
                lines.append(f"      {hit}: {count}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1] if __doc__ else "")
    parser.add_argument("--lang", default="en", choices=sorted(PATTERNS_BY_LANG))
    parser.add_argument(
        "--audit", choices=["pattern", "human", "both"], default="both",
        help="Which audit to run (default: both).",
    )
    parser.add_argument("--json", action="store_true", help="JSON output.")
    args = parser.parse_args()

    results = {}
    if args.audit in ("pattern", "both"):
        results["pattern_audit"] = audit_pattern_corpus(args.lang)
    if args.audit in ("human", "both"):
        results["human_audit"] = audit_human_samples(args.lang)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    if "pattern_audit" in results:
        print(format_pattern_audit(results["pattern_audit"]))
        print()
    if "human_audit" in results:
        print(format_human_audit(results["human_audit"]))


if __name__ == "__main__":
    main()
