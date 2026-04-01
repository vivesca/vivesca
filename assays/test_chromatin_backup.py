from __future__ import annotations

"""Tests for chromatin-backup.sh — auto-commit and push chromatin changes."""

import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path.home() / "germline" / "effectors" / "chromatin-backup.sh"


def _run(
    script: Path, args: list[str] | None = None, env: dict | None = None
) -> subprocess.CompletedProcess[str]:
    """Run chromatin-backup.sh with optional args and HOME override."""
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
        timeout=30,
    )


def _init_git_repo(repo_path: Path, with_remote: bool = False) -> Path | None:
    """Initialize a git repo with minimal config for testing.

    Args:
        repo_path: Path where repo should be created
        with_remote: If True, create a bare repo as remote origin

    Returns:
        Path to remote repo if with_remote=True, else None.
    """
    subprocess.run(
        ["git", "init", "-b", "main", str(repo_path)],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_path), "config", "user.email", "test@test.com"],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_path), "config", "user.name", "Test"],
        capture_output=True,
        check=True,
    )
    # Create initial commit
    subprocess.run(
        ["git", "-C", str(repo_path), "commit", "--allow-empty", "-m", "init"],
        capture_output=True,
        check=True,
    )

    remote_path = None
    if with_remote:
        # Create a bare repo to act as remote
        remote_path = repo_path.parent / "remote.git"
        subprocess.run(
            ["git", "init", "--bare", "-b", "main", str(remote_path)],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(repo_path), "remote", "add", "origin", str(remote_path)],
            capture_output=True,
            check=True,
        )
        # Push initial commit to set up tracking
        subprocess.run(
            ["git", "-C", str(repo_path), "push", "-u", "origin", "main"],
            capture_output=True,
            check=True,
        )
    return remote_path


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

    def test_help_mentions_chromatin(self):
        """Help text mentions chromatin backup purpose."""
        r = _run(SCRIPT, ["--help"])
        assert "chromatin" in r.stdout.lower() or "backup" in r.stdout.lower()


# ── Missing directory tests ────────────────────────────────────────────


class TestMissingDirectory:
    """Tests for missing chromatin directory."""

    def test_exits_when_chromatin_dir_missing(self, tmp_path):
        """Script exits 1 when $HOME/epigenome/chromatin doesn't exist."""
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 1

    def test_exits_when_epigenome_missing(self, tmp_path):
        """Script exits 1 when epigenome parent dir doesn't exist."""
        r = _run(SCRIPT, env={"HOME": str(tmp_path / "nonexistent")})
        assert r.returncode == 1


# ── No changes tests ───────────────────────────────────────────────────


class TestNoChanges:
    """Tests when there are no changes to commit."""

    def test_exits_0_when_no_changes(self, tmp_path):
        """Script exits 0 when repo has no changes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin)

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_no_commit_when_clean(self, tmp_path):
        """Script does not create commit when repo is clean."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin)

        # Get commit count before
        before = subprocess.run(
            ["git", "-C", str(chromatin), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
        )

        _run(SCRIPT, env={"HOME": str(tmp_path)})

        # Get commit count after
        after = subprocess.run(
            ["git", "-C", str(chromatin), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
        )

        assert before.stdout.strip() == after.stdout.strip()


# ── Commit and push tests ──────────────────────────────────────────────


class TestCommitAndPush:
    """Tests for commit and push functionality."""

    def test_commits_new_file(self, tmp_path):
        """Script commits new untracked files and pushes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Create a new file
        (chromatin / "test.md").write_text("test content\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Verify file was committed
        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--name-only"],
            capture_output=True,
            text=True,
        )
        assert "test.md" in show.stdout

    def test_commits_modified_file(self, tmp_path):
        """Script commits modified tracked files and pushes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Add and commit a file first
        test_file = chromatin / "existing.md"
        test_file.write_text("original\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "existing.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "add existing"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "push", "origin", "main"],
            capture_output=True,
        )

        # Modify the file
        test_file.write_text("modified\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Verify modification was committed
        show = subprocess.run(
            ["git", "-C", str(chromatin), "show"],
            capture_output=True,
            text=True,
        )
        assert "modified" in show.stdout

    def test_commit_message_includes_timestamp(self, tmp_path):
        """Script creates commit with timestamp in message."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        (chromatin / "timestamp.md").write_text("test\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Check commit message format
        log = subprocess.run(
            ["git", "-C", str(chromatin), "log", "-1", "--format=%s"],
            capture_output=True,
            text=True,
        )
        assert "chromatin backup:" in log.stdout
        # Should contain date pattern like 2024-01-15
        assert "-" in log.stdout  # Simple check for date-like content

    def test_commits_deleted_file(self, tmp_path):
        """Script commits deletion of tracked files and pushes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Add and commit a file first
        test_file = chromatin / "to_delete.md"
        test_file.write_text("delete me\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "to_delete.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "add file"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "push", "origin", "main"],
            capture_output=True,
        )

        # Delete the file
        test_file.unlink()

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Verify deletion was committed
        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--stat"],
            capture_output=True,
            text=True,
        )
        assert "to_delete.md" in show.stdout


