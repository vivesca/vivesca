from __future__ import annotations

"""Tests for metabolon/enzymes/sortase.py — supplementary coverage.

Covers: temp-file lifecycle, event-loop threading path, log-entry shape,
dispatch cleanup on exception, stats edge cases, route priority, and
default field values.
"""


import asyncio
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from metabolon.enzymes.sortase import (
    RouteResult,
    SortaseResult,
    StatsResult,
    sortase,
)

# ── Helpers & Fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def proj_dir():
    """Temporary project directory."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


def _mock_task(name="mcp-dispatch", tool="goose", success=True, durations=None, fallbacks=None):
    """Create a mock execute-result."""
    d = durations or [1.0]
    return MagicMock(
        task_name=name,
        tool=tool,
        success=success,
        attempts=[MagicMock(duration_s=dur) for dur in d],
        fallbacks=fallbacks or [],
    )


@pytest.fixture
def full_dispatch_mocks(proj_dir):
    """Bundle all mocks needed for dispatch action, return a namespace dict."""
    with (
        patch("metabolon.sortase.router.route_description") as m_route,
        patch("metabolon.sortase.executor.execute_tasks") as m_exec,
        patch("metabolon.sortase.validator.validate_execution") as m_val,
        patch("subprocess.run") as m_sp,
        patch("metabolon.sortase.logger.append_log") as m_log,
        patch("metabolon.sortase.decompose.TaskSpec") as m_spec,
    ):
        m_route.return_value = MagicMock(tool="goose", reason="default")
        m_exec.return_value = [_mock_task()]
        m_val.return_value = []
        m_sp.return_value = MagicMock(stdout="", stderr="", returncode=0)
        _ts = MagicMock()
        _ts.name = "mcp-dispatch"
        _ts.description = "mcp-dispatch"
        _ts.spec = ""
        _ts.files = []
        _ts.signal = "default"
        _ts.temp_file = ""
        m_spec.return_value = _ts
        yield {
            "route": m_route,
            "exec": m_exec,
            "val": m_val,
            "sp": m_sp,
            "log": m_log,
            "spec": m_spec,
            "proj_dir": proj_dir,
        }


# ── Temp file lifecycle ───────────────────────────────────────────────────


def test_dispatch_creates_and_removes_temp_file(full_dispatch_mocks):
    """Dispatch writes a temp spec file and removes it afterwards."""
    m = full_dispatch_mocks
    sortase(action="dispatch", prompt="hello world", project_dir=str(m["proj_dir"]))

    # The temp file should have been cleaned up — verify by checking write_text was
    # called on a path inside /tmp.  We patch Path.write_text to observe it.
    # Instead, check the temp file doesn't linger.
    tmp_path = Path(tempfile.gettempdir()) / "sortase-mcp-dispatch.txt"
    assert not tmp_path.exists(), "Temp spec file should be cleaned up after dispatch"


def test_dispatch_cleanup_temp_file_on_exception(full_dispatch_mocks):
    """Temp file is cleaned up even when execute_tasks raises."""
    m = full_dispatch_mocks
    m["exec"].side_effect = RuntimeError("boom")

    with pytest.raises(RuntimeError):
        sortase(action="dispatch", prompt="will crash", project_dir=str(m["proj_dir"]))

    tmp_path = Path(tempfile.gettempdir()) / "sortase-mcp-dispatch.txt"
    assert not tmp_path.exists(), "Temp file must be removed in finally block"


# ── Log entry shape ───────────────────────────────────────────────────────


def test_dispatch_log_entry_fields(full_dispatch_mocks):
    """append_log receives a dict with expected keys."""
    m = full_dispatch_mocks
    m["exec"].return_value = [_mock_task(durations=[2.5])]
    m["sp"].return_value = MagicMock(stdout="a.py\n", stderr="", returncode=0)

    sortase(action="dispatch", prompt="do stuff", project_dir=str(m["proj_dir"]))

    m["log"].assert_called_once()
    entry = m["log"].call_args[0][0]

    expected_keys = {
        "timestamp",
        "plan",
        "project",
        "tasks",
        "tool",
        "fallbacks",
        "duration_s",
        "success",
        "failure_reason",
        "files_changed",
        "tests_passed",
    }
    assert set(entry.keys()) == expected_keys
    assert entry["plan"] == "mcp-dispatch"
    assert entry["tasks"] == 1
    assert entry["duration_s"] == 2.5
    assert entry["files_changed"] == 1
    assert entry["success"] is True


def test_dispatch_log_failure_reason(full_dispatch_mocks):
    """Log entry captures first error-level validation issue."""
    m = full_dispatch_mocks
    m["val"].return_value = [
        MagicMock(severity="warning", message="low coverage", check="tests"),
        MagicMock(severity="error", message="syntax error in foo.py", check="syntax"),
    ]

    sortase(action="dispatch", prompt="bad code", project_dir=str(m["proj_dir"]))

    entry = m["log"].call_args[0][0]
    assert entry["failure_reason"] == "syntax error in foo.py"


def test_dispatch_log_tests_passed_flag(full_dispatch_mocks):
    """Log entry sets tests_passed=0 when validation finds test issues."""
    m = full_dispatch_mocks
    m["val"].return_value = [
        MagicMock(severity="error", message="test failures", check="tests"),
    ]

    sortase(action="dispatch", prompt="flaky", project_dir=str(m["proj_dir"]))

    entry = m["log"].call_args[0][0]
    assert entry["tests_passed"] == 0


# ── Event-loop / threading path ───────────────────────────────────────────


def test_dispatch_inside_running_event_loop(full_dispatch_mocks):
    """Dispatch uses a background thread when a running event loop exists."""
    m = full_dispatch_mocks

    async def _inner():
        # We are inside a running loop — sortase should spawn a thread.
        result = sortase(action="dispatch", prompt="async test", project_dir=str(m["proj_dir"]))
        return result

    result = asyncio.run(_inner())
    assert isinstance(result, SortaseResult)
    assert result.success is True
    m["exec"].assert_called_once()


# ── Git diff invocation ───────────────────────────────────────────────────


def test_dispatch_git_diff_cwd(full_dispatch_mocks):
    """Dispatch runs git diff with cwd set to the project directory."""
    m = full_dispatch_mocks

    sortase(action="dispatch", prompt="check git", project_dir=str(m["proj_dir"]))

    m["sp"].assert_called_once()
    cmd_args = m["sp"].call_args
    assert cmd_args[0][0][:3] == ["git", "diff", "--name-only"]
    assert cmd_args[1]["cwd"] == m["proj_dir"]


def test_dispatch_git_diff_filters_blank_lines(full_dispatch_mocks):
    """Blank lines in git diff output are filtered out."""
    m = full_dispatch_mocks
    m["sp"].return_value = MagicMock(stdout="a.py\n\nb.py\n  \n", stderr="", returncode=0)

    result = sortase(action="dispatch", prompt="files", project_dir=str(m["proj_dir"]))

    assert result.files_changed == ["a.py", "b.py"]


# ── Route priority ────────────────────────────────────────────────────────


def test_route_description_takes_priority_over_prompt():
    """When both description and prompt given, description wins."""
    with patch("metabolon.sortase.router.route_description") as m_route:
        m_route.return_value = MagicMock(tool="codex", reason="desc wins")
        result = sortase(action="route", description="desc text", prompt="prompt text")
        assert result.tool == "codex"
        # route_description should be called with desc text
        m_route.assert_called_once_with("desc text")


def test_route_falls_back_to_prompt():
    """When only prompt is given, route uses prompt."""
    with patch("metabolon.sortase.router.route_description") as m_route:
        m_route.return_value = MagicMock(tool="goose", reason="prompt fallback")
        result = sortase(action="route", prompt="prompt text")
        assert result.tool == "goose"
        m_route.assert_called_once_with("prompt text")


# ── Stats edge cases ──────────────────────────────────────────────────────


def test_stats_last_n_larger_than_entries():
    """last_n greater than total logs returns all entries."""
    with (
        patch("metabolon.sortase.logger.read_logs") as m_read,
        patch("metabolon.sortase.logger.aggregate_stats") as m_agg,
    ):
        m_read.return_value = [
            {"timestamp": "2025-01-01", "plan": "a", "tool": "goose", "success": True},
            {"timestamp": "2025-01-02", "plan": "b", "tool": "codex", "success": False},
        ]
        m_agg.return_value = {"per_tool": {}}

        result = sortase(action="stats", last_n=100)
        assert result.total_runs == 2
        assert len(result.entries) == 2


def test_stats_last_n_zero_returns_all():
    """last_n=0 — Python slice entries[-0:] == entries[:] — returns all."""
    with (
        patch("metabolon.sortase.logger.read_logs") as m_read,
        patch("metabolon.sortase.logger.aggregate_stats") as m_agg,
    ):
        m_read.return_value = [
            {"timestamp": "2025-01-01", "plan": "a", "tool": "goose", "success": True},
            {"timestamp": "2025-01-02", "plan": "b", "tool": "codex", "success": False},
        ]
        m_agg.return_value = {"per_tool": {"goose": {"runs": 1}}}

        result = sortase(action="stats", last_n=0)
        assert result.total_runs == 2
        assert len(result.entries) == 2  # -0 slice returns everything


def test_stats_entries_have_expected_keys():
    """Each stats entry has timestamp, plan, tool, success."""
    with (
        patch("metabolon.sortase.logger.read_logs") as m_read,
        patch("metabolon.sortase.logger.aggregate_stats") as m_agg,
    ):
        m_read.return_value = [
            {"timestamp": "2025-01-01", "plan": "a", "tool": "goose", "success": True},
        ]
        m_agg.return_value = {"per_tool": {}}

        result = sortase(action="stats")
        entry = result.entries[0]
        assert "timestamp" in entry
        assert "plan" in entry
        assert "tool" in entry
        assert "success" in entry


# ── Dispatch validation integration ───────────────────────────────────────


def test_dispatch_validation_issues_shape(full_dispatch_mocks):
    """Validation issues in result are dicts with severity and message."""
    m = full_dispatch_mocks
    m["val"].return_value = [
        MagicMock(severity="error", message="import error", check="imports"),
        MagicMock(severity="warning", message="lint", check="lint"),
    ]

    result = sortase(action="dispatch", prompt="validate", project_dir=str(m["proj_dir"]))

    assert len(result.validation_issues) == 2
    for issue in result.validation_issues:
        assert "severity" in issue
        assert "message" in issue


def test_dispatch_with_multiple_results(full_dispatch_mocks):
    """Dispatch correctly aggregates multiple execute results."""
    m = full_dispatch_mocks
    m["exec"].return_value = [
        _mock_task(name="t1", durations=[1.0]),
        _mock_task(name="t2", durations=[2.0, 0.5], success=False, fallbacks=["gemini"]),
    ]

    result = sortase(action="dispatch", prompt="multi", project_dir=str(m["proj_dir"]))

    assert result.success is False  # one failed
    assert len(result.tasks) == 2
    assert result.tasks[0]["duration_s"] == 1.0
    assert result.tasks[1]["duration_s"] == 2.5
    assert result.tasks[1]["fallbacks"] == ["gemini"]


def test_dispatch_project_name_in_log(full_dispatch_mocks):
    """Log entry captures the project directory basename."""
    m = full_dispatch_mocks
    sortase(action="dispatch", prompt="name check", project_dir=str(m["proj_dir"]))

    entry = m["log"].call_args[0][0]
    assert entry["project"] == m["proj_dir"].name


# ── Default field values ──────────────────────────────────────────────────


def test_sortase_result_defaults():
    """SortaseResult defaults: success=True, empty lists, duration=0."""
    r = SortaseResult()
    assert r.success is True
    assert r.message == ""
    assert r.tasks == []
    assert r.files_changed == []
    assert r.validation_issues == []
    assert r.duration_s == 0.0


def test_route_result_defaults():
    """RouteResult requires tool and reason."""
    r = RouteResult(tool="x", reason="y")
    assert r.tool == "x"
    assert r.reason == "y"


def test_stats_result_defaults():
    """StatsResult defaults: empty lists/dicts, total_runs=0."""
    r = StatsResult()
    assert r.entries == []
    assert r.per_tool == {}
    assert r.total_runs == 0


# ── Action dispatch with empty execute results ────────────────────────────


def test_dispatch_empty_results(full_dispatch_mocks):
    """Dispatch with no results from executor succeeds (vacuously true)."""
    m = full_dispatch_mocks
    m["exec"].return_value = []

    result = sortase(action="dispatch", prompt="nothing", project_dir=str(m["proj_dir"]))

    assert result.success is True
    assert result.tasks == []
    assert result.duration_s == 0.0


# ── Dispatch input validation ─────────────────────────────────────────────


def test_dispatch_missing_prompt():
    """Dispatch without prompt returns failure."""
    result = sortase(action="dispatch", project_dir="/tmp")
    assert result.success is False
    assert "prompt" in result.message.lower() or "project_dir" in result.message.lower()


def test_dispatch_missing_project_dir():
    """Dispatch without project_dir returns failure."""
    result = sortase(action="dispatch", prompt="do something")
    assert result.success is False
    assert "prompt" in result.message.lower() or "project_dir" in result.message.lower()


def test_dispatch_nonexistent_project_dir():
    """Dispatch with a non-existent directory returns failure."""
    result = sortase(action="dispatch", prompt="task", project_dir="/no/such/dir/abc123")
    assert result.success is False
    assert "Not a directory" in result.message


def test_dispatch_forced_backend(full_dispatch_mocks):
    """Dispatch passes forced backend through to route_description."""
    m = full_dispatch_mocks
    sortase(action="dispatch", prompt="task", project_dir=str(m["proj_dir"]), backend="codex")

    m["route"].assert_called_once()
    call_kwargs = m["route"].call_args
    assert (
        call_kwargs[1].get("forced_backend") == "codex"
        or (len(call_kwargs[0]) > 1 and call_kwargs[0][1] == "codex")
        or call_kwargs == call(m["route"].call_args[0][0], forced_backend="codex")
    )


def test_dispatch_backend_empty_string_uses_none(full_dispatch_mocks):
    """Empty backend string is treated as None (no forcing)."""
    m = full_dispatch_mocks
    sortase(action="dispatch", prompt="task", project_dir=str(m["proj_dir"]), backend="")

    # forced_backend should be None when backend is empty
    call_kwargs = m["route"].call_args
    kw = call_kwargs[1] if call_kwargs[1] else {}
    assert kw.get("forced_backend") is None or "forced_backend" not in kw


# ── Route: no input ────────────────────────────────────────────────────────


def test_route_no_description_no_prompt():
    """Route with neither description nor prompt returns unknown."""
    result = sortase(action="route")
    assert result.tool == "unknown"
    assert "no description" in result.reason.lower()


# ── Status action ──────────────────────────────────────────────────────────


def test_status_returns_running_entries():
    """Status action returns entries from list_running."""
    with patch("metabolon.sortase.executor.list_running") as m_list:
        m_list.return_value = [
            {"task_name": "t1", "tool": "goose", "project_dir": "/x", "started_at": "12:00"},
            {"task_name": "t2", "tool": "codex", "project_dir": "/y", "started_at": "12:01"},
        ]
        result = sortase(action="status")
        assert isinstance(result, SortaseResult)
        assert result.success is True
        assert result.message == "2 running"
        assert len(result.tasks) == 2
        assert result.tasks[0]["name"] == "t1"
        assert result.tasks[1]["tool"] == "codex"


def test_status_empty():
    """Status with no running tasks."""
    with patch("metabolon.sortase.executor.list_running") as m_list:
        m_list.return_value = []
        result = sortase(action="status")
        assert result.success is True
        assert result.message == "0 running"
        assert result.tasks == []


# ── Stats: empty logs ─────────────────────────────────────────────────────


def test_stats_empty_logs():
    """Stats with no log entries returns zeroes."""
    with patch("metabolon.sortase.logger.read_logs") as m_read:
        m_read.return_value = []
        result = sortase(action="stats")
        assert isinstance(result, StatsResult)
        assert result.total_runs == 0
        assert result.entries == []
        assert result.per_tool == {}


# ── Unknown action ─────────────────────────────────────────────────────────


def test_enzymes_sortase_unknown_action():
    """Unknown action returns failure with valid-action list."""
    result = sortase(action="foobar")
    assert isinstance(result, SortaseResult)
    assert result.success is False
    assert "Unknown action" in result.message
    assert "dispatch" in result.message


# ── Action case insensitivity ──────────────────────────────────────────────


def test_enzymes_sortase_action_case_insensitive():
    """Action is case-insensitive."""
    with patch("metabolon.sortase.executor.list_running") as m_list:
        m_list.return_value = []
        result = sortase(action="STATUS")
        assert result.success is True

    with patch("metabolon.sortase.router.route_description") as m_route:
        m_route.return_value = MagicMock(tool="goose", reason="ok")
        result = sortase(action="Route", description="test")
        assert result.tool == "goose"
