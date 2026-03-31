from __future__ import annotations

"""Tests for metabolon.enzymes.endocytosis — all actions mocked."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import metabolon.enzymes.endocytosis as mod
from metabolon.enzymes.endocytosis import (
    EndocytosisResult,
    _stats_result,
    _status_result,
    _top_result,
    endocytosis,
)
from metabolon.morphology import EffectorResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ts(days_ago: int = 0) -> str:
    return (datetime.now(UTC) - timedelta(days=days_ago)).isoformat()


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


# ---------------------------------------------------------------------------
# _status_result
# ---------------------------------------------------------------------------


class TestStatusResult:
    """Tests for the status action helper."""

    @patch("metabolon.enzymes.endocytosis.datetime")
    @patch("metabolon.organelles.endocytosis_rss.cli._file_age", return_value="2h old")
    @patch("metabolon.organelles.endocytosis_rss.state.restore_state", return_value={})
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_basic_status_output(
        self, mock_restore_config, mock_restore_state, mock_file_age, mock_dt
    ):
        fake_config = SimpleNamespace(
            config_dir=Path("/fake/cfg"),
            sources_path=Path("/fake/cfg/sources.yaml"),
            state_path=Path("/fake/cfg/state.json"),
            log_path=Path("/fake/cfg/news.log"),
            article_cache_dir=Path("/fake/cfg/cache"),
        )
        mock_restore_config.return_value = fake_config
        mock_dt.now.return_value.astimezone.return_value = datetime(
            2025, 6, 15, 12, 0, tzinfo=UTC
        )

        with patch.object(Path, "exists", return_value=False):
            result = _status_result()

        assert result.status == "ok"
        assert "Endocytosis Status" in result.output
        assert "Config dir:    /fake/cfg" in result.output
        assert "2h old" in result.output

    @patch("metabolon.enzymes.endocytosis.datetime")
    @patch("metabolon.organelles.endocytosis_rss.cli._file_age", return_value="ok")
    @patch("metabolon.organelles.endocytosis_rss.cli._parse_aware")
    @patch("metabolon.organelles.endocytosis_rss.state.restore_state")
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_status_with_state(
        self, mock_restore_config, mock_restore_state, mock_parse, mock_file_age, mock_dt
    ):
        fake_config = SimpleNamespace(
            config_dir=Path("/fake/cfg"),
            sources_path=Path("/fake/cfg/sources.yaml"),
            state_path=Path("/fake/cfg/state.json"),
            log_path=Path("/fake/cfg/news.log"),
            article_cache_dir=Path("/fake/cfg/cache"),
        )
        mock_restore_config.return_value = fake_config
        mock_restore_state.return_value = {
            "feed_a": "2025-06-14T10:00:00+00:00",
            "feed_b": "2025-06-15T08:00:00+00:00",
        }
        # _parse_aware returns a datetime for the state values
        mock_parse.side_effect = lambda s: datetime.fromisoformat(s) if s else None
        mock_dt.now.return_value.astimezone.return_value = datetime(
            2025, 6, 15, 12, 0, tzinfo=UTC
        )

        with patch.object(Path, "exists", return_value=False):
            result = _status_result()

        assert result.status == "ok"
        assert "2 tracked" in result.output
        assert "Last fetch:" in result.output

    @patch("metabolon.enzymes.endocytosis.datetime")
    @patch("metabolon.organelles.endocytosis_rss.cli._file_age", return_value="ok")
    @patch("metabolon.organelles.endocytosis_rss.state.restore_state", return_value={})
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_status_with_article_cache(
        self, mock_restore_config, mock_restore_state, mock_file_age, mock_dt, tmp_path
    ):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "a.json").write_text('{"a":1}')
        (cache_dir / "b.json").write_text('{"b":2}')

        fake_config = SimpleNamespace(
            config_dir=Path("/fake/cfg"),
            sources_path=Path("/fake/cfg/sources.yaml"),
            state_path=Path("/fake/cfg/state.json"),
            log_path=Path("/fake/cfg/news.log"),
            article_cache_dir=cache_dir,
        )
        mock_restore_config.return_value = fake_config
        mock_dt.now.return_value.astimezone.return_value = datetime(
            2025, 6, 15, 12, 0, tzinfo=UTC
        )

        result = _status_result()
        assert "Article cache: 2 files" in result.output

    @patch("metabolon.enzymes.endocytosis.datetime")
    @patch("metabolon.organelles.endocytosis_rss.cli._file_age", return_value="ok")
    @patch("metabolon.organelles.endocytosis_rss.state.restore_state", return_value={})
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_status_cache_missing(
        self, mock_restore_config, mock_restore_state, mock_file_age, mock_dt
    ):
        fake_config = SimpleNamespace(
            config_dir=Path("/fake/cfg"),
            sources_path=Path("/fake/cfg/sources.yaml"),
            state_path=Path("/fake/cfg/state.json"),
            log_path=Path("/fake/cfg/news.log"),
            article_cache_dir=Path("/nonexistent/cache"),
        )
        mock_restore_config.return_value = fake_config
        mock_dt.now.return_value.astimezone.return_value = datetime(
            2025, 6, 15, 12, 0, tzinfo=UTC
        )

        result = _status_result()
        assert "missing" in result.output


# ---------------------------------------------------------------------------
# _stats_result
# ---------------------------------------------------------------------------


class TestStatsResult:
    """Tests for the stats action helper with fully mocked internals."""

    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_insufficient_data_no_rows(self, mock_read, mock_stats):
        mock_read.return_value = []
        result = _stats_result()
        assert result.status == "insufficient_data"
        assert "no affinity log entries" in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_stats_insufficient_engagement(self, mock_read, mock_stats):
        mock_read.return_value = [
            {"title": "A", "score": 5},
            {"title": "B", "score": 8},
        ]
        mock_stats.return_value = {"status": "insufficient_data"}

        result = _stats_result()
        assert result.status == "insufficient_data"
        assert result.total_scored == 2
        # signal_ratio: 2 of 2 scored >= 5 → 1.0
        assert result.signal_ratio == pytest.approx(1.0)

    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_stats_with_full_data(self, mock_read, mock_stats):
        mock_read.return_value = [
            {"title": "High", "score": 8},
            {"title": "Low", "score": 2},
            {"title": "Mid", "score": 5},
        ]
        mock_stats.return_value = {
            "status": "ok",
            "total_scored": 3,
            "total_engaged": 1,
            "avg_engaged_score": 7.5,
            "false_positives_count": 0,
            "false_negatives": [],
        }

        result = _stats_result()
        assert result.status == "ok"
        assert result.total_scored == 3
        assert result.total_engaged == 1
        assert result.avg_engaged_score == pytest.approx(7.5)
        # signal_ratio: 2 of 3 scored >= 5 → 0.667
        assert result.signal_ratio == pytest.approx(2 / 3, abs=0.01)
        assert "Signal ratio:" in result.output
        assert "Engaged: 1" in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_stats_with_false_negatives(self, mock_read, mock_stats):
        mock_read.return_value = [
            {"title": "Gem", "score": 3},
        ]
        mock_stats.return_value = {
            "status": "ok",
            "total_scored": 1,
            "total_engaged": 1,
            "avg_engaged_score": 3.0,
            "false_positives_count": 0,
            "false_negatives": ["Gem", "Another"],
        }

        result = _stats_result()
        assert result.false_negatives == ["Gem", "Another"]
        assert "False negatives" in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_stats_skips_empty_titles(self, mock_read, mock_stats):
        mock_read.return_value = [
            {"title": "", "score": 5},
            {"title": "Valid", "score": 8},
        ]
        mock_stats.return_value = {"status": "insufficient_data"}

        result = _stats_result()
        # Only "Valid" counted (1 of 1 >= 5)
        assert result.signal_ratio == pytest.approx(1.0)

    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_stats_handles_non_numeric_score(self, mock_read, mock_stats):
        mock_read.return_value = [
            {"title": "Bad", "score": "high"},
            {"title": "Good", "score": 6},
        ]
        mock_stats.return_value = {"status": "insufficient_data"}

        result = _stats_result()
        # int("high") raises ValueError → suppressed → entry skipped entirely
        # Only "Good" remains in scored dict → 1 of 1 >= 5
        assert result.signal_ratio == pytest.approx(1.0)
        assert result.total_scored == 1


# ---------------------------------------------------------------------------
# _top_result
# ---------------------------------------------------------------------------


class TestTopResult:
    """Tests for the top action helper with mocked top_cargo."""

    @patch("metabolon.organelles.endocytosis_rss.relevance.top_cargo")
    def test_empty_items(self, mock_top):
        mock_top.return_value = []
        result = _top_result(limit=5, days=7)
        assert result.status == "ok"
        assert result.items == []
        assert result.count == 0
        assert "No items found" in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.top_cargo")
    def test_with_items(self, mock_top):
        mock_top.return_value = [
            {"title": "First", "score": 9, "source": "src_a", "banking_angle": "AI bias"},
            {"title": "Second", "score": 7, "source": "src_b", "banking_angle": ""},
        ]
        result = _top_result(limit=10, days=3)
        assert result.count == 2
        assert result.days_window == 3
        assert "[9/10] First" in result.output
        assert "Banking angle: AI bias" in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.top_cargo")
    def test_n_a_banking_angle_suppressed(self, mock_top):
        mock_top.return_value = [
            {"title": "X", "score": 5, "source": "s", "banking_angle": "N/A"},
        ]
        result = _top_result(limit=5, days=7)
        assert "Banking angle" not in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.top_cargo")
    def test_limit_and_days_forwarded(self, mock_top):
        mock_top.return_value = []
        _top_result(limit=42, days=99)
        mock_top.assert_called_once_with(limit=42, days=99)


# ---------------------------------------------------------------------------
# endocytosis dispatch
# ---------------------------------------------------------------------------


class TestEndocytosisDispatch:
    """Tests for the main endocytosis() dispatch function."""

    @patch("metabolon.enzymes.endocytosis._status_result")
    def test_status_action(self, mock_status):
        mock_status.return_value = EndocytosisResult(
            output="status ok", status="ok"
        )
        result = endocytosis(action="status")
        assert result.status == "ok"
        mock_status.assert_called_once()

    def test_fetch_action(self):
        mock_config = SimpleNamespace(
            state_path=Path("/fake/state.json"),
        )
        mock_lock = MagicMock()
        mock_lock.__enter__ = MagicMock(return_value=None)
        mock_lock.__exit__ = MagicMock(return_value=False)

        with (
            patch("metabolon.organelles.endocytosis_rss.config.restore_config", return_value=mock_config),
            patch("metabolon.organelles.endocytosis_rss.state.lockfile", return_value=mock_lock),
            patch("metabolon.organelles.endocytosis_rss.cli._fetch_locked") as mock_fetch,
        ):
            result = endocytosis(action="fetch")

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert "Fetch cycle complete" in result.message
        assert result.data == {"no_archive": False}
        mock_fetch.assert_called_once_with(mock_config, False)

    def test_fetch_action_with_no_archive(self):
        mock_config = SimpleNamespace(
            state_path=Path("/fake/state.json"),
        )
        mock_lock = MagicMock()
        mock_lock.__enter__ = MagicMock(return_value=None)
        mock_lock.__exit__ = MagicMock(return_value=False)

        with (
            patch("metabolon.organelles.endocytosis_rss.config.restore_config", return_value=mock_config),
            patch("metabolon.organelles.endocytosis_rss.state.lockfile", return_value=mock_lock),
            patch("metabolon.organelles.endocytosis_rss.cli._fetch_locked") as mock_fetch,
        ):
            result = endocytosis(action="fetch", no_archive=True)

        assert result.data == {"no_archive": True}
        mock_fetch.assert_called_once_with(mock_config, True)

    @patch("metabolon.enzymes.endocytosis._stats_result")
    def test_stats_action(self, mock_stats):
        mock_stats.return_value = EndocytosisResult(
            output="stats ok", status="ok", total_scored=5
        )
        result = endocytosis(action="stats")
        assert result.status == "ok"
        assert result.total_scored == 5
        mock_stats.assert_called_once()

    @patch("metabolon.enzymes.endocytosis._top_result")
    def test_top_action(self, mock_top):
        mock_top.return_value = EndocytosisResult(
            output="top ok", status="ok", count=3
        )
        result = endocytosis(action="top", limit=5, days=7)
        assert result.count == 3
        mock_top.assert_called_once_with(limit=5, days=7)

    def test_unknown_action(self):
        result = endocytosis(action="explode")
        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "Unknown action" in result.message
        assert "explode" in result.message

    def test_action_case_insensitive(self):
        """Actions should be case-insensitive and whitespace-trimmed."""
        with patch("metabolon.enzymes.endocytosis._status_result") as mock:
            mock.return_value = EndocytosisResult(output="ok", status="ok")
            endocytosis(action="  STATUS  ")
            mock.assert_called_once()

    def test_action_whitespace_trimmed(self):
        with patch("metabolon.enzymes.endocytosis._status_result") as mock:
            mock.return_value = EndocytosisResult(output="ok", status="ok")
            endocytosis(action=" status ")
            mock.assert_called_once()
