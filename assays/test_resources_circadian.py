from __future__ import annotations

"""Tests for circadian resource — calendar management via gog CLI.

Covers:
  - circadian.py module-level attributes (BINARY constant, docstring)
  - circadian_clock._gog subprocess wrapper
  - scheduled_events / scheduled_events_json
  - schedule_event / reschedule_event / cancel_event
  - is_weekend / is_holiday / detect_phase
"""

import json
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

import metabolon.resources.circadian as circadian_mod
from metabolon.organelles.circadian_clock import (
    HKT,
    _gog,
    cancel_event,
    detect_phase,
    is_holiday,
    is_weekend,
    reschedule_event,
    schedule_event,
    scheduled_events,
    scheduled_events_json,
)


# ── Module-level attributes ───────────────────────────────────────────


class TestCircadianModule:
    def test_binary_constant(self):
        assert circadian_mod.BINARY == "fasti"

    def test_module_docstring_mentions_circadian(self):
        assert "circadian" in circadian_mod.__doc__.lower()


# ── _gog subprocess wrapper ────────────────────────────────────────────


class TestGogWrapper:
    @patch("metabolon.organelles.circadian_clock.subprocess.run")
    def test_gog_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="output\n", stderr="")
        result = _gog(["calendar", "list"])
        assert result == "output"
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "gog"
        assert args[1:] == ["calendar", "list"]

    @patch("metabolon.organelles.circadian_clock.subprocess.run")
    def test_gog_failure_raises(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error message")
        with pytest.raises(ValueError, match="gog failed"):
            _gog(["calendar", "list"])

    @patch("metabolon.organelles.circadian_clock.subprocess.run")
    def test_gog_timeout(self, mock_run):
        mock_run.side_effect = TimeoutError()
        with pytest.raises(TimeoutError):
            _gog(["calendar", "list"], timeout=5)


# ── scheduled_events ───────────────────────────────────────────────────


class TestScheduledEvents:
    @patch("metabolon.organelles.circadian_clock._gog")
    def test_scheduled_events_today(self, mock_gog):
        mock_gog.return_value = "Event 1 at 10:00"
        result = scheduled_events("today")
        assert result == "Event 1 at 10:00"
        mock_gog.assert_called_once_with(["calendar", "list", "--json"])

    @patch("metabolon.organelles.circadian_clock._gog")
    def test_scheduled_events_specific_date(self, mock_gog):
        mock_gog.return_value = "Event on date"
        result = scheduled_events("2026-04-15")
        assert result == "Event on date"
        mock_gog.assert_called_once_with(["calendar", "list", "2026-04-15"])


# ── scheduled_events_json ──────────────────────────────────────────────


class TestScheduledEventsJson:
    @patch("metabolon.organelles.circadian_clock._gog")
    def test_returns_parsed_json(self, mock_gog):
        mock_gog.return_value = '[{"summary": "Meeting", "start": "10:00"}]'
        result = scheduled_events_json()
        assert result == [{"summary": "Meeting", "start": "10:00"}]

    @patch("metabolon.organelles.circadian_clock._gog")
    def test_returns_empty_on_invalid_json(self, mock_gog):
        mock_gog.return_value = "not valid json"
        result = scheduled_events_json()
        assert result == []

    @patch("metabolon.organelles.circadian_clock._gog")
    def test_returns_empty_on_empty_string(self, mock_gog):
        mock_gog.return_value = ""
        result = scheduled_events_json()
        assert result == []


# ── schedule_event ─────────────────────────────────────────────────────


class TestScheduleEvent:
    @patch("metabolon.organelles.circadian_clock._gog")
    def test_schedule_event_basic(self, mock_gog):
        mock_gog.return_value = "Created event ID: 123"
        result = schedule_event("Meeting", "2026-04-15", "10:00")
        assert "Created event" in result
        mock_gog.assert_called_once_with(
            ["calendar", "create", "Meeting", "--date", "2026-04-15", "--time", "10:00", "--duration", "60"]
        )

    @patch("metabolon.organelles.circadian_clock._gog")
    def test_schedule_event_custom_duration(self, mock_gog):
        mock_gog.return_value = "Created event"
        result = schedule_event("Long Meeting", "2026-04-15", "14:00", duration=120)
        mock_gog.assert_called_once()
        args = mock_gog.call_args[0][0]
        assert args[-1] == "120"


# ── reschedule_event ───────────────────────────────────────────────────


class TestRescheduleEvent:
    @patch("metabolon.organelles.circadian_clock._gog")
    def test_reschedule_event(self, mock_gog):
        mock_gog.return_value = "Event moved"
        result = reschedule_event("evt123", "2026-04-16", "15:00")
        assert result == "Event moved"
        mock_gog.assert_called_once_with(
            ["calendar", "update", "evt123", "--from", "2026-04-16T15:00"]
        )


# ── cancel_event ───────────────────────────────────────────────────────


class TestCancelEvent:
    @patch("metabolon.organelles.circadian_clock._gog")
    def test_cancel_event(self, mock_gog):
        mock_gog.return_value = "Event deleted"
        result = cancel_event("evt456")
        assert result == "Event deleted"
        mock_gog.assert_called_once_with(
            ["calendar", "delete", "evt456", "--force"]
        )


# ── is_weekend ─────────────────────────────────────────────────────────


class TestIsWeekend:
    def test_saturday_is_weekend(self):
        saturday = date(2026, 4, 4)  # Saturday
        assert is_weekend(saturday) is True

    def test_sunday_is_weekend(self):
        sunday = date(2026, 4, 5)  # Sunday
        assert is_weekend(sunday) is True

    def test_monday_not_weekend(self):
        monday = date(2026, 4, 6)  # Monday
        assert is_weekend(monday) is False

    def test_friday_not_weekend(self):
        friday = date(2026, 4, 3)  # Friday
        assert is_weekend(friday) is False


# ── is_holiday ─────────────────────────────────────────────────────────


class TestIsHoliday:
    @patch("metabolon.organelles.circadian_clock._gog")
    def test_holiday_keyword_detected(self, mock_gog):
        mock_gog.return_value = json.dumps({
            "events": [{"start": {"date": "2026-04-01"}, "summary": "Public Holiday"}]
        })
        result = is_holiday(date(2026, 4, 1))
        assert result is True

    @patch("metabolon.organelles.circadian_clock._gog")
    def test_leave_keyword_detected(self, mock_gog):
        mock_gog.return_value = json.dumps({
            "events": [{"start": {"date": "2026-04-01"}, "summary": "Annual Leave"}]
        })
        result = is_holiday(date(2026, 4, 1))
        assert result is True

    @patch("metabolon.organelles.circadian_clock._gog")
    def test_chinese_keyword_detected(self, mock_gog):
        mock_gog.return_value = json.dumps({
            "events": [{"start": {"date": "2026-04-01"}, "summary": "休假"}]
        })
        result = is_holiday(date(2026, 4, 1))
        assert result is True

    @patch("metabolon.organelles.circadian_clock._gog")
    def test_regular_event_not_holiday(self, mock_gog):
        mock_gog.return_value = json.dumps({
            "events": [{"start": {"date": "2026-04-01"}, "summary": "Team Meeting"}]
        })
        result = is_holiday(date(2026, 4, 1))
        assert result is False

    @patch("metabolon.organelles.circadian_clock._gog")
    def test_timed_event_ignored(self, mock_gog):
        """Timed events (with dateTime, not date) are not treated as holidays."""
        mock_gog.return_value = json.dumps({
            "events": [{"start": {"dateTime": "2026-04-01T09:00"}, "summary": "Holiday"}]
        })
        result = is_holiday(date(2026, 4, 1))
        assert result is False

    @patch("metabolon.organelles.circadian_clock._gog")
    def test_error_returns_false(self, mock_gog):
        mock_gog.side_effect = ValueError("gog failed")
        result = is_holiday(date(2026, 4, 1))
        assert result is False

    @patch("metabolon.organelles.circadian_clock._gog")
    def test_json_error_returns_false(self, mock_gog):
        mock_gog.return_value = "invalid json"
        result = is_holiday(date(2026, 4, 1))
        assert result is False


# ── detect_phase ────────────────────────────────────────────────────────


class TestDetectPhase:
    def test_dawn_phase(self):
        # 06:00-09:59 HKT
        now = datetime(2026, 4, 1, 8, 30, tzinfo=HKT)  # 08:30
        result = detect_phase(now)
        assert result["phase"] == "dawn"
        assert result["hkt_hour"] == 8

    def test_day_phase(self):
        # 10:00-16:59 HKT
        now = datetime(2026, 4, 1, 14, 0, tzinfo=HKT)  # 14:00
        result = detect_phase(now)
        assert result["phase"] == "day"
        assert result["hkt_hour"] == 14

    def test_dusk_phase(self):
        # 17:00-20:59 HKT
        now = datetime(2026, 4, 1, 18, 30, tzinfo=HKT)  # 18:30
        result = detect_phase(now)
        assert result["phase"] == "dusk"
        assert result["hkt_hour"] == 18

    def test_night_phase_early(self):
        # 21:00-23:59 HKT
        now = datetime(2026, 4, 1, 22, 0, tzinfo=HKT)  # 22:00
        result = detect_phase(now)
        assert result["phase"] == "night"
        assert result["hkt_hour"] == 22

    def test_night_phase_late(self):
        # 00:00-05:59 HKT
        now = datetime(2026, 4, 1, 3, 0, tzinfo=HKT)  # 03:00
        result = detect_phase(now)
        assert result["phase"] == "night"
        assert result["hkt_hour"] == 3

    def test_phase_boundary_dawn_start(self):
        now = datetime(2026, 4, 1, 6, 0, tzinfo=HKT)  # Exactly 06:00
        result = detect_phase(now)
        assert result["phase"] == "dawn"

    def test_phase_boundary_dawn_end(self):
        now = datetime(2026, 4, 1, 9, 59, tzinfo=HKT)  # 09:59
        result = detect_phase(now)
        assert result["phase"] == "dawn"

    def test_phase_boundary_day_start(self):
        now = datetime(2026, 4, 1, 10, 0, tzinfo=HKT)  # Exactly 10:00
        result = detect_phase(now)
        assert result["phase"] == "day"

    def test_phase_boundary_day_end(self):
        now = datetime(2026, 4, 1, 16, 59, tzinfo=HKT)  # 16:59
        result = detect_phase(now)
        assert result["phase"] == "day"

    def test_phase_boundary_dusk_start(self):
        now = datetime(2026, 4, 1, 17, 0, tzinfo=HKT)  # Exactly 17:00
        result = detect_phase(now)
        assert result["phase"] == "dusk"

    def test_phase_boundary_dusk_end(self):
        now = datetime(2026, 4, 1, 20, 59, tzinfo=HKT)  # 20:59
        result = detect_phase(now)
        assert result["phase"] == "dusk"

    def test_phase_boundary_night_start(self):
        now = datetime(2026, 4, 1, 21, 0, tzinfo=HKT)  # Exactly 21:00
        result = detect_phase(now)
        assert result["phase"] == "night"

    def test_weekday_name(self):
        now = datetime(2026, 4, 1, 12, 0, tzinfo=HKT)  # Wednesday
        result = detect_phase(now)
        assert result["weekday"] == "Wednesday"

    @patch("metabolon.organelles.circadian_clock.is_weekend")
    @patch("metabolon.organelles.circadian_clock.is_holiday")
    def test_workday_flags(self, mock_holiday, mock_weekend):
        mock_weekend.return_value = False
        mock_holiday.return_value = False
        now = datetime(2026, 4, 1, 12, 0, tzinfo=HKT)
        result = detect_phase(now)
        assert result["is_weekend"] is False
        assert result["is_holiday"] is False
        assert result["is_workday"] is True

    @patch("metabolon.organelles.circadian_clock.is_weekend")
    @patch("metabolon.organelles.circadian_clock.is_holiday")
    def test_weekend_not_workday(self, mock_holiday, mock_weekend):
        mock_weekend.return_value = True
        mock_holiday.return_value = False
        now = datetime(2026, 4, 4, 12, 0, tzinfo=HKT)  # Saturday
        result = detect_phase(now)
        assert result["is_weekend"] is True
        assert result["is_workday"] is False

    @patch("metabolon.organelles.circadian_clock.is_weekend")
    @patch("metabolon.organelles.circadian_clock.is_holiday")
    def test_holiday_not_workday(self, mock_holiday, mock_weekend):
        mock_weekend.return_value = False
        mock_holiday.return_value = True
        now = datetime(2026, 4, 1, 12, 0, tzinfo=HKT)
        result = detect_phase(now)
        assert result["is_holiday"] is True
        assert result["is_workday"] is False

    def test_all_keys_present(self):
        now = datetime(2026, 4, 1, 12, 0, tzinfo=HKT)
        result = detect_phase(now)
        expected_keys = {"phase", "is_weekend", "is_holiday", "is_workday", "hkt_hour", "weekday"}
        assert set(result.keys()) == expected_keys


# ── HKT timezone ────────────────────────────────────────────────────────


class TestHKTTimezone:
    def test_hkt_offset(self):
        assert HKT.utcoffset(None) == timedelta(hours=8)

    def test_hkt_is_utc_plus_8(self):
        now_utc = datetime.now(timezone.utc)
        now_hkt = now_utc.astimezone(HKT)
        diff = now_hkt.hour - now_utc.hour
        # Account for day boundary
        if diff < 0:
            diff += 24
        assert diff == 8
