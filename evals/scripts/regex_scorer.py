"""
Deterministic AI-tell scorer for the humanizer skill.

Counts high-confidence Tier-1 AI-writing patterns by regex and reports
density per 100 words, per-paragraph breakdown, and (in --compare mode)
length delta and pattern regressions between input and output.

This script handles MECHANICS only. Substance dimensions (Specificity,
Voice) need LLM judgment and live in SKILL.md prose, not here. A score
the model can't self-flatter forces it to do real work on the things
that can't be counted.

Author: Asaf Lecht (https://github.com/Seithx)
Integrated into humanizer-ext as a fast deterministic first-pass alongside
the LLM-based `run_pattern_eval.py` (which scores behavioral pattern
removal, not raw substring presence). See `evals/README.md` for how the
two relate. See `CONTRIBUTORS.md` for full attribution.

Usage:
    python -m evals.scripts.regex_scorer text.txt                      # score one file
    python -m evals.scripts.regex_scorer < text.txt                    # stdin
    python -m evals.scripts.regex_scorer --compare input.txt out.txt   # diff
    python -m evals.scripts.regex_scorer text.txt --json               # machine-readable
    python -m evals.scripts.regex_scorer text.txt --lang en            # explicit language (default en)

Python 3.10+, stdlib only. No dependencies.
"""

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Pattern catalogues, one per supported language. Grouped by Mechanics
# dimensions. Each entry: (regex, short label).
#
# Regexes are conservative; false negatives are preferred over false positives
# so the LLM still has to read the text, not just trust the score. For the
# humanizer eval use case this means the skill does NOT get full credit for
# clean rewrites (false negative), rather than getting penalized for
# legitimate prose (false positive) — the desired tradeoff.
#
# To add a new language pack (e.g., DE in Phase 2), define PATTERNS_DE with
# the same shape and add it to PATTERNS_BY_LANG. The dimension map is shared
# across languages — pattern keys must use the same names where the concept
# is universal (em_dash_overuse, boldface_overuse, emoji_bullet); language-
# specific tells get language-specific keys.
# ---------------------------------------------------------------------------

