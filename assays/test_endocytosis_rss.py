"""Tests for endocytosis enzyme analytics wiring.

Tests cover the inline JSONL analytics (stats and top) which are
deterministic and don't require network or lustro binary access.
The fetch/status tools are CLI-delegating and tested via integration only.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.enzymes.endocytosis import (
    _compute_stats,
    _get_top_items,
    _read_jsonl,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _ts(days_ago: int = 0) -> str:
    dt = datetime.now(UTC) - timedelta(days=days_ago)
    return dt.isoformat()


# ---------------------------------------------------------------------------
# _read_jsonl
# ---------------------------------------------------------------------------


class TestReadJsonl:
    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        p.write_text("")
        assert _read_jsonl(p) == []

    def test_missing_file(self, tmp_path):
        assert _read_jsonl(tmp_path / "nonexistent.jsonl") == []

    def test_reads_valid_rows(self, tmp_path):
        p = tmp_path / "data.jsonl"
        _write_jsonl(p, [{"a": 1}, {"b": 2}])
        rows = _read_jsonl(p)
        assert len(rows) == 2
        assert rows[0] == {"a": 1}

    def test_skips_blank_lines(self, tmp_path):
        p = tmp_path / "data.jsonl"
        p.write_text('{"a": 1}\n\n{"b": 2}\n')
        rows = _read_jsonl(p)
        assert len(rows) == 2

    def test_skips_malformed_lines(self, tmp_path):
        p = tmp_path / "data.jsonl"
        p.write_text('{"a": 1}\nnot json\n{"b": 2}\n')
        rows = _read_jsonl(p)
        assert len(rows) == 2


# ---------------------------------------------------------------------------
# _compute_stats
# ---------------------------------------------------------------------------


class TestComputeStats:
    def test_no_affinity_log_returns_insufficient(self, tmp_path):
        with (
            patch("metabolon.enzymes.endocytosis.AFFINITY_LOG", tmp_path / "missing.jsonl"),
            patch("metabolon.enzymes.endocytosis.ENGAGEMENT_LOG", tmp_path / "eng.jsonl"),
        ):
            result = _compute_stats()
        assert result["status"] == "insufficient_data"

    def test_basic_stats(self, tmp_path):
        aff = tmp_path / "relevance.jsonl"
        eng = tmp_path / "engagement.jsonl"
        _write_jsonl(
            aff,
            [
                {"title": "High signal", "source": "src", "score": 8, "timestamp": _ts(1)},
                {"title": "Low signal", "source": "src", "score": 2, "timestamp": _ts(1)},
                {"title": "Medium signal", "source": "src", "score": 5, "timestamp": _ts(1)},
            ],
        )
        _write_jsonl(eng, [{"title": "High signal", "action": "deepened"}])

        with (
            patch("metabolon.enzymes.endocytosis.AFFINITY_LOG", aff),
            patch("metabolon.enzymes.endocytosis.ENGAGEMENT_LOG", eng),
        ):
            result = _compute_stats()

        assert result["status"] == "ok"
        assert result["total_scored"] == 3
        assert result["total_engaged"] == 1
        # 2 of 3 items scored >= 5 → signal_ratio = 0.667
        assert result["signal_ratio"] == pytest.approx(2 / 3, abs=0.01)

    def test_false_positive_counted(self, tmp_path):
        aff = tmp_path / "relevance.jsonl"
        eng = tmp_path / "engagement.jsonl"
        _write_jsonl(
            aff,
            [
                {"title": "Hyped but useless", "source": "src", "score": 9, "timestamp": _ts(1)},
            ],
        )
        _write_jsonl(eng, [])  # never engaged

        with (
            patch("metabolon.enzymes.endocytosis.AFFINITY_LOG", aff),
            patch("metabolon.enzymes.endocytosis.ENGAGEMENT_LOG", eng),
        ):
            result = _compute_stats()

        assert result["false_positives_count"] == 1

    def test_false_negative_detected(self, tmp_path):
        aff = tmp_path / "relevance.jsonl"
        eng = tmp_path / "engagement.jsonl"
        _write_jsonl(
            aff,
            [
                {"title": "Underrated gem", "source": "src", "score": 3, "timestamp": _ts(1)},
            ],
        )
        _write_jsonl(eng, [{"title": "Underrated gem", "action": "deepened"}])

        with (
            patch("metabolon.enzymes.endocytosis.AFFINITY_LOG", aff),
            patch("metabolon.enzymes.endocytosis.ENGAGEMENT_LOG", eng),
        ):
            result = _compute_stats()

        assert "Underrated gem" in result["false_negatives"]


# ---------------------------------------------------------------------------
# _get_top_items
# ---------------------------------------------------------------------------


class TestGetTopItems:
    def test_returns_empty_when_no_data(self, tmp_path):
        with patch("metabolon.enzymes.endocytosis.AFFINITY_LOG", tmp_path / "missing.jsonl"):
            items = _get_top_items(limit=5, days=7)
        assert items == []

    def test_filters_by_window(self, tmp_path):
        aff = tmp_path / "relevance.jsonl"
        _write_jsonl(
            aff,
            [
                {"title": "Recent", "score": 7, "timestamp": _ts(1)},
                {"title": "Old", "score": 9, "timestamp": _ts(30)},
            ],
        )

        with patch("metabolon.enzymes.endocytosis.AFFINITY_LOG", aff):
            items = _get_top_items(limit=10, days=7)

        titles = [i["title"] for i in items]
        assert "Recent" in titles
        assert "Old" not in titles

    def test_sorted_by_score_descending(self, tmp_path):
        aff = tmp_path / "relevance.jsonl"
        _write_jsonl(
            aff,
            [
                {"title": "Low", "score": 3, "timestamp": _ts(1)},
                {"title": "High", "score": 9, "timestamp": _ts(1)},
                {"title": "Mid", "score": 6, "timestamp": _ts(1)},
            ],
        )

        with patch("metabolon.enzymes.endocytosis.AFFINITY_LOG", aff):
            items = _get_top_items(limit=10, days=7)

        assert items[0]["title"] == "High"
        assert items[1]["title"] == "Mid"
        assert items[2]["title"] == "Low"

    def test_respects_limit(self, tmp_path):
        aff = tmp_path / "relevance.jsonl"
        _write_jsonl(
            aff, [{"title": f"Item {i}", "score": i, "timestamp": _ts(1)} for i in range(10)]
        )

        with patch("metabolon.enzymes.endocytosis.AFFINITY_LOG", aff):
            items = _get_top_items(limit=3, days=7)

        assert len(items) == 3

    def test_skips_items_with_invalid_timestamp(self, tmp_path):
        aff = tmp_path / "relevance.jsonl"
        _write_jsonl(
            aff,
            [
                {"title": "Valid", "score": 8, "timestamp": _ts(1)},
                {"title": "Broken ts", "score": 9, "timestamp": "not-a-date"},
            ],
        )

        with patch("metabolon.enzymes.endocytosis.AFFINITY_LOG", aff):
            items = _get_top_items(limit=10, days=7)

        titles = [i["title"] for i in items]
        assert "Valid" in titles
        assert "Broken ts" not in titles


# ---------------------------------------------------------------------------
# Tool schemas (smoke test — verify tools are importable and callable)
# ---------------------------------------------------------------------------


class TestToolSchemas:
    def test_stats_tool_returns_secretion(self, tmp_path):
        from metabolon.enzymes.endocytosis import endocytosis

        aff = tmp_path / "relevance.jsonl"
        _write_jsonl(aff, [{"title": "T", "source": "s", "score": 6, "timestamp": _ts(1)}])

        with (
            patch("metabolon.enzymes.endocytosis.AFFINITY_LOG", aff),
            patch("metabolon.enzymes.endocytosis.ENGAGEMENT_LOG", tmp_path / "eng.jsonl"),
        ):
            result = endocytosis(action="stats")

        assert result.status == "ok"
        assert result.total_scored == 1

    def test_top_tool_returns_secretion(self, tmp_path):
        from metabolon.enzymes.endocytosis import endocytosis

        aff = tmp_path / "relevance.jsonl"
        _write_jsonl(aff, [{"title": "T", "source": "s", "score": 8, "timestamp": _ts(1)}])

        with patch("metabolon.enzymes.endocytosis.AFFINITY_LOG", aff):
            result = endocytosis(action="top", limit=5, days=7)

        assert result.count == 1
        assert result.items[0]["title"] == "T"

    def test_top_tool_empty_returns_empty_result(self, tmp_path):
        from metabolon.enzymes.endocytosis import endocytosis

        with patch("metabolon.enzymes.endocytosis.AFFINITY_LOG", tmp_path / "none.jsonl"):
            result = endocytosis(action="top")

        assert result.count == 0
        assert "No items" in result.summary

    def test_stats_insufficient_data(self, tmp_path):
        from metabolon.enzymes.endocytosis import endocytosis

        with (
            patch("metabolon.enzymes.endocytosis.AFFINITY_LOG", tmp_path / "none.jsonl"),
            patch("metabolon.enzymes.endocytosis.ENGAGEMENT_LOG", tmp_path / "none2.jsonl"),
        ):
            result = endocytosis(action="stats")

        assert result.status == "insufficient_data"
