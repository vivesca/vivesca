from __future__ import annotations

"""Tests for metabolon/enzymes/sortase.py — dispatch coding tasks to cheap LLM backends."""


from dataclasses import dataclass
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fn():
    """Return the raw function behind the @tool decorator."""
    from metabolon.enzymes import sortase as mod

    return mod.sortase


def _make_execution_result(
    task_name: str = "test-task",
    tool: str = "goose",
    success: bool = True,
    duration_s: float = 1.5,
    fallbacks: list[str] | None = None,
) -> object:
    """Create a mock TaskExecutionResult."""
    from metabolon.sortase.executor import ExecutionAttempt

    @dataclass
    class MockResult:
        task_name: str
        tool: str
        success: bool
        attempts: list
        fallbacks: list[str]

    return MockResult(
        task_name=task_name,
        tool=tool,
        success=success,
        attempts=[ExecutionAttempt(tool=tool, exit_code=0, duration_s=duration_s, output="ok")],
        fallbacks=fallbacks or [],
    )


def _make_route_decision(tool: str = "goose", reason: str = "Default route") -> object:
    """Create a mock RouteDecision."""
    from metabolon.sortase.router import RouteDecision

    return RouteDecision(tool=tool, reason=reason)


def _make_validation_issue(severity: str = "warning", message: str = "Test issue") -> object:
    """Create a mock ValidationIssue."""
    from metabolon.sortase.validator import ValidationIssue

    return ValidationIssue(check="test", message=message, severity=severity)


# ---------------------------------------------------------------------------
# dispatch action tests
# ---------------------------------------------------------------------------


class TestDispatchValidation:
    """Tests for dispatch action input validation."""

    def test_missing_prompt_returns_error(self, tmp_path):
        fn = _fn()
        result = fn(action="dispatch", prompt="", project_dir=str(tmp_path))
        assert result.success is False
        assert "prompt" in result.message.lower()

    def test_missing_project_dir_returns_error(self):
        fn = _fn()
        result = fn(action="dispatch", prompt="do something", project_dir="")
        assert result.success is False
        assert "project_dir" in result.message.lower()

    def test_nonexistent_project_dir_returns_error(self):
        fn = _fn()
        result = fn(action="dispatch", prompt="do something", project_dir="/nonexistent/path")
        assert result.success is False
        assert "not a directory" in result.message.lower()