PATTERNS_EN = {
    # --- Directness ---------------------------------------------------------
    "hedging": (
        re.compile(
            r"\b(it could be argued|some might say|it is important to note|"
            r"it should be noted|it is worth mentioning|one might consider|"
            r"arguably)\b",
            re.I,
        ),
        "hedging / it-is-important-to-note",
    ),
    "vague_attribution": (
        re.compile(
            r"\b(experts (?:say|believe|argue|note)|many (?:believe|argue)|"
            r"studies (?:show|suggest|indicate)|research (?:shows|suggests)|"
            r"it is widely (?:accepted|believed|known))\b",
            re.I,
        ),
        "vague attribution",
    ),
    # --- Rhythm -------------------------------------------------------------
    "transitional_cliche": (
        re.compile(
            r"(?m)^[ \t>*\-]*"
            r"(Moreover|Furthermore|Additionally|In essence|It's worth noting|"
            r"That said|In other words|Indeed|Notably|Importantly)\s*,",
            re.I,
        ),
        "transitional cliche at sentence start",
    ),
    "not_just_X_its_Y": (
        re.compile(
            r"\b[Nn]ot just\s+[^.,;!?\n]{2,60}[,;.]?\s+(it'?s|but)\b|"
            r"\b[Nn]ot only\s+[^.,;!?\n]{2,80}\s+but\s+also\b",
            re.I,
        ),
        "'not just X, it's Y' / 'not only X but also' parallelism",
    ),
    # --- Trust --------------------------------------------------------------
    "explainer_voice": (
        re.compile(
            r"\b(let me explain|let'?s dive into|let'?s break (?:this|that|it) down|"
            r"let me walk you through|let'?s explore|let'?s unpack|"
            r"let me clarify)\b",
            re.I,
        ),
        "explainer voice opener",
    ),
    "summary_loop": (
        re.compile(
            r"\b(in conclusion|in summary|to summarize|overall|all in all|"
            r"to wrap (?:up|things up)|in closing)\b",
            re.I,
        ),
        "summary loop",
    ),
    "sycophantic_opener": (
        re.compile(
            r"^\s*(Great question|Absolutely|Certainly|What a (?:great|fascinating|wonderful)|"
            r"I'd be (?:happy|delighted) to help|Excellent question|"
            r"That'?s a (?:great|fantastic) question)",
            re.I | re.M,
        ),
        "sycophantic opener",
    ),
    # --- Authenticity -------------------------------------------------------
    "puffery": (
        re.compile(
            r"\b(delve into|leverage|robust|comprehensive|seamless|holistic|"
            r"synergy|paradigm|landscape of|ecosystem of|vibrant|cutting[- ]edge|"
            r"state[- ]of[- ]the[- ]art|game[- ]changing|revolutionary|"
            r"unparalleled|unprecedented)\b",
            re.I,
        ),
        "puffery vocabulary",
    ),
    "vocabulary_tells": (
        re.compile(
            r"\b(elucidate|myriad|plethora|tapestry|intricate(?:ly)?|"
            r"navigate(?:s|d)? (?:the|this|these) (?:complex|complexities|"
            r"challenges|landscape|terrain|world)|paramount|quintessential|"
            r"manifold|multifaceted)\b",
            re.I,
        ),
        "vocabulary tells",
    ),
    "ai_apology": (
        re.compile(
            r"\b(I apologize for (?:any |the )?(?:confusion|inconvenience|misunderstanding)|"
            r"my apologies for (?:any |the )?(?:confusion|inconvenience))\b",
            re.I,
        ),
        "AI-style apology",
    ),
    # --- Density / Restraint -----------------------------------------------
    "significance_inflation": (
        re.compile(
            r"\b(stands? as a testament|is a testament to|vital role|crucial role|"
            r"pivotal (?:role|moment|point)|reflects broader|"
            r"set(?:s|ting)? the stage for|indelible mark|deeply rooted|"
            r"marks? a (?:pivotal|significant|critical) (?:moment|point|turning point)|"
            r"key turning point|evolving landscape|underscores the (?:importance|need))\b",
            re.I,
        ),
        "significance inflation",
    ),
    "fake_ing_analysis": (
        re.compile(
            r",\s+(creating|making|marking|representing|reflecting|symbolizing|"
            r"highlighting|underscoring|shaping|contributing to|setting|paving|"
            r"emphasizing|illustrating|demonstrating)\s+\w+",
            re.I,
        ),
        "trailing -ing fake analysis clause",
    ),
    "ultimately_starter": (
        re.compile(r"(?m)^[ \t>*\-]*Ultimately\s*,", re.I),
        "'Ultimately,' as sentence opener",
    ),
    "filler_phrases": (
        re.compile(
            r"\bI hope this helps\b|"
            r"\b(?:please )?(?:let me know if|feel free to (?:ask|reach out|"
            r"let me know|share))\b|"
            r"\bit'?s important to (?:note|remember|mention|understand|recognize)\b",
            re.I,
        ),
        "filler / closer phrases",
    ),
    # --- Punctuation / formatting tells ------------------------------------
    "em_dash_overuse": (
        # Em-dash, spaced em-dash, en-dash w/ spaces, double-hyphen, triple-hyphen.
        # Exclude markdown list markers (^- ) and code-block fences (handled elsewhere).
        re.compile(r"—| — | – |(?<!\w)--(?!-)|(?<!\w)---(?!-)"),
        "em-dash overuse (any variant)",
    ),
    "boldface_overuse": (
        re.compile(r"\*\*[^*\n]{1,80}\*\*"),
        "boldface span (count, threshold-checked)",
    ),
    "emoji_bullet": (
        re.compile(
            r"(?m)^[ \t]*(?:✅|✨|⭐|🌟|🚀|🎉|⚡|🔍|💡|🎯|📊|📝|📌|🔥|👍|💯|✔️|☑️|🔹|🔸)"
        ),
        "emoji-prefixed bullet",
    ),
    "rule_of_three": (
        re.compile(r"\b\w+,\s+\w+,?\s+and\s+\w+\b"),
        "rule-of-three list (count, threshold-checked)",
    ),
}

# Language registry. Add new packs here (e.g., "de": PATTERNS_DE).
PATTERNS_BY_LANG: dict[str, dict] = {
    "en": PATTERNS_EN,
}

# Threshold-based patterns: a single occurrence is fine, density is the tell.
# Same thresholds across languages (universal mechanics — em-dash counts the
# same in any language). Override per-language by extending this dict if
# evidence shows a language has different baseline density.
THRESHOLD_PATTERNS = {
    "boldface_overuse": 0.5,   # > 0.5 bolded spans per 100 words
    "rule_of_three": 1.5,      # > 1.5 rule-of-three per 100 words
}

