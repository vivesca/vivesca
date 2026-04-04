from __future__ import annotations

"""Meta-tests for metabolon/organelles/tests/test_moneo.py.

Verifies every test function in the original test module executes
without error, and adds supplementary tests with mocked external
calls (datetime.now, subprocess, file I/O) to cover edge cases.
"""

import io
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.organelles import moneo
from metabolon.organelles.tests import test_moneo as tm

# ---------------------------------------------------------------------------
# Helpers (mirror the ones in test_moneo.py to avoid coupling)
# ---------------------------------------------------------------------------


def _empty_db() -> dict:
    return {"re": [], "mt": {"ts": 0}, "dl": {}}


def _db_with_reminders() -> dict:
    data = _empty_db()
    data["re"] = [
        {"u": "AAAAAAaaaaaabbbbbb", "n": "Buy milk", "d": 1000},
        {"u": "BBBBBBccccccdddddd", "n": "Call dentist", "d": 2000},
        {"u": "CCCCCCeeeeeeffffff", "n": "Read book", "d": 3000},
    ]
    return data


# ===================================================================
# Part 1: Regression guard — every original test must pass
# ===================================================================

# --- parse_due_string group ---


def test_original_parse_due_time_only() -> None:
    tm.test_parse_due_time_only()


def test_original_parse_due_date_only() -> None:
    tm.test_parse_due_date_only()


def test_original_parse_due_today_with_time() -> None:
    tm.test_parse_due_today_with_time()


def test_original_parse_due_tomorrow_with_time() -> None:
    tm.test_parse_due_tomorrow_with_time()


def test_original_parse_due_iso_date_with_time() -> None:
    tm.test_parse_due_iso_date_with_time()


def test_original_parse_due_today_keyword_alone() -> None:
    tm.test_parse_due_today_keyword_alone()


def test_original_parse_due_tomorrow_keyword_alone() -> None:
    tm.test_parse_due_tomorrow_keyword_alone()


# --- resolve_date_keyword ---


def test_original_resolve_date_keyword_today_case_insensitive() -> None:
    tm.test_resolve_date_keyword_today_case_insensitive()


def test_original_resolve_date_keyword_passthrough() -> None:
    tm.test_resolve_date_keyword_passthrough()


# --- parse_time ---


def test_original_parse_time_with_date_defaults_to_0900() -> None:
    tm.test_parse_time_with_date_defaults_to_0900()


# --- expand_schedule ---


def test_original_expand_schedule_skips_night() -> None:
    tm.test_expand_schedule_skips_night_by_default()


def test_original_expand_schedule_can_include_night() -> None:
    tm.test_expand_schedule_can_include_night()


# --- recur_code ---


def test_original_recur_code_all_frequencies() -> None:
    tm.test_recur_code_all_frequencies()


def test_original_recur_code_unknown_returns_none() -> None:
    tm.test_recur_code_unknown_returns_none()


# --- generate_uuid ---


def test_original_generate_uuid_format() -> None:
    tm.test_generate_uuid_format()


def test_original_generate_uuid_uniqueness() -> None:
    tm.test_generate_uuid_uniqueness()


# --- make_reminder ---


def test_original_make_reminder_basic() -> None:
    tm.test_make_reminder_basic()


def test_original_make_reminder_with_autosnooze() -> None:
    tm.test_make_reminder_with_autosnooze()


def test_original_make_reminder_daily_recurrence() -> None:
    tm.test_make_reminder_daily_recurrence()


def test_original_make_reminder_weekly_recurrence() -> None:
    tm.test_make_reminder_weekly_recurrence()


def test_original_make_reminder_quarterly_recurrence() -> None:
    tm.test_make_reminder_quarterly_recurrence()


# --- add_direct ---


def test_original_add_direct_appends_to_data() -> None:
    tm.test_add_direct_appends_to_data()


def test_original_add_direct_multiple() -> None:
    tm.test_add_direct_multiple()


def test_original_add_direct_preserves_existing() -> None:
    tm.test_add_direct_preserves_existing()


# --- find_duplicate ---


def test_original_find_duplicate_same_title_and_time() -> None:
    tm.test_find_duplicate_detects_same_title_and_time()


def test_original_find_duplicate_case_insensitive() -> None:
    tm.test_find_duplicate_case_insensitive()


def test_original_find_duplicate_different_time() -> None:
    tm.test_find_duplicate_different_time_no_match()


def test_original_find_duplicate_different_title() -> None:
    tm.test_find_duplicate_different_title_no_match()


# --- short_uuid ---


def test_original_short_uuid_first_8() -> None:
    tm.test_short_uuid_returns_first_8_chars()


