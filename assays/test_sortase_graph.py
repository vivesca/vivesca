"""Tests for metabolon.sortase.graph — LangGraph executor for plan-based agent orchestration."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from langgraph.checkpoint.memory import MemorySaver
from metabolon.sortase.decompose import TaskSpec
from metabolon.sortase.executor import FallbackStep, TaskExecutionResult
from metabolon.sortase.graph import (
    CHECKPOINT_DB,
    SortaseState,
    _open_checkpointer,
    build_graph,
    decompose,
    execute,
    log_results,
    review_and_continue,
    route,
    run,
    validate,
)

# ═══════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def task_spec_a():
    return TaskSpec(
        name="add-auth",
        description="Add authentication middleware for Rust API",
        spec="Implement JWT auth in the Axum server",
        files=["src/auth.rs"],
        signal="rust",
        prerequisite=None,
        temp_file=None,
    )


@pytest.fixture
def task_spec_b():
    return TaskSpec(
        name="fix-overflow",
        description="Fix integer overflow in calculate function",
        spec="Use checked arithmetic in calculate()",
        files=["src/math.rs"],
        signal="algorithmic",
        prerequisite=None,
        temp_file=None,
    )


@pytest.fixture
def sample_task_specs(task_spec_a, task_spec_b):
    """TaskSpec objects — what decompose_plan actually returns."""
    return [task_spec_a, task_spec_b]


@pytest.fixture
def sample_task_dicts(sample_task_specs):
    """Serialized TaskSpec dicts — what the graph stores in state['tasks']."""
    return [asdict(t) for t in sample_task_specs]


@pytest.fixture
def initial_state() -> SortaseState:
    return {
        "plan_file": "/tmp/test-plan.yaml",
        "project_dir": "/tmp/test-project",
        "serial": False,
        "backend": "",
        "test_command": "",
        "timeout": 600,
        "tasks": [],
        "task_count": 0,
        "tool_by_task": {},
        "route_decisions": [],
        "results": [],
        "executed": False,
        "validation_issues": [],
        "changed_files": [],
        "success": False,
        "log_entry": {},
        "errors": [],
    }


@pytest.fixture
def routed_state(initial_state, sample_task_dicts):
    s = dict(initial_state)
    s["tasks"] = sample_task_dicts
    s["task_count"] = 2
    s["tool_by_task"] = {"add-auth": "codex", "fix-overflow": "gemini"}
    s["route_decisions"] = [
        {"task": "add-auth", "tool": "codex", "reason": "Rust -> Codex"},
        {"task": "fix-overflow", "tool": "gemini", "reason": "Algorithmic -> Gemini"},
    ]
    return s


@pytest.fixture
def executed_state(routed_state):
    s = dict(routed_state)
    s["results"] = [
        {
            "task_name": "add-auth", "tool": "codex", "success": True,
            "output": "Auth module created successfully",
            "fallbacks": [], "fallback_chain": [],
            "prompt_file": None, "cost_estimate": "$0.0125",
        },
        {
            "task_name": "fix-overflow", "tool": "gemini", "success": True,
            "output": "Fixed integer overflow",
            "fallbacks": ["goose"],
            "fallback_chain": [FallbackStep(tool="goose", succeeded=False, failure_reason="quota")],
            "prompt_file": None, "cost_estimate": "$0.00 (flat-rate)",
        },
    ]
    s["executed"] = True
    return s


def _fake_result(task_name="t1", tool="codex", success=True, output="ok", **kw):
    return TaskExecutionResult(
        task_name=task_name, tool=tool, prompt_file=kw.get("prompt_file"),
        success=success, output=output,
        fallbacks=kw.get("fallbacks", []),
        fallback_chain=kw.get("fallback_chain", []),
        cost_estimate=kw.get("cost_estimate", ""),
    )


# ═══════════════════════════════════════════════════════════════
# decompose node
# ═══════════════════════════════════════════════════════════════


class TestDecomposeNode:

    @patch("metabolon.sortase.graph.decompose_plan")
    def test_success(self, mock_dp, initial_state, sample_task_specs):
        mock_dp.return_value = sample_task_specs
        r = decompose(initial_state)
        assert r["task_count"] == 2
        assert r["tasks"][0]["name"] == "add-auth"
        assert len(r.get("errors", [])) == 0

    @patch("metabolon.sortase.graph.decompose_plan")
    def test_empty_plan(self, mock_dp, initial_state):
        mock_dp.return_value = []
        r = decompose(initial_state)
        assert r["tasks"] == []
        assert r["task_count"] == 0

    @patch("metabolon.sortase.graph.decompose_plan")
    def test_exception_caught(self, mock_dp, initial_state):
        mock_dp.side_effect = FileNotFoundError("gone")
        r = decompose(initial_state)
        assert r["task_count"] == 0
        assert any("Decompose failed" in e for e in r["errors"])

    @patch("metabolon.sortase.graph.decompose_plan")
    def test_all_spec_fields_serialized(self, mock_dp, initial_state):
        ts = TaskSpec(
            name="x", description="d", spec="s", files=["f.py"],
            signal="default", prerequisite="other", temp_file="/tmp/x.txt",
        )
        mock_dp.return_value = [ts]
        r = decompose(initial_state)
        assert r["tasks"][0]["prerequisite"] == "other"
        assert r["tasks"][0]["temp_file"] == "/tmp/x.txt"


# ═══════════════════════════════════════════════════════════════
# route node
# ═══════════════════════════════════════════════════════════════


class TestRouteNode:

    @patch("metabolon.sortase.graph.route_description")
    def test_auto_route(self, mock_rd, initial_state, sample_task_dicts):
        state = dict(initial_state); state["tasks"] = sample_task_dicts; state["backend"] = ""
        from metabolon.sortase.router import RouteDecision
        mock_rd.side_effect = [
            RouteDecision(tool="codex", reason="Rust"),
            RouteDecision(tool="gemini", reason="Algo"),
        ]
        r = route(state)
        assert r["tool_by_task"]["add-auth"] == "codex"
        assert len(r["route_decisions"]) == 2

    @patch("metabolon.sortase.graph.route_description")
    def test_forced_backend(self, mock_rd, initial_state, sample_task_dicts):
        state = dict(initial_state); state["tasks"] = sample_task_dicts; state["backend"] = "goose"
        from metabolon.sortase.router import RouteDecision
        mock_rd.return_value = RouteDecision(tool="goose", reason="Forced")
        r = route(state)
        assert all(v == "goose" for v in r["tool_by_task"].values())

    @patch("metabolon.sortase.graph.route_description")
    def test_empty_tasks(self, mock_rd, initial_state):
        r = route(initial_state)
        assert r["tool_by_task"] == {}
        mock_rd.assert_not_called()

    @patch("metabolon.sortase.graph.route_description")
    def test_single_task(self, mock_rd, initial_state):
        state = dict(initial_state)
        state["tasks"] = [{"name": "solo", "description": "d", "spec": "s", "files": []}]
        state["backend"] = ""
        from metabolon.sortase.router import RouteDecision
        mock_rd.return_value = RouteDecision(tool="goose", reason="Default")
        r = route(state)
        assert r["route_decisions"][0]["task"] == "solo"

    @patch("metabolon.sortase.graph.route_description")
    def test_falsy_backend_treated_as_auto(self, mock_rd, initial_state, sample_task_dicts):
        from metabolon.sortase.router import RouteDecision
        mock_rd.return_value = RouteDecision(tool="goose", reason="Default")
        for bv in ("", None):
            state = dict(initial_state); state["tasks"] = sample_task_dicts; state["backend"] = bv
            r = route(state)
            assert r["tool_by_task"]["add-auth"] == "goose"

    @patch("metabolon.sortase.graph.route_description")
    def test_missing_description_defaults_to_empty(self, mock_rd, initial_state):
        state = dict(initial_state)
        state["tasks"] = [{"name": "m", "spec": "s", "files": []}]
        state["backend"] = ""
        from metabolon.sortase.router import RouteDecision
        mock_rd.return_value = RouteDecision(tool="goose", reason="Default")
        route(state)
        mock_rd.assert_called_once_with("", forced_backend=None)


# ═══════════════════════════════════════════════════════════════
# execute node
# ═══════════════════════════════════════════════════════════════


class TestExecuteNode:

    @patch("metabolon.sortase.graph.asyncio")
    def test_no_tasks(self, mock_aio, initial_state):
        r = execute(initial_state)
        assert r["executed"] is True
        assert r["results"] == []
        assert "No tasks to execute" in r["errors"]

    @patch("metabolon.sortase.graph.asyncio")
    def test_success(self, mock_aio, routed_state):
        mock_aio.run.return_value = [
            _fake_result("add-auth", "codex", cost_estimate="$0.01"),
            _fake_result("fix-overflow", "gemini", fallbacks=["goose"],
                         fallback_chain=[FallbackStep(tool="goose", succeeded=False, failure_reason="quota")],
                         cost_estimate="$0.00 (flat-rate)"),
        ]
        r = execute(routed_state)
        assert r["executed"] is True
        assert len(r["results"]) == 2
        assert r["results"][0]["success"] is True
        assert r["results"][1]["fallbacks"] == ["goose"]

    @patch("metabolon.sortase.graph.asyncio")
    def test_truncates_long_output(self, mock_aio, routed_state):
        mock_aio.run.return_value = [_fake_result(output="x" * 5000)]
        r = execute(routed_state)
        assert len(r["results"][0]["output"]) == 1000

    @patch("metabolon.sortase.graph.asyncio")
    def test_empty_output(self, mock_aio, routed_state):
        mock_aio.run.return_value = [_fake_result(output="")]
        r = execute(routed_state)
        assert r["results"][0]["output"] == ""

    @patch("metabolon.sortase.graph.asyncio")
    def test_calls_asyncio_run(self, mock_aio, initial_state, sample_task_dicts):
        state = dict(initial_state)
        state["tasks"] = sample_task_dicts
        state["tool_by_task"] = {"add-auth": "codex"}
        mock_aio.run.return_value = [_fake_result()]
        execute(state)
        mock_aio.run.assert_called_once()


# ═══════════════════════════════════════════════════════════════
# validate node
# ═══════════════════════════════════════════════════════════════


class TestValidateNode:

    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.subprocess")
    def test_success(self, mock_sp, mock_ve, initial_state, sample_task_dicts):
        state = dict(initial_state); state["tasks"] = sample_task_dicts; state["executed"] = True
        mock_sp.run.return_value = MagicMock(stdout="a.rs\nb.rs\n", stderr="", returncode=0)
        mock_ve.return_value = []
        r = validate(state)
        assert r["changed_files"] == ["a.rs", "b.rs"]
        assert r["validation_issues"] == []

    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.subprocess")
    def test_with_issues(self, mock_sp, mock_ve, initial_state, sample_task_dicts):
        state = dict(initial_state); state["tasks"] = sample_task_dicts; state["executed"] = True
        from metabolon.sortase.validator import ValidationIssue
        mock_sp.run.return_value = MagicMock(stdout="a.rs\n", stderr="", returncode=0)
        mock_ve.return_value = [
            ValidationIssue(check="scope", message="big", severity="warning"),
            ValidationIssue(check="placeholder-scan", message="stub", severity="error"),
        ]
        r = validate(state)
        assert len(r["validation_issues"]) == 2
        assert r["validation_issues"][1]["severity"] == "error"

    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.subprocess")
    def test_test_command_forwarded(self, mock_sp, mock_ve, initial_state, sample_task_dicts):
        state = dict(initial_state); state["tasks"] = sample_task_dicts
        state["test_command"] = "pytest tests/"; state["executed"] = True
        mock_sp.run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        mock_ve.return_value = []
        validate(state)
        assert mock_ve.call_args.kwargs["test_command"] == "pytest tests/"

    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.subprocess")
    def test_empty_diff(self, mock_sp, mock_ve, initial_state, sample_task_dicts):
        state = dict(initial_state); state["tasks"] = sample_task_dicts; state["executed"] = True
        mock_sp.run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        mock_ve.return_value = []
        r = validate(state)
        assert r["changed_files"] == []

    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.subprocess")
    def test_blank_lines_filtered(self, mock_sp, mock_ve, initial_state, sample_task_dicts):
        state = dict(initial_state); state["tasks"] = sample_task_dicts; state["executed"] = True
        mock_sp.run.return_value = MagicMock(stdout="\n  \na.rs\n\nb.rs\n\n", stderr="", returncode=0)
        mock_ve.return_value = []
        r = validate(state)
        assert r["changed_files"] == ["a.rs", "b.rs"]


# ═══════════════════════════════════════════════════════════════
# log_results node
# ═══════════════════════════════════════════════════════════════


class TestLogResultsNode:

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_all_success(self, mock_sum, mock_al, executed_state):
        mock_sum.return_value = "$0.0125"
        r = log_results(executed_state)
        assert r["success"] is True
        mock_al.assert_called_once()

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_validation_error_blocks_success(self, mock_sum, mock_al, executed_state):
        state = dict(executed_state)
        state["validation_issues"] = [{"check": "p", "message": "m", "severity": "error"}]
        mock_sum.return_value = "$0.01"
        assert log_results(state)["success"] is False

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_task_failure_blocks_success(self, mock_sum, mock_al, executed_state):
        state = dict(executed_state); state["results"][0]["success"] = False
        mock_sum.return_value = "N/A"
        assert log_results(state)["success"] is False

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_failure_reason_from_validation(self, mock_sum, mock_al, executed_state):
        state = dict(executed_state)
        state["validation_issues"] = [{"check": "tests", "message": "fail", "severity": "error"}]
        mock_sum.return_value = "$0.01"
        r = log_results(state)
        assert r["log_entry"]["failure_reason"] == "tests"
        assert r["log_entry"]["tests_passed"] == 0

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_entry_fields(self, mock_sum, mock_al, executed_state):
        mock_sum.return_value = "$0.0125 (+ flat-rate backends)"
        e = log_results(executed_state)["log_entry"]
        assert "timestamp" in e
        assert e["plan"] == "test-plan.yaml"
        assert e["project"] == "test-project"
        assert e["tasks"] == 2
        assert e["files_changed"] == 0
        assert e["executor"] == "langgraph"
        assert e["cost_estimate"] == "$0.0125 (+ flat-rate backends)"
        assert e["fallbacks"] == ["goose"]

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_fallback_chain_serialized(self, mock_sum, mock_al, executed_state):
        mock_sum.return_value = "$0.01"
        chain = log_results(executed_state)["log_entry"]["fallback_chain"]
        assert len(chain) == 1
        assert chain[0]["tool"] == "goose"
        assert chain[0]["succeeded"] is False

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_empty_results_is_vacuously_successful(self, mock_sum, mock_al, initial_state):
        state = dict(initial_state); state["results"] = []
        mock_sum.return_value = "N/A"
        assert log_results(state)["success"] is True

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_backend_from_state(self, mock_sum, mock_al, executed_state):
        state = dict(executed_state); state["backend"] = "codex"
        mock_sum.return_value = "$0.01"
        assert log_results(state)["log_entry"]["tool"] == "codex"

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_backend_falls_back_to_first_result(self, mock_sum, mock_al, executed_state):
        mock_sum.return_value = "$0.01"
        assert log_results(executed_state)["log_entry"]["tool"] == "codex"

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_unknown_tool_when_empty(self, mock_sum, mock_al, initial_state):
        state = dict(initial_state); state["results"] = []; state["backend"] = ""
        mock_sum.return_value = "N/A"
        assert log_results(state)["log_entry"]["tool"] == "unknown"

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_warnings_only_still_success(self, mock_sum, mock_al, executed_state):
        state = dict(executed_state)
        state["validation_issues"] = [{"check": "s", "message": "m", "severity": "warning"}]
        mock_sum.return_value = "$0.01"
        assert log_results(state)["success"] is True

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_no_failure_reason_when_clean(self, mock_sum, mock_al, executed_state):
        mock_sum.return_value = "$0.01"
        assert log_results(executed_state)["log_entry"]["failure_reason"] is None

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_duration_s_zero(self, mock_sum, mock_al, executed_state):
        mock_sum.return_value = "$0.01"
        assert log_results(executed_state)["log_entry"]["duration_s"] == 0.0

    @patch("metabolon.sortase.graph.append_log")
    @patch("metabolon.sortase.graph.summarize_cost_estimates")
    def test_files_changed_count(self, mock_sum, mock_al, executed_state):
        state = dict(executed_state); state["changed_files"] = ["a.py", "b.py", "c.rs"]
        mock_sum.return_value = "$0.01"
        assert log_results(state)["log_entry"]["files_changed"] == 3


# ═══════════════════════════════════════════════════════════════
# build_graph
# ═══════════════════════════════════════════════════════════════


class TestBuildGraph:

    def test_has_all_nodes(self):
        names = set(build_graph().nodes.keys())
        assert {"decompose", "route", "execute", "validate", "log_results"}.issubset(names)

    def test_entry_point(self):
        assert "decompose" in build_graph().nodes

    def test_compiles(self):
        assert build_graph().compile() is not None


# ═══════════════════════════════════════════════════════════════
# _open_checkpointer
# ═══════════════════════════════════════════════════════════════


class TestOpenCheckpointer:

    @patch("metabolon.sortase.graph.SqliteSaver")
    @patch("metabolon.sortase.graph.sqlite3")
    def test_creates_parent_directory(self, mock_sqlite, mock_saver, tmp_path, monkeypatch):
        db = tmp_path / "a" / "b" / "cp.db"
        monkeypatch.setattr("metabolon.sortase.graph.CHECKPOINT_DB", db)
        mock_sqlite.connect.return_value = MagicMock()
        mock_saver.return_value = MagicMock()
        _open_checkpointer()
        assert db.parent.exists()
        mock_sqlite.connect.assert_called_once_with(str(db), check_same_thread=False)

    @patch("metabolon.sortase.graph.SqliteSaver")
    @patch("metabolon.sortase.graph.sqlite3")
    def test_returns_saver_instance(self, mock_sqlite, mock_saver, tmp_path, monkeypatch):
        db = tmp_path / "cp.db"
        monkeypatch.setattr("metabolon.sortase.graph.CHECKPOINT_DB", db)
        conn = MagicMock()
        mock_sqlite.connect.return_value = conn
        saver = MagicMock()
        mock_saver.return_value = saver
        assert _open_checkpointer() is saver
        mock_saver.assert_called_once_with(conn)


# ═══════════════════════════════════════════════════════════════
# run() — public API
# ═══════════════════════════════════════════════════════════════


class TestRunPublicAPI:

    @patch("metabolon.sortase.graph.decompose_plan")
    @patch("metabolon.sortase.graph.subprocess")
    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.asyncio")
    @patch("metabolon.sortase.graph.append_log")
    def test_happy_path(
        self, mock_log, mock_aio, mock_ve, mock_sp, mock_dp,
        tmp_path, sample_task_specs,
    ):
        mock_dp.return_value = sample_task_specs
        mock_sp.run.return_value = MagicMock(stdout="a.rs\n", stderr="", returncode=0)
        mock_ve.return_value = []
        mock_aio.run.return_value = [_fake_result(), _fake_result("fix-overflow")]
        plan = tmp_path / "p.md"; plan.write_text("# plan\n")
        with patch("metabolon.sortase.graph._open_checkpointer", return_value=MemorySaver()):
            r = run(plan_file=str(plan), project_dir=str(tmp_path))
        assert r["success"] is True
        assert r["task_count"] == 2
        mock_log.assert_called_once()

    @patch("metabolon.sortase.graph.decompose_plan")
    @patch("metabolon.sortase.graph.append_log")
    def test_interactive_returns_paused(
        self, mock_log, mock_dp, tmp_path, sample_task_specs,
    ):
        mock_dp.return_value = sample_task_specs
        plan = tmp_path / "p.md"; plan.write_text("# plan\n")
        with patch("metabolon.sortase.graph._open_checkpointer", return_value=MemorySaver()):
            r = run(plan_file=str(plan), project_dir=str(tmp_path), interactive=True)
        assert r["status"] == "paused"
        assert "thread_id" in r
        assert "route_decisions" in r

    @patch("metabolon.sortase.graph.decompose_plan")
    @patch("metabolon.sortase.graph.subprocess")
    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.asyncio")
    @patch("metabolon.sortase.graph.append_log")
    def test_forced_backend(
        self, mock_log, mock_aio, mock_ve, mock_sp, mock_dp,
        tmp_path, sample_task_specs,
    ):
        mock_dp.return_value = sample_task_specs
        mock_sp.run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        mock_ve.return_value = []
        mock_aio.run.return_value = [_fake_result("add-auth", "gemini"), _fake_result("fix-overflow", "gemini")]
        plan = tmp_path / "p.md"; plan.write_text("# plan\n")
        with patch("metabolon.sortase.graph._open_checkpointer", return_value=MemorySaver()):
            r = run(plan_file=str(plan), project_dir=str(tmp_path), backend="gemini")
        assert r["success"] is True
        for d in r["route_decisions"]:
            assert d["tool"] == "gemini"

    @patch("metabolon.sortase.graph.decompose_plan")
    @patch("metabolon.sortase.graph.subprocess")
    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.asyncio")
    @patch("metabolon.sortase.graph.append_log")
    def test_custom_thread_id(
        self, mock_log, mock_aio, mock_ve, mock_sp, mock_dp,
        tmp_path, sample_task_specs,
    ):
        mock_dp.return_value = sample_task_specs
        mock_sp.run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        mock_ve.return_value = []
        mock_aio.run.return_value = [_fake_result()]
        plan = tmp_path / "p.md"; plan.write_text("# plan\n")
        with patch("metabolon.sortase.graph._open_checkpointer", return_value=MemorySaver()):
            r = run(plan_file=str(plan), project_dir=str(tmp_path), thread_id="custom-42")
        assert r["success"] is True

    @patch("metabolon.sortase.graph.decompose_plan")
    @patch("metabolon.sortase.graph.subprocess")
    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.asyncio")
    @patch("metabolon.sortase.graph.append_log")
    def test_test_command_and_timeout(
        self, mock_log, mock_aio, mock_ve, mock_sp, mock_dp,
        tmp_path, sample_task_specs,
    ):
        mock_dp.return_value = sample_task_specs
        mock_sp.run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        mock_ve.return_value = []
        mock_aio.run.return_value = [_fake_result()]
        plan = tmp_path / "p.md"; plan.write_text("# plan\n")
        with patch("metabolon.sortase.graph._open_checkpointer", return_value=MemorySaver()):
            r = run(plan_file=str(plan), project_dir=str(tmp_path),
                    test_command="pytest tests/", timeout=300)
        mock_ve.assert_called_once()
        assert mock_ve.call_args.kwargs["test_command"] == "pytest tests/"

    @patch("metabolon.sortase.graph.decompose_plan")
    @patch("metabolon.sortase.graph.subprocess")
    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.asyncio")
    @patch("metabolon.sortase.graph.append_log")
    def test_decompose_failure(
        self, mock_log, mock_aio, mock_ve, mock_sp, mock_dp, tmp_path,
    ):
        mock_dp.side_effect = FileNotFoundError("gone")
        mock_sp.run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        mock_ve.return_value = []
        plan = tmp_path / "p.md"; plan.write_text("# plan\n")
        with patch("metabolon.sortase.graph._open_checkpointer", return_value=MemorySaver()):
            r = run(plan_file=str(plan), project_dir=str(tmp_path))
        assert r["task_count"] == 0
        # errors accumulate: decompose error + execute "No tasks to execute"
        assert any("Decompose failed" in e for e in r["errors"])
        assert any("No tasks to execute" in e for e in r["errors"])

    @patch("metabolon.sortase.graph.decompose_plan")
    @patch("metabolon.sortase.graph.subprocess")
    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.asyncio")
    @patch("metabolon.sortase.graph.append_log")
    def test_serial_flag(
        self, mock_log, mock_aio, mock_ve, mock_sp, mock_dp,
        tmp_path, sample_task_specs,
    ):
        mock_dp.return_value = sample_task_specs
        mock_sp.run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        mock_ve.return_value = []
        mock_aio.run.return_value = [_fake_result(), _fake_result("fix-overflow")]
        plan = tmp_path / "p.md"; plan.write_text("# plan\n")
        with patch("metabolon.sortase.graph._open_checkpointer", return_value=MemorySaver()):
            r = run(plan_file=str(plan), project_dir=str(tmp_path), serial=True)
        assert r["success"] is True
        mock_aio.run.assert_called_once()

    @patch("metabolon.sortase.graph.decompose_plan")
    @patch("metabolon.sortase.graph.subprocess")
    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.asyncio")
    @patch("metabolon.sortase.graph.append_log")
    def test_generates_thread_id(
        self, mock_log, mock_aio, mock_ve, mock_sp, mock_dp,
        tmp_path, sample_task_specs,
    ):
        mock_dp.return_value = sample_task_specs
        mock_sp.run.return_value = MagicMock(stdout="", stderr="", returncode=0)
        mock_ve.return_value = []
        mock_aio.run.return_value = [_fake_result()]
        plan = tmp_path / "p.md"; plan.write_text("# plan\n")
        with patch("metabolon.sortase.graph._open_checkpointer", return_value=MemorySaver()):
            r = run(plan_file=str(plan), project_dir=str(tmp_path))
        assert r["success"] is True


# ═══════════════════════════════════════════════════════════════
# review_and_continue
# ═══════════════════════════════════════════════════════════════


class TestReviewAndContinue:

    @patch("metabolon.sortase.graph._open_checkpointer")
    def test_abort_sets_error(self, mock_cp):
        app = MagicMock()
        app.invoke.return_value = {"errors": ["Operator aborted."], "success": False}
        mock_cp.return_value = MagicMock()
        with patch("metabolon.sortase.graph.build_graph") as bg:
            g = MagicMock(); g.compile.return_value = app; bg.return_value = g
            r = review_and_continue("t1", approve=False)
        app.update_state.assert_called_once()
        assert "Operator aborted" in str(app.update_state.call_args)
        assert r["success"] is False

    @patch("metabolon.sortase.graph._open_checkpointer")
    def test_approve_no_override(self, mock_cp):
        app = MagicMock()
        app.invoke.return_value = {"success": True}
        mock_cp.return_value = MagicMock()
        with patch("metabolon.sortase.graph.build_graph") as bg:
            g = MagicMock(); g.compile.return_value = app; bg.return_value = g
            r = review_and_continue("t1", approve=True)
        assert r["success"] is True
        app.invoke.assert_called_once()
        assert len(app.update_state.call_args_list) == 0

    @patch("metabolon.sortase.graph._open_checkpointer")
    def test_override_routing_merged(self, mock_cp):
        app = MagicMock()
        app.invoke.return_value = {"success": True}
        mock_cp.return_value = MagicMock()
        sm = MagicMock(); sm.values = {"tool_by_task": {"a": "codex", "b": "gemini"}}
        app.get_state.return_value = sm
        with patch("metabolon.sortase.graph.build_graph") as bg:
            g = MagicMock(); g.compile.return_value = app; bg.return_value = g
            review_and_continue("t1", approve=True, override_routing={"a": "goose"})
        merged = app.update_state.call_args[0][1]["tool_by_task"]
        assert merged["a"] == "goose"
        assert merged["b"] == "gemini"

    @patch("metabolon.sortase.graph._open_checkpointer")
    def test_thread_id_in_config(self, mock_cp):
        app = MagicMock()
        app.invoke.return_value = {"success": True}
        mock_cp.return_value = MagicMock()
        sm = MagicMock(); sm.values = {"tool_by_task": {}}
        app.get_state.return_value = sm
        with patch("metabolon.sortase.graph.build_graph") as bg:
            g = MagicMock(); g.compile.return_value = app; bg.return_value = g
            review_and_continue("my-thread", approve=True)
        cfg = app.invoke.call_args[0][1]
        assert cfg["configurable"]["thread_id"] == "my-thread"


# ═══════════════════════════════════════════════════════════════
# SortaseState type & constants
# ═══════════════════════════════════════════════════════════════


class TestTypesAndConstants:

    def test_state_has_all_keys(self):
        expected = {
            "plan_file", "project_dir", "serial", "backend", "test_command", "timeout",
            "tasks", "task_count", "tool_by_task", "route_decisions",
            "results", "executed", "validation_issues", "changed_files",
            "success", "log_entry", "errors",
        }
        assert expected.issubset(set(SortaseState.__annotations__))

    def test_checkpoint_db_path(self):
        assert CHECKPOINT_DB.name == "checkpoints.db"
        assert ".local" in str(CHECKPOINT_DB)
        assert "vivesca" in str(CHECKPOINT_DB)