# Mapping pattern -> dimension (for the per-dimension breakdown).
DIMENSION_MAP = {
    "Directness": ["hedging", "vague_attribution"],
    "Rhythm": ["transitional_cliche", "not_just_X_its_Y"],
    "Trust": ["explainer_voice", "summary_loop", "sycophantic_opener"],
    "Authenticity": ["puffery", "vocabulary_tells", "ai_apology"],
    "Density": ["fake_ing_analysis", "ultimately_starter", "filler_phrases",
                "boldface_overuse", "emoji_bullet"],
    "Restraint": ["significance_inflation", "rule_of_three"],
    "Punctuation": ["em_dash_overuse"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HEBREW_RE = re.compile(r"[\u0590-\u05FF]")
CODE_FENCE_RE = re.compile(r"```.*?```", re.S)
BLOCK_QUOTE_RE = re.compile(r"(?m)^>.*$")
WORD_RE = re.compile(r"\b[\w']+\b", re.U)
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\u0590-\u05FF])")


def clean_text(text: str) -> str:
    """Strip code blocks and block-quoted text so the scorer ignores quoted AI."""
    text = CODE_FENCE_RE.sub("", text)
    text = BLOCK_QUOTE_RE.sub("", text)
    return text


def is_mostly_hebrew(paragraph: str) -> bool:
    """A paragraph is Hebrew-dominant if >40% of its alpha chars are Hebrew."""
    hebrew = len(HEBREW_RE.findall(paragraph))
    total_alpha = sum(1 for c in paragraph if c.isalpha())
    return total_alpha > 0 and hebrew / total_alpha > 0.4


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def sentence_lengths(text: str) -> list:
    sents = SENT_SPLIT_RE.split(text.strip())
    return [word_count(s) for s in sents if word_count(s) > 0]


def split_paragraphs(text: str) -> list:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------

def get_patterns(lang: str) -> dict:
    """Return the pattern dict for `lang`. Raises KeyError if pack unknown."""
    if lang not in PATTERNS_BY_LANG:
        raise KeyError(
            f"unknown language pack: {lang!r}. "
            f"Available: {sorted(PATTERNS_BY_LANG)}"
        )
    return PATTERNS_BY_LANG[lang]


# Patterns that are universal mechanics (formatting / punctuation) and apply
# regardless of the paragraph's natural language. Used when a paragraph is in
# a script the active language pack doesn't cover.
UNIVERSAL_MECHANICS_KEYS = ("em_dash_overuse", "boldface_overuse", "emoji_bullet")


def scan(text: str, *, lang: str = "en", skip_lang_specific: bool = False) -> dict:
    """Count pattern hits in a block of text. Returns {pattern: count}.

    When `skip_lang_specific=True`, only universal-mechanics patterns are
    counted — use for paragraphs whose script does not match `lang` (e.g., a
    Hebrew paragraph in an EN document).
    """
    patterns = get_patterns(lang)
    hits = {}
    for name, (rx, _label) in patterns.items():
        if skip_lang_specific and name not in UNIVERSAL_MECHANICS_KEYS:
            hits[name] = 0
            continue
        hits[name] = len(rx.findall(text))
    return hits


def density(hits: int, words: int) -> float:
    """Hits per 100 words. 0 if no words."""
    return (hits / words * 100) if words > 0 else 0.0


def tier1_total(hits: dict, words: int) -> int:
    """Sum of all tells, ignoring threshold patterns that are under their threshold."""
    total = 0
    for name, count in hits.items():
        if name in THRESHOLD_PATTERNS:
            if density(count, words) > THRESHOLD_PATTERNS[name]:
                total += count
        else:
            total += count
    return total


def verdict_for_density(d: float) -> str:
    """Pass-strength verdict from density per 100 words."""
    if d < 3:
        return "LOW (0-2/100w) — light touch only, leave voice alone"
    if d < 6:
        return "MEDIUM (3-5/100w) — fix Tier-1 + Tier-2"
    return f"HIGH ({d:.1f}/100w) — full pass, all patterns apply"


def rhythm_check(text: str) -> dict:
    """Sentence-length variance. Low variance = metronomic AI rhythm."""
    lengths = sentence_lengths(text)
    if len(lengths) < 3:
        return {"sentences": len(lengths), "mean": 0, "stdev": 0, "verdict": "n/a"}
    mean = statistics.mean(lengths)
    stdev = statistics.stdev(lengths)
    cv = stdev / mean if mean > 0 else 0
    # Coefficient of variation: < 0.35 reads as metronomic, > 0.6 reads varied.
    if cv < 0.35:
        verdict = "METRONOMIC — sentences too uniform in length"
    elif cv > 0.6:
        verdict = "VARIED — good rhythm"
    else:
        verdict = "OK"
    return {
        "sentences": len(lengths),
        "mean": round(mean, 1),
        "stdev": round(stdev, 1),
        "cv": round(cv, 2),
        "verdict": verdict,
    }


