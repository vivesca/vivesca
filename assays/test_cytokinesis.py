"""Tests for metabolon.enzymes.cytokinesis — all 4 actions."""

from __future__ import annotations

import json
from unittest.mock import patch

from metabolon.enzymes.cytokinesis import CytoResult, cytokinesis
from metabolon.morphology import EffectorResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gates_payload(gates: dict, **extras) -> str:
    """Build JSON with gates dict."""
    data = {"gates": gates, **extras}
    return json.dumps(data)


# ---------------------------------------------------------------------------
# gather action — success
# ---------------------------------------------------------------------------


class TestGatherSuccess:
    """gather action with valid CLI output."""

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_gather_all_passed(self, mock_cli):
        gates = {"memory": "DONE", "repos": "DONE", "g1": "DONE"}
        mock_cli.return_value = (0, _gates_payload(gates))

        result = cytokinesis(action="gather")

        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is True
        assert result.gates == gates
        assert "3 gates" in result.output
        assert "0 pending" in result.output
        mock_cli.assert_called_once_with("gather")

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_gather_with_pending(self, mock_cli):
        gates = {"memory": "DONE", "repos": "PENDING", "g1": "PENDING"}
        mock_cli.return_value = (0, _gates_payload(gates))

        result = cytokinesis(action="gather")

        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is False
        assert "2 pending" in result.output


# ---------------------------------------------------------------------------
# gather action — failure
# ---------------------------------------------------------------------------


class TestGatherFailure:
    """gather action when CLI fails."""

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_gather_cli_failure(self, mock_cli):
        mock_cli.return_value = (1, "command not found")

        result = cytokinesis(action="gather")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "gather failed" in result.message

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_gather_bad_json(self, mock_cli):
        mock_cli.return_value = (0, "not json {{{")

        result = cytokinesis(action="gather")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "invalid JSON" in result.message


# ---------------------------------------------------------------------------
# verify action
# ---------------------------------------------------------------------------


class TestVerify:
    """verify action paths."""

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_verify_all_passed(self, mock_cli):
        gates = {"memory": "DONE", "repos": "DONE"}
        data = {"gates": gates, "all_passed": True}
        mock_cli.return_value = (0, json.dumps(data))

        result = cytokinesis(action="verify")

        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is True
        assert "All gates passed" in result.output
        mock_cli.assert_called_once_with("verify")

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_verify_pending_gates(self, mock_cli):
        gates = {"memory": "DONE", "repos": "PENDING"}
        data = {"gates": gates, "all_passed": False}
        mock_cli.return_value = (0, json.dumps(data))

        result = cytokinesis(action="verify")

        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is False
        assert "BLOCKED" in result.output
        assert "repos" in result.output


# ---------------------------------------------------------------------------
# flush action
# ---------------------------------------------------------------------------


class TestFlush:
    """flush action paths."""

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_flush_returns_output(self, mock_cli):
        mock_cli.return_value = (0, "committed 3 repos\n")

        result = cytokinesis(action="flush")

        assert isinstance(result, CytoResult)
        assert result.output == "committed 3 repos"
        assert result.data == {"exit_code": 0}
        mock_cli.assert_called_once_with("flush")

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_flush_empty_output(self, mock_cli):
        mock_cli.return_value = (0, "")

        result = cytokinesis(action="flush")

        assert isinstance(result, CytoResult)
        assert result.output == "flushed"


# ---------------------------------------------------------------------------
# wrap action
# ---------------------------------------------------------------------------


class TestWrap:
    """wrap action — gather + verify combined."""

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_wrap_all_passed(self, mock_cli):
        gather_data = {"gates": {"memory": "DONE"}, "summary": "ok"}
        verify_data = {"gates": {"memory": "DONE"}, "all_passed": True}
        mock_cli.side_effect = [
            (0, json.dumps(gather_data)),
            (0, json.dumps(verify_data)),
        ]

        result = cytokinesis(action="wrap")

        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is True
        assert "wrapped" in result.output.lower()
        assert mock_cli.call_count == 2
        mock_cli.assert_any_call("gather", ["--fast"])
        mock_cli.assert_any_call("verify")

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_wrap_gather_fails(self, mock_cli):
        mock_cli.return_value = (1, "gather error")

        result = cytokinesis(action="wrap")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "gather failed" in result.message

    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_wrap_verify_has_pending(self, mock_cli):
        gather_data = {"gates": {"memory": "DONE"}}
        verify_data = {"gates": {"memory": "DONE", "repos": "PENDING"}, "all_passed": False}
        mock_cli.side_effect = [
            (0, json.dumps(gather_data)),
            (0, json.dumps(verify_data)),
        ]

        result = cytokinesis(action="wrap")

        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is False
        assert "CANNOT WRAP" in result.output
        assert "repos" in result.output


# ---------------------------------------------------------------------------
# unknown action
# ---------------------------------------------------------------------------


class TestUnknownAction:
    @patch("metabolon.enzymes.cytokinesis._run_cli")
    def test_unknown_action(self, mock_cli):
        result = cytokinesis(action="explode")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "Unknown action" in result.message
        mock_cli.assert_not_called()


# ---------------------------------------------------------------------------
# CytoResult model defaults
# ---------------------------------------------------------------------------


class TestCytoResultDefaults:
    def test_defaults(self):
        result = CytoResult(output="test")
        assert result.data == {}
        assert result.gates == {}
        assert result.all_gates_passed is False
        assert result.output == "test"

    def test_is_secretion_subclass(self):
        from metabolon.morphology import Secretion

        assert issubclass(CytoResult, Secretion)
