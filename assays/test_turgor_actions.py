"""Tests for tonus action-dispatch consolidation."""
from unittest.mock import patch, MagicMock
import pytest

def test_unknown_action():
    from metabolon.enzymes.turgor import tonus
    result = tonus(action="nonexistent")
    assert isinstance(result, str)
    assert "unknown" in result.lower() or "nonexistent" in result.lower()

@patch("metabolon.enzymes.turgor.TONUS_MD")
def test_status_action(mock_tonus):
    from metabolon.enzymes.turgor import tonus
    mock_tonus.exists.return_value = True
    mock_tonus.read_text.return_value = "tonus content"
    result = tonus(action="status")
    assert isinstance(result, str)

@patch("metabolon.enzymes.turgor.TONUS_MD")
def test_mark_action(mock_tonus):
    from metabolon.enzymes.turgor import tonus
    mock_tonus.exists.return_value = True
    mock_tonus.read_text.return_value = "tonus content"
    result = tonus(action="mark", item_status="done", description="test")
    assert isinstance(result, str)
