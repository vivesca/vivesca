"""Tests for polarization action-dispatch consolidation."""
from unittest.mock import patch
import pytest


def test_polarization_actions_unknown_action():
    from metabolon.enzymes.polarization import polarization, EffectorResult
    result = polarization(action="nonexistent")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "unknown" in result.message.lower()


@patch("metabolon.enzymes.polarization.subprocess.run")
def test_preflight_action(mock_run):
    from metabolon.enzymes.polarization import polarization, PolarizationPreflightResult
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = '{"budget": "ok"}'
    result = polarization(action="preflight")
    assert isinstance(result, PolarizationPreflightResult)


@patch("metabolon.enzymes.polarization.subprocess.run")
def test_guard_action(mock_run):
    from metabolon.enzymes.polarization import polarization, EffectorResult
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "guard activated"
    result = polarization(action="guard", guard_action="on")
    assert isinstance(result, EffectorResult)
    assert result.success is True
