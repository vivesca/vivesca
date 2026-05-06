"""Tests for g1 action-dispatch consolidation."""

from unittest.mock import patch


def test_turgor_actions_unknown_action():
    from metabolon.enzymes.turgor import g1

    result = g1(action="nonexistent")
    assert isinstance(result, dict)
    assert not result.get("success", True)
    assert "unknown" in result.get("message", "").lower()


@patch("metabolon.enzymes.turgor.G1")
def test_turgor_actions_status_action(mock_g1):
    from metabolon.enzymes.turgor import g1

    mock_g1.exists.return_value = True
    mock_g1.read_text.return_value = (
        "- [done] **Task A.** completed item\n- [in-progress] **Task B.** working on it"
    )
    result = g1(action="status")
    assert isinstance(result, dict)
    assert "items" in result
    assert result["count"] == 2


@patch("metabolon.enzymes.turgor.G1")
def test_mark_action(mock_g1):
    from metabolon.enzymes.turgor import g1

    mock_g1.read_text.return_value = (
        "- [in-progress] **Task A.** some task\n<!-- last checkpoint: 01/01/2026 ~12:00 HKT -->"
    )
    result = g1(action="mark", label="Task A", item_status="done", description="completed")
    assert isinstance(result, dict)
    assert result.get("success") is True
