from __future__ import annotations

"""Tests for metabolon.sortase.graph module."""


import tempfile
from dataclasses import asdict
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metabolon.sortase.decompose import TaskSpec
from metabolon.sortase.executor import TaskExecutionResult


class TestSortaseState:
    """Tests for SortaseState TypedDict."""

    def test_state_structure(self):
        """State has expected keys."""
        from metabolon.sortase.graph import SortaseState
        
        state: SortaseState = {
            "plan_file": "/path/to/plan.md",
            "project_dir": "/path/to/project",
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
        
        assert state["plan_file"] == "/path/to/plan.md"
        assert state["timeout"] == 600


class TestDecomposeNode:
    """Tests for decompose node function."""

    def test_decompose_success(self, tmp_path):
        """Successful decomposition returns tasks."""
        from metabolon.sortase.graph import decompose, SortaseState
        
        # Create a plan file
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
- name: task1
  description: Task 1
  files: []
  spec: Do something
""")
        
        state: SortaseState = {
            "plan_file": str(plan_file),
            "project_dir": str(tmp_path),
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
        
        result = decompose(state)
        
        assert result["task_count"] == 1
        assert len(result["tasks"]) == 1
        assert result["tasks"][0]["name"] == "task1"

    def test_decompose_error(self, tmp_path):
        """Decompose error is captured."""
        from metabolon.sortase.graph import decompose, SortaseState
        
        state: SortaseState = {
            "plan_file": str(tmp_path / "nonexistent.yaml"),
            "project_dir": str(tmp_path),
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
        
        result = decompose(state)
        
        assert result["task_count"] == 0
        assert len(result["errors"]) == 1
        assert "Decompose failed" in result["errors"][0]


class TestRouteNode:
    """Tests for route node function."""

    def test_route_with_forced_backend(self, tmp_path):
        """Route with forced backend uses that backend."""
        from metabolon.sortase.graph import route, SortaseState
        from metabolon.sortase.router import RouteDecision
        
        state: SortaseState = {
            "plan_file": str(tmp_path / "plan.md"),
            "project_dir": str(tmp_path),
            "serial": False,
            "backend": "gemini",
            "test_command": "",
            "timeout": 600,
            "tasks": [
                {"name": "task1", "description": "Create a function", "spec": "", "files": []},
            ],
            "task_count": 1,
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
        
        with patch("metabolon.sortase.graph.route_description") as mock_route:
            mock_route.return_value = RouteDecision(tool="gemini", reason="forced")
            result = route(state)
        
        assert result["tool_by_task"]["task1"] == "gemini"
        assert len(result["route_decisions"]) == 1

    def test_route_auto_detect(self, tmp_path):
        """Route auto-detects backend based on description."""
        from metabolon.sortase.graph import route, SortaseState
        from metabolon.sortase.router import RouteDecision
        
        state: SortaseState = {
            "plan_file": str(tmp_path / "plan.md"),
            "project_dir": str(tmp_path),
            "serial": False,
            "backend": "",  # auto-detect
            "test_command": "",
            "timeout": 600,
            "tasks": [
                {"name": "task1", "description": "Rust coding task", "spec": "", "files": []},
            ],
            "task_count": 1,
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
        
        with patch("metabolon.sortase.graph.route_description") as mock_route:
            mock_route.return_value = RouteDecision(tool="codex", reason="rust signal")
            result = route(state)
        
        assert result["tool_by_task"]["task1"] == "codex"


class TestExecuteNode:
    """Tests for execute node function."""

    def test_execute_no_tasks(self, tmp_path):
        """Execute with no tasks returns early."""
        from metabolon.sortase.graph import execute, SortaseState
        
        state: SortaseState = {
            "plan_file": str(tmp_path / "plan.md"),
            "project_dir": str(tmp_path),
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
        
        result = execute(state)
        
        assert result["executed"] is True
        assert "No tasks to execute" in result["errors"]

    def test_execute_with_tasks(self, tmp_path):
        """Execute with tasks returns results."""
        from metabolon.sortase.graph import execute, SortaseState
        
        state: SortaseState = {
            "plan_file": str(tmp_path / "plan.md"),
            "project_dir": str(tmp_path),
            "serial": True,
            "backend": "gemini",
            "test_command": "",
            "timeout": 60,
            "tasks": [
                {"name": "task1", "description": "Task 1", "spec": "Do something", "files": [], "signal": "default"},
            ],
            "task_count": 1,
            "tool_by_task": {"task1": "gemini"},
            "route_decisions": [],
            "results": [],
            "executed": False,
            "validation_issues": [],
            "changed_files": [],
            "success": False,
            "log_entry": {},
            "errors": [],
        }
        
        mock_result = TaskExecutionResult(
            task_name="task1",
            tool="gemini",
            prompt_file=None,
            success=True,
            output="Done",
            fallbacks=[],
            fallback_chain=[],
            cost_estimate="$0.001",
        )
        
        with patch("metabolon.sortase.graph.execute_tasks", new_callable=AsyncMock, return_value=[mock_result]):
            result = execute(state)
        
        assert result["executed"] is True
        assert len(result["results"]) == 1
        assert result["results"][0]["success"] is True


class TestValidateNode:
    """Tests for validate node function."""

    def test_validate_no_issues(self, tmp_path):
        """Validate with no issues."""
        from metabolon.sortase.graph import validate, SortaseState
        
        state: SortaseState = {
            "plan_file": str(tmp_path / "plan.md"),
            "project_dir": str(tmp_path),
            "serial": False,
            "backend": "",
            "test_command": "",
            "timeout": 600,
            "tasks": [],
            "task_count": 0,
            "tool_by_task": {},
            "route_decisions": [],
            "results": [],
            "executed": True,
            "validation_issues": [],
            "changed_files": [],
            "success": False,
            "log_entry": {},
            "errors": [],
        }
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            with patch("metabolon.sortase.graph.validate_execution", return_value=[]):
                result = validate(state)
        
        assert result["validation_issues"] == []
        assert result["changed_files"] == []

    def test_validate_with_changed_files(self, tmp_path):
        """Validate captures changed files."""
        from metabolon.sortase.graph import validate, SortaseState
        
        state: SortaseState = {
            "plan_file": str(tmp_path / "plan.md"),
            "project_dir": str(tmp_path),
            "serial": False,
            "backend": "",
            "test_command": "",
            "timeout": 600,
            "tasks": [],
            "task_count": 0,
            "tool_by_task": {},
            "route_decisions": [],
            "results": [],
            "executed": True,
            "validation_issues": [],
            "changed_files": [],
            "success": False,
            "log_entry": {},
            "errors": [],
        }
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="src/main.py\ntests/test_main.py\n", returncode=0)
            with patch("metabolon.sortase.graph.validate_execution", return_value=[]):
                result = validate(state)
        
        assert "src/main.py" in result["changed_files"]
        assert "tests/test_main.py" in result["changed_files"]


class TestLogResultsNode:
    """Tests for log_results node function."""

    def test_log_results_success(self, tmp_path):
        """Log results on success."""
        from metabolon.sortase.graph import log_results, SortaseState
        
        state: SortaseState = {
            "plan_file": str(tmp_path / "plan.md"),
            "project_dir": str(tmp_path),
            "serial": False,
            "backend": "gemini",
            "test_command": "",
            "timeout": 600,
            "tasks": [],
            "task_count": 1,
            "tool_by_task": {"task1": "gemini"},
            "route_decisions": [],
            "results": [
                {"task_name": "task1", "tool": "gemini", "success": True, "fallbacks": [], "fallback_chain": [], "cost_estimate": "$0.001"},
            ],
            "executed": True,
            "validation_issues": [],
            "changed_files": ["src/main.py"],
            "success": False,
            "log_entry": {},
            "errors": [],
        }
        
        with patch("metabolon.sortase.graph.append_log") as mock_append:
            result = log_results(state)
        
        assert result["success"] is True
        assert result["log_entry"]["success"] is True
        mock_append.assert_called_once()

    def test_log_results_with_validation_error(self, tmp_path):
        """Log results captures validation errors."""
        from metabolon.sortase.graph import log_results, SortaseState
        
        state: SortaseState = {
            "plan_file": str(tmp_path / "plan.md"),
            "project_dir": str(tmp_path),
            "serial": False,
            "backend": "gemini",
            "test_command": "",
            "timeout": 600,
            "tasks": [],
            "task_count": 1,
            "tool_by_task": {"task1": "gemini"},
            "route_decisions": [],
            "results": [
                {"task_name": "task1", "tool": "gemini", "success": True, "fallbacks": [], "fallback_chain": [], "cost_estimate": "$0.001"},
            ],
            "executed": True,
            "validation_issues": [
                {"check": "tests", "message": "Tests failed", "severity": "error"},
            ],
            "changed_files": [],
            "success": False,
            "log_entry": {},
            "errors": [],
        }
        
        with patch("metabolon.sortase.graph.append_log"):
            result = log_results(state)
        
        assert result["success"] is False
        assert result["log_entry"]["failure_reason"] == "tests"


class TestBuildGraph:
    """Tests for build_graph function."""

    def test_graph_structure(self):
        """Graph has expected nodes and edges."""
        from metabolon.sortase.graph import build_graph
        
        graph = build_graph()
        
        # Check nodes exist
        assert "decompose" in graph.nodes
        assert "route" in graph.nodes
        assert "execute" in graph.nodes
        assert "validate" in graph.nodes
        assert "log_results" in graph.nodes


class TestRun:
    """Tests for run function."""

    def test_run_basic_flow(self, tmp_path):
        """Run executes basic flow."""
        from metabolon.sortase.graph import run
        from langgraph.checkpoint.memory import InMemorySaver

        # Create a plan file
        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
- name: task1
  description: Task 1
  files: []
  spec: Do something
""")

        mock_result = TaskExecutionResult(
            task_name="task1",
            tool="gemini",
            prompt_file=None,
            success=True,
            output="Done",
            fallbacks=[],
            fallback_chain=[],
            cost_estimate="$0.001",
        )

        with patch("metabolon.sortase.graph._open_checkpointer", return_value=InMemorySaver()):
            with patch("metabolon.sortase.graph.route_description") as mock_route:
                from metabolon.sortase.router import RouteDecision
                mock_route.return_value = RouteDecision(tool="gemini", reason="test")

                with patch("metabolon.sortase.graph.execute_tasks", new_callable=AsyncMock, return_value=[mock_result]):
                    with patch("metabolon.sortase.graph.validate_execution", return_value=[]):
                        with patch("metabolon.sortase.graph.append_log"):
                            with patch("subprocess.run") as mock_subprocess:
                                mock_subprocess.return_value = MagicMock(stdout="", returncode=0)
                                result = run(
                                    plan_file=str(plan_file),
                                    project_dir=str(tmp_path),
                                    serial=True,
                                )

        assert result["success"] is True

    def test_run_interactive_paused(self, tmp_path):
        """Run with interactive pauses before execute."""
        from metabolon.sortase.graph import run, build_graph
        from langgraph.checkpoint.memory import InMemorySaver

        plan_file = tmp_path / "plan.yaml"
        plan_file.write_text("""
- name: task1
  description: Task 1
  files: []
  spec: Do something
""")

        checkpointer = InMemorySaver()

        with patch("metabolon.sortase.graph._open_checkpointer", return_value=checkpointer):
            with patch("metabolon.sortase.graph.route_description") as mock_route:
                from metabolon.sortase.router import RouteDecision
                mock_route.return_value = RouteDecision(tool="gemini", reason="test")

                result = run(
                    plan_file=str(plan_file),
                    project_dir=str(tmp_path),
                    interactive=True,
                )

        # When interactive, the graph pauses before execute
        assert result["status"] == "paused"
        assert "route_decisions" in result


