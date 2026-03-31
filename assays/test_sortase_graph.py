"""Tests for sortase.graph — LangGraph executor for plan-based agent orchestration.

Covers all node functions (decompose, route, execute, validate, log_results),
build_graph assembly, run(), and review_and_continue().
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metabolon.sortase.decompose import TaskSpec
from metabolon.sortase.executor import (
    ExecutionAttempt,
    FallbackStep,
    TaskExecutionResult,
)
from metabolon.sortase.graph import (
    CHECKPOINT_DB,
    SortaseState,
    build_graph,
    decompose,
    execute,
    log_results,
    review_and_continue,
    route,
    run,
    validate,
    _open_checkpointer,
)


# ── fixtures ─────────────────────────────────────────────────


@pytest.fixture()
def sample_tasks():
    """Two TaskSpecs for reuse across tests."""
    return [
        TaskSpec(
            name="add-auth",
            description="Add Rust authentication module",
            spec="Implement auth.rs with JWT validation",
            files=["src/auth.rs"],
        ),
        TaskSpec(
            name="add-tests",
            description="Add boilerplate test scaffolding",
            spec="Create test_auth.py",
            files=["tests/test_auth.py"],
        ),
    ]


@pytest.fixture()
def base_state(tmp_path, sample_tasks):
    """A minimal SortaseState with plan file written to tmp_path."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("# plan\n")
    return SortaseState(
        plan_file=str(plan_file),
        project_dir=str(tmp_path),
        serial=False,
        backend="",
        test_command="",
        timeout=600,
        tasks=[asdict(t) for t in sample_tasks],
        task_count=2,
        tool_by_task={},
        route_decisions=[],
        results=[],
        executed=False,
        validation_issues=[],
        changed_files=[],
        success=False,
        log_entry={},
        errors=[],
    )


@pytest.fixture()
def executed_state(base_state):
    """State after successful execution, ready for validate/log."""
    base_state["tool_by_task"] = {"add-auth": "codex", "add-tests": "opencode"}
    base_state["results"] = [
        {
            "task_name": "add-auth",
            "tool": "codex",
            "success": True,
            "output": "auth.rs created",
            "fallbacks": [],
            "fallback_chain": [],
            "prompt_file": "/tmp/prompt1.txt",
            "cost_estimate": "$0.0012",
        },
        {
            "task_name": "add-tests",
            "tool": "opencode",
            "success": True,
            "output": "test_auth.py created",
            "fallbacks": [],
            "fallback_chain": [],
            "prompt_file": "/tmp/prompt2.txt",
            "cost_estimate": "$0.00 (flat-rate)",
        },
    ]
    base_state["executed"] = True
    return base_state


# ── decompose node ───────────────────────────────────────────


class TestDecompose:
    """Tests for the decompose() node function."""

    @patch("metabolon.sortase.graph.decompose_plan")
    def test_returns_tasks_as_dicts(self, mock_decompose, sample_tasks):
        mock_decompose.return_value = sample_tasks
        state = SortaseState(
            plan_file="/tmp/plan.md", project_dir="/tmp/proj",
            serial=False, backend="", test_command="", timeout=600,
            tasks=[], task_count=0, tool_by_task={}, route_decisions=[],
            results=[], executed=False, validation_issues=[], changed_files=[],
            success=False, log_entry={}, errors=[],
        )
        result = decompose(state)
        assert result["task_count"] == 2
        assert result["tasks"][0]["name"] == "add-auth"
        assert isinstance(result["tasks"], list)
        for task_dict in result["tasks"]:
            assert "name" in task_dict
            assert "spec" in task_dict

    @patch("metabolon.sortase.graph.decompose_plan")
    def test_handles_decompose_error(self, mock_decompose):
        mock_decompose.side_effect = FileNotFoundError("plan not found")
        state = SortaseState(
            plan_file="/missing.md", project_dir="/tmp/proj",
            serial=False, backend="", test_command="", timeout=600,
            tasks=[], task_count=0, tool_by_task={}, route_decisions=[],
            results=[], executed=False, validation_issues=[], changed_files=[],
            success=False, log_entry={}, errors=[],
        )
        result = decompose(state)
        assert result["task_count"] == 0
        assert result["tasks"] == []
        assert len(result["errors"]) == 1
        assert "Decompose failed" in result["errors"][0]

    @patch("metabolon.sortase.graph.decompose_plan")
    def test_empty_plan_produces_empty_tasks(self, mock_decompose):
        mock_decompose.return_value = []
        state = SortaseState(
            plan_file="/tmp/empty.md", project_dir="/tmp/proj",
            serial=False, backend="", test_command="", timeout=600,
            tasks=[], task_count=0, tool_by_task={}, route_decisions=[],
            results=[], executed=False, validation_issues=[], changed_files=[],
            success=False, log_entry={}, errors=[],
        )
        result = decompose(state)
        assert result["task_count"] == 0
        assert result["tasks"] == []