class TestDispatchSuccess:
    """Tests for successful dispatch execution."""

    def test_dispatch_returns_sortase_result(self, tmp_path):
        fn = _fn()
        with (
            patch("metabolon.sortase.decompose.TaskSpec"),
            patch("metabolon.sortase.executor.execute_tasks") as mock_exec,
            patch("metabolon.sortase.router.route_description") as mock_route,
            patch("metabolon.sortase.validator.validate_execution") as mock_validate,
            patch("metabolon.sortase.logger.append_log"),
            patch("subprocess.run") as mock_run,
        ):
            mock_route.return_value = _make_route_decision(tool="goose")
            mock_exec.return_value = [_make_execution_result()]
            mock_validate.return_value = []
            mock_run.return_value = MagicMock(stdout="", stderr="")

            result = fn(
                action="dispatch",
                prompt="write a hello world function",
                project_dir=str(tmp_path),
            )

            assert result.success is True
            assert "goose" in result.message.lower()
            assert len(result.tasks) == 1
            assert result.tasks[0]["name"] == "test-task"

    def test_dispatch_with_backend_override(self, tmp_path):
        fn = _fn()
        with (
            patch("metabolon.sortase.decompose.TaskSpec"),
            patch("metabolon.sortase.executor.execute_tasks") as mock_exec,
            patch("metabolon.sortase.router.route_description") as mock_route,
            patch("metabolon.sortase.validator.validate_execution") as mock_validate,
            patch("metabolon.sortase.logger.append_log"),
            patch("subprocess.run") as mock_run,
        ):
            mock_route.return_value = _make_route_decision(tool="codex", reason="Forced")
            mock_exec.return_value = [_make_execution_result(tool="codex")]
            mock_validate.return_value = []
            mock_run.return_value = MagicMock(stdout="", stderr="")

            result = fn(
                action="dispatch",
                prompt="write rust code",
                project_dir=str(tmp_path),
                backend="codex",
            )

            assert result.success is True
            # route_description should be called with forced_backend
            mock_route.assert_called_once()
            call_kwargs = mock_route.call_args[1]
            assert call_kwargs.get("forced_backend") == "codex"

    def test_dispatch_captures_files_changed(self, tmp_path):
        fn = _fn()
        with (
            patch("metabolon.sortase.decompose.TaskSpec"),
            patch("metabolon.sortase.executor.execute_tasks") as mock_exec,
            patch("metabolon.sortase.router.route_description") as mock_route,
            patch("metabolon.sortase.validator.validate_execution") as mock_validate,
            patch("metabolon.sortase.logger.append_log"),
            patch("subprocess.run") as mock_run,
        ):
            mock_route.return_value = _make_route_decision()
            mock_exec.return_value = [_make_execution_result()]
            mock_validate.return_value = []
            mock_run.return_value = MagicMock(stdout="main.py\nutils.py\n", stderr="")

            result = fn(
                action="dispatch",
                prompt="refactor code",
                project_dir=str(tmp_path),
            )

            assert result.files_changed == ["main.py", "utils.py"]

    def test_dispatch_captures_validation_issues(self, tmp_path):
        fn = _fn()
        with (
            patch("metabolon.sortase.decompose.TaskSpec"),
            patch("metabolon.sortase.executor.execute_tasks") as mock_exec,
            patch("metabolon.sortase.router.route_description") as mock_route,
            patch("metabolon.sortase.validator.validate_execution") as mock_validate,
            patch("metabolon.sortase.logger.append_log"),
            patch("subprocess.run") as mock_run,
        ):
            mock_route.return_value = _make_route_decision()
            mock_exec.return_value = [_make_execution_result()]
            mock_validate.return_value = [
                _make_validation_issue(severity="warning", message="Unused import")
            ]
            mock_run.return_value = MagicMock(stdout="", stderr="")

            result = fn(
                action="dispatch",
                prompt="add a feature",
                project_dir=str(tmp_path),
            )

            assert len(result.validation_issues) == 1
            assert result.validation_issues[0]["severity"] == "warning"

    def test_dispatch_logs_execution(self, tmp_path):
        fn = _fn()
        with (
            patch("metabolon.sortase.decompose.TaskSpec"),
            patch("metabolon.sortase.executor.execute_tasks") as mock_exec,
            patch("metabolon.sortase.router.route_description") as mock_route,
            patch("metabolon.sortase.validator.validate_execution") as mock_validate,
            patch("metabolon.sortase.logger.append_log") as mock_log,
            patch("subprocess.run") as mock_run,
        ):
            mock_route.return_value = _make_route_decision()
            mock_exec.return_value = [_make_execution_result()]
            mock_validate.return_value = []
            mock_run.return_value = MagicMock(stdout="", stderr="")

            fn(
                action="dispatch",
                prompt="write tests",
                project_dir=str(tmp_path),
            )

            mock_log.assert_called_once()
            entry = mock_log.call_args[0][0]
            assert entry["plan"] == "mcp-dispatch"
            assert entry["tasks"] == 1


# ---------------------------------------------------------------------------
# route action tests
# ---------------------------------------------------------------------------


class TestRouteAction:
    """Tests for route action."""

    def test_route_returns_route_result(self):
        fn = _fn()
        with patch("metabolon.sortase.router.route_description") as mock_route:
            mock_route.return_value = _make_route_decision(tool="gemini", reason="Algorithmic")

            result = fn(action="route", description="write an algorithm to sort numbers")

            assert result.tool == "gemini"
            assert "Algorithmic" in result.reason

    def test_route_uses_prompt_if_no_description(self):
        fn = _fn()
        with patch("metabolon.sortase.router.route_description") as mock_route:
            mock_route.return_value = _make_route_decision(tool="codex", reason="Rust")

            result = fn(action="route", prompt="refactor cargo crate")

            assert result.tool == "codex"
            mock_route.assert_called_once_with("refactor cargo crate")

    def test_route_no_input_returns_unknown(self):
        fn = _fn()
        result = fn(action="route", prompt="", description="")
        assert result.tool == "unknown"
        assert "no description" in result.reason.lower()


# ---------------------------------------------------------------------------
# status action tests
# ---------------------------------------------------------------------------


class TestStatusAction:
    """Tests for status action."""

    def test_status_returns_running_tasks(self):
        fn = _fn()
        with patch("metabolon.sortase.executor.list_running") as mock_list:
            mock_list.return_value = [
                {"task_name": "task-1", "tool": "goose", "project_dir": "/tmp/proj"},
                {"task_name": "task-2", "tool": "codex", "project_dir": "/tmp/other"},
            ]

            result = fn(action="status")

            assert result.success is True
            assert "2 running" in result.message
            assert len(result.tasks) == 2
            assert result.tasks[0]["name"] == "task-1"
            assert result.tasks[1]["name"] == "task-2"

    def test_status_empty_returns_zero(self):
        fn = _fn()
        with patch("metabolon.sortase.executor.list_running") as mock_list:
            mock_list.return_value = []

            result = fn(action="status")

            assert result.success is True
            assert "0 running" in result.message
            assert result.tasks == []


