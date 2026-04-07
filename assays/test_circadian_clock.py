from __future__ import annotations

"""Tests for circadian_clock organelle."""

from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

HKT = timezone(timedelta(hours=8))


class TestIsWeekend:
    def test_saturday(self):
        from metabolon.organelles.circadian_clock import is_weekend

        # 2026-03-28 is a Saturday
        assert is_weekend(date(2026, 3, 28)) is True

    def test_sunday(self):
        from metabolon.organelles.circadian_clock import is_weekend

        assert is_weekend(date(2026, 3, 29)) is True

    def test_weekday(self):
        from metabolon.organelles.circadian_clock import is_weekend

        # 2026-03-30 is a Monday
        assert is_weekend(date(2026, 3, 30)) is False


class TestDetectPhase:
    def test_dawn(self):
        from metabolon.organelles.circadian_clock import detect_phase

        now = datetime(2026, 3, 30, 7, 30, tzinfo=HKT)
        with patch("metabolon.organelles.circadian_clock.is_holiday", return_value=False):
            result = detect_phase(now)
        assert result["phase"] == "dawn"
        assert result["hkt_hour"] == 7

    def test_day(self):
        from metabolon.organelles.circadian_clock import detect_phase

        now = datetime(2026, 3, 30, 14, 0, tzinfo=HKT)
        with patch("metabolon.organelles.circadian_clock.is_holiday", return_value=False):
            result = detect_phase(now)
        assert result["phase"] == "day"

    def test_dusk(self):
        from metabolon.organelles.circadian_clock import detect_phase

        now = datetime(2026, 3, 30, 19, 0, tzinfo=HKT)
        with patch("metabolon.organelles.circadian_clock.is_holiday", return_value=False):
            result = detect_phase(now)
        assert result["phase"] == "dusk"

    def test_night(self):
        from metabolon.organelles.circadian_clock import detect_phase

        now = datetime(2026, 3, 30, 23, 0, tzinfo=HKT)
        with patch("metabolon.organelles.circadian_clock.is_holiday", return_value=False):
            result = detect_phase(now)
        assert result["phase"] == "night"

    def test_early_morning_is_night(self):
        from metabolon.organelles.circadian_clock import detect_phase

        now = datetime(2026, 3, 30, 3, 0, tzinfo=HKT)
        with patch("metabolon.organelles.circadian_clock.is_holiday", return_value=False):
            result = detect_phase(now)
        assert result["phase"] == "night"

    def test_weekend_flag(self):
        from metabolon.organelles.circadian_clock import detect_phase

        sat = datetime(2026, 3, 28, 10, 0, tzinfo=HKT)
        with patch("metabolon.organelles.circadian_clock.is_holiday", return_value=False):
            result = detect_phase(sat)
        assert result["is_weekend"] is True
        assert result["is_workday"] is False

    def test_workday_flag(self):
        from metabolon.organelles.circadian_clock import detect_phase

        mon = datetime(2026, 3, 30, 10, 0, tzinfo=HKT)
        with patch("metabolon.organelles.circadian_clock.is_holiday", return_value=False):
            result = detect_phase(mon)
        assert result["is_weekend"] is False
        assert result["is_workday"] is True

    def test_holiday_flag(self):
        from metabolon.organelles.circadian_clock import detect_phase

        mon = datetime(2026, 3, 30, 10, 0, tzinfo=HKT)
        with patch("metabolon.organelles.circadian_clock.is_holiday", return_value=True):
            result = detect_phase(mon)
        assert result["is_holiday"] is True
        assert result["is_workday"] is False


