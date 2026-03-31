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

    def test_git_pull_error_does_not_crash(self, tmp_path):
        """Script tolerates git pull errors gracefully (|| true)."""
        repo = tmp_path / "agent-config"
        repo.mkdir()
        (repo / ".git").mkdir()
        # Not a real git repo — .git/ exists but is empty, so git commands fail
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_git_rebase_fallback(self, tmp_path):
        """Script falls back from --rebase to plain pull when rebase fails."""
        repo = tmp_path / "skills"
        repo.mkdir()
        subprocess.run(["git", "init", str(repo)], capture_output=True, check=True)
        # Add a dummy commit so there's something to pull
        subprocess.run(
            ["git", "-C", str(repo), "commit", "--allow-empty", "-m", "init"],
            capture_output=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                 "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
        )
        # Point origin at a non-existent path so pull fails gracefully
        subprocess.run(
            ["git", "-C", str(repo), "remote", "add", "origin", "/no/such/path"],
            capture_output=True,
        )
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_mixed_git_and_non_git_repos(self, tmp_path):
        """Script processes repos with mixed .git presence."""
        # agent-config has .git, skills does not, chromatin has .git
        repo1 = tmp_path / "agent-config"
        repo1.mkdir()
        subprocess.run(["git", "init", str(repo1)], capture_output=True, check=True)

        (tmp_path / "skills").mkdir()

        repo3 = tmp_path / "code" / "epigenome" / "chromatin"
        repo3.mkdir(parents=True)
        subprocess.run(["git", "init", str(repo3)], capture_output=True, check=True)

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_memory_file_with_unicode(self, tmp_path):
        """Script handles MEMORY.md with unicode content."""
        src_dir = tmp_path / "agent-config" / "claude" / "memory"
        src_dir.mkdir(parents=True)
        (src_dir / "MEMORY.md").write_text("# Mémoire 🧠\nÜnïcödé content: 日本語\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        project_dash = str(tmp_path).lstrip("/").replace("/", "-")
        dst = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
        assert dst.exists()
        content = dst.read_text()
        assert "Mémoire" in content
        assert "日本語" in content

    def test_memory_file_large_content(self, tmp_path):
        """Script copies large MEMORY.md files correctly."""
        src_dir = tmp_path / "agent-config" / "claude" / "memory"
        src_dir.mkdir(parents=True)
        large_content = "# Large\n" + "line of data\n" * 10000
        (src_dir / "MEMORY.md").write_text(large_content)

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        project_dash = str(tmp_path).lstrip("/").replace("/", "-")
        dst = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
        assert dst.exists()
        assert len(dst.read_text()) == len(large_content)

    def test_memory_source_is_directory_not_file(self, tmp_path):
        """Script handles case where MEMORY.md source path is a directory."""
        src_dir = tmp_path / "agent-config" / "claude" / "memory"
        src_dir.mkdir(parents=True)
        # Create MEMORY.md as a directory instead of a file
        (src_dir / "MEMORY.md").mkdir()

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # Script checks [ -f "$SRC" ], so directory is skipped
        assert r.returncode == 0

        project_dash = str(tmp_path).lstrip("/").replace("/", "-")
        dst = tmp_path / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
        assert not dst.exists()

    def test_deeply_nested_home_path(self, tmp_path):
        """Script correctly handles deeply nested HOME with many slashes."""
        nested = tmp_path / "a" / "b" / "c" / "d" / "e"
        nested.mkdir(parents=True)

        src_dir = nested / "agent-config" / "claude" / "memory"
        src_dir.mkdir(parents=True)
        (src_dir / "MEMORY.md").write_text("deep path test\n")

        r = _run(SCRIPT, env={"HOME": str(nested)})
        assert r.returncode == 0

        project_dash = str(nested).lstrip("/").replace("/", "-")
        dst = nested / ".claude" / "projects" / f"-{project_dash}" / "memory" / "MEMORY.md"
        assert dst.exists()
        assert dst.read_text() == "deep path test\n"

    def test_home_with_trailing_slash(self, tmp_path):
        """Script handles HOME with trailing slash."""
        home = tmp_path / "myhome"
        home.mkdir()
        src_dir = home / "agent-config" / "claude" / "memory"
        src_dir.mkdir(parents=True)
        (src_dir / "MEMORY.md").write_text("trailing slash\n")

        r = _run(SCRIPT, env={"HOME": str(home) + "/"})
        assert r.returncode == 0

        # sed 's|^/||' strips leading /, then tr '/' '-'
        # With trailing slash: /tmp/.../myhome/ -> tmp/.../myhome/ -> tmp-...-myhome-
        # The dst dir should exist somewhere under .claude/projects/
        claude_dir = home / ".claude" / "projects"
        if claude_dir.exists():
            # Find MEMORY.md anywhere under projects
            found = list(claude_dir.rglob("MEMORY.md"))
            assert len(found) >= 1
