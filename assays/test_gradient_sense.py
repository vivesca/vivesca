from __future__ import annotations

"""Tests for gradient_sense — sensor array reading and polarity detection."""


import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.organelles.gradient_sense import (
    GradientReport,
    GradientVector,
    build_gradient_report,
    score_text,
    sense_endocytosis,
    sense_rheotaxis,
    sense_signals,
    topology_weight,
)

# ---------------------------------------------------------------------------
# TestTopologyWeight
# ---------------------------------------------------------------------------


class TestTopologyWeight:
    def test_empty_set(self) -> None:
        weight, label = topology_weight(set())
        assert weight == 0.0
        assert label == "single"

    def test_single_sensor(self) -> None:
        weight, label = topology_weight({"endocytosis_signal"})
        assert weight == 1.0
        assert label == "single"

    def test_two_adjacent_sensors(self) -> None:
        weight, label = topology_weight({"endocytosis_signal", "rheotaxis_queries"})
        assert weight == 1.5
        assert label == "adjacent"

    def test_two_independent_sensors(self) -> None:
        weight, label = topology_weight({"endocytosis_signal", "tool_signals"})
        assert weight == 2.0
        assert label == "independent"

    def test_two_independent_sensors_alt(self) -> None:
        weight, label = topology_weight({"rheotaxis_queries", "tool_signals"})
        assert weight == 2.0
        assert label == "independent"

    def test_three_sensors(self) -> None:
        weight, label = topology_weight(
            {"endocytosis_signal", "tool_signals", "rheotaxis_queries"}
        )
        assert weight == 3.0
        assert label == "full"


# ---------------------------------------------------------------------------
# TestScoreText (classify_text equivalent)
# ---------------------------------------------------------------------------


class TestScoreText:
    def test_ai_governance_match(self) -> None:
        hits = score_text("HKMA regulatory framework")
        assert "ai_governance" in hits
        assert hits["ai_governance"] >= 1

    def test_ai_models_match(self) -> None:
        hits = score_text("new GPT model benchmark")
        assert "ai_models" in hits
        assert hits["ai_models"] >= 1

    def test_banking_fintech_match(self) -> None:
        hits = score_text("banking fraud detection")
        assert "banking_fintech" in hits
        assert hits["banking_fintech"] >= 1

    def test_nonsense_returns_empty(self) -> None:
        hits = score_text("pure nonsense xyz123")
        assert hits == {}


# ---------------------------------------------------------------------------
# TestSenseEndocytosis — mocked relevance log
# ---------------------------------------------------------------------------


def _recent_timestamp() -> str:
    return (datetime.now(UTC) - timedelta(hours=1)).isoformat()


class TestSenseEndocytosis:
    @patch("metabolon.organelles.gradient_sense._RELEVANCE_LOG")
    def test_reads_domain_hits_and_titles(self, mock_path: Path, tmp_path: Path) -> None:
        entries = [
            {
                "score": 8,
                "timestamp": _recent_timestamp(),
                "title": "HKMA regulatory framework update",
            },
            {
                "score": 9,
                "timestamp": _recent_timestamp(),
                "title": "New GPT model benchmark results",
            },
        ]
        log_file = tmp_path / "relevance.jsonl"
        log_file.write_text(
            "\n".join(json.dumps(e) for e in entries), encoding="utf-8"
        )
        # Override the path constant by patching _read_jsonl to read our file
        with patch(
            "metabolon.organelles.gradient_sense._read_jsonl",
            return_value=entries,
        ):
            hits, titles = sense_endocytosis(days=7)

        assert "ai_governance" in hits
        assert "ai_models" in hits
        assert any("HKMA" in t for t in titles.get("ai_governance", []))

    def test_low_score_filtered(self) -> None:
        entries = [
            {
                "score": 3,
                "timestamp": _recent_timestamp(),
                "title": "HKMA regulatory framework update",
            },
        ]
        with patch(
            "metabolon.organelles.gradient_sense._read_jsonl",
            return_value=entries,
        ):
            hits, titles = sense_endocytosis(days=7)

        assert hits == {}
        assert titles == {}


# ---------------------------------------------------------------------------
# TestSenseSignals — mocked tool invocation log
# ---------------------------------------------------------------------------


class TestSenseSignals:
    def test_maps_tools_to_domains(self) -> None:
        entries = [
            {"ts": _recent_timestamp(), "tool": "rheotaxis"},
            {"ts": _recent_timestamp(), "tool": "rheotaxis"},
            {"ts": _recent_timestamp(), "tool": "circadian"},
        ]
        with patch(
            "metabolon.organelles.gradient_sense._read_jsonl",
            return_value=entries,
        ):
            hits = sense_signals(days=7)

        assert hits.get("ai_models") == 2
        assert hits.get("career_consulting") == 1

    def test_unknown_tool_ignored(self) -> None:
        entries = [
            {"ts": _recent_timestamp(), "tool": "nonexistent_tool_xyz"},
        ]
        with patch(
            "metabolon.organelles.gradient_sense._read_jsonl",
            return_value=entries,
        ):
            hits = sense_signals(days=7)

        assert hits == {}

    def test_old_entries_filtered(self) -> None:
        old_ts = (datetime.now(UTC) - timedelta(days=30)).isoformat()
        entries = [{"ts": old_ts, "tool": "rheotaxis"}]
        with patch(
            "metabolon.organelles.gradient_sense._read_jsonl",
            return_value=entries,
        ):
            hits = sense_signals(days=7)

        assert hits == {}


