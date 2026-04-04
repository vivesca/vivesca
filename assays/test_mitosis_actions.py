"""Tests for mitosis action-dispatch consolidation."""

from unittest.mock import MagicMock, patch


def test_mitosis_actions_unknown_action():
    from metabolon.enzymes.mitosis import EffectorResult, mitosis

    result = mitosis(action="nonexistent")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "unknown" in result.message.lower()


@patch("metabolon.organelles.mitosis.sync")
def test_sync_action(mock_sync):
    from metabolon.enzymes.mitosis import EffectorResult, mitosis

    mock_report = MagicMock()
    mock_report.ok = True
    mock_report.summary = "synced all targets"
    mock_report.elapsed_s = 1.5
    mock_result = MagicMock()
    mock_result.target = "chromatin"
    mock_result.success = True
    mock_result.elapsed_s = 1.0
    mock_result.message = ""
    mock_report.results = [mock_result]
    mock_sync.return_value = mock_report
    result = mitosis(action="sync")
    assert isinstance(result, EffectorResult)
    assert result.success is True


@patch("metabolon.organelles.mitosis.status")
def test_mitosis_actions_status_action(mock_status):
    from metabolon.enzymes.mitosis import Vital, mitosis

    mock_status.return_value = {"reachable": True, "machine_state": "running", "targets": {}}
    result = mitosis(action="status")
    assert isinstance(result, Vital)
    assert result.status == "ok"
