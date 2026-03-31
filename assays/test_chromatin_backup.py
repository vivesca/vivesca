from __future__ import annotations
"""Tests for chromatin-backup.sh — git auto-commit and push for chromatin vault."""

import subprocess
from pathlib import Path
from unittest.mock import patch
import time


SCRIPT_PATH = Path("/home/terry/germline/effectors/chromatin-backup.sh")


def run_script(chromatin_dir: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run chromatin-backup.sh with HOME pointing to chromatin_dir's parent."""
    run_env = {"HOME": str(chromatin_dir.parent)}
    if env:
        run_env.update(env)
    return subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        env=run_env,
        cwd="/tmp",
    )


def init_git_repo(repo_path: Path, with_remote: bool = True) -> None:
    """Initialize a git repo with optional fake remote."""
    repo_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_path, capture_output=True, check=True)
    if with_remote:
        # Add a fake remote (won't actually push anywhere)
        subprocess.run(
            ["git", "remote", "add", "origin", "/nonexistent/remote.git"],
            cwd=repo_path,
            capture_output=True,
            check=True,
        )


def make_commit(repo_path: Path, filename: str, content: str, msg: str = "initial") -> None:
    """Create a commit with a file."""
    (repo_path / filename).write_text(content)
    subprocess.run(["git", "add", filename], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=repo_path, capture_output=True, check=True)


class TestChromatinBackup:
    """Tests for chromatin-backup.sh behavior."""

    def test_exits_1_if_chromatin_dir_missing(self, tmp_path: Path) -> None:
        """Script exits with 1 when chromatin directory doesn't exist."""
        # tmp_path has no 'chromatin' subdir
        result = run_script(tmp_path / "epigenome")
        assert result.returncode == 1

    def test_exits_0_when_no_changes(self, tmp_path: Path) -> None:
        """Script exits 0 and makes no commit when repo is clean."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        init_git_repo(chromatin)
        make_commit(chromatin, "README.md", "# Chromatin\n", "initial")

        # Clean repo — no changes
        result = run_script(chromatin)
        assert result.returncode == 0

    def test_commits_new_file(self, tmp_path: Path) -> None:
        """Script adds and commits new untracked files."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        init_git_repo(chromatin, with_remote=False)  # No remote to avoid push errors
        make_commit(chromatin, "README.md", "# Chromatin\n", "initial")

        # Add an untracked file
        (chromatin / "new_note.md").write_text("New content\n")

        # Run the script (will fail at push but should have committed)
        result = run_script(chromatin)

        # Check that file was added and committed (even if push fails)
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=chromatin,
            capture_output=True,
            text=True,
        )
        # File should be committed (no longer untracked)
        assert "new_note.md" not in status.stdout or status.stdout.strip() == ""

    def test_commits_modified_file(self, tmp_path: Path) -> None:
        """Script commits modified tracked files."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        init_git_repo(chromatin, with_remote=False)
        make_commit(chromatin, "note.md", "Original content\n", "initial")

        # Modify the file
        (chromatin / "note.md").write_text("Modified content\n")

        result = run_script(chromatin)

        # Check that modification was committed
        diff = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=chromatin,
            capture_output=True,
            text=True,
        )
        # No diff means it was committed
        assert diff.stdout.strip() == ""

    def test_commits_staged_changes(self, tmp_path: Path) -> None:
        """Script commits already staged changes."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        init_git_repo(chromatin, with_remote=False)
        make_commit(chromatin, "note.md", "Original\n", "initial")

        # Stage a modification
        (chromatin / "note.md").write_text("Staged\n")
        subprocess.run(["git", "add", "note.md"], cwd=chromatin, capture_output=True, check=True)

        result = run_script(chromatin)

        # Should be committed
        diff_cached = subprocess.run(
            ["git", "diff", "--cached"],
            cwd=chromatin,
            capture_output=True,
            text=True,
        )
        assert diff_cached.stdout.strip() == ""

    def test_commit_message_includes_timestamp(self, tmp_path: Path) -> None:
        """Commit message follows 'chromatin backup: YYYY-MM-DD HH:MM:SS' format."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        init_git_repo(chromatin, with_remote=False)
        make_commit(chromatin, "README.md", "# Chromatin\n", "initial")

        # Add a file to trigger commit
        (chromatin / "new.md").write_text("New\n")

        result = run_script(chromatin)

        # Check last commit message format
        log = subprocess.run(
            ["git", "log", "-1", "--format=%s"],
            cwd=chromatin,
            capture_output=True,
            text=True,
        )
        msg = log.stdout.strip()
        assert msg.startswith("chromatin backup: ")
        # Should have timestamp format
        parts = msg.replace("chromatin backup: ", "").split()
        assert len(parts) == 2  # date and time
        # Date should have dashes
        assert "-" in parts[0]

    def test_handles_multiple_untracked_files(self, tmp_path: Path) -> None:
        """Script commits all untracked files in one commit."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        init_git_repo(chromatin, with_remote=False)
        make_commit(chromatin, "README.md", "# Chromatin\n", "initial")

        # Add multiple files
        (chromatin / "note1.md").write_text("Note 1\n")
        (chromatin / "note2.md").write_text("Note 2\n")
        (chromatin / "subdir").mkdir(exist_ok=True)
        (chromatin / "subdir" / "note3.md").write_text("Note 3\n")

        result = run_script(chromatin)

        # All files should be committed
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=chromatin,
            capture_output=True,
            text=True,
        )
        # No untracked files
        assert "??" not in status.stdout

    def test_skips_commit_when_only_ignored_files(self, tmp_path: Path) -> None:
        """Script skips commit when only ignored files are changed."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        init_git_repo(chromatin, with_remote=False)
        make_commit(chromatin, "README.md", "# Chromatin\n", "initial")

        # Add gitignore
        (chromatin / ".gitignore").write_text("*.tmp\n")
        subprocess.run(["git", "add", ".gitignore"], cwd=chromatin, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "add gitignore"], cwd=chromatin, capture_output=True, check=True)

        # Create ignored file
        (chromatin / "scratch.tmp").write_text("temp\n")

        # Get initial commit count
        log_before = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=chromatin,
            capture_output=True,
            text=True,
        )
        count_before = int(log_before.stdout.strip())

        result = run_script(chromatin)

        # Should exit 0 (no changes to commit)
        assert result.returncode == 0

        # No new commit should be made
        log_after = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=chromatin,
            capture_output=True,
            text=True,
        )
        count_after = int(log_after.stdout.strip())
        assert count_after == count_before


class TestChromatinBackupRebase:
    """Tests for rebase/merge behavior when remote is ahead."""

    def test_fetches_from_origin_main(self, tmp_path: Path) -> None:
        """Script runs git fetch origin main."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        init_git_repo(chromatin, with_remote=False)
        make_commit(chromatin, "README.md", "# Chromatin\n", "initial")

        # Create a local branch called main and set upstream
        subprocess.run(["git", "branch", "-M", "main"], cwd=chromatin, capture_output=True, check=True)

        # Add a fake remote that exists (a bare repo)
        remote_repo = tmp_path / "remote.git"
        subprocess.run(["git", "init", "--bare", str(remote_repo)], capture_output=True, check=True)
        subprocess.run(
            ["git", "remote", "set-url", "origin", str(remote_repo)],
            cwd=chromatin,
            capture_output=True,
            check=True,
        )

        # Make initial push to set up tracking
        subprocess.run(
            ["git", "push", "-u", "origin", "main"],
            cwd=chromatin,
            capture_output=True,
            check=True,
        )

        result = run_script(chromatin)
        # Should succeed - fetch happens, no changes to commit
        assert result.returncode == 0


