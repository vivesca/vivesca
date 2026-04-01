from __future__ import annotations

"""Tests for gradient_sense organelle."""


import json
import datetime
from pathlib import Path
from unittest import mock

import pytest

from metabolon.organelles.gradient_sense import (
    topology_weight,
    score_text,
    _read_jsonl,
    sense_endocytosis,
    sense_signals,
    sense_rheotaxis,
    build_gradient_report,
    GradientVector,
    GradientReport,
)


def test_topology_weight_single_sensor():
    """Test topology_weight with single active sensor."""
    weight, bonus = topology_weight({"endocytosis_signal"})
    assert weight == 1.0
    assert bonus == "single"


def test_topology_weight_adjacent_pair():
    """Test topology_weight with adjacent sensor pair."""
    weight, bonus = topology_weight({"endocytosis_signal", "rheotaxis_queries"})
    assert weight == 1.5
    assert bonus == "adjacent"


def test_topology_weight_independent_pair():
    """Test topology_weight with independent sensor pair."""
    weight, bonus = topology_weight({"endocytosis_signal", "tool_signals"})
    assert weight == 2.0
    assert bonus == "independent"


def test_topology_weight_all_three_sensors():
    """Test topology_weight with all three sensors active."""
    weight, bonus = topology_weight(
        {"endocytosis_signal", "tool_signals", "rheotaxis_queries"}
    )
    assert weight == 3.0
    assert bonus == "full"


def test_score_text_no_hits():
    """Test score_text returns empty dict when no keywords match."""
    result = score_text("This is a completely unrelated text about nothing.")
    assert result == {}


def test_score_text_single_domain_hits():
    """Test score_text returns hits for single domain."""
    result = score_text("GPT-4o model release with new reasoning capabilities.")
    assert "ai_models" in result
    assert result["ai_models"] > 0


def test_score_text_multiple_domain_hits():
    """Test score_text returns hits for multiple domains."""
    result = score_text(
        "New regulatory framework for AI governance and model deployment."
    )
    assert "ai_governance" in result
    assert "ai_models" in result or "ai_infra" in result


def test_read_jsonl_nonexistent_file(tmp_path):
    """Test _read_jsonl returns empty list for nonexistent file."""
    path = tmp_path / "nonexistent.jsonl"
    result = _read_jsonl(path)
    assert result == []


def test_read_jsonl_empty_file(tmp_path):
    """Test _read_jsonl returns empty list for empty file."""
    path = tmp_path / "empty.jsonl"
    path.write_text("")
    result = _read_jsonl(path)
    assert result == []


def test_read_jsonl_valid_entries(tmp_path):
    """Test _read_jsonl reads valid JSONL entries correctly."""
    path = tmp_path / "test.jsonl"
    entries = [{"a": 1}, {"b": 2}, {"c": 3}]
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    result = _read_jsonl(path)
    assert result == entries


def test_read_jsonl_skips_invalid_json(tmp_path):
    """Test _read_jsonl skips invalid JSON lines."""
    path = tmp_path / "test.jsonl"
    with open(path, "w") as f:
        f.write('{"valid": true}\n')
        f.write("not valid json\n")
        f.write('{"another_valid": 42}\n')
    result = _read_jsonl(path)
    assert len(result) == 2
    assert result[0]["valid"] is True
    assert result[1]["another_valid"] == 42


def test_sense_endocytosis_no_file():
    """Test sense_endocytosis returns empty when file doesn't exist."""
    with mock.patch("metabolon.organelles.gradient_sense._RELEVANCE_LOG", Path("/does/not/exist")):
        hits, titles = sense_endocytosis(days=7)
        assert hits == {}
        assert titles == {}


def test_sense_endocytosis_with_mocked_file(tmp_path):
    """Test sense_endocytosis with a mocked relevance log file."""
    test_file = tmp_path / "relevance.jsonl"
    test_entries = [
        {
            "score": 8,
            "timestamp": "2026-03-30T00:00:00+00:00",
            "title": "New Claude model release with enhanced reasoning capabilities",
        },
        {
            "score": 7,
            "timestamp": "2026-03-29T00:00:00+00:00",
            "title": "AI governance policy update from EU",
        },
        {
            "score": 5,  # Too low, should be ignored
            "timestamp": "2026-03-28T00:00:00+00:00",
            "title": "Something else",
        },
    ]
    with open(test_file, "w") as f:
        for entry in test_entries:
            f.write(json.dumps(entry) + "\n")

    with mock.patch("metabolon.organelles.gradient_sense._RELEVANCE_LOG", test_file):
        hits, titles = sense_endocytosis(days=7)
        assert "ai_models" in hits
        assert "ai_governance" in hits
        assert len(titles["ai_models"]) == 1
        assert len(titles["ai_governance"]) == 1


