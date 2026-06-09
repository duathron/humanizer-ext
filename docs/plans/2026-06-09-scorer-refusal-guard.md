# Scorer refusal-guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax. **Review rule (maintainer): no self-review — every task diff + the detector logic is verified by the independent Skeptic (`AI/AGENT PERSONAS/Agents/independent-review-agent.md`) from primary evidence before acceptance.**

**Goal:** Stop the eval scorers counting a skill **refusal** ("no text provided…") as a detection / over-edit. A refusal run becomes a `None` run in the SP3a multi-run aggregation → excluded → `inconclusive` if most runs refuse.

**Architecture:** A pure phrase-only `is_refusal(text)` in `_shared.py`. In `run_pattern_eval._score_case_once` (both the scored AND true_negative branches) and `run_false_positive_eval._score_human_text_once`, after the raw rewrite is obtained: `if is_refusal(raw): return None`. The existing multi-run loops already append `_score_*_once(...)` returns into `run_dicts` and `aggregate_runs` excludes `None`s — so no new status, no loop change. No skill change; `force_full` kept.

**Tech Stack:** Python 3.11 stdlib (`re`) + pytest. Zero quota (all tests monkeypatch `run_skill`/`_score_*_once`).

**Spec:** `docs/specs/2026-06-09-scorer-refusal-guard-design.md` (meetup consensus + Skeptic-approved, 2 rounds).

**Branch:** in-place on `scorer-refusal-guard` (off `main`).

---

## File structure

| File | Change | Task |
|---|---|---|
| `evals/scripts/_shared.py` | NEW pure `is_refusal(text)` (phrase-only) | 1 |
| `tests/test_evals_shared.py` | unit-test `is_refusal` | 1 |
| `evals/scripts/run_pattern_eval.py` | `_score_case_once`: refusal → `return None` (both branches) | 2 |
| `tests/test_run_pattern_eval.py` | refusal run → None → excluded / inconclusive | 2 |
| `evals/scripts/run_false_positive_eval.py` | `_score_human_text_once`: refusal → `return None` | 3 |
| `tests/test_false_positive_eval.py` | refusal run → None (defensive) | 3 |
| `evals/scripts/run_pattern_eval.py` + `run_e2e_eval.py` (report strings) | name detection-capability vs routing-fidelity | 4 |

---

## Task 1: `is_refusal(text)` pure detector (`_shared.py`)

**Files:**
- Modify: `evals/scripts/_shared.py` (add the function near `aggregate_runs` ~line 397; `import re` already present at line 64)
- Test: `tests/test_evals_shared.py`

- [ ] **Step 1: Write the failing tests** — append to `tests/test_evals_shared.py`:

```python
def test_is_refusal_flags_real_refusal_stubs():
    from evals.scripts._shared import is_refusal
    assert is_refusal("no text provided. what should I humanize?") is True
    assert is_refusal("Paste the text to humanize and I'll run a full casual pass.") is True
    assert is_refusal("No text to humanize was provided.") is True
    assert is_refusal("") is True
    assert is_refusal("   \n  ") is True


def test_is_refusal_does_not_flag_aggressive_rewrite():
    """Load-bearing (round-1 BLOCKER): a legit heavy rewrite has NO refusal phrase."""
    from evals.scripts._shared import is_refusal
    assert is_refusal("It works better.") is False
    assert is_refusal("This approach simply works better than before.") is False
    # "can't help" appears in legit prose and is NOT a refusal phrase
    assert is_refusal("You can't help noticing the difference.") is False


def test_is_refusal_passes_real_short_rewrites():
    from evals.scripts._shared import is_refusal
    # real SP3b conversion rewrites (skill actually rewrote)
    assert is_refusal("Gallery 825 is LAAA's exhibition space; it has four rooms.") is False
    assert is_refusal("The goal is to write clearly.") is False
    assert is_refusal("The report, which covered three continents, concluded demand had shifted.") is False
```

- [ ] **Step 2: Run, verify FAIL** — `PYTHONPATH=. python3 -m pytest tests/test_evals_shared.py -k is_refusal -q` → FAIL (ImportError). If it errors for an unrelated reason, STOP and report.

- [ ] **Step 3: Implement** — add to `evals/scripts/_shared.py` (near `aggregate_runs`):

```python
# Observed skill-refusal stubs (the skill asks for input instead of rewriting).
# Phrase-only by design: NEVER false-flags a real rewrite (an aggressive rewrite
# shares ~0 content with the input but contains none of these meta-phrases). A
# novel/DE refusal not listed slips through as detected/miss — the SAFE direction
# (one bad data point) vs killing a good rewrite (corrupts the rate by exclusion).
_REFUSAL_PHRASES = (
    "no text",
    "what text",
    "what should i humanize",
    "paste the text",
    "provide the text",
    "what do you want",
    "text to humanize?",
)


def is_refusal(text: str) -> bool:
    """True if `text` is a skill refusal / non-rewrite (empty, or an input-request
    meta-message), so eval scorers can treat it as a None run instead of scoring
    the trivially-absent tell as a detection (or the huge edit_ratio as over-edit)."""
    if not text or not text.strip():
        return True
    low = text.lower()
    return any(p in low for p in _REFUSAL_PHRASES)
```

