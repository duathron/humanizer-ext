# SP3a — Multi-run-median eval harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. **Review rule (maintainer): no self-review — every task diff + the `aggregate_runs` semantics + any eval number is verified by the independent Skeptic (`AI/AGENT PERSONAS/Agents/independent-review-agent.md`) from primary evidence before acceptance.**

**Goal:** Make `run_pattern_eval` and `run_false_positive_eval` multi-run (`--runs N`, default 5) with median/majority aggregation, so a skill-behavior fix's effect is distinguishable from run-to-run noise (the thing SP1 couldn't measure).

**Architecture:** A pure `aggregate_runs()` in `_shared.py` (median for continuous, majority for binary, inconclusive when <⌈N/2⌉ runs succeed) is the no-drift core. Each runner's `score_case`/`score_human_text` runs the skill N times per case/file (per-run try/except with a session-limit carve-out → re-raise; non-session failure → `None` run), stores `runs:[...]` in the per-case partial, and aggregates via `aggregate_runs`. `run_e2e_eval` is NOT touched (already multi-run).

**Tech Stack:** Python 3.11 stdlib (`statistics`, `math`) + pytest. No new deps. Evals call `claude -p` (subscription) — but every task here is unit-tested with `run_skill`/`score_*` monkeypatched, **zero quota**. One optional final live smoke is quota-gated.

**Spec:** `docs/specs/2026-06-08-sp3a-multirun-harness-design.md` (Skeptic-approved, round 4). 

**Branch:** in-place on `sp3a-multirun-harness` (off `main`).

---

## File structure

| File | Responsibility | Tasks |
|---|---|---|
| `evals/scripts/_shared.py` | NEW pure `aggregate_runs()` — the shared aggregation policy | 1 |
| `tests/test_evals_shared.py` | unit-test `aggregate_runs` | 1 |
| `evals/scripts/run_pattern_eval.py` | `--runs`; `score_case` runs N times; multi-run summary | 2 |
| `tests/test_run_pattern_eval.py` | pattern multi-run tests + re-point stale timeout test | 2 |
| `evals/scripts/run_false_positive_eval.py` | `--runs`; `score_human_text` runs N times; median verdict | 3 |
| `tests/test_false_positive_eval.py` | FP multi-run tests + re-point stale timeout test | 3 |

---

## Task 1: `aggregate_runs` pure function (`_shared.py`)

