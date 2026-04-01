from __future__ import annotations

"""Tests for metabolon.organelles.moneo — pure helpers, accessors, DB ops,
snapshot logic, resolve_target, schedule expansion, and side-effect functions
(mocked)."""

import gzip
import json
from datetime import UTC, date, datetime, time as dt_time, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

import metabolon.organelles.moneo as m

HKT = ZoneInfo("Asia/Hong_Kong")


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _ts(year: int, month: int, day: int, hour: int = 9, minute: int = 0) -> int:
    """Convenience: build a unix timestamp in HKT."""
    return int(datetime(year, month, day, hour, minute, tzinfo=HKT).timestamp())


def _reminder(title: str, due_ts: int, *, uuid: str = "abc12345", **kw: object) -> dict:
    return {"n": title, "d": due_ts, "u": uuid, **kw}


def _db(reminders: list[dict] | None = None, **kw: object) -> dict:
    data: dict = {"re": reminders or [], **kw}
    return data


# ---------------------------------------------------------------------------
# fatal, home_dir, path helpers
# ---------------------------------------------------------------------------

class TestFatal:
    def test_raises_moneo_error(self):
        with pytest.raises(m.MoneoError, match="boom"):
            m.fatal("boom")


class TestHomeDir:
    def test_uses_home_env(self):
        with patch.dict(m.os.environ, {"HOME": "/tmp/testhome"}):
            assert m.home_dir() == Path("/tmp/testhome")

    def test_missing_home_raises(self):
        with patch.dict(m.os.environ, {}, clear=True):
            with pytest.raises(m.MoneoError, match="HOME"):
                m.home_dir()


class TestPaths:
    def test_snapshot_path(self):
        with patch.dict(m.os.environ, {"HOME": "/home/user"}):
            assert m.snapshot_path() == Path("/home/user/officina/backups/due-reminders.json")

    def test_log_path(self):
        with patch.dict(m.os.environ, {"HOME": "/home/user"}):
            assert m.log_path() == Path("/home/user/tmp/due-snapshot.log")


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

class TestHktNow:
    def test_returns_hkt_datetime(self):
        result = m.hkt_now()
        assert isinstance(result, datetime)
        assert result.tzinfo is not None


class TestNowTs:
    def test_returns_positive_int(self):
        assert isinstance(m.now_ts(), int)
        assert m.now_ts() > 0


class TestHktFromTs:
    def test_roundtrip(self):
        dt = datetime(2026, 6, 15, 14, 30, tzinfo=HKT)
        ts = int(dt.timestamp())
        result = m.hkt_from_ts(ts)
        assert result.year == 2026
        assert result.month == 6
        assert result.hour == 14
        assert result.minute == 30

    def test_custom_timezone(self):
        ts = int(datetime(2026, 1, 1, 12, 0, tzinfo=UTC).timestamp())
        result = m.hkt_from_ts(ts, "Asia/Tokyo")
        assert result.hour == 21


# ---------------------------------------------------------------------------
# resolve_local_timestamp, parse_time
# ---------------------------------------------------------------------------

class TestResolveLocalTimestamp:
    def test_default_time_is_9am(self):
        ts = m.resolve_local_timestamp(date(2026, 3, 15), None, "Asia/Hong_Kong")
        dt = datetime.fromtimestamp(ts, tz=HKT)
        assert dt.hour == 9
        assert dt.date() == date(2026, 3, 15)

    def test_specific_time(self):
        ts = m.resolve_local_timestamp(date(2026, 3, 15), "14:30", "Asia/Hong_Kong")
        dt = datetime.fromtimestamp(ts, tz=HKT)
        assert dt.hour == 14
        assert dt.minute == 30


