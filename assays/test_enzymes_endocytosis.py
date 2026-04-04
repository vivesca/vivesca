from __future__ import annotations

"""Tests for metabolon/enzymes/endocytosis.py — RSS ingestion and status tools."""

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

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


def _make_config():
    """Build a lightweight config mock."""
    cfg = MagicMock()
    cfg.config_dir = Path("/fake/config")
    cfg.sources_path = Path("/fake/sources.json")
    cfg.state_path = Path("/fake/state.json")
    cfg.log_path = Path("/fake/news.log")
    cfg.article_cache_dir = Path("/fake/cache")
    return cfg


# ---------------------------------------------------------------------------
# EndocytosisResult dataclass
# ---------------------------------------------------------------------------


class TestEndocytosisResult:
    def test_defaults(self):
        r = EndocytosisResult(output="hello")
        assert r.output == "hello"
        assert r.status == ""
        assert r.total_scored == 0
        assert r.total_engaged == 0
        assert r.signal_ratio == 0.0
        assert r.avg_engaged_score == 0.0
        assert r.false_positives_count == 0
        assert r.false_negatives == []
        assert r.items == []
        assert r.count == 0
        assert r.days_window == 0

    def test_custom_values(self):
        r = EndocytosisResult(
            output="out",
            status="ok",
            total_scored=42,
            total_engaged=10,
            signal_ratio=0.75,
            avg_engaged_score=6.3,
            false_positives_count=2,
            false_negatives=["a", "b"],
            items=[{"title": "x"}],
            count=1,
            days_window=7,
        )
        assert r.status == "ok"
        assert r.total_scored == 42
        assert r.items == [{"title": "x"}]


# ---------------------------------------------------------------------------
# _status_result
# ---------------------------------------------------------------------------


class TestStatusResult:
    @patch("metabolon.enzymes.endocytosis.datetime")
    @patch("metabolon.organelles.endocytosis_rss.state.restore_state")
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_basic_status(self, mock_restore_config, mock_restore_state, mock_dt):
        cfg = _make_config()
        mock_restore_config.return_value = cfg
        mock_restore_state.return_value = {}
        mock_dt.now.return_value = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        with patch("metabolon.organelles.endocytosis_rss.cli._file_age", return_value="2h ago"):
            result = _status_result()

        assert result.status == "ok"
        assert "Endocytosis Status" in result.output
        assert "Config dir:" in result.output
        assert "2026-01-15" in result.output

    @patch("metabolon.enzymes.endocytosis.datetime")
    @patch("metabolon.organelles.endocytosis_rss.state.restore_state")
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_status_with_state(self, mock_restore_config, mock_restore_state, mock_dt):
        cfg = _make_config()
        mock_restore_config.return_value = cfg
        mock_restore_state.return_value = {
            "src1": "2026-01-15T10:00:00+00:00",
            "src2": "2026-01-14T08:00:00+00:00",
        }
        mock_dt.now.return_value = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        with patch("metabolon.organelles.endocytosis_rss.cli._file_age", return_value="ok"):
            with patch("metabolon.organelles.endocytosis_rss.cli._parse_aware") as mock_parse:
                mock_parse.side_effect = lambda v: datetime.fromisoformat(v)
                result = _status_result()

        assert result.status == "ok"
        assert "2 tracked" in result.output
        assert "Last fetch:" in result.output

    @patch("metabolon.enzymes.endocytosis.datetime")
    @patch("metabolon.organelles.endocytosis_rss.state.restore_state")
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_status_with_cache(self, mock_restore_config, mock_restore_state, mock_dt):
        cfg = _make_config()
        mock_restore_config.return_value = cfg
        mock_restore_state.return_value = {}
        mock_dt.now.return_value = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        mock_cache_file = MagicMock()
        mock_cache_file.stat.return_value.st_size = 2048
        with patch("metabolon.organelles.endocytosis_rss.cli._file_age", return_value="ok"):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "glob", return_value=[mock_cache_file]):
                    result = _status_result()

        assert "Article cache:" in result.output
        assert "1 files" in result.output
        assert "2 KB" in result.output

    @patch("metabolon.enzymes.endocytosis.datetime")
    @patch("metabolon.organelles.endocytosis_rss.state.restore_state")
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_status_missing_cache(self, mock_restore_config, mock_restore_state, mock_dt):
        cfg = _make_config()
        mock_restore_config.return_value = cfg
        mock_restore_state.return_value = {}
        mock_dt.now.return_value = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        with patch("metabolon.organelles.endocytosis_rss.cli._file_age", return_value="ok"):
            with patch.object(Path, "exists", return_value=False):
                result = _status_result()

        assert "Article cache: missing" in result.output


# ---------------------------------------------------------------------------
# _stats_result
# ---------------------------------------------------------------------------


