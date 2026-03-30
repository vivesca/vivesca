"""Tests for tonus action-dispatch consolidation."""
from unittest.mock import patch
import pytest


def test_unknown_action():
    from metabolon.enzymes.turgor import tonus
    result = tonus(action="nonexistent")
    assert isinstance(result, dict)
    assert not result.get("success", True)
    assert "unknown" in result.get("message", "").lower()


@patch("metabolon.enzymes.turgor.TONUS")
def test_status_action(mock_tonus):
    from metabolon.enzymes.turgor import tonus
    mock_tonus.exists.return_value = True
    mock_tonus.read_text.return_value = "- [done] **Task A.** completed item\n- [in-progress] **Task B.** working on it"
    result = tonus(action="status")
    assert isinstance(result, dict)
    assert "items" in result
    assert result["count"] == 2


@patch("metabolon.enzymes.turgor.TONUS")
def test_mark_action(mock_tonus):
    from metabolon.enzymes.turgor import tonus
    mock_tonus.read_text.return_value = "- [in-progress] **Task A.** some task\n<!-- last checkpoint: 01/01/2026 ~12:00 HKT -->"
    result = tonus(action="mark", label="Task A", item_status="done", description="completed")
    assert isinstance(result, dict)
    assert result.get("success") is True
