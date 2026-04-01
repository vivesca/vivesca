from __future__ import annotations

import json
import subprocess
from unittest.mock import patch, Mock

import pytest

from metabolon.enzymes.polarization import (
    polarization,
    _preflight,
    _guard,
    PolarizationPreflightResult,
    EffectorResult,
    _CLI,
)


def test_polarization_unknown_action():
    """Test unknown action returns error."""
    result = polarization(action="unknown")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "Unknown action" in result.message


def test_preflight_cli_not_found():
    """Test preflight when CLI is not found."""
    with patch("metabolon.enzymes.polarization.shutil.which", return_value=None):
        result = _preflight()
        assert isinstance(result, PolarizationPreflightResult)
        assert f"{_CLI} not found" in result.summary
        assert "error" in result.data


def test_preflight_timeout():
    """Test preflight timeout handling."""
    with patch("metabolon.enzymes.polarization.shutil.which", return_value="/usr/bin/polarization-gather"):
        with patch("metabolon.enzymes.polarization.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="", timeout=30)):
            result = _preflight()
            assert "timed out" in result.summary
            assert result.data["error"] == "timeout"


def test_preflight_non_zero_exit():
    """Test preflight handles non-zero exit code."""
    mock_process = Mock()
    mock_process.returncode = 1
    mock_process.stdout = ""
    mock_process.stderr = "some error"

    with patch("metabolon.enzymes.polarization.shutil.which", return_value="/usr/bin/polarization-gather"):
        with patch("metabolon.enzymes.polarization.subprocess.run", return_value=mock_process):
            result = _preflight()
            assert "preflight failed" in result.summary
            assert result.data["error"] == "some error"


def test_preflight_valid_json():
    """Test preflight with valid JSON output."""
    test_data = {
        "consumption_gb": 12.5,
        "north_stars": 3,
        "guard_active": False,
        "budget_remaining_pct": 75,
    }
    mock_process = Mock()
    mock_process.returncode = 0
    mock_process.stdout = json.dumps(test_data)
    mock_process.stderr = ""

    with patch("metabolon.enzymes.polarization.shutil.which", return_value="/usr/bin/polarization-gather"):
        with patch("metabolon.enzymes.polarization.subprocess.run", return_value=mock_process):
            result = _preflight()
            assert result.raw == json.dumps(test_data)
            assert result.data == test_data
            assert "Polarization pre-flight:" in result.summary
            assert "consumption_gb: 12.5" in result.summary
            assert "guard_active: False" in result.summary


def test_preflight_invalid_json():
    """Test preflight handles invalid JSON output gracefully."""
    mock_process = Mock()
    mock_process.returncode = 0
    mock_process.stdout = "plain text output"
    mock_process.stderr = ""

    with patch("metabolon.enzymes.polarization.shutil.which", return_value="/usr/bin/polarization-gather"):
        with patch("metabolon.enzymes.polarization.subprocess.run", return_value=mock_process):
            result = _preflight()
            assert result.raw == "plain text output"
            assert result.data == {"raw_text": "plain text output"}
            assert result.summary == "plain text output"


def test_guard_invalid_action():
    """Test guard rejects invalid action."""
    result = _guard("invalid")
    assert not result.success
    assert "Invalid guard_action" in result.message


def test_guard_cli_not_found():
    """Test guard when CLI not found."""
    with patch("metabolon.enzymes.polarization.shutil.which", return_value=None):
        result = _guard("on")
        assert not result.success
        assert f"'{_CLI}' not found" in result.message


def test_guard_timeout():
    """Test guard timeout handling."""
    with patch("metabolon.enzymes.polarization.shutil.which", return_value="/usr/bin/polarization-gather"):
        with patch("metabolon.enzymes.polarization.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="", timeout=10)):
            result = _guard("on")
            assert not result.success
            assert "timed out" in result.message


def test_guard_non_zero_exit():
    """Test guard handles non-zero exit."""
    mock_process = Mock()
    mock_process.returncode = 2
    mock_process.stdout = "oops"
    mock_process.stderr = ""

    with patch("metabolon.enzymes.polarization.shutil.which", return_value="/usr/bin/polarization-gather"):
        with patch("metabolon.enzymes.polarization.subprocess.run", return_value=mock_process):
            result = _guard("off")
            assert not result.success
            assert "guard off failed (exit 2): oops" in result.message
            assert result.data["action"] == "off"


def test_guard_success_on():
    """Test guard activation succeeds."""
    mock_process = Mock()
    mock_process.returncode = 0
    mock_process.stdout = ""
    mock_process.stderr = ""

    with patch("metabolon.enzymes.polarization.shutil.which", return_value="/usr/bin/polarization-gather"):
        with patch("metabolon.enzymes.polarization.subprocess.run", return_value=mock_process):
            result = _guard("ON")
            assert result.success
            assert "activated" in result.message
            assert result.data["guard_state"] == "on"


def test_guard_success_off():
    """Test guard deactivation succeeds."""
    mock_process = Mock()
    mock_process.returncode = 0
    mock_process.stdout = ""
    mock_process.stderr = ""

    with patch("metabolon.enzymes.polarization.shutil.which", return_value="/usr/bin/polarization-gather"):
        with patch("metabolon.enzymes.polarization.subprocess.run", return_value=mock_process):
            result = _guard("  off  ")
            assert result.success
            assert "deactivated" in result.message
            assert result.data["guard_state"] == "off"


def test_polarization_dispatch_preflight():
    """Test polarization dispatches to preflight."""
    with patch("metabolon.enzymes.polarization._preflight", return_value=PolarizationPreflightResult(raw="", data={}, summary="test")):
        result = polarization(action="preflight")
        assert isinstance(result, PolarizationPreflightResult)
        assert result.summary == "test"


def test_polarization_dispatch_guard():
    """Test polarization dispatches to guard."""
    with patch("metabolon.enzymes.polarization._guard", return_value=EffectorResult(success=True, message="ok")):
        result = polarization(action="guard", guard_action="on")
        assert isinstance(result, EffectorResult)
        assert result.success
        assert result.message == "ok"