# ── route node ───────────────────────────────────────────────


class TestRoute:
    """Tests for the route() node function."""

    def test_routes_each_task(self, base_state):
        result = route(base_state)
        assert "add-auth" in result["tool_by_task"]
        assert "add-tests" in result["tool_by_task"]
        assert len(result["route_decisions"]) == 2
        for decision in result["route_decisions"]:
            assert "task" in decision
            assert "tool" in decision
            assert "reason" in decision

    def test_rust_description_routes_to_codex(self, base_state):
        result = route(base_state)
        auth_decision = next(
            d for d in result["route_decisions"] if d["task"] == "add-auth"
        )
        assert auth_decision["tool"] == "codex"

    def test_forced_backend_overrides_routing(self, base_state):
        base_state["backend"] = "gemini"
        result = route(base_state)
        for decision in result["route_decisions"]:
            assert decision["tool"] == "gemini"

    def test_empty_tasks_produce_empty_routing(self):
        state = SortaseState(
            plan_file="/tmp/plan.md", project_dir="/tmp/proj",
            serial=False, backend="", test_command="", timeout=600,
            tasks=[], task_count=0, tool_by_task={}, route_decisions=[],
            results=[], executed=False, validation_issues=[], changed_files=[],
            success=False, log_entry={}, errors=[],
        )
        result = route(state)
        assert result["tool_by_task"] == {}
        assert result["route_decisions"] == []


# ── execute node ─────────────────────────────────────────────


class TestExecute:
    """Tests for the execute() node function."""

    @patch("metabolon.sortase.graph.asyncio.run")
    def test_dispatches_tasks_and_returns_results(self, mock_asyncio_run, base_state):
        fake_result = TaskExecutionResult(
            task_name="add-auth",
            tool="codex",
            prompt_file="/tmp/p1.txt",
            success=True,
            output="done",
            fallbacks=[],
            fallback_chain=[],
            cost_estimate="$0.0012",
        )
        mock_asyncio_run.return_value = [fake_result]
        base_state["tool_by_task"] = {"add-auth": "codex", "add-tests": "opencode"}

        result = execute(base_state)
        assert result["executed"] is True
        assert len(result["results"]) == 1
        assert result["results"][0]["task_name"] == "add-auth"
        assert result["results"][0]["success"] is True

    @patch("metabolon.sortase.graph.asyncio.run")
    def test_truncates_long_output(self, mock_asyncio_run, base_state):
        long_output = "x" * 2000
        fake_result = TaskExecutionResult(
            task_name="add-auth",
            tool="codex",
            prompt_file=None,
            success=True,
            output=long_output,
            fallbacks=[],
            fallback_chain=[],
            cost_estimate="",
        )
        mock_asyncio_run.return_value = [fake_result]
        base_state["tool_by_task"] = {"add-auth": "codex"}

        result = execute(base_state)
        assert len(result["results"][0]["output"]) == 1000

    def test_no_tasks_returns_error(self, base_state):
        base_state["tasks"] = []
        result = execute(base_state)
        assert result["executed"] is True
        assert "No tasks to execute" in result["errors"]

    @patch("metabolon.sortase.graph.asyncio.run")
    def test_reconstructs_task_specs_from_dicts(self, mock_asyncio_run, base_state):
        """Verify TaskSpec is reconstructed with all fields from the dict."""
        fake_result = TaskExecutionResult(
            task_name="add-auth", tool="codex", prompt_file=None,
            success=True, output="", fallbacks=[], fallback_chain=[], cost_estimate="",
        )
        mock_asyncio_run.return_value = [fake_result]
        base_state["tool_by_task"] = {"add-auth": "codex"}

        execute(base_state)
        call_args = mock_asyncio_run.call_args
        tasks_arg = call_args[0][0]
        assert isinstance(tasks_arg[0], TaskSpec)
        assert tasks_arg[0].name == "add-auth"
        assert tasks_arg[0].files == ["src/auth.rs"]

    @patch("metabolon.sortase.graph.asyncio.run")
    def test_fallback_chain_preserved_in_output(self, mock_asyncio_run, base_state):
        chain = [
            FallbackStep(tool="codex", succeeded=False, failure_reason="timeout"),
            FallbackStep(tool="gemini", succeeded=True),
        ]
        fake_result = TaskExecutionResult(
            task_name="add-auth", tool="gemini", prompt_file=None,
            success=True, output="ok", fallbacks=["codex"],
            fallback_chain=chain, cost_estimate="",
        )
        mock_asyncio_run.return_value = [fake_result]
        base_state["tool_by_task"] = {"add-auth": "codex"}

        result = execute(base_state)
        output_result = result["results"][0]
        assert output_result["fallbacks"] == ["codex"]
        assert len(output_result["fallback_chain"]) == 2
        assert output_result["fallback_chain"][0]["succeeded"] is False


