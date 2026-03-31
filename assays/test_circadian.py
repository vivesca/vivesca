from __future__ import annotations

"""Tests for metabolon.enzymes.circadian — all external calls mocked."""

import pytest
from unittest.mock import patch, MagicMock

from metabolon.enzymes.circadian import circadian, CircadianResult
from metabolon.morphology import EffectorResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _result(r):
    """Normalize: circadian returns CircadianResult or EffectorResult."""
    return r


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

class TestList:
    @patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="No events")
    def test_list_default(self, mock_se):
        r = circadian(action="list")
        assert isinstance(r, CircadianResult)
        assert r.output == "No events"
        mock_se.assert_called_once_with("today")

    @patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="evt1,evt2")
    def test_list_specific_date(self, mock_se):
        r = circadian(action="list", date="2025-06-15")
        assert isinstance(r, CircadianResult)
        assert r.output == "evt1,evt2"
        mock_se.assert_called_once_with("2025-06-15")


# ---------------------------------------------------------------------------
# set
# ---------------------------------------------------------------------------

class TestSet:
    def test_set_missing_fields(self):
        r = circadian(action="set")
        assert isinstance(r, EffectorResult)
        assert r.success is False
        assert "set requires" in r.message

    @patch("metabolon.organelles.circadian_clock.schedule_event", return_value="created E1")
    def test_set_basic(self, mock_se):
        r = circadian(action="set", summary="Meeting", date="2025-06-15", from_time="09:00", to_time="10:30")
        assert isinstance(r, CircadianResult)
        assert "created E1" in r.output
        # 9:00 → 10:30 = 90 minutes
        mock_se.assert_called_once_with("Meeting", "2025-06-15", "09:00", duration=90)

    @patch("metabolon.organelles.circadian_clock.schedule_event", return_value="created E2")
    def test_set_duration_wraps_midnight(self, mock_se):
        """End before start → falls back to 60 min."""
        r = circadian(action="set", summary="Late", date="2025-06-15", from_time="23:00", to_time="01:00")
        assert isinstance(r, CircadianResult)
        mock_se.assert_called_once_with("Late", "2025-06-15", "23:00", duration=60)

    @patch("metabolon.organelles.circadian_clock.schedule_event", return_value="ok")
    def test_set_bad_time_format_fallback(self, mock_se):
        """Unparseable times → default 60 min."""
        r = circadian(action="set", summary="X", date="2025-06-15", from_time="noon", to_time="one")
        assert isinstance(r, CircadianResult)
        mock_se.assert_called_once_with("X", "2025-06-15", "noon", duration=60)

    @patch("metabolon.organelles.circadian_clock.schedule_event", return_value="ok")
    def test_set_with_description_and_location(self, mock_se):
        r = circadian(
            action="set",
            summary="S",
            date="2025-06-15",
            from_time="10:00",
            to_time="11:00",
            description="desc",
            location="room",
        )
        assert isinstance(r, CircadianResult)
        assert "description ignored by circadian_clock: desc" in r.output
        assert "location ignored by circadian_clock: room" in r.output

    @patch("metabolon.organelles.circadian_clock.schedule_event", return_value="ok")
    def test_set_exact_one_hour(self, mock_se):
        r = circadian(action="set", summary="S", date="2025-06-15", from_time="10:00", to_time="11:00")
        mock_se.assert_called_once_with("S", "2025-06-15", "10:00", duration=60)


# ---------------------------------------------------------------------------
# move
# ---------------------------------------------------------------------------

class TestMove:
    def test_move_missing_fields(self):
        r = circadian(action="move")
        assert isinstance(r, EffectorResult)
        assert r.success is False
        assert "move requires" in r.message

    @patch("metabolon.organelles.circadian_clock.reschedule_event", return_value="moved ok")
    def test_move_success(self, mock_re):
        r = circadian(action="move", event_id="E42", date="2025-07-01", time="14:00")
        assert isinstance(r, CircadianResult)
        assert r.output == "moved ok"
        mock_re.assert_called_once_with("E42", "2025-07-01", "14:00")


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    def test_delete_missing_event_id(self):
        r = circadian(action="delete")
        assert isinstance(r, EffectorResult)
        assert r.success is False
        assert "delete requires" in r.message

    @patch("metabolon.organelles.circadian_clock.cancel_event", return_value="deleted ok")
    def test_delete_success(self, mock_ce):
        r = circadian(action="delete", event_id="E99")
        assert isinstance(r, CircadianResult)
        assert r.output == "deleted ok"
        mock_ce.assert_called_once_with("E99")


# ---------------------------------------------------------------------------
# sleep
# ---------------------------------------------------------------------------

class TestSleep:
    @patch("metabolon.enzymes.interoception._sleep_result")
    def test_sleep_default(self, mock_sr):
        mock_sr.return_value = MagicMock(summary="7.5h sleep")
        r = circadian(action="sleep")
        assert isinstance(r, CircadianResult)
        assert r.output == "7.5h sleep"
        mock_sr.assert_called_once_with("today")

    @patch("metabolon.enzymes.interoception._sleep_result")
    def test_sleep_specific_period(self, mock_sr):
        mock_sr.return_value = MagicMock(summary="6h sleep")
        r = circadian(action="sleep", period="yesterday")
        assert isinstance(r, CircadianResult)
        assert r.output == "6h sleep"
        mock_sr.assert_called_once_with("yesterday")


# ---------------------------------------------------------------------------
# heartrate
# ---------------------------------------------------------------------------

class TestHeartRate:
    @patch("metabolon.enzymes.interoception._heartrate_result")
    def test_heartrate_default(self, mock_hr):
        mock_hr.return_value = MagicMock(summary="avg 72 bpm")
        r = circadian(action="heartrate")
        assert isinstance(r, CircadianResult)
        assert r.output == "avg 72 bpm"
        mock_hr.assert_called_once_with("", "")

    @patch("metabolon.enzymes.interoception._heartrate_result")
    def test_heartrate_with_range(self, mock_hr):
        mock_hr.return_value = MagicMock(summary="max 110 bpm")
        r = circadian(action="heartrate", start_datetime="2025-06-01", end_datetime="2025-06-07")
        assert isinstance(r, CircadianResult)
        assert r.output == "max 110 bpm"
        mock_hr.assert_called_once_with("2025-06-01", "2025-06-07")


# ---------------------------------------------------------------------------
# unknown action
# ---------------------------------------------------------------------------

class TestUnknown:
    def test_unknown_action(self):
        r = circadian(action="dance")
        assert isinstance(r, EffectorResult)
        assert r.success is False
        assert "Unknown action" in r.message

    def test_action_case_insensitive(self):
        """Actions are lowercased, so 'LIST' should still be dispatched."""
        with patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="ok"):
            r = circadian(action="LIST")
            assert isinstance(r, CircadianResult)
            assert r.output == "ok"

    def test_action_whitespace_trimmed(self):
        with patch("metabolon.organelles.circadian_clock.scheduled_events", return_value="ok"):
            r = circadian(action="  list  ")
            assert isinstance(r, CircadianResult)
            assert r.output == "ok"
