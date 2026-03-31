from __future__ import annotations

"""Tests for chromatin-backup.sh — git auto-commit and push for chromatin vault."""

import subprocess
from pathlib import Path


SCRIPT_PATH = Path("/home/terry/germline/effectors/chromatin-backup.sh")


def run_script(home_dir: Path) -> subprocess.CompletedProcess:
    """Run chromatin-backup.sh with HOME pointing to home_dir.

    The script does: cd "$HOME/epigenome/chromatin"
    """
    return subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        env={"HOME": str(home_dir)},
        cwd="/tmp",
    )


def init_chromatin_repo(home_dir: Path) -> Path:
    """Create epigenome/chromatin under home_dir and init git repo.

    Returns the path to the chromatin repo.
    """
    chromatin = home_dir / "epigenome" / "chromatin"
    chromatin.mkdir(parents=True, exist_ok=True)

    subprocess.run(["git", "init"], cwd=chromatin, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=chromatin, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=chromatin, capture_output=True, check=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=chromatin, capture_output=True, check=True)

    return chromatin


def make_commit(repo_path: Path, filename: str, content: str, msg: str = "initial") -> None:
    """Create a commit with a file."""
    (repo_path / filename).write_text(content)
    subprocess.run(["git", "add", filename], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=repo_path, capture_output=True, check=True)


def get_commit_count(repo_path: Path) -> int:
    """Get the number of commits in the repo."""
    result = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    return int(result.stdout.strip()) if result.returncode == 0 else 0


def get_last_commit_message(repo_path: Path) -> str:
    """Get the last commit message."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%s"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def is_working_tree_clean(repo_path: Path) -> bool:
    """Check if the working tree has no changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() == ""


class TestChromatinBackupBasics:
    """Basic functionality tests for chromatin-backup.sh."""

    def test_exits_1_if_chromatin_dir_missing(self, tmp_path: Path) -> None:
        """Script exits with 1 when chromatin directory doesn't exist."""
        # tmp_path has no 'epigenome/chromatin' subdir
        result = run_script(tmp_path)
        assert result.returncode == 1

    def test_exits_0_when_no_changes(self, tmp_path: Path) -> None:
        """Script exits 0 and makes no commit when repo is clean."""
        chromatin = init_chromatin_repo(tmp_path)
        make_commit(chromatin, "README.md", "# Chromatin\n")

        # Clean repo — no changes
        result = run_script(tmp_path)
        assert result.returncode == 0

    def test_commits_new_file(self, tmp_path: Path) -> None:
        """Script adds and commits new untracked files."""
        chromatin = init_chromatin_repo(tmp_path)
        make_commit(chromatin, "README.md", "# Chromatin\n")

        count_before = get_commit_count(chromatin)

        # Add an untracked file
        (chromatin / "new_note.md").write_text("New content\n")

        # Run the script
        result = run_script(tmp_path)

        # File should be committed
        assert is_working_tree_clean(chromatin)
        assert get_commit_count(chromatin) == count_before + 1

    def test_commits_modified_file(self, tmp_path: Path) -> None:
        """Script commits modified tracked files."""
        chromatin = init_chromatin_repo(tmp_path)
        make_commit(chromatin, "note.md", "Original content\n")

        count_before = get_commit_count(chromatin)

        # Modify the file
        (chromatin / "note.md").write_text("Modified content\n")

        result = run_script(tmp_path)

        # Modification should be committed
        assert is_working_tree_clean(chromatin)
        assert get_commit_count(chromatin) == count_before + 1

    def test_commits_staged_changes(self, tmp_path: Path) -> None:
        """Script commits already staged changes."""
        chromatin = init_chromatin_repo(tmp_path)
        make_commit(chromatin, "note.md", "Original\n")

        count_before = get_commit_count(chromatin)

        # Stage a modification
        (chromatin / "note.md").write_text("Staged\n")
        subprocess.run(["git", "add", "note.md"], cwd=chromatin, capture_output=True, check=True)

        result = run_script(tmp_path)

        assert is_working_tree_clean(chromatin)
        assert get_commit_count(chromatin) == count_before + 1

    def test_commit_message_format(self, tmp_path: Path) -> None:
        """Commit message follows 'chromatin backup: YYYY-MM-DD HH:MM:SS' format."""
        chromatin = init_chromatin_repo(tmp_path)
        make_commit(chromatin, "README.md", "# Chromatin\n")

        # Add a file to trigger commit
        (chromatin / "new.md").write_text("New\n")

        result = run_script(tmp_path)

        msg = get_last_commit_message(chromatin)
        assert msg.startswith("chromatin backup: ")
        # Should have timestamp format: YYYY-MM-DD HH:MM:SS
        timestamp = msg.replace("chromatin backup: ", "")
        parts = timestamp.split()
        assert len(parts) == 2  # date and time
        assert "-" in parts[0]  # date has dashes
        assert ":" in parts[1]  # time has colons

    def test_commits_multiple_files_together(self, tmp_path: Path) -> None:
        """Script commits all changes in one commit."""
        chromatin = init_chromatin_repo(tmp_path)
        make_commit(chromatin, "README.md", "# Chromatin\n")

        count_before = get_commit_count(chromatin)

        # Add multiple files
        (chromatin / "note1.md").write_text("Note 1\n")
        (chromatin / "note2.md").write_text("Note 2\n")
        (chromatin / "subdir").mkdir(exist_ok=True)
        (chromatin / "subdir" / "note3.md").write_text("Note 3\n")

        result = run_script(tmp_path)

        # All files should be committed in one commit
        assert is_working_tree_clean(chromatin)
        assert get_commit_count(chromatin) == count_before + 1

    def test_skips_commit_when_only_ignored_files(self, tmp_path: Path) -> None:
        """Script skips commit when only ignored files are changed."""
        chromatin = init_chromatin_repo(tmp_path)
        make_commit(chromatin, "README.md", "# Chromatin\n")

        # Add gitignore
        (chromatin / ".gitignore").write_text("*.tmp\n")
        subprocess.run(["git", "add", ".gitignore"], cwd=chromatin, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "add gitignore"], cwd=chromatin, capture_output=True, check=True)

        count_before = get_commit_count(chromatin)

        # Create ignored file
        (chromatin / "scratch.tmp").write_text("temp\n")

        result = run_script(tmp_path)

        # Should exit 0 (no changes to commit)
        assert result.returncode == 0
        # No new commit
        assert get_commit_count(chromatin) == count_before


