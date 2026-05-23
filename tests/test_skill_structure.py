"""Repo-structure sanity tests. No API calls."""
from pathlib import Path
import re
import yaml

REPO_ROOT = Path(__file__).parent.parent


def _parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise AssertionError(f"{path}: no YAML frontmatter found")
    return yaml.safe_load(match.group(1))


def test_skill_md_frontmatter_valid():
    fm = _parse_frontmatter(REPO_ROOT / "SKILL.md")
    assert fm.get("name") == "humanizer"
    assert "description" in fm
    assert "version" in fm


def test_skill_md_description_under_plugin_limit():
    """Claude Code plugin frontmatter caps description at 1024 chars."""
    fm = _parse_frontmatter(REPO_ROOT / "SKILL.md")
    assert len(fm["description"]) <= 1024, (
        f"description is {len(fm['description'])} chars, "
        f"exceeds Claude Code 1024-char limit"
    )
