from __future__ import annotations

"""Tests for metabolon.organelles.circadian_clock — full coverage with mocked gog CLI."""

import json
from datetime import date, datetime, timedelta, timezone
from subprocess import CompletedProcess
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
    _gog,
)

HKT = timezone(timedelta(hours=8))
MOD = "metabolon.organelles.circadian_clock"


# ---------------------------------------------------------------------------
# _gog
# ---------------------------------------------------------------------------


class TestGog:
    """Unit tests for the low-level _gog subprocess wrapper."""

    @patch(f"{MOD}.subprocess.run")
    def test_success_returns_stdout(self, mock_run):
        mock_run.return_value = CompletedProcess(
            args=["gog"], returncode=0, stdout="ok output\n", stderr=""
        )
        assert _gog(["calendar", "list"]) == "ok output"

    @patch(f"{MOD}.subprocess.run")
    def test_failure_raises_value_error(self, mock_run):
        mock_run.return_value = CompletedProcess(
            args=["gog"], returncode=1, stdout="", stderr="auth error"
        )
        with pytest.raises(ValueError, match="auth error"):
            _gog(["calendar", "list"])

    @patch(f"{MOD}.subprocess.run")
    def test_timeout_propagated(self, mock_run):
        mock_run.side_effect = TimeoutError("timed out")
        with pytest.raises(TimeoutError):
            _gog(["calendar", "list"], timeout=1)

    @patch(f"{MOD}.subprocess.run")
    def test_args_forwarded(self, mock_run):
        mock_run.return_value = CompletedProcess(
            args=["gog"], returncode=0, stdout="done", stderr=""
        )
        _gog(["calendar", "create", "Meeting", "--date", "2026-04-01"])
        mock_run.assert_called_once_with(
            ["gog", "calendar", "create", "Meeting", "--date", "2026-04-01"],
            capture_output=True,
            text=True,
            timeout=15,
        )


# ---------------------------------------------------------------------------
# scheduled_events / scheduled_events_json
# ---------------------------------------------------------------------------


class TestScheduledEvents:
    @patch(f"{MOD}._gog", return_value="3 events found")
    def test_default_today(self, mock_gog):
        result = scheduled_events()
        assert result == "3 events found"
        mock_gog.assert_called_once_with(["calendar", "list", "--json"])

    @patch(f"{MOD}._gog", return_value="1 event")
    def test_custom_date(self, mock_gog):
        result = scheduled_events(date="2026-04-15")
        assert result == "1 event"
        mock_gog.assert_called_once_with(["calendar", "list", "2026-04-15"])


class TestScheduledEventsJson:
    @patch(f"{MOD}._gog", return_value='[{"summary": "Standup"}]')
    def test_valid_json(self, mock_gog):
        result = scheduled_events_json()
        assert result == [{"summary": "Standup"}]

    @patch(f"{MOD}._gog", return_value="not json")
    def test_invalid_json_returns_empty(self, mock_gog):
        result = scheduled_events_json()
        assert result == []

    @patch(f"{MOD}._gog", return_value="")
    def test_empty_output(self, mock_gog):
        result = scheduled_events_json()
        assert result == []


# ---------------------------------------------------------------------------
# schedule_event / reschedule_event / cancel_event
# ---------------------------------------------------------------------------


class TestScheduleEvent:
    @patch(f"{MOD}._gog", return_value="created evt_123")
    def test_create_with_defaults(self, mock_gog):
        result = schedule_event("Sync", "2026-04-01", "10:00")
        assert result == "created evt_123"
        mock_gog.assert_called_once_with(
            ["calendar", "create", "Sync", "--date", "2026-04-01",
             "--time", "10:00", "--duration", "60"]
        )

    @patch(f"{MOD}._gog", return_value="created evt_456")
    def test_create_with_custom_duration(self, mock_gog):
        result = schedule_event("Deep work", "2026-04-01", "09:00", duration=120)
        mock_gog.assert_called_once_with(
            ["calendar", "create", "Deep work", "--date", "2026-04-01",
             "--time", "09:00", "--duration", "120"]
        )


class TestRescheduleEvent:
    @patch(f"{MOD}._gog", return_value="updated")
    def test_reschedule(self, mock_gog):
        result = reschedule_event("evt_abc", "2026-04-02", "14:00")
        assert result == "updated"
        mock_gog.assert_called_once_with(
            ["calendar", "update", "evt_abc", "--from", "2026-04-02T14:00"]
        )


class TestCancelEvent:
    @patch(f"{MOD}._gog", return_value="deleted")
    def test_cancel(self, mock_gog):
        result = cancel_event("evt_xyz")
        assert result == "deleted"
        mock_gog.assert_called_once_with(
            ["calendar", "delete", "evt_xyz", "--force"]
        )


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
    @patch(f"{MOD}._gog")
    def test_holiday_keyword_match(self, mock_gog):
        mock_gog.return_value = json.dumps({
            "events": [{"start": {"date": "2026-03-30"}, "summary": "Public Holiday"}]
        })
        assert is_holiday(date(2026, 3, 30)) is True

    @patch(f"{MOD}._gog")
    def test_chinese_keyword(self, mock_gog):
        mock_gog.return_value = json.dumps({
            "events": [{"start": {"date": "2026-10-01"}, "summary": "假期"}]
        })
        assert is_holiday(date(2026, 10, 1)) is True

    @patch(f"{MOD}._gog")
    def test_timed_event_not_holiday(self, mock_gog):
        mock_gog.return_value = json.dumps({
            "events": [{"start": {"dateTime": "2026-03-30T10:00:00"}, "summary": "Team Sync"}]
        })
        assert is_holiday(date(2026, 3, 30)) is False

    @patch(f"{MOD}._gog")
    def test_no_events(self, mock_gog):
        mock_gog.return_value = json.dumps({"events": []})
        assert is_holiday(date(2026, 3, 30)) is False

    @patch(f"{MOD}._gog")
    def test_null_summary_treated_as_empty(self, mock_gog):
        mock_gog.return_value = json.dumps({
            "events": [{"start": {"date": "2026-03-30"}, "summary": None}]
        })
        assert is_holiday(date(2026, 3, 30)) is False

    @patch(f"{MOD}._gog", side_effect=ValueError("gog down"))
    def test_gog_error_returns_false(self, mock_gog):
        assert is_holiday(date(2026, 3, 30)) is False

    @patch(f"{MOD}._gog", return_value="bad json")
    def test_json_parse_error_returns_false(self, mock_gog):
        assert is_holiday(date(2026, 3, 30)) is False

    @patch(f"{MOD}._gog")
    def test_all_keywords_covered(self, mock_gog):
        """Every keyword in _HOLIDAY_KEYWORDS should trigger a match."""
        from metabolon.organelles.circadian_clock import _HOLIDAY_KEYWORDS
        for kw in _HOLIDAY_KEYWORDS:
            mock_gog.return_value = json.dumps({
                "events": [{"start": {"date": "2026-04-01"}, "summary": kw}]
            })
            assert is_holiday(date(2026, 4, 1)) is True, f"keyword {kw!r} not detected"

    @patch(f"{MOD}.datetime")
    def test_default_uses_today(self, mock_dt):
        """When no date is passed, it uses datetime.now(HKT).date()."""
        fake_now = datetime(2026, 4, 1, 12, 0, tzinfo=HKT)
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        with patch(f"{MOD}._gog", return_value='{"events": []}') as mock_gog:
            assert is_holiday() is False
            call_args = mock_gog.call_args[0][0]
            assert "2026-04-01" in call_args


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
