"""probe_fence_emission.py — Phase 2 Task 4 Step 2: measure fence_emission_rate.

PURPOSE
-------
Measures what fraction of commentary-bearing skill outputs contain the
``<!--HUMANIZER-AUDIT-->`` fence sentinel (``fence_emission_rate``). Run by the
operator (not CI) because it consumes claude-p quota.

OFF/ON MECHANISM (OPERATOR-DRIVEN)
-----------------------------------
The installed skill at ``~/.claude/skills/humanizer/SKILL.md`` is a SYMLINK
into this repo's ``SKILL.md``. So the fence directive can be toggled without
touching the installed path:

    # Turn directive OFF (before first probe run):
    git checkout 1439502~1 -- SKILL.md

    # Run off-condition probe:
    python3 evals/scripts/probe_fence_emission.py --cond off 5

    # Turn directive ON (before second probe run):
    git checkout HEAD -- SKILL.md

    # Run on-condition probe:
    python3 evals/scripts/probe_fence_emission.py --cond on 5

The script does NOT call git; it only calls run_skill against whatever
SKILL.md is currently checked out. Tag each run with ``--cond off|on``.

INPUTS
------
Two "clean" human-written texts (expect no / minimal commentary — exercises
the Tier-1 Quick preserve-note path). Two "dirty" high-AI-tell texts (expect
commentary — exercises the change-summary + fence path).

OUTPUT
------
JSONL lines appended to ``/tmp/fence_probe_<cond>.log`` (resumable).
Summary printed to stdout with Wilson 95 % CI on fence_emission_rate.

SELF-TEST (--selftest)
----------------------
Zero-quota: exercises only detection helpers and the Wilson CI fallback.
No ``run_skill`` call, no ``claude`` subprocess. Exit 0 + print SELFTEST OK.

KNOWN MEASUREMENT LIMITATION — OFF-condition commentary undercount
------------------------------------------------------------------
``has_commentary`` detects trailing text AFTER the rewrite body (using
``_trailing_region``). When the directive is OFF the model may emit an
UNFENCED free-form note that ``parse_skill_output`` does NOT strip, so the
note merges verbatim into ``final``. In that case ``_trailing_region`` returns
"" (the note is already inside ``final``), and ``has_commentary`` returns
False — the run is NOT counted as commentary-bearing.

Consequence: the OFF-condition ``has_commentary`` rate (and therefore the
denominator used for ``fence_emission_rate``) is a LOWER BOUND.  Real
unfenced-leak ≥ measured.  The ON-condition is accurate: the sentinel fence IS
stripped from ``final`` by the parser, so the fenced note appears in the
trailing region and is correctly counted.  Gate decisions (Task 5) must treat
the OFF commentary-rate as a floor, not an exact value.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Repo root on sys.path — required for bare invocation without PYTHONPATH.
# mirrors the pattern used in evals/scripts/sp1_changelog_probe.py.
# parents[0]=evals/scripts, parents[1]=evals, parents[2]=repo root.
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

# ---------------------------------------------------------------------------
# Shared utilities (parse_skill_output, run_skill, _AUDIT_SENTINEL)
# ---------------------------------------------------------------------------
# We must be able to import _shared without any claude call at import time.
# _shared has no I/O at import time (as documented in its module docstring).
from evals.scripts._shared import (  # noqa: E402
    _AUDIT_SENTINEL,
    parse_skill_output,
    run_skill,
)

# ---------------------------------------------------------------------------
# Embedded inputs — literal strings, zero external I/O at runtime
# ---------------------------------------------------------------------------
# Each entry: id, text (body only — YAML frontmatter stripped), lang, domain.
# Clean texts exercise the Quick/preserve path; dirty texts exercise the
# full-pass change-summary + fence path.

# ---- de_clean_pflege: anschreiben_pflege_01.md (body, YAML stripped) -----
_DE_CLEAN_PFLEGE = """\
Betreff: Bewerbung als Pflegefachkraft, Station Innere Medizin

Sehr geehrte Frau Albrecht,

nach elf Jahren auf einer geriatrischen Station im Klinikum Fürth suche ich einen Wechsel in die Innere Medizin — nicht, weil mir die Arbeit mit alten Menschen nicht mehr liegt, sondern weil ich fachlich wieder breiter werden möchte.

Auf meiner jetzigen Station betreue ich im Frühdienst regulär zehn bis zwölf Patientinnen und Patienten und bin seit 2021 als Praxisanleiterin für die Auszubildenden zuständig. Im vergangenen Jahr habe ich drei Schülerinnen durch das Examen begleitet; zwei davon arbeiten heute fest bei uns. Was ich dabei gelernt habe: Ruhe bei der Übergabe spart später Zeit, und eine saubere Dokumentation schützt am Ende alle.

