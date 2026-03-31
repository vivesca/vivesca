from __future__ import annotations

"""Tests for metabolon/enzymes/tachometer.py"""


from datetime import datetime
from unittest.mock import patch

import pytest


class TestTachometerSpeed:
    """Tests for speed action."""

    @patch("metabolon.enzymes.tachometer.current_rate")
    def test_speed_returns_formatted_rate(self, mock_rate):
        mock_rate.return_value = 12.5
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("speed")
        assert result == "Dispatch rate: 12.5 tasks/hour (last 60 min)"
        mock_rate.assert_called_once()

    @patch("metabolon.enzymes.tachometer.current_rate")
    def test_speed_zero_rate(self, mock_rate):
        mock_rate.return_value = 0.0
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("speed")
        assert result == "Dispatch rate: 0.0 tasks/hour (last 60 min)"

    @patch("metabolon.enzymes.tachometer.current_rate")
    def test_speed_high_rate(self, mock_rate):
        mock_rate.return_value = 156.789
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("speed")
        assert result == "Dispatch rate: 156.8 tasks/hour (last 60 min)"


class TestTachometerTrend:
    """Tests for trend action."""

    @patch("metabolon.enzymes.tachometer.success_trend")
    def test_trend_improving(self, mock_trend):
        mock_trend.return_value = {
            "recent_rate": 0.85,
            "recent_count": 10,
            "historical_rate": 0.70,
            "historical_count": 100,
            "delta": 0.15,
            "direction": "improving",
        }
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("trend")
        assert "Recent (10): 85.0%" in result
        assert "Historical (100): 70.0%" in result
        assert "Delta: +0.150" in result
        assert "improving" in result

    @patch("metabolon.enzymes.tachometer.success_trend")
    def test_trend_declining(self, mock_trend):
        mock_trend.return_value = {
            "recent_rate": 0.50,
            "recent_count": 10,
            "historical_rate": 0.80,
            "historical_count": 100,
            "delta": -0.30,
            "direction": "declining",
        }
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("trend")
        assert "Delta: -0.300" in result
        assert "declining" in result

    @patch("metabolon.enzymes.tachometer.success_trend")
    def test_trend_stable(self, mock_trend):
        mock_trend.return_value = {
            "recent_rate": 0.75,
            "recent_count": 10,
            "historical_rate": 0.74,
            "historical_count": 100,
            "delta": 0.01,
            "direction": "stable",
        }
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("trend")
        assert "stable" in result

    @patch("metabolon.enzymes.tachometer.success_trend")
    def test_trend_no_data(self, mock_trend):
        mock_trend.return_value = {
            "recent_rate": 0.0,
            "recent_count": 0,
            "historical_rate": 0.0,
            "historical_count": 0,
            "delta": 0.0,
            "direction": "no data",
        }
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("trend")
        assert "Recent (0): 0.0%" in result
        assert "no data" in result


class TestTachometerSlowest:
    """Tests for slowest action."""

    @patch("metabolon.enzymes.tachometer.slowest_recent")
    def test_slowest_returns_formatted_task(self, mock_slowest):
        mock_slowest.return_value = {
            "plan": "golem-review-42",
            "duration_s": 125.5,
            "tool": "reviewer",
            "timestamp": "2026-04-01T10:30:00",
            "success": True,
        }
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("slowest")
        assert "Plan: golem-review-42" in result
        assert "Duration: 125.5s" in result
        assert "Tool: reviewer" in result
        assert "Timestamp: 2026-04-01T10:30:00" in result
        assert "Success: True" in result

    @patch("metabolon.enzymes.tachometer.slowest_recent")
    def test_slowest_failed_task(self, mock_slowest):
        mock_slowest.return_value = {
            "plan": "failing-plan",
            "duration_s": 300.0,
            "tool": "builder",
            "timestamp": "2026-04-01T09:00:00",
            "success": False,
        }
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("slowest")
        assert "Success: False" in result

    @patch("metabolon.enzymes.tachometer.slowest_recent")
    def test_slowest_no_tasks(self, mock_slowest):
        mock_slowest.return_value = None
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("slowest")
        assert result == "No tasks in window."

    @patch("metabolon.enzymes.tachometer.slowest_recent")
    def test_slowest_with_custom_hours(self, mock_slowest):
        mock_slowest.return_value = {
            "plan": "test-plan",
            "duration_s": 50.0,
            "tool": "tester",
            "timestamp": "2026-04-01T08:00:00",
            "success": True,
        }
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("slowest", hours=4)
        mock_slowest.assert_called_once_with(hours=4)
        assert "Plan: test-plan" in result


