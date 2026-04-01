"""Tests for metabolon.enzymes.mitosis."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from metabolon.enzymes.mitosis import mitosis
from metabolon.morphology import EffectorResult, Vital


def test_unknown_action():
    """Test unknown action returns error."""
    result = mitosis(action="invalid")
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "Unknown action" in result.message
    assert "invalid" in result.message


def test_status_unreachable():
    """Test status when soma unreachable."""
    mock_status = MagicMock(return_value={"reachable": False})
    with patch("metabolon.organelles.mitosis.status", mock_status):
        result = mitosis(action="status")
        assert isinstance(result, Vital)
        assert result.status == "error"
        assert "soma unreachable" in result.message
        assert result.details == {"reachable": False}


def test_status_stale_targets():
    """Test status with stale targets returns warning."""
    mock_info = {
        "reachable": True,
        "machine_state": "started",
        "targets": {
            "germline": {"state": "ok"},
            "epigenome": {"state": "stale"},
        },
    }
    mock_status = MagicMock(return_value=mock_info)
    with patch("metabolon.organelles.mitosis.status", mock_status):
        result = mitosis(action="status")
        assert isinstance(result, Vital)
        assert result.status == "warning"
        assert "1 targets stale" in result.message
        assert "epigenome" in result.message
        assert result.details == mock_info


def test_status_all_ok():
    """Test status when all targets ok."""
    mock_info = {
        "reachable": True,
        "machine_state": "running",
        "targets": {
            "germline": {"state": "ok"},
            "epigenome": {"state": "ok"},
        },
    }
    mock_status = MagicMock(return_value=mock_info)
    with patch("metabolon.organelles.mitosis.status", mock_status):
        result = mitosis(action="status")
        assert isinstance(result, Vital)
        assert result.status == "ok"
        assert "soma healthy" in result.message
        assert "running" in result.message


class MockReplicationResult:
    __slots__ = ("target", "success", "elapsed_s", "message")
    def __init__(self, target, success, elapsed_s, message=""):
        self.target = target
        self.success = success
        self.elapsed_s = elapsed_s
        self.message = message


def create_mock_fidelity_report(results):
    class MockFidelityReport:
        def __init__(self):
            self.results = results
            self.started = 0.0
            self.finished = sum(r.elapsed_s for r in results)

        @property
        def elapsed_s(self):
            return self.finished - self.started

        @property
        def ok(self):
            # Mimic the real logic from organelles.mitosis
            # All critical targets (germline, epigenome) must succeed
            return all(r.success for r in self.results if r.target in ("germline", "epigenome"))

        @property
        def summary(self):
            ok = sum(1 for r in self.results if r.success)
            return f"{ok}/{len(self.results)} targets synced in {self.elapsed_s:.1f}s"

    return MockFidelityReport()


def test_sync_success():
    """Test sync with all successful targets."""
    mock_results = [
        MockReplicationResult("germline", True, 0.5),
        MockReplicationResult("epigenome", True, 0.8),
    ]
    mock_report = create_mock_fidelity_report(mock_results)
    mock_sync = MagicMock(return_value=mock_report)
    with patch("metabolon.organelles.mitosis.sync", mock_sync):
        result = mitosis(action="sync")
        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert "2/2 targets" in result.message
        assert len(result.data["results"]) == 2
        assert result.data["elapsed_s"] == 1.3
        assert all(r["ok"] for r in result.data["results"])


def test_sync_partial_failure_non_critical():
    """Test sync with partial failure but all critical ok."""
    mock_results = [
        MockReplicationResult("germline", True, 0.5),
        MockReplicationResult("cc-auth", False, 0.1, "permission denied"),
    ]
    mock_report = create_mock_fidelity_report(mock_results)
    mock_sync = MagicMock(return_value=mock_report)
    with patch("metabolon.organelles.mitosis.sync", mock_sync):
        result = mitosis(action="sync", targets=["germline"])
        assert isinstance(result, EffectorResult)
        assert result.success is True  # still ok because cc-auth not critical
        assert "1/2 targets" in result.message
        assert len(result.data["results"]) == 2
        assert result.data["results"][1]["ok"] is False
        assert result.data["results"][1]["error"] == "permission denied"


def test_sync_with_targets_filtered():
    """Test sync with specific targets only passes them through."""
    mock_results = [MockReplicationResult("germline", True, 0.5)]
    mock_report = create_mock_fidelity_report(mock_results)
    mock_sync = MagicMock(return_value=mock_report)
    with patch("metabolon.organelles.mitosis.sync", mock_sync):
        mitosis(action="sync", targets=["germline"])
        mock_sync.assert_called_once_with(["germline"])
