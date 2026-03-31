from __future__ import annotations

"""Tests for agent-sync.sh — pull config repos and sync MEMORY.md."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path.home() / "germline" / "effectors" / "agent-sync.sh"


def _run(script: Path, args: list[str] | None = None, env: dict | None = None) -> subprocess.CompletedProcess[str]:
    """Run agent-sync.sh with optional args and HOME override."""
    cmd = ["bash", str(script)]
    if args:
        cmd.extend(args)
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=run_env,
        timeout=10,
    )


# ── Help flag tests ───────────────────────────────────────────────────


class TestHelpFlag:
    """Tests for -h / --help."""

    def test_help_flag_shows_usage(self):
        """--help prints usage and exits 0."""
        r = _run(SCRIPT, ["--help"])
        assert r.returncode == 0
        assert "Usage" in r.stdout

    def test_short_help_flag(self):
        """-h prints usage and exits 0."""
        r = _run(SCRIPT, ["-h"])
        assert r.returncode == 0
        assert "Usage" in r.stdout

    def test_help_mentions_sync(self):
        """Help text mentions MEMORY.md sync purpose."""
        r = _run(SCRIPT, ["--help"])
        assert "MEMORY.md" in r.stdout or "sync" in r.stdout.lower() or "Pull" in r.stdout


# ── Repo pull tests ──────────────────────────────────────────────────


class TestRepoPull:
    """Tests for git pull on configured repos."""

    def test_skips_nonexistent_repos(self, tmp_path):
        """Script exits 0 even when no repos exist."""
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_skips_dirs_without_git(self, tmp_path):
        """Script skips directories that exist but lack .git/."""
        # Create the three repo dirs without .git
        for d in ["agent-config", "skills", "code/epigenome/chromatin"]:
            (tmp_path / d).mkdir(parents=True, exist_ok=True)
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_pulls_git_repos(self, tmp_path):
        """Script attempts git pull on repos with .git/ directory."""
        repo = tmp_path / "agent-config"
        repo.mkdir()
        (repo / ".git").mkdir()
        # Create a git repo so git -C pull doesn't fail catastrophically
        subprocess.run(
            ["git", "init", str(repo)],
            capture_output=True,
            check=True,
        )
        # Configure a fake remote to avoid git errors about missing origin
        subprocess.run(
            ["git", "-C", str(repo), "remote", "add", "origin", "/dev/null"],
            capture_output=True,
        )
        # git pull will fail (no commits), but script should not crash
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0


# ── MEMORY.md sync tests ────────────────────────────────────────────


class TestMemorySync:
    """Tests for MEMORY.md copy to .claude/projects/."""

    def test_no_memory_file_no_error(self, tmp_path):
        """Script exits 0 when MEMORY.md source does not exist."""
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_copies_memory_file(self, tmp_path):
        """Script copies MEMORY.md to .claude/projects/-home-terry/memory/."""
        src_dir = tmp_path / "agent-config" / "claude" / "memory"
        src_dir.mkdir(parents=True)
        (src_dir / "MEMORY.md").write_text("# My Memory\nTest content.\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Derive expected dst path: $HOME/.claude/projects/-<dashed-home>/memory/MEMORY.md
        project_dash = str(tmp_path).lstrip("/").replace("/", "-")
        dst = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
        assert dst.exists()
        assert "# My Memory" in dst.read_text()

    def test_creates_destination_directory(self, tmp_path):
        """Script creates destination directory if it does not exist."""
        src_dir = tmp_path / "agent-config" / "claude" / "memory"
        src_dir.mkdir(parents=True)
        (src_dir / "MEMORY.md").write_text("created dir test\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        project_dash = str(tmp_path).lstrip("/").replace("/", "-")
        dst_dir = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory"
        assert dst_dir.is_dir()

    def test_overwrites_existing_memory(self, tmp_path):
        """Script overwrites destination MEMORY.md if it already exists."""
        src_dir = tmp_path / "agent-config" / "claude" / "memory"
        src_dir.mkdir(parents=True)
        (src_dir / "MEMORY.md").write_text("new content\n")

        project_dash = str(tmp_path).lstrip("/").replace("/", "-")
        dst_dir = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory"
        dst_dir.mkdir(parents=True)
        (dst_dir / "MEMORY.md").write_text("old content\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        assert (dst_dir / "MEMORY.md").read_text() == "new content\n"

    def test_path_dash_conversion(self, tmp_path):
        """Script correctly converts HOME slashes to dashes in project path."""
        # Use a nested tmp to verify slash-to-dash conversion
        nested = tmp_path / "a" / "b"
        nested.mkdir(parents=True)

        src_dir = nested / "agent-config" / "claude" / "memory"
        src_dir.mkdir(parents=True)
        (src_dir / "MEMORY.md").write_text("dash test\n")

        r = _run(SCRIPT, env={"HOME": str(nested)})
        assert r.returncode == 0

        # /home/terry/.../a/b -> a-b (after stripping leading /)
        project_dash = str(nested).lstrip("/").replace("/", "-")
        dst = nested / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
        assert dst.exists()
        assert dst.read_text() == "dash test\n"


# ── Edge case tests ─────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases for agent-sync.sh."""

    def test_empty_home(self, tmp_path):
        """Script handles completely empty HOME directory."""
        empty = tmp_path / "empty_home"
        empty.mkdir()
        r = _run(SCRIPT, env={"HOME": str(empty)})
        assert r.returncode == 0

    def test_multiple_repos_with_git(self, tmp_path):
        """Script processes all three repos when they have .git/."""
        repos = [
            tmp_path / "agent-config",
            tmp_path / "skills",
            tmp_path / "code" / "epigenome" / "chromatin",
        ]
        for repo in repos:
            repo.mkdir(parents=True)
            subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_no_args_runs_normally(self, tmp_path):
        """Script runs without any arguments."""
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0