Ihr Haus kenne ich aus der Zusammenarbeit bei Verlegungen. Mir ist aufgefallen, dass Ihre Stationen die Bezugspflege ernst nehmen und nicht nur im Leitbild führen. Das ist mir wichtig, weil ich Menschen nicht im Schichtwechsel verlieren möchte.

Ich arbeite gern im Drei-Schicht-System und bin auch zu Wochenenddiensten bereit. Frei wäre ich ab dem 1. Oktober.

Über ein Kennenlernen, gern auch bei einer Hospitation auf Station, würde ich mich freuen.

Mit freundlichen Grüßen
Petra Sandmann"""

# ---- en_clean_blog: casual_blog_draft_01.md (body, YAML stripped) --------
_EN_CLEAN_BLOG = """\
I spent the morning trying to convince my router that yes, the printer really does exist. It's been on the same network for four years. The router knows. The printer knows. Somehow the laptop has decided otherwise.

What I keep coming back to is how much modern troubleshooting is just restarting things in different orders. Restart the router. Restart the printer. Restart the laptop. Restart all three in sequence, ascending alphabetically, while holding your tongue at the correct angle.

(My partner says I sound like someone summoning a minor deity. They are not wrong.)

The thing that fixed it, eventually, was unplugging the printer for ninety seconds. Not eighty. Not a hundred. Some weirdly specific duration that I can only assume corresponds to a capacitor draining somewhere inside the machine. I don't know. I'm not an electrical engineer. I just want to print a boarding pass."""

# ---- de_dirty_mkt: evals/corpus/de/patterns/pattern_007.json case 2 ------
# Pattern 7 DE: "Übernutzte KI-Vokabeln" — classic AI marketing vocabulary
# (innovative, nahtlos, nachhaltig, transformativ, Synergien).
# Source file: evals/corpus/de/patterns/pattern_007.json, id=pattern_007_de_002
_DE_DIRTY_MKT = (
    "Die innovative Plattform ermöglicht eine nahtlose und nachhaltige Zusammenarbeit,"
    " die es Teams erlaubt, transformative Ergebnisse zu erzielen und vielfältige"
    " Synergien zu nutzen."
)

# ---- en_dirty_mkt: evals/corpus/en/patterns/pattern_007.json case 1 ------
# Pattern 7 EN: "Overused AI Vocabulary Words" — additionally, testament,
# showcasing, integrating, landscape.
# Source file: evals/corpus/en/patterns/pattern_007.json, id=pattern_007_en_001
_EN_DIRTY_MKT = (
    "Additionally, a distinctive feature of Somali cuisine is the incorporation of"
    " camel meat. An enduring testament to Italian colonial influence is the widespread"
    " adoption of pasta in the local culinary landscape, showcasing how these dishes"
    " have integrated into the traditional diet."
)

INPUTS: dict[str, dict[str, Any]] = {
    "de_clean_pflege": {
        "text": _DE_CLEAN_PFLEGE,
        "lang": "de",
        "domain": "career",
    },
    "en_clean_blog": {
        "text": _EN_CLEAN_BLOG,
        "lang": "en",
        "domain": "casual",
    },
    "de_dirty_mkt": {
        "text": _DE_DIRTY_MKT,
        "lang": "de",
        "domain": "marketing",
    },
    "en_dirty_mkt": {
        "text": _EN_DIRTY_MKT,
        "lang": "en",
        "domain": "marketing",
    },
}

# ---------------------------------------------------------------------------
# Detection helpers
# ---------------------------------------------------------------------------

def is_fenced(raw: str) -> bool:
    """True when the raw skill response contains the ``<!--HUMANIZER-AUDIT-->`` sentinel."""
    return _AUDIT_SENTINEL in raw


def _trailing_region(raw: str, final: str) -> str:
    """Text in raw AFTER the rewrite body ends.

    Banners/headers (``**Final rewrite:**``, ``Pre-flight:``, ``> `` blockquote
    markers, etc.) precede the body, so they are not counted as trailing
    commentary.  Locates the body by its last occurrence in raw; if the model
    reflowed the body (not found verbatim), returns "" — conservative: we can't
    locate trailing commentary so we don't fabricate it.

    NOTE — OFF-condition undercount: when the directive is OFF the model may
    emit an unfenced free-form note that parse_skill_output does NOT strip, so
    the note merges into ``final``.  _trailing_region then returns "" and
    has_commentary returns False.  The OFF commentary-rate is therefore a
    LOWER BOUND (see module docstring).
    """
    body = final.strip()
    if not body:
        return raw.strip()            # empty/refusal parse -> whole raw is non-rewrite
    i = raw.rfind(body)
    if i == -1:
        # try the body's tail (model may have tweaked the head/whitespace)
        tail = body[-60:]
        i = raw.rfind(tail)
        if i == -1:
            return ""                 # can't locate -> conservative no-trailing
        i += len(tail) - len(body)    # align to body start est.
    return raw[i + len(body):]


def has_commentary(raw: str, final: str) -> bool:
    """True when raw contains content AFTER the rewrite body ends.

    Uses _trailing_region to detect only trailing text (banners/headers that
    precede the body are correctly excluded).  The +1 tolerance avoids false
    positives from a lone trailing newline.

    See module docstring for the OFF-condition lower-bound caveat.
    """
    return len(_trailing_region(raw, final).strip()) > 1


# ---------------------------------------------------------------------------
# Wilson proportion CI
# ---------------------------------------------------------------------------

def _wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a proportion k/n at confidence z.

    Hand-rolled fallback used when statsmodels is unavailable. Returns
    (lower, upper) in [0, 1]. Safe for k=0 and k=n edge cases.
    """
    if n == 0:
        return (0.0, 1.0)
    p_hat = k / n
    denom = 1 + z * z / n
    centre = (p_hat + z * z / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(p_hat * (1 - p_hat) / n + z * z / (4 * n * n))
    return (max(0.0, centre - margin), min(1.0, centre + margin))


def wilson_ci(k: int, n: int) -> tuple[float, float]:
    """Wilson 95 % CI — statsmodels if available, hand-rolled fallback otherwise."""
    try:
        from statsmodels.stats.proportion import proportion_confint  # type: ignore
        lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
        return float(lo), float(hi)
    except ImportError:
        return _wilson_ci(k, n)


# ---------------------------------------------------------------------------
# Log I/O
# ---------------------------------------------------------------------------

def _log_path(cond: str) -> Path:
    return Path(f"/tmp/fence_probe_{cond}.log")


def _load_done(log_path: Path) -> set[tuple[str, int]]:
    """Return the set of (input_id, rep) pairs already present in the log."""
    done: set[tuple[str, int]] = set()
    if not log_path.exists():
        return done
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            done.add((entry["id"], entry["rep"]))
        except (json.JSONDecodeError, KeyError):
            pass
    return done


def _append_entry(log_path: Path, entry: dict[str, Any]) -> None:
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def _print_summary(cond: str, log_path: Path) -> None:
    entries: list[dict[str, Any]] = []
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    commentary_entries = [e for e in entries if e.get("has_commentary")]
    k = sum(1 for e in commentary_entries if e.get("is_fenced"))
    n = len(commentary_entries)

    print(f"\n=== fence_emission_rate summary (cond={cond}) ===")
    print(f"  total logged entries : {len(entries)}")
    print(f"  commentary-bearing   : {n}")
    print(f"  fenced               : {k}")

    if n == 0:
        print("  fence_emission_rate  : n/a (no commentary-bearing outputs logged)")
    else:
        rate = k / n
        lo, hi = wilson_ci(k, n)
        print(f"  fence_emission_rate  : {rate:.3f}  ({k}/{n})")
        print(f"  Wilson 95% CI        : [{lo:.3f}, {hi:.3f}]")

    if cond == "off":
        print(
            "\n  NOTE (OFF condition): has_commentary is a LOWER BOUND here.\n"
            "  When the directive is off the model may emit unfenced free-form notes\n"
            "  that parse_skill_output does NOT strip; those notes merge into final\n"
            "  and are NOT counted as trailing commentary. Real unfenced-leak rate\n"
            "  >= measured. Treat the commentary-bearing count above as a floor."
        )


# ---------------------------------------------------------------------------
# Self-test (zero quota)
# ---------------------------------------------------------------------------

def _selftest() -> None:  # noqa: C901
    """Run detection-helper + Wilson CI assertions. No claude call, no network."""
    errors: list[str] = []

    # --- is_fenced ---
    raw_fenced = "body\n\n<!--HUMANIZER-AUDIT-->\nnote"
    raw_plain = "body only"
    if not is_fenced(raw_fenced):
        errors.append("is_fenced: expected True for fenced raw")
    if is_fenced(raw_plain):
        errors.append("is_fenced: expected False for plain raw")

    # --- has_commentary (trailing-region detector) ---
    # Case 1: fenced note AFTER body -> trailing region is non-empty -> True
    if not has_commentary(
        raw="REWRITE BODY HERE.\n\n<!--HUMANIZER-AUDIT-->\nnote",
        final="REWRITE BODY HERE.",
    ):
        errors.append(
            "has_commentary: expected True when fenced note trails the rewrite body"
        )
    # Case 2: banner BEFORE body only -> no trailing text -> False.
    # This is the case the old raw-vs-final-length check got wrong:
    # parse_skill_output strips the banner from final, making raw > final
    # even though there is zero trailing commentary.
    if has_commentary(
        raw="**Final rewrite:**\nREWRITE BODY HERE.",
        final="REWRITE BODY HERE.",
    ):
        errors.append(
            "has_commentary: expected False for pre-rewrite banner (no trailing commentary)"
        )
    # Case 3: raw == final -> False
    if has_commentary("REWRITE BODY HERE.", "REWRITE BODY HERE."):
        errors.append("has_commentary: expected False when raw == final")

    # --- Wilson fallback ---
    k, n = 7, 10
    lo_fallback, hi_fallback = _wilson_ci(k, n)
    if not (0.3 <= lo_fallback <= 0.5):
        errors.append(
            f"Wilson fallback lower bound {lo_fallback:.4f} not in [0.3, 0.5]"
        )

    # Compare with statsmodels if available
    try:
        from statsmodels.stats.proportion import proportion_confint  # type: ignore
        lo_sm, hi_sm = proportion_confint(k, n, alpha=0.05, method="wilson")
        diff_lo = abs(lo_fallback - float(lo_sm))
        diff_hi = abs(hi_fallback - float(hi_sm))
        if diff_lo > 0.01 or diff_hi > 0.01:
            errors.append(
                f"Wilson fallback diverges from statsmodels by >{0.01:.2f}: "
                f"fallback=({lo_fallback:.4f},{hi_fallback:.4f}) "
                f"sm=({lo_sm:.4f},{hi_sm:.4f})"
            )
    except ImportError:
        pass  # statsmodels not present — skip comparison, fallback already tested

    # --- Confirm no claude call happens in selftest ---
    # (structural check: run_skill is imported but NOT called in this branch;
    # the probe loop is gated on args.selftest being False — verified by code path)

    if errors:
        print("SELFTEST FAILED:")
        for e in errors:
            print(f"  ERROR: {e}")
        sys.exit(1)

    print("SELFTEST OK")
    sys.exit(0)


# ---------------------------------------------------------------------------
# Main probe loop
# ---------------------------------------------------------------------------

def main() -> None:  # noqa: C901
    parser = argparse.ArgumentParser(
        description="Measure fence_emission_rate for the humanizer skill commentary fence."
    )
    parser.add_argument(
        "--cond",
        choices=["on", "off"],
        help=(
            "Required (unless --selftest). Tag results with fence directive ON or OFF. "
            "Operator toggles the directive via git checkout between runs."
        ),
    )
    parser.add_argument(
        "reps",
        nargs="?",
        type=int,
        default=5,
        metavar="REPS",
        help="Number of repetitions per input (default: 5).",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help=(
            "Run zero-quota self-tests (detection helpers + Wilson CI). "
            "Does NOT call run_skill or claude."
        ),
    )
    args = parser.parse_args()

    if args.selftest:
        _selftest()
        return  # _selftest exits; this is unreachable but explicit

    if args.cond is None:
        parser.error("--cond {on|off} is required when not using --selftest")

    cond: str = args.cond
    reps: int = args.reps
    log_path = _log_path(cond)
    done = _load_done(log_path)

    print(f"[fence_probe] cond={cond}, reps={reps}, log={log_path}")
    print(f"[fence_probe] already done: {len(done)} entries (resumable)")

    total_attempted = 0
    total_skipped = 0
    total_errors = 0

    for input_id, cfg in INPUTS.items():
        for rep in range(1, reps + 1):
            key = (input_id, rep)
            if key in done:
                total_skipped += 1
                continue

            total_attempted += 1
            text: str = cfg["text"]
            lang: str = cfg["lang"]
            domain: str = cfg["domain"]
            print(
                f"  [{input_id} rep={rep}/{reps}] calling run_skill "
                f"(lang={lang}, domain={domain}) ...",
                flush=True,
            )

            try:
                raw, parsed = run_skill(
                    text,
                    lang=lang,
                    mode="full",
                    domain=domain,
                    return_raw=True,
                )
            except Exception as exc:
                print(f"  ERROR: run_skill failed for {input_id} rep={rep}: {exc}")
                total_errors += 1
                continue

            if parsed is None:
                print(f"  WARN: parsed is None for {input_id} rep={rep}, skipping")
                total_errors += 1
                continue

            final_text = parsed.get("final") or ""

            _is_fenced = is_fenced(raw)
            _has_commentary = has_commentary(raw, final_text)

            entry: dict[str, Any] = {
                "id": input_id,
                "rep": rep,
                "cond": cond,
                "has_commentary": _has_commentary,
                "is_fenced": _is_fenced,
                "final": final_text,
            }
            _append_entry(log_path, entry)
            print(
                f"    -> has_commentary={_has_commentary}, is_fenced={_is_fenced}"
            )

    print(
        f"\n[fence_probe] done. attempted={total_attempted}, "
        f"skipped={total_skipped}, errors={total_errors}"
    )
    _print_summary(cond, log_path)


if __name__ == "__main__":
    main()
