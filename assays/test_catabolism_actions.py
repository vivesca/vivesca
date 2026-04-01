"""Tests for catabolism action-dispatch consolidation."""
from unittest.mock import patch
import pytest


def test_catabolism_actions_unknown_action():
    from metabolon.enzymes.catabolism import catabolism, CatabolismConfirmResult
    result = catabolism(action="nonexistent")
    assert isinstance(result, CatabolismConfirmResult)
    assert not result.success
    assert "unknown" in result.message.lower()


@patch("metabolon.enzymes.catabolism._spending")
def test_spending_action(mock_spending):
    from metabolon.enzymes.catabolism import catabolism
    mock_spending.return_value = "spending summary"
    result = catabolism(action="spending")
    assert result == "spending summary"
    mock_spending.assert_called_once()


@patch("metabolon.enzymes.catabolism._confirm")
def test_confirm_action(mock_confirm):
    from metabolon.enzymes.catabolism import catabolism
    mock_confirm.return_value = "confirm summary"
    result = catabolism(action="confirm")
    assert result == "confirm summary"
    mock_confirm.assert_called_once()
