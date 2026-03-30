"""Tests for circadian_clock organelle."""
from __future__ import annotations

from datetime import date, datetime, timezone, timedelta
from unittest.mock import patch

import pytest

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
        events_json = '{"events": [{"start": {"date": "2026-03-30"}, "summary": "Public Holiday"}]}'
        with patch("metabolon.organelles.circadian_clock._gog", return_value=events_json):
            assert is_holiday(date(2026, 3, 30)) is True

    def test_no_holiday(self):
        from metabolon.organelles.circadian_clock import is_holiday
        events_json = '{"events": [{"start": {"dateTime": "2026-03-30T10:00:00"}, "summary": "Team Meeting"}]}'
        with patch("metabolon.organelles.circadian_clock._gog", return_value=events_json):
            assert is_holiday(date(2026, 3, 30)) is False

    def test_gog_failure_returns_false(self):
        from metabolon.organelles.circadian_clock import is_holiday
        with patch("metabolon.organelles.circadian_clock._gog", side_effect=ValueError("gog failed")):
            assert is_holiday(date(2026, 3, 30)) is False

    def test_chinese_holiday_keyword(self):
        from metabolon.organelles.circadian_clock import is_holiday
        events_json = '{"events": [{"start": {"date": "2026-10-01"}, "summary": "假期"}]}'
        with patch("metabolon.organelles.circadian_clock._gog", return_value=events_json):
            assert is_holiday(date(2026, 10, 1)) is True