class TestParseTime:
    def test_relative(self):
        now = datetime(2026, 5, 10, 14, 0, tzinfo=HKT)
        ts = m.parse_time("30m", None, None, now=now)
        result = datetime.fromtimestamp(ts, tz=HKT)
        assert result.hour == 14
        assert result.minute == 30

    def test_date_value(self):
        ts = m.parse_time(None, None, "2026-06-01", timezone="Asia/Hong_Kong")
        dt = datetime.fromtimestamp(ts, tz=HKT)
        assert dt.date() == date(2026, 6, 1)
        assert dt.hour == 9  # default

    def test_at_only(self):
        now = datetime(2026, 5, 10, 8, 0, tzinfo=HKT)
        ts = m.parse_time(None, "15:30", None, now=now)
        result = datetime.fromtimestamp(ts, tz=HKT)
        assert result.hour == 15
        assert result.minute == 30

    def test_none_returns_none(self):
        now = datetime(2026, 5, 10, 8, 0, tzinfo=HKT)
        assert m.parse_time(None, None, None, now=now) is None


# ---------------------------------------------------------------------------
# fmt_ts
# ---------------------------------------------------------------------------

class TestFmtTs:
    @patch.object(m, "hkt_now")
    def test_today(self, mock_now):
        mock_now.return_value = datetime(2026, 6, 15, 10, 0, tzinfo=HKT)
        ts = _ts(2026, 6, 15, 14, 30)
        assert m.fmt_ts(ts) == "today 14:30"

    @patch.object(m, "hkt_now")
    def test_tomorrow(self, mock_now):
        mock_now.return_value = datetime(2026, 6, 15, 10, 0, tzinfo=HKT)
        ts = _ts(2026, 6, 16, 9, 0)
        assert m.fmt_ts(ts) == "tomorrow 09:00"

    @patch.object(m, "hkt_now")
    def test_other_date(self, mock_now):
        mock_now.return_value = datetime(2026, 6, 15, 10, 0, tzinfo=HKT)
        ts = _ts(2026, 7, 20, 10, 0)
        result = m.fmt_ts(ts)
        assert "Jul" in result


# ---------------------------------------------------------------------------
# Accessors: reminder_due_ts, reminder_title, reminder_uuid
# ---------------------------------------------------------------------------

class TestAccessors:
    def test_reminder_due_ts(self):
        assert m.reminder_due_ts({"d": 12345}) == 12345
        assert m.reminder_due_ts({}) is None
        assert m.reminder_due_ts({"d": "bad"}) is None

    def test_reminder_title(self):
        assert m.reminder_title({"n": "Hello"}) == "Hello"
        assert m.reminder_title({}) == ""
        assert m.reminder_title({"n": 42}) == ""

    def test_reminder_uuid(self):
        assert m.reminder_uuid({"u": "abc"}) == "abc"
        assert m.reminder_uuid({}) is None
        assert m.reminder_uuid({"u": 123}) is None


# ---------------------------------------------------------------------------
# reminders_slice, reminders_mut, sorted_reminders
# ---------------------------------------------------------------------------

class TestRemindersSlice:
    def test_returns_list(self):
        data = _db([{"n": "x"}])
        assert m.reminders_slice(data) == [{"n": "x"}]

    def test_missing_key_returns_empty(self):
        assert m.reminders_slice({}) == []

    def test_non_list_returns_empty(self):
        assert m.reminders_slice({"re": "nope"}) == []


class TestRemindersMut:
    def test_returns_list_and_sets_default(self):
        data: dict = {}
        result = m.reminders_mut(data)
        assert result == []
        assert data["re"] == []

    def test_existing_list(self):
        data = _db([{"n": "a"}])
        result = m.reminders_mut(data)
        assert len(result) == 1

    def test_non_list_raises(self):
        with pytest.raises(m.MoneoError, match="not an array"):
            m.reminders_mut({"re": "bad"})


class TestSortedReminders:
    def test_sorts_by_due_ts(self):
        data = _db([_reminder("late", 200), _reminder("early", 100)])
        result = m.sorted_reminders(data)
        assert m.reminder_title(result[0]) == "early"

    def test_none_due_ts_goes_to_front(self):
        data = _db([_reminder("with_ts", 100), {"n": "no_ts", "u": "z"}])
        result = m.sorted_reminders(data)
        assert m.reminder_due_ts(result[0]) is None


