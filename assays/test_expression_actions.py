"""Tests for expression action-dispatch consolidation."""
from unittest.mock import patch, MagicMock
import pytest

def test_unknown_action():
    from metabolon.enzymes.expression import expression
    result = expression(action="nonexistent")
    assert isinstance(result, str)
    assert "unknown" in result.lower() or "nonexistent" in result.lower()

@patch("metabolon.enzymes.expression.Path.exists")
@patch("metabolon.enzymes.expression.Path.glob")
def test_preflight_action(mock_glob, mock_exists):
    from metabolon.enzymes.expression import expression
    mock_exists.return_value = True
    mock_glob.return_value = []
    result = expression(action="preflight")
    assert isinstance(result, str)

@patch("metabolon.enzymes.expression.Path.exists")
@patch("metabolon.enzymes.expression.Path.iterdir")
def test_library_action(mock_iterdir, mock_exists):
    from metabolon.enzymes.expression import expression
    mock_exists.return_value = True
    mock_iterdir.return_value = []
    result = expression(action="library")
    assert isinstance(result, str)