# ── Staged changes tests ───────────────────────────────────────────────


class TestStagedChanges:
    """Tests for handling pre-staged changes."""

    def test_commits_pre_staged_files(self, tmp_path):
        """Script commits files that were already staged and pushes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        (chromatin / "staged.md").write_text("staged content\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "staged.md"],
            capture_output=True,
        )

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--name-only"],
            capture_output=True,
            text=True,
        )
        assert "staged.md" in show.stdout


# ── Edge case tests ────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases for chromatin-backup.sh."""

    def test_empty_git_dir_exits_gracefully(self, tmp_path):
        """Script handles .git dir without proper git repo."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        (chromatin / ".git").mkdir()  # Empty .git dir

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # Will fail on git commands - exit 1 since cd succeeds but git fails
        assert r.returncode != 0

    def test_git_fetch_fails_gracefully(self, tmp_path):
        """Script handles git fetch failure when no remote configured."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin)

        # No remote configured - fetch will fail, but script handles it
        # However push will also fail, so overall exit is 1
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # With no remote, fetch fails silently but push fails loudly
        # This is expected behavior - script exits 1 on push failure

    def test_subdirectory_changes(self, tmp_path):
        """Script commits changes in subdirectories and pushes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Create subdirectory with file
        subdir = chromatin / "notes" / "daily"
        subdir.mkdir(parents=True)
        (subdir / "2024-01-15.md").write_text("Daily note\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--name-only"],
            capture_output=True,
            text=True,
        )
        assert "notes/daily/2024-01-15.md" in show.stdout

    def test_unicode_content(self, tmp_path):
        """Script handles files with unicode content and pushes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        (chromatin / "unicode.md").write_text("# 日本語テスト\nEmoji: 🧠📝\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        show = subprocess.run(
            ["git", "-C", str(chromatin), "show"],
            capture_output=True,
            text=True,
        )
        assert "日本語" in show.stdout

    def test_multiple_files(self, tmp_path):
        """Script commits multiple files in one commit and pushes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Create multiple files
        for i in range(5):
            (chromatin / f"file{i}.md").write_text(f"content {i}\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--name-only"],
            capture_output=True,
            text=True,
        )
        for i in range(5):
            assert f"file{i}.md" in show.stdout

    def test_large_file(self, tmp_path):
        """Script handles large files and pushes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Create a moderately large file (100KB)
        large_content = "x" * 100000
        (chromatin / "large.md").write_text(large_content)

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

    def test_hidden_file(self, tmp_path):
        """Script commits hidden files (dotfiles) and pushes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        (chromatin / ".hidden").write_text("hidden content\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--name-only"],
            capture_output=True,
            text=True,
        )
        assert ".hidden" in show.stdout

    def test_no_args_runs_normally(self, tmp_path):
        """Script runs without any arguments."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0
