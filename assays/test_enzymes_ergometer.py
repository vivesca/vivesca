from __future__ import annotations

from unittest.mock import patch

from metabolon.enzymes.ergometer import ergometer


def test_ergometer_unknown_action():
    """Test unknown action returns error message."""
    result = ergometer("invalid_action")
    assert "Unknown action" in result
    assert "speed|trend|slowest|coaching|eta" in result


@patch("metabolon.enzymes.ergometer.current_rate")
def test_ergometer_speed(mock_current_rate):
    """Test speed action returns formatted string."""
    mock_current_rate.return_value = 5.5
    result = ergometer("speed")
    assert result == "Dispatch rate: 5.5 tasks/hour (last 60 min)"
    mock_current_rate.assert_called_once()


@patch("metabolon.enzymes.ergometer.success_trend")
def test_ergometer_trend_improving(mock_success_trend):
    """Test trend action returns formatted improving trend."""
    mock_success_trend.return_value = {
        "recent_rate": 0.9,
        "recent_count": 10,
        "historical_rate": 0.8,
        "historical_count": 100,
        "delta": 0.1,
        "direction": "improving",
    }
    result = ergometer("trend")
    assert "Recent (10): 90.0%" in result
    assert "Historical (100): 80.0%" in result
    assert "Delta: +0.100 — improving" in result
    mock_success_trend.assert_called_once()


@patch("metabolon.enzymes.ergometer.success_trend")
def test_ergometer_trend_declining(mock_success_trend):
    """Test trend action returns formatted declining trend."""
    mock_success_trend.return_value = {
        "recent_rate": 0.7,
        "recent_count": 10,
        "historical_rate": 0.85,
        "historical_count": 100,
        "delta": -0.15,
        "direction": "declining",
    }
    result = ergometer("trend")
    assert "Recent (10): 70.0%" in result
    assert "Historical (100): 85.0%" in result
    assert "Delta: -0.150 — declining" in result


@patch("metabolon.enzymes.ergometer.success_trend")
def test_ergometer_trend_stable(mock_success_trend):
    """Test trend action returns formatted stable trend."""
    mock_success_trend.return_value = {
        "recent_rate": 0.85,
        "recent_count": 10,
        "historical_rate": 0.85,
        "historical_count": 100,
        "delta": 0.0,
        "direction": "stable",
    }
    result = ergometer("trend")
    assert "Delta: +0.000 — stable" in result


@patch("metabolon.enzymes.ergometer.slowest_recent")
def test_ergometer_slowest_found(mock_slowest_recent):
    """Test slowest action returns formatted slowest task."""
    mock_slowest_recent.return_value = {
        "plan": "test-plan",
        "duration_s": 123.4,
        "tool": "test-tool",
        "timestamp": "2026-04-01T10:00:00",
        "success": True,
    }
    result = ergometer("slowest", hours=24)
    assert "Plan: test-plan" in result
    assert "Duration: 123.4s" in result
    assert "Tool: test-tool" in result
    assert "Timestamp: 2026-04-01T10:00:00" in result
    assert "Success: True" in result
    mock_slowest_recent.assert_called_once_with(hours=24)


@patch("metabolon.enzymes.ergometer.slowest_recent")
def test_ergometer_slowest_none(mock_slowest_recent):
    """Test slowest returns correct message when no tasks found."""
    mock_slowest_recent.return_value = None
    result = ergometer("slowest")
    assert result == "No tasks in window."


@patch("metabolon.enzymes.ergometer.coaching_effectiveness")
def test_ergometer_coaching(mock_coaching_effectiveness):
    """Test coaching action returns formatted effectiveness."""
    mock_coaching_effectiveness.return_value = {
        "before_failure_rate": 0.25,
        "after_failure_rate": 0.10,
        "improvement_pct": 15.0,
        "notes_analyzed": 5,
        "total_entries": 200,
    }
    result = ergometer("coaching")
    assert "Before coaching failure rate: 25.0%" in result
    assert "After coaching failure rate:  10.0%" in result
    assert "Improvement: +15.0pp" in result
    assert "Notes analyzed: 5 over 200 entries" in result
    mock_coaching_effectiveness.assert_called_once()


@patch("metabolon.enzymes.ergometer.estimate_completion")
def test_ergometer_eta(mock_estimate_completion):
    """Test eta action returns formatted completion estimate."""
    mock_estimate_completion.return_value = 4.5
    result = ergometer("eta", remaining_tasks=10)
    assert result == "Estimated completion: 4.5 hours for 10 remaining tasks"
    mock_estimate_completion.assert_called_once_with(remaining_tasks=10)


def test_ergometer_action_case_insensitive():
    """Test action is case-insensitive."""
    with patch("metabolon.enzymes.ergometer.current_rate") as mock_current_rate:
        mock_current_rate.return_value = 2.0
        result = ergometer("SPEED")
        assert "Dispatch rate" in result
        mock_current_rate.assert_called_once()


def test_ergometer_action_strips_whitespace():
    """Test action strips whitespace."""
    with patch("metabolon.enzymes.ergometer.current_rate") as mock_current_rate:
        mock_current_rate.return_value = 3.0
        result = ergometer("  speed  ")
        assert "Dispatch rate" in result
        mock_current_rate.assert_called_once()
