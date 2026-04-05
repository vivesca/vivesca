"""Tests for proteasome action-dispatch consolidation."""

from unittest.mock import patch


def test_proteasome_actions_unknown_action():
    from metabolon.enzymes.proteasome import ProteasomeConfirmResult, proteasome

    result = proteasome(action="nonexistent")
    assert isinstance(result, ProteasomeConfirmResult)
    assert not result.success
    assert "unknown" in result.message.lower()


@patch("metabolon.enzymes.proteasome._spending")
def test_spending_action(mock_spending):
    from metabolon.enzymes.proteasome import proteasome

    mock_spending.return_value = "spending summary"
    result = proteasome(action="spending")
    assert result == "spending summary"
    mock_spending.assert_called_once()


@patch("metabolon.enzymes.proteasome._confirm")
def test_confirm_action(mock_confirm):
    from metabolon.enzymes.proteasome import proteasome

    mock_confirm.return_value = "confirm summary"
    result = proteasome(action="confirm")
    assert result == "confirm summary"
    mock_confirm.assert_called_once()
