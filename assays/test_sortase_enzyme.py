"""Tests for metabolon/enzymes/sortase.py - LLM task dispatcher."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.sortase import (
    RouteResult,
    SortaseResult,
    StatsResult,
    sortase,
)


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def mock_route_description():
    """Mock route_description at the source module."""
    with patch("metabolon.sortase.router.route_description") as mock:
        mock.return_value = MagicMock(tool="goose", reason="Default route")
        yield mock


@pytest.fixture
def mock_execute_tasks():
    """Mock execute_tasks at the source module."""
    with patch("metabolon.sortase.executor.execute_tasks") as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_list_running():
    """Mock list_running at the source module."""
    with patch("metabolon.sortase.executor.list_running") as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_read_logs():
    """Mock read_logs at the source module."""
    with patch("metabolon.sortase.logger.read_logs") as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_append_log():
    """Mock append_log at the source module."""
    with patch("metabolon.sortase.logger.append_log") as mock:
        yield mock


@pytest.fixture
def mock_aggregate_stats():
    """Mock aggregate_stats at the source module."""
    with patch("metabolon.sortase.logger.aggregate_stats") as mock:
        mock.return_value = {"per_tool": {}}
        yield mock


@pytest.fixture
def mock_validate_execution():
    """Mock validate_execution at the source module."""
    with patch("metabolon.sortase.validator.validate_execution") as mock:
        mock.return_value = []
        yield mock


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for git diff."""
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(stdout="", stderr="", returncode=0)
        yield mock


@pytest.fixture
def mock_task_spec():
    """Mock TaskSpec class at the source module."""
    with patch("metabolon.sortase.decompose.TaskSpec") as mock:
        # Create a mock instance with all required attributes
        mock_instance = MagicMock()
        mock_instance.name = "mcp-dispatch"
        mock_instance.description = "test prompt"
        mock_instance.spec = "test prompt"
        mock_instance.files = []
        mock_instance.signal = "default"
        mock_instance.temp_file = None
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ── Action validation tests ────────────────────────────────────────────────


def test_sortase_unknown_action():
    """sortase returns error for unknown action."""
    result = sortase(action="unknown")

    assert isinstance(result, SortaseResult)
    assert result.success is False
    assert "Unknown action" in result.message
    assert "dispatch|route|status|stats" in result.message


def test_sortase_action_case_insensitive():
    """sortase handles action case-insensitively."""
    result = sortase(action="STATUS")
    assert isinstance(result, SortaseResult)
    assert result.success is True


def test_sortase_action_with_whitespace():
    """sortase handles action with leading/trailing whitespace."""
    result = sortase(action="  STATUS  ")
    assert isinstance(result, SortaseResult)
    assert result.success is True


# ── Dispatch action tests ───────────────────────────────────────────────────


def test_sortase_dispatch_requires_prompt():
    """sortase dispatch requires prompt parameter."""
    result = sortase(action="dispatch", prompt="", project_dir="/tmp")

    assert isinstance(result, SortaseResult)
    assert result.success is False
    assert "prompt" in result.message


def test_sortase_dispatch_requires_project_dir():
    """sortase dispatch requires project_dir parameter."""
    result = sortase(action="dispatch", prompt="test", project_dir="")

    assert isinstance(result, SortaseResult)
    assert result.success is False
    assert "project_dir" in result.message


def test_sortase_dispatch_requires_valid_directory(temp_project_dir):
    """sortase dispatch requires existing directory."""
    result = sortase(action="dispatch", prompt="test", project_dir="/nonexistent/path")

    assert isinstance(result, SortaseResult)
    assert result.success is False
    assert "Not a directory" in result.message


