"""Tests for catabolism action-dispatch consolidation."""
from unittest.mock import patch
import pytest

def test_unknown_action():
    from metabolon.enzymes.catabolism import catabolism
    result = catabolism(action="nonexistent")
    assert isinstance(result, str)
    assert "unknown" in result.lower() or "nonexistent" in result.lower()

@patch("metabolon.enzymes.catabolism._spending")
def test_spending_action(mock_spending):
    from metabolon.enzymes.catabolism import catabolism
    mock_spending.return_value = "spending summary"
    result = catabolism(action="spending")
    assert isinstance(result, str)
    mock_spending.assert_called_once()

@patch("metabolon.enzymes.catabolism._confirm")
def test_confirm_action(mock_confirm):
    from metabolon.enzymes.catabolism import catabolism
    mock_confirm.return_value = "confirm summary"
    result = catabolism(action="confirm")
    assert isinstance(result, str)
    mock_confirm.assert_called_once()
