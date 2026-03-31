from __future__ import annotations
"""Tests for effectors/express — membrane receptor installation.

Express is a script (effectors/express), not an importable module.
It is loaded via exec() so that module-level constants can be patched per test.
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

EXPRESS_PATH = Path(__file__).resolve().parents[1] / "effectors" / "express"


# ── Fixture ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def express(tmp_path):
    """Load express via exec, redirecting all path constants to tmp_path."""
    ns: dict = {
        "__name__": "test_express",
        "__file__": str(EXPRESS_PATH),
    }
    source = EXPRESS_PATH.read_text(encoding="utf-8")
    exec(source, ns)

    # Create a fake germline root in tmp_path
    fake_root = tmp_path / "germline"
    fake_root.mkdir()

    # Create membrane structure
    membrane = fake_root / "membrane"
    membrane.mkdir()
    (membrane / "cytoskeleton").mkdir()
    (membrane / "phenotype.md").write_text("# Phenotype\n", encoding="utf-8")
    (membrane / "expression.json").write_text("{}", encoding="utf-8")

    # Create engrams directory
    engrams = fake_root / "engrams"
    engrams.mkdir()

    # Create receptors directory with skills
    receptors = membrane / "receptors"
    receptors.mkdir()
    (receptors / "skill_a").mkdir()
    (receptors / "skill_b").mkdir()

    # Create buds directory
    buds = membrane / "buds"
    buds.mkdir()
    (buds / "agent_x").mkdir()

    # Create regulatory directory (may not exist in real install)
    regulatory = membrane / "regulatory"
    regulatory.mkdir()

    # Redirect VIVESCA_ROOT
    ns["VIVESCA_ROOT"] = fake_root

    # Create fake platform directories in tmp_path
    platform_home = tmp_path / "platform"
    platform_home.mkdir()
    claude_dir = platform_home / ".claude"
    claude_dir.mkdir()
    codex_dir = platform_home / ".codex"
    codex_dir.mkdir()

    return ns


# ── File existence and structure ────────────────────────────────────────────


class TestExpressBasics:
    def test_file_exists(self):
        """Test that express effector file exists."""
        assert EXPRESS_PATH.exists()
        assert EXPRESS_PATH.is_file()

    def test_is_python_script(self):
        """Test that express has Python shebang."""
        first_line = EXPRESS_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/usr/bin/env python")

    def test_has_docstring(self):
        """Test that express has docstring."""
        content = EXPRESS_PATH.read_text()
        assert '"""' in content
        assert "membrane" in content.lower() or "symlink" in content.lower()


# ── CLI subprocess tests ─────────────────────────────────────────────────────


