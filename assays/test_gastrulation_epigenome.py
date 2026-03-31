"""Tests for metabolon/gastrulation/epigenome.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.gastrulation.epigenome import (
    _initialise_genome_repo,
    _transcribe_templates,
    scaffold_epigenome,
)


class TestScaffoldEpigenome:
    """Tests for scaffold_epigenome function."""

    def test_creates_directory_structure(self, tmp_path: Path) -> None:
        """Should create all required subdirectories."""
        target = tmp_path / "new_epigenome"

        result = scaffold_epigenome(target)

        assert result == target
        assert target.exists()
        assert (target / "credentials").is_dir()
        assert (target / "config").is_dir()
        assert (target / "launchd").is_dir()

    def test_creates_nonexistent_directory(self, tmp_path: Path) -> None:
        """Should create target directory if it doesn't exist."""
        target = tmp_path / "nested" / "path" / "epigenome"

        scaffold_epigenome(target)

        assert target.exists()

    def test_raises_on_non_empty_directory(self, tmp_path: Path) -> None:
        """Should raise if target exists and is non-empty."""
        import click

        target = tmp_path / "existing"
        target.mkdir()
        (target / "some_file.txt").write_text("content")

        with pytest.raises(click.ClickException, match="already exists and is not empty"):
            scaffold_epigenome(target)

    def test_allows_empty_directory(self, tmp_path: Path) -> None:
        """Should allow target that exists but is empty."""
        target = tmp_path / "empty_dir"
        target.mkdir()

        result = scaffold_epigenome(target)

        assert result == target

    def test_calls_transcribe_templates(self, tmp_path: Path) -> None:
        """Should call _transcribe_templates with target."""
        target = tmp_path / "epigenome"

        with patch("metabolon.gastrulation.epigenome._transcribe_templates") as mock_transcribe:
            with patch("metabolon.gastrulation.epigenome._initialise_genome_repo"):
                scaffold_epigenome(target)

        mock_transcribe.assert_called_once_with(target)

    def test_calls_initialise_genome_repo(self, tmp_path: Path) -> None:
        """Should call _initialise_genome_repo with target."""
        target = tmp_path / "epigenome"

        with patch("metabolon.gastrulation.epigenome._initialise_genome_repo") as mock_init:
            scaffold_epigenome(target)

        mock_init.assert_called_once_with(target)


class TestTranscribeTemplates:
    """Tests for _transcribe_templates function."""

    def test_creates_template_files(self, tmp_path: Path) -> None:
        """Should create files from templates."""
        target = tmp_path / "epigenome"
        target.mkdir()

        _transcribe_templates(target)

        # Check key files are created
        assert (target / "README.md").exists()
        assert (target / "genome.md").exists()
        assert (target / ".gitignore").exists()
        assert (target / "config" / "server.yaml").exists()
        assert (target / "config" / "config.yaml").exists()
        assert (target / "credentials" / ".env.template").exists()
        assert (target / "launchd" / "README.md").exists()

    def test_creates_missing_template_as_empty(self, tmp_path: Path) -> None:
        """Should create empty file if template is missing."""
        target = tmp_path / "epigenome"
        target.mkdir()

        # This should not fail even if some templates don't exist
        _transcribe_templates(target)

        # All expected files should exist (even if empty)
        for expected in [
            target / "README.md",
            target / ".gitignore",
            target / "genome.md",
        ]:
            assert expected.exists()

    def test_preserves_template_content(self, tmp_path: Path) -> None:
        """Should copy template content to destination."""
        target = tmp_path / "epigenome"
        target.mkdir()

        _transcribe_templates(target)

        # README.md should have actual content from template
        readme = target / "README.md"
        content = readme.read_text()
        assert len(content) > 0  # Should not be empty


class TestInitialiseGenomeRepo:
    """Tests for _initialise_genome_repo function."""

    def test_initializes_git_repo(self, tmp_path: Path) -> None:
        """Should initialize a git repository."""
        target = tmp_path / "epigenome"
        target.mkdir()

        _initialise_genome_repo(target)

        assert (target / ".git").is_dir()

    def test_creates_initial_commit(self, tmp_path: Path) -> None:
        """Should create an initial commit."""
        target = tmp_path / "epigenome"
        target.mkdir()
        (target / "test.txt").write_text("test")

        _initialise_genome_repo(target)

        # Check git log for the commit
        import subprocess

        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=target,
            capture_output=True,
            text=True,
        )
        assert "initialise epigenome scaffold" in result.stdout

    def test_handles_git_unavailable(self, tmp_path: Path) -> None:
        """Should silently skip if git is unavailable."""
        target = tmp_path / "epigenome"
        target.mkdir()

        # Patch subprocess.run to raise FileNotFoundError
        with patch("subprocess.run", side_effect=FileNotFoundError):
            # Should not raise
            _initialise_genome_repo(target)

    def test_handles_git_failure(self, tmp_path: Path) -> None:
        """Should silently skip if git command fails."""
        import subprocess

        target = tmp_path / "epigenome"
        target.mkdir()

        # Patch subprocess.run to raise CalledProcessError
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            # Should not raise
            _initialise_genome_repo(target)


class TestEpigenomeIntegration:
    """Integration tests for epigenome scaffolding."""

    def test_full_scaffold_creates_valid_structure(self, tmp_path: Path) -> None:
        """Should create a complete, valid epigenome structure."""
        target = tmp_path / "full_epigenome"

        result = scaffold_epigenome(target)

        assert result == target
        assert target.is_dir()

        # Check all expected directories
        for subdir in ["credentials", "config", "launchd"]:
            assert (target / subdir).is_dir()

        # Check all expected files
        for filepath in [
            "README.md",
            "genome.md",
            ".gitignore",
            "credentials/.env.template",
            "config/server.yaml",
            "config/config.yaml",
            "launchd/README.md",
        ]:
            assert (target / filepath).exists(), f"Missing: {filepath}"

        # Check git repo was initialized
        assert (target / ".git").is_dir()
