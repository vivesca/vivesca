from __future__ import annotations

"""Tests for sortase exec --json-output format comprehensiveness."""


import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from click.testing import CliRunner

from metabolon.sortase.executor import ExecutionAttempt, TaskExecutionResult
from metabolon.sortase.validator import ValidationIssue


def _extract_json(output: str) -> dict:
    """Extract the JSON object from CLI output that may contain Rich formatting."""
    start = output.index("{")
    # Find matching closing brace
    depth = 0
    for idx in range(start, len(output)):
        if output[idx] == "{":
            depth += 1
        elif output[idx] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(output[start : idx + 1])
    raise ValueError("No matching closing brace found")


@pytest.fixture()
def plan_file(tmp_path: Path) -> Path:
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan\n## Task 1: Do something\nDescription here.\n")
    return plan


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    proj = tmp_path / "project"
    proj.mkdir()
    (proj / ".git").mkdir()
    return proj


def _make_results() -> list[TaskExecutionResult]:
    return [
        TaskExecutionResult(
            task_name="task_1",
            tool="goose",
            prompt_file="/tmp/task_1.prompt.md",
            success=True,
            attempts=[
                ExecutionAttempt(
                    tool="goose",
                    exit_code=0,
                    duration_s=5.2,
                    output="done",
                    cost_estimate="$0.00 (flat-rate)",
                ),
            ],
            output="done",
            cost_estimate="$0.00 (flat-rate)",
        ),
    ]


def _make_validation_issues() -> list[ValidationIssue]:
    return [
        ValidationIssue(
            check="placeholder-scan", message="Found TODO in foo.py", severity="warning"
        ),
        ValidationIssue(check="ast-check", message="Syntax error in bar.py", severity="error"),
    ]


