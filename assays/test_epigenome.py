"""Tests for metabolon.gastrulation.epigenome."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import click
import pytest

from metabolon.gastrulation.epigenome import (
    _TEMPLATE_ROOT,
    _initialise_genome_repo,
    _transcribe_templates,
    scaffold_epigenome,
)


class TestScaffoldEpigenome:
    """Tests for scaffold_epigenome()."""

    def test_creates_directory_structure(self, tmp_path: Path):
        """Scaffold creates credentials/, config/, and launchd/ subdirectories."""
        target = tmp_path / "new_instance"
        scaffold_epigenome(target)

        assert (target / "credentials").is_dir()
        assert (target / "config").is_dir()
        assert (target / "launchd").is_dir()

    def test_returns_target_path(self, tmp_path: Path):
        """scaffold_epigenome returns the path to the created directory."""
        target = tmp_path / "my_instance"
        result = scaffold_epigenome(target)
        assert result == target
        assert result.exists()

    def test_refuses_non_empty_directory(self, tmp_path: Path):
        """Raises ClickException when target already exists and is non-empty."""
        target = tmp_path / "existing"
        target.mkdir()
        (target / "some_file.txt").write_text("data")

        with pytest.raises(click.ClickException, match="already exists and is not empty"):
            scaffold_epigenome(target)

    def test_allows_empty_existing_directory(self, tmp_path: Path):
        """Succeeds when target directory exists but is empty."""
        target = tmp_path / "empty_dir"
        target.mkdir()
        assert list(target.iterdir()) == []

        result = scaffold_epigenome(target)
        assert result == target
        assert (target / "credentials").is_dir()

    def test_initialises_git_repo(self, tmp_path: Path):
        """Scaffold creates a git repo with an initial commit."""
        target = tmp_path / "git_instance"
        scaffold_epigenome(target)

        assert (target / ".git").is_dir()
        log = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=target,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "initialise epigenome scaffold" in log.stdout


class TestTranscribeTemplates:
    """Tests for _transcribe_templates()."""

    def test_copies_existing_templates(self, tmp_path: Path):
        """Template files that exist in _TEMPLATE_ROOT are copied with content."""
        target = tmp_path / "t"
        target.mkdir()
        _transcribe_templates(target)

        # These files exist in the template root (verified at runtime).
        if (_TEMPLATE_ROOT / ".gitignore").exists():
            assert (target / ".gitignore").read_bytes() == (
                _TEMPLATE_ROOT / ".gitignore"
            ).read_bytes()

    def test_touches_missing_templates(self, tmp_path: Path):
        """Template files absent from _TEMPLATE_ROOT are created as empty files."""
        target = tmp_path / "t"
        target.mkdir()
        _transcribe_templates(target)

        # credentials/.env.template is not in the template tree — becomes empty.
        env_template = target / "credentials" / ".env.template"
        assert env_template.exists()
        assert env_template.read_text() == ""


class TestInitialiseGenomeRepo:
    """Tests for _initialise_genome_repo()."""

    def test_creates_git_repo(self, tmp_path: Path):
        """_initialise_genome_repo creates a .git directory."""
        target = tmp_path / "repo"
        target.mkdir()
        _initialise_genome_repo(target)
        assert (target / ".git").is_dir()

    def test_graceful_on_git_failure(self, tmp_path: Path):
        """No exception raised when git init fails (git unavailable)."""
        target = tmp_path / "repo"
        target.mkdir()

        with patch("metabolon.gastrulation.epigenome.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError
            # Should not raise.
            _initialise_genome_repo(target)
