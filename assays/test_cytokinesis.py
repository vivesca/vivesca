"""Tests for metabolon.enzymes.cytokinesis — session consolidation tool."""

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

def _mock_completed(returncode: int = 0, stdout: str = "", stderr: str = ""):
    """Build a fake CompletedProcess."""
    return MagicMock(
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _gather_payload(**overrides) -> dict:
    """Minimal successful cytokinesis gather JSON with no pending gates."""
    base = {
        "repos": {},
        "skills": {},
        "memory": {"lines": 10, "limit": 150},
        "now": {"age_label": "fresh"},
        "rfts": [],
        "deps": [],
        "reflect": [],
        "methylation": [],
        "gates": {"gate_a": "DONE", "gate_b": "DONE"},
    }
    base.update(overrides)
    return base


def _verify_payload(all_passed: bool = True, **overrides) -> dict:
    """Minimal verify JSON payload."""
    base = {
        "gates": {"gate_a": "DONE", "gate_b": "DONE"},
        "all_passed": all_passed,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Gather action
# ---------------------------------------------------------------------------

class TestGatherAction:
    """Tests for action='gather'."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_all_gates_passed(self, mock_run):
        payload = _gather_payload()
        mock_run.return_value = _mock_completed(stdout=json.dumps(payload))

        result = cytokinesis("gather")

        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is True
        assert result.gates == {"gate_a": "DONE", "gate_b": "DONE"}
        assert "0 pending" in result.output

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_pending_gates(self, mock_run):
        payload = _gather_payload(gates={"gate_a": "DONE", "gate_b": "PENDING"})
        mock_run.return_value = _mock_completed(stdout=json.dumps(payload))

        result = cytokinesis("gather")

        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is False
        assert "1 pending" in result.output

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_subprocess_args(self, mock_run):
        mock_run.return_value = _mock_completed(stdout=json.dumps(_gather_payload()))

        cytokinesis("gather")

        mock_run.assert_called_once_with(
            ["cytokinesis", "gather"],
            capture_output=True,
            text=True,
            timeout=90,
        )

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_data_forwarded(self, mock_run):
        payload = _gather_payload(repos={"r": {"clean": True}})
        mock_run.return_value = _mock_completed(stdout=json.dumps(payload))

        result = cytokinesis("gather")

        assert isinstance(result, CytoResult)
        assert result.data == payload


# ---------------------------------------------------------------------------
# Verify action
# ---------------------------------------------------------------------------

class TestVerifyAction:
    """Tests for action='verify'."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_all_passed(self, mock_run):
        mock_run.return_value = _mock_completed(
            stdout=json.dumps(_verify_payload(all_passed=True))
        )

        result = cytokinesis("verify")

        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is True
        assert "All gates passed" in result.output

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_gates_pending(self, mock_run):
        mock_run.return_value = _mock_completed(
            stdout=json.dumps(
                _verify_payload(
                    all_passed=False,
                    gates={"gate_a": "DONE", "gate_b": "PENDING"},
                )
            )
        )

        result = cytokinesis("verify")

        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is False
        assert "BLOCKED" in result.output
        assert "gate_b" in result.output

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_subprocess_args(self, mock_run):
        mock_run.return_value = _mock_completed(
            stdout=json.dumps(_verify_payload())
        )

        cytokinesis("verify")

        mock_run.assert_called_once_with(
            ["cytokinesis", "verify"],
            capture_output=True,
            text=True,
            timeout=90,
        )


# ---------------------------------------------------------------------------
# Flush action
# ---------------------------------------------------------------------------

class TestFlushAction:
    """Tests for action='flush'."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_flush_success(self, mock_run):
        mock_run.return_value = _mock_completed(stdout="flushed output\n")

        result = cytokinesis("flush")

        assert isinstance(result, CytoResult)
        assert result.output == "flushed output"
        assert result.data == {"exit_code": 0}

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_flush_empty_stdout(self, mock_run):
        mock_run.return_value = _mock_completed(stdout="")

        result = cytokinesis("flush")

        assert isinstance(result, CytoResult)
        assert result.output == "flushed"


# ---------------------------------------------------------------------------
# Wrap action
# ---------------------------------------------------------------------------

class TestWrapAction:
    """Tests for action='wrap'."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_wrap_success(self, mock_run):
        gather_data = _gather_payload()
        verify_data = _verify_payload(all_passed=True)
        mock_run.side_effect = [
            _mock_completed(stdout=json.dumps(gather_data)),
            _mock_completed(stdout=json.dumps(verify_data)),
        ]

        result = cytokinesis("wrap")

        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is True
        assert "Session wrapped" in result.output
        assert result.data == gather_data

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_wrap_pending_gates(self, mock_run):
        gather_data = _gather_payload()
        verify_data = _verify_payload(
            all_passed=False,
            gates={"gate_a": "DONE", "gate_b": "PENDING"},
        )
        mock_run.side_effect = [
            _mock_completed(stdout=json.dumps(gather_data)),
            _mock_completed(stdout=json.dumps(verify_data)),
        ]

        result = cytokinesis("wrap")

        assert isinstance(result, CytoResult)
        assert result.all_gates_passed is False
        assert "CANNOT WRAP" in result.output

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_wrap_uses_fast_flag(self, mock_run):
        gather_data = _gather_payload()
        verify_data = _verify_payload(all_passed=True)
        mock_run.side_effect = [
            _mock_completed(stdout=json.dumps(gather_data)),
            _mock_completed(stdout=json.dumps(verify_data)),
        ]

        cytokinesis("wrap")

        # First call is gather with --fast
        first_call = mock_run.call_args_list[0]
        assert first_call[0][0] == ["cytokinesis", "gather", "--fast"]
        # Second call is verify
        second_call = mock_run.call_args_list[1]
        assert second_call[0][0] == ["cytokinesis", "verify"]


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

class TestErrorPaths:
    """Error handling across actions."""

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_gather_nonzero_exit(self, mock_run):
        mock_run.return_value = _mock_completed(returncode=1, stderr="oops")

        result = cytokinesis("gather")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "gather failed" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_gather_bad_json(self, mock_run):
        mock_run.return_value = _mock_completed(stdout="not json {{{")

        result = cytokinesis("gather")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "invalid JSON" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_gather_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="cytokinesis", timeout=90)

        result = cytokinesis("gather")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "gather failed" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_gather_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError("cytokinesis not found")

        result = cytokinesis("gather")

        assert isinstance(result, EffectorResult)
        assert result.success is False

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_verify_bad_json(self, mock_run):
        mock_run.return_value = _mock_completed(stdout="bad")

        result = cytokinesis("verify")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "invalid JSON" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_wrap_gather_fails(self, mock_run):
        mock_run.return_value = _mock_completed(returncode=1)

        result = cytokinesis("wrap")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "gather failed" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_wrap_gather_bad_json(self, mock_run):
        mock_run.side_effect = [
            _mock_completed(stdout="not json"),
            _mock_completed(stdout=json.dumps(_verify_payload())),
        ]

        result = cytokinesis("wrap")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "gather returned invalid JSON" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_wrap_verify_bad_json(self, mock_run):
        mock_run.side_effect = [
            _mock_completed(stdout=json.dumps(_gather_payload())),
            _mock_completed(stdout="not json"),
        ]

        result = cytokinesis("wrap")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "verify returned invalid JSON" in result.message

    @patch("metabolon.enzymes.cytokinesis.subprocess.run")
    def test_unknown_action(self, mock_run):
        result = cytokinesis("explode")

        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "Unknown action" in result.message


# ---------------------------------------------------------------------------
# CytoResult model
# ---------------------------------------------------------------------------

class TestCytoResultModel:
    """Verify CytoResult defaults and field types."""

    def test_defaults(self):
        r = CytoResult(output="test")
        assert r.data == {}
        assert r.gates == {}
        assert r.all_gates_passed is False

    def test_output_required(self):
        with pytest.raises(Exception):
            CytoResult()

    def test_full_construction(self):
        r = CytoResult(
            output="msg",
            data={"k": "v"},
            gates={"g": "DONE"},
            all_gates_passed=True,
        )
        assert r.output == "msg"
        assert r.data == {"k": "v"}
        assert r.gates == {"g": "DONE"}
        assert r.all_gates_passed is True

    def test_is_secretion_subclass(self):
        from metabolon.morphology import Secretion

        assert issubclass(CytoResult, Secretion)