class TestChromatinBackupEdgeCases:
    """Edge case tests for chromatin-backup.sh."""

    def test_handles_spaces_in_filename(self, tmp_path: Path) -> None:
        """Script commits files with spaces in names."""
        chromatin = init_chromatin_repo(tmp_path)
        make_commit(chromatin, "README.md", "# Chromatin\n")

        # File with space in name
        (chromatin / "my note.md").write_text("Content\n")

        result = run_script(tmp_path)

        assert is_working_tree_clean(chromatin)

    def test_handles_special_characters_in_content(self, tmp_path: Path) -> None:
        """Script commits files with special characters."""
        chromatin = init_chromatin_repo(tmp_path)
        make_commit(chromatin, "README.md", "# Chromatin\n")

        # File with special chars
        (chromatin / "special.md").write_text("Content with 'quotes' and \"double\" and $vars\n")

        result = run_script(tmp_path)

        assert is_working_tree_clean(chromatin)

    def test_handles_deleted_file(self, tmp_path: Path) -> None:
        """Script commits deleted files."""
        chromatin = init_chromatin_repo(tmp_path)
        make_commit(chromatin, "to_delete.md", "Will be deleted\n")

        # Delete the file
        (chromatin / "to_delete.md").unlink()

        result = run_script(tmp_path)

        assert is_working_tree_clean(chromatin)

    def test_empty_directory_ignored(self, tmp_path: Path) -> None:
        """Script doesn't fail with empty directories."""
        chromatin = init_chromatin_repo(tmp_path)
        make_commit(chromatin, "README.md", "# Chromatin\n")

        # Create empty directory
        (chromatin / "emptydir").mkdir()

        result = run_script(tmp_path)

        # Should succeed, no commit made (empty dirs not tracked)
        assert result.returncode == 0
        assert is_working_tree_clean(chromatin)


class TestChromatinBackupScriptIntegrity:
    """Tests for script structure and safety patterns."""

    def test_script_exists(self) -> None:
        """Script file exists."""
        assert SCRIPT_PATH.exists()
        assert SCRIPT_PATH.is_file()

    def test_script_has_bash_shebang(self) -> None:
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

    def test_script_uses_git_add_a(self) -> None:
        """Script uses git add -A to stage all changes."""
        content = SCRIPT_PATH.read_text()
        assert "git add -A" in content

    def test_script_commits_with_timestamp(self) -> None:
        """Script commits with timestamp in message."""
        content = SCRIPT_PATH.read_text()
        assert "chromatin backup:" in content
        assert "date" in content

    def test_script_pushes_to_origin_main(self) -> None:
        """Script pushes to origin main."""
        content = SCRIPT_PATH.read_text()
        assert "git push origin main" in content

    def test_script_fetches_before_push(self) -> None:
        """Script fetches from origin main before making changes."""
        content = SCRIPT_PATH.read_text()
        assert "git fetch origin main" in content

    def test_script_has_rebase_fallback(self) -> None:
        """Script has fallback logic for rebase failures."""
        content = SCRIPT_PATH.read_text()
        assert "git rebase" in content
        assert "git merge" in content