- [ ] **Step 4: Run tests** — `PYTHONPATH=. python3 -m pytest tests/test_evals_shared.py -k is_refusal -q` → 3 pass. Full suite `PYTHONPATH=. python3 -m pytest -q` → green (baseline 329 + 3 = 332). Paste the real summary.

- [ ] **Step 5: Commit**

```bash
git add evals/scripts/_shared.py tests/test_evals_shared.py
git commit -m "feat(evals): pure phrase-only is_refusal() detector (scorer-guard Task 1)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 6: Skeptic review** the diff: phrase-only, never flags a real rewrite (the aggressive-rewrite test), flags the real stubs + empty. Any listed phrase a plausible legit rewrite substring (the accepted-risk QUESTION)? Fix findings.

---

## Task 2: wire into `run_pattern_eval._score_case_once` (both branches → `None` on refusal)

**Files:**
- Modify: `evals/scripts/run_pattern_eval.py` (`_score_case_once`: true_negative branch ~line 67, scored branch ~line 114; add `is_refusal` to the `_shared` import)
- Test: `tests/test_run_pattern_eval.py`

- [ ] **Step 1: Write the failing tests** — append to `tests/test_run_pattern_eval.py` (reuse `Case`, the `**_` fakes pattern, `_corpus_dir_override`/`_partial_dir_override`):

```python
def test_score_case_refusal_run_becomes_none_scored(monkeypatch):
    """A refusal output on a DETECTION case → None run → excluded; all-refuse → inconclusive."""
    import evals.scripts.run_pattern_eval as pat
    from evals.scripts._shared import Case
    monkeypatch.setattr(pat, "run_skill",
                        lambda *a, **k: {"final": "No text provided. What should I humanize?"})
    case = Case(id="p1_en_001", input="aiword here", expected_changes=["aiword"],
                expected_unchanged=[], domain="casual", true_negative=False,
                metadata={"pattern_id": 1, "lang": "en"})
    score = pat.score_case(case, model="sonnet", force_full=True, runs=5)
    assert score["runs"] == [None, None, None, None, None]   # every refusal → None
    assert score["aggregate"]["inconclusive"] is True         # 0 successes < ceil(5/2)
    assert score["detected"] is False                         # NEVER a false detection


def test_score_case_refusal_run_becomes_none_true_negative(monkeypatch):
    """A refusal on a TRUE-NEG case → None run → excluded from median (not a false over-edit fail)."""
    import evals.scripts.run_pattern_eval as pat
    from evals.scripts._shared import Case
    monkeypatch.setattr(pat, "run_skill",
                        lambda *a, **k: {"final": "no text to humanize was provided. paste the text."})
    case = Case(id="p8_en_001", input="A clean human sentence left alone.",
                expected_changes=[], expected_unchanged=[], domain="casual",
                true_negative=True, metadata={"pattern_id": 8, "lang": "en"})
    score = pat.score_case(case, model="sonnet", runs=5)
    assert score["runs"] == [None, None, None, None, None]
    assert score["aggregate"]["inconclusive"] is True
    assert score["passes_true_negative"] is False  # bool(None); harmless because run() excludes inconclusive


def test_run_all_refuse_true_negative_is_inconclusive_not_failure(monkeypatch, tmp_path):
    """run()-level proof (load-bearing): an all-refuse TRUE-NEG case lands in
    inconclusive_cases and is NOT counted as a true_neg failure."""
    import evals.scripts.run_pattern_eval as pat
    corpus_dir = tmp_path / "corpus"; corpus_dir.mkdir()
    partial_dir = tmp_path / "partial"; partial_dir.mkdir()
    _write_pattern_file(corpus_dir, 8, [
        {"id": "p8_en_001", "input": "A clean human sentence left alone.",
         "expected_changes": [], "expected_unchanged": [], "domain": "casual",
         "true_negative": True, "metadata": {"pattern_id": 8, "lang": "en"}},
    ])
    monkeypatch.setattr(pat, "run_skill",
                        lambda *a, **k: {"final": "No text provided. What should I humanize?"})
    monkeypatch.setattr(pat, "verify_skill_install", lambda: None)
    monkeypatch.setattr(f"{PATTERN_MODULE}.REPO_ROOT", tmp_path)
    report = pat.run(lang="en", runs=5, _corpus_dir_override=corpus_dir,
                     _partial_dir_override=partial_dir)
    s = report["summary"]
    assert "p8_en_001" in s["inconclusive_cases"]
    # not counted as a true-neg failure anywhere in per_pattern
    for p in report["per_pattern"]:
        assert "p8_en_001" not in p.get("true_neg_failures", [])


