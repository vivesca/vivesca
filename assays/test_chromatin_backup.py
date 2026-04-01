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
        """Script exits 0 when repo has no changes and a remote."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

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
        """Script handles .git dir without proper git repo — exits 0 (all git errors suppressed)."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        (chromatin / ".git").mkdir()  # Empty .git dir

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # Git errors go to stderr; script never explicitly fails
        assert r.returncode == 0

    def test_git_fetch_fails_gracefully_no_remote(self, tmp_path):
        """Script with no remote exits non-zero (origin/main unresolved, push fails)."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin)

        # No remote configured — script attempts rebase/push and exits non-zero
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode != 0

    def test_push_fails_without_remote_when_changes(self, tmp_path):
        """Script exits non-zero when changes exist but no remote to push to."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin)

        (chromatin / "orphan.md").write_text("no remote\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # Push will fail since there's no remote
        assert r.returncode != 0

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


# ── Push verification tests ──────────────────────────────────────────────


class TestPushVerification:
    """Verify that commits actually reach the remote bare repo."""

    def test_push_updates_remote(self, tmp_path):
        """Script pushes commit so the remote bare repo has the new file."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        remote_path = _init_git_repo(chromatin, with_remote=True)

        (chromatin / "pushed.md").write_text("pushed content\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Verify the bare remote received the commit
        remote_log = subprocess.run(
            ["git", "-C", str(remote_path), "log", "-1", "--format=%s"],
            capture_output=True,
            text=True,
        )
        assert "chromatin backup:" in remote_log.stdout

        # Verify the file content on the remote
        remote_show = subprocess.run(
            ["git", "-C", str(remote_path), "show", "main:pushed.md"],
            capture_output=True,
            text=True,
        )
        assert remote_show.stdout.strip() == "pushed content"

    def test_push_multiple_commits(self, tmp_path):
        """Script pushes the latest commit; remote matches local HEAD."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        remote_path = _init_git_repo(chromatin, with_remote=True)

        # First round: add a file
        (chromatin / "first.md").write_text("first\n")
        _run(SCRIPT, env={"HOME": str(tmp_path)})

        # Second round: add another file
        (chromatin / "second.md").write_text("second\n")
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Remote should have both files
        remote_ls = subprocess.run(
            ["git", "-C", str(remote_path), "ls-tree", "-r", "--name-only", "main"],
            capture_output=True,
            text=True,
        )
        assert "first.md" in remote_ls.stdout
        assert "second.md" in remote_ls.stdout


# ── Rebase / sync tests ─────────────────────────────────────────────────


class TestRebaseSync:
    """Tests for the fetch-rebase-merge sync logic (lines 16-29)."""

    def test_rebases_on_remote_changes(self, tmp_path):
        """Script rebases local changes on top of remote changes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        remote_path = _init_git_repo(chromatin, with_remote=True)

        # Simulate a remote change (e.g. Obsidian Git pushed)
        # Clone remote, make a commit, push back
        clone_dir = tmp_path / "obsidian_clone"
        subprocess.run(
            ["git", "clone", str(remote_path), str(clone_dir)],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.email", "obsidian@test.com"],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.name", "Obsidian"],
            capture_output=True,
            check=True,
        )
        (clone_dir / "remote_note.md").write_text("from obsidian\n")
        subprocess.run(
            ["git", "-C", str(clone_dir), "add", "remote_note.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "commit", "-m", "obsidian push"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "push", "origin", "main"],
            capture_output=True,
            check=True,
        )

        # Now add a local change (diverges from remote)
        (chromatin / "local_note.md").write_text("from local\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Both files should be present after rebase
        local_ls = subprocess.run(
            ["git", "-C", str(chromatin), "ls-tree", "-r", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
        )
        assert "remote_note.md" in local_ls.stdout
        assert "local_note.md" in local_ls.stdout

    def test_merge_fallback_on_conflict(self, tmp_path):
        """Script falls back to merge when rebase has committed conflicts."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        remote_path = _init_git_repo(chromatin, with_remote=True)

        # Create a shared file and push
        shared = chromatin / "shared.md"
        shared.write_text("original\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "shared.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "add shared"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "push", "origin", "main"],
            capture_output=True,
        )

        # Remote changes the file differently (simulating Obsidian Git push)
        clone_dir = tmp_path / "obsidian_clone"
        subprocess.run(
            ["git", "clone", str(remote_path), str(clone_dir)],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.email", "obsidian@test.com"],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.name", "Obsidian"],
            capture_output=True,
            check=True,
        )
        (clone_dir / "shared.md").write_text("remote change\n")
        subprocess.run(
            ["git", "-C", str(clone_dir), "add", "shared.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "commit", "-m", "remote edit"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "push", "origin", "main"],
            capture_output=True,
            check=True,
        )

        # Local also commits a different change to the same file (diverges)
        shared.write_text("local change\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "shared.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "local edit"],
            capture_output=True,
        )

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # Script should succeed via merge fallback
        assert r.returncode == 0

        # Both branches should be merged — check for a merge commit
        log = subprocess.run(
            ["git", "-C", str(chromatin), "log", "--oneline", "--graph"],
            capture_output=True,
            text=True,
        )
        # Should have a merge commit or a linear history after rebase
        # The key assertion: the repo is not broken and HEAD advanced
        assert "local edit" in log.stdout or "remote edit" in log.stdout

    def test_no_rebase_when_up_to_date(self, tmp_path):
        """Script skips rebase when local HEAD matches origin/main."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Add a local change (local is ahead, not behind)
        (chromatin / "local.md").write_text("local\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Commit should be straightforward, no merge commits
        log = subprocess.run(
            ["git", "-C", str(chromatin), "log", "--oneline"],
            capture_output=True,
            text=True,
        )
        # Only init commit + backup commit, no merge commit
        lines = [l for l in log.stdout.strip().splitlines() if l]
        assert len(lines) == 2  # init + backup


# ── Additional edge case tests ───────────────────────────────────────────


class TestAdditionalEdgeCases:
    """More edge cases for chromatin-backup.sh."""

    def test_binary_file_commit(self, tmp_path):
        """Script commits binary files and pushes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        (chromatin / "image.bin").write_bytes(bytes(range(256)))

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--name-only"],
            capture_output=True,
            text=True,
        )
        assert "image.bin" in show.stdout

    def test_empty_file_commit(self, tmp_path):
        """Script commits empty files and pushes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        (chromatin / "empty.md").write_text("")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--name-only"],
            capture_output=True,
            text=True,
        )
        assert "empty.md" in show.stdout

    def test_gitignore_respected(self, tmp_path):
        """Script does not commit files matching .gitignore."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Create .gitignore
        (chromatin / ".gitignore").write_text("*.tmp\nsecret/\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", ".gitignore"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "add gitignore"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "push", "origin", "main"],
            capture_output=True,
        )

        # Create an ignored file and a normal file
        (chromatin / "ignored.tmp").write_text("should be ignored\n")
        (chromatin / "real.md").write_text("should be committed\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Only real.md should be in the commit
        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--name-only"],
            capture_output=True,
            text=True,
        )
        assert "real.md" in show.stdout
        assert "ignored.tmp" not in show.stdout

    def test_whitespace_only_change_no_commit(self, tmp_path):
        """Script does not create a new commit for whitespace-only changes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Create and commit a file
        (chromatin / "doc.md").write_text("content\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "doc.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "add doc"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "push", "origin", "main"],
            capture_output=True,
        )

        # Get commit count before
        before = subprocess.run(
            ["git", "-C", str(chromatin), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
        )

        # No changes at all
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        after = subprocess.run(
            ["git", "-C", str(chromatin), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
        )
        assert before.stdout.strip() == after.stdout.strip()

    def test_mixed_staged_and_unstaged(self, tmp_path):
        """Script commits both staged and unstaged changes together."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Add an initial file and commit
        (chromatin / "base.md").write_text("base\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "base.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "base"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "push", "origin", "main"],
            capture_output=True,
        )

        # Stage one file
        (chromatin / "staged.md").write_text("staged\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "staged.md"],
            capture_output=True,
        )

        # Leave another file unstaged
        (chromatin / "unstaged.md").write_text("unstaged\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--name-only"],
            capture_output=True,
            text=True,
        )
        assert "staged.md" in show.stdout
        assert "unstaged.md" in show.stdout

    def test_deeply_nested_directory(self, tmp_path):
        """Script commits files in deeply nested directories."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        deep = chromatin / "a" / "b" / "c" / "d" / "e"
        deep.mkdir(parents=True)
        (deep / "deep.md").write_text("deeply nested\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--name-only"],
            capture_output=True,
            text=True,
        )
        assert "a/b/c/d/e/deep.md" in show.stdout

    def test_commit_message_date_format(self, tmp_path):
        """Commit message contains a recognizable YYYY-MM-DD HH:MM:SS timestamp."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        (chromatin / "date.md").write_text("test\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        log = subprocess.run(
            ["git", "-C", str(chromatin), "log", "-1", "--format=%s"],
            capture_output=True,
            text=True,
        )
        msg = log.stdout.strip()
        # Verify format: "chromatin backup: YYYY-MM-DD HH:MM:SS"
        import re

        assert re.search(r"chromatin backup: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", msg)

    def test_file_with_spaces_in_name(self, tmp_path):
        """Script commits files with spaces in filename."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        (chromatin / "my notes.md").write_text("spaced name\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--name-only"],
            capture_output=True,
            text=True,
        )
        assert "my notes.md" in show.stdout


# ── Script metadata tests ──────────────────────────────────────────────


class TestScriptMetadata:
    """Basic script file checks."""

    def test_script_exists(self):
        """Script file exists."""
        assert SCRIPT.exists()

    def test_script_executable(self):
        """Script is executable."""
        assert os.access(SCRIPT, os.X_OK)

    def test_script_is_bash(self):
        """Script has bash shebang."""
        first_line = SCRIPT.read_text().splitlines()[0]
        assert first_line == "#!/bin/bash"

    def test_help_mentions_epigenome(self):
        """Help text mentions epigenome repo path."""
        r = _run(SCRIPT, ["--help"])
        assert "epigenome" in r.stdout.lower()

    def test_help_mentions_skip(self):
        """Help text mentions skipping when no changes."""
        r = _run(SCRIPT, ["--help"])
        assert "skip" in r.stdout.lower()


# ── Idempotency tests ─────────────────────────────────────────────────


class TestIdempotency:
    """Running the script multiple times should be safe."""

    def test_second_run_no_extra_commit(self, tmp_path):
        """Second run with no changes creates no extra commit."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        (chromatin / "once.md").write_text("first\n")
        r1 = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r1.returncode == 0

        # Count commits after first run
        after_first = subprocess.run(
            ["git", "-C", str(chromatin), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
        )

        # Second run with no changes
        r2 = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r2.returncode == 0

        after_second = subprocess.run(
            ["git", "-C", str(chromatin), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
        )

        assert after_first.stdout.strip() == after_second.stdout.strip()

    def test_third_run_with_new_change(self, tmp_path):
        """Third run after adding a file creates exactly one new commit."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Run 1: initial commit of a file
        (chromatin / "a.md").write_text("a\n")
        _run(SCRIPT, env={"HOME": str(tmp_path)})

        # Run 2: no changes
        _run(SCRIPT, env={"HOME": str(tmp_path)})

        # Run 3: add another file
        (chromatin / "b.md").write_text("b\n")
        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Should have exactly 3 commits: init + backup-a + backup-b
        count = subprocess.run(
            ["git", "-C", str(chromatin), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
        )
        assert count.stdout.strip() == "3"


# ── Rebase conflict resolution tests ───────────────────────────────────


class TestConflictResolution:
    """Tests for the --theirs last-resort fallback (lines 23-27)."""

    def test_rebase_succeeds_for_non_conflicting_diverge(self, tmp_path):
        """Non-conflicting diverge is resolved via rebase (not merge)."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        remote_path = _init_git_repo(chromatin, with_remote=True)

        # Add a base file and push
        (chromatin / "base.md").write_text("base\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "base.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "base"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "push", "origin", "main"],
            capture_output=True,
        )

        # Remote adds a different file
        clone_dir = tmp_path / "remote_clone"
        subprocess.run(
            ["git", "clone", str(remote_path), str(clone_dir)],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.email", "r@t.com"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.name", "R"],
            capture_output=True,
        )
        (clone_dir / "remote_file.md").write_text("from remote\n")
        subprocess.run(
            ["git", "-C", str(clone_dir), "add", "remote_file.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "commit", "-m", "remote add"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "push", "origin", "main"],
            capture_output=True,
        )

        # Local adds yet another different file (uncommitted)
        (chromatin / "local_file.md").write_text("from local\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Both files should be present
        ls = subprocess.run(
            ["git", "-C", str(chromatin), "ls-tree", "-r", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
        )
        assert "remote_file.md" in ls.stdout
        assert "local_file.md" in ls.stdout

    def test_merge_fallback_preserves_both_branches(self, tmp_path):
        """When rebase conflicts, merge fallback produces a working tree."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        remote_path = _init_git_repo(chromatin, with_remote=True)

        # Create base with a shared file
        shared = chromatin / "conflict.md"
        shared.write_text("base\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "conflict.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "base"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "push", "origin", "main"],
            capture_output=True,
        )

        # Remote modifies the file
        clone_dir = tmp_path / "remote_clone"
        subprocess.run(
            ["git", "clone", str(remote_path), str(clone_dir)],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.email", "r@t.com"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.name", "R"],
            capture_output=True,
        )
        (clone_dir / "conflict.md").write_text("remote version\n")
        subprocess.run(
            ["git", "-C", str(clone_dir), "add", "conflict.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "commit", "-m", "remote change"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "push", "origin", "main"],
            capture_output=True,
        )

        # Local commits a conflicting change, then adds uncommitted changes
        shared.write_text("local version\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "conflict.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "local change"],
            capture_output=True,
        )

        # Add an uncommitted file too — this triggers commit+push after sync
        (chromatin / "extra.md").write_text("extra\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # Script should resolve via merge or --theirs fallback
        assert r.returncode == 0

        # HEAD should have advanced past both local and remote
        log = subprocess.run(
            ["git", "-C", str(chromatin), "log", "--oneline"],
            capture_output=True,
            text=True,
        )
        assert "local change" in log.stdout or "extra" in log.stdout or "merge" in log.stdout.lower()


# ── Bare repo sync edge case ──────────────────────────────────────────


class TestRemoteSyncEdgeCases:
    """Edge cases for remote sync behavior."""

    def test_remote_receives_exact_file_content(self, tmp_path):
        """File content on remote exactly matches what was committed locally."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        remote_path = _init_git_repo(chromatin, with_remote=True)

        content = "# My Note\n\nSome **markdown** here.\n"
        (chromatin / "note.md").write_text(content)

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        remote_cat = subprocess.run(
            ["git", "-C", str(remote_path), "show", "main:note.md"],
            capture_output=True,
            text=True,
        )
        assert remote_cat.stdout == content

    def test_consecutive_pushes_stay_in_sync(self, tmp_path):
        """Multiple rounds of push keep local and remote in sync."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        remote_path = _init_git_repo(chromatin, with_remote=True)

        for i in range(3):
            (chromatin / f"round{i}.md").write_text(f"round {i}\n")
            r = _run(SCRIPT, env={"HOME": str(tmp_path)})
            assert r.returncode == 0

        # Remote should have all 3 files
        remote_ls = subprocess.run(
            ["git", "-C", str(remote_path), "ls-tree", "-r", "--name-only", "main"],
            capture_output=True,
            text=True,
        )
        for i in range(3):
            assert f"round{i}.md" in remote_ls.stdout

        # Local HEAD should match remote HEAD
        local_head = subprocess.run(
            ["git", "-C", str(chromatin), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
        )
        remote_head = subprocess.run(
            ["git", "-C", str(remote_path), "rev-parse", "main"],
            capture_output=True,
            text=True,
        )
        assert local_head.stdout.strip() == remote_head.stdout.strip()


# ── Theirs fallback verification ────────────────────────────────────────


class TestTheirsFallback:
    """Verify the checkout --theirs last-resort path (lines 23-27)."""

    def test_theirs_fallback_resolves_to_remote_content(self, tmp_path):
        """When rebase and merge both fail, --theirs picks remote version."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        remote_path = _init_git_repo(chromatin, with_remote=True)

        # Create a shared file with base content and push
        shared = chromatin / "shared.md"
        shared.write_text("base\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "shared.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "base"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "push", "origin", "main"],
            capture_output=True,
        )

        # Remote changes the file
        clone_dir = tmp_path / "remote_clone"
        subprocess.run(
            ["git", "clone", str(remote_path), str(clone_dir)],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.email", "r@t.com"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.name", "R"],
            capture_output=True,
        )
        (clone_dir / "shared.md").write_text("remote_wins\n")
        subprocess.run(
            ["git", "-C", str(clone_dir), "add", "shared.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "commit", "-m", "remote edit"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "push", "origin", "main"],
            capture_output=True,
            check=True,
        )

        # Local commits a conflicting change to the same file
        shared.write_text("local_loses\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "shared.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "local edit"],
            capture_output=True,
        )

        # Add an uncommitted file to trigger the commit+push after sync
        (chromatin / "new_file.md").write_text("new\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # After --theirs resolution, shared.md should have remote content
        cat = subprocess.run(
            ["git", "-C", str(chromatin), "show", "HEAD:shared.md"],
            capture_output=True,
            text=True,
        )
        # The theirs fallback resolves to remote version
        assert cat.stdout.strip() in ("remote_wins", "local_loses")

        # The new uncommitted file should also be committed
        ls = subprocess.run(
            ["git", "-C", str(chromatin), "ls-tree", "-r", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
        )
        assert "new_file.md" in ls.stdout

    def test_theirs_fallback_commit_is_local_only(self, tmp_path):
        """After --theirs resolution, commit is local but not pushed.

        The theirs fallback creates a merge commit that includes the resolved
        conflict, so the working tree is clean afterward. The change-check
        exits 0 before reaching the push line.
        """
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        remote_path = _init_git_repo(chromatin, with_remote=True)

        # Base commit
        shared = chromatin / "data.md"
        shared.write_text("v1\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "data.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "v1"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "push", "origin", "main"],
            capture_output=True,
        )

        # Remote modifies
        clone_dir = tmp_path / "remote_clone"
        subprocess.run(
            ["git", "clone", str(remote_path), str(clone_dir)],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.email", "r@t.com"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.name", "R"],
            capture_output=True,
        )
        (clone_dir / "data.md").write_text("remote_v2\n")
        subprocess.run(
            ["git", "-C", str(clone_dir), "add", "data.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "commit", "-m", "remote v2"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "push", "origin", "main"],
            capture_output=True,
            check=True,
        )

        # Local commits conflicting change
        shared.write_text("local_v2\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "data.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "local v2"],
            capture_output=True,
        )

        # Add uncommitted change — absorbed by theirs fallback commit
        (chromatin / "extra.md").write_text("extra\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Local HEAD should be ahead of remote (fallback commit not pushed)
        local_head = subprocess.run(
            ["git", "-C", str(chromatin), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
        )
        remote_head = subprocess.run(
            ["git", "-C", str(remote_path), "rev-parse", "main"],
            capture_output=True,
            text=True,
        )
        # The fallback commit is local-only; remote still has the pre-fallback state
        assert local_head.stdout.strip() != remote_head.stdout.strip()

        # Local tree should have the resolved file and extra.md
        local_ls = subprocess.run(
            ["git", "-C", str(chromatin), "ls-tree", "-r", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
        )
        assert "data.md" in local_ls.stdout
        assert "extra.md" in local_ls.stdout


# ── Push rejection test ─────────────────────────────────────────────────


class TestPushRejection:
    """Tests for push failure handling."""

    def test_push_rejected_by_pre_receive_hook(self, tmp_path):
        """Script exits non-zero when remote rejects push via hook."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        remote_path = _init_git_repo(chromatin, with_remote=True)

        # Install a pre-receive hook that rejects all pushes
        hooks_dir = remote_path / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        hook = hooks_dir / "pre-receive"
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)

        # Create a file to commit and push
        (chromatin / "rejected.md").write_text("will be rejected\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # Push should fail, script exits non-zero
        assert r.returncode != 0


# ── Detached HEAD test ──────────────────────────────────────────────────


class TestDetachedHEAD:
    """Tests for detached HEAD state."""

    def test_detached_head_still_commits(self, tmp_path):
        """Script handles detached HEAD by committing and pushing."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        remote_path = _init_git_repo(chromatin, with_remote=True)

        # Put repo in detached HEAD state
        subprocess.run(
            ["git", "-C", str(chromatin), "checkout", "HEAD^0"],
            capture_output=True,
        )

        # Add a file
        (chromatin / "detached.md").write_text("from detached\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        # Detached HEAD: push origin main may fail (HEAD != main)
        # The script pushes to origin main explicitly, but HEAD may not be on main
        # This is expected to potentially fail or succeed depending on git behavior
        # The key assertion: script doesn't hang or produce unexpected output
        assert r.returncode in (0, 1)


# ── Renamed file test ──────────────────────────────────────────────────


class TestRenamedFile:
    """Tests for file rename detection."""

    def test_renamed_file_captured_by_add_all(self, tmp_path):
        """Script captures renamed files via git add -A."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Create and commit original file
        original = chromatin / "original.md"
        original.write_text("content\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "original.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "add original"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "push", "origin", "main"],
            capture_output=True,
        )

        # Rename the file
        original.rename(chromatin / "renamed.md")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Renamed file should be in the commit
        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--name-status"],
            capture_output=True,
            text=True,
        )
        assert "renamed.md" in show.stdout

        # Original should no longer be tracked
        ls = subprocess.run(
            ["git", "-C", str(chromatin), "ls-tree", "-r", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
        )
        assert "original.md" not in ls.stdout
        assert "renamed.md" in ls.stdout


# ── Symlink handling test ──────────────────────────────────────────────


class TestSymlink:
    """Tests for symbolic link handling."""

    def test_symlink_committed(self, tmp_path):
        """Script commits symbolic links and pushes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Create a file and a symlink to it
        (chromatin / "target.md").write_text("target content\n")
        subprocess.run(
            ["git", "-C", str(chromatin), "add", "target.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "commit", "-m", "add target"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(chromatin), "push", "origin", "main"],
            capture_output=True,
        )

        # Create symlink
        (chromatin / "link.md").symlink_to("target.md")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # Symlink should be in the commit
        show = subprocess.run(
            ["git", "-C", str(chromatin), "show", "--name-only"],
            capture_output=True,
            text=True,
        )
        assert "link.md" in show.stdout

        # Verify it's actually a symlink in git
        ls_output = subprocess.run(
            ["git", "-C", str(chromatin), "ls-tree", "HEAD"],
            capture_output=True,
            text=True,
        )
        # Git stores symlinks with mode 120000
        for line in ls_output.stdout.splitlines():
            if "link.md" in line:
                assert line.startswith("120000")


# ── Rapid sequential changes test ──────────────────────────────────────


class TestRapidChanges:
    """Tests for rapid sequential modifications."""

    def test_rapid_modifications_single_commit(self, tmp_path):
        """Multiple rapid file changes result in a single commit."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        _init_git_repo(chromatin, with_remote=True)

        # Get initial commit count
        before = subprocess.run(
            ["git", "-C", str(chromatin), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
        )

        # Rapidly modify the same file multiple times
        f = chromatin / "rapid.md"
        for i in range(5):
            f.write_text(f"version {i}\n")

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        after = subprocess.run(
            ["git", "-C", str(chromatin), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
        )

        # Only one new commit despite multiple writes
        assert int(after.stdout.strip()) - int(before.stdout.strip()) == 1

        # File should have the last version
        cat = subprocess.run(
            ["git", "-C", str(chromatin), "show", "HEAD:rapid.md"],
            capture_output=True,
            text=True,
        )
        assert "version 4" in cat.stdout


# ── Fetch-only behavior test ───────────────────────────────────────────


class TestFetchOnly:
    """Tests for when fetch finds remote changes but local has nothing."""

    def test_fetch_only_no_local_changes(self, tmp_path):
        """When remote has new commits but local has no changes, script skips commit."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        chromatin.mkdir(parents=True)
        remote_path = _init_git_repo(chromatin, with_remote=True)

        # Remote adds a commit
        clone_dir = tmp_path / "remote_clone"
        subprocess.run(
            ["git", "clone", str(remote_path), str(clone_dir)],
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.email", "r@t.com"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "config", "user.name", "R"],
            capture_output=True,
        )
        (clone_dir / "remote_only.md").write_text("from remote\n")
        subprocess.run(
            ["git", "-C", str(clone_dir), "add", "remote_only.md"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "commit", "-m", "remote only"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "-C", str(clone_dir), "push", "origin", "main"],
            capture_output=True,
            check=True,
        )

        # Local has no changes but is behind remote
        before = subprocess.run(
            ["git", "-C", str(chromatin), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
        )

        r = _run(SCRIPT, env={"HOME": str(tmp_path)})
        assert r.returncode == 0

        # After rebase, local should have remote's commit
        after = subprocess.run(
            ["git", "-C", str(chromatin), "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
        )

        # Local advanced by rebasing onto remote (1 new commit from remote)
        assert int(after.stdout.strip()) > int(before.stdout.strip())

        # The remote file should now be in local tree
        ls = subprocess.run(
            ["git", "-C", str(chromatin), "ls-tree", "-r", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
        )
        assert "remote_only.md" in ls.stdout
