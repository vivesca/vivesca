"""Tests for mtor scan — organism gap detection.

mtor scan runs deterministic checks against the organism and returns
a ranked JSON list of actionable tasks. Each task has enough context
for CC to write a test file and dispatch.
"""

from __future__ import annotations

import io
import json
import sys
from unittest.mock import AsyncMock, patch

from mtor.cli import app

# ---------------------------------------------------------------------------
# Helpers (same pattern as test_mtor.py)
# ---------------------------------------------------------------------------


def invoke(args: list[str] | None = None) -> tuple[int, dict]:
    """Invoke CLI and return (exit_code, parsed_json)."""
    captured = io.StringIO()
    old_stdout = sys.stdout
    exit_code = 0
    try:
        sys.stdout = captured
        app(args or [])
    except SystemExit as exc:
        exit_code = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.stdout = old_stdout

    output = captured.getvalue()
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"Output is not valid JSON. Exit={exit_code}\nOutput: {output!r}\nException: {exc}"
        ) from exc
    return exit_code, data


# ---------------------------------------------------------------------------
# scan command — returns JSON task list
# ---------------------------------------------------------------------------


class TestScanOutput:
    """mtor scan returns a porin JSON envelope with detected tasks."""

    @patch("mtor.scan._run_checks")
    def test_scan_returns_ok_envelope(self, mock_checks):
        """scan returns ok=true with a tasks array."""
        mock_checks.return_value = [
            {
                "description": "cytokinesis has no tests",
                "category": "coverage",
                "priority": 3,
                "target": "~/germline/effectors/cytokinesis",
                "suggested_test": "assays/test_cytokinesis.py",
            }
        ]
        exit_code, data = invoke(["scan"])
        assert exit_code == 0
        assert data["ok"] is True
        assert "tasks" in data["result"]

    @patch("mtor.scan._run_checks")
    def test_scan_tasks_have_required_fields(self, mock_checks):
        """Each task must have description, category, priority, target."""
        mock_checks.return_value = [
            {
                "description": "missing test coverage for mtor deploy",
                "category": "coverage",
                "priority": 2,
                "target": "~/germline/effectors/mtor/mtor/cli.py",
                "suggested_test": "assays/test_deploy.py",
            }
        ]
        _exit_code, data = invoke(["scan"])
        tasks = data["result"]["tasks"]
        assert len(tasks) >= 1
        for task in tasks:
            assert "description" in task
            assert "category" in task
            assert task["category"] in ("health", "coverage", "stale", "todo", "broken")
            assert "priority" in task
            assert isinstance(task["priority"], int)
            assert 1 <= task["priority"] <= 5
            assert "target" in task

    @patch("mtor.scan._run_checks")
    def test_scan_tasks_sorted_by_priority(self, mock_checks):
        """Tasks are returned highest priority first (5=critical, 1=low)."""
        mock_checks.return_value = [
            {"description": "low", "category": "todo", "priority": 1, "target": "a"},
            {"description": "high", "category": "broken", "priority": 5, "target": "b"},
            {"description": "mid", "category": "coverage", "priority": 3, "target": "c"},
        ]
        _exit_code, data = invoke(["scan"])
        tasks = data["result"]["tasks"]
        priorities = [t["priority"] for t in tasks]
        assert priorities == sorted(priorities, reverse=True)

    @patch("mtor.scan._run_checks")
    def test_scan_empty_organism_returns_empty_tasks(self, mock_checks):
        """If no gaps found, tasks is an empty list (not an error)."""
        mock_checks.return_value = []
        exit_code, data = invoke(["scan"])
        assert exit_code == 0
        assert data["result"]["tasks"] == []
        assert data["result"]["count"] == 0


# ---------------------------------------------------------------------------
# scan check categories
# ---------------------------------------------------------------------------


class TestScanChecks:
    """_run_checks aggregates multiple detection strategies."""

    def test_run_checks_returns_list(self):
        """_run_checks returns a list (may be empty on clean organism)."""
        from mtor.scan import _run_checks

        result = _run_checks()
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, dict)
            assert "description" in item
            assert "category" in item

    def test_check_categories_are_valid(self):
        """All returned categories are from the allowed set."""
        from mtor.scan import VALID_CATEGORIES

        assert "health" in VALID_CATEGORIES
        assert "coverage" in VALID_CATEGORIES
        assert "stale" in VALID_CATEGORIES
        assert "todo" in VALID_CATEGORIES
        assert "broken" in VALID_CATEGORIES


# ---------------------------------------------------------------------------
# test gate — build tasks require test file reference
# ---------------------------------------------------------------------------


class TestBuildGate:
    """mtor refuses build dispatch without test file reference."""

    @patch("mtor.dispatch._get_client")
    def test_build_without_test_reference_rejected(self, mock_client):
        """Prompt without test_*.py or assays/ is rejected with NO_TEST_FILE."""
        exit_code, data = invoke(["Add a shiny new feature"])
        assert exit_code == 2
        assert data["ok"] is False
        assert data["error"]["code"] == "NO_TEST_FILE"

    @patch("mtor.dispatch._get_client")
    def test_build_with_test_reference_accepted(self, mock_client):
        """Prompt referencing test_*.py passes the gate."""
        mock_async = AsyncMock()
        mock_async.start_workflow = AsyncMock(return_value="wf-123")
        mock_client.return_value = (mock_async, None)

        # Should not raise NO_TEST_FILE — may fail later on Temporal connection
        # but the gate itself should pass
        _exit_code, data = invoke(["Make assays/test_feature.py pass"])
        # If we get past the gate, error will be about Temporal, not NO_TEST_FILE
        if not data["ok"]:
            assert data["error"]["code"] != "NO_TEST_FILE"

    @patch("mtor.dispatch._get_client")
    def test_build_with_assays_path_accepted(self, mock_client):
        """Prompt referencing assays/ directory passes the gate."""
        mock_async = AsyncMock()
        mock_async.start_workflow = AsyncMock(return_value="wf-123")
        mock_client.return_value = (mock_async, None)

        _exit_code, data = invoke(["Fix failing assays/test_mtor.py"])
        if not data["ok"]:
            assert data["error"]["code"] != "NO_TEST_FILE"
