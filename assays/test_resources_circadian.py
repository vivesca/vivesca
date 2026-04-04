"""Tests for circadian resource — calendar management via Google Calendar API.

Covers:
  - circadian.py module-level attributes (BINARY constant, docstring)
  - scheduled_events / scheduled_events_json (mocking Google Calendar API)
  - schedule_event / reschedule_event / cancel_event
  - is_weekend / is_holiday / detect_phase
"""

from datetime import UTC, date, datetime, timedelta
from unittest.mock import MagicMock, patch

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_service(events=None):
    """Build a mock Google Calendar service with events().list().execute() chain."""
    svc = MagicMock()
    execute = MagicMock(return_value={"items": events or []})
    svc.events.return_value.list.return_value.execute = execute
    return svc


# ── Module-level attributes ───────────────────────────────────────────


class TestCircadianModule:
    def test_binary_constant(self):
        assert circadian_mod.BINARY == "fasti"

    def test_module_docstring_mentions_circadian(self):
        assert circadian_mod.__doc__ is not None
        assert "circadian" in circadian_mod.__doc__.lower()


# ── scheduled_events ───────────────────────────────────────────────────


class TestScheduledEvents:
    @patch(f"{MOD}.scheduled_events_json")
    def test_scheduled_events_today(self, mock_json):
        mock_json.return_value = [
            {"summary": "Event 1", "start": {"dateTime": "2026-04-01T10:00:00+08:00"}},
        ]
        result = scheduled_events("today")
        assert "10:00  Event 1" in result

    @patch(f"{MOD}.scheduled_events_json")
    def test_scheduled_events_specific_date(self, mock_json):
        mock_json.return_value = [
            {"summary": "Event on date", "start": {"dateTime": "2026-04-15T09:00:00+08:00"}},
        ]
        result = scheduled_events("2026-04-15")
        assert "09:00  Event on date" in result
        mock_json.assert_called_once_with("2026-04-15")


# ── scheduled_events_json ──────────────────────────────────────────────


class TestScheduledEventsJson:
    @patch(f"{MOD}.service")
    def test_returns_parsed_items(self, mock_svc_fn):
        items = [{"summary": "Meeting", "start": {"dateTime": "2026-04-01T10:00:00+08:00"}}]
        mock_svc_fn.return_value = _mock_service(events=items)
        result = scheduled_events_json("2026-04-01")
        assert result == items

    @patch(f"{MOD}.service")
    def test_returns_empty_on_api_error(self, mock_svc_fn):
        mock_svc_fn.side_effect = RuntimeError("auth failed")
        result = scheduled_events_json("2026-04-01")
        assert result == []

    @patch(f"{MOD}.service")
    def test_returns_empty_on_empty_calendar(self, mock_svc_fn):
        mock_svc_fn.return_value = _mock_service(events=[])
        result = scheduled_events_json("2026-04-01")
        assert result == []


# ── schedule_event ─────────────────────────────────────────────────────


class TestScheduleEvent:
    @patch(f"{MOD}.service")
    def test_schedule_event_basic(self, mock_svc_fn):
        svc = MagicMock()
        svc.events.return_value.insert.return_value.execute.return_value = {"id": "evt123"}
        mock_svc_fn.return_value = svc
        result = schedule_event("Meeting", "2026-04-15", "10:00")
        assert result == "evt123"
        call_kwargs = svc.events.return_value.insert.call_args[1]
        assert call_kwargs["body"]["summary"] == "Meeting"

    @patch(f"{MOD}.service")
    def test_schedule_event_custom_duration(self, mock_svc_fn):
        svc = MagicMock()
        svc.events.return_value.insert.return_value.execute.return_value = {"id": "evt456"}
        mock_svc_fn.return_value = svc
        result = schedule_event("Long Meeting", "2026-04-15", "14:00", duration=120)
        assert result == "evt456"
        body = svc.events.return_value.insert.call_args[1]["body"]
        start_dt = datetime.fromisoformat(body["start"]["dateTime"])
        end_dt = datetime.fromisoformat(body["end"]["dateTime"])
        assert (end_dt - start_dt) == timedelta(minutes=120)


# ── reschedule_event ───────────────────────────────────────────────────


class TestRescheduleEvent:
    @patch(f"{MOD}.service")
    def test_reschedule_event(self, mock_svc_fn):
        svc = MagicMock()
        svc.events.return_value.get.return_value.execute.return_value = {
            "summary": "Meeting",
            "start": {"dateTime": "2026-04-15T10:00:00+08:00"},
            "end": {"dateTime": "2026-04-15T11:00:00+08:00"},
        }
        svc.events.return_value.update.return_value.execute.return_value = {"id": "evt123"}
        mock_svc_fn.return_value = svc
        result = reschedule_event("evt123", "2026-04-16", "15:00")
        assert result == "evt123"
        svc.events.return_value.get.assert_called_once()
        svc.events.return_value.update.assert_called_once()


# ── cancel_event ───────────────────────────────────────────────────────