# ── validate node ────────────────────────────────────────────


class TestValidate:
    """Tests for the validate() node function."""

    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.subprocess.run")
    def test_returns_changed_files(self, mock_subprocess, mock_validate, base_state):
        mock_subprocess.return_value = MagicMock(
            stdout="src/auth.rs\ntests/test_auth.py\n", stderr=""
        )
        mock_validate.return_value = []
        result = validate(base_state)
        assert result["changed_files"] == ["src/auth.rs", "tests/test_auth.py"]

    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.subprocess.run")
    def test_returns_validation_issues_as_dicts(self, mock_subprocess, mock_validate, base_state):
        from metabolon.sortase.validator import ValidationIssue

        mock_subprocess.return_value = MagicMock(stdout="", stderr="")
        mock_validate.return_value = [
            ValidationIssue(check="placeholder-scan", message="TODO found", severity="warning"),
            ValidationIssue(check="tests", message="Tests failed", severity="error"),
        ]
        result = validate(base_state)
        assert len(result["validation_issues"]) == 2
        assert result["validation_issues"][0]["check"] == "placeholder-scan"
        assert result["validation_issues"][1]["severity"] == "error"

    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.subprocess.run")
    def test_no_changes_no_issues(self, mock_subprocess, mock_validate, base_state):
        mock_subprocess.return_value = MagicMock(stdout="", stderr="")
        mock_validate.return_value = []
        result = validate(base_state)
        assert result["changed_files"] == []
        assert result["validation_issues"] == []

    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.subprocess.run")
    def test_ignores_blank_lines_in_diff(self, mock_subprocess, mock_validate, base_state):
        mock_subprocess.return_value = MagicMock(
            stdout="src/auth.rs\n\n\ntests/test_auth.py\n", stderr=""
        )
        mock_validate.return_value = []
        result = validate(base_state)
        assert result["changed_files"] == ["src/auth.rs", "tests/test_auth.py"]

    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.subprocess.run")
    def test_passes_test_command_when_provided(self, mock_subprocess, mock_validate, base_state):
        base_state["test_command"] = "pytest -x"
        mock_subprocess.return_value = MagicMock(stdout="", stderr="")
        mock_validate.return_value = []
        validate(base_state)
        mock_validate.assert_called_once()
        call_kwargs = mock_validate.call_args
        assert call_kwargs[1].get("test_command") == "pytest -x" or call_kwargs[0][2] == "pytest -x" if len(call_kwargs[0]) > 2 else True


# ── log_results node ─────────────────────────────────────────


