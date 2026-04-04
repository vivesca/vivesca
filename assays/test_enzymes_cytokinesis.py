"""Edge-case tests for metabolon.enzymes.cytokinesis."""

import json
from unittest.mock import patch

import pytest

from metabolon.enzymes.cytokinesis import CytoResult, cytokinesis
from metabolon.morphology import EffectorResult

# ---------------------------------------------------------------------------
# Empty / missing JSON fields
# ---------------------------------------------------------------------------


class TestEmptyAndPartialJson:
    """Handle edge cases in CLI JSON output."""

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_empty_json_object(self, mock_cli):
        """Empty JSON → no gates, data preserved, all_gates_passed=True (0 pending)."""
        mock_cli.return_value = (0, json.dumps({}))

        result = cytokinesis(action="gather")

        assert isinstance(result, CytoResult)
        assert result.gates == {}
        assert result.all_gates_passed is True  # 0 gates, 0 pending
        assert result.data == {}

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_missing_gates_key(self, mock_cli):
        """JSON without 'gates' key → empty gates dict via .get()."""
        data = {"summary": "no gates here"}
        mock_cli.return_value = (0, json.dumps(data))

        result = cytokinesis(action="gather")

        assert isinstance(result, CytoResult)
        assert result.gates == {}
        assert result.data == data

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_partial_json_fields(self, mock_cli):
        """JSON with gates but no other fields."""
        data = {"gates": {"memory": "PENDING"}}
        mock_cli.return_value = (0, json.dumps(data))

        result = cytokinesis(action="gather")

        assert isinstance(result, CytoResult)
        assert result.gates == {"memory": "PENDING"}
        assert result.all_gates_passed is False

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_verify_missing_all_passed_key(self, mock_cli):
        """verify JSON without 'all_passed' defaults to False."""
        data = {"gates": {"memory": "DONE"}}
        mock_cli.return_value = (0, json.dumps(data))

        result = cytokinesis(action="verify")

        assert isinstance(result, CytoResult)
        # all_passed missing → defaults to False, but no PENDING gates
        # The code checks data.get("all_passed", False) first
        assert result.all_gates_passed is False


# ---------------------------------------------------------------------------
# Subprocess exceptions from _run_cli
# ---------------------------------------------------------------------------


class TestSubprocessExceptions:
    """_run_cli catches exceptions and returns (1, error_string)."""

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_timeout_from_cli(self, mock_cli):
        """Timeout returns exit_code=1 and error text."""
        mock_cli.return_value = (1, "timed out after 90 seconds")

        result = cytokinesis(action="gather")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "gather failed" in result.message

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_file_not_found_from_cli(self, mock_cli):
        """FileNotFoundError returns exit_code=1 and error text."""
        mock_cli.return_value = (1, "No such file or directory: 'cytokinesis'")

        result = cytokinesis(action="gather")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "gather failed" in result.message


# ---------------------------------------------------------------------------
# Action case-insensitivity
# ---------------------------------------------------------------------------


class TestActionCaseInsensitivity:
    """action is .lower().strip() before matching."""

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_uppercase_gather(self, mock_cli):
        mock_cli.return_value = (0, json.dumps({"gates": {}}))

        result = cytokinesis(action="GATHER")

        assert isinstance(result, CytoResult)
        mock_cli.assert_called_once_with("gather")

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_padded_gather(self, mock_cli):
        mock_cli.return_value = (0, json.dumps({"gates": {}}))

        result = cytokinesis(action=" gather ")

        assert isinstance(result, CytoResult)
        mock_cli.assert_called_once_with("gather")

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_mixed_case_verify(self, mock_cli):
        data = {"gates": {"a": "DONE"}, "all_passed": True}
        mock_cli.return_value = (0, json.dumps(data))

        result = cytokinesis(action="Verify")

        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is True

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_uppercase_flush(self, mock_cli):
        mock_cli.return_value = (0, "done")

        result = cytokinesis(action="FLUSH")

        assert isinstance(result, CytoResult)
        mock_cli.assert_called_once_with("flush")


# ---------------------------------------------------------------------------
# CytoResult model validation
# ---------------------------------------------------------------------------


class TestCytoResultValidation:
    """Model field validation and edge cases."""

    def test_output_required(self):
        """output is a required field with no default."""
        with pytest.raises(ValueError):
            CytoResult()  # type: ignore[call-arg]

    def test_defaults_for_optional_fields(self):
        result = CytoResult(output="x")
        assert result.data == {}
        assert result.gates == {}
        assert result.all_gates_passed is False

    def test_extra_fields_allowed(self):
        """Secretion base has extra='allow'."""
        result = CytoResult(output="x", **{"custom_field": "val"})  # type: ignore[call-overload]
        assert result.custom_field == "val"

    def test_gates_accepts_various_statuses(self):
        result = CytoResult(
            output="test",
            gates={"a": "DONE", "b": "PENDING", "c": "SKIPPED"},
        )
        assert len(result.gates) == 3

    def test_data_accepts_nested_dict(self):
        result = CytoResult(
            output="test",
            data={"nested": {"deep": [1, 2, 3]}},
        )
        assert result.data["nested"]["deep"] == [1, 2, 3]


# ---------------------------------------------------------------------------
# Tool decorator attributes
# ---------------------------------------------------------------------------


class TestToolDecorator:
    """Verify the @tool decorator was applied correctly."""

    def test_tool_name(self):
        meta = cytokinesis.__fastmcp__
        assert meta.name == "cytokinesis"

    def test_tool_annotations(self):
        meta = cytokinesis.__fastmcp__
        assert meta.annotations.readOnlyHint is False
        assert meta.annotations.destructiveHint is False
