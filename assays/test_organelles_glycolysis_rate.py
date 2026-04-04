from __future__ import annotations

import json
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from metabolon.organelles.glycolysis_rate import (
    _CONVERTIBLE_CAPABILITIES,
    _REGISTRY,
    get_conversion_report,
    measure_rate,
    snapshot,
    suggest_conversions,
    trend,
)


def test_measure_rate_basic():
    """Test measure_rate returns correct counts and percentage."""
    result = measure_rate()

    # Check that we have counts for all types
    assert result["deterministic_count"] > 0
    assert result["symbiont_count"] > 0
    assert result["hybrid_count"] > 0
    assert result["total"] == len(_REGISTRY)
    assert 0 <= result["glycolysis_pct"] <= 100

    # Recalculate manually to verify formula
    d = sum(1 for v in _REGISTRY.values() if v == "deterministic")
    s = sum(1 for v in _REGISTRY.values() if v == "symbiont")
    h = sum(1 for v in _REGISTRY.values() if v == "hybrid")
    total = d + s + h
    expected_pct = round(((d + h * 0.5) / total * 100) if total else 0.0, 1)

    assert result["deterministic_count"] == d
    assert result["symbiont_count"] == s
    assert result["hybrid_count"] == h
    assert result["glycolysis_pct"] == expected_pct


def test_measure_rate_empty_registry():
    """Test measure_rate handles empty registry."""
    with patch("metabolon.organelles.glycolysis_rate._REGISTRY", {}):
        result = measure_rate()
        assert result["deterministic_count"] == 0
        assert result["symbiont_count"] == 0
        assert result["hybrid_count"] == 0
        assert result["total"] == 0
        assert result["glycolysis_pct"] == 0.0


def test_trend_no_snapshot_file():
    """Test trend returns empty list when snapshot file doesn't exist."""
    with patch("metabolon.organelles.glycolysis_rate._SNAPSHOT_PATH") as mock_path:
        mock_path.exists.return_value = False
        result = trend(days=30)
        assert result == []


def test_trend_with_snapshots():
    """Test trend reads and filters snapshots correctly."""
    today = date.today()
    ten_days_ago = (today - timedelta(days=10)).isoformat()
    forty_days_ago = (today - timedelta(days=40)).isoformat()

    snapshots = [
        json.dumps(
            {
                "timestamp": f"{ten_days_ago}T10:00:00+00:00",
                "glycolysis_pct": 65.5,
                "deterministic_count": 40,
                "symbiont_count": 20,
                "hybrid_count": 5,
            }
        ),
        json.dumps(
            {
                "timestamp": f"{forty_days_ago}T10:00:00+00:00",
                "glycolysis_pct": 64.0,
                "deterministic_count": 39,
                "symbiont_count": 20,
                "hybrid_count": 5,
            }
        ),
    ]

    with patch("metabolon.organelles.glycolysis_rate._SNAPSHOT_PATH") as mock_path:
        mock_path.exists.return_value = True
        mock_file = MagicMock()
        mock_file.__enter__.return_value.readlines.return_value = snapshots
        mock_path.open.return_value = mock_file

        result = trend(days=30)
        # Only the 10-day-old entry should be included, 40-day is cutoff
        assert len(result) == 1
        assert result[0]["date"] == ten_days_ago
        assert result[0]["glycolysis_pct"] == 65.5


def test_trend_skips_invalid_entries():
    """Test trend skips invalid JSON and bad timestamps."""
    invalid_entries = [
        "not valid json",
        json.dumps({"timestamp": "bad-format", "glycolysis_pct": 50}),
        json.dumps({"timestamp": "2024-13-01T00:00:00", "glycolysis_pct": 50}),
    ]

    with patch("metabolon.organelles.glycolysis_rate._SNAPSHOT_PATH") as mock_path:
        mock_path.exists.return_value = True
        mock_file = MagicMock()
        mock_file.__enter__.return_value.readlines.return_value = invalid_entries
        mock_path.open.return_value = mock_file

        result = trend(days=30)
        assert len(result) == 0


