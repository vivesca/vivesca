from __future__ import annotations

"""Tests for metabolon.organelles.circadian_clock — full coverage with mocked Calendar API."""

import json
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles.circadian_clock import (
    cancel_event,
    detect_phase,
    is_holiday,
    is_weekend,
    reschedule_event,
    schedule_event,
    scheduled_events,
    scheduled_events_json,
)

HKT = timezone(timedelta(hours=8))
MOD = "metabolon.organelles.circadian_clock"


# ---------------------------------------------------------------------------
# scheduled_events / scheduled_events_json
# ---------------------------------------------------------------------------


class TestScheduledEvents:
    @patch(f"{MOD}.scheduled_events_json", return_value=[])
    def test_no_events(self, mock_json):
        result = scheduled_events()
        assert result == "No events."

    @patch(f"{MOD}.scheduled_events_json")
    def test_timed_events(self, mock_json):
        mock_json.return_value = [
            {"start": {"dateTime": "2026-04-01T10:00:00+08:00"}, "summary": "Standup"},
            {"start": {"dateTime": "2026-04-01T14:30:00+08:00"}, "summary": "Review"},
        ]
        result = scheduled_events()
        assert "10:00  Standup" in result
        assert "14:30  Review" in result

    @patch(f"{MOD}.scheduled_events_json")
    def test_all_day_event(self, mock_json):
        mock_json.return_value = [
            {"start": {"date": "2026-04-01"}, "summary": "Holiday"},
        ]
        result = scheduled_events()
        assert "all-day  Holiday" in result


class TestScheduledEventsJson:
    @patch(f"{MOD}.service")
    def test_valid_events(self, mock_service):
        mock_service.return_value.events.return_value.list.return_value.execute.return_value = {
            "items": [{"summary": "Standup"}]
        }
        result = scheduled_events_json()
        assert result == [{"summary": "Standup"}]

    @patch(f"{MOD}.service")
    def test_no_items_key(self, mock_service):
        mock_service.return_value.events.return_value.list.return_value.execute.return_value = {}
        result = scheduled_events_json()
        assert result == []

    @patch(f"{MOD}.service", side_effect=Exception("API error"))
    def test_exception_returns_empty(self, mock_service):
        result = scheduled_events_json()
        assert result == []


# ---------------------------------------------------------------------------
# schedule_event / reschedule_event / cancel_event
# ---------------------------------------------------------------------------


class TestScheduleEvent:
    @patch(f"{MOD}.service")
    def test_create_with_defaults(self, mock_service):
        mock_service.return_value.events.return_value.insert.return_value.execute.return_value = {
            "id": "evt_123"
        }
        result = schedule_event("Sync", "2026-04-01", "10:00")
        assert result == "evt_123"

    @patch(f"{MOD}.service")
    def test_create_with_custom_duration(self, mock_service):
        mock_service.return_value.events.return_value.insert.return_value.execute.return_value = {
            "id": "evt_456"
        }
        result = schedule_event("Deep work", "2026-04-01", "09:00", duration=120)
        assert result == "evt_456"


class TestRescheduleEvent:
    @patch(f"{MOD}.service")
    def test_reschedule(self, mock_service):
        mock_svc = mock_service.return_value
        mock_svc.events.return_value.get.return_value.execute.return_value = {
            "start": {"dateTime": "2026-04-01T10:00:00+08:00"},
            "end": {"dateTime": "2026-04-01T11:00:00+08:00"},
        }
        mock_svc.events.return_value.update.return_value.execute.return_value = {}
        result = reschedule_event("evt_abc", "2026-04-02", "14:00")
        assert result == "evt_abc"


class TestCancelEvent:
    @patch(f"{MOD}.service")
    def test_cancel(self, mock_service):
        mock_service.return_value.events.return_value.delete.return_value.execute.return_value = None
        result = cancel_event("evt_xyz")
        assert result == "evt_xyz"


# ---------------------------------------------------------------------------
# is_weekend
# ---------------------------------------------------------------------------


class TestIsWeekend:
    def test_saturday(self):
        assert is_weekend(date(2026, 3, 28)) is True

    def test_sunday(self):
        assert is_weekend(date(2026, 3, 29)) is True

    def test_monday(self):
        assert is_weekend(date(2026, 3, 30)) is False

    def test_friday(self):
        assert is_weekend(date(2026, 3, 27)) is False

    @patch(f"{MOD}.datetime")
    def test_default_uses_today(self, mock_dt):
        """When no date is passed, it uses datetime.now(HKT).date()."""
        fake_now = datetime(2026, 3, 28, 12, 0, tzinfo=HKT)
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        assert is_weekend() is True


# ---------------------------------------------------------------------------
# is_holiday
# ---------------------------------------------------------------------------


