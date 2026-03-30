"""Tests for glycolysis_rate — symbiont dependency ratio."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest


class TestMeasureRate:
    def test_returns_all_keys(self):
        from metabolon.organelles.glycolysis_rate import measure_rate
        result = measure_rate()
        assert "deterministic_count" in result
        assert "symbiont_count" in result
        assert "hybrid_count" in result
        assert "glycolysis_pct" in result
        assert "total" in result

    def test_counts_are_positive(self):
        from metabolon.organelles.glycolysis_rate import measure_rate
        result = measure_rate()
        assert result["deterministic_count"] > 0
        assert result["symbiont_count"] > 0
        assert result["total"] == result["deterministic_count"] + result["symbiont_count"] + result["hybrid_count"]

    def test_glycolysis_pct_range(self):
        from metabolon.organelles.glycolysis_rate import measure_rate
        result = measure_rate()
        assert 0 <= result["glycolysis_pct"] <= 100


class TestTrend:
    def test_no_snapshot_file(self, tmp_path):
        from metabolon.organelles.glycolysis_rate import trend
        import metabolon.organelles.glycolysis_rate as gr
        with patch.object(gr, "_SNAPSHOT_PATH", tmp_path / "nope.jsonl"):
            assert trend() == []

    def test_reads_snapshots(self, tmp_path):
        from metabolon.organelles.glycolysis_rate import trend
        import metabolon.organelles.glycolysis_rate as gr
        f = tmp_path / "snapshots.jsonl"
        entry = json.dumps({
            "timestamp": "2026-03-30T10:00:00",
            "glycolysis_pct": 65.0,
            "deterministic_count": 20,
            "symbiont_count": 10,
            "hybrid_count": 3,
        })
        f.write_text(entry + "\n")
        with patch.object(gr, "_SNAPSHOT_PATH", f):
            result = trend(days=7)
        assert len(result) == 1
        assert result[0]["glycolysis_pct"] == 65.0


class TestSnapshot:
    def test_appends_to_file(self, tmp_path):
        from metabolon.organelles.glycolysis_rate import snapshot
        import metabolon.organelles.glycolysis_rate as gr
        f = tmp_path / "snapshots.jsonl"
        with patch.object(gr, "_SNAPSHOT_PATH", f):
            snapshot()
        assert f.exists()
        data = json.loads(f.read_text().strip())
        assert "glycolysis_pct" in data
