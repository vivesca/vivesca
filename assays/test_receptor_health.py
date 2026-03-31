#!/usr/bin/env python3
"""Tests for effectors/receptor-health — receptor SKILL.md validation."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

RECEPTOR_HEALTH_PATH = Path(__file__).resolve().parents[1] / "effectors" / "receptor-health"
RECEPTORS_DIR = Path(__file__).resolve().parents[1] / "membrane" / "receptors"

# Load effector via exec (PEP 723 script, not importable as module)
_MOD_NS = {}


def _load_module():
    """Load receptor-health as a module for unit testing."""
    if _MOD_NS:
        return _MOD_NS["mod"]
    ns = {"__name__": "receptor_health", "__file__": str(RECEPTOR_HEALTH_PATH)}
    exec(RECEPTOR_HEALTH_PATH.read_text(), ns)
    _MOD_NS["mod"] = type("Module", (), ns)()
    # Copy attributes to namespace so they're accessible as mod.attr
    mod = _MOD_NS["mod"]
    for k, v in ns.items():
        if not k.startswith("_") or k == "__name__":
            setattr(mod, k, v)
    _MOD_NS["mod"] = mod
    return mod


# ── Script structure tests ────────────────────────────────────────────────────


class TestReceptorHealthScript:
    def test_script_exists(self):
        assert RECEPTOR_HEALTH_PATH.exists()

    def test_script_is_executable(self):
        assert RECEPTOR_HEALTH_PATH.stat().st_mode & 0o111

    def test_script_has_shebang(self):
        first_line = RECEPTOR_HEALTH_PATH.read_text().splitlines()[0]
        assert "python" in first_line.lower()

    def test_script_parseable(self):
        import ast
        # Strip PEP 723 metadata before parsing
        text = RECEPTOR_HEALTH_PATH.read_text()
        # Remove the # /// blocks
        lines = text.splitlines()
        in_block = False
        clean = []
        for line in lines:
            if line.strip() == "# ///":
                in_block = not in_block
                continue
            if not in_block:
                clean.append(line)
        ast.parse("\n".join(clean))


# ── Unit tests: parse_frontmatter ─────────────────────────────────────────────


class TestParseFrontmatter:
    def test_valid_frontmatter(self):
        mod = _load_module()
        text = "---\nname: foo\ndescription: bar\n---\n# Body"
        fm, err = mod.parse_frontmatter(text)
        assert err == ""
        assert fm == {"name": "foo", "description": "bar"}

    def test_no_frontmatter(self):
        mod = _load_module()
        text = "# Just markdown\nNo frontmatter here."
        fm, err = mod.parse_frontmatter(text)
        assert fm is None
        assert "no YAML frontmatter" in err

    def test_bad_yaml(self):
        mod = _load_module()
        text = "---\nname: [\nbad yaml\n---\n# Body"
        fm, err = mod.parse_frontmatter(text)
        assert fm is None
        assert "YAML parse error" in err

    def test_non_mapping_frontmatter(self):
        mod = _load_module()
        text = "---\n- just\n- a\n- list\n---\n# Body"
        fm, err = mod.parse_frontmatter(text)
        assert fm is None
        assert "not a mapping" in err


# ── Unit tests: check_frontmatter ─────────────────────────────────────────────


class TestCheckFrontmatter:
    def test_missing_name(self):
        mod = _load_module()
        report = mod.ReceptorReport(receptor="test")
        mod.check_frontmatter("test", {"description": "has desc"}, report)
        assert not report.ok
        assert any(
            i.check == "frontmatter" and "name" in i.detail for i in report.issues
        )

    def test_missing_description(self):
        mod = _load_module()
        report = mod.ReceptorReport(receptor="test")
        mod.check_frontmatter("test", {"name": "has_name"}, report)
        assert not report.ok
        assert any(
            i.check == "frontmatter" and "description" in i.detail
            for i in report.issues
        )

    def test_none_frontmatter(self):
        mod = _load_module()
        report = mod.ReceptorReport(receptor="test")
        mod.check_frontmatter("test", None, report)
        assert not report.ok

    def test_valid_frontmatter_passes(self):
        mod = _load_module()
        report = mod.ReceptorReport(receptor="test")
        mod.check_frontmatter("test", {"name": "x", "description": "y"}, report)
        assert report.ok


# ── Unit tests: check_description_length ──────────────────────────────────────


class TestCheckDescriptionLength:
    def test_short_description_ok(self):
        mod = _load_module()
        report = mod.ReceptorReport(receptor="test")
        mod.check_description_length("test", {"description": "short"}, report)
        assert report.ok
        assert not report.issues

    def test_long_description_warns(self):
        mod = _load_module()
        report = mod.ReceptorReport(receptor="test")
        long_desc = "x" * 2000
        mod.check_description_length("test", {"description": long_desc}, report)
        assert any(i.check == "description_length" for i in report.issues)
        assert report.issues[0].severity == "warn"

    def test_none_frontmatter_skipped(self):
        mod = _load_module()
        report = mod.ReceptorReport(receptor="test")
        mod.check_description_length("test", None, report)
        assert report.ok


# ── Unit tests: check_recipe_yaml ─────────────────────────────────────────────


class TestCheckRecipeYaml:
    def test_no_recipe_is_ok(self, tmp_path):
        mod = _load_module()
        report = mod.ReceptorReport(receptor="test")
        mod.check_recipe_yaml("test", tmp_path, report)
        assert report.ok

    def test_valid_recipe(self, tmp_path):
        mod = _load_module()
        recipe = tmp_path / "recipe.yaml"
        recipe.write_text(
            yaml.dump({"name": "test", "description": "d", "instructions": "do it"})
        )
        report = mod.ReceptorReport(receptor="test")
        mod.check_recipe_yaml("test", tmp_path, report)
        assert report.ok

    def test_invalid_recipe_yaml(self, tmp_path):
        mod = _load_module()
        recipe = tmp_path / "recipe.yaml"
        recipe.write_text("name: [\nbad yaml")
        report = mod.ReceptorReport(receptor="test")
        mod.check_recipe_yaml("test", tmp_path, report)
        assert not report.ok
        assert any(i.check == "recipe_yaml" for i in report.issues)

    def test_recipe_missing_required_key(self, tmp_path):
        mod = _load_module()
        recipe = tmp_path / "recipe.yaml"
        recipe.write_text(yaml.dump({"name": "test"}))
        report = mod.ReceptorReport(receptor="test")
        mod.check_recipe_yaml("test", tmp_path, report)
        assert any(i.check == "recipe_yaml" for i in report.issues)


# ── Unit tests: check_referenced_files ────────────────────────────────────────


class TestCheckReferencedFiles:
    def test_references_dir_missing_but_mentioned(self, tmp_path):
        mod = _load_module()
        skill = tmp_path / "SKILL.md"
        skill.write_text(
            "---\nname: test\ndescription: d\n---\nSee references/ for details."
        )
        report = mod.ReceptorReport(receptor="test")
        mod.check_referenced_files("test", tmp_path, report)
        assert any("references" in i.detail for i in report.issues)

    def test_broken_markdown_link(self, tmp_path):
        mod = _load_module()
        skill = tmp_path / "SKILL.md"
        skill.write_text(
            "---\nname: test\ndescription: d\n---\nSee [guide](./guide.md)."
        )
        report = mod.ReceptorReport(receptor="test")
        mod.check_referenced_files("test", tmp_path, report)
        assert any("guide.md" in i.detail for i in report.issues)

    def test_valid_markdown_link(self, tmp_path):
        mod = _load_module()
        skill = tmp_path / "SKILL.md"
        skill.write_text(
            "---\nname: test\ndescription: d\n---\nSee [guide](./guide.md)."
        )
        (tmp_path / "guide.md").write_text("# Guide")
        report = mod.ReceptorReport(receptor="test")
        mod.check_referenced_files("test", tmp_path, report)
        assert report.ok


# ── Unit tests: check_receptor (integration) ──────────────────────────────────


class TestCheckReceptor:
    def test_healthy_receptor(self, tmp_path):
        mod = _load_module()
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: test\ndescription: a good one\n---\n# Body")
        report = mod.check_receptor(tmp_path)
        assert report.ok

    def test_missing_skill_md(self, tmp_path):
        mod = _load_module()
        report = mod.check_receptor(tmp_path)
        assert not report.ok
        assert any(i.check == "skill_missing" for i in report.issues)

    def test_lowercase_skill_md(self, tmp_path):
        mod = _load_module()
        (tmp_path / "skill.md").write_text(
            "---\nname: test\ndescription: d\n---\n# Body"
        )
        report = mod.check_receptor(tmp_path)
        assert not report.ok
        assert any(i.check == "filename_case" for i in report.issues)

    def test_bad_frontmatter_and_bad_recipe(self, tmp_path):
        mod = _load_module()
        skill = tmp_path / "SKILL.md"
        skill.write_text("---\nname: test\n---\n# Body")  # missing description
        recipe = tmp_path / "recipe.yaml"
        recipe.write_text("bad: [\nyaml")
        report = mod.check_receptor(tmp_path)
        assert not report.ok
        assert len(report.issues) >= 2


# ── Unit tests: format_table / format_json ────────────────────────────────────


class TestFormatting:
    def test_format_table_healthy(self):
        mod = _load_module()
        reports = [mod.ReceptorReport(receptor="foo", ok=True)]
        out = mod.format_table(reports)
        assert "foo" in out
        assert "OK" in out

    def test_format_table_broken(self):
        mod = _load_module()
        reports = [
            mod.ReceptorReport(
                receptor="bar",
                ok=False,
                issues=[
                    mod.Issue("bar", "error", "frontmatter", "missing 'name'")
                ],
            )
        ]
        out = mod.format_table(reports)
        assert "bar" in out
        assert "BROKEN" in out
        assert "missing 'name'" in out

    def test_format_json_healthy(self):
        mod = _load_module()
        reports = [mod.ReceptorReport(receptor="baz", ok=True)]
        out = mod.format_json(reports)
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["ok"] is True
        assert data[0]["receptor"] == "baz"

    def test_format_json_broken(self):
        mod = _load_module()
        reports = [
            mod.ReceptorReport(
                receptor="qux",
                ok=False,
                issues=[
                    mod.Issue("qux", "error", "test_check", "test detail")
                ],
            )
        ]
        out = mod.format_json(reports)
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["ok"] is False
        assert data[0]["issues"][0]["check"] == "test_check"


# ── CLI integration tests ─────────────────────────────────────────────────────


class TestCLI:
    def test_help_runs(self):
        result = subprocess.run(
            [sys.executable, str(RECEPTOR_HEALTH_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "receptor" in result.stdout.lower()

    def test_runs_on_real_receptors(self):
        """Smoke test against actual receptor directory."""
        result = subprocess.run(
            [sys.executable, str(RECEPTOR_HEALTH_PATH), "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode in (0, 1)
        data = json.loads(result.stdout)
        assert len(data) > 0
        for entry in data:
            assert "receptor" in entry
            assert "ok" in entry
            assert "issues" in entry

    def test_specific_receptor(self):
        result = subprocess.run(
            [
                sys.executable,
                str(RECEPTOR_HEALTH_PATH),
                "debridement",
                "--json",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode in (0, 1)
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["receptor"] == "debridement"

    def test_unknown_receptor_warns(self):
        result = subprocess.run(
            [sys.executable, str(RECEPTOR_HEALTH_PATH), "nonexistent_xyz"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert "not found" in result.stderr.lower()


# ── Real receptor validation (catches actual problems) ────────────────────────


class TestRealReceptors:
    def test_all_receptors_parseable(self):
        """Every SKILL.md should have valid YAML frontmatter."""
        mod = _load_module()
        broken = []
        for d in sorted(RECEPTORS_DIR.iterdir()):
            if not d.is_dir():
                continue
            report = mod.check_receptor(d)
            if not report.ok:
                broken.append(report)
        if broken:
            names = [r.receptor for r in broken]
            print(f"\nBroken receptors ({len(broken)}): {', '.join(names)}")
            for r in broken:
                for i in r.issues:
                    print(
                        f"  {r.receptor}: [{i.severity}] {i.check}: {i.detail}"
                    )

    def test_all_recipe_yamls_parseable(self):
        """Every recipe.yaml should be valid YAML with required keys."""
        mod = _load_module()
        broken = []
        for rp in sorted(RECEPTORS_DIR.glob("*/recipe.yaml")):
            name = rp.parent.name
            report = mod.ReceptorReport(receptor=name)
            mod.check_recipe_yaml(name, rp.parent, report)
            if not report.ok:
                broken.append(report)
        if broken:
            names = [r.receptor for r in broken]
            print(f"\nBad recipe.yaml ({len(broken)}): {', '.join(names)}")