class TestJsonOutputFormat:
    """Verify --json-output includes all required fields for machine parsing."""

    @patch("metabolon.sortase.cli.validate_execution")
    @patch("metabolon.sortase.cli.execute_tasks", new_callable=AsyncMock)
    @patch("metabolon.sortase.cli.decompose_plan")
    @patch("metabolon.sortase.cli.route_description")
    def test_json_output_has_cost_estimate_per_task(
        self,
        mock_route: MagicMock,
        mock_decompose: MagicMock,
        mock_exec: AsyncMock,
        mock_validate: MagicMock,
        plan_file: Path,
        project_dir: Path,
    ) -> None:
        """Each task in JSON output must include cost_estimate."""
        from metabolon.sortase.cli import main

        mock_decompose.return_value = []
        mock_route.return_value = MagicMock(tool="goose")
        mock_exec.return_value = _make_results()
        mock_validate.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["exec", str(plan_file), "-p", str(project_dir), "--json-output"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        # Find JSON in output (after any Rich formatting)
        data = _extract_json(result.output)

        assert "tasks" in data
        assert len(data["tasks"]) == 1
        assert "cost_estimate" in data["tasks"][0]
        assert data["tasks"][0]["cost_estimate"] == "$0.00 (flat-rate)"

    @patch("metabolon.sortase.cli.validate_execution")
    @patch("metabolon.sortase.cli.execute_tasks", new_callable=AsyncMock)
    @patch("metabolon.sortase.cli.decompose_plan")
    @patch("metabolon.sortase.cli.route_description")
    def test_json_output_has_run_level_cost_estimate(
        self,
        mock_route: MagicMock,
        mock_decompose: MagicMock,
        mock_exec: AsyncMock,
        mock_validate: MagicMock,
        plan_file: Path,
        project_dir: Path,
    ) -> None:
        """Top-level JSON output must include aggregate cost_estimate."""
        from metabolon.sortase.cli import main

        mock_decompose.return_value = []
        mock_route.return_value = MagicMock(tool="goose")
        mock_exec.return_value = _make_results()
        mock_validate.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["exec", str(plan_file), "-p", str(project_dir), "--json-output"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        data = _extract_json(result.output)

        assert data["cost_estimate"] == "$0.00 (flat-rate)"

    @patch("metabolon.sortase.cli.validate_execution")
    @patch("metabolon.sortase.cli.execute_tasks", new_callable=AsyncMock)
    @patch("metabolon.sortase.cli.decompose_plan")
    @patch("metabolon.sortase.cli.route_description")
    def test_json_output_has_validation_issues_with_check_and_severity(
        self,
        mock_route: MagicMock,
        mock_decompose: MagicMock,
        mock_exec: AsyncMock,
        mock_validate: MagicMock,
        plan_file: Path,
        project_dir: Path,
    ) -> None:
        """validation_issues must include severity AND check fields."""
        from metabolon.sortase.cli import main

        mock_decompose.return_value = []
        mock_route.return_value = MagicMock(tool="goose")
        mock_exec.return_value = _make_results()
        mock_validate.return_value = _make_validation_issues()

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["exec", str(plan_file), "-p", str(project_dir), "--json-output"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        data = _extract_json(result.output)

        assert "validation_issues" in data
        assert len(data["validation_issues"]) == 2
        issue = data["validation_issues"][0]
        assert "severity" in issue
        assert "check" in issue
        assert issue["check"] == "placeholder-scan"
        assert issue["severity"] == "warning"

    @patch("metabolon.sortase.cli.validate_execution")
    @patch("metabolon.sortase.cli.execute_tasks", new_callable=AsyncMock)
    @patch("metabolon.sortase.cli.decompose_plan")
    @patch("metabolon.sortase.cli.route_description")
    def test_json_output_has_total_duration(
        self,
        mock_route: MagicMock,
        mock_decompose: MagicMock,
        mock_exec: AsyncMock,
        mock_validate: MagicMock,
        plan_file: Path,
        project_dir: Path,
    ) -> None:
        """JSON output must include total_duration field."""
        from metabolon.sortase.cli import main

        mock_decompose.return_value = []
        mock_route.return_value = MagicMock(tool="goose")
        mock_exec.return_value = _make_results()
        mock_validate.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["exec", str(plan_file), "-p", str(project_dir), "--json-output"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        data = _extract_json(result.output)

        assert "total_duration_s" in data
        assert isinstance(data["total_duration_s"], (int, float))
        assert data["total_duration_s"] > 0

    @patch("metabolon.sortase.cli.validate_execution")
    @patch("metabolon.sortase.cli.execute_tasks", new_callable=AsyncMock)
    @patch("metabolon.sortase.cli.decompose_plan")
    @patch("metabolon.sortase.cli.route_description")
    def test_json_output_has_attempt_details(
        self,
        mock_route: MagicMock,
        mock_decompose: MagicMock,
        mock_exec: AsyncMock,
        mock_validate: MagicMock,
        plan_file: Path,
        project_dir: Path,
    ) -> None:
        """Each task should expose attempt-level details for machine parsing."""
        from metabolon.sortase.cli import main

        mock_decompose.return_value = []
        mock_route.return_value = MagicMock(tool="goose")
        mock_exec.return_value = _make_results()
        mock_validate.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["exec", str(plan_file), "-p", str(project_dir), "--json-output"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        data = _extract_json(result.output)

        task = data["tasks"][0]
        assert task["attempt_count"] == 1
        assert task["fallback_count"] == 0
        assert task["prompt_file"] == "/tmp/task_1.prompt.md"
        assert task["output"] == "done"
        assert len(task["attempts"]) == 1

        attempt = task["attempts"][0]
        for key in (
            "tool",
            "exit_code",
            "duration_s",
            "failure_reason",
            "cost_estimate",
            "output",
        ):
            assert key in attempt, f"Missing attempt key: {key}"
        assert attempt["tool"] == "goose"
        assert attempt["exit_code"] == 0
        assert attempt["cost_estimate"] == "$0.00 (flat-rate)"

    @patch("metabolon.sortase.cli.validate_execution")
    @patch("metabolon.sortase.cli.execute_tasks", new_callable=AsyncMock)
    @patch("metabolon.sortase.cli.decompose_plan")
    @patch("metabolon.sortase.cli.route_description")
    def test_json_output_comprehensive_schema(
        self,
        mock_route: MagicMock,
        mock_decompose: MagicMock,
        mock_exec: AsyncMock,
        mock_validate: MagicMock,
        plan_file: Path,
        project_dir: Path,
    ) -> None:
        """Full schema check: all expected top-level and per-task keys present."""
        from metabolon.sortase.cli import main

        mock_decompose.return_value = []
        mock_route.return_value = MagicMock(tool="goose")
        mock_exec.return_value = _make_results()
        mock_validate.return_value = _make_validation_issues()

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["exec", str(plan_file), "-p", str(project_dir), "--json-output"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        data = _extract_json(result.output)

        # Top-level keys
        for key in (
            "schema_version",
            "success",
            "timestamp",
            "plan",
            "project_dir",
            "requested_backend",
            "resolved_backend",
            "task_count",
            "tasks",
            "files_changed",
            "files_changed_count",
            "validation_issues",
            "validation_issue_count",
            "failure_reason",
            "tests_passed",
            "cost_estimate",
            "duration_s",
            "total_duration_s",
        ):
            assert key in data, f"Missing top-level key: {key}"

        # Per-task keys
        task = data["tasks"][0]
        for key in (
            "name",
            "tool",
            "prompt_file",
            "success",
            "duration_s",
            "attempt_count",
            "fallbacks",
            "fallback_count",
            "fallback_chain",
            "failure_reason",
            "cost_estimate",
            "output",
            "attempts",
        ):
            assert key in task, f"Missing task key: {key}"

        # Per-issue keys
        issue = data["validation_issues"][0]
        for key in ("severity", "message", "check"):
            assert key in issue, f"Missing validation_issue key: {key}"

        # Per-attempt keys
        attempt = task["attempts"][0]
        for key in (
            "tool",
            "exit_code",
            "duration_s",
            "failure_reason",
            "cost_estimate",
            "output",
        ):
            assert key in attempt, f"Missing attempt key: {key}"