def test_snapshot_creates_dir_and_writes():
    """Test snapshot creates parent dir and appends entry correctly."""
    mock_rate = {
        "deterministic_count": 40,
        "symbiont_count": 20,
        "hybrid_count": 5,
        "total": 65,
        "glycolysis_pct": 65.4,
    }

    with patch("metabolon.organelles.glycolysis_rate.measure_rate", return_value=mock_rate):
        with patch("metabolon.organelles.glycolysis_rate._SNAPSHOT_PATH") as mock_path:
            mock_parent = MagicMock()
            mock_path.parent = mock_parent
            mock_open = MagicMock()
            mock_path.open.return_value = mock_open
            mock_file = MagicMock()
            mock_open.__enter__.return_value = mock_file

            result = snapshot()

            # Check directory created
            mock_parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
            # Check file opened for append
            mock_path.open.assert_called_once_with("a")
            # Check json written
            assert mock_file.write.called
            # Check result is correct entry
            assert "timestamp" in result
            assert result["glycolysis_pct"] == mock_rate["glycolysis_pct"]


def test_suggest_conversions():
    """Test suggest_conversions returns correct sorted suggestions."""
    suggestions = suggest_conversions()

    # Should return all convertible capabilities that are in registry
    assert len(suggestions) == len(_CONVERTIBLE_CAPABILITIES)

    # Check sorted by priority descending
    priorities = [s["priority"] for s in suggestions]
    assert priorities == sorted(priorities, reverse=True)

    # Check priority calculation: low effort (3) + hybrid bonus (2) = 5 for rss_breaking
    for s in suggestions:
        if s["capability"] == "rss_breaking":
            assert s["current_type"] == "hybrid"
            assert s["priority"] == 3 + 2  # low effort + hybrid bonus
            break


def test_suggest_conversions_filters_missing_or_deterministic():
    """Test suggest_conversions filters out capabilities that are already deterministic."""
    test_convertible = {
        "test_cap": {
            "reason": "Test",
            "effort": "low",
            "dependencies": [],
        }
    }

    with patch("metabolon.organelles.glycolysis_rate._CONVERTIBLE_CAPABILITIES", test_convertible):
        with patch(
            "metabolon.organelles.glycolysis_rate._REGISTRY", {"test_cap": "deterministic"}
        ):
            suggestions = suggest_conversions()
            assert len(suggestions) == 0


def test_get_conversion_report():
    """Test get_conversion_report calculates potential gain correctly."""
    report = get_conversion_report()

    assert report["total_symbiont"] == measure_rate()["symbiont_count"]
    assert report["total_hybrid"] == measure_rate()["hybrid_count"]
    assert report["conversion_candidates"] == len(_CONVERTIBLE_CAPABILITIES)
    assert report["potential_glycolysis_gain"] >= 0
    assert (
        report["potential_glycolysis_pct"]
        == report["potential_glycolysis_gain"] + measure_rate()["glycolysis_pct"]
    )

    # Check potential gain calculation
    current_rate = measure_rate()
    suggestions = suggest_conversions()
    expected_gain = 0.0
    for s in suggestions:
        if s["current_type"] == "symbiont":
            expected_gain += 1.0
        elif s["current_type"] == "hybrid":
            expected_gain += 0.5

    total = current_rate["total"]
    current_de = current_rate["deterministic_count"] + current_rate["hybrid_count"] * 0.5
    new_de = current_de + expected_gain
    expected_pct = round((new_de / total * 100) if total else 0.0, 1)
    expected_gain_pct = round(expected_pct - current_rate["glycolysis_pct"], 1)

    assert report["potential_glycolysis_gain"] == expected_gain_pct
    assert report["potential_glycolysis_pct"] == expected_pct
