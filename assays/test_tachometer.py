"""Tests for metabolon.enzymes.tachometer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestTachometerSpeed:
    """Tests for the speed action."""

    @patch("metabolon.enzymes.tachometer.current_rate")
    def test_speed_returns_formatted_rate(self, mock_current_rate: MagicMock) -> None:
        """Return formatted dispatch rate."""
        from metabolon.enzymes.tachometer import tachometer

        mock_current_rate.return_value = 12.5
        result = tachometer(action="speed")

        assert result == "Dispatch rate: 12.5 tasks/hour (last 60 min)"
        mock_current_rate.assert_called_once()

    @patch("metabolon.enzymes.tachometer.current_rate")
    def test_speed_zero_rate(self, mock_current_rate: MagicMock) -> None:
        """Handle zero rate correctly."""
        from metabolon.enzymes.tachometer import tachometer

        mock_current_rate.return_value = 0.0
        result = tachometer(action="speed")

        assert result == "Dispatch rate: 0.0 tasks/hour (last 60 min)"


class TestTachometerTrend:
    """Tests for the trend action."""

    @patch("metabolon.enzymes.tachometer.success_trend")
    def test_trend_improving(self, mock_success_trend: MagicMock) -> None:
        """Return formatted trend showing improvement."""
        from metabolon.enzymes.tachometer import tachometer

        mock_success_trend.return_value = {
            "recent_rate": 0.90,
            "recent_count": 10,
            "historical_rate": 0.75,
            "historical_count": 100,
            "delta": 0.15,
            "direction": "improving",
        }
        result = tachometer(action="trend")

        assert "Recent (10): 90.0%" in result
        assert "Historical (100): 75.0%" in result
        assert "Delta: +0.150" in result
        assert "improving" in result

    @patch("metabolon.enzymes.tachometer.success_trend")
    def test_trend_declining(self, mock_success_trend: MagicMock) -> None:
        """Return formatted trend showing decline."""
        from metabolon.enzymes.tachometer import tachometer

        mock_success_trend.return_value = {
            "recent_rate": 0.60,
            "recent_count": 10,
            "historical_rate": 0.80,
            "historical_count": 50,
            "delta": -0.20,
            "direction": "declining",
        }
        result = tachometer(action="trend")

        assert "Delta: -0.200" in result
        assert "declining" in result


class TestTachometerSlowest:
    """Tests for the slowest action."""

    @patch("metabolon.enzymes.tachometer.slowest_recent")
    def test_slowest_with_result(self, mock_slowest_recent: MagicMock) -> None:
        """Return formatted slowest task info."""
        from metabolon.enzymes.tachometer import tachometer

        mock_slowest_recent.return_value = {
            "plan": "golem-reviewer",
            "duration_s": 45.2,
            "tool": "read_file",
            "timestamp": "2026-04-01T10:30:00",
            "success": True,
        }
        result = tachometer(action="slowest", hours=2)

        assert "Plan: golem-reviewer" in result
        assert "Duration: 45.2s" in result
        assert "Tool: read_file" in result
        assert "Timestamp: 2026-04-01T10:30:00" in result
        assert "Success: True" in result
        mock_slowest_recent.assert_called_once_with(hours=2)

    @patch("metabolon.enzymes.tachometer.slowest_recent")
    def test_slowest_no_tasks(self, mock_slowest_recent: MagicMock) -> None:
        """Handle case when no tasks in window."""
        from metabolon.enzymes.tachometer import tachometer

        mock_slowest_recent.return_value = None
        result = tachometer(action="slowest")

        assert result == "No tasks in window."

    @patch("metabolon.enzymes.tachometer.slowest_recent")
    def test_slowest_failed_task(self, mock_slowest_recent: MagicMock) -> None:
        """Show failure status correctly."""
        from metabolon.enzymes.tachometer import tachometer

        mock_slowest_recent.return_value = {
            "plan": "test-plan",
            "duration_s": 10.0,
            "tool": "write_file",
            "timestamp": "2026-04-01T11:00:00",
            "success": False,
        }
        result = tachometer(action="slowest")

        assert "Success: False" in result


class TestTachometerCoaching:
    """Tests for the coaching action."""

    @patch("metabolon.enzymes.tachometer.coaching_effectiveness")
    def test_coaching_with_improvement(self, mock_coaching: MagicMock) -> None:
        """Return formatted coaching effectiveness showing improvement."""
        from metabolon.enzymes.tachometer import tachometer

        mock_coaching.return_value = {
            "before_failure_rate": 0.25,
            "after_failure_rate": 0.10,
            "improvement_pct": 15.0,
            "notes_analyzed": 5,
            "total_entries": 100,
        }
        result = tachometer(action="coaching")

        assert "Before coaching failure rate: 25.0%" in result
        assert "After coaching failure rate:  10.0%" in result
        assert "Improvement: +15.0pp" in result
        assert "Notes analyzed: 5" in result
        assert "over 100 entries" in result

    @patch("metabolon.enzymes.tachometer.coaching_effectiveness")
    def test_coaching_no_change(self, mock_coaching: MagicMock) -> None:
        """Handle case with no improvement."""
        from metabolon.enzymes.tachometer import tachometer

        mock_coaching.return_value = {
            "before_failure_rate": 0.20,
            "after_failure_rate": 0.20,
            "improvement_pct": 0.0,
            "notes_analyzed": 3,
            "total_entries": 50,
        }
        result = tachometer(action="coaching")

        assert "Improvement: +0.0pp" in result


class TestTachometerEta:
    """Tests for the eta action."""

    @patch("metabolon.enzymes.tachometer.estimate_completion")
    def test_eta_with_tasks(self, mock_estimate: MagicMock) -> None:
        """Return formatted ETA for remaining tasks."""
        from metabolon.enzymes.tachometer import tachometer

        mock_estimate.return_value = 2.5
        result = tachometer(action="eta", remaining_tasks=10)

        assert result == "Estimated completion: 2.5 hours for 10 remaining tasks"
        mock_estimate.assert_called_once_with(remaining_tasks=10)

    @patch("metabolon.enzymes.tachometer.estimate_completion")
    def test_eta_zero_tasks(self, mock_estimate: MagicMock) -> None:
        """Handle zero remaining tasks."""
        from metabolon.enzymes.tachometer import tachometer

        mock_estimate.return_value = 0.0
        result = tachometer(action="eta", remaining_tasks=0)

        assert "0.0 hours for 0 remaining tasks" in result


class TestTachometerInvalidAction:
    """Tests for invalid actions."""

    def test_unknown_action_returns_error(self) -> None:
        """Return error message for unknown action."""
        from metabolon.enzymes.tachometer import tachometer

        result = tachometer(action="invalid")

        assert "Unknown action: invalid" in result
        assert "speed|trend|slowest|coaching|eta" in result

    def test_action_case_insensitive(self) -> None:
        """Handle uppercase action names."""
        from metabolon.enzymes.tachometer import tachometer

        with patch("metabolon.enzymes.tachometer.current_rate") as mock_rate:
            mock_rate.return_value = 5.0
            result = tachometer(action="SPEED")

            assert "Dispatch rate: 5.0 tasks/hour" in result

    def test_action_with_whitespace(self) -> None:
        """Handle action with leading/trailing whitespace."""
        from metabolon.enzymes.tachometer import tachometer

        with patch("metabolon.enzymes.tachometer.current_rate") as mock_rate:
            mock_rate.return_value = 3.0
            result = tachometer(action="  speed  ")

            assert "Dispatch rate: 3.0 tasks/hour" in result


class TestFormatHelpers:
    """Tests for private formatting helpers."""

    def test_fmt_slowest_none(self) -> None:
        """_fmt_slowest returns message for None input."""
        from metabolon.enzymes.tachometer import _fmt_slowest

        assert _fmt_slowest(None) == "No tasks in window."

    def test_fmt_slowest_dict(self) -> None:
        """_fmt_slowest formats dict correctly."""
        from metabolon.enzymes.tachometer import _fmt_slowest

        result = _fmt_slowest({
            "plan": "my-plan",
            "duration_s": 30.123,
            "tool": "bash",
            "timestamp": "2026-04-01T12:00:00",
            "success": True,
        })

        assert "Plan: my-plan" in result
        assert "Duration: 30.1s" in result
        assert "Tool: bash" in result
        assert "Success: True" in result

    def test_fmt_trend(self) -> None:
        """_fmt_trend formats trend dict correctly."""
        from metabolon.enzymes.tachometer import _fmt_trend

        result = _fmt_trend({
            "recent_rate": 0.85,
            "recent_count": 8,
            "historical_rate": 0.70,
            "historical_count": 40,
            "delta": 0.15,
            "direction": "improving",
        })

        assert "Recent (8): 85.0%" in result
        assert "Historical (40): 70.0%" in result
        assert "Delta: +0.150" in result
        assert "improving" in result

    def test_fmt_coaching(self) -> None:
        """_fmt_coaching formats coaching dict correctly."""
        from metabolon.enzymes.tachometer import _fmt_coaching

        result = _fmt_coaching({
            "before_failure_rate": 0.30,
            "after_failure_rate": 0.15,
            "improvement_pct": 15.0,
            "notes_analyzed": 7,
            "total_entries": 200,
        })

        assert "Before coaching failure rate: 30.0%" in result
        assert "After coaching failure rate:  15.0%" in result
        assert "Improvement: +15.0pp" in result
        assert "Notes analyzed: 7" in result
        assert "over 200 entries" in result