# ---------------------------------------------------------------------------
# TestSenseRheotaxis — mocked search query log
# ---------------------------------------------------------------------------


class TestSenseRheotaxis:
    def test_reads_domain_hits_and_queries(self, tmp_path: Path) -> None:
        log_file = tmp_path / "rheotaxis.jsonl"
        entry = json.dumps({
            "ts": _recent_timestamp(),
            "query": "HKMA regulatory framework for AI governance",
        })
        log_file.write_text(entry + "\n", encoding="utf-8")

        with patch("metabolon.organelles.gradient_sense._RHEOTAXIS_LOG", log_file):
            hits, queries = sense_rheotaxis(days=7)

        assert "ai_governance" in hits
        assert any("HKMA" in q for q in queries.get("ai_governance", []))

    def test_empty_query_skipped(self, tmp_path: Path) -> None:
        log_file = tmp_path / "rheotaxis.jsonl"
        entry = json.dumps({"ts": _recent_timestamp(), "query": ""})
        log_file.write_text(entry + "\n", encoding="utf-8")

        with patch("metabolon.organelles.gradient_sense._RHEOTAXIS_LOG", log_file):
            hits, queries = sense_rheotaxis(days=7)

        assert hits == {}
        assert queries == {}


# ---------------------------------------------------------------------------
# TestBuildGradientReport — integration with all sensors mocked
# ---------------------------------------------------------------------------


class TestBuildGradientReport:
    def test_returns_gradient_report(self) -> None:
        with (
            patch(
                "metabolon.organelles.gradient_sense.sense_endocytosis",
                return_value=({"ai_governance": 5}, {"ai_governance": ["HKMA framework"]}),
            ),
            patch(
                "metabolon.organelles.gradient_sense.sense_signals",
                return_value={"ai_governance": 3},
            ),
            patch(
                "metabolon.organelles.gradient_sense.sense_rheotaxis",
                return_value=({"ai_governance": 2}, {"ai_governance": ["EU AI Act query"]}),
            ),
        ):
            report = build_gradient_report(days=7)

        assert isinstance(report, GradientReport)
        assert report.polarity_vector == "ai_governance"
        assert len(report.gradients) >= 1

    def test_signal_strength_normalized(self) -> None:
        with (
            patch(
                "metabolon.organelles.gradient_sense.sense_endocytosis",
                return_value=({"ai_governance": 5, "banking_fintech": 1}, {}),
            ),
            patch(
                "metabolon.organelles.gradient_sense.sense_signals",
                return_value={"ai_governance": 3},
            ),
            patch(
                "metabolon.organelles.gradient_sense.sense_rheotaxis",
                return_value=({}, {}),
            ),
        ):
            report = build_gradient_report(days=7)

        for g in report.gradients:
            assert 0.0 <= g.signal_strength <= 1.0
        # Strongest domain should have strength 1.0
        assert report.gradients[0].signal_strength == 1.0

    def test_sensor_coverage_matches_active_sensors(self) -> None:
        with (
            patch(
                "metabolon.organelles.gradient_sense.sense_endocytosis",
                return_value=({"ai_governance": 5}, {}),
            ),
            patch(
                "metabolon.organelles.gradient_sense.sense_signals",
                return_value={"ai_governance": 3},
            ),
            patch(
                "metabolon.organelles.gradient_sense.sense_rheotaxis",
                return_value=({"ai_governance": 2}, {}),
            ),
        ):
            report = build_gradient_report(days=7)

        top = report.gradients[0]
        assert top.domain == "ai_governance"
        assert top.sensor_coverage == 3
        assert set(top.sensors.keys()) == {
            "endocytosis_signal",
            "tool_signals",
            "rheotaxis_queries",
        }

    def test_diffuse_when_no_data(self) -> None:
        with (
            patch(
                "metabolon.organelles.gradient_sense.sense_endocytosis",
                return_value=({}, {}),
            ),
            patch(
                "metabolon.organelles.gradient_sense.sense_signals",
                return_value={},
            ),
            patch(
                "metabolon.organelles.gradient_sense.sense_rheotaxis",
                return_value=({}, {}),
            ),
        ):
            report = build_gradient_report(days=7)

        assert report.polarity_vector == "diffuse"
        assert report.gradients == []
        assert report.interpretation != ""

    def test_single_sensor_unconfirmed(self) -> None:
        with (
            patch(
                "metabolon.organelles.gradient_sense.sense_endocytosis",
                return_value=({"ai_models": 3}, {}),
            ),
            patch(
                "metabolon.organelles.gradient_sense.sense_signals",
                return_value={},
            ),
            patch(
                "metabolon.organelles.gradient_sense.sense_rheotaxis",
                return_value=({}, {}),
            ),
        ):
            report = build_gradient_report(days=7)

        assert "single-sensor" in report.polarity_vector
        assert "ai_models" in report.polarity_vector

    def test_report_contains_sensors_read(self) -> None:
        with (
            patch(
                "metabolon.organelles.gradient_sense.sense_endocytosis",
                return_value=({"ai_governance": 2}, {}),
            ),
            patch(
                "metabolon.organelles.gradient_sense.sense_signals",
                return_value={},
            ),
            patch(
                "metabolon.organelles.gradient_sense.sense_rheotaxis",
                return_value=({}, {}),
            ),
        ):
            report = build_gradient_report(days=7)

        assert "endocytosis_signal" in report.sensors_read
        assert "tool_signals" not in report.sensors_read
