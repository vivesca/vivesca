from __future__ import annotations

"""Tests for circadian resource — calendar management via Google Calendar API.

Covers:
  - circadian.py module-level attributes (BINARY constant, docstring)
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
    cancel_event,
    detect_phase,
    is_holiday,
    is_weekend,
    reschedule_event,
    schedule_event,
    scheduled_events,
    scheduled_events_json,
)

MOD = "metabolon.organelles.circadian_clock"


# ── Module-level attributes ───────────────────────────────────────────


class TestCircadianModule:
    def test_binary_constant(self):
        assert circadian_mod.BINARY == "fasti"

    def test_module_docstring_mentions_circadian(self):
        assert "circadian" in circadian_mod.__doc__.lower()


# ── scheduled_events ───────────────────────────────────────────────────


class TestScheduledEvents:
    @patch(f"{MOD}.scheduled_events_json", return_value=[])
    def test_no_events(self, mock_json):
        result = scheduled_events("today")
        assert result == "No events."

    @patch(f"{MOD}.scheduled_events_json")
    def test_timed_event(self, mock_json):
        mock_json.return_value = [
            {"start": {"dateTime": "2026-04-15T10:00:00+08:00"}, "summary": "Meeting"},
        ]
        result = scheduled_events("2026-04-15")
        assert "10:00  Meeting" in result


# ── scheduled_events_json ──────────────────────────────────────────────


class TestScheduledEventsJson:
    @patch(f"{MOD}.service")
    def test_returns_events(self, mock_service):
        mock_service.return_value.events.return_value.list.return_value.execute.return_value = {
            "items": [{"summary": "Meeting", "start": {"dateTime": "2026-04-15T10:00:00+08:00"}}]
        }
        result = scheduled_events_json()
        assert result == [{"summary": "Meeting", "start": {"dateTime": "2026-04-15T10:00:00+08:00"}}]

    @patch(f"{MOD}.service", side_effect=Exception("API error"))
    def test_returns_empty_on_error(self, mock_service):
        result = scheduled_events_json()
        assert result == []

    @patch(f"{MOD}.service")
    def test_returns_empty_on_no_items(self, mock_service):
        mock_service.return_value.events.return_value.list.return_value.execute.return_value = {}
        result = scheduled_events_json()
        assert result == []


# ── schedule_event ─────────────────────────────────────────────────────


class TestScheduleEvent:
    @patch(f"{MOD}.service")
    def test_schedule_event_basic(self, mock_service):
        mock_service.return_value.events.return_value.insert.return_value.execute.return_value = {
            "id": "evt123"
        }
        result = schedule_event("Meeting", "2026-04-15", "10:00")
        assert result == "evt123"

    @patch(f"{MOD}.service")
    def test_schedule_event_custom_duration(self, mock_service):
        mock_service.return_value.events.return_value.insert.return_value.execute.return_value = {
            "id": "evt789"
        }
        result = schedule_event("Long Meeting", "2026-04-15", "14:00", duration=120)
        assert result == "evt789"


# ── reschedule_event ───────────────────────────────────────────────────


class TestRescheduleEvent:
    @patch(f"{MOD}.service")
    def test_reschedule_event(self, mock_service):
        mock_svc = mock_service.return_value
        mock_svc.events.return_value.get.return_value.execute.return_value = {
            "start": {"dateTime": "2026-04-15T10:00:00+08:00"},
            "end": {"dateTime": "2026-04-15T11:00:00+08:00"},
        }
        mock_svc.events.return_value.update.return_value.execute.return_value = {}
        result = reschedule_event("evt123", "2026-04-16", "15:00")
        assert result == "evt123"


# ── cancel_event ───────────────────────────────────────────────────────


class TestCancelEvent:
    @patch(f"{MOD}.service")
    def test_cancel_event(self, mock_service):
        mock_service.return_value.events.return_value.delete.return_value.execute.return_value = None
        result = cancel_event("evt456")
        assert result == "evt456"


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
    @patch(f"{MOD}.scheduled_events_json")
    def test_holiday_keyword_detected(self, mock_json):
        mock_json.return_value = [
            {"start": {"date": "2026-04-01"}, "summary": "Public Holiday"}
        ]
        result = is_holiday(date(2026, 4, 1))
        assert result is True

    @patch(f"{MOD}.scheduled_events_json")
    def test_leave_keyword_detected(self, mock_json):
        mock_json.return_value = [
            {"start": {"date": "2026-04-01"}, "summary": "Annual Leave"}
        ]
        result = is_holiday(date(2026, 4, 1))
        assert result is True

    @patch(f"{MOD}.scheduled_events_json")
    def test_chinese_keyword_detected(self, mock_json):
        mock_json.return_value = [
            {"start": {"date": "2026-04-01"}, "summary": "休假"}
        ]
        result = is_holiday(date(2026, 4, 1))
        assert result is True

    @patch(f"{MOD}.scheduled_events_json")
    def test_regular_event_not_holiday(self, mock_json):
        mock_json.return_value = [
            {"start": {"date": "2026-04-01"}, "summary": "Team Meeting"}
        ]
        result = is_holiday(date(2026, 4, 1))
        assert result is False

    @patch(f"{MOD}.scheduled_events_json")
    def test_timed_event_ignored(self, mock_json):
        """Timed events (with dateTime, not date) are not treated as holidays."""
        mock_json.return_value = [
            {"start": {"dateTime": "2026-04-01T09:00"}, "summary": "Holiday"}
        ]
        result = is_holiday(date(2026, 4, 1))
        assert result is False

    @patch(f"{MOD}.scheduled_events_json", side_effect=Exception("API error"))
    def test_error_returns_false(self, mock_json):
        result = is_holiday(date(2026, 4, 1))
        assert result is False

    @patch(f"{MOD}.scheduled_events_json")
    def test_empty_events_returns_false(self, mock_json):
        mock_json.return_value = []
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
