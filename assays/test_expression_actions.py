"""Tests for expression action-dispatch consolidation."""
from unittest.mock import patch, MagicMock
import pytest

def test_unknown_action():
    from metabolon.enzymes.expression import expression
    result = expression(action="nonexistent")
    assert isinstance(result, str)
    assert "unknown" in result.lower() or "nonexistent" in result.lower()

@patch("metabolon.enzymes.expression._file_age_days")
@patch("metabolon.enzymes.expression._count_sparks")
@patch("metabolon.enzymes.expression.Path.exists")
def test_preflight_action(mock_exists, mock_count, mock_age):
    from metabolon.enzymes.expression import expression
    mock_exists.return_value = True
    mock_count.return_value = 5
    mock_age.return_value = 1.0
    
    result = expression(action="preflight")
    # Returns ForgePreflightResult
    assert hasattr(result, "ready")

@patch("metabolon.enzymes.expression._file_age_days")
@patch("metabolon.enzymes.expression.Path.exists")
@patch("metabolon.enzymes.expression.Path.iterdir")
def test_library_action(mock_iterdir, mock_exists, mock_age):
    from metabolon.enzymes.expression import expression
    mock_exists.return_value = True
    mock_iterdir.return_value = []
    mock_age.return_value = 1.0
    
    result = expression(action="library")
    # Returns ForgeLibraryResult
    assert hasattr(result, "totals")