class TestReviewAndContinue:
    """Tests for review_and_continue function."""

    def test_review_abort(self, tmp_path):
        """Review and abort."""
        from metabolon.sortase.graph import review_and_continue, build_graph
        from langgraph.checkpoint.memory import InMemorySaver

        checkpointer = InMemorySaver()
        graph = build_graph()
        app = graph.compile(checkpointer=checkpointer, interrupt_before=["execute"])

        # First create a paused state by running interactively
        initial_state = {
            "plan_file": str(tmp_path / "plan.md"),
            "project_dir": str(tmp_path),
            "serial": False,
            "backend": "",
            "test_command": "",
            "timeout": 600,
            "tasks": [{"name": "task1", "description": "Task", "spec": "Do", "files": []}],
            "task_count": 1,
            "tool_by_task": {"task1": "gemini"},
            "route_decisions": [],
            "results": [],
            "executed": False,
            "validation_issues": [],
            "changed_files": [],
            "success": False,
            "log_entry": {},
            "errors": [],
        }

        # Invoke to create a paused state
        thread_id = "test-thread-abort"
        config = {"configurable": {"thread_id": thread_id}}
        app.invoke(initial_state, config)

        with patch("metabolon.sortase.graph._open_checkpointer", return_value=checkpointer):
            result = review_and_continue(thread_id, approve=False)

        assert result["success"] is False
        assert any("aborted" in str(e).lower() for e in result.get("errors", []))
