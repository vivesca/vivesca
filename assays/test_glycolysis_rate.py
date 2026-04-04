from __future__ import annotations

"""Tests for glycolysis_rate — symbiont dependency ratio."""

import json
from unittest.mock import patch


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
        assert (
            result["total"]
            == result["deterministic_count"] + result["symbiont_count"] + result["hybrid_count"]
        )

    def test_glycolysis_pct_range(self):
        from metabolon.organelles.glycolysis_rate import measure_rate

        result = measure_rate()
        assert 0 <= result["glycolysis_pct"] <= 100


class TestTrend:
    def test_no_snapshot_file(self, tmp_path):
        import metabolon.organelles.glycolysis_rate as gr
        from metabolon.organelles.glycolysis_rate import trend

        with patch.object(gr, "_SNAPSHOT_PATH", tmp_path / "nope.jsonl"):
            assert trend() == []

    def test_reads_snapshots(self, tmp_path):
        import metabolon.organelles.glycolysis_rate as gr
        from metabolon.organelles.glycolysis_rate import trend

        f = tmp_path / "snapshots.jsonl"
        entry = json.dumps(
            {
                "timestamp": "2026-03-30T10:00:00",
                "glycolysis_pct": 65.0,
                "deterministic_count": 20,
                "symbiont_count": 10,
                "hybrid_count": 3,
            }
        )
        f.write_text(entry + "\n")
        with patch.object(gr, "_SNAPSHOT_PATH", f):
            result = trend(days=7)
        assert len(result) == 1
        assert result[0]["glycolysis_pct"] == 65.0


class TestSnapshot:
    def test_appends_to_file(self, tmp_path):
        import metabolon.organelles.glycolysis_rate as gr
        from metabolon.organelles.glycolysis_rate import snapshot

        f = tmp_path / "snapshots.jsonl"
        with patch.object(gr, "_SNAPSHOT_PATH", f):
            snapshot()
        assert f.exists()
        data = json.loads(f.read_text().strip())
        assert "glycolysis_pct" in data


class TestSuggestConversions:
    def test_returns_list_of_dicts(self):
        from metabolon.organelles.glycolysis_rate import suggest_conversions

        result = suggest_conversions()
        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)

    def test_each_suggestion_has_required_keys(self):
        from metabolon.organelles.glycolysis_rate import suggest_conversions

        result = suggest_conversions()
        required_keys = {
            "capability",
            "current_type",
            "reason",
            "effort",
            "dependencies",
            "priority",
        }
        for item in result:
            assert required_keys.issubset(item.keys())

    def test_current_type_is_symbiont_or_hybrid(self):
        from metabolon.organelles.glycolysis_rate import suggest_conversions

        result = suggest_conversions()
        for item in result:
            assert item["current_type"] in ("symbiont", "hybrid")

    def test_sorted_by_priority_descending(self):
        from metabolon.organelles.glycolysis_rate import suggest_conversions

        result = suggest_conversions()
        priorities = [item["priority"] for item in result]
        assert priorities == sorted(priorities, reverse=True)

    def test_effort_is_valid_value(self):
        from metabolon.organelles.glycolysis_rate import suggest_conversions

        result = suggest_conversions()
        valid_efforts = {"low", "medium", "high", "unknown"}
        for item in result:
            assert item["effort"] in valid_efforts

    def test_dependencies_is_list(self):
        from metabolon.organelles.glycolysis_rate import suggest_conversions

        result = suggest_conversions()
        for item in result:
            assert isinstance(item["dependencies"], list)


class TestGetConversionReport:
    def test_returns_required_keys(self):
        from metabolon.organelles.glycolysis_rate import get_conversion_report

        result = get_conversion_report()
        required_keys = {
            "total_symbiont",
            "total_hybrid",
            "conversion_candidates",
            "potential_glycolysis_gain",
            "potential_glycolysis_pct",
            "suggestions",
        }
        assert required_keys.issubset(result.keys())

    def test_suggestions_match_suggest_conversions(self):
        from metabolon.organelles.glycolysis_rate import get_conversion_report, suggest_conversions

        report = get_conversion_report()
        direct = suggest_conversions()
        assert len(report["suggestions"]) == len(direct)

    def test_potential_glycolysis_pct_higher_than_current(self):
        from metabolon.organelles.glycolysis_rate import get_conversion_report, measure_rate

        report = get_conversion_report()
        current = measure_rate()
        if report["conversion_candidates"] > 0:
            assert report["potential_glycolysis_pct"] >= current["glycolysis_pct"]

    def test_gain_is_non_negative(self):
        from metabolon.organelles.glycolysis_rate import get_conversion_report

        report = get_conversion_report()
        assert report["potential_glycolysis_gain"] >= 0

    def test_counts_are_non_negative(self):
        from metabolon.organelles.glycolysis_rate import get_conversion_report

        report = get_conversion_report()
        assert report["total_symbiont"] >= 0
        assert report["total_hybrid"] >= 0
        assert report["conversion_candidates"] >= 0
