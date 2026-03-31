"""Tests for mitosis DR sync tool."""
import pytest
from unittest.mock import patch, MagicMock

from metabolon.enzymes.mitosis import mitosis
from metabolon.morphology import EffectorResult, Vital


def test_unknown_action():
    """Test unknown action returns error."""
    result = mitosis(action="invalid")
    assert isinstance(result, EffectorResult)
    assert not result.success
    assert "Unknown action" in result.message
    assert result.data == {}


def test_status_unreachable():
    """Test status when gemmule unreachable."""
    mock_status = MagicMock(return_value={"reachable": False})
    
    with patch("metabolon.organelles.mitosis.status", mock_status):
        result = mitosis(action="status")
    
    assert isinstance(result, Vital)
    assert result.status == "error"
    assert "gemmule unreachable" in result.message
    assert result.details["reachable"] is False


def test_status_stale_targets():
    """Test status when some targets are stale."""
    mock_status = MagicMock(return_value={
        "reachable": True,
        "machine_state": "started",
        "targets": {
            "germline": {"state": "ok"},
            "epigenome": {"state": "stale"},
        }
    })
    
    with patch("metabolon.organelles.mitosis.status", mock_status):
        result = mitosis(action="status")
    
    assert isinstance(result, Vital)
    assert result.status == "warning"
    assert "1 targets stale" in result.message
    assert "epigenome" in result.message


def test_status_all_ok():
    """Test status when all targets are ok."""
    mock_status = MagicMock(return_value={
        "reachable": True,
        "machine_state": "running",
        "targets": {
            "germline": {"state": "ok"},
            "epigenome": {"state": "ok"},
        }
    })
    
    with patch("metabolon.organelles.mitosis.status", mock_status):
        result = mitosis(action="status")
    
    assert isinstance(result, Vital)
    assert result.status == "ok"
    assert "gemmule healthy" in result.message
    assert "machine running" in result.message


def test_sync_success():
    """Test sync with all targets successful."""
    mock_report = MagicMock()
    mock_report.ok = True
    mock_report.elapsed_s = 10.5
    mock_report.summary = "2/2 targets synced in 10.5s (0 failed)"
    
    mock_result1 = MagicMock()
    mock_result1.target = "germline"
    mock_result1.success = True
    mock_result1.elapsed_s = 5.2
    mock_result1.message = "ok"
    
    mock_result2 = MagicMock()
    mock_result2.target = "epigenome"
    mock_result2.success = True
    mock_result2.elapsed_s = 5.3
    mock_result2.message = "ok"
    
    mock_report.results = [mock_result1, mock_result2]
    
    mock_sync = MagicMock(return_value=mock_report)
    
    with patch("metabolon.organelles.mitosis.sync", mock_sync):
        result = mitosis(action="sync", targets=["germline", "epigenome"])
    
    mock_sync.assert_called_once_with(["germline", "epigenome"])
    assert isinstance(result, EffectorResult)
    assert result.success is True
    assert len(result.data["results"]) == 2
    assert result.data["elapsed_s"] == 10.5
    assert all(r["ok"] for r in result.data["results"])


def test_sync_partial_failure():
    """Test sync with some failures but criticals ok."""
    mock_report = MagicMock()
    mock_report.ok = True  # criticals still ok
    mock_report.elapsed_s = 8.0
    mock_report.summary = "1/2 targets synced in 8.0s (1 failed)"
    
    mock_result1 = MagicMock()
    mock_result1.target = "germline"
    mock_result1.success = True
    mock_result1.elapsed_s = 4.0
    mock_result1.message = "ok"
    
    mock_result2 = MagicMock()
    mock_result2.target = "cc-auth"
    mock_result2.success = False
    mock_result2.elapsed_s = 4.0
    mock_result2.message = "permission denied"
    
    mock_report.results = [mock_result1, mock_result2]
    
    mock_sync = MagicMock(return_value=mock_report)
    
    with patch("metabolon.organelles.mitosis.sync", mock_sync):
        result = mitosis(action="sync")
    
    assert isinstance(result, EffectorResult)
    assert result.success is True  # because only non-critical failed
    assert len(result.data["results"]) == 2
