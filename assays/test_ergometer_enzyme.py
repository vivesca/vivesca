"""Tests for ergometer enzyme — dispatch speed monitor."""

from unittest.mock import patch


class TestErgometerSpeed:
    """Tests for speed action."""

    @patch("metabolon.enzymes.ergometer.current_rate")
    def test_speed_returns_formatted_rate(self, mock_rate):
        from metabolon.enzymes.ergometer import ergometer

        mock_rate.return_value = 12.5
        result = ergometer(action="speed")

        assert isinstance(result, str)
        assert "12.5" in result
        assert "tasks/hour" in result
        mock_rate.assert_called_once()

    @patch("metabolon.enzymes.ergometer.current_rate")
    def test_speed_with_zero_rate(self, mock_rate):
        from metabolon.enzymes.ergometer import ergometer

        mock_rate.return_value = 0.0
        result = ergometer(action="speed")

        assert "0.0" in result
        assert "tasks/hour" in result


class TestErgometerTrend:
    """Tests for trend action."""

    @patch("metabolon.enzymes.ergometer.success_trend")
    def test_trend_returns_formatted_trend(self, mock_trend):
        from metabolon.enzymes.ergometer import ergometer

        mock_trend.return_value = {
            "recent_count": 10,
            "recent_rate": 0.85,
            "historical_count": 50,
            "historical_rate": 0.70,
            "delta": 0.15,
            "direction": "improving",
        }
        result = ergometer(action="trend")

        assert "85.0%" in result
        assert "70.0%" in result
        assert "improving" in result
        mock_trend.assert_called_once()

    @patch("metabolon.enzymes.ergometer.success_trend")
    def test_trend_with_negative_delta(self, mock_trend):
        from metabolon.enzymes.ergometer import ergometer

        mock_trend.return_value = {
            "recent_count": 5,
            "recent_rate": 0.60,
            "historical_count": 100,
            "historical_rate": 0.80,
            "delta": -0.20,
            "direction": "declining",
        }
        result = ergometer(action="trend")

        assert "declining" in result
        assert "-0.200" in result


class TestErgometerSlowest:
    """Tests for slowest action."""

    @patch("metabolon.enzymes.ergometer.slowest_recent")
    def test_slowest_returns_formatted_task(self, mock_slowest):
        from metabolon.enzymes.ergometer import ergometer

        mock_slowest.return_value = {
            "plan": "plan-42",
            "duration_s": 123.4,
            "tool": "writer",
            "timestamp": "2026-04-01T12:00:00",
            "success": True,
        }
        result = ergometer(action="slowest", hours=2)

        assert "plan-42" in result
        assert "123.4s" in result
        assert "writer" in result
        assert "True" in result
        mock_slowest.assert_called_once_with(hours=2)

    @patch("metabolon.enzymes.ergometer.slowest_recent")
    def test_slowest_none_result(self, mock_slowest):
        from metabolon.enzymes.ergometer import ergometer

        mock_slowest.return_value = None
        result = ergometer(action="slowest")

        assert "No tasks in window" in result

    @patch("metabolon.enzymes.ergometer.slowest_recent")
    def test_slowest_default_hours(self, mock_slowest):
        from metabolon.enzymes.ergometer import ergometer

        mock_slowest.return_value = {
            "plan": "plan-1",
            "duration_s": 10.0,
            "tool": "test",
            "timestamp": "2026-04-01T10:00:00",
            "success": False,
        }
        ergometer(action="slowest")

        mock_slowest.assert_called_once_with(hours=1)


class TestErgometerCoaching:
    """Tests for coaching action."""

    @patch("metabolon.enzymes.ergometer.coaching_effectiveness")
    def test_coaching_returns_formatted_metrics(self, mock_coaching):
        from metabolon.enzymes.ergometer import ergometer

        mock_coaching.return_value = {
            "before_failure_rate": 0.25,
            "after_failure_rate": 0.10,
            "improvement_pct": 15.0,
            "notes_analyzed": 42,
            "total_entries": 100,
        }
        result = ergometer(action="coaching")

        assert "25.0%" in result
        assert "10.0%" in result
        assert "+15.0pp" in result
        assert "42" in result
        mock_coaching.assert_called_once()


