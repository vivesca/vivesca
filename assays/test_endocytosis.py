"""Tests for metabolon.enzymes.endocytosis."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.endocytosis import (
    EndocytosisResult,
    _stats_result,
    _status_result,
    _top_result,
    endocytosis,
)
from metabolon.morphology import EffectorResult

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_config(
    sources_path="/tmp/sources.yaml",
    state_path="/tmp/state.json",
    log_path="/tmp/news.log",
    config_dir="/tmp/endocytosis",
    article_cache_dir="/tmp/endocytosis/cache",
):
    cfg = MagicMock()
    cfg.config_dir = Path(config_dir)
    cfg.sources_path = Path(sources_path)
    cfg.state_path = Path(state_path)
    cfg.log_path = Path(log_path)
    cfg.article_cache_dir = Path(article_cache_dir)
    return cfg


# ---------------------------------------------------------------------------
# 1. Dispatch: unknown action returns EffectorResult failure
# ---------------------------------------------------------------------------


def test_unknown_action_returns_error():
    result = endocytosis(action="foobar")
    assert isinstance(result, EffectorResult)
    assert result.success is False
    assert "Unknown action" in result.message
    assert "foobar" in result.message


# ---------------------------------------------------------------------------
# 2. status action builds human-readable report
# ---------------------------------------------------------------------------


@patch("metabolon.enzymes.endocytosis._status_result")
def test_status_dispatches(mock_status):
    mock_status.return_value = EndocytosisResult(output="status-ok", status="ok")
    result = endocytosis(action="status")
    assert isinstance(result, EndocytosisResult)
    assert result.output == "status-ok"
    mock_status.assert_called_once()


@patch("metabolon.organelles.endocytosis_rss.state.restore_state")
@patch("metabolon.organelles.endocytosis_rss.config.restore_config")
@patch("metabolon.organelles.endocytosis_rss.cli._parse_aware")
@patch("metabolon.organelles.endocytosis_rss.cli._file_age")
def test_status_result_builds_output(
    mock_file_age, mock_parse_aware, mock_restore_config, mock_restore_state
):
    mock_file_age.return_value = "2h ago"
    mock_parse_aware.return_value = datetime(2025, 6, 1, 12, 0, tzinfo=UTC)
    cfg = _make_config()
    # Make article_cache_dir exist so it lists files
    cfg.article_cache_dir = Path("/tmp/endocytosis_test_cache_status")
    cfg.article_cache_dir.mkdir(parents=True, exist_ok=True)
    mock_restore_config.return_value = cfg
    mock_restore_state.return_value = {
        "src1": "2025-06-01T12:00:00+00:00",
        "src2": "2025-06-01T11:00:00+00:00",
    }

    result = _status_result()
    assert isinstance(result, EndocytosisResult)
    assert result.status == "ok"
    assert "Endocytosis Status" in result.output
    assert "2h ago" in result.output
    assert "2 tracked" in result.output
    assert "Last fetch:" in result.output


# ---------------------------------------------------------------------------
# 3. stats action with no data returns insufficient_data
# ---------------------------------------------------------------------------


@patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl", return_value=[])
def test_stats_result_no_data(mock_read):
    result = _stats_result()
    assert isinstance(result, EndocytosisResult)
    assert result.status == "insufficient_data"
    assert "no affinity log" in result.output.lower()


@patch(
    "metabolon.organelles.endocytosis_rss.relevance.affinity_stats",
    return_value={"status": "insufficient_data"},
)
@patch(
    "metabolon.organelles.endocytosis_rss.relevance._read_jsonl",
    return_value=[
        {"title": "Alpha", "score": 7},
        {"title": "Beta", "score": 2},
        {"title": "Gamma", "score": 5},
    ],
)
def test_stats_result_with_scored_entries(mock_read, mock_stats):
    result = _stats_result()
    assert isinstance(result, EndocytosisResult)
    assert result.total_scored == 3
    # Signal ratio: items with score >= 5 are "Alpha"(7) and "Gamma"(5) => 2/3
    assert result.signal_ratio == pytest.approx(round(2 / 3, 3))
    assert "Signal ratio:" in result.output


@patch(
    "metabolon.organelles.endocytosis_rss.relevance.affinity_stats",
    return_value={
        "status": "ok",
        "total_scored": 10,
        "total_engaged": 4,
        "avg_engaged_score": 7.5,
        "false_positives_count": 1,
        "false_negatives": ["Missed Article A"],
    },
)
@patch(
    "metabolon.organelles.endocytosis_rss.relevance._read_jsonl",
    return_value=[
        {"title": "Alpha", "score": 8},
        {"title": "Beta", "score": 3},
    ],
)
def test_stats_result_full_affinity(mock_read, mock_stats):
    result = _stats_result()
    assert result.status == "ok"
    assert result.total_engaged == 4
    assert result.avg_engaged_score == 7.5
    assert result.false_positives_count == 1
    assert "Missed Article A" in result.false_negatives
    assert "False positives:" in result.output
    assert "False negatives" in result.output


# ---------------------------------------------------------------------------
# 4. top action with items formats numbered list
# ---------------------------------------------------------------------------


@patch(
    "metabolon.organelles.endocytosis_rss.relevance.top_cargo",
    return_value=[
        {
            "title": "Breaking News",
            "score": 9,
            "source": "Reuters",
            "banking_angle": "geopolitical shift",
        },
        {"title": "Tech Update", "score": 7, "source": "Ars", "banking_angle": "N/A"},
    ],
)
def test_top_result_with_items(mock_top):
    result = _top_result(limit=5, days=3)
    assert isinstance(result, EndocytosisResult)
    assert result.count == 2
    assert result.days_window == 3
    assert "1. [9/10] Breaking News" in result.output
    assert "2. [7/10] Tech Update" in result.output
    # banking_angle "N/A" should NOT appear
    assert "geopolitical shift" in result.output
    assert "Banking angle: N/A" not in result.output


@patch(
    "metabolon.organelles.endocytosis_rss.relevance.top_cargo",
    return_value=[],
)
def test_top_result_empty(mock_top):
    result = _top_result(limit=10, days=7)
    assert result.count == 0
    assert "No items found" in result.output


# ---------------------------------------------------------------------------
# 5. fetch action returns EffectorResult on success
# ---------------------------------------------------------------------------


@patch("metabolon.organelles.endocytosis_rss.state.lockfile")
@patch("metabolon.organelles.endocytosis_rss.config.restore_config")
@patch("metabolon.organelles.endocytosis_rss.cli._fetch_locked")
def test_fetch_action_success(mock_fetch, mock_config, mock_lockfile):
    mock_config.return_value = _make_config()
    mock_lockfile.return_value = MagicMock(
        __enter__=MagicMock(), __exit__=MagicMock(return_value=False)
    )

    result = endocytosis(action="fetch", no_archive=True)
    assert isinstance(result, EffectorResult)
    assert result.success is True
    assert "Fetch cycle complete" in result.message
    mock_fetch.assert_called_once()