# ---------------------------------------------------------------------------
# active_reminders (logbook cross-reference)
# ---------------------------------------------------------------------------

class TestActiveReminders:
    def test_no_logbook_returns_all(self):
        data = _db([_reminder("A", 100)])
        assert len(m.active_reminders(data)) == 1

    def test_excludes_completed_pair(self):
        r = _reminder("Meds", 100, uuid="u1")
        data = _db([r], lb=[{"n": "Meds", "d": 100}])
        assert m.active_reminders(data) == []

    def test_keeps_non_completed(self):
        r1 = _reminder("Meds", 100, uuid="u1")
        r2 = _reminder("Water", 200, uuid="u2")
        data = _db([r1, r2], lb=[{"n": "Meds", "d": 100}])
        active = m.active_reminders(data)
        assert len(active) == 1
        assert m.reminder_title(active[0]) == "Water"

    def test_title_only_logbook_match(self):
        r = _reminder("Task", 0, uuid="u1")  # no valid due_ts
        r.pop("d")  # remove 'd' so due_ts is None
        data = _db([r], lb=[{"n": "Task"}])  # lb has no "d" → title-only match
        assert m.active_reminders(data) == []


# ---------------------------------------------------------------------------
# Recur helpers
# ---------------------------------------------------------------------------

class TestRecurHelpers:
    @pytest.mark.parametrize("code,expected", [
        ("d", "daily"), ("w", "weekly"), ("m", "monthly"),
        ("q", "quarterly"), ("y", "yearly"),
    ])
    def test_recur_label(self, code, expected):
        assert m.recur_label(code) == expected

    def test_recur_label_unknown(self):
        assert m.recur_label("x") is None
        assert m.recur_label(None) is None
        assert m.recur_label("") is None

    def test_recur_code(self):
        assert m.recur_code("daily") == "d"
        assert m.recur_code("weekly") == "w"
        assert m.recur_code("monthly") == "m"
        assert m.recur_code("quarterly") == "q"
        assert m.recur_code("yearly") == "y"
        assert m.recur_code("hourly") is None

    def test_recur_unit(self):
        assert m.recur_unit("daily") == 16
        assert m.recur_unit("weekly") == 256
        assert m.recur_unit("monthly") == 8
        assert m.recur_unit("quarterly") == 8
        assert m.recur_unit("yearly") == 4
        assert m.recur_unit("hourly") is None

    def test_recur_freq(self):
        assert m.recur_freq("daily") == 1
        assert m.recur_freq("quarterly") == 3
        assert m.recur_freq("hourly") is None


# ---------------------------------------------------------------------------
# generate_uuid
# ---------------------------------------------------------------------------

class TestGenerateUuid:
    def test_returns_string(self):
        uid = m.generate_uuid()
        assert isinstance(uid, str)
        assert len(uid) > 0

    def test_unique(self):
        assert m.generate_uuid() != m.generate_uuid()


# ---------------------------------------------------------------------------
# make_reminder
# ---------------------------------------------------------------------------