class TestStatsResult:
    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_no_data(self, mock_read, mock_stats):
        mock_read.return_value = []
        result = _stats_result()
        assert result.status == "insufficient_data"
        assert "no affinity log entries" in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_with_scored_data_insufficient_engagement(self, mock_read, mock_stats):
        mock_read.return_value = [
            {"title": "Article A", "score": 7},
            {"title": "Article B", "score": 2},
        ]
        mock_stats.return_value = {"status": "insufficient_data"}
        result = _stats_result()

        assert result.status == "insufficient_data"
        assert "Signal ratio:" in result.output
        assert result.total_scored == 2
        assert result.signal_ratio == 0.5  # 1/2 scored >= 5

    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_with_full_stats(self, mock_read, mock_stats):
        mock_read.return_value = [
            {"title": "A", "score": 8},
            {"title": "B", "score": 6},
            {"title": "C", "score": 3},
        ]
        mock_stats.return_value = {
            "status": "ok",
            "total_scored": 3,
            "total_engaged": 2,
            "avg_engaged_score": 7.0,
            "false_positives_count": 1,
            "false_negatives": ["Low Scored Article"],
        }
        result = _stats_result()

        assert result.status == "ok"
        assert result.total_engaged == 2
        assert result.avg_engaged_score == 7.0
        assert result.false_positives_count == 1
        assert "Low Scored Article" in result.false_negatives
        assert "False negatives" in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_skips_empty_titles(self, mock_read, mock_stats):
        mock_read.return_value = [
            {"title": "", "score": 5},
            {"title": "Valid", "score": 7},
        ]
        mock_stats.return_value = {"status": "ok", "total_engaged": 1, "avg_engaged_score": 7.0}
        result = _stats_result()

        assert result.status == "ok"
        assert result.total_scored == 1  # only the valid one

    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_no_false_negatives_summary(self, mock_read, mock_stats):
        mock_read.return_value = [{"title": "A", "score": 9}]
        mock_stats.return_value = {
            "status": "ok",
            "total_scored": 1,
            "total_engaged": 1,
            "avg_engaged_score": 9.0,
            "false_positives_count": 0,
            "false_negatives": [],
        }
        result = _stats_result()
        assert "False negatives" not in result.output


# ---------------------------------------------------------------------------
# _top_result
# ---------------------------------------------------------------------------


class TestTopResult:
    @patch("metabolon.organelles.endocytosis_rss.relevance.top_cargo")
    def test_empty(self, mock_top):
        mock_top.return_value = []
        result = _top_result(limit=5, days=7)

        assert result.status == "ok"
        assert result.count == 0
        assert result.days_window == 7
        assert "No items found" in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.top_cargo")
    def test_with_items(self, mock_top):
        mock_top.return_value = [
            {"score": 9, "title": "Top Story", "source": "News", "banking_angle": "AI"},
            {"score": 7, "title": "Second", "source": "Tech", "banking_angle": "N/A"},
        ]
        result = _top_result(limit=10, days=3)

        assert result.status == "ok"
        assert result.count == 2
        assert result.days_window == 3
        assert "Top Story" in result.output
        assert "9/10" in result.output
        assert "Banking angle: AI" in result.output
        # N/A angle should NOT appear
        assert "Banking angle: N/A" not in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.top_cargo")
    def test_no_banking_angle(self, mock_top):
        mock_top.return_value = [
            {"score": 5, "title": "Plain", "source": "Feed"},
        ]
        result = _top_result(limit=5, days=1)

        assert "Banking angle" not in result.output
        assert result.items == mock_top.return_value


# ---------------------------------------------------------------------------
# endocytosis dispatch
# ---------------------------------------------------------------------------


class TestEndocytosisDispatch:
    @patch("metabolon.enzymes.endocytosis._status_result")
    def test_action_status(self, mock_status):
        mock_status.return_value = EndocytosisResult(output="status ok", status="ok")
        result = endocytosis(action="status")
        assert result.status == "ok"

    @patch("metabolon.enzymes.endocytosis._status_result")
    def test_action_status_case_insensitive(self, mock_status):
        mock_status.return_value = EndocytosisResult(output="ok", status="ok")
        endocytosis(action="STATUS")
        mock_status.assert_called_once()

    @patch("metabolon.organelles.endocytosis_rss.cli._fetch_locked")
    @patch("metabolon.organelles.endocytosis_rss.state.lockfile")
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_action_fetch(self, mock_cfg, mock_lockfile, mock_fetch):
        cfg = _make_config()
        mock_cfg.return_value = cfg
        mock_lockfile.return_value.__enter__ = MagicMock(return_value=None)
        mock_lockfile.return_value.__exit__ = MagicMock(return_value=False)

        result = endocytosis(action="fetch")

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert "Fetch cycle complete" in result.message
        mock_fetch.assert_called_once_with(cfg, False)

    @patch("metabolon.organelles.endocytosis_rss.cli._fetch_locked")
    @patch("metabolon.organelles.endocytosis_rss.state.lockfile")
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_action_fetch_no_archive(self, mock_cfg, mock_lockfile, mock_fetch):
        cfg = _make_config()
        mock_cfg.return_value = cfg
        mock_lockfile.return_value.__enter__ = MagicMock(return_value=None)
        mock_lockfile.return_value.__exit__ = MagicMock(return_value=False)

        result = endocytosis(action="fetch", no_archive=True)

        assert result.success is True
        assert result.data["no_archive"] is True
        mock_fetch.assert_called_once_with(cfg, True)

    @patch("metabolon.enzymes.endocytosis._stats_result")
    def test_action_stats(self, mock_stats):
        mock_stats.return_value = EndocytosisResult(output="stats", status="ok")
        result = endocytosis(action="stats")
        assert result.status == "ok"

    @patch("metabolon.enzymes.endocytosis._top_result")
    def test_action_top(self, mock_top):
        mock_top.return_value = EndocytosisResult(output="top", status="ok", count=3)
        result = endocytosis(action="top", limit=5, days=3)
        mock_top.assert_called_once_with(limit=5, days=3)
        assert result.count == 3

    def test_action_unknown(self):
        result = endocytosis(action="bogus")
        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "Unknown action" in result.message
        assert "status" in result.message

    def test_action_whitespace_handling(self):
        result = endocytosis(action="  STATUS  ")
        # status is dispatched (will fail due to no mock, but action IS recognized)
        # It will try to run _status_result which imports real modules —
        # so we just check it didn't return "unknown action"
        assert (
            not isinstance(result, EffectorResult)
            or result.success is True
            or "Unknown" not in result.message
        )