**Files:**
- Modify: `evals/scripts/_shared.py` (add the function + `import math`; `import statistics` may already exist — check the top of the file and only add what's missing)
- Test: `tests/test_evals_shared.py`

- [ ] **Step 1: Write the failing tests** — append to `tests/test_evals_shared.py`:

```python
def test_aggregate_runs_continuous_median_verdict():
    from evals.scripts._shared import aggregate_runs
    # 3 of 5 under 0.10; median = 0.08 <= 0.10 -> verdict True
    r = aggregate_runs([0.02, 0.05, 0.08, 0.40, 0.50], threshold=0.10,
                       kind="continuous", n_target=5)
    assert r["verdict"] is True
    assert r["median"] == 0.08
    assert r["fraction"] is None
    assert r["passed_fraction"] == "3/5"   # count <= threshold
    assert r["inconclusive"] is False
    assert r["flaky"] is True               # successes straddle the threshold


def test_aggregate_runs_continuous_passed_fraction_can_disagree_with_verdict():
    from evals.scripts._shared import aggregate_runs
    # 2/5 under threshold, but median (0.11) is OVER -> verdict False, k=2
    r = aggregate_runs([0.05, 0.06, 0.11, 0.12, 0.13], threshold=0.10,
                       kind="continuous", n_target=5)
    assert r["verdict"] is False
    assert r["median"] == 0.11
    assert r["passed_fraction"] == "2/5"


def test_aggregate_runs_continuous_not_flaky_when_all_one_side():
    from evals.scripts._shared import aggregate_runs
    r = aggregate_runs([0.02, 0.03, 0.04, 0.05, 0.06], threshold=0.10,
                       kind="continuous", n_target=5)
    assert r["flaky"] is False
    assert r["verdict"] is True


def test_aggregate_runs_binary_majority_and_fraction():
    from evals.scripts._shared import aggregate_runs
    # 3/5 detected -> majority True, fraction 0.6
    r = aggregate_runs([1.0, 1.0, 1.0, 0.0, 0.0], kind="binary", n_target=5)
    assert r["verdict"] is True            # majority
    assert r["fraction"] == 0.6            # the stability signal
    assert r["median"] is None
    assert r["passed_fraction"] == "3/5"
    assert r["flaky"] is True              # runs disagreed


def test_aggregate_runs_binary_unanimous_not_flaky():
    from evals.scripts._shared import aggregate_runs
    r = aggregate_runs([1.0, 1.0, 1.0, 1.0, 1.0], kind="binary", n_target=5)
    assert r["verdict"] is True
    assert r["fraction"] == 1.0
    assert r["flaky"] is False


def test_aggregate_runs_inconclusive_when_too_few_succeed():
    from evals.scripts._shared import aggregate_runs
    # only 2 successes out of n_target 5 (3 None) -> inconclusive, verdict None
    r = aggregate_runs([0.02, 0.05, None, None, None], threshold=0.10,
                       kind="continuous", n_target=5)
    assert r["inconclusive"] is True
    assert r["verdict"] is None
    assert r["flaky"] is False             # inconclusive is not separately flaky
    assert r["n_success"] == 2
    assert r["n_fail"] == 3


def test_aggregate_runs_all_failed_is_inconclusive():
    from evals.scripts._shared import aggregate_runs
    r = aggregate_runs([None, None, None, None, None], threshold=0.10,
                       kind="continuous", n_target=5)
    assert r["inconclusive"] is True
    assert r["verdict"] is None
    assert r["median"] is None
    assert r["passed_fraction"] == "0/0"
```

- [ ] **Step 2: Run them, verify failure** — `PYTHONPATH=. python3 -m pytest tests/test_evals_shared.py -k aggregate_runs -q` → FAIL (`ImportError: cannot import name 'aggregate_runs'`).

- [ ] **Step 3: Implement** — add to `evals/scripts/_shared.py` (check imports first; add `import math` and `import statistics` only if absent):

```python
def aggregate_runs(
    values: list,
    *,
    kind: str,
    n_target: int,
    threshold: float | None = None,
) -> dict:
    """Aggregate per-run outcomes for ONE case/file into a stable verdict.

    `values`: per-run outcomes; `None` = a failed/timed-out run (excluded).
    `kind="continuous"`: values are floats (e.g. edit_ratio). verdict = median <= threshold.
    `kind="binary"`:     values are 1.0/0.0 (e.g. detected). verdict = majority of successes.
    Inconclusive when fewer than ceil(n_target/2) runs succeed -> verdict None.

    Returns a fixed-shape dict; the unused fields per kind are None. See the spec
    (docs/specs/2026-06-08-sp3a-multirun-harness-design.md, Component 1).
    """
    successes = [v for v in values if v is not None]
    n_success = len(successes)
    n_fail = len(values) - n_success
    inconclusive = n_success < math.ceil(n_target / 2)

    if kind == "continuous":
        if threshold is None:
            raise ValueError("continuous kind requires a threshold")
        median = round(statistics.median(successes), 4) if n_success else None
        k = sum(1 for v in successes if v <= threshold)
        fraction = None
        verdict = None if inconclusive else (median is not None and median <= threshold)
        flaky = (
            not inconclusive and n_success > 0
            and min(successes) <= threshold < max(successes)
        )
    elif kind == "binary":
        k = sum(1 for v in successes if v == 1.0)
        fraction = round(k / n_success, 4) if n_success else None
        median = None
        majority = (k >= math.ceil(n_success / 2)) if n_success else False
        verdict = None if inconclusive else majority
        flaky = not inconclusive and 0 < k < n_success
    else:
        raise ValueError(f"unknown kind: {kind!r}")

    return {
        "verdict": verdict,
        "median": median,
        "fraction": fraction,
        "passed_fraction": f"{k}/{n_success}",
        "n_success": n_success,
        "n_fail": n_fail,
        "inconclusive": inconclusive,
        "flaky": flaky,
    }
```

- [ ] **Step 4: Run tests** — `PYTHONPATH=. python3 -m pytest tests/test_evals_shared.py -k aggregate_runs -q` → PASS. Then full suite `PYTHONPATH=. python3 -m pytest -q` → ≥306 + 7 new, zero regressions.

- [ ] **Step 5: Commit**

```bash
git add evals/scripts/_shared.py tests/test_evals_shared.py
git commit -m "feat(evals): pure aggregate_runs() — median/majority/inconclusive core (SP3a Task 1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 6: Skeptic review** the diff: do the continuous/binary branches match the spec contract exactly (verdict/median/fraction/k/flaky per kind; inconclusive threshold ⌈N/2⌉; flaky excludes inconclusive)? Edge cases (n_success=1, all-equal, threshold-equal, empty)? Fix findings, re-verify.

---

## Task 2: `run_pattern_eval` multi-run

**Files:**
- Modify: `evals/scripts/run_pattern_eval.py` (`score_case`, `run()`, `main()`, `--runs` arg)
- Test: `tests/test_run_pattern_eval.py`

The refactor: extract the current single-run body of `score_case` into `_score_case_once(case, *, model, force_full)` (verbatim move — it already returns the per-run dict). `score_case` becomes the multi-run wrapper. Unscorable categories (which never call `run_skill`) are decided ONCE without multi-run.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_run_pattern_eval.py` (reuse the file's existing `_write_pattern_file`, `PATTERN_MODULE`, `_corpus_dir_override`/`_partial_dir_override` helpers):

```python
def test_pattern_score_case_runs_n_times_and_aggregates_detection(monkeypatch):
    """score_case runs the skill N times; detected = majority; partial carries runs[]."""
    import evals.scripts.run_pattern_eval as pat
    from evals.scripts._shared import Case
    # 3 of 5 runs remove the tell -> majority detected True, fraction 0.6
    outs = iter([
        {"final": "clean"},            # removed -> detected
        {"final": "clean"},            # removed
        {"final": "clean"},            # removed
        {"final": "still aiword here"},# retained -> not detected
        {"final": "still aiword here"},# retained
    ])
    monkeypatch.setattr(pat, "run_skill", lambda *a, **k: next(outs))
    case = Case(id="p1_en_001", input="aiword here", expected_changes=["aiword"],
                domain="casual", true_negative=False, expected_unchanged=[], metadata={"pattern_id": 1, "lang": "en"})
    score = pat.score_case(case, model="sonnet", force_full=True, runs=5)
    assert len(score["runs"]) == 5
    assert score["detected"] is True                  # majority verdict
    assert score["aggregate"]["fraction"] == 0.6      # stability signal
    assert score["status"] == "scored"


def test_pattern_score_case_true_negative_uses_median_edit_ratio(monkeypatch):
    import evals.scripts.run_pattern_eval as pat
    from evals.scripts._shared import Case
    inp = "This is a clean human sentence that should be left alone entirely."
    # 3 runs ~unchanged (low ratio), 2 heavily edited -> median low -> passes
    outs = iter([
        {"final": inp}, {"final": inp}, {"final": inp},
        {"final": "totally different rewritten text"},
        {"final": "totally different rewritten text"},
    ])
    monkeypatch.setattr(pat, "run_skill", lambda *a, **k: next(outs))
    case = Case(id="p8_en_001", input=inp, expected_changes=[], expected_unchanged=[],
                domain="casual", true_negative=True, metadata={"pattern_id": 8, "lang": "en"})
    score = pat.score_case(case, model="sonnet", force_full=False, runs=5)
    assert score["status"] == "true_negative"
    assert score["passes_true_negative"] is True      # median edit_ratio <= 0.10
    assert score["aggregate"]["flaky"] is True         # runs straddled the threshold


def test_pattern_score_case_session_limit_propagates(monkeypatch):
    """A session-limit error mid-case must propagate (quota guard), not become a None run."""
    import evals.scripts.run_pattern_eval as pat
    from evals.scripts._shared import Case, SkillRunError
    def boom(*a, **k):
        raise SkillRunError("Claude usage limit reached — session limit")
    monkeypatch.setattr(pat, "run_skill", boom)
    case = Case(id="p1_en_001", input="aiword here", expected_changes=["aiword"],
                domain="casual", true_negative=False, expected_unchanged=[], metadata={"pattern_id": 1, "lang": "en"})
    with pytest.raises(SkillRunError):
        pat.score_case(case, model="sonnet", force_full=True, runs=5)


def test_pattern_score_case_nonsession_failure_becomes_none_run(monkeypatch):
    """A non-session failure on one run becomes a None run; the case is NOT aborted."""
    import evals.scripts.run_pattern_eval as pat
    from evals.scripts._shared import Case, SkillRunError
    seq = iter([
        {"final": "clean"},                      # detected
        SkillRunError("transient CLI exit 1"),   # non-session -> None run
        {"final": "clean"},                      # detected
        {"final": "clean"},                      # detected
        {"final": "clean"},                      # detected
    ])
    def maybe(*a, **k):
        x = next(seq)
        if isinstance(x, Exception):
            raise x
        return x
    monkeypatch.setattr(pat, "run_skill", maybe)
    case = Case(id="p1_en_001", input="aiword here", expected_changes=["aiword"],
                domain="casual", true_negative=False, expected_unchanged=[], metadata={"pattern_id": 1, "lang": "en"})
    score = pat.score_case(case, model="sonnet", force_full=True, runs=5)
    assert score["runs"].count(None) == 1
    assert score["aggregate"]["n_fail"] == 1
    assert score["detected"] is True             # 4/4 successful detected


def test_pattern_run_inconclusive_case_own_bucket_not_failed(monkeypatch, tmp_path):
    """A case with <ceil(N/2) successful runs lands in inconclusive_cases, not failed."""
    import evals.scripts.run_pattern_eval as pat
    corpus_dir = tmp_path / "corpus"; corpus_dir.mkdir()
    partial_dir = tmp_path / "partial"; partial_dir.mkdir()
    _write_pattern_file(corpus_dir, 1, [
        {"id": "p1_en_001", "input": "aiword here", "expected_changes": ["aiword"],
         "domain": "casual", "metadata": {"pattern_id": 1, "lang": "en"}},
    ])
    from evals.scripts._shared import SkillRunError
    # 4 of 5 runs fail (non-session) -> only 1 success < ceil(5/2)=3 -> inconclusive
    seq = iter([
        {"final": "clean"},
        SkillRunError("x"), SkillRunError("x"), SkillRunError("x"), SkillRunError("x"),
    ])
    def maybe(*a, **k):
        x = next(seq)
        if isinstance(x, Exception):
            raise x
        return x
    monkeypatch.setattr(pat, "run_skill", maybe)
    monkeypatch.setattr(pat, "verify_skill_install", lambda: None)
    monkeypatch.setattr(f"{PATTERN_MODULE}.REPO_ROOT", tmp_path)
    report = pat.run(lang="en", runs=5, _corpus_dir_override=corpus_dir,
                     _partial_dir_override=partial_dir)
    s = report["summary"]
    assert "p1_en_001" in s["inconclusive_cases"]
    assert not s["failed"]                        # NOT laundered into failed
    assert s["is_complete"] is False              # terminal-unstable, exit 1
```

- [ ] **Step 1b: Add a resume test** (spec Testing requires it) — append to `tests/test_run_pattern_eval.py`:

```python
def test_pattern_multirun_partial_reused_wholesale(monkeypatch, tmp_path):
    """A cached multi-run partial (with runs[]) is reused without re-scoring; --force redoes."""
    import evals.scripts.run_pattern_eval as pat
    corpus_dir = tmp_path / "corpus"; corpus_dir.mkdir()
    partial_dir = tmp_path / "partial"; partial_dir.mkdir()
    _write_pattern_file(corpus_dir, 1, [
        {"id": "p1_en_001", "input": "aiword here", "expected_changes": ["aiword"],
         "domain": "casual", "metadata": {"pattern_id": 1, "lang": "en"}},
    ])
    calls = {"n": 0}
    def counting(*a, **k):
        calls["n"] += 1
        return {"final": "clean"}
    monkeypatch.setattr(pat, "run_skill", counting)
    monkeypatch.setattr(pat, "verify_skill_install", lambda: None)
    monkeypatch.setattr(f"{PATTERN_MODULE}.REPO_ROOT", tmp_path)
    pat.run(lang="en", runs=5, _corpus_dir_override=corpus_dir, _partial_dir_override=partial_dir)
    first = calls["n"]
    assert first == 5                       # 5 runs for the one case
    pat.run(lang="en", runs=5, _corpus_dir_override=corpus_dir, _partial_dir_override=partial_dir)
    assert calls["n"] == first              # second run reused the partial, no new skill calls
    pat.run(lang="en", runs=5, force=True, _corpus_dir_override=corpus_dir, _partial_dir_override=partial_dir)
    assert calls["n"] == first + 5          # --force re-scored
```

- [ ] **Step 2: Run them, verify failure** — `PYTHONPATH=. python3 -m pytest tests/test_run_pattern_eval.py -k "score_case_runs or median_edit or session_limit_propagates or none_run or inconclusive_case or partial_reused" -q` → FAIL (`score_case() got an unexpected keyword argument 'runs'`).

- [ ] **Step 3: Refactor `score_case` → extract `_score_case_once`** — rename the existing `def score_case(case, *, model="sonnet", force_full=False)` body to `def _score_case_once(case, *, model="sonnet", force_full=False)` (no body change — it already returns the per-run dict for all branches).

- [ ] **Step 4: Add the new multi-run `score_case`** — directly below `_score_case_once`:

```python
def score_case(case: Case, *, model: str = "sonnet", force_full: bool = False, runs: int = 5) -> dict:
    """Multi-run wrapper: run the per-case scoring `runs` times and aggregate.

    Unscorable categories (no run_skill call) are decided once. Scored + true-neg
    categories run N times; each run's run_skill exception is caught EXCEPT a
    session-limit error, which re-raises so run()'s case-level break still fires.
    """
    # Unscorable categories don't call the skill — decide once, no multi-run.
    if not case.true_negative and not case.expected_changes:
        return _score_case_once(case, model=model, force_full=force_full)
    if not case.true_negative:
        input_lower = case.input.lower()
        if not [t for t in case.expected_changes if t.lower() in input_lower]:
            return _score_case_once(case, model=model, force_full=force_full)

    run_dicts: list[dict | None] = []
    for _ in range(runs):
        try:
            run_dicts.append(_score_case_once(case, model=model, force_full=force_full))
        except SkillRunError as exc:
            if _is_session_limit_error(exc):
                raise  # quota guard: propagate so run()'s break fires
            run_dicts.append(None)
        except subprocess.TimeoutExpired:
            run_dicts.append(None)

    if case.true_negative:
        values = [r["edit_ratio"] if r is not None else None for r in run_dicts]
        agg = aggregate_runs(values, kind="continuous", n_target=runs, threshold=0.10)
        present_vals = [r for r in run_dicts if r is not None]
        return {
            "case_id": case.id,
            "pattern_id": case.metadata.get("pattern_id"),
            "status": "true_negative",
            "detected": bool(agg["verdict"]),            # for true-neg, "left it alone"
            "passes_true_negative": bool(agg["verdict"]),
            "edit_ratio": agg["median"],
            "runs": [None if r is None else r["edit_ratio"] for r in run_dicts],
            "aggregate": agg,
            "rewrite_preview": (present_vals[0]["rewrite_preview"] if present_vals else ""),
        }

    # scored detection case
    values = [1.0 if (r is not None and r["detected"]) else (0.0 if r is not None else None)
              for r in run_dicts]
    agg = aggregate_runs(values, kind="binary", n_target=runs)
    present = [r for r in run_dicts if r is not None]
    med_present = round(statistics.median([r["terms_present"] for r in present])) if present else 0
    med_removed = round(statistics.median([r["terms_removed"] for r in present])) if present else 0
    return {
        "case_id": case.id,
        "pattern_id": case.metadata.get("pattern_id"),
        "status": "scored",
        "detected": bool(agg["verdict"]) if agg["verdict"] is not None else False,
        "runs": [None if r is None else r["detected"] for r in run_dicts],
        "aggregate": agg,
        "terms_present": med_present,
        "terms_removed": med_removed,
        "rewrite_preview": (present[0]["rewrite_preview"] if present else ""),
        "preflight": (present[0]["preflight"] if present else ""),  # back-compat: test_score_case_scorable_returns_extra_keys asserts this key
    }
```

Then add the imports at the top of `run_pattern_eval.py`: `import statistics` and extend the `_shared` import to include `aggregate_runs`.

- [ ] **Step 5: Thread `runs` through `run()` + collect inconclusive/flaky** — change `def run(..., aggregate_only=False,` to add `runs: int = 5,` (keyword, before the `*`). At the scoring call site (currently `score = score_case(case, model=model, force_full=True)`) pass `runs=runs`. The existing case-level `except SkillRunError`/`_is_session_limit_error` block stays (a propagated session-limit error from `score_case` is caught there → break). After the scoring loop, build the new buckets. Replace the `is_complete = (...)` line and the summary dict with:

```python
    inconclusive_cases = [
        s["case_id"] for ps in by_pattern.values() for s in ps
        if s.get("aggregate", {}).get("inconclusive")
    ]
    flaky_cases = [
        s["case_id"] for ps in by_pattern.values() for s in ps
        if s.get("aggregate", {}).get("flaky")
    ]
    is_complete = (
        not skipped_no_partial and not failed and not session_limit_hit
        and not inconclusive_cases
    )
```

In the per-pattern loop, exclude inconclusive cases from the detection rate denominator: change `scorable = [s for s in scores if s.get("status") == "scored"]` to `scorable = [s for s in scores if s.get("status") == "scored" and not s.get("aggregate", {}).get("inconclusive")]`. Apply the same `and not ... inconclusive` filter to the `true_negatives` list used for `tn_passes`. (Inconclusive cases are reported in their own bucket, never silently counted pass/fail.)

Add `overall_detection_fraction` and the new buckets to the summary. After the existing `overall` computation add:

```python
    overall_fraction = (
        sum(s["aggregate"]["fraction"] for s in all_scorable
            if s.get("aggregate", {}).get("fraction") is not None)
        / len([s for s in all_scorable if s.get("aggregate", {}).get("fraction") is not None])
    ) if any(s.get("aggregate", {}).get("fraction") is not None for s in all_scorable) else 0.0
```

(`all_scorable` must also exclude inconclusive — apply the same filter where `all_scorable` is built.) Restate `per_term_removal_rate` to use the per-case **median** term counts already stored (`terms_present`/`terms_removed` are now medians from `score_case`) — the existing summation code already reads those keys and now sums medians, so `Σ(median_removed)/Σ(median_present)` is computed unchanged. Add to the `summary` dict:

```python
            "overall_detection_fraction": round(overall_fraction, 3),
            "flaky_cases": flaky_cases,
            "inconclusive_cases": inconclusive_cases,
            "runs_per_case": runs,
```

- [ ] **Step 6: Wire `--runs` in `main()`** — add `parser.add_argument("--runs", type=int, default=5, help="Skill invocations per case; verdict = majority/median over runs.")` and pass `runs=args.runs` into the `run(...)` call. In `main()`'s exit/message section, add a distinct branch BEFORE the generic completion, so inconclusive (terminal) isn't reported as "will retry":

```python
    if report["summary"].get("inconclusive_cases"):
        print(
            f"Inconclusive ({len(report['summary']['inconclusive_cases'])} cases — "
            "too few successful runs; NOT resumable, needs --force or a corpus/skill fix): "
            + ", ".join(report["summary"]["inconclusive_cases"])
        )
    if report["summary"].get("flaky_cases"):
        print(f"Flaky ({len(report['summary']['flaky_cases'])} cases disagreed run-to-run): "
              + ", ".join(report["summary"]["flaky_cases"]))
```

- [ ] **Step 7a: Update ALL existing `score_case` monkeypatch fakes for the new `runs` kwarg.** `run()` now calls `score_case(case, model=model, force_full=True, runs=runs)`. Every existing test that monkeypatches `score_case` through `run()` has a fake with a fixed signature that will raise `TypeError: unexpected keyword argument 'runs'`. In `tests/test_run_pattern_eval.py`, find each `def fake_score_case(case, *, model=..., force_full=...)` (there are **6**: in the per-item-timeout test, the session-limit test, and the resume/aggregate tests — grep `def fake_score_case`) and add `**_` to each signature: `def fake_score_case(case, *, model="sonnet", force_full=False, **_):`. The `**_` absorbs `runs` (and any future kwarg) without changing behavior.

- [ ] **Step 7b: Re-point the stale timeout test** — `tests/test_run_pattern_eval.py::test_pattern_run_per_item_timeout_continues_and_records_failure` monkeypatches `score_case` to raise `TimeoutExpired` and asserts `summary['failed']`. Under SP3a a *real* per-run timeout becomes a `None` run inside `score_case`, so this test now only exercises a monkeypatched-score path that production multi-run no longer hits. Update its docstring to state it covers the **case-level** fallback (a `score_case` that itself raises — e.g. a bug, not a per-run timeout) and note the realistic per-run path is covered by `test_pattern_score_case_nonsession_failure_becomes_none_run`. Keep it green; do not delete (the case-level except still exists for a propagated session-limit and defensive coverage).

- [ ] **Step 8: Run tests** — `PYTHONPATH=. python3 -m pytest tests/test_run_pattern_eval.py -q` → PASS. Full suite `PYTHONPATH=. python3 -m pytest -q` → green (≥306 + new).

- [ ] **Step 9: Commit**

```bash
git add evals/scripts/run_pattern_eval.py tests/test_run_pattern_eval.py
git commit -m "feat(evals): run_pattern_eval --runs N multi-run + median/majority/inconclusive (SP3a Task 2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 10: Skeptic review** the diff: does multi-run preserve the unscorable short-circuit (no skill call)? Is the session-limit carve-out correct (propagates, run()'s break fires)? Does excluding inconclusive from the rate denominators avoid silent pass/fail? Does `per_term_removal_rate` now correctly sum per-case medians? Any existing summary consumer broken? Fix findings, re-verify.

---

## Task 3: `run_false_positive_eval` multi-run

**Files:**
- Modify: `evals/scripts/run_false_positive_eval.py` (`score_human_text`, `run()`, `main()`, `--runs`)
- Test: `tests/test_false_positive_eval.py`

Same shape as Task 2 but the only metric is `edit_ratio` (continuous). Extract the current `score_human_text` body to `_score_human_text_once`; the new `score_human_text` runs N times and aggregates median.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_false_positive_eval.py`:

```python
def test_fp_score_runs_n_times_median_verdict(monkeypatch):
    import evals.scripts.run_false_positive_eval as fp
    inp = "A clean human paragraph that the skill should leave essentially intact here."
    # 3 near-verbatim (low ratio) + 2 heavy edits -> median low -> NOT over-threshold
    outs = iter([
        {"final": inp}, {"final": inp}, {"final": inp},
        {"final": "completely different text entirely"},
        {"final": "completely different text entirely"},
    ])
    monkeypatch.setattr(fp, "run_skill", lambda *a, **k: next(outs))
    score = fp.score_human_text(inp, lang="en", model="sonnet", domain="casual", runs=5)
    assert len(score["runs"]) == 5
    assert score["above_threshold"] is False          # median edit_ratio <= 0.10
    assert score["aggregate"]["flaky"] is True


def test_fp_score_session_limit_propagates(monkeypatch):
    import evals.scripts.run_false_positive_eval as fp
    from evals.scripts._shared import SkillRunError
    def boom(*a, **k):
        raise SkillRunError("session limit reached")
    monkeypatch.setattr(fp, "run_skill", boom)
    with pytest.raises(SkillRunError):
        fp.score_human_text("clean text", lang="en", model="sonnet", domain="casual", runs=5)


def test_fp_run_inconclusive_file_own_bucket(monkeypatch, tmp_path):
    import evals.scripts.run_false_positive_eval as fp
    from evals.scripts._shared import SkillRunError
    corpus_dir = tmp_path / "human" / "synthetic"; corpus_dir.mkdir(parents=True)
    (corpus_dir / "f1.md").write_text("A clean human sentence left alone.", encoding="utf-8")
    partial_dir = tmp_path / "partial"; partial_dir.mkdir()
    seq = iter([
        {"final": "A clean human sentence left alone."},
        SkillRunError("x"), SkillRunError("x"), SkillRunError("x"), SkillRunError("x"),
    ])
    def maybe(*a, **k):
        x = next(seq)
        if isinstance(x, Exception): raise x
        return x
    monkeypatch.setattr(fp, "run_skill", maybe)
    monkeypatch.setattr(fp, "verify_skill_install", lambda: None)
    monkeypatch.setattr("evals.scripts.run_false_positive_eval.REPO_ROOT", tmp_path)
    report = fp.run(lang="en", corpus="synthetic", runs=5,
                    _corpus_dir_override=corpus_dir, _partial_dir_override=partial_dir)
    s = report["summary"]
    assert "f1.md" in s["inconclusive_files"]
    assert not s["failed"]
    assert s["is_complete"] is False


def test_fp_run_all_failed_file_no_crash_none_median(monkeypatch, tmp_path):
    """All N runs fail -> median None. run() must NOT crash on `None > threshold`."""
    import evals.scripts.run_false_positive_eval as fp
    from evals.scripts._shared import SkillRunError
    corpus_dir = tmp_path / "human" / "synthetic"; corpus_dir.mkdir(parents=True)
    (corpus_dir / "f1.md").write_text("A clean human sentence.", encoding="utf-8")
    partial_dir = tmp_path / "partial"; partial_dir.mkdir()
    monkeypatch.setattr(fp, "run_skill",
                        lambda *a, **k: (_ for _ in ()).throw(SkillRunError("transient")))
    monkeypatch.setattr(fp, "verify_skill_install", lambda: None)
    monkeypatch.setattr("evals.scripts.run_false_positive_eval.REPO_ROOT", tmp_path)
    report = fp.run(lang="en", corpus="synthetic", runs=5,
                    _corpus_dir_override=corpus_dir, _partial_dir_override=partial_dir)
    s = report["summary"]
    assert "f1.md" in s["inconclusive_files"]      # 0 successes -> inconclusive
    # the per-file record exists with above_threshold False (None-median guarded), no crash
    rec = next(r for r in report["per_file"] if r["file"] == "f1.md")
    assert rec["above_threshold"] is False
    assert rec["edit_ratio"] is None
```

- [ ] **Step 2: Run them, verify failure** — `PYTHONPATH=. python3 -m pytest tests/test_false_positive_eval.py -k "runs_n_times or session_limit_propagates or inconclusive_file" -q` → FAIL.

- [ ] **Step 3: Extract `_score_human_text_once`** — rename the existing `def score_human_text(text, *, lang="en", model="sonnet", domain="casual")` body to `_score_human_text_once(...)` (no body change).

- [ ] **Step 4: New multi-run `score_human_text`** — below it:

```python
def score_human_text(
    text: str, *, lang: str = "en", model: str = "sonnet", domain: str = "casual", runs: int = 5
) -> dict:
    """Multi-run: run N times, verdict = median(edit_ratio) > threshold (over-edit)."""
    run_dicts: list[dict | None] = []
    for _ in range(runs):
        try:
            run_dicts.append(_score_human_text_once(text, lang=lang, model=model, domain=domain))
        except SkillRunError as exc:
            if _is_session_limit_error(exc):
                raise
            run_dicts.append(None)
        except subprocess.TimeoutExpired:
            run_dicts.append(None)

    values = [r["edit_ratio"] if r is not None else None for r in run_dicts]
    agg = aggregate_runs(values, kind="continuous", n_target=runs, threshold=DEFAULT_THRESHOLD)
    present = [r for r in run_dicts if r is not None]
    quick_drops = sum(1 for r in present if r["density_preflight_quick_drop"])
    return {
        "edit_ratio": agg["median"],
        "median_edit_ratio": agg["median"],
        "runs": values,
        "aggregate": agg,
        # over-threshold when the MEDIAN exceeds threshold (None when inconclusive)
        "above_threshold": (agg["median"] is not None and agg["median"] > DEFAULT_THRESHOLD),
        "density_preflight_quick_drop": (quick_drops >= math.ceil(len(present) / 2)) if present else False,
        "rewrite_length_chars": (present[0]["rewrite_length_chars"] if present else 0),
        "preflight_message": (present[0]["preflight_message"] if present else ""),
    }
```

Add imports: `import math` (FP's new code uses `math.ceil`; it does NOT need `statistics`), and extend the `_shared` import with `aggregate_runs`. **Single-source-of-truth note:** the helper sets `above_threshold` against its own `DEFAULT_THRESHOLD` param purely so *direct* callers (the unit tests) get a sensible verdict; **`run()` is the authority** — it overwrites `above_threshold` against the configured `--threshold` (Step 5). Leave a comment to that effect on the helper's `above_threshold` line so a future refactor doesn't mistake it for the gate.

- [ ] **Step 5: Thread `runs` + buckets through `run()`** — add `runs: int = 5,` to `run()` signature (keyword). Pass `runs=runs` to `score_human_text`. The line `score["above_threshold"] = score["edit_ratio"] > threshold` must now compare the **median** to the run-configured `threshold` — but **guard against a `None` median** (an all-failed inconclusive file has `edit_ratio=None`; `None > 0.10` raises `TypeError` and crashes `run()`). Replace that line with:

```python
        score["above_threshold"] = (score["edit_ratio"] is not None and score["edit_ratio"] > threshold)
```
(`score["edit_ratio"]` is the median; for a non-inconclusive file it's a float, for an all-failed file it's `None` → `False`. This `run()` line is the authority for the configured `--threshold`; the helper's `DEFAULT_THRESHOLD` set is the direct-call fallback.) After the loop add:

```python
    inconclusive_files = [s["file"] for s in per_file if s.get("aggregate", {}).get("inconclusive")]
    flaky_files = [s["file"] for s in per_file if s.get("aggregate", {}).get("flaky")]
```
Exclude inconclusive files from `over_edited`/`mean_ratio`:
```python
    scorable_files = [s for s in per_file if not s.get("aggregate", {}).get("inconclusive")]
    total = len(scorable_files)
    over_edited = sum(1 for s in scorable_files if s["above_threshold"])
    mean_ratio = sum(s["edit_ratio"] for s in scorable_files) / total if total else 0.0
```
Also compute `quick_drops` over `scorable_files` (not `per_file`) so numerator and denominator (`density_preflight_quick_drop_rate = quick_drops / total`) are over the same set — replace the existing `quick_drops = sum(1 for s in per_file if s["density_preflight_quick_drop"])` with `quick_drops = sum(1 for s in scorable_files if s["density_preflight_quick_drop"])`.
`is_complete = not skipped_no_partial and not failed and not session_limit_hit and not inconclusive_files`. Add to summary: `"flaky_files": flaky_files, "inconclusive_files": inconclusive_files, "runs_per_file": runs,` and keep `mean_edit_ratio` (now the mean of per-file medians — a same-name multi-run analog, not comparable to single-run baselines).

- [ ] **Step 6: `--runs` in `main()` + inconclusive/flaky messages** — add `parser.add_argument("--runs", type=int, default=5, ...)`, pass `runs=args.runs`. Add the inconclusive (terminal, "NOT resumable") + flaky print branches mirroring Task 2 Step 6 (keyed on `inconclusive_files`/`flaky_files`, listing file names).

- [ ] **Step 7a: Update ALL existing `score_human_text` monkeypatch fakes for the new `runs` kwarg.** `run()` now calls `score_human_text(body, lang=lang, model=model, domain=domain, runs=runs)`. In `tests/test_false_positive_eval.py`, find each fake (grep `def fake_score` — there are **4**) and add `**_` to its signature so `runs=` is absorbed without `TypeError`.

- [ ] **Step 7b: Re-point the stale FP timeout test** — `tests/test_false_positive_eval.py::test_fp_run_per_item_timeout_continues_and_records_failure`: same treatment as Task 2 Step 7b — annotate it as the case-level (`score_human_text` itself raising) fallback, note the realistic per-run path is covered by the new tests. Keep green.

- [ ] **Step 8: Run tests** — `PYTHONPATH=. python3 -m pytest tests/test_false_positive_eval.py -q` → PASS. Full suite → green.

- [ ] **Step 9: Commit**

```bash
git add evals/scripts/run_false_positive_eval.py tests/test_false_positive_eval.py
git commit -m "feat(evals): run_false_positive_eval --runs N multi-run + median verdict (SP3a Task 3)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 10: Skeptic review** the diff: median-per-file verdict correct? `above_threshold` reconciled against `--threshold` (not double-applied)? inconclusive excluded from mean/over-count? buckets + messages right? Fix findings.

---

## Task 4: Full-suite green + close-out (+ optional live smoke)

- [ ] **Step 1:** `PYTHONPATH=. python3 -m pytest -q` → all green (≥306 + new). Confirm `run_e2e_eval.py` + its tests are byte-unchanged (`git diff main -- evals/scripts/run_e2e_eval.py` empty).
- [ ] **Step 2 (OPTIONAL, QUOTA — user-gated):** live smoke to prove the harness surfaces noise on real data. Subscription `claude -p`, no API key. The 9 EN true-neg cases at `--runs 5` (~45 calls):
  ```bash
  PYTHONPATH=. python3 -u evals/scripts/run_pattern_eval.py --lang en --runs 5 --force
  ```
  **Pass = structural:** the report lists non-empty `flaky_cases` and per-case `passed_fraction` (proves the harness exposes the run-to-run disagreement single-run scoring hid). The exact majority X/9 may vary — that variance IS the noise; do NOT gate on a specific count. Skip/defer this step if conserving quota — the unit tests already prove the logic.
- [ ] **Step 3: Final Skeptic sign-off** of the whole SP3a (all three diffs + `aggregate_runs` semantics together): honest, no e2e change, no policy drift between the two runners, inconclusive never silently passed/failed. Fix anything found.
- [ ] **Step 4:** Update `docs/plans/sp1-baselines.md` or a short `docs/plans/sp3a-notes.md` noting the harness is live + how SP3b/SP3c should call it (slices). Run `/freshness` to sweep vault STATUS/SESSION_LOG/DECISIONS.
- [ ] **Step 5:** `superpowers:finishing-a-development-branch` — squash-merge `sp3a-multirun-harness` → `main` (harness + tests; no skill change → no version bump, per the SP1 precedent), push on explicit user OK.

---

## Acceptance criteria (all must hold)

- [ ] `aggregate_runs` pure + unit-tested in `_shared.py`; both runners use it (no policy drift).
- [ ] `run_pattern_eval --runs N` (default 5): `score_case` runs N times; summary reports majority `overall_detection_rate` + `overall_detection_fraction` + median-based `true_neg_passes` + `per_term_removal_rate` (sum of per-case medians) + `flaky_cases` + `inconclusive_cases`.
- [ ] `run_false_positive_eval --runs N` (default 5): median(edit_ratio)-per-file verdict; `flaky_files` + `inconclusive_files`.
- [ ] Session-limit error mid-case PROPAGATES (quota guard intact); non-session failure → `None` run; <⌈N/2⌉ successes → `inconclusive_*` bucket (own bucket, partial written, skipped on resume, exit 1), never aliased to `failed`.
- [ ] `run_e2e_eval.py` + its tests unchanged. Full pytest green (≥306 + new).
- [ ] Every task diff + the aggregation semantics Skeptic-verified (no self-review).