class TestMakeReminder:
    @patch.object(m, "now_ts", return_value=9999)
    @patch.object(m, "generate_uuid", return_value="uuid-fixed-value")
    def test_basic_no_recur(self, mock_uid, mock_ts):
        r = m.make_reminder("Test", 5000, None, None)
        assert r["n"] == "Test"
        assert r["d"] == 5000
        assert r["u"] == "uuid-fixed-value"
        assert r["b"] == 9999
        assert r["si"] == 5 * 60  # default autosnooze

    @patch.object(m, "now_ts", return_value=9999)
    @patch.object(m, "generate_uuid", return_value="uuid-fixed-value")
    def test_custom_autosnooze(self, mock_uid, mock_ts):
        r = m.make_reminder("Test", 5000, None, 15)
        assert r["si"] == 15 * 60

    @patch.object(m, "now_ts", return_value=9999)
    @patch.object(m, "generate_uuid", return_value="uuid-fixed-value")
    def test_monthly_recur(self, mock_uid, mock_ts):
        ts = _ts(2026, 3, 20, 10, 0)
        r = m.make_reminder("Monthly", ts, "monthly", None)
        assert r["rf"] == "m"
        assert r["rd"] == ts
        assert r["rn"] == 8

    @patch.object(m, "now_ts", return_value=9999)
    @patch.object(m, "generate_uuid", return_value="uuid-fixed-value")
    def test_quarterly_recur(self, mock_uid, mock_ts):
        ts = _ts(2026, 3, 20, 10, 0)
        r = m.make_reminder("Quarterly", ts, "quarterly", None)
        assert r["rf"] == "q"
        assert r["ru"] == {"i": 3}

    @patch.object(m, "now_ts", return_value=9999)
    @patch.object(m, "generate_uuid", return_value="uuid-fixed-value")
    def test_weekly_recur_sets_weekday(self, mock_uid, mock_ts):
        # 2026-03-20 is a Friday (weekday 4)
        ts = _ts(2026, 3, 20, 10, 0)
        r = m.make_reminder("Weekly", ts, "weekly", None)
        assert r["rf"] == "w"
        # weekday = ((4+1) % 7) + 1 = 6
        assert r["rb"] == 6


# ---------------------------------------------------------------------------
# find_duplicate
# ---------------------------------------------------------------------------

class TestFindDuplicate:
    def test_finds_duplicate_same_day_hour_minute(self):
        ts = _ts(2026, 3, 20, 10, 0)
        data = _db([_reminder("Meds", ts)])
        assert m.find_duplicate("Meds", ts, data) is not None

    def test_different_title_no_duplicate(self):
        ts = _ts(2026, 3, 20, 10, 0)
        data = _db([_reminder("Meds", ts)])
        assert m.find_duplicate("Water", ts, data) is None

    def test_different_time_no_duplicate(self):
        ts10 = _ts(2026, 3, 20, 10, 0)
        ts14 = _ts(2026, 3, 20, 14, 0)
        data = _db([_reminder("Meds", ts10)])
        assert m.find_duplicate("Meds", ts14, data) is None

    def test_empty_db_returns_none(self):
        ts = _ts(2026, 3, 20, 10, 0)
        assert m.find_duplicate("Anything", ts, _db()) is None


# ---------------------------------------------------------------------------
# make_snapshot, comparable_snapshot
# ---------------------------------------------------------------------------

class TestSnapshots:
    @patch.object(m, "hkt_now")
    def test_make_snapshot(self, mock_now):
        mock_now.return_value = datetime(2026, 6, 15, 10, 0, tzinfo=HKT)
        ts = _ts(2026, 6, 15, 14, 30)
        data = _db([_reminder("Test", ts, rf="d")])
        snap = m.make_snapshot(data)
        assert len(snap) == 1
        assert snap[0]["title"] == "Test"
        assert snap[0]["due_ts"] == ts
        assert snap[0]["recur"] == "daily"
        assert snap[0]["due"] == "today 14:30"

    def test_comparable_snapshot(self):
        data = _db([_reminder("A", 100)])
        result = m.comparable_snapshot(data)
        assert len(result) == 1
        assert result[0]["title"] == "A"
        assert result[0]["due"] == 100


# ---------------------------------------------------------------------------
# git_snapshot (mocked subprocess + filesystem)
# ---------------------------------------------------------------------------

class TestGitSnapshot:
    @patch.object(m.subprocess, "run")
    def test_writes_json_and_commits(self, mock_run):
        with patch.dict(m.os.environ, {"HOME": "/tmp/gittest"}):
            data = _db([_reminder("R1", 100)])
            m.git_snapshot(data)
            # Should have called git add and git commit
            assert mock_run.call_count == 2
            add_call = mock_run.call_args_list[0]
            commit_call = mock_run.call_args_list[1]
            assert "add" in add_call[0][0]
            assert "commit" in commit_call[0][0]


# ---------------------------------------------------------------------------
# read_db
# ---------------------------------------------------------------------------