def test_score_case_mixed_refusal_and_real_detection(monkeypatch):
    """3 real rewrites that detect + 2 refusals → 3 None... no: refusals→None, reals→detected."""
    import evals.scripts.run_pattern_eval as pat
    from evals.scripts._shared import Case
    outs = iter([
        {"final": "clean"},                                   # detected (aiword gone)
        {"final": "No text provided."},                       # refusal → None
        {"final": "clean"},                                   # detected
        {"final": "clean"},                                   # detected
        {"final": "What text do you want humanized?"},        # refusal → None
    ])
    monkeypatch.setattr(pat, "run_skill", lambda *a, **k: next(outs))
    case = Case(id="p1_en_001", input="aiword here", expected_changes=["aiword"],
                expected_unchanged=[], domain="casual", true_negative=False,
                metadata={"pattern_id": 1, "lang": "en"})
    score = pat.score_case(case, model="sonnet", force_full=True, runs=5)
    assert score["runs"].count(None) == 2                     # 2 refusals excluded
    assert score["aggregate"]["n_success"] == 3               # 3 real runs
    assert score["detected"] is True                          # 3/3 real detected → majority
```

- [ ] **Step 2: Run, verify FAIL** — `PYTHONPATH=. python3 -m pytest tests/test_run_pattern_eval.py -k "refusal_run or mixed_refusal" -q` → FAIL (refusals currently score as detected, runs not None).

- [ ] **Step 3: Add the import** — in `run_pattern_eval.py` extend the `from evals.scripts._shared import (...)` block to include `is_refusal`.

- [ ] **Step 4: Guard the true_negative branch** — in `_score_case_once`, the true-neg branch computes `rewritten = result.get("final") or result.get("draft") or ""`. Immediately after that line, before the edit-distance math, insert:

```python
        if is_refusal(rewritten):
            return None
```

- [ ] **Step 5: Guard the scored branch** — the scored branch currently does `rewritten = (result.get("final") or result.get("draft") or "").lower()`. Replace that single line with a raw-first version that checks refusal BEFORE lowercasing:

```python
    rewritten_raw = result.get("final") or result.get("draft") or ""
    if is_refusal(rewritten_raw):
        return None
    rewritten = rewritten_raw.lower()
```

- [ ] **Step 6: Run tests** — the 3 new tests PASS; full suite `PYTHONPATH=. python3 -m pytest -q` → green (no regressions). The multi-run loop is UNCHANGED — it already appends `_score_case_once(...)` returns (a `None` is appended as a None run, exactly like a caught failure). Verify no existing pattern test breaks (the unscorable short-circuit paths never reach `run_skill`, so they never return `None`).

- [ ] **Step 7: Commit**

```bash
git add evals/scripts/run_pattern_eval.py tests/test_run_pattern_eval.py
git commit -m "feat(evals): refusal output -> None run in pattern scorer, both branches (scorer-guard Task 2)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 8: Skeptic review** the diff: refusal → None in BOTH branches; raw (not lowercased) checked; loop unchanged + correctly maps None; unscorable short-circuits unaffected; a refusal never scores `detected`/over-edit; all-refuse → inconclusive. Fix findings.

---

## Task 3: wire into `run_false_positive_eval._score_human_text_once` (defensive)

**Files:**
- Modify: `evals/scripts/run_false_positive_eval.py` (`_score_human_text_once` ~line 41; add `is_refusal` to imports)
- Test: `tests/test_false_positive_eval.py`

- [ ] **Step 1: Write the failing test** — append to `tests/test_false_positive_eval.py`:

```python
def test_fp_score_refusal_run_becomes_none(monkeypatch):
    """A refusal on an FP file → None run → excluded from median; all-refuse → inconclusive
    (FP uses force_full=False and shouldn't refuse, but this closes the inverse bug:
    a refusal = huge edit_ratio = false 'over-edit')."""
    import evals.scripts.run_false_positive_eval as fp
    monkeypatch.setattr(fp, "run_skill",
                        lambda *a, **k: {"final": "No text provided. Paste the text to humanize."})
    score = fp.score_human_text("A clean human paragraph left alone.", lang="en",
                                model="sonnet", domain="casual", runs=5)
    assert score["runs"] == [None, None, None, None, None]
    assert score["aggregate"]["inconclusive"] is True
    assert score["above_threshold"] is False                  # NOT a false over-edit
```