def test_original_short_uuid_none() -> None:
    tm.test_short_uuid_none_returns_dashes()


def test_original_short_uuid_short_input() -> None:
    tm.test_short_uuid_short_input()


# --- is_uuid_prefix ---


def test_original_is_uuid_prefix_valid_8() -> None:
    tm.test_is_uuid_prefix_valid_8_chars()


def test_original_is_uuid_prefix_full() -> None:
    tm.test_is_uuid_prefix_valid_full_uuid()


def test_original_is_uuid_prefix_too_short() -> None:
    tm.test_is_uuid_prefix_too_short()


def test_original_is_uuid_prefix_too_long() -> None:
    tm.test_is_uuid_prefix_too_long()


def test_original_is_uuid_prefix_spaces() -> None:
    tm.test_is_uuid_prefix_with_spaces()


def test_original_is_uuid_prefix_special_chars() -> None:
    tm.test_is_uuid_prefix_with_special_chars()


def test_original_is_uuid_prefix_base64url() -> None:
    tm.test_is_uuid_prefix_base64url_chars()


# --- is_numeric ---


def test_original_is_numeric_positive() -> None:
    tm.test_is_numeric_positive_int()


def test_original_is_numeric_zero() -> None:
    tm.test_is_numeric_zero_is_false()


def test_original_is_numeric_negative() -> None:
    tm.test_is_numeric_negative_is_false()


def test_original_is_numeric_non_number() -> None:
    tm.test_is_numeric_non_number()


# --- find_by_uuid_prefix ---


def test_original_find_by_uuid_prefix_exact() -> None:
    tm.test_find_by_uuid_prefix_exact_match()


def test_original_find_by_uuid_prefix_no_match() -> None:
    tm.test_find_by_uuid_prefix_no_match()


def test_original_find_by_uuid_prefix_multiple() -> None:
    tm.test_find_by_uuid_prefix_multiple_matches()


# --- resolve_target ---


def test_original_resolve_target_numeric() -> None:
    tm.test_resolve_target_by_numeric_index()


def test_original_resolve_target_uuid_prefix() -> None:
    tm.test_resolve_target_by_uuid_prefix()


def test_original_resolve_target_pattern() -> None:
    tm.test_resolve_target_by_pattern()


def test_original_resolve_target_pattern_case_insensitive() -> None:
    tm.test_resolve_target_pattern_case_insensitive()


def test_original_resolve_target_pattern_not_found() -> None:
    tm.test_resolve_target_pattern_not_found()


def test_original_resolve_target_uuid_not_found() -> None:
    tm.test_resolve_target_uuid_prefix_not_found()


def test_original_resolve_target_numeric_out_of_range() -> None:
    tm.test_resolve_target_numeric_out_of_range()


def test_original_resolve_target_prefers_numeric() -> None:
    tm.test_resolve_target_prefers_numeric_over_uuid()


# --- confirm_action ---


def test_original_confirm_action_eof() -> None:
    tm.test_confirm_action_eof_returns_false()


def test_original_confirm_action_yes() -> None:
    tm.test_confirm_action_yes()


def test_original_confirm_action_no() -> None:
    tm.test_confirm_action_no()


def test_original_confirm_action_empty() -> None:
    tm.test_confirm_action_empty_is_no()


# ===================================================================
# Part 2: Supplementary tests with mocked external calls
# ===================================================================


class TestParseDueStringWithMockedNow:
    """Tests for parse_due_string with datetime.now patched."""

    @patch.object(moneo, "hkt_now")
    def test_today_resolves_to_mocked_date(self, mock_now: MagicMock) -> None:
        mock_now.return_value = datetime(2026, 6, 15, 10, 0, tzinfo=moneo.HKT)
        at, date = moneo.parse_due_string("today 14:00")
        assert at == "14:00"
        assert date == "2026-06-15"

    @patch.object(moneo, "hkt_now")
    def test_tomorrow_resolves_to_next_day(self, mock_now: MagicMock) -> None:
        mock_now.return_value = datetime(2026, 12, 31, 23, 0, tzinfo=moneo.HKT)
        at, date = moneo.parse_due_string("tomorrow 09:00")
        assert at == "09:00"
        assert date == "2027-01-01"

    @patch.object(moneo, "hkt_now")
    def test_today_at_year_boundary(self, mock_now: MagicMock) -> None:
        mock_now.return_value = datetime(2025, 12, 31, 12, 0, tzinfo=moneo.HKT)
        at, date = moneo.parse_due_string("today")
        assert at is None
        assert date == "2025-12-31"


