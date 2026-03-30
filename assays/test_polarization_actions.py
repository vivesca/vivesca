"""Tests for polarization action-dispatch consolidation."""
from unittest.mock import patch
import pytest

def test_unknown_action():
    from metabolon.enzymes.polarization import polarization
    result = polarization(action="nonexistent")
    assert isinstance(result, str)
    assert "unknown" in result.lower() or "nonexistent" in result.lower()

@patch("metabolon.enzymes.polarization.subprocess.run")
def test_preflight_action(mock_run):
    from metabolon.enzymes.polarization import polarization
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "preflight result"
    result = polarization(action="preflight")
    assert isinstance(result, str)

@patch("metabolon.enzymes.polarization.subprocess.run")
def test_guard_action(mock_run):
    from metabolon.enzymes.polarization import polarization
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "guard result"
    result = polarization(action="guard", guard_action="status")
    assert isinstance(result, str)
