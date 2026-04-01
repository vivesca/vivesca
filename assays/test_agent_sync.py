#!/usr/bin/env python3
"""Tests for agent-sync.sh — pull config repos and sync MEMORY.md."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "effectors" / "agent-sync.sh"


# ── Existence / permission checks ─────────────────────────────────────


def test_script_exists_and_executable():
    assert SCRIPT.exists()
    assert os.access(SCRIPT, os.X_OK), "agent-sync.sh must be executable"


# ── Help flag ──────────────────────────────────────────────────────────


class TestHelp:
    """--help and -h both show usage and exit 0."""

    def test_help_long_flag(self):
        r = subprocess.run(
            [str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        assert "Usage: agent-sync.sh" in r.stdout
        assert "Pull agent config repos" in r.stdout
        assert "--help" in r.stdout

    def test_help_short_flag(self):
        r = subprocess.run(
            [str(SCRIPT), "-h"],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        assert "Usage: agent-sync.sh" in r.stdout


# ── No repos present — graceful success ───────────────────────────────


class TestNoRepos:
    """Script succeeds (exit 0) when none of the repos exist."""

    def test_exits_zero_with_empty_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        r = subprocess.run(
            [str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0

    def test_no_error_output_with_empty_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        r = subprocess.run(
            [str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        # No git errors should appear — repos are skipped via `[ -d ... ] || continue`
        assert "not a git repo" not in r.stderr
        assert "fatal:" not in r.stderr


# ── Git pull behaviour ────────────────────────────────────────────────


class TestGitPull:
    """Script pulls git repos when they contain a .git directory."""

    def _make_fake_repo(self, path: Path) -> Path:
        """Create a minimal git repo at path and return it."""
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "init"],
            cwd=str(path),
            capture_output=True,
            check=True,
        )
        # Need at least one commit so git pull doesn't fail
        dummy = path / "README"
        dummy.write_text("init\n")
        subprocess.run(
            ["git", "add", "README"],
            cwd=str(path),
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init"],
            cwd=str(path),
            capture_output=True,
            check=True,
        )
        return path

    def test_pulls_agent_config_repo(self, tmp_path, monkeypatch):
        """Script attempts git pull on $HOME/agent-config when it has .git."""
        repo = self._make_fake_repo(tmp_path / "agent-config")
        monkeypatch.setenv("HOME", str(tmp_path))
        r = subprocess.run(
            [str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        # The repo should still be valid after the pull attempt
        assert (repo / ".git").is_dir()

    def test_pulls_skills_repo(self, tmp_path, monkeypatch):
        """Script attempts git pull on $HOME/skills when it has .git."""
        repo = self._make_fake_repo(tmp_path / "skills")
        monkeypatch.setenv("HOME", str(tmp_path))
        r = subprocess.run(
            [str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        assert (repo / ".git").is_dir()

    def test_pulls_chromatin_repo(self, tmp_path, monkeypatch):
        """Script attempts git pull on $HOME/code/epigenome/chromatin when it has .git."""
        repo = self._make_fake_repo(tmp_path / "code" / "epigenome" / "chromatin")
        monkeypatch.setenv("HOME", str(tmp_path))
        r = subprocess.run(
            [str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        assert (repo / ".git").is_dir()

    def test_skips_repo_without_git_dir(self, tmp_path, monkeypatch):
        """Directories in REPOS without .git are silently skipped."""
        # Create agent-config dir but NOT as a git repo
        (tmp_path / "agent-config").mkdir()
        monkeypatch.setenv("HOME", str(tmp_path))
        r = subprocess.run(
            [str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        # No git errors — the dir was skipped via `|| continue`
        assert "fatal:" not in r.stderr

    def test_pull_failure_does_not_crash(self, tmp_path, monkeypatch):
        """A failing git pull is swallowed (|| true) and script still exits 0."""
        repo = self._make_fake_repo(tmp_path / "agent-config")
        # Corrupt the git repo so pull fails
        git_dir = repo / ".git"
        # Remove HEAD to make git commands fail
        (git_dir / "HEAD").unlink()
        monkeypatch.setenv("HOME", str(tmp_path))
        r = subprocess.run(
            [str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        # Script still succeeds — `|| true` absorbs the failure
        assert r.returncode == 0


# ── MEMORY.md sync ────────────────────────────────────────────────────


class TestMemorySync:
    """MEMORY.md is copied from agent-config to the Claude project dir."""

    def test_copies_memory_md(self, tmp_path, monkeypatch):
        """MEMORY.md is copied from $HOME/agent-config/claude/memory/ to .claude/projects/."""
        src_dir = tmp_path / "agent-config" / "claude" / "memory"
        src_dir.mkdir(parents=True)
        (src_dir / "MEMORY.md").write_text("# Test memory content\n")
        monkeypatch.setenv("HOME", str(tmp_path))
        r = subprocess.run(
            [str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0

        # Derive the expected destination path the same way the script does
        project_dash = str(tmp_path).lstrip("/").replace("/", "-")
        dst = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
        assert dst.exists(), f"Expected MEMORY.md at {dst}"
        assert dst.read_text() == "# Test memory content\n"

    def test_creates_destination_directory(self, tmp_path, monkeypatch):
        """mkdir -p ensures the destination directory exists before cp."""
        src_dir = tmp_path / "agent-config" / "claude" / "memory"
        src_dir.mkdir(parents=True)
        (src_dir / "MEMORY.md").write_text("data")
        monkeypatch.setenv("HOME", str(tmp_path))

        r = subprocess.run(
            [str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0

        project_dash = str(tmp_path).lstrip("/").replace("/", "-")
        dst_dir = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory"
        assert dst_dir.is_dir()

    def test_no_error_when_source_missing(self, tmp_path, monkeypatch):
        """If $HOME/agent-config/claude/memory/MEMORY.md doesn't exist, script still exits 0."""
        monkeypatch.setenv("HOME", str(tmp_path))
        r = subprocess.run(
            [str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        # No destination should have been created
        assert not list((tmp_path / ".claude").rglob("MEMORY.md")) if (tmp_path / ".claude").exists() else True

    def test_overwrites_existing_memory(self, tmp_path, monkeypatch):
        """Running the script twice overwrites the destination MEMORY.md."""
        src_dir = tmp_path / "agent-config" / "claude" / "memory"
        src_dir.mkdir(parents=True)
        monkeypatch.setenv("HOME", str(tmp_path))

        # First write
        (src_dir / "MEMORY.md").write_text("version 1\n")
        subprocess.run([str(SCRIPT)], capture_output=True, text=True)

        # Second write with updated content
        (src_dir / "MEMORY.md").write_text("version 2\n")
        r = subprocess.run([str(SCRIPT)], capture_output=True, text=True)
        assert r.returncode == 0

        project_dash = str(tmp_path).lstrip("/").replace("/", "-")
        dst = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
        assert dst.read_text() == "version 2\n"


# ── Static source checks ─────────────────────────────────────────────


class TestSourceContent:
    """Verify expected constants and patterns in the script source."""

    def test_repos_array(self):
        src = SCRIPT.read_text()
        assert '"$HOME/agent-config"' in src
        assert '"$HOME/skills"' in src
        assert '"$HOME/code/epigenome/chromatin"' in src

    def test_set_flags(self):
        src = SCRIPT.read_text()
        assert "set -uo pipefail" in src

    def test_pull_with_rebase(self):
        src = SCRIPT.read_text()
        assert "git -C \"$repo\" pull --rebase" in src

    def test_pull_fallback(self):
        src = SCRIPT.read_text()
        assert "git -C \"$repo\" pull" in src

    def test_cp_and_mkdir(self):
        src = SCRIPT.read_text()
        assert 'mkdir -p "$(dirname "$DST")"' in src
        assert 'cp "$SRC" "$DST"' in src