class TestResolveDateKeywordWithMock:
    """Edge cases for resolve_date_keyword."""

    @patch.object(moneo, "hkt_now")
    def test_tomorrow_case_insensitive(self, mock_now: MagicMock) -> None:
        mock_now.return_value = datetime(2026, 3, 1, 8, 0, tzinfo=moneo.HKT)
        assert moneo.resolve_date_keyword("TOMORROW") == "2026-03-02"
        assert moneo.resolve_date_keyword("Tomorrow") == "2026-03-02"

    def test_passthrough_non_keyword(self) -> None:
        assert moneo.resolve_date_keyword("2025-01-01") == "2025-01-01"


class TestParseTimeWithMock:
    """Tests for parse_time with now= parameter."""

    def test_relative_30m(self) -> None:
        now = datetime(2026, 5, 10, 14, 0, tzinfo=moneo.HKT)
        ts = moneo.parse_time("30m", None, None, now=now)
        result = moneo.hkt_from_ts(ts)
        assert result.hour == 14
        assert result.minute == 30

    def test_relative_2h(self) -> None:
        now = datetime(2026, 5, 10, 14, 0, tzinfo=moneo.HKT)
        ts = moneo.parse_time("2h", None, None, now=now)
        result = moneo.hkt_from_ts(ts)
        assert result.hour == 16

    def test_at_only_uses_today(self) -> None:
        now = datetime(2026, 5, 10, 8, 0, tzinfo=moneo.HKT)
        ts = moneo.parse_time(None, "15:30", None, now=now)
        result = moneo.hkt_from_ts(ts)
        assert result.hour == 15
        assert result.minute == 30
        assert result.date() == now.date()

    def test_none_inputs_returns_none(self) -> None:
        now = datetime(2026, 5, 10, 8, 0, tzinfo=moneo.HKT)
        assert moneo.parse_time(None, None, None, now=now) is None


class TestExpandScheduleWithMock:
    """Tests for expand_schedule edge cases."""

    def test_single_day_schedule(self) -> None:
        base = int(datetime(2026, 3, 16, 9, 0, tzinfo=moneo.HKT).timestamp())
        expanded = moneo.expand_schedule(base, moneo.parse_interval("8h"), "2026-03-16")
        formatted = [moneo.hkt_from_ts(ts).strftime("%H:%M") for ts in expanded]
        assert formatted == ["09:00", "17:00"]

    def test_night_skipping_excludes_23_and_before_7(self) -> None:
        base = int(datetime(2026, 3, 16, 22, 0, tzinfo=moneo.HKT).timestamp())
        expanded = moneo.expand_schedule(base, moneo.parse_interval("1h"), "2026-03-17")
        hours = [moneo.hkt_from_ts(ts).hour for ts in expanded]
        assert 23 not in hours
        for h in range(0, 7):
            assert h not in hours


class TestMakeReminderWithMockedTimestamp:
    """Tests for make_reminder with now_ts patched."""

    @patch.object(moneo, "now_ts", return_value=9999999)
    @patch.object(moneo, "generate_uuid", return_value="fixeduuid1234567890")
    def test_created_and_modified_use_now_ts(
        self, mock_uuid: MagicMock, mock_now: MagicMock
    ) -> None:
        reminder = moneo.make_reminder("Test", 5000, None, None)
        assert reminder["b"] == 9999999
        assert reminder["m"] == 9999999
        assert reminder["u"] == "fixeduuid1234567890"

    def test_make_uuid_is_exactly_22_chars(self) -> None:
        uid = moneo.generate_uuid()
        assert len(uid) == 22

    def test_make_reminder_monthly_recurrence(self) -> None:
        ts = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
        reminder = moneo.make_reminder("Monthly", ts, "monthly", None)
        assert reminder["rf"] == "m"
        assert reminder["rd"] == ts
        assert reminder["rn"] == 8  # monthly unit

    def test_make_reminder_yearly_recurrence(self) -> None:
        ts = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
        reminder = moneo.make_reminder("Yearly", ts, "yearly", None)
        assert reminder["rf"] == "y"
        assert reminder["rd"] == ts
        assert reminder["rn"] == 4  # yearly unit


class TestFindDuplicateWithMock:
    """Tests for find_duplicate with in-memory data (no file I/O)."""

    def test_finds_duplicate_across_different_hours_same_date(self) -> None:
        ts = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
        data = _empty_db()
        data["re"].append({"u": "abc123", "n": "Meds", "d": ts})
        # Same title, same timestamp → match
        assert moneo.find_duplicate("Meds", ts, data) is not None

    def test_no_duplicate_with_different_hour(self) -> None:
        ts10 = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
        ts14 = int(datetime(2026, 3, 20, 14, 0, tzinfo=moneo.HKT).timestamp())
        data = _empty_db()
        data["re"].append({"u": "abc123", "n": "Meds", "d": ts10})
        # Same title but different hour → no match
        assert moneo.find_duplicate("Meds", ts14, data) is None

    def test_no_duplicate_in_empty_db(self) -> None:
        ts = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
        assert moneo.find_duplicate("Anything", ts, _empty_db()) is None


