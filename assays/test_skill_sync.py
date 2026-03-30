"""Tests for skill-sync — SKILL.md → recipe.yaml → config.yaml sync."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

# Import the module by exec-ing it (it has no .py extension)
import types

_SCRIPT = Path.home() / "germline" / "effectors" / "skill-sync"
skill_sync = types.ModuleType("skill_sync")
skill_sync.__file__ = str(_SCRIPT)

# Read the source, skip the uv shebang + header block
_source = _SCRIPT.read_text()
# Strip everything up to and including the closing # /// marker
import re
_source = re.sub(r"\A.*?# ///\s*\n", "", _source, count=1, flags=re.DOTALL)
exec(compile(_source, str(_SCRIPT), "exec"), skill_sync.__dict__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_skill_md(directory: Path, name: str, description: str, extra_meta: str = "", body: str = "") -> Path:
    """Create a SKILL.md in directory, return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    frontmatter = f"name: {name}\ndescription: \"{description}\""
    if extra_meta:
        frontmatter += "\n" + extra_meta
    content = f"---\n{frontmatter}\n---\n{body}\n"
    p = directory / "SKILL.md"
    p.write_text(content)
    return p


def _write_goose_config(config_path: Path, slash_commands: list[dict] | None = None) -> Path:
    """Create a minimal goose config.yaml."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config: dict = {"extensions": {}}
    if slash_commands is not None:
        config["slash_commands"] = slash_commands
    config_path.write_text(yaml.dump(config, default_flow_style=False))
    return config_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestParseFrontmatter:
    def test_extracts_name_and_description(self):
        content = '---\nname: folding\ndescription: "Execute a plan"\n---\nBody text\n'
        meta, body = skill_sync.parse_frontmatter(content)
        assert meta["name"] == "folding"
        assert meta["description"] == "Execute a plan"
        assert "Body text" in body

    def test_no_frontmatter_returns_empty_meta(self):
        content = "Just body text, no frontmatter at all.\n"
        meta, body = skill_sync.parse_frontmatter(content)
        assert meta == {}
        assert content in body

    def test_extra_metadata_fields(self):
        content = '---\nname: test\nmodel: sonnet\nepistemics: [build]\n---\nBody\n'
        meta, body = skill_sync.parse_frontmatter(content)
        assert meta["model"] == "sonnet"
        assert meta["epistemics"] == ["build"]


class TestExtractTitle:
    def test_first_heading(self):
        assert skill_sync.extract_title("# /folding — Execute the Plan\nMore text") == "/folding — Execute the Plan"

    def test_strips_bold_markers(self):
        assert skill_sync.extract_title("# **Bold Title**") == "Bold Title"

    def test_no_heading_returns_empty(self):
        assert skill_sync.extract_title("No heading here\nJust text") == ""

    def test_h2_heading(self):
        assert skill_sync.extract_title("## Sub-heading") == "Sub-heading"


class TestGenerateRecipe:
    def test_produces_valid_yaml(self):
        recipe_str = skill_sync.build_recipe(
            "test-skill", "A test skill", "Test Title", "Do the thing.\n"
        )
        recipe = yaml.safe_load(recipe_str)
        assert recipe["name"] == "test-skill"
        assert recipe["description"] == "A test skill"
        assert recipe["title"] == "Test Title"
        assert "Do the thing" in recipe["instructions"]
        assert recipe["prompt"] == "Execute the test-skill skill."

    def test_extensions_block(self):
        recipe_str = skill_sync.build_recipe("x", "x", "x", "body")
        recipe = yaml.safe_load(recipe_str)
        ext_names = [e["name"] for e in recipe["extensions"]]
        assert "developer" in ext_names
        assert "vivesca" in ext_names

    def test_instructions_include_body(self):
        body = "## Step 1\nDo something.\n## Step 2\nDo another thing.\n"
        recipe_str = skill_sync.build_recipe("x", "x", "x", body)
        recipe = yaml.safe_load(recipe_str)
        assert "Step 1" in recipe["instructions"]
        assert "Step 2" in recipe["instructions"]


class TestSkipWhenFresh:
    def test_does_not_regenerate_when_recipe_newer(self, tmp_path):
        """recipe.yaml mtime >= SKILL.md mtime → skip."""
        skill_dir = tmp_path / "receptors" / "my-skill"
        skill_md = _write_skill_md(skill_dir, "my-skill", "desc", body="# Title\n")
        config_path = tmp_path / "config" / "config.yaml"
        _write_goose_config(config_path)

        # First sync: generates recipe.yaml
        skill_sync.sync(tmp_path / "receptors", config_path)
        recipe_path = skill_dir / "recipe.yaml"
        assert recipe_path.exists()
        first_content = recipe_path.read_text()

        # Second sync: should be unchanged
        skill_sync.sync(tmp_path / "receptors", config_path)
        assert recipe_path.read_text() == first_content


class TestForceRegenerate:
    def test_force_regenerates_even_when_fresh(self, tmp_path):
        skill_dir = tmp_path / "receptors" / "my-skill"
        _write_skill_md(skill_dir, "my-skill", "old desc", body="# Old Title\n")
        config_path = tmp_path / "config" / "config.yaml"
        _write_goose_config(config_path)

        # First sync
        skill_sync.sync(tmp_path / "receptors", config_path)
        recipe_path = skill_dir / "recipe.yaml"
        first_content = recipe_path.read_text()

        # Modify SKILL.md description
        _write_skill_md(skill_dir, "my-skill", "new desc", body="# New Title\n")

        # Force sync
        skill_sync.sync(tmp_path / "receptors", config_path, force=True)
        new_content = recipe_path.read_text()
        assert new_content != first_content
        assert "new desc" in new_content


class TestRegisterConfig:
    def test_adds_new_slash_commands(self, tmp_path):
        skill_dir = tmp_path / "receptors" / "alpha"
        _write_skill_md(skill_dir, "alpha", "Alpha skill", body="# Alpha\n")
        config_path = tmp_path / "config" / "config.yaml"
        _write_goose_config(config_path)

        skill_sync.sync(tmp_path / "receptors", config_path)

        config = yaml.safe_load(config_path.read_text())
        commands = {c["command"] for c in config["slash_commands"]}
        assert "alpha" in commands

    def test_does_not_duplicate_existing(self, tmp_path):
        skill_dir = tmp_path / "receptors" / "beta"
        _write_skill_md(skill_dir, "beta", "Beta skill", body="# Beta\n")
        config_path = tmp_path / "config" / "config.yaml"
        recipe_path = str((skill_dir / "recipe.yaml").resolve())
        _write_goose_config(config_path, slash_commands=[
            {"command": "beta", "recipe_path": recipe_path}
        ])

        skill_sync.sync(tmp_path / "receptors", config_path)

        config = yaml.safe_load(config_path.read_text())
        beta_entries = [c for c in config["slash_commands"] if c["command"] == "beta"]
        assert len(beta_entries) == 1


class TestCleanStaleCommands:
    def test_removes_entries_with_no_recipe(self, tmp_path):
        config_path = tmp_path / "config" / "config.yaml"
        _write_goose_config(config_path, slash_commands=[
            {"command": "gone-skill", "recipe_path": "/nonexistent/recipe.yaml"},
            {"command": "also-gone", "recipe_path": "/nowhere/recipe.yaml"},
        ])

        # Sync with no skills → stale entries removed
        skill_sync.sync(tmp_path / "receptors", config_path)

        config = yaml.safe_load(config_path.read_text())
        commands = [c["command"] for c in config.get("slash_commands", [])]
        assert "gone-skill" not in commands
        assert "also-gone" not in commands


class TestDryRun:
    def test_dry_run_does_not_write_files(self, tmp_path):
        skill_dir = tmp_path / "receptors" / "dry-test"
        _write_skill_md(skill_dir, "dry-test", "Dry test", body="# Dry\n")
        config_path = tmp_path / "config" / "config.yaml"
        _write_goose_config(config_path)

        skill_sync.sync(tmp_path / "receptors", config_path, dry_run=True)

        assert not (skill_dir / "recipe.yaml").exists()
        # Config unchanged
        config = yaml.safe_load(config_path.read_text())
        assert "slash_commands" not in config or len(config.get("slash_commands", [])) == 0


class TestSingleSkill:
    def test_syncs_only_named_skill(self, tmp_path):
        receptors = tmp_path / "receptors"
        alpha_dir = receptors / "alpha"
        beta_dir = receptors / "beta"
        _write_skill_md(alpha_dir, "alpha", "Alpha", body="# Alpha\n")
        _write_skill_md(beta_dir, "beta", "Beta", body="# Beta\n")
        config_path = tmp_path / "config" / "config.yaml"
        _write_goose_config(config_path)

        skill_sync.sync(receptors, config_path, single_name="alpha")

        # Alpha should have recipe.yaml
        assert (alpha_dir / "recipe.yaml").exists()
        # Beta should NOT
        assert not (beta_dir / "recipe.yaml").exists()