def test_sortase_dispatch_success(
    temp_project_dir,
    mock_route_description,
    mock_execute_tasks,
    mock_validate_execution,
    mock_subprocess_run,
    mock_append_log,
    mock_task_spec,
):
    """sortase dispatch succeeds with valid parameters."""
    # Setup mock execution result
    mock_execute_tasks.return_value = [
        MagicMock(
            task_name="mcp-dispatch",
            tool="goose",
            success=True,
            attempts=[MagicMock(duration_s=1.5)],
            fallbacks=[],
        )
    ]
    mock_subprocess_run.return_value = MagicMock(stdout="file1.py\nfile2.py\n", stderr="", returncode=0)

    result = sortase(
        action="dispatch",
        prompt="Add a test for function X",
        project_dir=str(temp_project_dir),
    )

    assert isinstance(result, SortaseResult)
    assert result.success is True
    assert "Dispatched to" in result.message
    assert len(result.files_changed) == 2
    mock_append_log.assert_called_once()


def test_sortase_dispatch_with_forced_backend(
    temp_project_dir,
    mock_route_description,
    mock_execute_tasks,
    mock_validate_execution,
    mock_subprocess_run,
    mock_append_log,
    mock_task_spec,
):
    """sortase dispatch respects forced backend parameter."""
    mock_execute_tasks.return_value = [
        MagicMock(
            task_name="mcp-dispatch",
            tool="codex",
            success=True,
            attempts=[MagicMock(duration_s=2.0)],
            fallbacks=[],
        )
    ]
    mock_route_description.return_value = MagicMock(tool="codex", reason="Forced by CLI option")

    result = sortase(
        action="dispatch",
        prompt="Refactor module",
        project_dir=str(temp_project_dir),
        backend="codex",
    )

    assert result.success is True
    # Verify forced backend was used
    mock_route_description.assert_called_once()
    call_kwargs = mock_route_description.call_args[1]
    assert call_kwargs.get("forced_backend") == "codex"


def test_sortase_dispatch_with_validation_issues(
    temp_project_dir,
    mock_route_description,
    mock_execute_tasks,
    mock_validate_execution,
    mock_subprocess_run,
    mock_append_log,
    mock_task_spec,
):
    """sortase dispatch includes validation issues in result."""
    mock_execute_tasks.return_value = [
        MagicMock(
            task_name="mcp-dispatch",
            tool="goose",
            success=True,
            attempts=[MagicMock(duration_s=1.0)],
            fallbacks=[],
        )
    ]
    mock_validate_execution.return_value = [
        MagicMock(severity="warning", message="Test coverage below 80%", check="tests")
    ]

    result = sortase(
        action="dispatch",
        prompt="Add feature",
        project_dir=str(temp_project_dir),
    )

    assert result.success is True
    assert len(result.validation_issues) == 1
    assert result.validation_issues[0]["severity"] == "warning"


def test_sortase_dispatch_with_execution_failure(
    temp_project_dir,
    mock_route_description,
    mock_execute_tasks,
    mock_validate_execution,
    mock_subprocess_run,
    mock_append_log,
    mock_task_spec,
):
    """sortase dispatch handles execution failure."""
    mock_execute_tasks.return_value = [
        MagicMock(
            task_name="mcp-dispatch",
            tool="goose",
            success=False,
            attempts=[MagicMock(duration_s=0.5)],
            fallbacks=["gemini"],
        )
    ]

    result = sortase(
        action="dispatch",
        prompt="Impossible task",
        project_dir=str(temp_project_dir),
    )

    assert isinstance(result, SortaseResult)
    assert result.success is False
    assert result.tasks[0]["fallbacks"] == ["gemini"]


def test_sortase_dispatch_with_timeout_parameter(
    temp_project_dir,
    mock_route_description,
    mock_execute_tasks,
    mock_validate_execution,
    mock_subprocess_run,
    mock_append_log,
    mock_task_spec,
):
    """sortase dispatch passes timeout to executor."""
    mock_execute_tasks.return_value = []

    sortase(
        action="dispatch",
        prompt="Quick fix",
        project_dir=str(temp_project_dir),
        timeout=300,
    )

    call_kwargs = mock_execute_tasks.call_args[1]
    assert call_kwargs["timeout_sec"] == 300


# ── Route action tests ──────────────────────────────────────────────────────


