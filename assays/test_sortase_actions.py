"""Tests for sortase — dispatch coding tasks to cheap LLM backends.

Covers public API: SortaseResult, RouteResult, StatsResult, sortase().
Tests all four actions (dispatch, route, status, stats) plus unknown action,
with edge cases for empty/missing input.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.sortase import (
    RouteResult,
    SortaseResult,
    StatsResult,
    sortase,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_task_result(
    task_name: str = "mcp-dispatch",
    tool: str = "goose",
    success: bool = True,
    duration_s: float = 1.0,
    fallbacks: list[str] | None = None,
):
    """Build a lightweight TaskExecutionResult-like object."""
    attempt = MagicMock()
    attempt.duration_s = duration_s
    result = MagicMock()
    result.task_name = task_name
    result.tool = tool
    result.success = success
    result.attempts = [attempt]
    result.fallbacks = fallbacks or []
    return result


# ---------------------------------------------------------------------------
# SortaseResult / RouteResult / StatsResult — construction
# ---------------------------------------------------------------------------

class TestSortaseResult:
    def test_defaults(self):
        r = SortaseResult()
        assert r.success is True
        assert r.message == ""
        assert r.tasks == []
        assert r.files_changed == []
        assert r.validation_issues == []
        assert r.duration_s == 0.0

    def test_custom_fields(self):
        r = SortaseResult(
            success=False,
            message="boom",
            tasks=[{"name": "t1"}],
            files_changed=["a.py"],
            validation_issues=[{"severity": "error", "message": "bad"}],
            duration_s=3.14,
        )
        assert r.success is False
        assert r.message == "boom"
        assert len(r.tasks) == 1
        assert r.files_changed == ["a.py"]
        assert r.duration_s == 3.14

    def test_extra_fields_allowed(self):
        r = SortaseResult(success=True, custom="value")
        assert r.custom == "value"


class TestRouteResult:
    def test_fields(self):
        r = RouteResult(tool="codex", reason="Rust -> Codex")
        assert r.tool == "codex"
        assert r.reason == "Rust -> Codex"

    def test_extra_fields(self):
        r = RouteResult(tool="gemini", reason="algo", pattern=r"\balgo\b")
        assert r.pattern == r"\balgo\b"


class TestStatsResult:
    def test_defaults(self):
        s = StatsResult()
        assert s.entries == []
        assert s.per_tool == {}
        assert s.total_runs == 0

    def test_custom(self):
        s = StatsResult(
            entries=[{"plan": "p1"}],
            per_tool={"goose": {"runs": 5}},
            total_runs=5,
        )
        assert s.total_runs == 5
        assert len(s.entries) == 1


# ---------------------------------------------------------------------------
# sortase() — unknown action
# ---------------------------------------------------------------------------

class TestUnknownAction:
    def test_unknown_returns_error(self):
        result = sortase(action="fly")
        assert isinstance(result, SortaseResult)
        assert result.success is False
        assert "Unknown action" in result.message
        assert "fly" in result.message

    def test_action_case_insensitive(self):
        """Action is lowercased, so 'DISPATCH' still needs prompt+dir."""
        result = sortase(action="DISPATCH")
        assert isinstance(result, SortaseResult)
        assert result.success is False


# ---------------------------------------------------------------------------
# sortase() — dispatch action
# ---------------------------------------------------------------------------

class TestDispatchAction:

    def test_missing_prompt(self, tmp_path):
        result = sortase(action="dispatch", prompt="", project_dir=str(tmp_path))
        assert isinstance(result, SortaseResult)
        assert result.success is False
        assert "prompt" in result.message.lower() or "project_dir" in result.message.lower()

    def test_missing_project_dir(self):
        result = sortase(action="dispatch", prompt="do stuff", project_dir="")
        assert isinstance(result, SortaseResult)
        assert result.success is False

    def test_nonexistent_directory(self):
        result = sortase(action="dispatch", prompt="do stuff", project_dir="/no/such/dir")
        assert isinstance(result, SortaseResult)
        assert result.success is False
        assert "Not a directory" in result.message

    @patch("metabolon.enzymes.sortase.append_log")
    @patch("metabolon.sortase.validator.validate_execution", return_value=[])
    @patch("metabolon.sortase.executor.execute_tasks")
    @patch("metabolon.sortase.router.route_description")
    @patch("subprocess.run")
    def test_dispatch_success(
        self, mock_sp, mock_route, mock_exec, mock_validate, mock_log, tmp_path
    ):
        from metabolon.sortase.router import RouteDecision

        mock_route.return_value = RouteDecision(tool="goose", reason="Default route")
        task_result = _make_task_result(success=True)
        mock_exec.return_value = [task_result]
        mock_sp.return_value = MagicMock(stdout="", stderr="")

        result = sortase(
            action="dispatch",
            prompt="fix the bug",
            project_dir=str(tmp_path),
        )

        assert isinstance(result, SortaseResult)
        assert result.success is True
        assert "goose" in result.message
        assert len(result.tasks) == 1
        assert result.tasks[0]["name"] == "mcp-dispatch"
        mock_log.assert_called_once()
        log_entry = mock_log.call_args[0][0]
        assert log_entry["success"] is True

    @patch("metabolon.enzymes.sortase.append_log")
    @patch("metabolon.sortase.validator.validate_execution")
    @patch("metabolon.sortase.executor.execute_tasks")
    @patch("metabolon.sortase.router.route_description")
    @patch("subprocess.run")
    def test_dispatch_with_backend_override(
        self, mock_sp, mock_route, mock_exec, mock_validate, mock_log, tmp_path
    ):
        from metabolon.sortase.router import RouteDecision

        mock_route.return_value = RouteDecision(tool="codex", reason="Forced by CLI option")
        task_result = _make_task_result(tool="codex", success=True)
        mock_exec.return_value = [task_result]
        mock_sp.return_value = MagicMock(stdout="", stderr="")
        mock_validate.return_value = []

        result = sortase(
            action="dispatch",
            prompt="refactor rust crate",
            project_dir=str(tmp_path),
            backend="codex",
        )

        assert result.success is True
        # route_description should receive forced_backend="codex"
        mock_route.assert_called_with("refactor rust crate", forced_backend="codex")

    @patch("metabolon.enzymes.sortase.append_log")
    @patch("metabolon.sortase.validator.validate_execution")
    @patch("metabolon.sortase.executor.execute_tasks")
    @patch("metabolon.sortase.router.route_description")
    @patch("subprocess.run")
    def test_dispatch_failure_recorded(
        self, mock_sp, mock_route, mock_exec, mock_validate, mock_log, tmp_path
    ):
        from metabolon.sortase.router import RouteDecision

        mock_route.return_value = RouteDecision(tool="gemini", reason="algo")
        task_result = _make_task_result(success=False)
        mock_exec.return_value = [task_result]
        mock_sp.return_value = MagicMock(stdout="", stderr="")

        from metabolon.sortase.validator import ValidationIssue
        mock_validate.return_value = [
            ValidationIssue(check="tests", message="test failed", severity="error"),
        ]

        result = sortase(
            action="dispatch",
            prompt="do stuff",
            project_dir=str(tmp_path),
        )

        assert result.success is False
        assert len(result.validation_issues) == 1
        assert result.validation_issues[0]["severity"] == "error"
        log_entry = mock_log.call_args[0][0]
        assert log_entry["success"] is False
        assert log_entry["failure_reason"] == "test failed"

    @patch("metabolon.enzymes.sortase.append_log")
    @patch("metabolon.sortase.validator.validate_execution", return_value=[])
    @patch("metabolon.sortase.executor.execute_tasks")
    @patch("metabolon.sortase.router.route_description")
    @patch("subprocess.run")
    def test_dispatch_files_changed(
        self, mock_sp, mock_route, mock_exec, mock_validate, mock_log, tmp_path
    ):
        from metabolon.sortase.router import RouteDecision

        mock_route.return_value = RouteDecision(tool="goose", reason="Default route")
        mock_exec.return_value = [_make_task_result()]
        mock_sp.return_value = MagicMock(stdout="main.py\nutils.py\n", stderr="")
        mock_validate.return_value = []

        result = sortase(
            action="dispatch",
            prompt="update code",
            project_dir=str(tmp_path),
        )

        assert result.files_changed == ["main.py", "utils.py"]


# ---------------------------------------------------------------------------
# sortase() — route action
# ---------------------------------------------------------------------------

class TestRouteAction:

    @patch("metabolon.sortase.router.route_description")
    def test_route_with_description(self, mock_route):
        from metabolon.sortase.router import RouteDecision

        mock_route.return_value = RouteDecision(tool="codex", reason="Rust -> Codex (sandbox + DNS)")

        result = sortase(action="route", description="build a rust crate")

        assert isinstance(result, RouteResult)
        assert result.tool == "codex"
        assert "Rust" in result.reason

    @patch("metabolon.sortase.router.route_description")
    def test_route_falls_back_to_prompt(self, mock_route):
        from metabolon.sortase.router import RouteDecision

        mock_route.return_value = RouteDecision(tool="gemini", reason="Algorithmic")

        result = sortase(action="route", prompt="compute the algorithm")

        assert isinstance(result, RouteResult)
        assert result.tool == "gemini"
        mock_route.assert_called_with("compute the algorithm")

    def test_route_no_description_no_prompt(self):
        result = sortase(action="route")
        assert isinstance(result, RouteResult)
        assert result.tool == "unknown"
        assert "No description" in result.reason

    @patch("metabolon.sortase.router.route_description")
    def test_route_empty_strings(self, mock_route):
        result = sortase(action="route", description="", prompt="")
        assert isinstance(result, RouteResult)
        assert result.tool == "unknown"
        mock_route.assert_not_called()


# ---------------------------------------------------------------------------
# sortase() — status action
# ---------------------------------------------------------------------------

class TestStatusAction:

    @patch("metabolon.sortase.executor.list_running", return_value=[])
    def test_status_no_running(self, mock_list):
        result = sortase(action="status")
        assert isinstance(result, SortaseResult)
        assert result.success is True
        assert "0 running" in result.message
        assert result.tasks == []

    @patch("metabolon.sortase.executor.list_running")
    def test_status_with_running_tasks(self, mock_list):
        mock_list.return_value = [
            {"task_name": "task-a", "tool": "goose", "project_dir": "/proj", "started_at": "2025-01-01T00:00"},
            {"task_name": "task-b", "tool": "codex", "project_dir": "/other", "started_at": "2025-01-01T00:01"},
        ]

        result = sortase(action="status")

        assert isinstance(result, SortaseResult)
        assert result.success is True
        assert "2 running" in result.message
        assert len(result.tasks) == 2
        assert result.tasks[0]["name"] == "task-a"
        assert result.tasks[1]["tool"] == "codex"


# ---------------------------------------------------------------------------
# sortase() — stats action
# ---------------------------------------------------------------------------

class TestStatsAction:

    @patch("metabolon.sortase.logger.read_logs", return_value=[])
    def test_stats_empty(self, mock_read):
        result = sortase(action="stats")
        assert isinstance(result, StatsResult)
        assert result.entries == []
        assert result.per_tool == {}
        assert result.total_runs == 0

    @patch("metabolon.sortase.logger.aggregate_stats")
    @patch("metabolon.sortase.logger.read_logs")
    def test_stats_with_entries(self, mock_read, mock_agg):
        mock_read.return_value = [
            {"timestamp": "2025-01-01T10:00", "plan": "p1", "tool": "goose", "success": True},
            {"timestamp": "2025-01-01T11:00", "plan": "p2", "tool": "codex", "success": False},
            {"timestamp": "2025-01-01T12:00", "plan": "p3", "tool": "gemini", "success": True},
        ]
        mock_agg.return_value = {
            "per_tool": {"goose": {"runs": 1}, "codex": {"runs": 1}},
            "total_runs": 3,
        }

        result = sortase(action="stats")

        assert isinstance(result, StatsResult)
        assert result.total_runs == 3
        assert len(result.entries) == 3
        assert result.entries[-1]["tool"] == "gemini"

    @patch("metabolon.sortase.logger.aggregate_stats")
    @patch("metabolon.sortase.logger.read_logs")
    def test_stats_last_n_limits_output(self, mock_read, mock_agg):
        entries = [
            {"timestamp": f"2025-01-01T{i:02d}:00", "plan": f"p{i}", "tool": "goose", "success": True}
            for i in range(20)
        ]
        mock_read.return_value = entries
        mock_agg.return_value = {"per_tool": {}, "total_runs": 20}

        result = sortase(action="stats", last_n=5)

        assert len(result.entries) == 5
        assert result.total_runs == 20

    @patch("metabolon.sortase.logger.aggregate_stats")
    @patch("metabolon.sortase.logger.read_logs")
    def test_stats_missing_fields_get_defaults(self, mock_read, mock_agg):
        mock_read.return_value = [{"tool": "goose"}]
        mock_agg.return_value = {"per_tool": {"goose": {"runs": 1}}, "total_runs": 1}

        result = sortase(action="stats")

        assert len(result.entries) == 1
        entry = result.entries[0]
        assert entry["timestamp"] == ""
        assert entry["plan"] == ""
        assert entry["success"] is False  # default from .get("success", False)
