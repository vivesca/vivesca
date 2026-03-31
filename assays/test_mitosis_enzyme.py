from __future__ import annotations

"""Tests for metabolon.enzymes.mitosis — DR sync MCP tool."""

from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.mitosis import mitosis
from metabolon.morphology import EffectorResult, Vital
from metabolon.organelles.mitosis import FidelityReport, ReplicationResult


# ── Fixtures / helpers ────────────────────────────────────────────────


def _make_report(results: list[ReplicationResult]) -> FidelityReport:
    """Build a FidelityReport with given results."""
    return FidelityReport(results=results, started=100.0, finished=101.5)


# ── action="sync" ─────────────────────────────────────────────────────


@patch("metabolon.organelles.mitosis.sync")
def test_sync_returns_effector_result_on_success(mock_sync):
    report = _make_report([
        ReplicationResult("germline", True, 1.2, "pushed"),
        ReplicationResult("epigenome", True, 0.8, "up-to-date"),
    ])
    mock_sync.return_value = report

    result = mitosis(action="sync")

    assert isinstance(result, EffectorResult)
    assert result.success is True
    assert "2/2" in result.message
    assert result.data["results"][0]["target"] == "germline"
    assert result.data["results"][0]["ok"] is True
    assert result.data["results"][1]["target"] == "epigenome"


@patch("metabolon.organelles.mitosis.sync")
def test_sync_passes_targets(mock_sync):
    mock_sync.return_value = _make_report([
        ReplicationResult("germline", True, 0.5, "pushed"),
    ])

    mitosis(action="sync", targets=["germline"])

    mock_sync.assert_called_once_with(["germline"])


@patch("metabolon.organelles.mitosis.sync")
def test_sync_passes_none_targets(mock_sync):
    mock_sync.return_value = _make_report([
        ReplicationResult("germline", True, 0.5, "pushed"),
    ])

    mitosis(action="sync")

    mock_sync.assert_called_once_with(None)


@patch("metabolon.organelles.mitosis.sync")
def test_sync_reports_failure(mock_sync):
    report = _make_report([
        ReplicationResult("germline", False, 2.0, "push: failed"),
    ])
    mock_sync.return_value = report

    result = mitosis(action="sync")

    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "0/1" in result.message


@patch("metabolon.organelles.mitosis.sync")
def test_sync_elapsed_s_is_rounded(mock_sync):
    report = _make_report([
        ReplicationResult("germline", True, 1.2345, "ok"),
    ])
    mock_sync.return_value = report

    result = mitosis(action="sync")

    assert result.data["elapsed_s"] == 1.5  # round(1.5, 1)


@patch("metabolon.organelles.mitosis.sync")
def test_sync_result_error_field_populated(mock_sync):
    mock_sync.return_value = _make_report([
        ReplicationResult("germline", False, 1.0, "pull failed: timeout"),
    ])

    result = mitosis(action="sync")

    assert result.data["results"][0]["error"] == "pull failed: timeout"


# ── action="status" ──────────────────────────────────────────────────


@patch("metabolon.organelles.mitosis.status")
def test_status_unreachable(mock_status):
    mock_status.return_value = {"reachable": False}

    result = mitosis(action="status")

    assert isinstance(result, Vital)
    assert result.status == "error"
    assert "unreachable" in result.message


@patch("metabolon.organelles.mitosis.status")
def test_status_healthy(mock_status):
    mock_status.return_value = {
        "reachable": True,
        "machine_state": "started",
        "targets": {
            "germline": {"state": "ok", "age_minutes": 5},
            "epigenome": {"state": "ok", "age_minutes": 3},
        },
    }

    result = mitosis(action="status")

    assert isinstance(result, Vital)
    assert result.status == "ok"
    assert "healthy" in result.message
    assert "started" in result.message


@patch("metabolon.organelles.mitosis.status")
def test_status_stale_targets(mock_status):
    mock_status.return_value = {
        "reachable": True,
        "machine_state": "started",
        "targets": {
            "germline": {"state": "stale", "age_minutes": 45},
            "epigenome": {"state": "ok", "age_minutes": 2},
        },
    }

    result = mitosis(action="status")

    assert isinstance(result, Vital)
    assert result.status == "warning"
    assert "1 targets stale" in result.message
    assert "germline" in result.message


@patch("metabolon.organelles.mitosis.status")
def test_status_missing_targets(mock_status):
    mock_status.return_value = {
        "reachable": True,
        "machine_state": "started",
        "targets": {
            "germline": {"state": "missing"},
            "epigenome": {"state": "missing"},
        },
    }

    result = mitosis(action="status")

    assert isinstance(result, Vital)
    assert result.status == "warning"
    assert "2 targets stale" in result.message


@patch("metabolon.organelles.mitosis.status")
def test_status_details_passed_through(mock_status):
    info = {
        "reachable": True,
        "machine_state": "started",
        "targets": {"germline": {"state": "ok"}},
    }
    mock_status.return_value = info

    result = mitosis(action="status")

    assert result.details == info


# ── unknown action ────────────────────────────────────────────────────


def test_unknown_action_returns_error():
    result = mitosis(action="foobar")

    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "Unknown action" in result.message
    assert "foobar" in result.message
    assert result.data == {}


def test_unknown_action_suggests_valid():
    result = mitosis(action="push")

    assert "sync" in result.message
    assert "status" in result.message
