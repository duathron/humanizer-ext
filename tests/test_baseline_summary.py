"""Gate: the hand-maintained summary_latest_* reports must carry the v3.6.0 marker line.

These reports are hand-maintained (no script writes them), so they have a history of
silently going stale. The gate asserts a v3.6.0-DISTINGUISHING marker line that is
ABSENT from the stale files — NOT a bare float (the prior DE 0.907 / EN 0.905 already
appeared in the stale files, so a bare-float gate would pass on a skipped refresh).
"""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPORTS = REPO / "evals" / "reports"


def test_summary_latest_en_matches_current_baseline():
    text = (REPORTS / "summary_latest_en.md").read_text(encoding="utf-8")
    assert "v3.6.0 baseline (run 2026-06-20, targeted EN)" in text, (
        "summary_latest_en.md missing the v3.6.0 targeted-Gate-2 marker — refresh skipped?"
    )
    assert "all-or-nothing 1.0" in text, "EN v3.6.0 #42/#34 headline figure missing"


def test_summary_latest_de_matches_current_baseline():
    text = (REPORTS / "summary_latest_de.md").read_text(encoding="utf-8")
    assert "v3.6.0 baseline (run 2026-06-20, targeted DE)" in text, (
        "summary_latest_de.md missing the v3.6.0 targeted-Gate-2 marker — refresh skipped?"
    )
    assert "per-term 0.95" in text, "DE v3.6.0 #42/#34 headline figure missing"