# ---------------------------------------------------------------------------
# stats action tests
# ---------------------------------------------------------------------------


class TestStatsAction:
    """Tests for stats action."""

    def test_stats_returns_stats_result(self):
        fn = _fn()
        with (
            patch("metabolon.sortase.logger.read_logs") as mock_read,
            patch("metabolon.sortase.logger.aggregate_stats") as mock_agg,
        ):
            mock_read.return_value = [
                {
                    "timestamp": "2025-01-01T12:00:00",
                    "plan": "p1",
                    "tool": "goose",
                    "success": True,
                },
                {
                    "timestamp": "2025-01-01T13:00:00",
                    "plan": "p2",
                    "tool": "codex",
                    "success": False,
                },
            ]
            mock_agg.return_value = {"per_tool": {"goose": 1, "codex": 1}}

            result = fn(action="stats")

            assert result.total_runs == 2
            assert "goose" in result.per_tool
            assert len(result.entries) == 2

    def test_stats_respects_last_n(self):
        fn = _fn()
        with (
            patch("metabolon.sortase.logger.read_logs") as mock_read,
            patch("metabolon.sortase.logger.aggregate_stats") as mock_agg,
        ):
            mock_read.return_value = [
                {
                    "timestamp": f"2025-01-0{i}T12:00:00",
                    "plan": f"p{i}",
                    "tool": "goose",
                    "success": True,
                }
                for i in range(1, 11)  # 10 entries
            ]
            mock_agg.return_value = {"per_tool": {"goose": 10}}

            result = fn(action="stats", last_n=3)

            assert result.total_runs == 10
            assert len(result.entries) == 3

    def test_stats_empty_logs_returns_empty_result(self):
        fn = _fn()
        with (
            patch("metabolon.sortase.logger.read_logs") as mock_read,
            patch("metabolon.sortase.logger.aggregate_stats"),
        ):
            mock_read.return_value = []

            result = fn(action="stats")

            assert result.total_runs == 0
            assert result.entries == []
            assert result.per_tool == {}


# ---------------------------------------------------------------------------
# unknown action tests
# ---------------------------------------------------------------------------


class TestUnknownAction:
    """Tests for unknown/invalid actions."""

    def test_unknown_action_returns_error(self):
        fn = _fn()
        result = fn(action="foobar")
        assert result.success is False
        assert "unknown action" in result.message.lower()
        assert "dispatch" in result.message.lower()


# ---------------------------------------------------------------------------
# result type tests
# ---------------------------------------------------------------------------


class TestResultTypes:
    """Verify correct return types for each action."""

    def test_dispatch_returns_sortase_result(self, tmp_path):
        from metabolon.enzymes.sortase import SortaseResult

        fn = _fn()
        with (
            patch("metabolon.sortase.decompose.TaskSpec"),
            patch("metabolon.sortase.executor.execute_tasks") as mock_exec,
            patch("metabolon.sortase.router.route_description") as mock_route,
            patch("metabolon.sortase.validator.validate_execution"),
            patch("metabolon.sortase.logger.append_log"),
            patch("subprocess.run") as mock_run,
        ):
            mock_route.return_value = _make_route_decision()
            mock_exec.return_value = [_make_execution_result()]
            mock_run.return_value = MagicMock(stdout="", stderr="")

            result = fn(action="dispatch", prompt="test", project_dir=str(tmp_path))
            assert isinstance(result, SortaseResult)

    def test_route_returns_route_result(self):
        from metabolon.enzymes.sortase import RouteResult

        fn = _fn()
        with patch("metabolon.sortase.router.route_description") as mock_route:
            mock_route.return_value = _make_route_decision()
            result = fn(action="route", description="test")
            assert isinstance(result, RouteResult)

    def test_stats_returns_stats_result(self):
        from metabolon.enzymes.sortase import StatsResult

        fn = _fn()
        with (
            patch("metabolon.sortase.logger.read_logs") as mock_read,
            patch("metabolon.sortase.logger.aggregate_stats"),
        ):
            mock_read.return_value = []
            result = fn(action="stats")
            assert isinstance(result, StatsResult)
