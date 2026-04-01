from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from metabolon.enzymes.mitosis import mitosis
from metabolon.morphology import EffectorResult, Vital


class TestMitosisEnzyme:
    """Tests for the mitosis DR sync tool enzyme."""

    def test_unknown_action_returns_error(self):
        """Test that unknown action returns error result."""
        result = mitosis(action="bad_action", targets=None)
        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "Unknown action" in result.message

    @patch("metabolon.organelles.mitosis._is_soma_reachable")
    def test_status_unreachable_returns_error_vital(self, mock_reachable):
        """Test status when soma is unreachable."""
        mock_reachable.return_value = False
        result = mitosis(action="status", targets=None)
        assert isinstance(result, Vital)
        assert result.status == "error"
        assert "unreachable" in result.message
        assert not result.details["reachable"]

    @patch("metabolon.organelles.mitosis._is_soma_reachable")
    @patch("metabolon.organelles.mitosis._fly_cmd")
    def test_status_healthy_returns_ok(self, mock_fly_cmd, mock_reachable):
        """Test status when all targets are fresh."""
        mock_reachable.return_value = True

        # Mock fly_cmd output with recent timestamps (less than 30 minutes old)
        current_time = 1717200000  # epoch
        mock_fly_cmd.return_value = MagicMock(
            stdout=f"{current_time}\n---\n{current_time}",
            returncode=0
        )

        with patch("time.time", return_value=current_time + 600):  # 10 minutes later
            result = mitosis(action="status", targets=None)
            assert isinstance(result, Vital)
            assert result.status == "ok"
            assert "healthy" in result.message

    @patch("metabolon.organelles.mitosis._is_soma_reachable")
    @patch("metabolon.organelles.mitosis._fly_cmd")
    def test_status_stale_targets_returns_warning(self, mock_fly_cmd, mock_reachable):
        """Test status when some targets are stale."""
        mock_reachable.return_value = True

        # Mock with stale timestamps (more than 30 minutes old)
        stale_time = 1717200000
        current_time = stale_time + 3600  # 1 hour later
        mock_fly_cmd.return_value = MagicMock(
            stdout=f"{stale_time}\n---\n{stale_time}",
            returncode=0
        )

        with patch("time.time", return_value=current_time):
            result = mitosis(action="status", targets=None)
            assert isinstance(result, Vital)
            assert result.status == "warning"
            assert "stale" in result.message

    @patch("metabolon.organelles.mitosis._is_soma_reachable")
    def test_sync_soma_unreachable_includes_connectivity_error(self, mock_reachable):
        """Test sync when soma is unreachable includes error in results.

        Note: report.ok is True because there are no failed critical targets (no targets processed).
        """
        mock_reachable.return_value = False
        result = mitosis(action="sync", targets=None)
        assert isinstance(result, EffectorResult)
        # Check that connectivity error is present
        results = result.data["results"]
        assert len(results) == 1
        assert results[0]["target"] == "connectivity"
        assert results[0]["ok"] is False
        assert "soma not running" in results[0]["error"]

    @patch("metabolon.organelles.mitosis.sync")
    def test_sync_all_targets_success_returns_ok(self, mock_sync):
        """Test sync with all targets succeeds when all succeed."""
        from metabolon.organelles.mitosis import FidelityReport, ReplicationResult

        report = FidelityReport()
        report.started = 0
        report.finished = 2.5
        report.results = [
            ReplicationResult("germline", True, 1.0, "ok"),
            ReplicationResult("epigenome", True, 1.5, "ok"),
        ]
        mock_sync.return_value = report

        result = mitosis(action="sync", targets=None)
        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert "2/2" in result.message
        assert len(result.data["results"]) == 2

    @patch("metabolon.organelles.mitosis.sync")
    def test_sync_specific_targets(self, mock_sync):
        """Test sync with specific target subset."""
        from metabolon.organelles.mitosis import FidelityReport, ReplicationResult

        report = FidelityReport()
        report.started = 0
        report.finished = 1.0
        report.results = [
            ReplicationResult("germline", True, 1.0, "ok"),
        ]
        mock_sync.return_value = report

        result = mitosis(action="sync", targets=["germline"])
        assert isinstance(result, EffectorResult)
        assert result.success is True
        mock_sync.assert_called_once_with(["germline"])

    @patch("metabolon.organelles.mitosis.sync")
    def test_sync_critical_failure_returns_failure(self, mock_sync):
        """Test sync returns failure when critical target fails."""
        from metabolon.organelles.mitosis import FidelityReport, ReplicationResult

        report = FidelityReport()
        report.started = 0
        report.finished = 2.5
        report.results = [
            ReplicationResult("germline", False, 1.0, "failed"),
            ReplicationResult("epigenome", True, 1.5, "ok"),
        ]
        mock_sync.return_value = report

        result = mitosis(action="sync", targets=None)
        assert isinstance(result, EffectorResult)
        assert result.success is False