class TestTachometerCoaching:
    """Tests for coaching action."""

    @patch("metabolon.enzymes.tachometer.coaching_effectiveness")
    def test_coaching_shows_improvement(self, mock_coaching):
        mock_coaching.return_value = {
            "before_failure_rate": 0.35,
            "after_failure_rate": 0.15,
            "improvement_pct": 20.0,
            "notes_analyzed": 5,
            "total_entries": 150,
        }
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("coaching")
        assert "Before coaching failure rate: 35.0%" in result
        assert "After coaching failure rate:  15.0%" in result
        assert "Improvement: +20.0pp" in result
        assert "Notes analyzed: 5" in result
        assert "over 150 entries" in result

    @patch("metabolon.enzymes.tachometer.coaching_effectiveness")
    def test_coaching_negative_improvement(self, mock_coaching):
        mock_coaching.return_value = {
            "before_failure_rate": 0.10,
            "after_failure_rate": 0.25,
            "improvement_pct": -15.0,
            "notes_analyzed": 3,
            "total_entries": 80,
        }
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("coaching")
        assert "Improvement: -15.0pp" in result

    @patch("metabolon.enzymes.tachometer.coaching_effectiveness")
    def test_coaching_no_data(self, mock_coaching):
        mock_coaching.return_value = {
            "before_failure_rate": 0.0,
            "after_failure_rate": 0.0,
            "improvement_pct": 0.0,
            "notes_analyzed": 0,
            "total_entries": 0,
        }
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("coaching")
        assert "Notes analyzed: 0" in result


class TestTachometerEta:
    """Tests for eta action."""

    @patch("metabolon.enzymes.tachometer.estimate_completion")
    def test_eta_returns_formatted_estimate(self, mock_eta):
        mock_eta.return_value = 2.5
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("eta", remaining_tasks=10)
        assert result == "Estimated completion: 2.5 hours for 10 remaining tasks"
        mock_eta.assert_called_once_with(remaining_tasks=10)

    @patch("metabolon.enzymes.tachometer.estimate_completion")
    def test_eta_zero_tasks(self, mock_eta):
        mock_eta.return_value = 0.0
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("eta", remaining_tasks=0)
        assert "0.0 hours for 0 remaining tasks" in result

    @patch("metabolon.enzymes.tachometer.estimate_completion")
    def test_eta_large_task_count(self, mock_eta):
        mock_eta.return_value = 125.7
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("eta", remaining_tasks=500)
        assert "125.7 hours for 500 remaining tasks" in result


class TestTachometerUnknownAction:
    """Tests for unknown action handling."""

    def test_unknown_action_returns_error_message(self):
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("invalid")
        assert "Unknown action: invalid" in result
        assert "speed|trend|slowest|coaching|eta" in result

    def test_unknown_action_case_preserved(self):
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("UNKNOWN")
        assert "Unknown action: unknown" in result  # action is lowercased


class TestTachometerActionCaseHandling:
    """Tests for action case normalization."""

    @patch("metabolon.enzymes.tachometer.current_rate")
    def test_action_case_insensitive_uppercase(self, mock_rate):
        mock_rate.return_value = 5.0
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("SPEED")
        assert "Dispatch rate: 5.0 tasks/hour" in result

    @patch("metabolon.enzymes.tachometer.current_rate")
    def test_action_case_insensitive_mixedcase(self, mock_rate):
        mock_rate.return_value = 5.0
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("SpEeD")
        assert "Dispatch rate: 5.0 tasks/hour" in result

    @patch("metabolon.enzymes.tachometer.current_rate")
    def test_action_with_whitespace(self, mock_rate):
        mock_rate.return_value = 5.0
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer("  speed  ")
        assert "Dispatch rate: 5.0 tasks/hour" in result
