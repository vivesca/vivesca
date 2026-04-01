"""Tests for auscultation action-dispatch consolidation."""
from unittest.mock import patch, MagicMock
import pytest

def test_auscultation_actions_unknown_action():
    from metabolon.enzymes.auscultation import auscultation
    result = auscultation(action="nonexistent")
    assert isinstance(result, str)
    assert "unknown" in result.lower() or "nonexistent" in result.lower()

@patch("metabolon.enzymes.auscultation._glob_logs")
@patch("metabolon.enzymes.auscultation._read_log_lines")
def test_logs_action(mock_read, mock_glob):
    from metabolon.enzymes.auscultation import auscultation
    mock_glob.return_value = [MagicMock()]
    mock_read.return_value = ["line1", "line2"]
    result = auscultation(action="logs", log_name="test")
    assert isinstance(result, str)

@patch("metabolon.enzymes.auscultation._glob_logs")
@patch("metabolon.enzymes.auscultation._read_log_lines")
def test_errors_action(mock_read, mock_glob):
    from metabolon.enzymes.auscultation import auscultation
    mock_glob.return_value = [MagicMock()]
    mock_read.return_value = ["error1", "error2"]
    result = auscultation(action="errors", log_name="test")
    assert isinstance(result, str)
