"""DE AI corpus generator — Source B: Claude CLI subscription generation.

Generates DE AI corpus samples via `claude -p` subprocess calls (subscription
auth, not API-key). Zero API spend. Vary model for cross-model idiolect diversity.

Six domain prompt templates × 5 topics × 3 models = 90 samples target.

Output layout:
    evals/corpus/de/ai/claude_cli/<domain>/<model>/sample_NN.md

Each file has YAML frontmatter: domain, model, topic, generated_via, generated_date.

Usage:
    python -m evals.scripts.generate_de_ai_corpus_cli --dry-run
    python -m evals.scripts.generate_de_ai_corpus_cli --domains all --models all
    python -m evals.scripts.generate_de_ai_corpus_cli --domains casual,academic --models sonnet
    python -m evals.scripts.generate_de_ai_corpus_cli --samples-per-combo 2 --dry-run
    python -m evals.scripts.generate_de_ai_corpus_cli --continue

Subprocess env-strip pattern (load-bearing):
    cli_env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
This ensures subscription auth is used even when ANTHROPIC_API_KEY is set in
the parent env (needed by E2E SDK calls). Mirrors the pattern in _shared.run_skill().

Stdlib only. Python 3.10+.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TODAY = date.today().isoformat()

_DEFAULT_OUT_DIR = Path("evals") / "corpus" / "de" / "ai" / "claude_cli"

_DEFAULT_TIMEOUT = 120  # seconds per generation call

_ALL_DOMAINS = ["casual", "academic", "legal", "technical", "marketing", "career"]

_ALL_MODELS = ["sonnet", "haiku", "opus"]

# ---------------------------------------------------------------------------
# Domain prompt templates
# Each template has a [TOPIC] or [POSITION] placeholder.
# The prompts explicitly ask for stereotypical AI-style content so the output
# is useful for pattern detection — this is the AI side of the eval corpus.
# ---------------------------------------------------------------------------

PROMPT_TEMPLATES: dict[str, str] = {
    "casual": (
        "Schreibe einen typischen KI-generierten Blogartikel (~200 Wörter) über das Thema [TOPIC]. "
        "Verwende dabei alle stereotypen KI-Stilmerkmale: Überleitungswörter wie 'darüber hinaus', "
        "'es ist wichtig zu beachten', 'zusammenfassend lässt sich sagen'; Substantivketten; "
        "Hedging-Formulierungen; dreigliedrige Aufzählungen; übertriebene Adjektive. "
        "Schreibe auf Deutsch."
    ),
    "academic": (
        "Schreibe einen typischen KI-generierten Abstract (~150 Wörter) zu einer akademischen Studie "
        "über [TOPIC]. Verwende dabei alle KI-Stilmerkmale: Passivkonstruktionen, Substantivierungen, "
        "Hedging ('es scheint', 'es lässt sich feststellen'), formelle Übergänge, "
        "dreigliedrige Strukturen, übermäßige Nominalstil. Schreibe auf Deutsch."
    ),
    "legal": (
        "Schreibe eine typische KI-generierte Vertragsklausel (~150 Wörter) zum Thema [TOPIC]. "
        "Verwende dabei alle KI-Stilmerkmale für juristische Texte: Substantivketten, "
        "Passivkonstruktionen, Aufzählungen in drei Punkten, formelle Übergänge wie "
        "'im Rahmen der vorliegenden Vereinbarung', 'gemäß den geltenden Vorschriften', "
        "übermäßige Nominalstil. Schreibe auf Deutsch."
    ),
    "technical": (
        "Schreibe ein typisches KI-generiertes README-Intro (~200 Wörter) für ein Software-Projekt "
        "zum Thema [TOPIC]. Verwende dabei alle KI-Stilmerkmale: Aufzählungen in drei Punkten, "
        "übertriebene Adjektive ('robust', 'skalierbar', 'intuitiv'), Passivkonstruktionen, "
        "Hedging, formelle Übergänge, Substantivketten. Schreibe auf Deutsch."
    ),
    "marketing": (
        "Schreibe einen typischen KI-generierten Werbetext (~200 Wörter) für ein Produkt [TOPIC]. "
        "Verwende dabei alle stereotypen KI-Stilmerkmale: übertriebene Adjektive, "
        "dreigliedrige Aufzählungen, Substantivketten, Hedging, formelle Übergänge wie "
        "'darüber hinaus', 'nicht zuletzt', 'zusammenfassend lässt sich sagen', "
        "Superlative und Begeisterungsformeln. Schreibe auf Deutsch."
    ),
    "career": (
        "Schreibe ein typisches KI-generiertes Bewerbungsanschreiben (~200 Wörter) für eine "
        "Stelle als [POSITION]. Verwende dabei alle stereotypen KI-Stilmerkmale für Anschreiben: "
        "'Sehr geehrte Damen und Herren', 'Mit großem Interesse habe ich Ihre Stellenanzeige gelesen', "
        "'Ich bin überzeugt, dass ich genau die richtige Person für diese Position bin', "
        "dreigliedrige Aufzählungen der Stärken, Hedging, formelle Übergänge, "
        "Substantivketten, abgedroschene Floskeln. Schreibe auf Deutsch."
    ),
}

# ---------------------------------------------------------------------------
# Domain topics (5 per domain — shuffled via fixed seed per domain at generation time)
# ---------------------------------------------------------------------------

DOMAIN_TOPICS: dict[str, list[str]] = {
    "casual": [
        "Homeoffice und Work-Life-Balance",
        "Nachhaltiges Reisen",
        "Digitale Gesundheits-Apps",
        "Minimalismus im Alltag",
        "Soziale Medien und Wohlbefinden",
    ],
    "academic": [
        "Klimawandel und Biodiversität",
        "Künstliche Intelligenz in der Medizin",
        "Soziale Ungleichheit in Bildungssystemen",
        "Quantencomputing und Kryptographie",
        "Urbanisierung und mentale Gesundheit",
    ],
    "legal": [
        "Datenschutz bei Cloud-Diensten",
        "Haftung bei autonomen Fahrzeugen",
        "Urheberrecht an KI-generierten Werken",
        "Verbraucherschutz im E-Commerce",
        "Arbeitsrecht beim Homeoffice",
    ],
    "technical": [
        "automatisierten Datenpipeline",
        "Microservices-Architektur",
        "Open-Source-Monitoring-Lösung",
        "Machine-Learning-Plattform",
        "DevOps-Automatisierungswerkzeug",
    ],
    "marketing": [
        "ergonomischer Bürostuhl",
        "vegane Proteinriegel",
        "intelligenter Lautsprecher",
        "nachhaltige Sportkleidung",
        "digitaler Sprachkurs",
    ],
    "career": [
        "Softwareentwicklerin",
        "Projektmanager im Bereich Nachhaltigkeit",
        "Data Scientist",
        "UX-Designerin",
        "Marketingmanager bei einem Startup",
    ],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_prompt(domain: str, topic: str) -> str:
    """Fill the [TOPIC] / [POSITION] placeholder in the domain template."""
    template = PROMPT_TEMPLATES[domain]
    return template.replace("[TOPIC]", topic).replace("[POSITION]", topic)


def _find_claude() -> str | None:
    """Return the path to the `claude` CLI, or None if not found."""
    return shutil.which("claude")


def _strip_api_key_env() -> dict[str, str]:
    """Build subprocess env with ANTHROPIC_API_KEY removed.

    This forces the claude CLI to use subscription (OAuth) auth instead of
    API-key auth. Required per the _shared.run_skill convention.
    """
    return {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}


def _sample_path(out_dir: Path, domain: str, model: str, idx: int) -> Path:
    """Return the path for sample_NN.md within out_dir/<domain>/<model>/."""
    return out_dir / domain / model / f"sample_{idx:02d}.md"


def _render_frontmatter(
    domain: str,
    model: str,
    topic: str,
    sample_idx: int,
    generated_date: str,
) -> str:
    """Render YAML frontmatter for a generated sample."""
    # Minimal inline YAML escaper
    def _ys(v: Any) -> str:
        s = str(v)
        if any(c in s for c in ':#{}[]|>&*!,\'"') or "\n" in s:
            s = s.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{s}"'
        return s

    lines = [
        "---",
        f"domain: {_ys(domain)}",
        f"model: {_ys(model)}",
        f"topic: {_ys(topic)}",
        f"sample_index: {sample_idx}",
        f"generated_via: claude -p subscription",
        f"generated_date: {_ys(generated_date)}",
        f"license_class: redistributable",
        "---",
    ]
    return "\n".join(lines)


def _write_sample(
    path: Path,
    text: str,
    domain: str,
    model: str,
    topic: str,
    sample_idx: int,
    generated_date: str,
) -> None:
    """Write a generated sample file with YAML frontmatter."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = _render_frontmatter(domain, model, topic, sample_idx, generated_date)
    content = f"{fm}\n\n{text.strip()}\n"
    path.write_text(content, encoding="utf-8")


