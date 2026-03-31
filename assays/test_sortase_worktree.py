from __future__ import annotations

"""Tests for sortase worktree support in executor and CLI."""

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


# ── _merge_worktree conflict detection ─────────────────────


def test_merge_worktree_conflict_both_sides_modified(tmp_path: Path):
    """If main and worktree branch both modify the same file, abort with conflict warning."""
    repo = _init_git_repo(tmp_path)
    worktree_path = _create_worktree(repo, "task-conflict")

    # Modify file in worktree branch
    readme_wt = worktree_path / "README.md"
    readme_wt.write_text("changed by worktree\n")
    subprocess.run(["git", "add", "-A"], cwd=worktree_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "worktree change"],
        cwd=worktree_path, capture_output=True, check=True,
    )

    # Modify the same file on main branch
    readme_main = repo / "README.md"
    readme_main.write_text("changed by main\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "main change"],
        cwd=repo, capture_output=True, check=True,
    )

    success, detail = _merge_worktree(repo, worktree_path)
    assert success is False
    assert "conflict" in detail.lower()
    assert "README.md" in detail
    # Main branch content should be preserved (not overwritten)
    assert readme_main.read_text() == "changed by main\n"


def test_merge_worktree_different_files_no_conflict(tmp_path: Path):
    """If worktree and main modified different files, merge should succeed."""
    repo = _init_git_repo(tmp_path)
    worktree_path = _create_worktree(repo, "task-noconflict")

    # Modify README in worktree
    readme_wt = worktree_path / "README.md"
    readme_wt.write_text("changed by worktree\n")
    subprocess.run(["git", "add", "-A"], cwd=worktree_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "worktree change"],
        cwd=worktree_path, capture_output=True, check=True,
    )

    # Add a NEW file on main (not modifying README)
    new_file = repo / "main_only.txt"
    new_file.write_text("main addition\n")
    subprocess.run(["git", "add", "-A"], cwd=repo, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "main new file"],
        cwd=repo, capture_output=True, check=True,
    )

    success, detail = _merge_worktree(repo, worktree_path)
    assert success is True
    assert (repo / "README.md").read_text() == "changed by worktree\n"
    assert (repo / "main_only.txt").read_text() == "main addition\n"


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


# ── clean command ───────────────────────────────────────────


from metabolon.sortase.cli import clean_command, main as sortase_main


def test_clean_no_stale(tmp_path: Path) -> None:
    """Fresh repo with no sortase worktrees → reports 0 stale."""
    repo = _init_git_repo(tmp_path)
    runner = CliRunner()
    result = runner.invoke(sortase_main, ["clean", "-p", str(repo)])
    assert result.exit_code == 0
    assert "0 stale" in result.output


def test_clean_dry_run_shows_but_preserves(tmp_path: Path) -> None:
    """Dry run should report stale branches but not delete them."""
    repo = _init_git_repo(tmp_path)

    # Create a sortase/* branch (without a real worktree — just the branch)
    subprocess.run(
        ["git", "branch", "sortase/test-task-abc123"],
        cwd=repo, capture_output=True, check=True,
    )

    # Create a worktree for it via _create_worktree so git knows about it
    worktree_path = _create_worktree(repo, "test-task-xyz789")

    runner = CliRunner()
    result = runner.invoke(sortase_main, ["clean", "-p", str(repo), "--dry-run"])
    assert result.exit_code == 0
    assert "would remove" in result.output

    # Verify branches still exist (dry-run must not delete)
    branches = subprocess.run(
        ["git", "branch", "--list", "sortase/*"],
        cwd=repo, capture_output=True, text=True,
    )
    branch_lines = [l.strip() for l in branches.stdout.splitlines() if l.strip()]
    assert len(branch_lines) >= 1, f"Branches should still exist after dry-run, got: {branch_lines}"

    # Verify worktree still exists
    assert worktree_path.exists(), "Worktree directory should still exist after dry-run"

    # Cleanup
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(worktree_path)],
        cwd=repo, capture_output=True,
    )


def test_clean_removes_stale_worktree(tmp_path: Path) -> None:
    """Clean should remove a sortase worktree, directory, and branch."""
    repo = _init_git_repo(tmp_path)
    worktree_path = _create_worktree(repo, "test-task-cleanup")

    # Confirm the branch exists
    branches_before = subprocess.run(
        ["git", "branch", "--list", "sortase/*"],
        cwd=repo, capture_output=True, text=True,
    )
    assert "sortase/test-task-cleanup" in branches_before.stdout

    runner = CliRunner()
    result = runner.invoke(sortase_main, ["clean", "-p", str(repo)])
    assert result.exit_code == 0
    assert "removed" in result.output
    assert "sortase/test-task-cleanup" in result.output

    # Worktree directory should be gone
    assert not worktree_path.exists()

    # Branch should be gone
    branches_after = subprocess.run(
        ["git", "branch", "--list", "sortase/*"],
        cwd=repo, capture_output=True, text=True,
    )
    assert branches_after.stdout.strip() == ""


def test_clean_prunes_missing_worktree_directory(tmp_path: Path) -> None:
    """If worktree directory is deleted but git still tracks it, clean should prune."""
    repo = _init_git_repo(tmp_path)
    worktree_path = _create_worktree(repo, "test-task-missing")

    # Manually delete the worktree directory (simulating external removal)
    import shutil
    shutil.rmtree(worktree_path, ignore_errors=True)
    assert not worktree_path.exists()

    runner = CliRunner()
    result = runner.invoke(sortase_main, ["clean", "-p", str(repo)])
    assert result.exit_code == 0
    assert "pruned" in result.output
    assert "sortase/test-task-missing" in result.output

    # Branch should be gone
    branches_after = subprocess.run(
        ["git", "branch", "--list", "sortase/*"],
        cwd=repo, capture_output=True, text=True,
    )
    assert branches_after.stdout.strip() == ""
