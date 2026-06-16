# Commentary Fence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make trailing skill commentary reliably strippable from the parsed rewrite by fencing it with a collision-proof `<!--HUMANIZER-AUDIT-->` sentinel — parser side first (safe, eval-only), then a SKILL.md directive gated on measured emission.

**Architecture:** Two phases. **Phase 1** teaches the eval parser (`_strip_trailing_commentary` in `evals/scripts/_shared.py`) to cut at the sentinel; it runs on the already-extracted rewrite region (so a Full-mode pre-rewrite audit can't be truncated) and is provably safe (the literal sentinel never occurs in legit prose). Phase 1 ships alone, eval-only, no version bump. **Phase 2** adds the SKILL.md directive that tells the model to emit the sentinel, plus a `fence_emission_rate` probe; it ships (v3.5.2) ONLY if emission ≥0.70 lower-CI AND rewrites are unchanged (formatting-only).

**Tech Stack:** Python 3, pytest, `rapidfuzz` Levenshtein, the `claude -p` subscription CLI (Phase 2 probe only). Spec: `docs/specs/2026-06-16-commentary-fence-design.md`.

---

## PHASE 1 — Parser sentinel cut (eval-only, no bump, hard-gated by tests)

### Task 1: Sentinel cut in `_strip_trailing_commentary`

**Files:**
- Modify: `evals/scripts/_shared.py` (`_strip_trailing_commentary`, ~lines 99-108; add a module constant near `_COMMENTARY_RE` ~line 91)
- Test: `tests/test_evals_shared.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_evals_shared.py`:

```python
from evals.scripts._shared import _strip_trailing_commentary, _AUDIT_SENTINEL

def test_audit_sentinel_value():
    assert _AUDIT_SENTINEL == "<!--HUMANIZER-AUDIT-->"

def test_strip_fence_cuts_trailing_note():
    s = "Sehr geehrte Frau Reichert,\n\nich bringe X mit.\n\nMit freundlichen Grüßen\nDaniel\n\n<!--HUMANIZER-AUDIT-->\nText unverändert. kein KI-Signal gefunden. DACH-register passt."
    assert _strip_trailing_commentary(s) == "Sehr geehrte Frau Reichert,\n\nich bringe X mit.\n\nMit freundlichen Grüßen\nDaniel"

def test_strip_fence_no_marker_unchanged():
    s = "A clean rewrite with no marker at all.\n\nSecond paragraph stays."
    assert _strip_trailing_commentary(s) == s

def test_strip_fence_no_false_cut_on_audit_word():
    # mentions 'audit'/'comment' inline but NOT the literal sentinel -> never cut
    s = "We reviewed the audit findings and left a comment in the thread.\n\nThe report ships Friday."
    assert _strip_trailing_commentary(s) == s

def test_strip_fence_no_false_cut_on_other_html_comment():
    # a different HTML comment in the body is not our sentinel -> not cut
    s = "See the diagram <!-- figure 1 --> below for the flow.\n\nDetails follow."
    assert _strip_trailing_commentary(s) == s

def test_strip_fence_then_existing_header_still_works():
    # no sentinel, but an existing English **Changes:** block -> still stripped (no regression)
    s = "The rewrite text.\n\n**Changes:** removed two em dashes."
    assert _strip_trailing_commentary(s) == "The rewrite text."
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd <repo> && PYTHONPATH=. python3 -m pytest tests/test_evals_shared.py -k "fence or sentinel" -v`
Expected: the module-level `from evals.scripts._shared import ... _AUDIT_SENTINEL` raises `ImportError` at **collection time** → the whole `test_evals_shared.py` file errors out (not per-test pass/fail) until Step 3 adds the constant. That collection error IS the red phase. (Of the 6 new tests, only `test_audit_sentinel_value` and `test_strip_fence_cuts_trailing_note` are genuinely red-on-behaviour; the other 4 are regression guards that pass once collection succeeds. That's expected — they lock no-false-cut + no-regression.)

- [ ] **Step 3: Implement the minimal change**

In `evals/scripts/_shared.py`, add the constant near `_COMMENTARY_RE` (~line 89):

```python
# Collision-proof fence the skill is instructed (Phase 2) to put before any
# trailing commentary. Never occurs in legit rewrite prose, so cutting at it
# cannot truncate real output. Applied to the already-extracted rewrite region.
_AUDIT_SENTINEL = "<!--HUMANIZER-AUDIT-->"
```

Replace `_strip_trailing_commentary` body (keep the docstring, append a sentence about the fence):

```python
def _strip_trailing_commentary(s: str) -> str:
    """Cut a trailing skill-commentary block off a rewrite.

    Two cutters, applied to the already-extracted rewrite region:
    1. The explicit `<!--HUMANIZER-AUDIT-->` fence (Phase 2) — everything from
       the literal sentinel onward is commentary. Exact-literal match only, so
       ordinary prose (or a different HTML comment) is never truncated.
    2. The legacy English bold-header block (`**Changes:**` etc.), newline-anchored.
    The earliest cut wins.
    """
    idx = s.find(_AUDIT_SENTINEL)
    if idx != -1:
        s = s[:idx].rstrip()
    m = _COMMENTARY_RE.search(s)
    return s[: m.start()].rstrip() if m else s
```

- [ ] **Step 4: Run to verify pass**

Run: `cd <repo> && PYTHONPATH=. python3 -m pytest tests/test_evals_shared.py -k "fence or sentinel" -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Run full suite**

Run: `cd <repo> && PYTHONPATH=. python3 -m pytest -q`
Expected: PASS — prior 346 + 6 new = 352 (0 regressions).

- [ ] **Step 6: Commit**

```bash
git add evals/scripts/_shared.py tests/test_evals_shared.py
git commit -m "feat(evals): parser honours <!--HUMANIZER-AUDIT--> fence (Phase 1, eval-only)

_strip_trailing_commentary now cuts at the literal sentinel (exact match, so no
false-strip of prose or other HTML comments) before the legacy header stripper.
Applied to the already-extracted rewrite region, so a Full-mode pre-rewrite audit
cannot be truncated. SKILL.md unchanged.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task 2: `parse_skill_output` integration test (ordering + Quick-direct)

**Files:**
- Test only: `tests/test_evals_shared.py` (no code change — proves Task 1's cut composes correctly with extraction)

- [ ] **Step 1: Write the failing/guard tests**

```python
from evals.scripts._shared import parse_skill_output

def test_parse_fullmode_pre_rewrite_audit_not_truncated_trailing_fence_cut():
    # Full mode: audit findings BEFORE the rewrite (must survive), trailing fenced note AFTER (must be cut)
    resp = (
        "**Final AI audit findings:**\n- em dash count: 0\n- concept coverage: 7/8\n\n"
        "**Final rewrite:**\n"
        "Der Brief ist fertig und sachlich.\n\n"
        "<!--HUMANIZER-AUDIT-->\nText unverändert. Authentisches DACH-Anschreiben."
    )
    assert parse_skill_output(resp)["final"] == "Der Brief ist fertig und sachlich."

def test_parse_quick_direct_trailing_fence_cut():
    # Quick-direct: whole response is the rewrite + a trailing fenced note
    resp = "Just the clean rewrite.\n\n<!--HUMANIZER-AUDIT-->\nNo edits made. human-authored."
    assert parse_skill_output(resp)["final"] == "Just the clean rewrite."

def test_parse_no_fence_unchanged():
    resp = "**Final rewrite:**\nA rewrite with no fence and no commentary."
    assert parse_skill_output(resp)["final"] == "A rewrite with no fence and no commentary."
```

- [ ] **Step 2: Run**

Run: `cd <repo> && PYTHONPATH=. python3 -m pytest tests/test_evals_shared.py -k "parse_fullmode or parse_quick or parse_no_fence" -v`
Expected: PASS immediately (Task 1's change already makes these pass, because `_strip_trailing_commentary` runs on the extracted region inside `parse_skill_output`). If `test_parse_fullmode...` FAILS by returning the audit findings or empty, the extraction-then-cut ordering is wrong — STOP and re-examine `parse_skill_output`; do NOT loosen the test.

- [ ] **Step 3: Full suite + commit**

Run: `cd <repo> && PYTHONPATH=. python3 -m pytest -q` (expect 355).

```bash
git add tests/test_evals_shared.py
git commit -m "test(evals): lock fence parse ordering — pre-rewrite audit survives, trailing note cut

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

**Phase 1 complete here.** It is independently shippable (eval-only, parses any fenced output safely). Phase 2 is gated.

---

## PHASE 2 — SKILL.md directive + emission probe + version bump (gated)

> Proceed ONLY after Phase 1 is merged. Phase 2 ships (the SKILL.md change + v3.5.2) ONLY if Task 5's gate passes; otherwise the directive is reworked or abandoned and Phase 1 stands alone.

### Task 3: Add the fence directive to SKILL.md Output Format

**Files:**
- Modify: `SKILL.md` — Output Format section (~lines 193-214)

- [ ] **Step 1: Add the directive**

After the Quick-mode output rule (current line ~203) and the Full→Quick rule (~205-214), add a new subsection at the end of `## Output Format`:

```markdown
**Commentary fence (all modes).** Any notes, audit summary, or commentary you place AFTER the final rewrite text MUST begin with the exact line `<!--HUMANIZER-AUDIT-->` on its own line; everything from that marker to the end of your response is non-rewrite commentary. Do NOT use this marker for the Full-mode pre-rewrite "Final AI audit findings" block — that stays where it is, before `**Final rewrite:**`. Quick mode still emits only the rewrite (no commentary); but if any commentary slips in, it MUST be fenced with this marker.
```

- [ ] **Step 2: Verify SKILL.md still parses / no structural break**

Run: `cd <repo> && PYTHONPATH=. python3 -m pytest -q` (the SKILL.md sanity tests — frontmatter, cross-references — must stay green; expect 355).

- [ ] **Step 3: Confirm rewrite-affecting sections untouched**

Run: `cd <repo> && git diff SKILL.md` — verify the diff is ONLY the added Output-Format subsection (no edits to Mode/Detection/Task/pattern sections). The directive is formatting-only.

- [ ] **Step 4: Commit (do NOT bump version yet — gated on Task 5)**

```bash
git add SKILL.md
git commit -m "feat(skill): fence trailing commentary with <!--HUMANIZER-AUDIT--> (Phase 2, pending gate)

Output-Format directive: any post-rewrite commentary must begin with the sentinel
(excludes the Full-mode pre-rewrite audit). Version bump deferred to the emission-gate
task. Pairs with the Phase-1 parser cut.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task 4: `fence_emission_rate` probe + formatting-only regression

**Files:**
- Modify: `evals/scripts/_shared.py` (`run_skill` — add a raw-capture path; it currently `return parse_skill_output(completed.stdout)` and DISCARDS the raw stdout, so the probe cannot detect the sentinel)
- Test: `tests/test_evals_shared.py` (the new `run_skill` path)
- Create: `evals/scripts/probe_fence_emission.py`

- [ ] **Step 1 (code, TDD): give `run_skill` a raw-capture path.** `run_skill` returns the parsed dict and throws away `completed.stdout`; the probe needs the raw response to check for the sentinel and trailing commentary. Add an opt-in that returns both.

Test (stub `subprocess.run` like the existing run_skill tests):
```python
def test_run_skill_return_raw_gives_stdout_and_parsed(monkeypatch):
    import evals.scripts._shared as sh
    class _CP:  # fake completed process
        returncode = 0
        stdout = "Rewrite body.\n\n<!--HUMANIZER-AUDIT-->\nText unverändert."
        stderr = ""
    monkeypatch.setattr(sh.subprocess, "run", lambda *a, **k: _CP())
    monkeypatch.setattr(sh, "verify_skill_install", lambda *a, **k: None)
    raw, parsed = sh.run_skill("x", return_raw=True)
    assert raw == _CP.stdout
    assert parsed["final"] == "Rewrite body."   # Phase-1 cut applied
```
Implementation: add `return_raw: bool = False` to `run_skill`; the success-path return lives in the nested `_one_attempt` closure that `retry_with_backoff` wraps — return `(completed.stdout, parse_skill_output(completed.stdout)) if return_raw else parse_skill_output(completed.stdout)` from `_one_attempt` so the wrapper passes the tuple through. Default path unchanged (back-compat — all existing callers pass no flag). Run the test red→green; full suite green.

Commit:
```bash
git add evals/scripts/_shared.py tests/test_evals_shared.py
git commit -m "feat(evals): run_skill(return_raw=True) exposes raw response for fence probe

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 2: Write the probe script** `evals/scripts/probe_fence_emission.py`:

```python
"""Phase-2 gate probe for the commentary fence. Measures, on commentary-prone
inputs (EN+DE), the fraction of commentary-bearing outputs that fence commentary
with <!--HUMANIZER-AUDIT-->, plus a paired directive-off/on rewrite regression.
Subscription claude -p (run_skill strips ANTHROPIC_API_KEY). Resumable: one JSON
line per (input, rep) to /tmp/fence_probe_<cond>.log; re-run skips logged ids.

IMPORTANT — off vs on conditions: run_skill loads the INSTALLED skill (the symlinks
at ~/.claude/skills/humanizer/), NOT a repo file. So measuring 'off' vs 'on' requires
RE-INSTALLING the skill between conditions:
  on:  git checkout <directive commit>; re-point/refresh the install symlinks; run with --cond on
  off: git checkout <pre-directive commit>; refresh symlinks; run with --cond off
Do NOT try to reuse the SP3c fp_de_synthetic_*__rewrites.json sidecars for 'off' —
they store the PARSED `final` (commentary already merged/stripped), so they carry no
raw-fencing signal.

Usage: PYTHONPATH=. python3 evals/scripts/probe_fence_emission.py --cond {on|off} [REPS]
"""
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
from evals.scripts._shared import run_skill, parse_skill_output, _AUDIT_SENTINEL

# id: (lang, domain, text). Clean = preserve-note path; dirty = change-summary path. EN+DE.
# Clean bodies: copy the BODY (after frontmatter) from the named .md files.
# Dirty inputs: extract a case's "input" string from a pattern JSON — the files
# under evals/corpus/{lang}/patterns/*.json are dicts with a `cases` list; each
# case is `{"id":..., "input": "<text>", ...}`. Use cases[i]["input"]. Pick 1 EN
# + 1 DE marketing/promotional case with high AI-tell density.
INPUTS = {
  "de_clean_pflege": ("de","career", "<body of evals/corpus/de/human/synthetic/anschreiben_pflege_01.md>"),
  "en_clean_blog":   ("en","casual", "<body of evals/corpus/en/human/synthetic/casual_blog_draft_01.md>"),
  "de_dirty_mkt":    ("de","marketing","<the 'input' field of a high-density DE marketing case in evals/corpus/de/patterns/*.json>"),
  "en_dirty_mkt":    ("en","marketing","<the 'input' field of a high-density EN marketing case in evals/corpus/en/patterns/*.json>"),
}

def is_fenced(raw): return _AUDIT_SENTINEL in raw
def has_commentary(raw, parsed_final):
    return len(raw.strip()) > len(parsed_final.strip()) + 1

# loop: for id,(lang,dom,txt) in INPUTS x REPS:
#   raw, parsed = run_skill(txt, lang=lang, mode="full", domain=dom, return_raw=True)
#   rec = {id, rep, cond, has_commentary: has_commentary(raw, parsed["final"]),
#          is_fenced: is_fenced(raw), final: parsed["final"]}
#   append rec to /tmp/fence_probe_<cond>.log (skip if (id,rep) already logged)
```
Implement the loop + resumable append/skip mirroring `/tmp/de_chunk.py`. The `<body of …>`/`<the 'input' field …>` are the probe's data the engineer pastes from the named files (real, existing); they are data, not logic placeholders.

- [ ] **Step 3: Run both conditions (quota; chunk across reset windows).** Install the directive-ON skill → `... --cond on 5`; then check out the pre-directive commit + refresh the install → `... --cond off 5`. Restore the directive-on install afterwards.

- [ ] **Step 4: Compute the gate metrics** (Wilson CI — use `statsmodels.stats.proportion.proportion_confint(k, n, method="wilson")`; if statsmodels absent, hand-roll Wilson — no helper exists in `evals/scripts/`):
```
fence_emission_rate = fenced / commentary-bearing   (Wilson 95% CI; gate = lower bound ≥ 0.70)
```
Paired regression (match on/off by input id):
- mean normalized Levenshtein (rapidfuzz) between off/on `final` — bar **≤ 0.02, upper-95%-CI ≤ 0.05**; on the clean inputs require **byte-identical**.
- commentary-bearing rate (on) must NOT exceed the off rate.

- [ ] **Step 5: Record** in `docs/plans/fence-probe-results.md` (per-input has_commentary/fenced; pooled rate + Wilson CI; off/on edit-distance + commentary-rate). Independent-Skeptic verify the numbers from the logs before the Task-5 gate.

### Task 5: Gate decision + version bump (conditional)

**Files (only if gate passes):**
- Modify: `SKILL.md` frontmatter `version:`; `.claude-plugin/plugin.json` `"version"` (confirmed carries `3.5.1` — MUST bump or `verify_skill_install` flags a skill/manifest mismatch); `README.md` version history; any other file the grep surfaces. NB `marketplace.json` has no version field (spec §5's mention of it is stale) — do not chase it.

- [ ] **Step 1: Evaluate the gate (hard AND)**

Ship the SKILL.md directive (already committed in Task 3) as a real release ONLY if ALL hold:
- (i) `fence_emission_rate` lower-95%-CI **≥ 0.70**;
- (ii) off/on edit-distance ≤ 0.02 (upper-CI ≤ 0.05), preserve-subset byte-identical;
- (iii) commentary-bearing rate not risen;
- (iv) `pytest -q` green.

**If (i) fails:** do NOT bump/release the directive; open a follow-up to rework the directive wording (or `git revert` Task 3 and keep Phase 1 only). **If (ii)/(iii) fail:** the directive perturbs behaviour → `git revert` Task 3, reconsider. Record the decision either way.

- [ ] **Step 2: If gate passes — bump version**

```bash
cd <repo>
grep -rn "3\.5\.1" . --include='*.md' --include='*.json'   # find EVERY version ref (incl. .claude-plugin/plugin.json)
```
Set `version: 3.5.2` in `SKILL.md` frontmatter AND `"version": "3.5.2"` in `.claude-plugin/plugin.json`; add a `### 3.5.2` entry to `README.md` version history describing the fence; update any other ref the grep surfaces. Re-run `grep -rn "3\.5\.1" .` → expect zero version-string hits (only historical changelog lines mentioning prior versions remain).

- [ ] **Step 3: Commit + (push/tag/release on explicit user OK)**

```bash
git add SKILL.md .claude-plugin/plugin.json README.md
git commit -m "chore(release): v3.5.2 — commentary fence (gate passed: emission <CI>, edit-dist <d>)"
```
Tag `v3.5.2`, push, GH release — ONLY on explicit user OK (project rule: never push tags without OK).

---

## Self-Review (against the spec)

- **Spec §3a (parser, post-rewrite-region):** Task 1 (cut in `_strip_trailing_commentary`, which runs on the extracted region) + Task 2 (ordering integration test). ✓
- **Spec §3b (SKILL.md directive, trailing-only, excludes pre-rewrite audit):** Task 3. ✓
- **Spec §3c (emission rate + paired regression):** Task 4. ✓
- **Spec §4 acceptance (Phase-1 hard gate; Phase-2 ≥0.70 CI + edit-dist ≤0.02 + no commentary-rate rise):** Tasks 1-2 gate Phase 1; Task 5 gates Phase 2. ✓
- **Spec §5 versioning (Phase 1 no bump; Phase 2 v3.5.2 gated):** Task 1/2 no bump; Task 5 conditional bump. ✓
- **Spec §7 layered/residual:** Task 1 keeps `_COMMENTARY_RE` + the scorer guard as fallback (not removed). ✓
- **No placeholders:** Task 4's `<paste …>` are the probe's data inputs (engineer fills from named corpus files), not logic placeholders; flagged explicitly.
- **Type consistency:** `_AUDIT_SENTINEL` defined in Task 1, reused in Tasks 1/4; `parse_skill_output`/`_strip_trailing_commentary` signatures unchanged.