def _write_sidecars(out_dir: Path, domain: str, model: str) -> None:
    """Write _LICENSE and _SOURCE sidecar files for a domain/model combination."""
    target = out_dir / domain / model
    target.mkdir(parents=True, exist_ok=True)

    lic_text = (
        "MIT (we own the generation context)\n"
        "Samples generated via Anthropic Claude Pro subscription CLI\n"
        f"Generated: {TODAY}\n"
        "License class: redistributable\n"
        "Note: These samples are intentionally AI-styled for pattern eval use.\n"
    )
    (target / "_LICENSE").write_text(lic_text, encoding="utf-8")
    (target / "_SOURCE").write_text(
        f"source_name: claude_cli_{domain}_{model}\n"
        f"license_class: redistributable\n"
        f"license: MIT\n"
        f"generated_via: claude -p subscription\n"
        f"generated_date: {TODAY}\n"
        f"domain: {domain}\n"
        f"model: {model}\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Generation driver
# ---------------------------------------------------------------------------

def _generate_one(
    prompt: str,
    model: str,
    claude_path: str,
    timeout: int = _DEFAULT_TIMEOUT,
) -> str:
    """Call `claude -p <prompt> --model <model>` and return stdout text.

    Strips ANTHROPIC_API_KEY from subprocess env (subscription auth).
    Raises subprocess.CalledProcessError / subprocess.TimeoutExpired on failure.
    """
    cli_env = _strip_api_key_env()
    result = subprocess.run(
        [claude_path, "-p", prompt, "--model", model],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=cli_env,
    )
    if result.returncode != 0:
        stderr_snippet = result.stderr.strip()[:300] or "(empty)"
        raise subprocess.CalledProcessError(
            result.returncode,
            [claude_path, "-p", "…", "--model", model],
            output=result.stdout,
            stderr=stderr_snippet,
        )
    return result.stdout.strip()


def generate_corpus(
    *,
    domains: list[str],
    models: list[str],
    samples_per_combo: int,
    out_dir: Path,
    resume: bool = False,
    dry_run: bool = False,
    timeout: int = _DEFAULT_TIMEOUT,
) -> None:
    """Generate AI corpus samples for all domain × model × topic combos.

    Parameters
    ----------
    domains:
        List of domain names (subset of _ALL_DOMAINS).
    models:
        List of model names (subset of _ALL_MODELS).
    samples_per_combo:
        Number of topic samples per (domain, model) combo. Pulls from DOMAIN_TOPICS.
    out_dir:
        Root output directory (will create <domain>/<model>/ subdirs).
    resume:
        If True, skip combos where the sample file already exists.
    dry_run:
        If True, print plan without generating or writing anything.
    timeout:
        Per-generation subprocess timeout in seconds.
    """
    if dry_run:
        _dry_run_report(
            domains=domains,
            models=models,
            samples_per_combo=samples_per_combo,
            out_dir=out_dir,
            resume=resume,
        )
        return

    claude_path = _find_claude()
    if not claude_path:
        print(
            "[generate_de_ai_corpus_cli] ERROR: `claude` CLI not found in PATH. "
            "Install Claude Code and try again.",
            file=sys.stderr,
        )
        sys.exit(1)

    total = len(domains) * len(models) * samples_per_combo
    done = 0
    skipped = 0
    failed = 0

    for domain in domains:
        topics = DOMAIN_TOPICS[domain][:samples_per_combo]

        for model in models:
            _write_sidecars(out_dir, domain, model)

            for idx, topic in enumerate(topics):
                sample_path = _sample_path(out_dir, domain, model, idx + 1)
                done += 1

                if resume and sample_path.exists():
                    print(
                        f"[{done}/{total}] SKIP {domain}/{model}/sample_{idx+1:02d}.md "
                        f"(already exists, --continue mode)",
                        file=sys.stderr,
                    )
                    skipped += 1
                    continue

                prompt = _build_prompt(domain, topic)
                print(
                    f"[{done}/{total}] Generating {domain}/{model}/sample_{idx+1:02d}.md "
                    f"(topic: {topic!r}) …",
                    file=sys.stderr,
                )

                try:
                    text = _generate_one(prompt, model, claude_path, timeout=timeout)
                    if not text:
                        raise ValueError("Empty output from claude CLI")
                    _write_sample(
                        sample_path,
                        text,
                        domain=domain,
                        model=model,
                        topic=topic,
                        sample_idx=idx + 1,
                        generated_date=TODAY,
                    )
                    print(
                        f"  → Wrote {len(text.split())} words to {sample_path}",
                        file=sys.stderr,
                    )
                except subprocess.TimeoutExpired:
                    print(
                        f"  TIMEOUT after {timeout}s — skipping.",
                        file=sys.stderr,
                    )
                    failed += 1
                except subprocess.CalledProcessError as exc:
                    stderr_snippet = repr(exc.stderr)[:200]
                    print(
                        f"  FAILED (exit {exc.returncode}): {stderr_snippet}",
                        file=sys.stderr,
                    )
                    failed += 1
                except Exception as exc:  # noqa: BLE001
                    print(
                        f"  ERROR: {exc}",
                        file=sys.stderr,
                    )
                    failed += 1

    print(
        f"\n[generate_de_ai_corpus_cli] Done. "
        f"Generated: {done - skipped - failed} / Skipped: {skipped} / Failed: {failed}",
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# Dry-run report
# ---------------------------------------------------------------------------

def _dry_run_report(
    *,
    domains: list[str],
    models: list[str],
    samples_per_combo: int,
    out_dir: Path,
    resume: bool,
) -> None:
    total = len(domains) * len(models) * samples_per_combo
    print("=== generate_de_ai_corpus_cli — DRY RUN ===")
    print()
    print(f"Domains:          {', '.join(domains)}")
    print(f"Models:           {', '.join(models)}")
    print(f"Samples per combo:{samples_per_combo}")
    print(f"Total samples:    {total}")
    print(f"Out dir:          {out_dir}/")
    print(f"Resume (--continue): {resume}")
    print()
    print("Env strip: ANTHROPIC_API_KEY removed from subprocess env (subscription auth)")
    print()
    print("Generation plan:")
    n = 0
    for domain in domains:
        topics = DOMAIN_TOPICS[domain][:samples_per_combo]
        for model in models:
            for idx, topic in enumerate(topics):
                n += 1
                path = _sample_path(out_dir, domain, model, idx + 1)
                resume_note = " [SKIP if exists]" if resume else ""
                print(f"  [{n:3d}/{total}] {path}{resume_note}")
                print(f"         topic: {topic!r}")
    print()
    print(f"Estimated wall time: ~{total * 5 // 60}–{total * 10 // 60} min "
          f"({total} samples × 5–10s each)")
    print()
    print("License: MIT (we own the generation context)")
    print("API cost: $0 — claude CLI uses subscription auth (ANTHROPIC_API_KEY stripped)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_list_arg(value: str, choices: list[str], arg_name: str) -> list[str]:
    """Parse a comma-separated list arg. 'all' expands to *choices*."""
    if value == "all":
        return choices[:]
    parts = [p.strip() for p in value.split(",") if p.strip()]
    invalid = [p for p in parts if p not in choices]
    if invalid:
        raise argparse.ArgumentTypeError(
            f"--{arg_name}: unknown values {invalid}. "
            f"Valid: {choices} or 'all'."
        )
    return parts


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate_de_ai_corpus_cli",
        description=(
            "Generate DE AI corpus samples via `claude -p` subscription CLI. "
            "Source B of the zero-budget DE AI corpus. "
            "Writes to evals/corpus/de/ai/claude_cli/<domain>/<model>/sample_NN.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m evals.scripts.generate_de_ai_corpus_cli --dry-run\n"
            "  python -m evals.scripts.generate_de_ai_corpus_cli\n"
            "  python -m evals.scripts.generate_de_ai_corpus_cli --domains casual,academic --models sonnet\n"
            "  python -m evals.scripts.generate_de_ai_corpus_cli --samples-per-combo 2\n"
            "  python -m evals.scripts.generate_de_ai_corpus_cli --continue\n"
        ),
    )
    parser.add_argument(
        "--domains",
        default="all",
        metavar="DOMAINS",
        help=(
            f"Comma-separated domain list or 'all' (default: all). "
            f"Valid: {', '.join(_ALL_DOMAINS)}."
        ),
    )
    parser.add_argument(
        "--models",
        default="all",
        metavar="MODELS",
        help=(
            f"Comma-separated model list or 'all' (default: all). "
            f"Valid: {', '.join(_ALL_MODELS)}."
        ),
    )
    parser.add_argument(
        "--samples-per-combo",
        type=int,
        default=5,
        metavar="N",
        help=(
            "Number of topic samples per (domain, model) combo (default: 5). "
            "5 topics × 3 models × 6 domains = 90 total at default."
        ),
    )
    parser.add_argument(
        "--out-dir",
        default=str(_DEFAULT_OUT_DIR),
        metavar="DIR",
        help=f"Root output directory (default: {_DEFAULT_OUT_DIR}).",
    )
    parser.add_argument(
        "--continue",
        dest="resume",
        action="store_true",
        help=(
            "Skip combos where sample file already exists. "
            "Use to resume a partial run without re-generating completed samples."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=_DEFAULT_TIMEOUT,
        metavar="SECONDS",
        help=f"Per-sample generation timeout in seconds (default: {_DEFAULT_TIMEOUT}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generation plan without making subprocess calls or writing files.",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Parse domains and models (may raise SystemExit via argparse error)
    try:
        domains = _parse_list_arg(args.domains, _ALL_DOMAINS, "domains")
        models = _parse_list_arg(args.models, _ALL_MODELS, "models")
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
        return  # unreachable; parser.error raises SystemExit

    out_dir = Path(args.out_dir)

    generate_corpus(
        domains=domains,
        models=models,
        samples_per_combo=args.samples_per_combo,
        out_dir=out_dir,
        resume=args.resume,
        dry_run=args.dry_run,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