class TestReadDb:
    @patch.object(m, "due_db_path")
    def test_reads_gzipped_json(self, mock_path, tmp_path):
        db_file = tmp_path / "Due.duedb"
        content = json.dumps({"re": [{"n": "Test"}]})
        with gzip.open(db_file, "wt", encoding="utf-8") as f:
            f.write(content)
        mock_path.return_value = db_file
        result = m.read_db()
        assert result["re"] == [{"n": "Test"}]

    @patch.object(m, "due_db_path")
    def test_permission_error_returns_empty(self, mock_path):
        mock_path.return_value = Path("/nonexistent/Due.duedb")
        with patch("gzip.open", side_effect=PermissionError("nope")):
            assert m.read_db() == {}

    @patch.object(m, "due_db_path")
    def test_file_not_found_raises(self, mock_path):
        mock_path.return_value = Path("/nonexistent/Due.duedb")
        with pytest.raises(m.MoneoError, match="Failed to read"):
            m.read_db()

    @patch.object(m, "due_db_path")
    def test_json_decode_error_raises(self, mock_path, tmp_path):
        db_file = tmp_path / "Due.duedb"
        with gzip.open(db_file, "wt", encoding="utf-8") as f:
            f.write("not json{{{")
        mock_path.return_value = db_file
        with pytest.raises(m.MoneoError, match="Failed to parse"):
            m.read_db()


# ---------------------------------------------------------------------------
# due_pid, run_best_effort
# ---------------------------------------------------------------------------

class TestDuePid:
    @patch.object(m.subprocess, "run")
    def test_found(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="12345\n")
        assert m.due_pid() == "12345"

    @patch.object(m.subprocess, "run")
    def test_not_found(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert m.due_pid() is None

    @patch.object(m.subprocess, "run")
    def test_empty_stdout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="\n")
        assert m.due_pid() is None


class TestRunBestEffort:
    @patch.object(m.subprocess, "run")
    def test_calls_subprocess(self, mock_run):
        m.run_best_effort("echo", "hello")
        mock_run.assert_called_once()
        assert mock_run.call_args[0][0] == ["echo", "hello"]


# ---------------------------------------------------------------------------
# write_db (heavily mocked)
# ---------------------------------------------------------------------------

class TestWriteDb:
    @patch.object(m, "git_snapshot")
    @patch.object(m, "due_pid", return_value=None)
    @patch.object(m, "due_db_path")
    def test_writes_and_snapshots(self, mock_path, mock_pid, mock_git, tmp_path):
        db_file = tmp_path / "Due.duedb"
        db_file.write_bytes(b"old")
        mock_path.return_value = db_file

        data = {"re": [], "mt": {"ts": 0}}
        with patch.object(m, "now_ts", return_value=5555555):
            m.write_db(data)

        # mt.ts should be updated
        assert data["mt"]["ts"] == 5555555
        # File should now contain gzipped JSON
        with gzip.open(db_file, "rt", encoding="utf-8") as f:
            written = json.load(f)
        assert written["re"] == []
        mock_git.assert_called_once_with(data)

    @patch.object(m, "due_db_path")
    def test_backup_failure_raises(self, mock_path, tmp_path):
        db_file = tmp_path / "Due.duedb"
        mock_path.return_value = db_file
        # db_file doesn't exist → read_bytes will fail
        data = {"re": []}
        with pytest.raises(m.MoneoError, match="Failed to back up"):
            m.write_db(data)


# ---------------------------------------------------------------------------
# set_tombstone
# ---------------------------------------------------------------------------

class TestSetTombstone:
    def test_sets_dl(self):
        data: dict = {}
        m.set_tombstone(data, "uuid1", 9999)
        assert data["dl"]["uuid1"] == 9999

    def test_existing_dl(self):
        data = {"dl": {"old": 1}}
        m.set_tombstone(data, "new", 2)
        assert data["dl"]["new"] == 2
        assert data["dl"]["old"] == 1

    def test_dl_not_dict_raises(self):
        with pytest.raises(m.MoneoError, match="not an object"):
            m.set_tombstone({"dl": [1, 2]}, "uuid", 1)


