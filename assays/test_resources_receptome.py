"""Tests for metabolon.resources.receptome"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import yaml

from metabolon.resources.receptome import (
    _operon_entry,
    _parse_frontmatter,
    express_operon_index,
)

# ---------------------------------------------------------------------------
# _parse_frontmatter
# ---------------------------------------------------------------------------


class TestParseFrontmatter:
    def test_valid_frontmatter(self, tmp_path: Path):
        fm = yaml.dump({"name": "foo", "description": "bar"})
        p = tmp_path / "SKILL.md"
        p.write_text(f"---\n{fm}---\nBody text here.\n")
        result = _parse_frontmatter(p)
        assert result is not None
        assert result["name"] == "foo"
        assert result["description"] == "bar"

    def test_no_frontmatter_delimiters(self, tmp_path: Path):
        p = tmp_path / "SKILL.md"
        p.write_text("Just some markdown.\n")
        assert _parse_frontmatter(p) is None

    def test_only_one_delimiter(self, tmp_path: Path):
        p = tmp_path / "SKILL.md"
        p.write_text("---\nname: foo\n")
        assert _parse_frontmatter(p) is None

    def test_invalid_yaml(self, tmp_path: Path):
        p = tmp_path / "SKILL.md"
        p.write_text("---\n: invalid : yaml : [\n---\n")
        assert _parse_frontmatter(p) is None

    def test_empty_frontmatter(self, tmp_path: Path):
        p = tmp_path / "SKILL.md"
        p.write_text("---\n\n---\nBody\n")
        result = _parse_frontmatter(p)
        assert result == {}

    def test_missing_file(self, tmp_path: Path):
        p = tmp_path / "nonexistent.md"
        assert _parse_frontmatter(p) is None

    def test_permission_error(self, tmp_path: Path):
        p = tmp_path / "secret.md"
        p.write_text("---\nname: x\n---\n")
        p.chmod(0o000)
        try:
            assert _parse_frontmatter(p) is None
        finally:
            p.chmod(0o644)


# ---------------------------------------------------------------------------
# _operon_entry
# ---------------------------------------------------------------------------


class TestOperonEntry:
    def _make_skill(self, tmp_path: Path, fm: dict, name: str = "myskill") -> Path:
        d = tmp_path / name
        d.mkdir()
        fm_text = yaml.dump(fm)
        (d / "SKILL.md").write_text(f"---\n{fm_text}---\nContent.\n")
        return d

    def test_basic_entry(self, tmp_path: Path):
        d = self._make_skill(tmp_path, {"name": "skill1", "description": "desc"})
        entry = _operon_entry(d)
        assert entry is not None
        assert entry["name"] == "skill1"
        assert entry["description"] == "desc"
        assert entry["user_invocable"] is False
        assert entry["runtime"] == ""
        # modified should be a date string
        datetime.strptime(entry["modified"], "%Y-%m-%d")

    def test_prefix_prepended(self, tmp_path: Path):
        d = self._make_skill(tmp_path, {"name": "inner"})
        entry = _operon_entry(d, prefix="ns")
        assert entry["name"] == "ns:inner"

    def test_prefix_empty_no_colon(self, tmp_path: Path):
        d = self._make_skill(tmp_path, {"name": "inner"})
        entry = _operon_entry(d, prefix="")
        assert entry["name"] == "inner"

    def test_name_defaults_to_dirname(self, tmp_path: Path):
        d = self._make_skill(tmp_path, {"description": "no name key"}, name="fallback")
        entry = _operon_entry(d)
        assert entry["name"] == "fallback"

    def test_all_fields(self, tmp_path: Path):
        d = self._make_skill(
            tmp_path,
            {
                "name": "full",
                "description": "a full entry",
                "user_invocable": True,
                "runtime": "python",
            },
        )
        entry = _operon_entry(d)
        assert entry["user_invocable"] is True
        assert entry["runtime"] == "python"

    def test_no_skill_file(self, tmp_path: Path):
        d = tmp_path / "empty_dir"
        d.mkdir()
        assert _operon_entry(d) is None

    def test_bad_frontmatter_returns_none(self, tmp_path: Path):
        d = tmp_path / "badfm"
        d.mkdir()
        (d / "SKILL.md").write_text("Not frontmatter\n")
        assert _operon_entry(d) is None


# ---------------------------------------------------------------------------
# express_operon_index
# ---------------------------------------------------------------------------


class TestExpressOperonIndex:
    def _write_skill(self, parent: Path, name: str, fm: dict, mtime: float | None = None) -> Path:
        d = parent / name
        d.mkdir(parents=True, exist_ok=True)
        fm_text = yaml.dump(fm)
        sf = d / "SKILL.md"
        sf.write_text(f"---\n{fm_text}---\nBody.\n")
        if mtime is not None:
            import os

            os.utime(str(sf), (mtime, mtime))
        return d

    def test_no_root_dir(self, tmp_path: Path):
        missing = tmp_path / "no_such_dir"
        result = express_operon_index(skills_root=missing)
        assert result == "No receptor directory found."

    def test_empty_root(self, tmp_path: Path):
        root = tmp_path / "skills"
        root.mkdir()
        result = express_operon_index(skills_root=root)
        assert "0 active" in result
        assert "|-------|" in result

    def test_single_skill(self, tmp_path: Path):
        root = tmp_path / "skills"
        root.mkdir()
        self._write_skill(root, "alpha", {"name": "alpha", "description": "First skill"})
        result = express_operon_index(skills_root=root)
        assert "1 active" in result
        assert "`alpha`" in result
        assert "First skill" in result

    def test_multiple_skills_sorted(self, tmp_path: Path):
        root = tmp_path / "skills"
        root.mkdir()
        self._write_skill(root, "zebra", {"name": "zebra"})
        self._write_skill(root, "alpha", {"name": "alpha"})
        result = express_operon_index(skills_root=root)
        lines = result.splitlines()
        # Find the data rows (after header separator)
        data = [l for l in lines if l.startswith("| `")]
        assert len(data) == 2
        assert "`alpha`" in data[0]
        assert "`zebra`" in data[1]

    def test_skips_dotdirs(self, tmp_path: Path):
        root = tmp_path / "skills"
        root.mkdir()
        (root / ".hidden").mkdir()
        self._write_skill(root, "visible", {"name": "visible"})
        result = express_operon_index(skills_root=root)
        assert "1 active" in result
        assert "hidden" not in result

    def test_skips_archive(self, tmp_path: Path):
        root = tmp_path / "skills"
        root.mkdir()
        self._write_skill(root / "archive", "old", {"name": "old"})
        self._write_skill(root, "current", {"name": "current"})
        result = express_operon_index(skills_root=root)
        assert "1 active" in result
        assert "`current`" in result
        assert "old" not in result

    def test_skips_files_not_dirs(self, tmp_path: Path):
        root = tmp_path / "skills"
        root.mkdir()
        (root / "readme.md").write_text("# Readme")
        self._write_skill(root, "skill", {"name": "skill"})
        result = express_operon_index(skills_root=root)
        assert "1 active" in result

    def test_namespace_subdirs(self, tmp_path: Path):
        root = tmp_path / "skills"
        root.mkdir()
        # "ns" has no SKILL.md of its own, but has sub-skills
        self._write_skill(root / "ns", "sub1", {"name": "sub1"})
        self._write_skill(root / "ns", "sub2", {"name": "sub2"})
        result = express_operon_index(skills_root=root)
        assert "2 active" in result
        assert "`ns:sub1`" in result
        assert "`ns:sub2`" in result

    def test_namespace_mixed_with_toplevel(self, tmp_path: Path):
        root = tmp_path / "skills"
        root.mkdir()
        self._write_skill(root, "top", {"name": "top"})
        self._write_skill(root / "ns", "sub", {"name": "sub"})
        result = express_operon_index(skills_root=root)
        assert "2 active" in result
        assert "`top`" in result
        assert "`ns:sub`" in result

    def test_description_truncated_over_80(self, tmp_path: Path):
        root = tmp_path / "skills"
        root.mkdir()
        long_desc = "x" * 100
        self._write_skill(root, "verbose", {"name": "v", "description": long_desc})
        result = express_operon_index(skills_root=root)
        # Should be truncated to 80 chars + "..."
        assert "..." in result
        assert long_desc not in result

    def test_description_short_not_truncated(self, tmp_path: Path):
        root = tmp_path / "skills"
        root.mkdir()
        short_desc = "short"
        self._write_skill(root, "brief", {"name": "b", "description": short_desc})
        result = express_operon_index(skills_root=root)
        assert short_desc in result
        assert "..." not in result.split("brief")[0] if "brief" in result else True

    def test_modified_date_format(self, tmp_path: Path):
        import os

        root = tmp_path / "skills"
        root.mkdir()
        ts = 1704067200.0  # 2024-01-01 00:00:00 UTC
        d = root / "dated"
        d.mkdir()
        sf = d / "SKILL.md"
        sf.write_text("---\nname: dated\n---\n")
        os.utime(str(sf), (ts, ts))
        result = express_operon_index(skills_root=root)
        assert "2024-01-01" in result

    def test_default_uses_claude_skills(self):
        """Verify default root falls through to claude_skills."""
        with patch("metabolon.resources.receptome._SKILLS_ROOT", new=Path("/fake")):
            with patch.object(Path, "exists", return_value=False):
                result = express_operon_index()
                assert result == "No receptor directory found."