class TestCancelEvent:
    @patch(f"{MOD}.service")
    def test_cancel_event(self, mock_svc_fn):
        svc = MagicMock()
        svc.events.return_value.delete.return_value.execute.return_value = None
        mock_svc_fn.return_value = svc
        result = cancel_event("evt456")
        assert result == "evt456"
        svc.events.return_value.delete.assert_called_once()


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
            {"start": {"date": "2026-04-01"}, "summary": "Public Holiday"},
        ]
        assert is_holiday(date(2026, 4, 1)) is True

    @patch(f"{MOD}.scheduled_events_json")
    def test_leave_keyword_detected(self, mock_json):
        mock_json.return_value = [
            {"start": {"date": "2026-04-01"}, "summary": "Annual Leave"},
        ]
        assert is_holiday(date(2026, 4, 1)) is True

    @patch(f"{MOD}.scheduled_events_json")
    def test_chinese_keyword_detected(self, mock_json):
        mock_json.return_value = [
            {"start": {"date": "2026-04-01"}, "summary": "\u4f11\u5047"},
        ]
        assert is_holiday(date(2026, 4, 1)) is True

    @patch(f"{MOD}.scheduled_events_json")
    def test_regular_event_not_holiday(self, mock_json):
        mock_json.return_value = [
            {"start": {"date": "2026-04-01"}, "summary": "Team Meeting"},
        ]
        assert is_holiday(date(2026, 4, 1)) is False

    @patch(f"{MOD}.scheduled_events_json")
    def test_timed_event_ignored(self, mock_json):
        """Timed events (with dateTime, not date) are not treated as holidays."""
        mock_json.return_value = [
            {"start": {"dateTime": "2026-04-01T09:00:00+08:00"}, "summary": "Holiday"},
        ]
        assert is_holiday(date(2026, 4, 1)) is False

    @patch(f"{MOD}.scheduled_events_json", side_effect=Exception("api down"))
    def test_error_returns_false(self, mock_json):
        assert is_holiday(date(2026, 4, 1)) is False

    @patch(f"{MOD}.scheduled_events_json", return_value=[])
    def test_empty_returns_false(self, mock_json):
        assert is_holiday(date(2026, 4, 1)) is False


# ── detect_phase ────────────────────────────────────────────────────────


class TestDetectPhase:
    def test_dawn_phase(self):
        now = datetime(2026, 4, 1, 8, 30, tzinfo=HKT)
        result = detect_phase(now)
        assert result["phase"] == "dawn"
        assert result["hkt_hour"] == 8

    def test_day_phase(self):
        now = datetime(2026, 4, 1, 14, 0, tzinfo=HKT)
        result = detect_phase(now)
        assert result["phase"] == "day"
        assert result["hkt_hour"] == 14

    def test_dusk_phase(self):
        now = datetime(2026, 4, 1, 18, 30, tzinfo=HKT)
        result = detect_phase(now)
        assert result["phase"] == "dusk"
        assert result["hkt_hour"] == 18

    def test_night_phase_early(self):
        now = datetime(2026, 4, 1, 22, 0, tzinfo=HKT)
        result = detect_phase(now)
        assert result["phase"] == "night"
        assert result["hkt_hour"] == 22

    def test_night_phase_late(self):
        now = datetime(2026, 4, 1, 3, 0, tzinfo=HKT)
        result = detect_phase(now)
        assert result["phase"] == "night"
        assert result["hkt_hour"] == 3

    def test_phase_boundary_dawn_start(self):
        now = datetime(2026, 4, 1, 6, 0, tzinfo=HKT)
        result = detect_phase(now)
        assert result["phase"] == "dawn"

    def test_phase_boundary_dawn_end(self):
        now = datetime(2026, 4, 1, 9, 59, tzinfo=HKT)
        result = detect_phase(now)
        assert result["phase"] == "dawn"

    def test_phase_boundary_day_start(self):
        now = datetime(2026, 4, 1, 10, 0, tzinfo=HKT)
        result = detect_phase(now)
        assert result["phase"] == "day"

    def test_phase_boundary_day_end(self):
        now = datetime(2026, 4, 1, 16, 59, tzinfo=HKT)
        result = detect_phase(now)
        assert result["phase"] == "day"

    def test_phase_boundary_dusk_start(self):
        now = datetime(2026, 4, 1, 17, 0, tzinfo=HKT)
        result = detect_phase(now)
        assert result["phase"] == "dusk"

    def test_phase_boundary_dusk_end(self):
        now = datetime(2026, 4, 1, 20, 59, tzinfo=HKT)
        result = detect_phase(now)
        assert result["phase"] == "dusk"

    def test_phase_boundary_night_start(self):
        now = datetime(2026, 4, 1, 21, 0, tzinfo=HKT)
        result = detect_phase(now)
        assert result["phase"] == "night"

    def test_weekday_name(self):
        now = datetime(2026, 4, 1, 12, 0, tzinfo=HKT)  # Wednesday
        result = detect_phase(now)
        assert result["weekday"] == "Wednesday"

    @patch(f"{MOD}.is_weekend")
    @patch(f"{MOD}.is_holiday")
    def test_workday_flags(self, mock_holiday, mock_weekend):
        mock_weekend.return_value = False
        mock_holiday.return_value = False
        now = datetime(2026, 4, 1, 12, 0, tzinfo=HKT)
        result = detect_phase(now)
        assert result["is_weekend"] is False
        assert result["is_holiday"] is False
        assert result["is_workday"] is True

    @patch(f"{MOD}.is_weekend")
    @patch(f"{MOD}.is_holiday")
    def test_weekend_not_workday(self, mock_holiday, mock_weekend):
        mock_weekend.return_value = True
        mock_holiday.return_value = False
        now = datetime(2026, 4, 4, 12, 0, tzinfo=HKT)  # Saturday
        result = detect_phase(now)
        assert result["is_weekend"] is True
        assert result["is_workday"] is False

    @patch(f"{MOD}.is_weekend")
    @patch(f"{MOD}.is_holiday")
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
        now_utc = datetime.now(UTC)
        now_hkt = now_utc.astimezone(HKT)
        diff = now_hkt.hour - now_utc.hour
        # Account for day boundary
        if diff < 0:
            diff += 24
        assert diff == 8
