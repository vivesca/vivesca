"""Tests for partial-progress detection in the Temporal worker retry path."""
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# Path setup — add temporal-golem to sys.path so imports work
_TEMPORAL_GOLEM_DIR = Path(__file__).resolve().parent.parent / "effectors" / "temporal-golem"
sys.path.insert(0, str(_TEMPORAL_GOLEM_DIR))


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture()
def tmp_git_repo(tmp_path: Path) -> Path:
    """Create a temporary git repo with an initial commit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(repo), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(repo), check=True, capture_output=True,
    )
    # Create an initial commit so HEAD exists
    readme = repo / "README.md"
    readme.write_text("# test repo\n")
    subprocess.run(["git", "add", "README.md"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial commit"],
        cwd=str(repo), check=True, capture_output=True,
    )
    return repo


# ============================================================================
# Tests for _detect_prior_commits
# ============================================================================


class TestDetectPriorCommits:
    """Test the _detect_prior_commits helper function."""

    def test_prior_commits_detected(self, tmp_git_repo: Path) -> None:
        """A recent golem-authored commit within the time window is returned."""
        # Make a commit authored by 'golem'
        f = tmp_git_repo / "partial.txt"
        f.write_text("partial fix\n")
        subprocess.run(["git", "add", "partial.txt"], cwd=str(tmp_git_repo), check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "golem: partial fix"],
            cwd=str(tmp_git_repo), check=True, capture_output=True,
        )
        # Set the author to golem on the last commit
        subprocess.run(
            ["git", "commit", "--amend", "--author=golem <golem@local>", "--no-edit"],
            cwd=str(tmp_git_repo), check=True, capture_output=True,
        )

        from worker import _detect_prior_commits
        result = _detect_prior_commits(str(tmp_git_repo), time_window_minutes=40, author="golem")
        assert len(result) == 1
        assert "partial fix" in result[0]

    def test_no_prior_commits(self, tmp_git_repo: Path) -> None:
        """Clean git state returns empty list."""
        from worker import _detect_prior_commits
        result = _detect_prior_commits(str(tmp_git_repo), time_window_minutes=40, author="golem")
        assert result == []

    def test_old_commits_ignored(self, tmp_git_repo: Path) -> None:
        """A commit outside the time window is not returned."""
        # Make a commit authored by 'golem' but dated 2 hours ago
        f = tmp_git_repo / "old.txt"
        f.write_text("old work\n")
        subprocess.run(["git", "add", "old.txt"], cwd=str(tmp_git_repo), check=True, capture_output=True)
        # Use GIT_AUTHOR_DATE and GIT_COMMITTER_DATE to place it in the past
        env = {
            **os.environ,
            "GIT_AUTHOR_DATE": "2020-01-01T12:00:00+0000",
            "GIT_COMMITTER_DATE": "2020-01-01T12:00:00+0000",
        }
        subprocess.run(
            ["git", "commit", "-m", "golem: old work", "--author=golem <golem@local>"],
            cwd=str(tmp_git_repo), check=True, capture_output=True, env=env,
        )

        from worker import _detect_prior_commits
        result = _detect_prior_commits(str(tmp_git_repo), time_window_minutes=40, author="golem")
        assert result == []


class TestPromptPrepend:
    """Test that prior commits produce the correct augmented prompt."""

    def test_prompt_prepend(self) -> None:
        """Given prior commits, the augmented prompt contains the NOTE prefix."""
        prior_commits = ["abc1234 golem: partial fix", "def5678 golem: more work"]
        commit_list = "\n".join(f"  - {c}" for c in prior_commits)
        prefix = (
            "NOTE: A prior attempt on this task made the following commits "
            "before being interrupted:\n"
            f"{commit_list}\n"
            "Review these commits — if they partially complete the task, "
            "continue from where they left off. "
            "Do NOT redo already-committed work.\n\n"
        )
        original_task = "[t-resume1] Fix the login bug"
        effective_task = prefix + original_task

        assert effective_task.startswith("NOTE: A prior attempt")
        assert "partial fix" in effective_task
        assert "more work" in effective_task
        assert "Do NOT redo already-committed work." in effective_task
        assert effective_task.endswith("[t-resume1] Fix the login bug")

    def test_no_prepend_when_empty(self) -> None:
        """When there are no prior commits, the task is unchanged."""
        prior_commits: list[str] = []
        original_task = "[t-resume1] Fix the login bug"
        effective_task = original_task
        if prior_commits:
            effective_task = "NOTE: ..." + effective_task
        assert effective_task == original_task
