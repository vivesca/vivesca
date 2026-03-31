"""Tests for metabolon.enzymes.endocytosis — public API dispatch.

Covers EndocytosisResult construction and the endocytosis() tool
for all four actions (status, fetch, stats, top) plus edge cases.
All internal helpers use lazy imports inside function bodies,
so we patch at the *source* module, not on the enzyme module.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.endocytosis import EndocytosisResult, endocytosis
from metabolon.morphology import EffectorResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso(days_ago: int = 0) -> str:
    return (datetime.now(UTC) - timedelta(days=days_ago)).isoformat()


def _make_config(tmp_path: Path) -> SimpleNamespace:
    """Minimal config-like object with paths used by _status_result."""
    sources_path = tmp_path / "sources.yaml"
    state_path = tmp_path / "state.json"
    log_path = tmp_path / "news.log"
    cache_dir = tmp_path / "cache"
    sources_path.write_text("sources: []")
    state_path.write_text("{}")
    log_path.write_text("")
    cache_dir.mkdir()
    return SimpleNamespace(
        config_dir=tmp_path,
        sources_path=sources_path,
        state_path=state_path,
        log_path=log_path,
        article_cache_dir=cache_dir,
    )


# ---------------------------------------------------------------------------
# EndocytosisResult construction
# ---------------------------------------------------------------------------

class TestEndocytosisResult:
    def test_defaults(self):
        r = EndocytosisResult(output="hello")
        assert r.output == "hello"
        assert r.status == ""
        assert r.total_scored == 0
        assert r.signal_ratio == 0.0
        assert r.items == []

    def test_all_fields(self):
        r = EndocytosisResult(
            output="text",
            status="ok",
            total_scored=42,
            total_engaged=10,
            signal_ratio=0.238,
            avg_engaged_score=6.5,
            false_positives_count=2,
            false_negatives=["a", "b"],
            items=[{"title": "x"}],
            count=1,
            days_window=7,
        )
        assert r.status == "ok"
        assert r.total_scored == 42
        assert r.false_negatives == ["a", "b"]
        assert r.items[0]["title"] == "x"

    def test_extra_fields_allowed(self):
        """Secretion base allows extra fields."""
        r = EndocytosisResult(output="o", custom_field=99)
        assert r.custom_field == 99  # type: ignore[attr-defined]

    def test_empty_output(self):
        r = EndocytosisResult(output="")
        assert r.output == ""


# ---------------------------------------------------------------------------
# endocytosis("status", ...)
# ---------------------------------------------------------------------------

class TestStatusAction:
    @patch("metabolon.enzymes.endocytosis._status_result")
    def test_status_dispatches(self, mock_status):
        mock_status.return_value = EndocytosisResult(output="Status OK", status="ok")
        result = endocytosis(action="status")
        mock_status.assert_called_once()
        assert isinstance(result, EndocytosisResult)
        assert result.status == "ok"

    @patch("metabolon.enzymes.endocytosis._status_result")
    def test_status_case_insensitive(self, mock_status):
        mock_status.return_value = EndocytosisResult(output="ok", status="ok")
        endocytosis(action="STATUS")
        mock_status.assert_called_once()

    @patch("metabolon.enzymes.endocytosis._status_result")
    def test_status_strips_whitespace(self, mock_status):
        mock_status.return_value = EndocytosisResult(output="ok", status="ok")
        endocytosis(action="  status  ")
        mock_status.assert_called_once()


# ---------------------------------------------------------------------------
# endocytosis("fetch", ...)
# ---------------------------------------------------------------------------

class TestFetchAction:
    @patch("metabolon.organelles.endocytosis_rss.cli._fetch_locked")
    @patch("metabolon.organelles.endocytosis_rss.state.lockfile")
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_fetch_default(self, mock_config, mock_lockfile, mock_fetch):
        cfg = SimpleNamespace(state_path=Path("/tmp/dummy_state"))
        mock_config.return_value = cfg
        mock_lockfile.return_value.__enter__ = MagicMock()
        mock_lockfile.return_value.__exit__ = MagicMock(return_value=False)

        result = endocytosis(action="fetch")
        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert "Fetch cycle complete" in result.message
        mock_fetch.assert_called_once_with(cfg, False)

    @patch("metabolon.organelles.endocytosis_rss.cli._fetch_locked")
    @patch("metabolon.organelles.endocytosis_rss.state.lockfile")
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_fetch_no_archive(self, mock_config, mock_lockfile, mock_fetch):
        cfg = SimpleNamespace(state_path=Path("/tmp/dummy_state"))
        mock_config.return_value = cfg
        mock_lockfile.return_value.__enter__ = MagicMock()
        mock_lockfile.return_value.__exit__ = MagicMock(return_value=False)

        result = endocytosis(action="fetch", no_archive=True)
        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.data["no_archive"] is True
        mock_fetch.assert_called_once_with(cfg, True)


# ---------------------------------------------------------------------------
# endocytosis("stats", ...)
# ---------------------------------------------------------------------------

class TestStatsAction:
    @patch("metabolon.enzymes.endocytosis._stats_result")
    def test_stats_dispatches(self, mock_stats):
        mock_stats.return_value = EndocytosisResult(
            output="Signal ratio: 45%", status="ok", total_scored=100
        )
        result = endocytosis(action="stats")
        assert isinstance(result, EndocytosisResult)
        assert result.total_scored == 100

    @patch("metabolon.enzymes.endocytosis._stats_result")
    def test_stats_insufficient_data(self, mock_stats):
        mock_stats.return_value = EndocytosisResult(
            output="Insufficient data", status="insufficient_data"
        )
        result = endocytosis(action="stats")
        assert result.status == "insufficient_data"


# ---------------------------------------------------------------------------
# endocytosis("top", ...)
# ---------------------------------------------------------------------------

class TestTopAction:
    @patch("metabolon.enzymes.endocytosis._top_result")
    def test_top_with_results(self, mock_top):
        mock_top.return_value = EndocytosisResult(
            output="1. [8/10] Title — Source",
            items=[{"title": "Title", "score": 8}],
            count=1,
            days_window=7,
            status="ok",
        )
        result = endocytosis(action="top", limit=5, days=7)
        assert isinstance(result, EndocytosisResult)
        assert result.count == 1
        mock_top.assert_called_once_with(limit=5, days=7)

    @patch("metabolon.enzymes.endocytosis._top_result")
    def test_top_empty(self, mock_top):
        mock_top.return_value = EndocytosisResult(
            output="No items found in last 3 days.",
            items=[],
            count=0,
            days_window=3,
            status="ok",
        )
        result = endocytosis(action="top", limit=10, days=3)
        assert result.count == 0
        assert "No items" in result.output

    @patch("metabolon.enzymes.endocytosis._top_result")
    def test_top_default_params(self, mock_top):
        mock_top.return_value = EndocytosisResult(output="ok", status="ok")
        endocytosis(action="top")
        mock_top.assert_called_once_with(limit=10, days=7)


# ---------------------------------------------------------------------------
# Unknown action
# ---------------------------------------------------------------------------

class TestUnknownAction:
    def test_unknown_returns_error(self):
        result = endocytosis(action="bogus")
        assert isinstance(result, EffectorResult)
        assert result.success is False
        assert "Unknown action" in result.message
        assert "bogus" in result.message

    def test_empty_string_action(self):
        result = endocytosis(action="")
        assert isinstance(result, EffectorResult)
        assert result.success is False

    def test_whitespace_action(self):
        result = endocytosis(action="   ")
        assert isinstance(result, EffectorResult)
        assert result.success is False


# ---------------------------------------------------------------------------
# _status_result integration (mocked lazy-imported internals at source)
# ---------------------------------------------------------------------------

class TestStatusResultInternal:
    @patch("metabolon.organelles.endocytosis_rss.state.restore_state")
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_status_with_state(self, mock_config, mock_state, tmp_path):
        from metabolon.enzymes.endocytosis import _status_result

        cfg = _make_config(tmp_path)
        mock_config.return_value = cfg
        mock_state.return_value = {"feed1": _iso(1), "feed2": _iso(0)}

        with (
            patch("metabolon.organelles.endocytosis_rss.cli._file_age", return_value="1h ago"),
            patch("metabolon.organelles.endocytosis_rss.cli._parse_aware") as mock_parse,
        ):
            mock_parse.side_effect = lambda v: datetime.fromisoformat(v)
            result = _status_result()

        assert isinstance(result, EndocytosisResult)
        assert result.status == "ok"
        assert "Endocytosis Status" in result.output
        assert "tracked" in result.output

    @patch("metabolon.organelles.endocytosis_rss.state.restore_state")
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_status_empty_state(self, mock_config, mock_state, tmp_path):
        from metabolon.enzymes.endocytosis import _status_result

        cfg = _make_config(tmp_path)
        mock_config.return_value = cfg
        mock_state.return_value = {}

        with patch("metabolon.organelles.endocytosis_rss.cli._file_age", return_value="missing"):
            result = _status_result()

        assert result.status == "ok"
        assert "Endocytosis Status" in result.output

    @patch("metabolon.organelles.endocytosis_rss.state.restore_state")
    @patch("metabolon.organelles.endocytosis_rss.config.restore_config")
    def test_status_missing_cache_dir(self, mock_config, mock_state, tmp_path):
        from metabolon.enzymes.endocytosis import _status_result

        sources_path = tmp_path / "sources.yaml"
        state_path = tmp_path / "state.json"
        log_path = tmp_path / "news.log"
        sources_path.write_text("")
        state_path.write_text("{}")
        log_path.write_text("")

        cfg = SimpleNamespace(
            config_dir=tmp_path,
            sources_path=sources_path,
            state_path=state_path,
            log_path=log_path,
            article_cache_dir=tmp_path / "nope_no_cache",
        )
        mock_config.return_value = cfg
        mock_state.return_value = {}

        with patch("metabolon.organelles.endocytosis_rss.cli._file_age", return_value="missing"):
            result = _status_result()

        assert "missing" in result.output


# ---------------------------------------------------------------------------
# _stats_result integration (mocked lazy-imported internals at source)
# ---------------------------------------------------------------------------

class TestStatsResultInternal:
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    @patch("metabolon.enzymes.endocytosis.endocytosis_affinity", new_callable=lambda: MagicMock)
    def test_stats_empty_log(self, mock_path, mock_read):
        from metabolon.enzymes.endocytosis import _stats_result

        mock_read.return_value = []
        result = _stats_result()

        assert result.status == "insufficient_data"
        assert "no affinity log" in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_stats_full_data(self, mock_read, mock_astats):
        from metabolon.enzymes.endocytosis import _stats_result

        mock_read.return_value = [
            {"title": "Good article", "score": 8},
            {"title": "Meh article", "score": 3},
        ]
        mock_astats.return_value = {
            "status": "ok",
            "total_scored": 2,
            "total_engaged": 1,
            "avg_engaged_score": 7.5,
            "false_positives_count": 1,
            "false_negatives": ["Missed one"],
        }

        result = _stats_result()

        assert result.status == "ok"
        assert result.total_scored == 2
        assert result.total_engaged == 1
        assert result.signal_ratio == 0.5  # 1 out of 2 >= 5
        assert "false negatives" in result.output.lower()

    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_stats_insufficient_engagement(self, mock_read, mock_astats):
        from metabolon.enzymes.endocytosis import _stats_result

        mock_read.return_value = [{"title": "X", "score": 5}]
        mock_astats.return_value = {"status": "insufficient_data"}

        result = _stats_result()

        assert result.status == "insufficient_data"
        assert result.signal_ratio == 1.0  # 1/1 >= 5

    @patch("metabolon.organelles.endocytosis_rss.relevance.affinity_stats")
    @patch("metabolon.organelles.endocytosis_rss.relevance._read_jsonl")
    def test_stats_skips_empty_titles(self, mock_read, mock_astats):
        from metabolon.enzymes.endocytosis import _stats_result

        mock_read.return_value = [
            {"title": "", "score": 10},
            {"score": 5},  # no title key
            {"title": "Real", "score": 7},
        ]
        mock_astats.return_value = {"status": "ok", "total_scored": 1, "total_engaged": 0,
                                    "avg_engaged_score": 0.0, "false_positives_count": 0,
                                    "false_negatives": []}

        result = _stats_result()
        assert result.status == "ok"
        # Only "Real" counted (score >= 5) => signal_ratio = 1.0
        assert result.signal_ratio == 1.0


# ---------------------------------------------------------------------------
# _top_result integration (mocked lazy-imported internals at source)
# ---------------------------------------------------------------------------

class TestTopResultInternal:
    @patch("metabolon.organelles.endocytosis_rss.relevance.top_cargo")
    def test_top_empty(self, mock_top):
        from metabolon.enzymes.endocytosis import _top_result

        mock_top.return_value = []
        result = _top_result(limit=5, days=3)

        assert result.status == "ok"
        assert result.count == 0
        assert "No items found in last 3 days" in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.top_cargo")
    def test_top_with_items(self, mock_top):
        from metabolon.enzymes.endocytosis import _top_result

        mock_top.return_value = [
            {"score": 9, "title": "AI regulation", "source": "Ars", "banking_angle": "Compliance spend"},
            {"score": 7, "title": "Crypto bill", "source": "TechCrunch", "banking_angle": "N/A"},
        ]
        result = _top_result(limit=10, days=7)

        assert result.count == 2
        assert "AI regulation" in result.output
        assert "Banking angle: Compliance spend" in result.output
        # N/A banking angle should NOT appear
        assert "Banking angle: N/A" not in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.top_cargo")
    def test_top_missing_fields(self, mock_top):
        from metabolon.enzymes.endocytosis import _top_result

        mock_top.return_value = [
            {},  # completely empty dict
        ]
        result = _top_result(limit=5, days=1)

        assert result.count == 1
        assert "Untitled" in result.output
        assert "Unknown" in result.output

    @patch("metabolon.organelles.endocytosis_rss.relevance.top_cargo")
    def test_top_empty_banking_angle_stripped(self, mock_top):
        from metabolon.enzymes.endocytosis import _top_result

        mock_top.return_value = [
            {"score": 5, "title": "T", "source": "S", "banking_angle": "  "},
        ]
        result = _top_result(limit=5, days=7)

        assert "Banking angle" not in result.output
