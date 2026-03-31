"""Tests for metabolon.resources.receptome — receptor (skill) index resource."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from metabolon.resources.receptome import (
    _operon_entry,
    _parse_frontmatter,
    express_operon_index,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_skill(directory: Path, name: str, frontmatter: dict, body: str = "") -> Path:
    """Create a skill directory with a SKILL.md containing YAML frontmatter."""
    skill_dir = directory / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    fm_yaml = yaml.dump(frontmatter, default_flow_style=False).strip()
    content = f"---\n{fm_yaml}\n---\n{body}"
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


# ---------------------------------------------------------------------------
# _parse_frontmatter
# ---------------------------------------------------------------------------

class TestParseFrontmatter:
    """Tests for _parse_frontmatter(path)."""

    def test_valid_frontmatter(self, tmp_path: Path) -> None:
        skill = _write_skill(tmp_path, "alpha", {"name": "Alpha", "description": "desc"})
        result = _parse_frontmatter(skill / "SKILL.md")
        assert result is not None
        assert result["name"] == "Alpha"
        assert result["description"] == "desc"

    def test_missing_file_returns_none(self, tmp_path: Path) -> None:
        result = _parse_frontmatter(tmp_path / "nonexistent.md")
        assert result is None

    def test_no_frontmatter_returns_none(self, tmp_path: Path) -> None:
        p = tmp_path / "no_fm.md"
        p.write_text("Just some text without frontmatter.")
        result = _parse_frontmatter(p)
        assert result is None

    def test_incomplete_frontmatter_returns_none(self, tmp_path: Path) -> None:
        p = tmp_path / "incomplete.md"
        p.write_text("---\nname: Broken\n")  # Only one --- separator
        result = _parse_frontmatter(p)
        assert result is None

    def test_invalid_yaml_returns_none(self, tmp_path: Path) -> None:
        p = tmp_path / "bad_yaml.md"
        p.write_text("---\n: invalid yaml [\n---\nbody")
        result = _parse_frontmatter(p)
        assert result is None

    def test_empty_frontmatter_returns_empty_dict(self, tmp_path: Path) -> None:
        p = tmp_path / "empty_fm.md"
        p.write_text("---\n\n---\nbody")
        result = _parse_frontmatter(p)
        assert result == {}

    def test_unreadable_file_returns_none(self, tmp_path: Path) -> None:
        p = tmp_path / "unreadable.md"
        p.write_text("---\nname: X\n---\nbody")
        p.chmod(0o000)
        try:
            result = _parse_frontmatter(p)
            assert result is None
        finally:
            p.chmod(0o644)  # cleanup


# ---------------------------------------------------------------------------
# _operon_entry
# ---------------------------------------------------------------------------

class TestOperonEntry:
    """Tests for _operon_entry(skill_dir, prefix)."""

    def test_basic_entry(self, tmp_path: Path) -> None:
        skill_dir = _write_skill(tmp_path, "my_skill", {
            "name": "My Skill",
            "description": "A test skill",
            "user_invocable": True,
            "runtime": "goose",
        })
        result = _operon_entry(skill_dir)
        assert result is not None
        assert result["name"] == "My Skill"
        assert result["description"] == "A test skill"
        assert result["user_invocable"] is True
        assert result["runtime"] == "goose"
        # modified should be today's date (just created)
        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        assert result["modified"] == today

    def test_prefix_prepended(self, tmp_path: Path) -> None:
        skill_dir = _write_skill(tmp_path, "sub_skill", {"name": "SubSkill"})
        result = _operon_entry(skill_dir, prefix="namespace")
        assert result is not None
        assert result["name"] == "namespace:SubSkill"

    def test_dir_without_skill_md_returns_none(self, tmp_path: Path) -> None:
        d = tmp_path / "empty_dir"
        d.mkdir()
        result = _operon_entry(d)
        assert result is None

    def test_defaults_when_fm_missing_fields(self, tmp_path: Path) -> None:
        skill_dir = _write_skill(tmp_path, "minimal", {})
        result = _operon_entry(skill_dir)
        assert result is not None
        assert result["name"] == "minimal"  # falls back to dir name
        assert result["description"] == ""
        assert result["user_invocable"] is False
        assert result["runtime"] == ""

    def test_name_from_frontmatter_overrides_dirname(self, tmp_path: Path) -> None:
        skill_dir = _write_skill(tmp_path, "dir_name", {"name": "Custom Name"})
        result = _operon_entry(skill_dir)
        assert result is not None
        assert result["name"] == "Custom Name"

    def test_invalid_frontmatter_returns_none(self, tmp_path: Path) -> None:
        d = tmp_path / "bad_fm"
        d.mkdir()
        (d / "SKILL.md").write_text("No frontmatter here")
        result = _operon_entry(d)
        assert result is None


# ---------------------------------------------------------------------------
# express_operon_index
# ---------------------------------------------------------------------------

class TestExpressOperonIndex:
    """Tests for express_operon_index(skills_root)."""

    def test_empty_directory(self, tmp_path: Path) -> None:
        root = tmp_path / "skills"
        root.mkdir()
        result = express_operon_index(skills_root=root)
        assert "Skill Index (0 active)" in result

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        root = tmp_path / "no_such_dir"
        result = express_operon_index(skills_root=root)
        assert result == "No receptor directory found."

    def test_single_top_level_skill(self, tmp_path: Path) -> None:
        root = tmp_path / "skills"
        root.mkdir()
        _write_skill(root, "alpha", {
            "name": "Alpha",
            "description": "First skill",
        })
        result = express_operon_index(skills_root=root)
        assert "Skill Index (1 active)" in result
        assert "`Alpha`" in result
        assert "First skill" in result

    def test_multiple_skills_sorted(self, tmp_path: Path) -> None:
        root = tmp_path / "skills"
        root.mkdir()
        _write_skill(root, "zebra", {"name": "Zebra", "description": "Last"})
        _write_skill(root, "alpha", {"name": "Alpha", "description": "First"})
        result = express_operon_index(skills_root=root)
        assert "Skill Index (2 active)" in result
        # Alpha should appear before Zebra (sorted)
        alpha_pos = result.index("Alpha")
        zebra_pos = result.index("Zebra")
        assert alpha_pos < zebra_pos

    def test_namespace_subdirectories(self, tmp_path: Path) -> None:
        root = tmp_path / "skills"
        root.mkdir()
        ns = root / "namespace"
        ns.mkdir()
        _write_skill(ns, "sub", {"name": "Sub", "description": "Namespaced"})
        result = express_operon_index(skills_root=root)
        assert "Skill Index (1 active)" in result
        assert "`namespace:Sub`" in result

    def test_archive_directory_skipped(self, tmp_path: Path) -> None:
        root = tmp_path / "skills"
        root.mkdir()
        _write_skill(root, "archive", {"name": "Archived", "description": "Old"})
        _write_skill(root, "active", {"name": "Active", "description": "Current"})
        result = express_operon_index(skills_root=root)
        assert "Skill Index (1 active)" in result
        assert "Active" in result
        assert "Archived" not in result

    def test_dot_directories_skipped(self, tmp_path: Path) -> None:
        root = tmp_path / "skills"
        root.mkdir()
        _write_skill(root, ".hidden", {"name": "Hidden", "description": "Should not appear"})
        _write_skill(root, "visible", {"name": "Visible", "description": "Should appear"})
        result = express_operon_index(skills_root=root)
        assert "Skill Index (1 active)" in result
        assert "Visible" in result
        assert "Hidden" not in result

    def test_long_description_truncated(self, tmp_path: Path) -> None:
        root = tmp_path / "skills"
        root.mkdir()
        long_desc = "A" * 120
        _write_skill(root, "verbose", {"name": "Verbose", "description": long_desc})
        result = express_operon_index(skills_root=root)
        assert "Skill Index (1 active)" in result
        # Description should be truncated at 80 chars with "..."
        assert "A" * 80 + "..." in result
        assert "A" * 120 not in result

    def test_exact_80_char_description_not_truncated(self, tmp_path: Path) -> None:
        root = tmp_path / "skills"
        root.mkdir()
        desc = "B" * 80
        _write_skill(root, "exact", {"name": "Exact", "description": desc})
        result = express_operon_index(skills_root=root)
        assert "Skill Index (1 active)" in result
        assert "B" * 80 in result
        assert "..." not in result.splitlines()[2]  # table row shouldn't have ...

    def test_table_headers_present(self, tmp_path: Path) -> None:
        root = tmp_path / "skills"
        root.mkdir()
        _write_skill(root, "x", {"name": "X", "description": "test"})
        result = express_operon_index(skills_root=root)
        assert "| Skill | Description | Modified |" in result
        assert "|-------|-------------|----------|" in result

    def test_default_root_uses_claude_skills(self) -> None:
        """When skills_root is None, it should fall back to claude_skills."""
        # Just verify it doesn't crash and produces output
        result = express_operon_index(skills_root=None)
        assert isinstance(result, str)
        # Should contain either a skill index or the not-found message
        assert "Skill Index" in result or result == "No receptor directory found."

    def test_namespace_without_subdirs_produces_no_entry(self, tmp_path: Path) -> None:
        root = tmp_path / "skills"
        root.mkdir()
        ns = root / "empty_ns"
        ns.mkdir()
        # namespace dir exists but has no sub-skill dirs, and no SKILL.md of its own
        result = express_operon_index(skills_root=root)
        assert "Skill Index (0 active)" in result

    def test_namespace_dir_with_own_skill_md(self, tmp_path: Path) -> None:
        """A namespace dir that ALSO has its own SKILL.md is treated as a top-level skill."""
        root = tmp_path / "skills"
        root.mkdir()
        ns = root / "dual"
        ns.mkdir()
        # Give the namespace dir its own SKILL.md
        fm_yaml = yaml.dump({"name": "Dual", "description": "Top-level"}, default_flow_style=False).strip()
        (ns / "SKILL.md").write_text(f"---\n{fm_yaml}\n---\n")
        result = express_operon_index(skills_root=root)
        assert "Skill Index (1 active)" in result
        assert "`Dual`" in result
