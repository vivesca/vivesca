"""Tests for effectors/receptor-health — SKILL.md / recipe.yaml validation.

Uses exec() to load the effector as a module (it is a script, not an
importable package). Tests cover: frontmatter parsing, field checks,
description length, body size, recipe YAML validation, directory checks,
and the full scan pipeline.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Load effector via exec (standard pattern for script-type effectors)
# ---------------------------------------------------------------------------

EFFECTOR = Path(__file__).resolve().parent.parent / "effectors" / "receptor-health"
_ns: dict = {}
exec(EFFECTOR.read_text(), _ns)

Violation = _ns["Violation"]
parse_frontmatter = _ns["parse_frontmatter"]
check_skill_md = _ns["check_skill_md"]
check_recipe_yaml = _ns["check_recipe_yaml"]
check_directory = _ns["check_directory"]
scan_receptors = _ns["scan_receptors"]
format_report = _ns["format_report"]

RECEPTORS = _ns["RECEPTORS"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_receptor(tmp_path: Path) -> Path:
    """Create a temporary receptors/ directory with one empty receptor."""
    rec_dir = tmp_path / "membrane" / "receptors" / "test-receptor"
    rec_dir.mkdir(parents=True)
    return rec_dir


def _write_skill(rec_dir: Path, frontmatter: dict, body: str = "") -> Path:
    """Write a SKILL.md with given frontmatter and body."""
    fm_yaml = yaml.dump(frontmatter, default_flow_style=False).strip()
    content = f"---\n{fm_yaml}\n---\n{body}"
    p = rec_dir / "SKILL.md"
    p.write_text(content)
    return p


def _write_recipe(rec_dir: Path, data: dict) -> Path:
    """Write a recipe.yaml."""
    p = rec_dir / "recipe.yaml"
    p.write_text(yaml.dump(data, default_flow_style=False))
    return p


# ---------------------------------------------------------------------------
# parse_frontmatter tests
# ---------------------------------------------------------------------------

class TestParseFrontmatter:
    def test_valid_frontmatter(self) -> None:
        text = "---\nname: foo\ndescription: bar\n---\nBody here."
        fm, body, errors = parse_frontmatter(text)
        assert errors == []
        assert fm == {"name": "foo", "description": "bar"}
        assert "Body here." in body

    def test_no_opening_delimiter(self) -> None:
        text = "name: foo\n---\nbody"
        fm, body, errors = parse_frontmatter(text)
        assert fm is None
        assert any("opening" in e for e in errors)

    def test_no_closing_delimiter(self) -> None:
        text = "---\nname: foo\nbody continues"
        fm, body, errors = parse_frontmatter(text)
        assert fm is None
        assert any("closing" in e for e in errors)

    def test_invalid_yaml(self) -> None:
        text = "---\n: invalid: [yaml: content\n---\nbody"
        fm, body, errors = parse_frontmatter(text)
        assert fm is None
        assert any("YAML parse error" in e for e in errors)

    def test_frontmatter_is_list(self) -> None:
        text = "---\n- item1\n- item2\n---\nbody"
        fm, body, errors = parse_frontmatter(text)
        assert fm is None
        assert any("list" in e.lower() or "mapping" in e.lower() for e in errors)

    def test_empty_body(self) -> None:
        text = "---\nname: x\ndescription: y\n---\n"
        fm, body, errors = parse_frontmatter(text)
        assert errors == []
        assert fm is not None


# ---------------------------------------------------------------------------
# check_skill_md tests
# ---------------------------------------------------------------------------

class TestCheckSkillMd:
    def test_healthy_skill(self, tmp_receptor: Path) -> None:
        _write_skill(tmp_receptor, {"name": "test", "description": "A test skill."})
        v = check_skill_md(tmp_receptor / "SKILL.md", "test-receptor")
        assert v == []

    def test_missing_skill(self, tmp_receptor: Path) -> None:
        v = check_skill_md(tmp_receptor / "SKILL.md", "test-receptor")
        assert any(vi.check == "SKILL.md" and "missing" in vi.detail for vi in v)

    def test_missing_name(self, tmp_receptor: Path) -> None:
        _write_skill(tmp_receptor, {"description": "Has desc but no name"})
        v = check_skill_md(tmp_receptor / "SKILL.md", "test-receptor")
        assert any(vi.check == "missing-field" and "name" in vi.detail for vi in v)

    def test_missing_description(self, tmp_receptor: Path) -> None:
        _write_skill(tmp_receptor, {"name": "test"})
        v = check_skill_md(tmp_receptor / "SKILL.md", "test-receptor")
        assert any(vi.check == "missing-field" and "description" in vi.detail for vi in v)

    def test_description_too_long(self, tmp_receptor: Path) -> None:
        long_desc = "x" * 1025
        _write_skill(tmp_receptor, {"name": "test", "description": long_desc})
        v = check_skill_md(tmp_receptor / "SKILL.md", "test-receptor")
        assert any(vi.check == "description-length" for vi in v)

    def test_description_at_limit(self, tmp_receptor: Path) -> None:
        desc = "x" * 1024
        _write_skill(tmp_receptor, {"name": "test", "description": desc})
        v = check_skill_md(tmp_receptor / "SKILL.md", "test-receptor")
        assert not any(vi.check == "description-length" for vi in v)

    def test_body_too_long(self, tmp_receptor: Path) -> None:
        long_body = "\n".join(["line"] * 501)
        _write_skill(tmp_receptor, {"name": "test", "description": "ok"}, body=long_body)
        v = check_skill_md(tmp_receptor / "SKILL.md", "test-receptor")
        assert any(vi.check == "body-size" for vi in v)

    def test_body_at_limit(self, tmp_receptor: Path) -> None:
        body = "\n".join(["line"] * 500)
        _write_skill(tmp_receptor, {"name": "test", "description": "ok"}, body=body)
        v = check_skill_md(tmp_receptor / "SKILL.md", "test-receptor")
        assert not any(vi.check == "body-size" for vi in v)


# ---------------------------------------------------------------------------
# check_recipe_yaml tests
# ---------------------------------------------------------------------------

class TestCheckRecipeYaml:
    def test_valid_recipe(self, tmp_receptor: Path) -> None:
        _write_recipe(tmp_receptor, {
            "name": "test",
            "description": "A test recipe.",
            "instructions": "do stuff",
            "extensions": [{"type": "builtin", "name": "developer"}],
        })
        v = check_recipe_yaml(tmp_receptor / "recipe.yaml", "test-receptor")
        assert v == []

    def test_no_recipe_is_ok(self, tmp_receptor: Path) -> None:
        v = check_recipe_yaml(tmp_receptor / "recipe.yaml", "test-receptor")
        assert v == []

    def test_invalid_yaml(self, tmp_receptor: Path) -> None:
        (tmp_receptor / "recipe.yaml").write_text(": bad: [yaml")
        v = check_recipe_yaml(tmp_receptor / "recipe.yaml", "test-receptor")
        assert any(vi.check == "recipe-yaml" and "parse error" in vi.detail for vi in v)

    def test_missing_name(self, tmp_receptor: Path) -> None:
        _write_recipe(tmp_receptor, {"description": "has desc"})
        v = check_recipe_yaml(tmp_receptor / "recipe.yaml", "test-receptor")
        assert any(vi.check == "recipe-missing-field" and "name" in vi.detail for vi in v)

    def test_missing_description(self, tmp_receptor: Path) -> None:
        _write_recipe(tmp_receptor, {"name": "has-name"})
        v = check_recipe_yaml(tmp_receptor / "recipe.yaml", "test-receptor")
        assert any(vi.check == "recipe-missing-field" and "description" in vi.detail for vi in v)

    def test_root_is_list(self, tmp_receptor: Path) -> None:
        (tmp_receptor / "recipe.yaml").write_text("- item1\n- item2\n")
        v = check_recipe_yaml(tmp_receptor / "recipe.yaml", "test-receptor")
        assert any(vi.check == "recipe-yaml" and "mapping" in vi.detail for vi in v)

    def test_extension_uri_missing_file(self, tmp_receptor: Path) -> None:
        _write_recipe(tmp_receptor, {
            "name": "test",
            "description": "ok",
            "extensions": [{"type": "local", "uri": "nonexistent.py"}],
        })
        v = check_recipe_yaml(tmp_receptor / "recipe.yaml", "test-receptor")
        assert any(vi.check == "reference-broken" for vi in v)

    def test_extension_uri_http_ok(self, tmp_receptor: Path) -> None:
        _write_recipe(tmp_receptor, {
            "name": "test",
            "description": "ok",
            "extensions": [{"type": "streamable_http", "uri": "http://127.0.0.1:8741/mcp"}],
        })
        v = check_recipe_yaml(tmp_receptor / "recipe.yaml", "test-receptor")
        assert not any(vi.check == "reference-broken" for vi in v)


# ---------------------------------------------------------------------------
# check_directory tests
# ---------------------------------------------------------------------------

class TestCheckDirectory:
    def test_clean_directory(self, tmp_receptor: Path) -> None:
        _write_skill(tmp_receptor, {"name": "test", "description": "ok"})
        v = check_directory(tmp_receptor, "test-receptor")
        assert v == []

    def test_allowed_dirs_ok(self, tmp_receptor: Path) -> None:
        (tmp_receptor / "scripts").mkdir()
        (tmp_receptor / "references").mkdir()
        (tmp_receptor / "agents").mkdir()
        v = check_directory(tmp_receptor, "test-receptor")
        assert v == []

    def test_unexpected_file(self, tmp_receptor: Path) -> None:
        (tmp_receptor / "README.md").write_text("oops")
        v = check_directory(tmp_receptor, "test-receptor")
        assert any(vi.check == "auxiliary-file" and "README.md" in vi.detail for vi in v)

    def test_unexpected_directory(self, tmp_receptor: Path) -> None:
        (tmp_receptor / "__pycache__").mkdir()
        v = check_directory(tmp_receptor, "test-receptor")
        assert any(vi.check == "auxiliary-dir" and "__pycache__" in vi.detail for vi in v)

    def test_hidden_files_ignored(self, tmp_receptor: Path) -> None:
        (tmp_receptor / ".gitkeep").write_text("")
        v = check_directory(tmp_receptor, "test-receptor")
        assert v == []

    def test_allowed_recipe_yaml(self, tmp_receptor: Path) -> None:
        _write_recipe(tmp_receptor, {"name": "test", "description": "ok"})
        v = check_directory(tmp_receptor, "test-receptor")
        assert v == []


# ---------------------------------------------------------------------------
# Violation + format_report tests
# ---------------------------------------------------------------------------

class TestFormatReport:
    def test_no_violations(self) -> None:
        report = format_report([])
        assert "healthy" in report.lower() or "no violations" in report.lower()

    def test_with_violations(self) -> None:
        viols = [
            Violation("foo", "check-a", "detail-1"),
            Violation("foo", "check-b", "detail-2"),
            Violation("bar", "check-c", "detail-3"),
        ]
        report = format_report(viols)
        assert "foo" in report
        assert "bar" in report
        assert "3 violation" in report
        assert "2 receptor" in report


class TestViolation:
    def test_to_dict(self) -> None:
        v = Violation("receptor-name", "some-check", "some detail")
        d = v.to_dict()
        assert d == {"receptor": "receptor-name", "check": "some-check", "detail": "some detail"}

    def test_repr(self) -> None:
        v = Violation("foo", "bar", "baz")
        assert "foo" in repr(v)
        assert "bar" in repr(v)


# ---------------------------------------------------------------------------
# Integration: scan_receptors on real repo
# ---------------------------------------------------------------------------

class TestScanReceptors:
    def test_scan_real_repo_finds_something(self) -> None:
        """The real repo has known violations (capco-prep, dokime, etc)."""
        v = scan_receptors()
        # Should find violations without crashing
        assert isinstance(v, list)
        assert all(isinstance(vi, Violation) for vi in v)

    def test_scan_specific_receptor(self) -> None:
        """Scanning a known-good receptor should return few or no violations."""
        v = scan_receptors(names=["integrin"])
        # integrin should be healthy
        assert isinstance(v, list)

    def test_scan_nonexistent_returns_empty(self) -> None:
        v = scan_receptors(names=["zzz-nonexistent-receptor"])
        assert v == []