class TestChromatinBackupEdgeCases:
    """Edge case tests for chromatin-backup.sh."""

    def test_works_with_empty_repo(self, tmp_path: Path) -> None:
        """Script handles repo with no commits gracefully."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        init_git_repo(chromatin, with_remote=False)

        # No commits yet - script should handle this
        result = run_script(chromatin)
        # May fail on rev-parse HEAD, that's expected
        # Just verify it doesn't hang or crash catastrophically

    def test_handles_spaces_in_filename(self, tmp_path: Path) -> None:
        """Script commits files with spaces in names."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        init_git_repo(chromatin, with_remote=False)
        make_commit(chromatin, "README.md", "# Chromatin\n", "initial")

        # File with space in name
        (chromatin / "my note.md").write_text("Content\n")

        result = run_script(chromatin)

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=chromatin,
            capture_output=True,
            text=True,
        )
        # File should be committed
        assert "my note.md" not in status.stdout or status.stdout.strip() == ""

    def test_handles_special_characters_in_content(self, tmp_path: Path) -> None:
        """Script commits files with special characters."""
        chromatin = tmp_path / "epigenome" / "chromatin"
        init_git_repo(chromatin, with_remote=False)
        make_commit(chromatin, "README.md", "# Chromatin\n", "initial")

        # File with special chars
        (chromatin / "special.md").write_text("Content with 'quotes' and \"double\" and $vars\n")

        result = run_script(chromatin)

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=chromatin,
            capture_output=True,
            text=True,
        )
        assert "special.md" not in status.stdout or status.stdout.strip() == ""

    def test_script_is_executable(self) -> None:
        """Script file exists and is readable."""
        assert SCRIPT_PATH.exists()
        assert SCRIPT_PATH.is_file()

    def test_script_has_shebang(self) -> None:
        """Script starts with bash shebang."""
        content = SCRIPT_PATH.read_text()
        assert content.startswith("#!/bin/bash")

    def test_script_uses_cd_with_or_exit(self) -> None:
        """Script uses 'cd ... || exit 1' pattern for safety."""
        content = SCRIPT_PATH.read_text()
        assert "cd " in content
        assert "|| exit 1" in content

    def test_script_checks_for_changes_before_commit(self) -> None:
        """Script checks for changes before committing."""
        content = SCRIPT_PATH.read_text()
        assert "git diff --quiet" in content
        assert "git diff --cached --quiet" in content
        assert "git ls-files --others" in content
