"""Tests for differentiation action-dispatch consolidation."""
from unittest.mock import patch, MagicMock
import pytest

def test_unknown_action():
    from metabolon.enzymes.differentiation import differentiation
    result = differentiation(action="nonexistent")
    assert isinstance(result, str)
    assert "unknown" in result.lower() or "nonexistent" in result.lower()

@patch("metabolon.enzymes.differentiation.GYM_LOGS_DIR")
def test_latest_log_action(mock_logs_dir):
    from metabolon.enzymes.differentiation import differentiation
    mock_logs_dir.exists.return_value = True
    mock_file = MagicMock()
    mock_file.read_text.return_value = "log content"
    mock_logs_dir.glob.return_value = [mock_file]
    result = differentiation(action="latest_log")
    assert isinstance(result, str)

@patch("metabolon.enzymes.differentiation.chemoreceptor.readiness")
def test_readiness_action(mock_readiness):
    from metabolon.enzymes.differentiation import differentiation
    mock_readiness.return_value = "readiness content"
    result = differentiation(action="readiness")
    assert isinstance(result, str)

@patch("metabolon.enzymes.differentiation.GYM_LOGS_DIR")
def test_write_log_action(mock_logs_dir):
    from metabolon.enzymes.differentiation import differentiation
    mock_logs_dir.exists.return_value = True
    result = differentiation(action="write_log", session_date="2026-03-30", content="test")
    assert isinstance(result, str)
