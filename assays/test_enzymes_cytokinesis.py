"""Additional edge-case tests for metabolon.enzymes.cytokinesis."""

from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.cytokinesis import CytoResult, cytokinesis
from metabolon.morphology import EffectorResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(returncode: int = 0, stdout: str = "", stderr: str = ""):
    return MagicMock(returncode=returncode, stdout=stdout, stderr=stderr)


def _gather_payload(**overrides) -> dict:
    base = {
        "repos": {},
        "skills": {},
        "memory": {"lines": 10, "limit": 150},
        "now": {"age_label": "fresh"},
        "rfts": [],
        "deps": [],
        "reflect": [],
        "methylation": [],
        "gates": {"gate_a": "DONE"},
    }
    base.update(overrides)
    return base


def _verify_payload(all_passed: bool = True, **overrides) -> dict:
    base = {
        "gates": {"gate_a": "DONE"},
        "all_passed": all_passed,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Gate counting edge cases
# ---------------------------------------------------------------------------

class TestGateCounting:
    """Edge cases for pending gate detection."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_no_gates_key(self, mock_run):
        mock_run.return_value = _run(stdout=json.dumps({"repos": {}}))
        result = cytokinesis("gather")
        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is True
        assert result.gates == {}

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_empty_gates(self, mock_run):
        mock_run.return_value = _run(stdout=json.dumps({"gates": {}}))
        result = cytokinesis("gather")
        assert result.all_gates_passed is True
        assert "0 pending" in result.output

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_multiple_pending_gates(self, mock_run):
        mock_run.return_value = _run(
            stdout=json.dumps({"gates": {"a": "PENDING", "b": "PENDING", "c": "DONE"}})
        )
        result = cytokinesis("gather")
        assert result.all_gates_passed is False
        assert "2 pending" in result.output

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_partial_pending_status(self, mock_run):
        """PENDING anywhere in the status string counts."""
        mock_run.return_value = _run(
            stdout=json.dumps({"gates": {"a": "STILL PENDING REVIEW"}})
        )
        result = cytokinesis("gather")
        assert result.all_gates_passed is False

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_verify_no_all_passed_key(self, mock_run):
        mock_run.return_value = _run(stdout=json.dumps({"gates": {"a": "DONE"}}))
        result = cytokinesis("verify")
        # all_passed defaults to False
        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is False
        assert "BLOCKED" in result.output


# ---------------------------------------------------------------------------
# Verify action edge cases
# ---------------------------------------------------------------------------

class TestVerifyEdgeCases:
    """Verify action edge cases."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_verify_all_passed_false_no_pending(self, mock_run):
        mock_run.return_value = _run(
            stdout=json.dumps({"gates": {"a": "DONE"}, "all_passed": False})
        )
        result = cytokinesis("verify")
        assert result.all_gates_passed is False
        assert "BLOCKED" in result.output

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_verify_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="cytokinesis", timeout=90)
        # _run_cli catches and returns (1, str(exc)), then verify tries json.loads
        # which fails → EffectorResult
        result = cytokinesis("verify")
        assert isinstance(result, EffectorResult)
        assert result.success is False


# ---------------------------------------------------------------------------
# Flush action edge cases
# ---------------------------------------------------------------------------

class TestFlushEdgeCases:
    """Flush action edge cases."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_flush_nonzero_exit(self, mock_run):
        mock_run.return_value = _run(returncode=1, stdout="error msg")
        result = cytokinesis("flush")
        assert isinstance(result, CytoResult)
        assert result.output == "error msg"
        assert result.data == {"exit_code": 1}

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_flush_whitespace_only(self, mock_run):
        mock_run.return_value = _run(stdout="   \n  ")
        result = cytokinesis("flush")
        assert result.output == "flushed"


# ---------------------------------------------------------------------------
# Wrap action edge cases
# ---------------------------------------------------------------------------

class TestWrapEdgeCases:
    """Wrap action edge cases."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_wrap_verify_returns_pending(self, mock_run):
        mock_run.side_effect = [
            _run(stdout=json.dumps(_gather_payload())),
            _run(
                stdout=json.dumps(
                    _verify_payload(
                        all_passed=False,
                        gates={"a": "PENDING", "b": "PENDING"},
                    )
                )
            ),
        ]
        result = cytokinesis("wrap")
        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is False
        assert "CANNOT WRAP" in result.output
        assert "a" in result.output
        assert "b" in result.output

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_wrap_gather_data_in_result(self, mock_run):
        gather_data = _gather_payload(repos={"r": {"clean": True}})
        mock_run.side_effect = [
            _run(stdout=json.dumps(gather_data)),
            _run(stdout=json.dumps(_verify_payload(all_passed=True))),
        ]
        result = cytokinesis("wrap")
        assert result.data == gather_data


# ---------------------------------------------------------------------------
# Action case handling
# ---------------------------------------------------------------------------

class TestActionCaseHandling:
    """Actions should be case-insensitive and stripped."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_uppercase_action(self, mock_run):
        mock_run.return_value = _run(stdout=json.dumps(_gather_payload()))
        result = cytokinesis("GATHER")
        assert isinstance(result, CytoResult)

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_action_with_spaces(self, mock_run):
        mock_run.return_value = _run(stdout=json.dumps(_gather_payload()))
        result = cytokinesis("  gather  ")
        assert isinstance(result, CytoResult)

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_default_action_is_gather(self, mock_run):
        mock_run.return_value = _run(stdout=json.dumps(_gather_payload()))
        result = cytokinesis()
        assert isinstance(result, CytoResult)


# ---------------------------------------------------------------------------
# Tool decorator attributes
# ---------------------------------------------------------------------------

class TestToolDecorator:
    """Verify the @tool decorator was applied correctly."""

    def test_tool_name(self):
        meta = cytokinesis.__fastmcp__
        assert meta.name == "cytokinesis"

    def test_tool_not_readonly(self):
        ann = cytokinesis.__fastmcp__.annotations
        assert ann.readOnlyHint is False
        assert ann.destructiveHint is False
