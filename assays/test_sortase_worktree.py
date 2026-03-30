"""Tests for sortase worktree support in executor and CLI."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from metabolon.sortase.executor import (
    _create_worktree,
    _merge_worktree,
    _remove_worktree,
    execute_task,
    execute_tasks,
)
from metabolon.sortase.decompose import TaskSpec


# ── helpers ──────────────────────────────────────────────────


def _init_git_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo with one committed file."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path, capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, capture_output=True, check=True,
    )
    readme = tmp_path / "README.md"
    readme.write_text("initial\n")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path, capture_output=True, check=True,
    )
    return tmp_path


# ── _create_worktree ────────────────────────────────────────


def test_create_worktree_creates_directory(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree_path = _create_worktree(repo, "task-alpha")
    assert worktree_path.exists()
    assert worktree_path.is_dir()
    assert (worktree_path / ".git").exists()
    # Clean up
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(worktree_path)],
        cwd=repo, capture_output=True,
    )


def test_create_worktree_has_committed_files(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree_path = _create_worktree(repo, "task-beta")
    readme = worktree_path / "README.md"
    assert readme.exists()
    assert readme.read_text() == "initial\n"
    # Clean up
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(worktree_path)],
        cwd=repo, capture_output=True,
    )


# ── _merge_worktree ─────────────────────────────────────────


def test_merge_worktree_merges_changes(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree_path = _create_worktree(repo, "task-gamma")

    # Make a change in the worktree
    readme = worktree_path / "README.md"
    readme.write_text("changed by worktree\n")
    subprocess.run(["git", "add", "-A"], cwd=worktree_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "worktree change"],
        cwd=worktree_path, capture_output=True, check=True,
    )

    success, detail = _merge_worktree(repo, worktree_path)
    assert success is True
    # Verify the change landed in the main repo
    assert (repo / "README.md").read_text() == "changed by worktree\n"


def test_merge_worktree_no_changes(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree_path = _create_worktree(repo, "task-delta")

    success, detail = _merge_worktree(repo, worktree_path)
    assert success is True
    assert detail == "no changes"


# ── _remove_worktree ────────────────────────────────────────


def test_remove_worktree_cleans_up(tmp_path: Path):
    repo = _init_git_repo(tmp_path)
    worktree_path = _create_worktree(repo, "task-epsilon")

    # Find the branch name before removal
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=repo, capture_output=True, text=True,
    )
    branch = None
    found_path = False
    resolved_wt = str(worktree_path.resolve())
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            found_path = Path(line[len("worktree "):]).resolve() == Path(resolved_wt)
        if found_path and line.startswith("branch refs/heads/"):
            branch = line[len("branch refs/heads/"):]
            break
    assert branch is not None

    _remove_worktree(repo, worktree_path, branch)

    assert not worktree_path.exists()
    # Branch should be gone
    branches = subprocess.run(
        ["git", "branch", "--list", branch],
        cwd=repo, capture_output=True, text=True,
    )
    assert branches.stdout.strip() == ""


# ── CLI --worktree flag ────────────────────────────────────


def test_worktree_flag_exists_in_cli():
    """The exec command should accept a --worktree flag without error."""
    from metabolon.sortase.cli import main

    runner = CliRunner()
    # Use --help to confirm the flag is accepted — no real execution needed
    result = runner.invoke(main, ["exec", "--help"])
    assert result.exit_code == 0
    assert "--worktree" in result.output


# ── execute_tasks with worktree=True (serial path) ─────────


@pytest.mark.asyncio
async def test_execute_tasks_serial_worktree(tmp_path: Path):
    """Serial execution with worktree=True should create, run in, and merge a worktree."""
    repo = _init_git_repo(tmp_path)

    task = TaskSpec(
        name="test-task",
        description="a test task",
        spec="echo hello",
        files=["README.md"],
        temp_file=None,
    )

    mock_attempt = MagicMock()
    mock_attempt.exit_code = 0
    mock_attempt.failure_reason = None
    mock_attempt.output = "hello"
    mock_attempt.duration_s = 1.0
    mock_attempt.cost_estimate = "$0.00 (flat-rate)"

    with patch(
        "metabolon.sortase.executor._run_command",
        new_callable=AsyncMock,
        return_value=mock_attempt,
    ) as mock_run:
        with patch("metabolon.sortase.executor._emit_completion_signal"):
            with patch("metabolon.sortase.executor._analyze_for_coaching"):
                results = await execute_tasks(
                    tasks=[task],
                    project_dir=repo,
                    tool_by_task={"test-task": "goose"},
                    serial=True,
                    worktree=True,
                )

    assert len(results) == 1
    assert results[0].success is True
    # _run_command should have been called with the worktree directory, not the repo
    call_args = mock_run.call_args
    called_project_dir = call_args[0][1]  # second positional arg
    assert called_project_dir != repo
    assert called_project_dir.exists() is False  # worktree should be cleaned up after merge


# ── execute_tasks with worktree=False (serial, default) ────


@pytest.mark.asyncio
async def test_execute_tasks_serial_no_worktree(tmp_path: Path):
    """Serial execution without worktree should run directly in project_dir."""
    repo = _init_git_repo(tmp_path)

    task = TaskSpec(
        name="test-task",
        description="a test task",
        spec="echo hello",
        files=["README.md"],
        temp_file=None,
    )

    mock_attempt = MagicMock()
    mock_attempt.exit_code = 0
    mock_attempt.failure_reason = None
    mock_attempt.output = "hello"
    mock_attempt.duration_s = 1.0
    mock_attempt.cost_estimate = "$0.00 (flat-rate)"

    with patch(
        "metabolon.sortase.executor._run_command",
        new_callable=AsyncMock,
        return_value=mock_attempt,
    ) as mock_run:
        with patch("metabolon.sortase.executor._emit_completion_signal"):
            with patch("metabolon.sortase.executor._analyze_for_coaching"):
                results = await execute_tasks(
                    tasks=[task],
                    project_dir=repo,
                    tool_by_task={"test-task": "goose"},
                    serial=True,
                    worktree=False,
                )

    assert len(results) == 1
    assert results[0].success is True
    # Should have been called with the original project_dir
    call_args = mock_run.call_args
    called_project_dir = call_args[0][1]
    assert called_project_dir == repo


# ── execute_tasks worktree cleanup on failure ──────────────


@pytest.mark.asyncio
async def test_execute_tasks_worktree_failure_cleans_up(tmp_path: Path):
    """If the task fails in worktree mode, the worktree should be removed (not merged)."""
    repo = _init_git_repo(tmp_path)

    task = TaskSpec(
        name="fail-task",
        description="a failing task",
        spec="do something bad",
        files=["README.md"],
        temp_file=None,
    )

    mock_attempt = MagicMock()
    mock_attempt.exit_code = 1
    mock_attempt.failure_reason = "process-error"
    mock_attempt.output = "error occurred"
    mock_attempt.duration_s = 0.5
    mock_attempt.cost_estimate = "$0.00 (flat-rate)"

    with patch(
        "metabolon.sortase.executor._run_command",
        new_callable=AsyncMock,
        return_value=mock_attempt,
    ):
        with patch("metabolon.sortase.executor._emit_completion_signal"):
            with patch("metabolon.sortase.executor._analyze_for_coaching"):
                results = await execute_tasks(
                    tasks=[task],
                    project_dir=repo,
                    tool_by_task={"fail-task": "goose"},
                    serial=True,
                    worktree=True,
                )

    assert len(results) == 1
    assert results[0].success is False
    # Verify no leftover worktrees
    wt_list = subprocess.run(
        ["git", "worktree", "list"],
        cwd=repo, capture_output=True, text=True,
    )
    # Should only have the main worktree
    lines = [l for l in wt_list.stdout.splitlines() if l.strip()]
    assert len(lines) == 1