def score_text(text: str, *, lang: str = "en") -> dict:
    """Full report for one text scored against the given language pack."""
    cleaned = clean_text(text)
    paragraphs = split_paragraphs(cleaned)
    total_words = word_count(cleaned)

    # Per-paragraph density (this is the key insight from issue #93)
    para_reports = []
    for i, p in enumerate(paragraphs, 1):
        # Hebrew check stays for backwards compat. A paragraph in a script the
        # active language pack does not target gets only universal mechanics.
        hebrew = is_mostly_hebrew(p) and lang == "en"
        p_hits = scan(p, lang=lang, skip_lang_specific=hebrew)
        p_words = word_count(p)
        p_tier1 = tier1_total(p_hits, p_words)
        p_density = density(p_tier1, p_words)
        para_reports.append({
            "paragraph": i,
            "words": p_words,
            "hebrew": hebrew,
            "tier1_hits": p_tier1,
            "density_per_100w": round(p_density, 2),
            "verdict": verdict_for_density(p_density),
            "hits_by_pattern": {k: v for k, v in p_hits.items() if v > 0},
        })

    # Global stats
    total_hits = scan(cleaned, lang=lang)
    total_tier1 = tier1_total(total_hits, total_words)
    global_density = density(total_tier1, total_words)

    # Per-dimension breakdown
    dim_breakdown = {}
    for dim, pattern_names in DIMENSION_MAP.items():
        dim_count = sum(total_hits.get(n, 0) for n in pattern_names)
        dim_breakdown[dim] = {
            "hits": dim_count,
            "density_per_100w": round(density(dim_count, total_words), 2),
            "patterns": {n: total_hits.get(n, 0) for n in pattern_names
                         if total_hits.get(n, 0) > 0},
        }

    return {
        "lang": lang,
        "words": total_words,
        "paragraphs": len(paragraphs),
        "tier1_total": total_tier1,
        "density_per_100w": round(global_density, 2),
        "verdict": verdict_for_density(global_density),
        "rhythm": rhythm_check(cleaned),
        "dimensions": dim_breakdown,
        "per_paragraph": para_reports,
    }


def compare(input_text: str, output_text: str, *, lang: str = "en") -> dict:
    """Diff a rewrite against its source. Catches truncation and regressions."""
    in_report = score_text(input_text, lang=lang)
    out_report = score_text(output_text, lang=lang)

    in_words = in_report["words"]
    out_words = out_report["words"]
    length_delta = out_words - in_words
    length_pct = (length_delta / in_words * 100) if in_words > 0 else 0

    if abs(length_pct) <= 10:
        length_verdict = "OK — within ±10%"
    elif length_pct < -25:
        length_verdict = f"TRUNCATED — output is {abs(length_pct):.0f}% shorter than input"
    elif length_pct < -10:
        length_verdict = f"SHORTENED — output is {abs(length_pct):.0f}% shorter (check nothing was dropped)"
    else:
        length_verdict = f"EXPANDED — output is {length_pct:.0f}% longer than input"

    # Pattern-level diff
    in_hits = scan(clean_text(input_text), lang=lang)
    out_hits = scan(clean_text(output_text), lang=lang)
    removed = {k: in_hits[k] - out_hits[k] for k in in_hits
               if in_hits[k] > out_hits[k]}
    introduced = {k: out_hits[k] - in_hits[k] for k in out_hits
                  if out_hits[k] > in_hits[k]}

    return {
        "lang": lang,
        "input": {"words": in_words, "tier1": in_report["tier1_total"],
                  "density": in_report["density_per_100w"]},
        "output": {"words": out_words, "tier1": out_report["tier1_total"],
                   "density": out_report["density_per_100w"]},
        "length_delta_words": length_delta,
        "length_delta_pct": round(length_pct, 1),
        "length_verdict": length_verdict,
        "tier1_removed": in_report["tier1_total"] - out_report["tier1_total"],
        "patterns_cleaned": removed,
        "patterns_introduced": introduced,
        "rhythm_before": in_report["rhythm"],
        "rhythm_after": out_report["rhythm"],
    }


# ---------------------------------------------------------------------------
# Pretty-printing
# ---------------------------------------------------------------------------

