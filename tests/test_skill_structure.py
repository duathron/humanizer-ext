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


UNIVERSAL_PATTERN_IDS = {6, 14, 15, 17, 18, 19, 25, 26, 29, 38, 39, 40}


def _pattern_ids_in_file(path: Path) -> set[int]:
    """Find lines like '### 14. Em Dash Overuse...' and return the IDs."""
    text = path.read_text(encoding="utf-8")
    return {
        int(m.group(1))
        for m in re.finditer(r"^### (\d+)\.\s", text, re.MULTILINE)
    }


def test_universal_pack_exists():
    assert (REPO_ROOT / "patterns" / "_universal.md").is_file()


def test_universal_pack_contains_expected_patterns():
    ids = _pattern_ids_in_file(REPO_ROOT / "patterns" / "_universal.md")
    assert ids == UNIVERSAL_PATTERN_IDS, (
        f"_universal.md pattern IDs differ from spec: "
        f"missing {UNIVERSAL_PATTERN_IDS - ids}, extra {ids - UNIVERSAL_PATTERN_IDS}"
    )


EN_PATTERN_IDS = {
    1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 16, 20, 21, 22, 23, 24,
    27, 28, 30, 31, 32, 33, 34, 35, 36, 37,
}


def test_en_pack_exists():
    assert (REPO_ROOT / "patterns" / "en.md").is_file()


def test_en_pack_contains_expected_patterns():
    ids = _pattern_ids_in_file(REPO_ROOT / "patterns" / "en.md")
    assert ids == EN_PATTERN_IDS, (
        f"en.md pattern IDs differ from spec: "
        f"missing {EN_PATTERN_IDS - ids}, extra {ids - EN_PATTERN_IDS}"
    )


def test_en_pack_includes_personality_section():
    text = (REPO_ROOT / "patterns" / "en.md").read_text(encoding="utf-8")
    assert "## PERSONALITY AND SOUL" in text


def test_universal_and_en_packs_are_disjoint():
    """No pattern ID appears in both packs."""
    universal = _pattern_ids_in_file(REPO_ROOT / "patterns" / "_universal.md")
    en = _pattern_ids_in_file(REPO_ROOT / "patterns" / "en.md")
    assert universal & en == set(), f"overlapping pattern IDs: {universal & en}"


def test_en_overrides_exists():
    assert (REPO_ROOT / "domains" / "en_overrides.md").is_file()


def test_en_overrides_contains_override_table_and_guidance():
    text = (REPO_ROOT / "domains" / "en_overrides.md").read_text(encoding="utf-8")
    # Sentinel strings from the existing SKILL.md sections we're extracting
    assert "Domain overrides" in text
    assert "Domain-specific guidance" in text
    # Override table must mention all 5 domain columns
    for domain in ["academic", "legal", "technical", "marketing", "casual"]:
        assert domain in text.lower(), f"missing domain mention: {domain}"


def test_en_overrides_pattern_ids_exist_in_packs():
    """Every pattern ID referenced in en_overrides.md must be in en.md or _universal.md."""
    overrides_text = (REPO_ROOT / "domains" / "en_overrides.md").read_text(encoding="utf-8")
    referenced = {int(m.group(1)) for m in re.finditer(r"#(\d+)\b", overrides_text)}
    defined = (
        _pattern_ids_in_file(REPO_ROOT / "patterns" / "en.md")
        | _pattern_ids_in_file(REPO_ROOT / "patterns" / "_universal.md")
    )
    orphans = referenced - defined
    assert not orphans, f"en_overrides.md references undefined pattern IDs: {orphans}"