class TestIsHoliday:
    @patch(f"{MOD}.scheduled_events_json")
    def test_holiday_keyword_match(self, mock_json):
        mock_json.return_value = [
            {"start": {"date": "2026-03-30"}, "summary": "Public Holiday"}
        ]
        assert is_holiday(date(2026, 3, 30)) is True

    @patch(f"{MOD}.scheduled_events_json")
    def test_chinese_keyword(self, mock_json):
        mock_json.return_value = [
            {"start": {"date": "2026-10-01"}, "summary": "假期"}
        ]
        assert is_holiday(date(2026, 10, 1)) is True

    @patch(f"{MOD}.scheduled_events_json")
    def test_timed_event_not_holiday(self, mock_json):
        mock_json.return_value = [
            {"start": {"dateTime": "2026-03-30T10:00:00"}, "summary": "Team Sync"}
        ]
        assert is_holiday(date(2026, 3, 30)) is False

    @patch(f"{MOD}.scheduled_events_json")
    def test_no_events(self, mock_json):
        mock_json.return_value = []
        assert is_holiday(date(2026, 3, 30)) is False

    @patch(f"{MOD}.scheduled_events_json")
    def test_null_summary_treated_as_empty(self, mock_json):
        mock_json.return_value = [
            {"start": {"date": "2026-03-30"}, "summary": None}
        ]
        assert is_holiday(date(2026, 3, 30)) is False

    @patch(f"{MOD}.scheduled_events_json", side_effect=Exception("API error"))
    def test_api_error_returns_false(self, mock_json):
        assert is_holiday(date(2026, 3, 30)) is False

    @patch(f"{MOD}.scheduled_events_json")
    def test_all_keywords_covered(self, mock_json):
        """Every keyword in _HOLIDAY_KEYWORDS should trigger a match."""
        from metabolon.organelles.circadian_clock import _HOLIDAY_KEYWORDS
        for kw in _HOLIDAY_KEYWORDS:
            mock_json.return_value = [
                {"start": {"date": "2026-04-01"}, "summary": kw}
            ]
            assert is_holiday(date(2026, 4, 1)) is True, f"keyword {kw!r} not detected"

    @patch(f"{MOD}.datetime")
    def test_default_uses_today(self, mock_dt):
        """When no date is passed, it uses datetime.now(HKT).date()."""
        fake_now = datetime(2026, 4, 1, 12, 0, tzinfo=HKT)
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        with patch(f"{MOD}.scheduled_events_json", return_value=[]) as mock_json:
            assert is_holiday() is False
            mock_json.assert_called_once_with("2026-04-01")


# ---------------------------------------------------------------------------
# detect_phase
# ---------------------------------------------------------------------------


class TestDetectPhase:
    """Phase boundaries: dawn [6,10), day [10,17), dusk [17,21), night [21,6)."""

    @pytest.fixture()
    def _no_holiday(self):
        with patch(f"{MOD}.is_holiday", return_value=False):
            yield

    def test_dawn_at_6(self, _no_holiday):
        result = detect_phase(datetime(2026, 3, 30, 6, 0, tzinfo=HKT))
        assert result["phase"] == "dawn"

    def test_dawn_at_9(self, _no_holiday):
        result = detect_phase(datetime(2026, 3, 30, 9, 59, tzinfo=HKT))
        assert result["phase"] == "dawn"

    def test_day_at_10(self, _no_holiday):
        result = detect_phase(datetime(2026, 3, 30, 10, 0, tzinfo=HKT))
        assert result["phase"] == "day"

    def test_day_at_16(self, _no_holiday):
        result = detect_phase(datetime(2026, 3, 30, 16, 59, tzinfo=HKT))
        assert result["phase"] == "day"

    def test_dusk_at_17(self, _no_holiday):
        result = detect_phase(datetime(2026, 3, 30, 17, 0, tzinfo=HKT))
        assert result["phase"] == "dusk"

    def test_dusk_at_20(self, _no_holiday):
        result = detect_phase(datetime(2026, 3, 30, 20, 59, tzinfo=HKT))
        assert result["phase"] == "dusk"

    def test_night_at_21(self, _no_holiday):
        result = detect_phase(datetime(2026, 3, 30, 21, 0, tzinfo=HKT))
        assert result["phase"] == "night"

    def test_night_at_midnight(self, _no_holiday):
        result = detect_phase(datetime(2026, 3, 30, 0, 0, tzinfo=HKT))
        assert result["phase"] == "night"

    def test_night_at_5am(self, _no_holiday):
        result = detect_phase(datetime(2026, 3, 30, 5, 59, tzinfo=HKT))
        assert result["phase"] == "night"

    def test_hkt_hour(self, _no_holiday):
        result = detect_phase(datetime(2026, 3, 30, 14, 30, tzinfo=HKT))
        assert result["hkt_hour"] == 14

    def test_weekday_name(self, _no_holiday):
        result = detect_phase(datetime(2026, 3, 30, 10, 0, tzinfo=HKT))
        assert result["weekday"] == "Monday"

    def test_weekend_workday_false(self, _no_holiday):
        result = detect_phase(datetime(2026, 3, 28, 10, 0, tzinfo=HKT))  # Saturday
        assert result["is_weekend"] is True
        assert result["is_workday"] is False

    def test_holiday_makes_non_workday(self):
        with patch(f"{MOD}.is_holiday", return_value=True):
            result = detect_phase(datetime(2026, 3, 30, 10, 0, tzinfo=HKT))
        assert result["is_holiday"] is True
        assert result["is_workday"] is False

    def test_normal_workday(self, _no_holiday):
        result = detect_phase(datetime(2026, 3, 30, 10, 0, tzinfo=HKT))
        assert result["is_weekend"] is False
        assert result["is_holiday"] is False
        assert result["is_workday"] is True

    def test_return_keys(self, _no_holiday):
        """Ensure all expected keys are present in the result."""
        result = detect_phase(datetime(2026, 3, 30, 12, 0, tzinfo=HKT))
        expected_keys = {"phase", "is_weekend", "is_holiday", "is_workday", "hkt_hour", "weekday"}
        assert set(result.keys()) == expected_keys

    @patch(f"{MOD}.datetime")
    def test_default_uses_now(self, mock_dt):
        """When no datetime is passed, detect_phase uses datetime.now(HKT)."""
        fake_now = datetime(2026, 3, 30, 14, 0, tzinfo=HKT)
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        with patch(f"{MOD}.is_holiday", return_value=False):
            result = detect_phase()
        assert result["phase"] == "day"
        assert result["hkt_hour"] == 14