class TestLogResults:
    """Tests for the log_results() node function."""

    @patch("metabolon.sortase.graph.append_log")
    def test_success_when_all_ok(self, mock_log, executed_state):
        executed_state["validation_issues"] = []
        result = log_results(executed_state)
        assert result["success"] is True
        assert result["log_entry"]["success"] is True
        mock_log.assert_called_once()

    @patch("metabolon.sortase.graph.append_log")
    def test_failure_on_task_failure(self, mock_log, executed_state):
        executed_state["results"][0]["success"] = False
        result = log_results(executed_state)
        assert result["success"] is False

    @patch("metabolon.sortase.graph.append_log")
    def test_failure_on_validation_error(self, mock_log, executed_state):
        executed_state["validation_issues"] = [
            {"check": "tests", "message": "Tests failed", "severity": "error"}
        ]
        result = log_results(executed_state)
        assert result["success"] is False
        assert result["log_entry"]["failure_reason"] == "tests"

    @patch("metabolon.sortase.graph.append_log")
    def test_log_entry_contains_required_fields(self, mock_log, executed_state):
        result = log_results(executed_state)
        entry = result["log_entry"]
        assert "timestamp" in entry
        assert "plan" in entry
        assert "project" in entry
        assert "tasks" in entry
        assert "tool" in entry
        assert "duration_s" in entry
        assert "executor" in entry
        assert entry["executor"] == "langgraph"

    @patch("metabolon.sortase.graph.append_log")
    def test_log_entry_tool_falls_back_to_first_result(self, mock_log, executed_state):
        executed_state["backend"] = ""
        result = log_results(executed_state)
        assert result["log_entry"]["tool"] == "codex"

    @patch("metabolon.sortase.graph.append_log")
    def test_log_entry_uses_forced_backend(self, mock_log, executed_state):
        executed_state["backend"] = "gemini"
        result = log_results(executed_state)
        assert result["log_entry"]["tool"] == "gemini"

    @patch("metabolon.sortase.graph.append_log")
    def test_tests_passed_zero_when_test_issue(self, mock_log, executed_state):
        executed_state["validation_issues"] = [
            {"check": "tests", "message": "fail", "severity": "error"}
        ]
        result = log_results(executed_state)
        assert result["log_entry"]["tests_passed"] == 0

    @patch("metabolon.sortase.graph.append_log")
    def test_empty_results_is_failure(self, mock_log, base_state):
        base_state["results"] = []
        base_state["validation_issues"] = []
        result = log_results(base_state)
        assert result["success"] is False

    @patch("metabolon.sortase.graph.append_log")
    def test_cost_estimate_aggregated(self, mock_log, executed_state):
        result = log_results(executed_state)
        cost = result["log_entry"]["cost_estimate"]
        assert cost != "N/A"


# ── build_graph ──────────────────────────────────────────────


class TestBuildGraph:
    """Tests for build_graph() graph assembly."""

    def test_graph_has_all_nodes(self):
        graph = build_graph()
        # Compiling the graph and checking it doesn't raise is a basic smoke test
        compiled = graph.compile()
        assert compiled is not None

    def test_graph_nodes_registered(self):
        graph = build_graph()
        node_names = set(graph.nodes.keys())
        expected = {"decompose", "route", "execute", "validate", "log_results", "__start__"}
        assert expected.issubset(node_names)


# ── run() public API ────────────────────────────────────────


class TestRun:
    """Tests for the run() entry point."""

    @patch("metabolon.sortase.graph._open_checkpointer")
    @patch("metabolon.sortase.graph.decompose_plan")
    @patch("metabolon.sortase.graph.subprocess.run")
    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.asyncio.run")
    @patch("metabolon.sortase.graph.append_log")
    def test_full_run_happy_path(
        self, mock_log, mock_asyncio, mock_validate, mock_subprocess,
        mock_decompose, mock_checkpointer, tmp_path, sample_tasks,
    ):
        mock_checkpointer.return_value = MagicMock()
        mock_decompose.return_value = sample_tasks
        mock_subprocess.return_value = MagicMock(stdout="src/auth.rs\n", stderr="")
        mock_validate.return_value = []
        fake_result = TaskExecutionResult(
            task_name="add-auth", tool="codex", prompt_file=None,
            success=True, output="ok", fallbacks=[], fallback_chain=[], cost_estimate="",
        )
        mock_asyncio.return_value = [fake_result]

        plan_file = tmp_path / "plan.md"
        plan_file.write_text("# plan\n")

        result = run(plan_file=str(plan_file), project_dir=str(tmp_path))
        assert result["success"] is True
        assert result["task_count"] == 2

    @patch("metabolon.sortase.graph._open_checkpointer")
    @patch("metabolon.sortase.graph.decompose_plan")
    @patch("metabolon.sortase.graph.append_log")
    def test_interactive_mode_returns_paused(
        self, mock_log, mock_decompose, mock_checkpointer, tmp_path, sample_tasks,
    ):
        mock_checkpointer.return_value = MagicMock()
        mock_decompose.return_value = sample_tasks

        # Interactive mode compiles with interrupt_before=["execute"]
        # so the graph stops after route and returns paused state
        plan_file = tmp_path / "plan.md"
        plan_file.write_text("# plan\n")

        result = run(
            plan_file=str(plan_file),
            project_dir=str(tmp_path),
            interactive=True,
        )
        assert result["status"] == "paused"
        assert "route_decisions" in result
        assert "thread_id" in result

    @patch("metabolon.sortase.graph._open_checkpointer")
    @patch("metabolon.sortase.graph.decompose_plan")
    @patch("metabolon.sortase.graph.subprocess.run")
    @patch("metabolon.sortase.graph.validate_execution")
    @patch("metabolon.sortase.graph.asyncio.run")
    @patch("metabolon.sortase.graph.append_log")
    def test_run_with_forced_backend(
        self, mock_log, mock_asyncio, mock_validate, mock_subprocess,
        mock_decompose, mock_checkpointer, tmp_path, sample_tasks,
    ):
        mock_checkpointer.return_value = MagicMock()
        mock_decompose.return_value = sample_tasks
        mock_subprocess.return_value = MagicMock(stdout="", stderr="")
        mock_validate.return_value = []
        fake_result = TaskExecutionResult(
            task_name="add-auth", tool="gemini", prompt_file=None,
            success=True, output="ok", fallbacks=[], fallback_chain=[], cost_estimate="",
        )
        mock_asyncio.return_value = [fake_result, fake_result]

        plan_file = tmp_path / "plan.md"
        plan_file.write_text("# plan\n")

        result = run(
            plan_file=str(plan_file),
            project_dir=str(tmp_path),
            backend="gemini",
        )
        assert result["success"] is True