class TestConfirmActionWithMockedInput:
    """Tests for confirm_action with sys.stdin mocked."""

    def test_keyboard_interrupt_returns_false(self) -> None:
        data = _db_with_reminders()
        reminder = data["re"][0]
        old_stdin = sys.stdin
        sys.stdin = MagicMock()
        sys.stdin.readline.side_effect = KeyboardInterrupt
        try:
            result = moneo.confirm_action(reminder, "Delete")
            assert result is False
        finally:
            sys.stdin = old_stdin

    def test_yes_uppercase_confirms(self) -> None:
        data = _db_with_reminders()
        reminder = data["re"][0]
        old_stdin = sys.stdin
        sys.stdin = io.StringIO("YES\n")
        try:
            result = moneo.confirm_action(reminder, "Delete")
            assert result is True
        finally:
            sys.stdin = old_stdin


class TestReadDbWithMockedFile:
    """Tests for read_db with file system mocked."""

    @patch.object(moneo, "due_db_path")
    def test_read_db_file_not_found_raises(self, mock_path: MagicMock) -> None:
        mock_path.return_value = Path("/tmp/nonexistent_due_test_db.duedb")
        with pytest.raises(moneo.MoneoError, match="Failed to read"):
            moneo.read_db()

    @patch.object(moneo, "due_db_path")
    def test_read_db_permission_error_returns_empty(self, mock_path: MagicMock) -> None:
        mock_path.return_value = Path("/tmp/permission_denied_test.duedb")
        with patch("gzip.open", side_effect=PermissionError("denied")):
            result = moneo.read_db()
            assert result == {}


class TestDuePidWithMockedSubprocess:
    """Tests for due_pid with subprocess.run mocked."""

    @patch.object(moneo.subprocess, "run")
    def test_due_pid_found(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="12345\n")
        assert moneo.due_pid() == "12345"

    @patch.object(moneo.subprocess, "run")
    def test_due_pid_not_found(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert moneo.due_pid() is None

    @patch.object(moneo.subprocess, "run")
    def test_due_pid_empty_stdout(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="\n")
        assert moneo.due_pid() is None


class TestWriteDbWithMockedIO:
    """Tests for write_db with file I/O and subprocess mocked."""

    @patch.object(moneo, "git_snapshot")
    @patch.object(moneo, "due_pid", return_value=None)
    @patch.object(moneo, "due_db_path")
    def test_write_db_updates_mt_timestamp(
        self, mock_path: MagicMock, mock_pid: MagicMock, mock_git: MagicMock
    ) -> None:
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".duedb", delete=False) as f:
            tmp = Path(f.name)
        mock_path.return_value = tmp
        data: dict = {"re": [], "mt": {"ts": 0}, "dl": {}}
        try:
            with patch.object(moneo, "now_ts", return_value=5555555):
                moneo.write_db(data)
            assert data["mt"]["ts"] == 5555555
        finally:
            tmp.unlink(missing_ok=True)


class TestHomeDir:
    """Tests for home_dir."""

    def test_home_dir_from_env(self) -> None:
        with patch.dict(moneo.os.environ, {"HOME": "/custom/home"}):
            assert moneo.home_dir() == Path("/custom/home")

    def test_home_dir_missing_env_raises(self) -> None:
        with patch.dict(moneo.os.environ, {}, clear=True):
            with pytest.raises(moneo.MoneoError, match="HOME"):
                moneo.home_dir()


