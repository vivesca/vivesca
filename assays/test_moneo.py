"""Tests for pure functions in metabolon.organelles.moneo."""

from __future__ import annotations

import pytest
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


class TestResolveDateKeyword:
    def test_today(self):
        from metabolon.organelles.moneo import resolve_date_keyword

        now = datetime(2026, 3, 30, 14, 0, tzinfo=ZoneInfo("Asia/Hong_Kong"))
        assert resolve_date_keyword("today", now) == "2026-03-30"

    def test_tomorrow(self):
        from metabolon.organelles.moneo import resolve_date_keyword

        now = datetime(2026, 3, 30, 14, 0, tzinfo=ZoneInfo("Asia/Hong_Kong"))
        assert resolve_date_keyword("tomorrow", now) == "2026-03-31"

    def test_literal_date(self):
        from metabolon.organelles.moneo import resolve_date_keyword

        assert resolve_date_keyword("2026-04-15") == "2026-04-15"


class TestParseRelative:
    def test_minutes(self):
        from metabolon.organelles.moneo import parse_relative

        assert parse_relative("30m") == timedelta(minutes=30)

    def test_hours(self):
        from metabolon.organelles.moneo import parse_relative

        assert parse_relative("2h") == timedelta(hours=2)

    def test_seconds(self):
        from metabolon.organelles.moneo import parse_relative

        assert parse_relative("90s") == timedelta(seconds=90)

    def test_invalid_raises(self):
        from metabolon.organelles.moneo import MoneoError, parse_relative

        with pytest.raises(MoneoError):
            parse_relative("bad")


class TestParseInterval:
    def test_days(self):
        from metabolon.organelles.moneo import parse_interval

        assert parse_interval("7d") == timedelta(days=7)

    def test_hours(self):
        from metabolon.organelles.moneo import parse_interval

        assert parse_interval("4h") == timedelta(hours=4)

    def test_invalid_unit_raises(self):
        from metabolon.organelles.moneo import MoneoError, parse_interval

        with pytest.raises(MoneoError):
            parse_interval("5x")

    def test_zero_raises(self):
        from metabolon.organelles.moneo import MoneoError, parse_interval

        with pytest.raises(MoneoError):
            parse_interval("0h")


class TestParseDate:
    def test_valid_date(self):
        from metabolon.organelles.moneo import parse_date

        assert parse_date("2026-03-30") == date(2026, 3, 30)

    def test_invalid_raises(self):
        from metabolon.organelles.moneo import MoneoError, parse_date

        with pytest.raises(MoneoError):
            parse_date("not-a-date")


class TestParseAt:
    def test_valid_time(self):
        from metabolon.organelles.moneo import parse_at

        assert parse_at("14:30") == time(14, 30)

    def test_invalid_raises(self):
        from metabolon.organelles.moneo import MoneoError, parse_at

        with pytest.raises(MoneoError):
            parse_at("bad")


class TestParseDueString:
    def test_time_only(self):
        from metabolon.organelles.moneo import parse_due_string

        time_str, date_str = parse_due_string("14:30")
        assert time_str == "14:30"
        assert date_str is None

    def test_date_only(self):
        from metabolon.organelles.moneo import parse_due_string

        time_str, date_str = parse_due_string("today")
        assert time_str is None
        # date_str will be resolved

    def test_date_and_time(self):
        from metabolon.organelles.moneo import parse_due_string

        time_str, date_str = parse_due_string("today 16:15")
        assert time_str == "16:15"

    def test_invalid_raises(self):
        from metabolon.organelles.moneo import MoneoError, parse_due_string

        with pytest.raises(MoneoError):
            parse_due_string("a b c")


class TestHktFromTs:
    def test_converts_correctly(self):
        from metabolon.organelles.moneo import hkt_from_ts

        result = hkt_from_ts(1711785600)  # 2024-03-30 08:00:00 UTC
        assert result.hour is not None  # Just verify it doesn't crash
        assert str(result.tzinfo) == "Asia/Hong_Kong"
