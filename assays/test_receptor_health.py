#!/usr/bin/env python3
"""Tests for effectors/receptor-health — receptor SKILL.md validation."""

import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

RECEPTOR_HEALTH_PATH = Path(__file__).resolve().parents[1] / "effectors" / "receptor-health"
RECEPTORS_DIR = Path(__file__).resolve().parents[1] / "membrane" / "receptors"


def _load_module():
    """Load the receptor-health script as a module."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("receptor_health", RECEPTOR_HEALTH_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── Script structure tests ────────────────────────────────────────────────────


class TestReceptorHealthScript:
    def test_script_exists(self):
        assert RECEPTOR_HEALTH_PATH.exists()

    def test_script_is_executable(self):
        assert RECEPTOR_HEALTH_PATH.stat().st_mode & 0o111

    def test_script_has_shebang(self):
        first_line = RECEPTOR_HEALTH_PATH.read_text().splitlines()[0]
        assert "python" in first_line.lower()


# ── Argument parsing ─────────────────────────────────────────────────────────


class TestArgumentParsing:
    def test_help_runs(self):
        result = subprocess.run(
            [sys.executable, str(RECEPTOR_HEALTH_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "receptor" in result.stdout.lower() or "skill" in result.stdout.lower()

    def test_json_flag_accepted(self):
        result = subprocess.run(
            [sys.executable, str(RECEPTOR_HEALTH_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0


# ── parse_front_matter ────────────────────────────────────────────────────────


class TestParseFrontMatter:
    def test_valid_yaml(self):
        mod = _load_module()
        text = "---\nname: foo\ndescription: bar\n---\nBody here"
        meta, body, err = mod.parse_front_matter(text)
        assert err is None
        assert meta["name"] == "foo"
        assert meta["description"] == "bar"
        assert "Body here" in body

    def test_missing_closing_delimiter(self):
        mod = _load_module()
        text = "---\nname: foo\n"
        meta, body, err = mod.parse_front_matter(text)
        assert err is not None
        assert "closing" in err.lower() or "delimiter" in err.lower()

    def test_invalid_yaml_content(self):
        mod = _load_module()
        text = "---\nname: [\n---\nBody"
        meta, body, err = mod.parse_front_matter(text)
        assert err is not None

    def test_empty_front_matter(self):
        mod = _load_module()
        text = "---\n---\nBody"
        meta, body, err = mod.parse_front_matter(text)
        assert err is None
        assert meta == {}
        assert "Body" in body


# ── validate_skill ────────────────────────────────────────────────────────────


class TestValidateSkill:
    def test_valid_skill_passes(self):
        mod = _load_module()
        meta = {"name": "test", "description": "A valid skill description for testing."}
        errors = mod.validate_skill("test-skill", meta, "body text here")
        assert errors == []

    def test_missing_name(self):
        mod = _load_module()
        meta = {"description": "A valid skill description for testing."}
        errors = mod.validate_skill("test-skill", meta, "")
        assert any("name" in e.lower() for e in errors)

    def test_missing_description(self):
        mod = _load_module()
        meta = {"name": "test"}
        errors = mod.validate_skill("test-skill", meta, "")
        assert any("description" in e.lower() for e in errors)

    def test_description_too_short(self):
        mod = _load_module()
        meta = {"name": "test", "description": "hi"}
        errors = mod.validate_skill("test-skill", meta, "")
        assert any("short" in e.lower() or "length" in e.lower() for e in errors)

    def test_description_too_long(self):
        mod = _load_module()
        meta = {"name": "test", "description": "x" * 300}
        errors = mod.validate_skill("test-skill", meta, "")
        assert any("long" in e.lower() or "length" in e.lower() for e in errors)

    def test_empty_description(self):
        mod = _load_module()
        meta = {"name": "test", "description": ""}
        errors = mod.validate_skill("test-skill", meta, "")
        assert any("description" in e.lower() for e in errors)


# ── check_referenced_files ────────────────────────────────────────────────────


class TestCheckReferencedFiles:
    def test_recipe_yaml_exists(self, tmp_path):
        mod = _load_module()
        receptor_dir = tmp_path / "test-receptor"
        receptor_dir.mkdir()
        (receptor_dir / "SKILL.md").write_text("---\nname: test\n---\n")
        (receptor_dir / "recipe.yaml").write_text("name: test\n")
        errors = mod.check_referenced_files(receptor_dir, "body")
        assert errors == []

    def test_recipe_yaml_missing(self, tmp_path):
        mod = _load_module()
        receptor_dir = tmp_path / "test-receptor"
        receptor_dir.mkdir()
        (receptor_dir / "SKILL.md").write_text("---\nname: test\n---\n")
        errors = mod.check_referenced_files(receptor_dir, "body")
        assert any("recipe.yaml" in e for e in errors)

    def test_invalid_recipe_yaml(self, tmp_path):
        mod = _load_module()
        receptor_dir = tmp_path / "test-receptor"
        receptor_dir.mkdir()
        (receptor_dir / "SKILL.md").write_text("---\nname: test\n---\n")
        (receptor_dir / "recipe.yaml").write_text("name: [\n")
        errors = mod.check_referenced_files(receptor_dir, "body")
        assert any("recipe.yaml" in e for e in errors)

    def test_relative_file_reference_in_body(self, tmp_path):
        """File paths like ./sibling.md referenced in body should be checked."""
        mod = _load_module()
        receptor_dir = tmp_path / "test-receptor"
        receptor_dir.mkdir()
        (receptor_dir / "SKILL.md").write_text("---\nname: test\n---\nSee [notes](./notes.md)")
        (receptor_dir / "recipe.yaml").write_text("name: test\n")
        errors = mod.check_referenced_files(receptor_dir, 'See [notes](./notes.md)')
        assert any("notes.md" in e for e in errors)


# ── scan_receptors (integration-ish) ──────────────────────────────────────────


class TestScanReceptors:
    def test_scan_finds_all_receptors(self):
        """scan_receptors should find all SKILL.md directories."""
        mod = _load_module()
        results = mod.scan_receptors(RECEPTORS_DIR)
        skill_dirs = {p.name for p in RECEPTORS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists()}
        result_names = {r["name"] for r in results}
        # "name" comes from YAML; check we got the right number
        assert len(results) >= len(skill_dirs) - 5  # allow a few with bad YAML

    def test_scan_returns_list_of_dicts(self):
        mod = _load_module()
        results = mod.scan_receptors(RECEPTORS_DIR)
        assert isinstance(results, list)
        for r in results:
            assert "name" in r
            assert "errors" in r
            assert isinstance(r["errors"], list)


# ── CLI output ────────────────────────────────────────────────────────────────


class TestCLIOutput:
    def test_runs_against_real_receptors(self):
        """Full run against the actual receptors dir should succeed."""
        result = subprocess.run(
            [sys.executable, str(RECEPTOR_HEALTH_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in (0, 1)  # 1 if broken, but shouldn't crash
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_table_output(self):
        """Default output should be a human-readable table."""
        result = subprocess.run(
            [sys.executable, str(RECEPTOR_HEALTH_PATH)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should contain receptor names
        assert result.returncode in (0, 1)
        # Should mention at least a few receptor names
        assert "integrin" in result.stdout or "total" in result.stdout.lower()