# ---------------------------------------------------------------------------
# get_reminder
# ---------------------------------------------------------------------------

class TestGetReminder:
    def test_valid_index(self):
        r = _reminder("First", 100, uuid="uid1")
        data = _db([r])
        raw_idx, result = m.get_reminder(data, 1)
        assert raw_idx == 0
        assert m.reminder_title(result) == "First"

    def test_out_of_range_raises(self):
        with pytest.raises(m.MoneoError, match="no reminder at index"):
            m.get_reminder(_db([]), 1)

    def test_zero_raises(self):
        with pytest.raises(m.MoneoError, match="no reminder at index"):
            m.get_reminder(_db([_reminder("A", 1)]), 0)

    def test_missing_uuid_raises(self):
        data = _db([{"n": "NoUUID", "d": 100}])
        with pytest.raises(m.MoneoError, match="missing UUID"):
            m.get_reminder(data, 1)


# ---------------------------------------------------------------------------
# short_uuid, is_uuid_prefix, is_numeric
# ---------------------------------------------------------------------------

class TestShortUuid:
    def test_normal(self):
        assert m.short_uuid("abcdefghijklmnop") == "abcdefgh"

    def test_none(self):
        assert m.short_uuid(None) == "--------"

    def test_short_string(self):
        assert m.short_uuid("abc") == "abc"


class TestIsUuidPrefix:
    def test_valid(self):
        assert m.is_uuid_prefix("abc123") is True

    def test_too_short(self):
        assert m.is_uuid_prefix("abc") is False

    def test_too_long(self):
        assert m.is_uuid_prefix("a" * 23) is False

    def test_invalid_chars(self):
        assert m.is_uuid_prefix("abc@#$!") is False


class TestIsNumeric:
    def test_positive(self):
        assert m.is_numeric("5") is True
        assert m.is_numeric("100") is True

    def test_zero(self):
        assert m.is_numeric("0") is False

    def test_negative(self):
        assert m.is_numeric("-1") is False

    def test_non_number(self):
        assert m.is_numeric("abc") is False


# ---------------------------------------------------------------------------
# find_by_uuid_prefix
# ---------------------------------------------------------------------------

class TestFindByUuidPrefix:
    def test_finds_match(self):
        r = _reminder("A", 100, uuid="abcdef1234")
        data = _db([r])
        result = m.find_by_uuid_prefix(data, "abcdef")
        assert len(result) == 1

    def test_no_match(self):
        data = _db([_reminder("A", 100, uuid="xyz")])
        assert m.find_by_uuid_prefix(data, "abc") == []


# ---------------------------------------------------------------------------
# confirm_action
# ---------------------------------------------------------------------------

class TestConfirmAction:
    def test_yes(self):
        reminder = _reminder("Test", 100)
        with patch("builtins.input", return_value="y"):
            assert m.confirm_action(reminder, "Delete") is True

    def test_no(self):
        reminder = _reminder("Test", 100)
        with patch("builtins.input", return_value="n"):
            assert m.confirm_action(reminder, "Delete") is False

    def test_eof_returns_false(self):
        reminder = _reminder("Test", 100)
        with patch("builtins.input", side_effect=EOFError):
            assert m.confirm_action(reminder, "Delete") is False


# ---------------------------------------------------------------------------
# resolve_target
# ---------------------------------------------------------------------------