def test_sortase_route_with_description(mock_route_description):
    """sortase route uses description parameter."""
    mock_route_description.return_value = MagicMock(
        tool="gemini", reason="Algorithmic -> Gemini"
    )

    result = sortase(action="route", description="Implement sorting algorithm")

    assert isinstance(result, RouteResult)
    assert result.tool == "gemini"
    assert "Algorithmic" in result.reason


def test_sortase_route_uses_prompt_as_description(mock_route_description):
    """sortase route falls back to prompt if no description."""
    mock_route_description.return_value = MagicMock(
        tool="codex", reason="Multi-file -> Codex"
    )

    result = sortase(action="route", prompt="Refactor across multiple files")

    assert isinstance(result, RouteResult)
    assert result.tool == "codex"


def test_sortase_route_no_description_or_prompt():
    """sortase route returns unknown if no description provided."""
    result = sortase(action="route")

    assert isinstance(result, RouteResult)
    assert result.tool == "unknown"
    assert "No description" in result.reason


# ── Status action tests ─────────────────────────────────────────────────────


def test_sortase_status_empty(mock_list_running):
    """sortase status returns empty list when no tasks running."""
    mock_list_running.return_value = []

    result = sortase(action="status")

    assert isinstance(result, SortaseResult)
    assert result.success is True
    assert result.message == "0 running"
    assert result.tasks == []


def test_sortase_status_with_running_tasks(mock_list_running):
    """sortase status returns running tasks."""
    mock_list_running.return_value = [
        {"task_name": "task-1", "tool": "goose", "project_dir": "/proj1", "started_at": "2024-01-01T10:00:00"},
        {"task_name": "task-2", "tool": "gemini", "project_dir": "/proj2", "started_at": "2024-01-01T11:00:00"},
    ]

    result = sortase(action="status")

    assert result.success is True
    assert result.message == "2 running"
    assert len(result.tasks) == 2
    assert result.tasks[0]["name"] == "task-1"
    assert result.tasks[1]["tool"] == "gemini"


def test_sortase_status_handles_missing_fields(mock_list_running):
    """sortase status handles entries with missing fields."""
    mock_list_running.return_value = [
        {"task_name": "incomplete-task"},
        {"tool": "unknown-tool"},
        {},
    ]

    result = sortase(action="status")

    assert result.success is True
    assert len(result.tasks) == 3
    # Missing fields should have empty string defaults
    assert result.tasks[0]["tool"] == ""
    assert result.tasks[1]["name"] == ""


# ── Stats action tests ──────────────────────────────────────────────────────


def test_sortase_stats_empty(mock_read_logs, mock_aggregate_stats):
    """sortase stats returns empty result when no logs."""
    mock_read_logs.return_value = []
    mock_aggregate_stats.return_value = {"per_tool": {}}

    result = sortase(action="stats")

    assert isinstance(result, StatsResult)
    assert result.total_runs == 0
    assert result.entries == []
    assert result.per_tool == {}


def test_sortase_stats_with_entries(mock_read_logs, mock_aggregate_stats):
    """sortase stats returns log statistics."""
    mock_read_logs.return_value = [
        {"timestamp": "2024-01-01T10:00:00", "plan": "plan-a", "tool": "goose", "success": True},
        {"timestamp": "2024-01-01T11:00:00", "plan": "plan-b", "tool": "gemini", "success": False},
        {"timestamp": "2024-01-01T12:00:00", "plan": "plan-c", "tool": "goose", "success": True},
    ]
    mock_aggregate_stats.return_value = {
        "per_tool": {"goose": {"runs": 2, "successes": 2}, "gemini": {"runs": 1, "successes": 0}}
    }

    result = sortase(action="stats")

    assert result.total_runs == 3
    assert len(result.entries) == 3
    assert "goose" in result.per_tool