class TestIsHoliday:
    def test_holiday_detected(self):
        from metabolon.organelles.circadian_clock import is_holiday

        events_json = (
            '{"events": [{"start": {"date": "2026-03-30"}, "summary": "Public Holiday"}]}'
        )
        with patch("metabolon.organelles.circadian_clock._gog", return_value=events_json):
            assert is_holiday(date(2026, 3, 30)) is True

    def test_no_holiday(self):
        from metabolon.organelles.circadian_clock import is_holiday

        events_json = '{"events": [{"start": {"dateTime": "2026-03-30T10:00:00"}, "summary": "Team Meeting"}]}'
        with patch("metabolon.organelles.circadian_clock._gog", return_value=events_json):
            assert is_holiday(date(2026, 3, 30)) is False

    def test_gog_failure_returns_false(self):
        from metabolon.organelles.circadian_clock import is_holiday

        with patch(
            "metabolon.organelles.circadian_clock._gog", side_effect=ValueError("gog failed")
        ):
            assert is_holiday(date(2026, 3, 30)) is False

    def test_chinese_holiday_keyword(self):
        from metabolon.organelles.circadian_clock import is_holiday

        events_json = '{"events": [{"start": {"date": "2026-10-01"}, "summary": "假期"}]}'
        with patch("metabolon.organelles.circadian_clock._gog", return_value=events_json):
            assert is_holiday(date(2026, 10, 1)) is True


class TestScheduleEvent:
    """Tests for schedule_event with description and location support."""

    def _make_mock_service(self, event_id="evt123"):
        mock_event = {"id": event_id}
        mock_insert = MagicMock()
        mock_insert.execute.return_value = mock_event
        mock_events = MagicMock()
        mock_events.insert.return_value = mock_insert
        mock_svc = MagicMock()
        mock_svc.events.return_value = mock_events
        return mock_svc

    def test_basic_event_no_optional_fields(self):
        from metabolon.organelles.circadian_clock import schedule_event

        mock_svc = self._make_mock_service("basic123")
        with patch("metabolon.organelles.circadian_clock.service", return_value=mock_svc):
            result = schedule_event("Team standup", "2026-04-10", "09:00")

        assert result == "basic123"
        call_args = mock_svc.events().insert.call_args
        body = call_args.kwargs["body"]
        assert body["summary"] == "Team standup"
        assert "description" not in body
        assert "location" not in body

    def test_event_with_description(self):
        from metabolon.organelles.circadian_clock import schedule_event

        mock_svc = self._make_mock_service("desc123")
        with patch("metabolon.organelles.circadian_clock.service", return_value=mock_svc):
            result = schedule_event(
                "Sprint review",
                "2026-04-10",
                "14:00",
                description="Q2 sprint review with stakeholders",
            )

        assert result == "desc123"
        call_args = mock_svc.events().insert.call_args
        body = call_args.kwargs["body"]
        assert body["summary"] == "Sprint review"
        assert body["description"] == "Q2 sprint review with stakeholders"
        assert "location" not in body

    def test_event_with_location(self):
        from metabolon.organelles.circadian_clock import schedule_event

        mock_svc = self._make_mock_service("loc123")
        with patch("metabolon.organelles.circadian_clock.service", return_value=mock_svc):
            result = schedule_event(
                "Client call",
                "2026-04-11",
                "10:30",
                location="Zoom - https://zoom.us/j/123",
            )

        assert result == "loc123"
        call_args = mock_svc.events().insert.call_args
        body = call_args.kwargs["body"]
        assert body["summary"] == "Client call"
        assert body["location"] == "Zoom - https://zoom.us/j/123"
        assert "description" not in body

    def test_event_with_description_and_location(self):
        from metabolon.organelles.circadian_clock import schedule_event

        mock_svc = self._make_mock_service("both123")
        with patch("metabolon.organelles.circadian_clock.service", return_value=mock_svc):
            result = schedule_event(
                "Board meeting",
                "2026-04-12",
                "15:00",
                duration=120,
                description="Quarterly board review",
                location="Conference Room A, 42/F",
            )

        assert result == "both123"
        call_args = mock_svc.events().insert.call_args
        body = call_args.kwargs["body"]
        assert body["summary"] == "Board meeting"
        assert body["description"] == "Quarterly board review"
        assert body["location"] == "Conference Room A, 42/F"
        # Verify start/end times with custom duration
        assert "15:00" in body["start"]["dateTime"]
        assert "17:00" in body["end"]["dateTime"]

    def test_empty_string_description_not_included(self):
        from metabolon.organelles.circadian_clock import schedule_event

        mock_svc = self._make_mock_service("empty_desc")
        with patch("metabolon.organelles.circadian_clock.service", return_value=mock_svc):
            result = schedule_event(
                "Quick sync",
                "2026-04-13",
                "11:00",
                description="",
            )

        assert result == "empty_desc"
        body = mock_svc.events().insert.call_args.kwargs["body"]
        assert "description" not in body
