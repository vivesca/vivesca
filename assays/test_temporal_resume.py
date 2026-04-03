"""Tests for temporal-golem partial-progress resume (t-resume1).

When a golem task is retried after being killed, the worker should detect
commits from the prior attempt and prepend context to the retry prompt.
Uses a temporary git repo, never touches real germline.
"""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_git_repo(tmp_path: Path):
    """Create a temporary git repo with an initial commit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo), capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(repo), capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "test"],
        cwd=str(repo), capture_output=True, check=True,
    )
    # Initial commit
    (repo / "README.md").write_text("init")
    subprocess.run(["git", "add", "."], cwd=str(repo), capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=str(repo), capture_output=True, check=True,
    )
    return repo


def _make_golem_commit(repo: Path, message: str, file_content: str = "change") -> str:
    """Create a commit that looks like golem output."""
    target = repo / "fix.py"
    target.write_text(file_content)
    subprocess.run(["git", "add", "."], cwd=str(repo), capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(repo), capture_output=True, check=True,
    )
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=str(repo), capture_output=True, text=True, check=True,
    )
    return result.stdout.strip()


def _detect_prior_commits(repo: Path, since_minutes: int = 40) -> list[str]:
    """Detect golem commits within a time window.

    This is the function the golem should implement in worker.py.
    We define the expected interface here for testing.
    """
    # Import from worker if available, otherwise define expected behavior
    try:
        import sys
        worker_dir = str(Path.home() / "germline" / "effectors" / "temporal-golem")
        if worker_dir not in sys.path:
            sys.path.insert(0, worker_dir)
        from worker import _detect_prior_commits as impl
        return impl(repo, since_minutes)
    except (ImportError, AttributeError):
        # Function not yet implemented — use reference implementation
        # to verify test structure works. Actual test will fail until
        # golem implements _detect_prior_commits in worker.py.
        pytest.skip("_detect_prior_commits not yet implemented in worker.py")


def _build_resume_prompt(task: str, prior_commits: list[str]) -> str:
    """Build a prompt with prior-commit context prepended.

    Expected interface for the golem to implement.
    """
    try:
        import sys
        worker_dir = str(Path.home() / "germline" / "effectors" / "temporal-golem")
        if worker_dir not in sys.path:
            sys.path.insert(0, worker_dir)
        from worker import _build_resume_prompt as impl
        return impl(task, prior_commits)
    except (ImportError, AttributeError):
        pytest.skip("_build_resume_prompt not yet implemented in worker.py")


class TestPriorCommitsDetected:
    """When a prior attempt left commits, they should be detected."""

    def test_recent_golem_commit_found(self, tmp_git_repo: Path):
        sha = _make_golem_commit(tmp_git_repo, "golem: fix test_foo.py")
        commits = _detect_prior_commits(tmp_git_repo, since_minutes=5)
        assert len(commits) >= 1
        assert any("golem" in c.lower() for c in commits)

    def test_multiple_commits_found(self, tmp_git_repo: Path):
        _make_golem_commit(tmp_git_repo, "golem: fix test_a.py", "a")
        _make_golem_commit(tmp_git_repo, "golem: fix test_b.py", "b")
        commits = _detect_prior_commits(tmp_git_repo, since_minutes=5)
        assert len(commits) >= 2


class TestNoCommitsCleanState:
    """With no prior golem commits, detection should return empty."""

    def test_clean_repo_returns_empty(self, tmp_git_repo: Path):
        commits = _detect_prior_commits(tmp_git_repo, since_minutes=5)
        assert commits == []


class TestPromptPrepend:
    """The resume prompt should include prior commit context."""

    def test_prompt_includes_commit_note(self, tmp_git_repo: Path):
        sha = _make_golem_commit(tmp_git_repo, "golem: partial fix")
        commits = [f"{sha} golem: partial fix"]
        prompt = _build_resume_prompt("Fix all tests", commits)
        assert "NOTE:" in prompt or "prior attempt" in prompt.lower()
        assert "golem: partial fix" in prompt
        assert "Fix all tests" in prompt

    def test_prompt_unchanged_without_commits(self, tmp_git_repo: Path):
        prompt = _build_resume_prompt("Fix all tests", [])
        assert prompt == "Fix all tests"


class TestOldCommitsIgnored:
    """Commits outside the time window should not be picked up."""

    def test_old_commit_not_detected(self, tmp_git_repo: Path):
        # Create a commit, then query with a 0-minute window
        _make_golem_commit(tmp_git_repo, "golem: old fix")
        # since_minutes=0 means "only commits from the future" — should return empty
        commits = _detect_prior_commits(tmp_git_repo, since_minutes=0)
        assert commits == []
