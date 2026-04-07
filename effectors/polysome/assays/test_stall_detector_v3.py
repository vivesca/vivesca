"""Tests for v3 stall detection — Langfuse trace integration.

v2: streaming-json pattern detection (local, real-time)
v3: emit stall events as Langfuse spans, query trace history for
    cross-workflow stall patterns, and surface stall rates in dashboard.

v3 adds observability — v2 detects, v3 records and learns.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestStallTraceEmission:
    """Stall events are recorded as Langfuse spans for observability."""

    @patch("polysome.stall_trace.get_langfuse")
    def test_stall_detected_emits_span(self, mock_lf):
        """When a stall is detected, a span is added to the current trace."""
        from polysome.stall_trace import record_stall_event

        mock_trace = MagicMock()
        mock_lf.return_value.trace.return_value = mock_trace

        record_stall_event(
            workflow_id="ribosome-glm51-sha-gate-a1b2c3d4",
            pattern="repeated_action",
            action_taken="warn",
            details={"tool": "Read", "count": 4},
        )

        mock_trace.span.assert_called_once()
        call_kwargs = mock_trace.span.call_args[1]
        assert call_kwargs["name"] == "stall-detected"
        assert call_kwargs["metadata"]["pattern"] == "repeated_action"
        assert call_kwargs["metadata"]["action"] == "warn"

    @patch("polysome.stall_trace.get_langfuse")
    def test_stall_kill_emits_generation(self, mock_lf):
        """Kill events include the partial stdout for debugging."""
        from polysome.stall_trace import record_stall_event

        mock_trace = MagicMock()
        mock_lf.return_value.trace.return_value = mock_trace

        record_stall_event(
            workflow_id="ribosome-glm51-sha-gate-a1b2c3d4",
            pattern="ping_pong",
            action_taken="kill",
            details={"partial_stdout": "Working on file..."},
        )

        call_kwargs = mock_trace.span.call_args[1]
        assert call_kwargs["metadata"]["action"] == "kill"
        assert "partial_stdout" in call_kwargs["metadata"]

    @patch("polysome.stall_trace.get_langfuse")
    def test_no_langfuse_graceful_noop(self, mock_lf):
        """If Langfuse is unavailable, stall recording is a silent no-op."""
        from polysome.stall_trace import record_stall_event

        mock_lf.return_value = None

        # Should not raise
        record_stall_event(
            workflow_id="test",
            pattern="repeated_action",
            action_taken="warn",
            details={},
        )


class TestStallRateQuery:
    """Query Langfuse for cross-workflow stall patterns."""

    @patch("polysome.stall_trace.get_langfuse")
    def test_stall_rate_returns_percentage(self, mock_lf):
        """stall_rate() returns fraction of recent workflows that hit stalls."""
        from polysome.stall_trace import stall_rate

        rate = stall_rate(window_hours=24)
        assert isinstance(rate, float)
        assert 0.0 <= rate <= 1.0

    @patch("polysome.stall_trace.get_langfuse")
    def test_most_common_pattern(self, mock_lf):
        """most_common_stall_pattern() returns the dominant pattern name."""
        from polysome.stall_trace import most_common_stall_pattern

        pattern = most_common_stall_pattern(window_hours=24)
        assert pattern is None or isinstance(pattern, str)