- [ ] **Step 2: Run, verify FAIL** — `PYTHONPATH=. python3 -m pytest tests/test_false_positive_eval.py -k refusal_run_becomes_none -q` → FAIL (refusal currently → huge edit_ratio, not None).

- [ ] **Step 3: Add the import** — extend `run_false_positive_eval.py`'s `from evals.scripts._shared import (...)` to include `is_refusal`.

- [ ] **Step 4: Guard `_score_human_text_once`** — it computes `rewritten = result.get("final") or result.get("draft") or ""`. Immediately after that line, before the Levenshtein math, insert:

```python
    if is_refusal(rewritten):
        return None
```

- [ ] **Step 5: Run tests** — new test PASS; full suite green. The `score_human_text` loop already appends `_score_human_text_once(...)` returns, so a `None` flows in as a None run (excluded by `aggregate_runs`); the `above_threshold`/median already None-guard.

- [ ] **Step 6: Commit**

```bash
git add evals/scripts/run_false_positive_eval.py tests/test_false_positive_eval.py
git commit -m "feat(evals): refusal output -> None run in FP scorer (defensive; scorer-guard Task 3)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 7: Skeptic review** the diff: refusal → None; loop/median None-handling intact; defensive (FP doesn't refuse in practice) but correct. Fix findings.

---

## Task 4: name what each eval measures (report honesty)

**Files:**
- Modify: `evals/scripts/run_pattern_eval.py` (`run()` summary or `main()` print), `evals/scripts/run_e2e_eval.py` (report header/docstring)

- [ ] **Step 1:** In `run_pattern_eval.py` `run()`'s returned `summary` dict, add a static key documenting the eval's meaning:

```python
            "measures": "detection-logic capability under a forced full pass (force_full=True bypasses the product's real pre-flight routing); NOT shipped-routing fidelity — see run_e2e_eval",
```

- [ ] **Step 2:** In `run_e2e_eval.py`'s returned report dict (top level, alongside `eval_type`), add:

```python
        "measures": "shipped-routing fidelity (real pre-flight, realistic multi-pattern inputs); the pattern eval measures detection-logic capability under forced full pass",
```

- [ ] **Step 3: Run tests** — full suite green (these are additive string keys; confirm no test asserts an exact `summary`/report dict equality that would break — grep `tests/` for `== {` on these dicts; if found, update).

- [ ] **Step 4: Commit**

```bash
git add evals/scripts/run_pattern_eval.py evals/scripts/run_e2e_eval.py
git commit -m "docs(evals): name what each eval measures (detection-capability vs routing-fidelity) (scorer-guard Task 4)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 5: Skeptic review:** strings accurate + no broken dict-equality test.

---

## Task 5: close-out

- [ ] **Step 1:** Full suite `PYTHONPATH=. python3 -m pytest -q` green (baseline 329 + new). `git diff main -- SKILL.md` empty (no skill change).
- [ ] **Step 2 (opportunistic, zero-API):** inflation note — read cached `evals/reports/_partial/pattern_en_*.json`; count detection-status partials whose `rewrite_preview` is a refusal stub (was scored `detected`). Record the lower-bound inflation (~0.67pp from the SP3b run) in a short `docs/plans/scorer-guard-notes.md`. If the cache is ambiguous/cross-branch, state that and move on — NO quota re-baseline (non-goal).
- [ ] **Step 3: Final Skeptic sign-off** of the whole sub-project (all diffs + the detector together): refusals never score detected/over-edited; phrase-only never false-flags; no skill change; force_full kept; eval-naming present. Fix anything.
- [ ] **Step 4:** Run `/freshness` — update vault STATUS/SESSION_LOG/DECISIONS (scorer-guard shipped; the skill-hallucination finding still deferred).
- [ ] **Step 5:** `superpowers:finishing-a-development-branch` — squash-merge `scorer-refusal-guard` → `main` (harness + tests, no skill change → no version bump), push on explicit user OK. **Then SP3b can resume** (rebase on main, drop its stranded `172cdfb`, re-validate 013/009_003 under the fixed scorer — they'll now go inconclusive, not false-detect).

---

## Acceptance criteria (all must hold)

- [ ] `is_refusal(text)` pure + unit-tested, **phrase-only**; the aggressive-rewrite test passes (never false-flags a real rewrite).
- [ ] Pattern scorer (both scored + true-neg branches) + FP scorer: a refusal output → `None` run → excluded; a refusal NEVER scores `detected`/over-edited; all-refuse → `inconclusive`.
- [ ] Multi-run loops unchanged (None handled by existing machinery); unscorable short-circuits unaffected.
- [ ] Reports name detection-capability (pattern) vs routing-fidelity (e2e).
- [ ] Full pytest green; **SKILL.md byte-identical to main**; `force_full` kept.
- [ ] Every diff + the detector Skeptic-verified (no self-review).