class TestErgometerEta:
    """Tests for eta action."""

    @patch("metabolon.enzymes.ergometer.estimate_completion")
    def test_eta_returns_formatted_estimate(self, mock_eta):
        from metabolon.enzymes.ergometer import ergometer

        mock_eta.return_value = 3.5
        result = ergometer(action="eta", remaining_tasks=7)

        assert "3.5 hours" in result
        assert "7 remaining tasks" in result
        mock_eta.assert_called_once_with(remaining_tasks=7)

    @patch("metabolon.enzymes.ergometer.estimate_completion")
    def test_eta_with_zero_tasks(self, mock_eta):
        from metabolon.enzymes.ergometer import ergometer

        mock_eta.return_value = 0.0
        result = ergometer(action="eta", remaining_tasks=0)

        assert "0.0 hours" in result
        assert "0 remaining tasks" in result


class TestErgometerUnknownAction:
    """Tests for unknown action handling."""

    def test_unknown_action_returns_error_message(self):
        from metabolon.enzymes.ergometer import ergometer

        result = ergometer(action="invalid")
        assert "Unknown action" in result
        assert "invalid" in result

    def test_unknown_action_suggests_valid_actions(self):
        from metabolon.enzymes.ergometer import ergometer

        result = ergometer(action="badaction")
        assert "speed" in result
        assert "trend" in result
        assert "slowest" in result

    def test_action_case_insensitive(self):
        """Test that action is lowercased before matching."""
        from metabolon.enzymes.ergometer import ergometer

        with patch("metabolon.enzymes.ergometer.current_rate") as mock_rate:
            mock_rate.return_value = 5.0
            result = ergometer(action="SPEED")

            assert "5.0" in result
            mock_rate.assert_called_once()

    def test_action_with_whitespace(self):
        """Test that action is stripped before matching."""
        from metabolon.enzymes.ergometer import ergometer

        with patch("metabolon.enzymes.ergometer.current_rate") as mock_rate:
            mock_rate.return_value = 5.0
            result = ergometer(action="  speed  ")

            assert "5.0" in result
            mock_rate.assert_called_once()


class TestFormatHelpers:
    """Tests for internal format helper functions."""

    def test_fmt_slowest_with_data(self):
        from metabolon.enzymes.ergometer import _fmt_slowest

        result = _fmt_slowest(
            {
                "plan": "p1",
                "duration_s": 45.0,
                "tool": "reader",
                "timestamp": "2026-04-01T08:00:00",
                "success": True,
            }
        )

        assert "Plan: p1" in result
        assert "Duration: 45.0s" in result
        assert "Tool: reader" in result
        assert "Success: True" in result

    def test_fmt_slowest_none(self):
        from metabolon.enzymes.ergometer import _fmt_slowest

        result = _fmt_slowest(None)
        assert result == "No tasks in window."

    def test_fmt_trend(self):
        from metabolon.enzymes.ergometer import _fmt_trend

        result = _fmt_trend(
            {
                "recent_count": 10,
                "recent_rate": 0.9,
                "historical_count": 100,
                "historical_rate": 0.75,
                "delta": 0.15,
                "direction": "improving",
            }
        )

        assert "Recent (10): 90.0%" in result
        assert "Historical (100): 75.0%" in result
        assert "Delta: +0.150" in result
        assert "improving" in result

    def test_fmt_coaching(self):
        from metabolon.enzymes.ergometer import _fmt_coaching

        result = _fmt_coaching(
            {
                "before_failure_rate": 0.30,
                "after_failure_rate": 0.15,
                "improvement_pct": 15.0,
                "notes_analyzed": 25,
                "total_entries": 50,
            }
        )

        assert "Before coaching failure rate: 30.0%" in result
        assert "After coaching failure rate:  15.0%" in result
        assert "Improvement: +15.0pp" in result
        assert "Notes analyzed: 25" in result
        assert "entries" in result