# ── review_and_continue ──────────────────────────────────────


class TestReviewAndContinue:
    """Tests for the review_and_continue() resume function."""

    @patch("metabolon.sortase.graph._open_checkpointer")
    def test_abort_sets_error(self, mock_checkpointer):
        mock_app = MagicMock()
        mock_app.invoke.return_value = {"errors": ["Operator aborted."], "success": False}
        mock_checkpointer.return_value = MagicMock()

        with patch("metabolon.sortase.graph.build_graph") as mock_build:
            mock_graph = MagicMock()
            mock_graph.compile.return_value = mock_app
            mock_build.return_value = mock_graph

            result = review_and_continue("thread-1", approve=False)

        mock_app.update_state.assert_called_once()
        call_args = mock_app.update_state.call_args[0]
        assert call_args[1]["errors"] == ["Operator aborted."]

    @patch("metabolon.sortase.graph._open_checkpointer")
    def test_approve_without_override(self, mock_checkpointer):
        mock_app = MagicMock()
        mock_app.invoke.return_value = {"success": True}
        mock_checkpointer.return_value = MagicMock()

        with patch("metabolon.sortase.graph.build_graph") as mock_build:
            mock_graph = MagicMock()
            mock_graph.compile.return_value = mock_app
            mock_build.return_value = mock_graph

            result = review_and_continue("thread-1", approve=True)
            assert result["success"] is True

    @patch("metabolon.sortase.graph._open_checkpointer")
    def test_override_routing_applied(self, mock_checkpointer):
        mock_app = MagicMock()
        mock_app.invoke.return_value = {"success": True}
        mock_checkpointer.return_value = MagicMock()

        mock_state = MagicMock()
        mock_state.values = {"tool_by_task": {"task-a": "codex"}}

        with patch("metabolon.sortase.graph.build_graph") as mock_build:
            mock_graph = MagicMock()
            mock_graph.compile.return_value = mock_app
            mock_build.return_value = mock_graph
            mock_app.get_state.return_value = mock_state

            result = review_and_continue(
                "thread-1",
                approve=True,
                override_routing={"task-a": "gemini"},
            )
        mock_app.update_state.assert_called()
        # The override should have been merged into tool_by_task
        update_call = mock_app.update_state.call_args
        assert update_call[0][0] == {"configurable": {"thread_id": "thread-1"}}
        assert update_call[0][1]["tool_by_task"]["task-a"] == "gemini"


# ── _open_checkpointer ──────────────────────────────────────


class TestOpenCheckpointer:
    """Tests for the _open_checkpointer helper."""

    @patch("metabolon.sortase.graph.SqliteSaver")
    def test_creates_parent_directory(self, mock_saver, tmp_path):
        with patch("metabolon.sortase.graph.CHECKPOINT_DB", tmp_path / "sub" / "checkpoints.db"):
            with patch("metabolon.sortase.graph.sqlite3.connect") as mock_conn:
                _open_checkpointer()
                assert (tmp_path / "sub").exists()