class TestEdgeCases:
    """Misc edge case tests for functions used in test_moneo.py."""

    def test_recur_label_known_codes(self) -> None:
        assert moneo.recur_label("d") == "daily"
        assert moneo.recur_label("w") == "weekly"
        assert moneo.recur_label("m") == "monthly"
        assert moneo.recur_label("q") == "quarterly"
        assert moneo.recur_label("y") == "yearly"

    def test_recur_label_unknown_returns_none(self) -> None:
        assert moneo.recur_label("x") is None
        assert moneo.recur_label(None) is None
        assert moneo.recur_label("") is None

    def test_recur_unit_values(self) -> None:
        assert moneo.recur_unit("daily") == 16
        assert moneo.recur_unit("weekly") == 256
        assert moneo.recur_unit("monthly") == 8
        assert moneo.recur_unit("quarterly") == 8
        assert moneo.recur_unit("yearly") == 4
        assert moneo.recur_unit("hourly") is None

    def test_recur_freq_values(self) -> None:
        assert moneo.recur_freq("daily") == 1
        assert moneo.recur_freq("quarterly") == 3
        assert moneo.recur_freq("hourly") is None

    def test_reminder_due_ts_returns_int(self) -> None:
        assert moneo.reminder_due_ts({"d": 12345}) == 12345

    def test_reminder_due_ts_none_for_non_int(self) -> None:
        assert moneo.reminder_due_ts({}) is None
        assert moneo.reminder_due_ts({"d": "bad"}) is None

    def test_reminder_title_returns_string(self) -> None:
        assert moneo.reminder_title({"n": "Hello"}) == "Hello"

    def test_reminder_title_empty_for_missing(self) -> None:
        assert moneo.reminder_title({}) == ""
        assert moneo.reminder_title({"n": 42}) == ""

    def test_reminder_uuid_returns_string(self) -> None:
        assert moneo.reminder_uuid({"u": "abc"}) == "abc"

    def test_reminder_uuid_none_for_missing(self) -> None:
        assert moneo.reminder_uuid({}) is None
        assert moneo.reminder_uuid({"u": 123}) is None

    def test_parse_interval_minutes(self) -> None:
        td = moneo.parse_interval("30m")
        assert td.total_seconds() == 1800

    def test_parse_interval_hours(self) -> None:
        td = moneo.parse_interval("6h")
        assert td.total_seconds() == 21600

    def test_parse_interval_days(self) -> None:
        td = moneo.parse_interval("2d")
        assert td.total_seconds() == 172800

    def test_parse_relative_seconds(self) -> None:
        td = moneo.parse_relative("90s")
        assert td.total_seconds() == 90

    def test_parse_date_iso(self) -> None:
        d = moneo.parse_date("2026-03-16")
        assert d.year == 2026
        assert d.month == 3
        assert d.day == 16

    def test_sorted_reminders_orders_by_due(self) -> None:
        data = _empty_db()
        data["re"] = [
            {"u": "c", "n": "C", "d": 3000},
            {"u": "a", "n": "A", "d": 1000},
            {"u": "b", "n": "B", "d": 2000},
        ]
        result = moneo.sorted_reminders(data)
        assert [r["n"] for r in result] == ["A", "B", "C"]

    def test_reminders_slice_returns_list(self) -> None:
        assert moneo.reminders_slice({"re": [{"n": "x"}]}) == [{"n": "x"}]

    def test_reminders_slice_missing_returns_empty(self) -> None:
        assert moneo.reminders_slice({}) == []

    def test_reminders_mut_creates_list(self) -> None:
        data: dict = {}
        result = moneo.reminders_mut(data)
        assert result == []
        assert data["re"] == []

    def test_set_tombstone(self) -> None:
        data: dict = {}
        moneo.set_tombstone(data, "uuid1", 9999)
        assert data["dl"]["uuid1"] == 9999

    def test_get_reminder_valid_index(self) -> None:
        data = _db_with_reminders()
        _raw_idx, reminder = moneo.get_reminder(data, 1)
        assert reminder["n"] == "Buy milk"

    def test_get_reminder_invalid_index_raises(self) -> None:
        data = _db_with_reminders()
        with pytest.raises(moneo.MoneoError, match="no reminder at index"):
            moneo.get_reminder(data, 99)

    def test_active_reminders_excludes_logbook(self) -> None:
        ts = int(datetime(2026, 3, 20, 10, 0, tzinfo=moneo.HKT).timestamp())
        data = _empty_db()
        data["re"] = [
            {"u": "a1", "n": "Active", "d": ts},
            {"u": "b2", "n": "Done", "d": ts},
        ]
        data["lb"] = [{"n": "Done", "d": ts}]
        active = moneo.active_reminders(data)
        assert len(active) == 1
        assert active[0]["n"] == "Active"

    def test_hkt_from_ts_roundtrip(self) -> None:
        dt = datetime(2026, 6, 15, 14, 30, tzinfo=moneo.HKT)
        ts = int(dt.timestamp())
        result = moneo.hkt_from_ts(ts)
        assert result.hour == 14
        assert result.minute == 30
        assert result.date() == dt.date()


# Ensure no syntax errors in the test module itself
def test_import_test_moneo_module() -> None:
    """The test module should import cleanly."""
    import importlib

    mod = importlib.import_module("metabolon.organelles.tests.test_moneo")
    assert hasattr(mod, "test_parse_due_time_only")