class TestResolveTarget:
    def _db_with(self, reminders):
        return _db(reminders)

    def test_numeric_index(self):
        r = _reminder("Item", 100, uuid="uid1")
        data = self._db_with([r])
        matches, needs_confirm = m.resolve_target(data, "1")
        assert len(matches) == 1
        assert needs_confirm is True
        assert m.reminder_title(matches[0][1]) == "Item"

    def test_uuid_prefix(self):
        r = _reminder("Item", 100, uuid="abcdef123456")
        data = self._db_with([r])
        matches, needs_confirm = m.resolve_target(data, "abcdef")
        assert len(matches) == 1
        assert needs_confirm is False

    def test_pattern_match(self):
        r = _reminder("Buy milk", 100, uuid="uid1")
        data = self._db_with([r])
        matches, needs_confirm = m.resolve_target(data, "milk", allow_pattern=True)
        assert len(matches) == 1
        assert needs_confirm is False

    def test_no_match_raises(self):
        data = self._db_with([_reminder("A", 100, uuid="uid1")])
        with pytest.raises(m.MoneoError, match="No reminders"):
            m.resolve_target(data, "xyz999")

    def test_uuid_prefix_no_match_raises(self):
        data = self._db_with([_reminder("A", 100, uuid="uid1")])
        with pytest.raises(m.MoneoError, match="UUID starting"):
            m.resolve_target(data, "zzzzzz")


# ---------------------------------------------------------------------------
# add_direct
# ---------------------------------------------------------------------------

class TestAddDirect:
    @patch.object(m, "now_ts", return_value=100)
    @patch.object(m, "generate_uuid", return_value="new-uuid")
    def test_appends_and_returns_uuid(self, mock_uid, mock_ts):
        data = _db()
        uid = m.add_direct("Task", 5000, None, None)
        assert uid == "new-uuid"
        assert len(data["re"]) == 1
        assert data["re"][0]["n"] == "Task"


# ---------------------------------------------------------------------------
# expand_schedule
# ---------------------------------------------------------------------------

class TestExpandSchedule:
    def test_basic_expansion(self):
        base = _ts(2026, 3, 16, 9, 0)
        result = m.expand_schedule(base, timedelta(hours=8), "2026-03-16")
        assert len(result) >= 2
        hours = [datetime.fromtimestamp(ts, tz=HKT).hour for ts in result]
        assert 9 in hours
        assert 17 in hours

    def test_skip_night(self):
        base = _ts(2026, 3, 16, 22, 0)
        result = m.expand_schedule(base, timedelta(hours=1), "2026-03-17",
                                   skip_night=True)
        hours = [datetime.fromtimestamp(ts, tz=HKT).hour for ts in result]
        assert all(7 <= h < 23 for h in hours)

    def test_no_skip_night(self):
        base = _ts(2026, 3, 16, 22, 0)
        result = m.expand_schedule(base, timedelta(hours=1), "2026-03-17",
                                   skip_night=False)
        hours = [datetime.fromtimestamp(ts, tz=HKT).hour for ts in result]
        assert any(h >= 23 or h < 7 for h in hours)


# ---------------------------------------------------------------------------
# ensure_no_duplicates
# ---------------------------------------------------------------------------

class TestEnsureNoDuplicates:
    def test_no_duplicates_passes(self):
        ts = _ts(2026, 3, 20, 10, 0)
        data = _db()
        m.ensure_no_duplicates("New", [ts], data)  # should not raise

    def test_duplicate_raises(self):
        ts = _ts(2026, 3, 20, 10, 0)
        data = _db([_reminder("Existing", ts)])
        with pytest.raises(m.MoneoError, match="Duplicate"):
            m.ensure_no_duplicates("Existing", [ts], data)


# ---------------------------------------------------------------------------
# ChangeSet dataclass
# ---------------------------------------------------------------------------

class TestChangeSet:
    def test_fields(self):
        cs = m.ChangeSet(title="T", due_ts=100, changed=["n"], recur="daily")
        assert cs.title == "T"
        assert cs.due_ts == 100
        assert cs.changed == ["n"]
        assert cs.recur == "daily"

    def test_frozen(self):
        cs = m.ChangeSet(title="T", due_ts=100, changed=[], recur=None)
        with pytest.raises(AttributeError):
            cs.title = "new"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_valid_autosnooze(self):
        assert m.VALID_AUTOSNOOZE == {1, 5, 10, 15, 30, 60}

    def test_recur_choices(self):
        assert m.RECUR_CHOICES == {"daily", "weekly", "monthly", "quarterly", "yearly"}