def test_sense_signals_no_file():
    """Test sense_signals returns empty when file doesn't exist."""
    with mock.patch("metabolon.organelles.gradient_sense._SIGNALS_LOG", Path("/does/not/exist")):
        hits = sense_signals(days=7)
        assert hits == {}


def test_sense_signals_with_mocked_file(tmp_path):
    """Test sense_signals with a mocked signals log file."""
    test_file = tmp_path / "signals.jsonl"
    test_entries = [
        {"ts": "2026-03-30T00:00:00+00:00", "tool": "rheotaxis_search"},
        {"ts": "2026-03-29T00:00:00+00:00", "tool": "homeostasis_system"},
        {"ts": "2026-03-28T00:00:00+00:00", "tool": "nonexistent_tool"},  # Not in _TOOL_DOMAINS
    ]
    with open(test_file, "w") as f:
        for entry in test_entries:
            f.write(json.dumps(entry) + "\n")

    with mock.patch("metabolon.organelles.gradient_sense._SIGNALS_LOG", test_file):
        hits = sense_signals(days=7)
        assert "ai_models" in hits
        assert hits["ai_models"] == 1
        assert "ai_infra" in hits
        assert hits["ai_infra"] == 1


def test_sense_rheotaxis_no_file():
    """Test sense_rheotaxis returns empty when file doesn't exist."""
    with mock.patch("metabolon.organelles.gradient_sense._RHEOTAXIS_LOG", Path("/does/not/exist")):
        hits, queries = sense_rheotaxis(days=7)
        assert hits == {}
        assert queries == {}


def test_build_gradient_report_empty():
    """Test build_gradient_report with no sensors returning data."""
    with mock.patch(
        "metabolon.organelles.gradient_sense.sense_endocytosis",
        return_value=({}, {}),
    ), mock.patch(
        "metabolon.organelles.gradient_sense.sense_signals",
        return_value={},
    ), mock.patch(
        "metabolon.organelles.gradient_sense.sense_rheotaxis",
        return_value=({}, {}),
    ):
        report = build_gradient_report(days=7)
        assert report.polarity_vector == "diffuse"
        assert len(report.gradients) == 0
        assert len(report.sensors_read) == 0


def test_build_gradient_report_single_sensor():
    """Test build_gradient_report with single sensor active."""
    with mock.patch(
        "metabolon.organelles.gradient_sense.sense_endocytosis",
        return_value=({"ai_models": 5}, {"ai_models": ["Model A release"]}),
    ), mock.patch(
        "metabolon.organelles.gradient_sense.sense_signals",
        return_value={},
    ), mock.patch(
        "metabolon.organelles.gradient_sense.sense_rheotaxis",
        return_value=({}, {}),
    ):
        report = build_gradient_report(days=7)
        assert "single-sensor" in report.polarity_vector
        assert len(report.gradients) == 1
        assert report.gradients[0].sensor_coverage == 1


def test_build_gradient_report_multiple_sensors():
    """Test build_gradient_report with multiple sensors active."""
    with mock.patch(
        "metabolon.organelles.gradient_sense.sense_endocytosis",
        return_value=({"ai_models": 5, "ai_governance": 3}, {"ai_models": ["Model A"]}),
    ), mock.patch(
        "metabolon.organelles.gradient_sense.sense_signals",
        return_value={"ai_models": 2},
    ), mock.patch(
        "metabolon.organelles.gradient_sense.sense_rheotaxis",
        return_value=({"ai_models": 3}, {"ai_models": ["How does Claude work?"]}),
    ):
        report = build_gradient_report(days=7)
        assert "ai_models" in report.polarity_vector
        assert len(report.gradients) >= 1
        assert report.gradients[0].sensor_coverage >= 2
        assert report.gradients[0].signal_strength == 1.0