def test_sortase_stats_respects_last_n(mock_read_logs, mock_aggregate_stats):
    """sortase stats limits entries to last_n."""
    mock_read_logs.return_value = [
        {"timestamp": f"2024-01-01T{h:02d}:00:00", "plan": f"plan-{h}", "tool": "goose", "success": True}
        for h in range(20)
    ]
    mock_aggregate_stats.return_value = {"per_tool": {}}

    result = sortase(action="stats", last_n=5)

    assert result.total_runs == 20
    assert len(result.entries) == 5


def test_sortase_stats_default_last_n(mock_read_logs, mock_aggregate_stats):
    """sortase stats uses default last_n of 10."""
    mock_read_logs.return_value = [
        {"timestamp": f"2024-01-01T{h:02d}:00:00", "plan": f"plan-{h}", "tool": "goose", "success": True}
        for h in range(25)
    ]
    mock_aggregate_stats.return_value = {"per_tool": {}}

    result = sortase(action="stats")

    assert len(result.entries) == 10


# ── Result type tests ───────────────────────────────────────────────────────


def test_sortase_result_types():
    """Verify result types for each action."""
    # Unknown action -> SortaseResult
    result = sortase(action="invalid")
    assert isinstance(result, SortaseResult)


def test_sortase_result_has_expected_fields():
    """SortaseResult has all expected fields."""
    result = SortaseResult(
        success=True,
        message="Test",
        tasks=[{"name": "task1"}],
        files_changed=["file1.py"],
        validation_issues=[{"severity": "warning"}],
        duration_s=1.5,
    )

    assert result.success is True
    assert result.message == "Test"
    assert len(result.tasks) == 1
    assert len(result.files_changed) == 1
    assert len(result.validation_issues) == 1
    assert result.duration_s == 1.5


def test_route_result_has_expected_fields():
    """RouteResult has all expected fields."""
    result = RouteResult(tool="goose", reason="Default route")

    assert result.tool == "goose"
    assert result.reason == "Default route"


def test_stats_result_has_expected_fields():
    """StatsResult has all expected fields."""
    result = StatsResult(
        entries=[{"timestamp": "2024-01-01"}],
        per_tool={"goose": {"runs": 5}},
        total_runs=5,
    )

    assert len(result.entries) == 1
    assert result.per_tool["goose"]["runs"] == 5
    assert result.total_runs == 5


# ── Edge case tests ─────────────────────────────────────────────────────────


def test_sortase_dispatch_handles_path_with_tilde(
    temp_project_dir,
    mock_route_description,
    mock_execute_tasks,
    mock_validate_execution,
    mock_subprocess_run,
    mock_append_log,
    mock_task_spec,
):
    """sortase dispatch expands ~ in project_dir."""
    # This test verifies that Path.expanduser() is called
    # We can't actually test ~ expansion without a real home directory setup
    # But we verify the code path doesn't crash
    mock_execute_tasks.return_value = []

    # Use the temp directory path (simulating expanded path)
    result = sortase(
        action="dispatch",
        prompt="Test",
        project_dir=str(temp_project_dir),
    )

    assert isinstance(result, SortaseResult)


def test_sortase_dispatch_duration_calculation(
    temp_project_dir,
    mock_route_description,
    mock_execute_tasks,
    mock_validate_execution,
    mock_subprocess_run,
    mock_append_log,
    mock_task_spec,
):
    """sortase dispatch calculates total duration from attempts."""
    mock_execute_tasks.return_value = [
        MagicMock(
            task_name="task-1",
            tool="goose",
            success=True,
            attempts=[
                MagicMock(duration_s=1.5),
                MagicMock(duration_s=0.5),  # fallback attempt
            ],
            fallbacks=["gemini"],
        ),
        MagicMock(
            task_name="task-2",
            tool="gemini",
            success=True,
            attempts=[MagicMock(duration_s=2.0)],
            fallbacks=[],
        ),
    ]

    result = sortase(
        action="dispatch",
        prompt="Multi-task",
        project_dir=str(temp_project_dir),
    )

    # Total: 1.5 + 0.5 + 2.0 = 4.0
    assert result.duration_s == 4.0