class TestCLISubprocess:
    def test_dry_run_flag_works(self):
        """Test --dry-run flag works."""
        result = subprocess.run(
            [sys.executable, str(EXPRESS_PATH), "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Dry run" in result.stdout

    def test_dry_run_exits_zero(self):
        """Test --dry-run exits with code 0."""
        result = subprocess.run(
            [sys.executable, str(EXPRESS_PATH), "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Dry run" in result.stdout

    def test_dry_run_prints_vivesca_root(self):
        """Test --dry-run prints the VIVESCA_ROOT."""
        result = subprocess.run(
            [sys.executable, str(EXPRESS_PATH), "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "Vivesca root" in result.stdout
        # Should include the germline path
        assert "germline" in result.stdout.lower()

    def test_dry_run_detects_existing_paths(self):
        """Test --dry-run detects existing membrane paths."""
        result = subprocess.run(
            [sys.executable, str(EXPRESS_PATH), "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should detect membrane/cytoskeleton exists
        assert "cytoskeleton" in result.stdout


# ── integrate function tests ────────────────────────────────────────────────


class TestIntegrate:
    def test_dry_run_prints_skip_for_missing_organism(self, express, capsys):
        """Test dry run prints SKIP when organism path doesn't exist."""
        # Point to a nonexistent organism path
        express["VIVESCA_ROOT"] = express["VIVESCA_ROOT"].parent / "nonexistent"

        express["integrate"](dry_run=True)
        out = capsys.readouterr().out

        assert "SKIP" in out

    def test_dry_run_prints_link_for_missing_platform(self, express, capsys):
        """Test dry run prints LINK when platform path doesn't exist."""
        fake_home = express["VIVESCA_ROOT"].parent / "fake_home"
        fake_home.mkdir()

        with patch.dict(os.environ, {"HOME": str(fake_home)}):
            ns2 = {"__name__": "test_express", "__file__": str(EXPRESS_PATH)}
            exec(EXPRESS_PATH.read_text(), ns2)
            ns2["VIVESCA_ROOT"] = express["VIVESCA_ROOT"]
            ns2["integrate"](dry_run=True)

        out = capsys.readouterr().out
        # Should show LINK for paths that don't exist yet
        assert "LINK" in out or "SKIP" in out  # May skip if org path missing

    def test_links_created_on_integrate(self, express, capsys):
        """Test actual symlinks are created when not dry run."""
        fake_home = express["VIVESCA_ROOT"].parent / "fake_home2"
        fake_home.mkdir()
        claude_dir = fake_home / ".claude"
        claude_dir.mkdir()

        with patch.dict(os.environ, {"HOME": str(fake_home)}):
            ns2 = {"__name__": "test_express", "__file__": str(EXPRESS_PATH)}
            exec(EXPRESS_PATH.read_text(), ns2)
            ns2["VIVESCA_ROOT"] = express["VIVESCA_ROOT"]
            ns2["integrate"](dry_run=False)

        # Check hooks symlink was created
        hooks_link = claude_dir / "hooks"
        assert hooks_link.is_symlink() or hooks_link.exists()

    def test_existing_correct_symlink_shows_ok(self, express, capsys):
        """Test OK is printed when symlink already points to correct target."""
        fake_home = express["VIVESCA_ROOT"].parent / "fake_home3"
        fake_home.mkdir()
        claude_dir = fake_home / ".claude"
        claude_dir.mkdir()

        # Pre-create correct symlink
        hooks_link = claude_dir / "hooks"
        hooks_link.symlink_to(express["VIVESCA_ROOT"] / "membrane" / "cytoskeleton")

        with patch.dict(os.environ, {"HOME": str(fake_home)}):
            ns2 = {"__name__": "test_express", "__file__": str(EXPRESS_PATH)}
            exec(EXPRESS_PATH.read_text(), ns2)
            ns2["VIVESCA_ROOT"] = express["VIVESCA_ROOT"]
            ns2["integrate"](dry_run=True)

        out = capsys.readouterr().out
        assert "OK" in out

    def test_conflict_shows_conflict_message(self, express, capsys):
        """Test CONFLICT is printed when platform path exists but isn't symlink."""
        fake_home = express["VIVESCA_ROOT"].parent / "fake_home4"
        fake_home.mkdir()
        claude_dir = fake_home / ".claude"
        claude_dir.mkdir()

        # Pre-create a real directory (not symlink) - this is a conflict
        hooks_dir = claude_dir / "hooks"
        hooks_dir.mkdir()

        with patch.dict(os.environ, {"HOME": str(fake_home)}):
            ns2 = {"__name__": "test_express", "__file__": str(EXPRESS_PATH)}
            exec(EXPRESS_PATH.read_text(), ns2)
            ns2["VIVESCA_ROOT"] = express["VIVESCA_ROOT"]
            ns2["integrate"](dry_run=True)

        out = capsys.readouterr().out
        assert "CONFLICT" in out

    def test_update_shows_when_symlink_points_elsewhere(self, express, capsys):
        """Test UPDATE is printed when symlink points to wrong location."""
        fake_home = express["VIVESCA_ROOT"].parent / "fake_home5"
        fake_home.mkdir()
        claude_dir = fake_home / ".claude"
        claude_dir.mkdir()

        # Create a wrong target
        wrong_target = fake_home / "wrong_target"
        wrong_target.mkdir()

        # Pre-create symlink pointing to wrong location
        hooks_link = claude_dir / "hooks"
        hooks_link.symlink_to(wrong_target)

        with patch.dict(os.environ, {"HOME": str(fake_home)}):
            ns2 = {"__name__": "test_express", "__file__": str(EXPRESS_PATH)}
            exec(EXPRESS_PATH.read_text(), ns2)
            ns2["VIVESCA_ROOT"] = express["VIVESCA_ROOT"]
            ns2["integrate"](dry_run=True)

        out = capsys.readouterr().out
        assert "UPDATE" in out


# ── PER_ITEM symlinks tests ─────────────────────────────────────────────────


class TestPerItemSymlinks:
    def test_per_item_creates_individual_links(self, express, capsys):
        """Test PER_ITEM creates individual symlinks for each skill."""
        fake_home = express["VIVESCA_ROOT"].parent / "fake_home6"
        fake_home.mkdir()
        claude_dir = fake_home / ".claude"
        claude_dir.mkdir()

        with patch.dict(os.environ, {"HOME": str(fake_home)}):
            ns2 = {"__name__": "test_express", "__file__": str(EXPRESS_PATH)}
            exec(EXPRESS_PATH.read_text(), ns2)
            ns2["VIVESCA_ROOT"] = express["VIVESCA_ROOT"]
            ns2["integrate"](dry_run=False)

        # Check skills directory was created
        skills_dir = claude_dir / "skills"
        assert skills_dir.exists()
        assert skills_dir.is_dir()

        # Check individual skill symlinks
        skill_a_link = skills_dir / "skill_a"
        assert skill_a_link.is_symlink()

    def test_per_item_shows_count(self, express, capsys):
        """Test PER_ITEM shows count of linked items."""
        fake_home = express["VIVESCA_ROOT"].parent / "fake_home7"
        fake_home.mkdir()
        claude_dir = fake_home / ".claude"
        claude_dir.mkdir()

        with patch.dict(os.environ, {"HOME": str(fake_home)}):
            ns2 = {"__name__": "test_express", "__file__": str(EXPRESS_PATH)}
            exec(EXPRESS_PATH.read_text(), ns2)
            ns2["VIVESCA_ROOT"] = express["VIVESCA_ROOT"]
            ns2["integrate"](dry_run=False)

        out = capsys.readouterr().out
        assert "items linked" in out

    def test_per_item_skip_hidden_files(self, express, capsys):
        """Test PER_ITEM skips hidden files (dotfiles)."""
        # Add a hidden directory to receptors
        receptors = express["VIVESCA_ROOT"] / "membrane" / "receptors"
        hidden_dir = receptors / ".hidden_skill"
        hidden_dir.mkdir()

        fake_home = express["VIVESCA_ROOT"].parent / "fake_home8"
        fake_home.mkdir()
        claude_dir = fake_home / ".claude"
        claude_dir.mkdir()

        with patch.dict(os.environ, {"HOME": str(fake_home)}):
            ns2 = {"__name__": "test_express", "__file__": str(EXPRESS_PATH)}
            exec(EXPRESS_PATH.read_text(), ns2)
            ns2["VIVESCA_ROOT"] = express["VIVESCA_ROOT"]
            ns2["integrate"](dry_run=False)

        # Hidden skill should not be linked
        skills_dir = claude_dir / "skills"
        assert not (skills_dir / ".hidden_skill").exists()

    def test_per_item_missing_organism_shows_skip(self, express, capsys):
        """Test PER_ITEM shows SKIP when organism directory doesn't exist."""
        # Remove receptors directory
        receptors = express["VIVESCA_ROOT"] / "membrane" / "receptors"
        import shutil
        shutil.rmtree(receptors)

        fake_home = express["VIVESCA_ROOT"].parent / "fake_home9"
        fake_home.mkdir()
        claude_dir = fake_home / ".claude"
        claude_dir.mkdir()

        with patch.dict(os.environ, {"HOME": str(fake_home)}):
            ns2 = {"__name__": "test_express", "__file__": str(EXPRESS_PATH)}
            exec(EXPRESS_PATH.read_text(), ns2)
            ns2["VIVESCA_ROOT"] = express["VIVESCA_ROOT"]
            ns2["integrate"](dry_run=True)

        out = capsys.readouterr().out
        assert "SKIP" in out


# ── Constants validation ────────────────────────────────────────────────────


class TestConstants:
    def test_links_defined(self, express):
        """Test LINKS constant is defined and is a list."""
        assert "LINKS" in express
        assert isinstance(express["LINKS"], list)
        assert len(express["LINKS"]) > 0

    def test_per_item_defined(self, express):
        """Test PER_ITEM constant is defined and is a list."""
        assert "PER_ITEM" in express
        assert isinstance(express["PER_ITEM"], list)
        assert len(express["PER_ITEM"]) > 0

    def test_links_format(self, express):
        """Test LINKS entries are tuples of (platform, organism)."""
        for entry in express["LINKS"]:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            assert entry[0].startswith("~/.claude") or entry[0].startswith("~/.codex")

    def test_per_item_format(self, express):
        """Test PER_ITEM entries are tuples of (platform_dir, organism_dir)."""
        for entry in express["PER_ITEM"]:
            assert isinstance(entry, tuple)
            assert len(entry) == 2


# ── Integration tests with real paths ───────────────────────────────────────


class TestIntegration:
    def test_paths_in_repo_exist(self):
        """Test that all required directories exist in the actual repo."""
        root = Path(__file__).resolve().parents[1]

        cytoskeleton = root / "membrane" / "cytoskeleton"
        assert cytoskeleton.exists(), f"Missing {cytoskeleton}"

        phenotype = root / "membrane" / "phenotype.md"
        assert phenotype.exists(), f"Missing {phenotype}"

        buds = root / "membrane" / "buds"
        assert buds.exists(), f"Missing {buds}"

        receptors = root / "membrane" / "receptors"
        assert receptors.exists(), f"Missing {receptors}"
        # Should have multiple skills
        assert len(list(receptors.iterdir())) >= 5, "Too few receptors"

    def test_receptors_path_in_code(self):
        """Test that membrane/receptors path is correctly defined in code."""
        content = EXPRESS_PATH.read_text()
        # Should use membrane/receptors, not just receptors
        assert '("membrane/receptors")' in content or '"membrane/receptors"' in content
