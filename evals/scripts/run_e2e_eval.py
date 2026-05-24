"""End-to-end eval runner — judge-LLM scored rewrite quality.

For each AI input in evals/corpus/{lang}/e2e/, run the skill, then ask a
judge LLM to score the rewrite on human-ness, meaning preservation, and
length appropriateness. Each case is run 3 times to capture both skill
sampling and judge noise; thresholds apply to the mean across runs.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

from anthropic import Anthropic

from evals.scripts._shared import (
    run_skill,
    verify_skill_install,
    write_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
JUDGE_PROMPT_PATH = REPO_ROOT / "evals" / "scripts" / "judge_prompt.md"

DEFAULT_RUNS = 3
DEFAULT_THRESHOLDS = {"human_ness": 7.5, "meaning": 9.0, "length": 7.0}


# Anthropic tool schema for structured judge scoring
_REPORT_SCORES_TOOL = {
    "name": "report_scores",
    "description": "Report the three judge scores for one rewrite.",
    "input_schema": {
        "type": "object",
        "properties": {
            "human_ness": {"type": "integer", "minimum": 1, "maximum": 10},
            "meaning": {"type": "integer", "minimum": 1, "maximum": 10},
            "length": {"type": "integer", "minimum": 1, "maximum": 10},
            "rationale": {
                "type": "object",
                "properties": {
                    "human_ness": {"type": "string"},
                    "meaning": {"type": "string"},
                    "length": {"type": "string"},
                },
                "required": ["human_ness", "meaning", "length"],
            },
        },
        "required": ["human_ness", "meaning", "length", "rationale"],
    },
}


def _model_to_api_id(model: str) -> str:
    """Map short names ('sonnet', 'opus') to current API IDs per repo conventions."""
    mapping = {
        "sonnet": "claude-sonnet-4-6",
        "opus": "claude-opus-4-7",
        "haiku": "claude-haiku-4-5-20251001",
    }
    return mapping.get(model, model)


def _call_judge(
    *,
    judge_model: str,
    input_text: str,
    rewrite: str,
    domain: str,
) -> dict:
    """Single judge call. Returns parsed scores dict."""
    client = Anthropic()
    system_prompt = JUDGE_PROMPT_PATH.read_text(encoding="utf-8")
    user_msg = (
        f"Domain: {domain}\n\n"
        f"## ORIGINAL AI INPUT\n\n{input_text}\n\n"
        f"## SKILL REWRITE\n\n{rewrite}\n\n"
        "Reason briefly, then call report_scores."
    )
    response = client.messages.create(
        model=_model_to_api_id(judge_model),
        max_tokens=1024,
        system=system_prompt,
        tools=[_REPORT_SCORES_TOOL],
        tool_choice={"type": "tool", "name": "report_scores"},
        messages=[{"role": "user", "content": user_msg}],
    )
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "report_scores":
            return dict(block.input)
    raise RuntimeError("judge LLM did not call report_scores tool")


def score_case(
    case: dict, *, runs: int = DEFAULT_RUNS, model: str = "sonnet", judge_model: str = "sonnet"
) -> dict:
    """Run skill+judge `runs` times on one case and aggregate mean+stddev."""
    run_results = []
    for run_idx in range(runs):
        skill_out = run_skill(
            case["input"],
            lang=case.get("lang", "en"),
            mode="full",
            domain=case.get("domain"),
            model=model,
        )
        rewrite = skill_out.get("final") or skill_out.get("draft") or ""
        scores = _call_judge(
            judge_model=judge_model,
            input_text=case["input"],
            rewrite=rewrite,
            domain=case.get("domain", "casual"),
        )
        scores["rewrite_length_words"] = len(rewrite.split())
        run_results.append(scores)

    def _mean(key: str) -> float:
        return round(statistics.fmean(r[key] for r in run_results), 3)

    def _stddev(key: str) -> float:
        if runs < 2:
            return 0.0
        return round(statistics.stdev(r[key] for r in run_results), 3)

    return {
        "case_id": case["id"],
        "domain": case.get("domain"),
        "runs": run_results,
        "mean": {k: _mean(k) for k in ("human_ness", "meaning", "length")},
        "stddev": {k: _stddev(k) for k in ("human_ness", "meaning", "length")},
    }


def run(
    lang: str = "en",
    domain: str | None = None,
    runs: int = DEFAULT_RUNS,
    model: str = "sonnet",
    judge_model: str = "sonnet",
) -> dict:
    verify_skill_install()
    corpus_dir = REPO_ROOT / "evals" / "corpus" / lang / "e2e"
    case_files = sorted(corpus_dir.glob("*.json"))

    per_case = []
    for path in case_files:
        case = json.loads(path.read_text(encoding="utf-8"))
        if domain and case.get("domain") != domain:
            continue
        per_case.append(score_case(case, runs=runs, model=model, judge_model=judge_model))

    overall = {}
    if per_case:
        for k in ("human_ness", "meaning", "length"):
            overall[k] = round(
                statistics.fmean(c["mean"][k] for c in per_case), 3
            )

    return {
        "eval_type": "e2e",
        "lang": lang,
        "model": model,
        "judge_model": judge_model,
        "runs_per_case": runs,
        "thresholds": DEFAULT_THRESHOLDS,
        "summary": {
            "overall_mean": overall,
            "total_cases": len(per_case),
            "below_threshold_count": sum(
                1 for c in per_case
                if c["mean"]["human_ness"] < DEFAULT_THRESHOLDS["human_ness"]
            ),
        },
        "per_case": per_case,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="E2E rewrite-quality eval runner.")
    parser.add_argument("--lang", default="en")
    parser.add_argument("--domain", default=None)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument(
        "--judge-model", default="sonnet",
        help="Short name (sonnet, opus) or full API ID",
    )
    args = parser.parse_args()

    report = run(
        lang=args.lang,
        domain=args.domain,
        runs=args.runs,
        model=args.model,
        judge_model=args.judge_model,
    )
    json_path, md_path = write_report(f"e2e_{args.lang}", report)
    print(f"Wrote {json_path.name} and {md_path.name}")
    print(f"Overall mean: {report['summary']['overall_mean']}")


if __name__ == "__main__":
    main()