def format_report(report: dict) -> str:
    lang = report.get("lang", "en")
    patterns = get_patterns(lang)
    lines = []
    lines.append("=" * 60)
    lines.append(f"AI-TELL DENSITY REPORT (lang={lang})")
    lines.append("=" * 60)
    lines.append(f"Words:           {report['words']}")
    lines.append(f"Paragraphs:      {report['paragraphs']}")
    lines.append(f"Tier-1 hits:     {report['tier1_total']}")
    lines.append(f"Density / 100w:  {report['density_per_100w']}")
    lines.append(f"Verdict:         {report['verdict']}")
    lines.append("")
    r = report["rhythm"]
    lines.append(f"Rhythm:          mean {r['mean']}w/sent, stdev {r['stdev']}, cv {r.get('cv', 0)} -> {r['verdict']}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("BY DIMENSION (mechanics only — substance is LLM judgment)")
    lines.append("-" * 60)
    for dim, data in report["dimensions"].items():
        if data["hits"] == 0:
            continue
        lines.append(f"{dim:14s}  {data['hits']:3d} hits  ({data['density_per_100w']}/100w)")
        for pat, count in data["patterns"].items():
            label = patterns[pat][1] if pat in patterns else pat
            lines.append(f"    - {label}: {count}")
    lines.append("")

    lines.append("-" * 60)
    lines.append("PER PARAGRAPH (target your rewrite to the high-density ones)")
    lines.append("-" * 60)
    for p in report["per_paragraph"]:
        marker = "  [Hebrew]" if p["hebrew"] else ""
        lines.append(f"P{p['paragraph']:2d}  {p['words']:3d}w  "
                     f"{p['tier1_hits']:2d} hits  "
                     f"{p['density_per_100w']:5.1f}/100w  "
                     f"-> {p['verdict']}{marker}")
    return "\n".join(lines)


def format_compare(diff: dict) -> str:
    lang = diff.get("lang", "en")
    patterns = get_patterns(lang)
    lines = []
    lines.append("=" * 60)
    lines.append(f"HUMANIZER REWRITE: BEFORE vs AFTER (lang={lang})")
    lines.append("=" * 60)
    i, o = diff["input"], diff["output"]
    lines.append(f"Input:   {i['words']:4d}w   {i['tier1']:3d} tells   {i['density']}/100w")
    lines.append(f"Output:  {o['words']:4d}w   {o['tier1']:3d} tells   {o['density']}/100w")
    lines.append("")
    lines.append(f"Length:  {diff['length_delta_words']:+d} words ({diff['length_delta_pct']:+.1f}%)  -> {diff['length_verdict']}")
    lines.append(f"Tells:   {diff['tier1_removed']:+d} removed")
    lines.append("")

    if diff["patterns_cleaned"]:
        lines.append("Cleaned (input -> output):")
        for pat, n in sorted(diff["patterns_cleaned"].items(), key=lambda x: -x[1]):
            label = patterns[pat][1] if pat in patterns else pat
            lines.append(f"    - {label}: -{n}")
    if diff["patterns_introduced"]:
        lines.append("")
        lines.append("REGRESSION — new tells introduced by the rewrite:")
        for pat, n in sorted(diff["patterns_introduced"].items(), key=lambda x: -x[1]):
            label = patterns[pat][1] if pat in patterns else pat
            lines.append(f"    + {label}: +{n}")
    if not diff["patterns_introduced"]:
        lines.append("")
        lines.append("(No new tells introduced. Good.)")

    lines.append("")
    rb, ra = diff["rhythm_before"], diff["rhythm_after"]
    lines.append(f"Rhythm before: cv={rb.get('cv', 0)} -> {rb['verdict']}")
    lines.append(f"Rhythm after:  cv={ra.get('cv', 0)} -> {ra['verdict']}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def read_input(path_or_stdin):
    if path_or_stdin == "-" or path_or_stdin is None:
        return sys.stdin.read()
    return Path(path_or_stdin).read_text(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("path", nargs="?", help="Text file to score (or '-' / omit for stdin)")
    ap.add_argument("--compare", nargs=2, metavar=("INPUT", "OUTPUT"),
                    help="Diff a rewrite against its source")
    ap.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    ap.add_argument("--lang", default="en",
                    choices=sorted(PATTERNS_BY_LANG),
                    help=f"Language pack to score against (default: en; available: {sorted(PATTERNS_BY_LANG)})")
    args = ap.parse_args()

    if args.compare:
        in_text = read_input(args.compare[0])
        out_text = read_input(args.compare[1])
        result = compare(in_text, out_text, lang=args.lang)
        print(json.dumps(result, indent=2, ensure_ascii=False)
              if args.json else format_compare(result))
        return

    text = read_input(args.path)
    result = score_text(text, lang=args.lang)
    print(json.dumps(result, indent=2, ensure_ascii=False)
          if args.json else format_report(result))


if __name__ == "__main__":
    main()
