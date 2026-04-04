from __future__ import annotations

"""Tests for metabolon.organelles.pacemaker — reminder signaling organelle."""

from unittest.mock import MagicMock, patch

import pytest

import metabolon.organelles.moneo as _m
import metabolon.organelles.pacemaker as pacemaker

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _make_reminder(
    title: str = "Remind me",
    uuid: str = "abc12345-6789-efab-cdef-0123456789ab",
    due_ts: int = 1711785600,
    rf: str | None = None,
) -> dict:
    return {"n": title, "u": uuid, "d": due_ts, **({"rf": rf} if rf else {})}


def _db(*reminders: dict) -> dict:
    return {"r": list(reminders), "lb": []}


# ===========================================================================
# add()
# ===========================================================================


class TestAdd:
    """Tests for pacemaker.add()."""

    def test_rejects_due_combined_with_at(self):
        with pytest.raises(_m.MoneoError, match="cannot be combined"):
            pacemaker.add("test", due="today 10:00", at="10:00")

    def test_rejects_due_combined_with_date(self):
        with pytest.raises(_m.MoneoError, match="cannot be combined"):
            pacemaker.add("test", due="today 10:00", date="2026-04-01")

    def test_rejects_no_time_specified(self):
        """parse_time returns None → MoneoError."""
        with patch.object(_m, "parse_time", return_value=None):
            with pytest.raises(_m.MoneoError, match="Specify a time"):
                pacemaker.add("test")

    def test_rejects_invalid_recur(self):
        with (
            patch.object(_m, "parse_time", return_value=1000),
            patch.object(_m, "read_db", return_value={}),
            patch.object(_m, "find_duplicate", return_value=None),
        ):
            with pytest.raises(_m.MoneoError, match="Invalid --recur"):
                pacemaker.add("test", rel="30m", recur="biweekly")

    def test_rejects_invalid_autosnooze(self):
        with (
            patch.object(_m, "parse_time", return_value=1000),
            patch.object(_m, "read_db", return_value={}),
            patch.object(_m, "find_duplicate", return_value=None),
        ):
            with pytest.raises(_m.MoneoError, match="autosnooze"):
                pacemaker.add("test", rel="30m", autosnooze=99)

    def test_rejects_duplicate(self):
        dup = _make_reminder("test")
        with (
            patch.object(_m, "parse_time", return_value=1000),
            patch.object(_m, "read_db", return_value={}),
            patch.object(_m, "find_duplicate", return_value=dup),
            patch.object(_m, "reminder_due_ts", return_value=1000),
            patch.object(_m, "fmt_ts", return_value="2026-04-01 10:00"),
        ):
            with pytest.raises(_m.MoneoError, match="Duplicate"):
                pacemaker.add("test", rel="30m")

    def test_successful_add_with_rel(self):
        with (
            patch.object(_m, "parse_time", return_value=1711785600),
            patch.object(_m, "read_db", return_value={}),
            patch.object(_m, "find_duplicate", return_value=None),
            patch.object(_m, "add_direct") as mock_add,
            patch.object(_m, "write_db") as mock_write,
            patch.object(_m, "fmt_ts", return_value="2026-03-30 10:00"),
        ):
            result = pacemaker.add("Test Reminder", rel="30m")
        assert "Added" in result
        assert "Test Reminder" in result
        mock_add.assert_called_once()
        mock_write.assert_called_once()

    def test_successful_add_with_due(self):
        """'due' triggers parse_due_string, then parse_time."""
        with (
            patch.object(_m, "parse_due_string", return_value=("10:00", "2026-04-01")),
            patch.object(_m, "parse_time", return_value=1711785600),
            patch.object(_m, "read_db", return_value={}),
            patch.object(_m, "find_duplicate", return_value=None),
            patch.object(_m, "add_direct"),
            patch.object(_m, "write_db"),
            patch.object(_m, "fmt_ts", return_value="2026-04-01 10:00"),
        ):
            result = pacemaker.add("Due Reminder", due="2026-04-01 10:00")
        assert "Added" in result
        assert "Due Reminder" in result

    def test_successful_add_with_recur(self):
        with (
            patch.object(_m, "parse_time", return_value=1711785600),
            patch.object(_m, "read_db", return_value={}),
            patch.object(_m, "find_duplicate", return_value=None),
            patch.object(_m, "add_direct"),
            patch.object(_m, "write_db"),
            patch.object(_m, "fmt_ts", return_value="2026-04-01 10:00"),
        ):
            result = pacemaker.add("Weekly", rel="1h", recur="weekly")
        assert "repeats weekly" in result

    def test_successful_add_with_valid_autosnooze(self):
        with (
            patch.object(_m, "parse_time", return_value=1711785600),
            patch.object(_m, "read_db", return_value={}),
            patch.object(_m, "find_duplicate", return_value=None),
            patch.object(_m, "add_direct") as mock_add,
            patch.object(_m, "write_db"),
            patch.object(_m, "fmt_ts", return_value="2026-04-01 10:00"),
        ):
            pacemaker.add("Snoozer", rel="1h", autosnooze=15)
        # autosnooze=15 passed through to add_direct
        call_args = mock_add.call_args
        assert call_args[0][3] == 15  # 4th positional = autosnooze


# ===========================================================================
# ls()
# ===========================================================================


class TestLs:
    """Tests for pacemaker.ls()."""

    def test_empty_db(self):
        with (
            patch.object(_m, "read_db", return_value={"r": []}),
            patch.object(_m, "sorted_reminders", return_value=[]),
            patch.object(_m, "now_ts", return_value=1711785600),
        ):
            result = pacemaker.ls()
        assert result == []

    def test_returns_correct_fields(self):
        rem = _make_reminder("Buy milk", due_ts=1711790000)
        with (
            patch.object(_m, "read_db", return_value=_db(rem)),
            patch.object(_m, "sorted_reminders", return_value=[rem]),
            patch.object(_m, "now_ts", return_value=1711785600),
            patch.object(_m, "reminder_uuid", return_value=rem["u"]),
            patch.object(_m, "short_uuid", return_value="abc12345"),
            patch.object(_m, "reminder_title", return_value="Buy milk"),
            patch.object(_m, "reminder_due_ts", return_value=1711790000),
            patch.object(_m, "fmt_ts", return_value="2026-03-30 11:06"),
            patch.object(_m, "recur_label", return_value=None),
        ):
            result = pacemaker.ls()
        assert len(result) == 1
        entry = result[0]
        assert entry["index"] == 1
        assert entry["title"] == "Buy milk"
        assert entry["short_uuid"] == "abc12345"
        assert entry["due"] == "2026-03-30 11:06"
        assert entry["overdue"] is False

    def test_marks_overdue(self):
        rem = _make_reminder("Late", due_ts=1711780000)
        with (
            patch.object(_m, "read_db", return_value=_db(rem)),
            patch.object(_m, "sorted_reminders", return_value=[rem]),
            patch.object(_m, "now_ts", return_value=1711785600),
            patch.object(_m, "reminder_uuid", return_value=rem["u"]),
            patch.object(_m, "short_uuid", return_value="abc12345"),
            patch.object(_m, "reminder_title", return_value="Late"),
            patch.object(_m, "reminder_due_ts", return_value=1711780000),
            patch.object(_m, "fmt_ts", return_value="2026-03-30 09:46"),
            patch.object(_m, "recur_label", return_value=None),
        ):
            result = pacemaker.ls()
        assert result[0]["overdue"] is True

    def test_multiple_reminders_indexed(self):
        r1 = _make_reminder("First", uuid="a" * 8 + "-1111", due_ts=100)
        r2 = _make_reminder("Second", uuid="b" * 8 + "-2222", due_ts=200)
        with (
            patch.object(_m, "read_db", return_value=_db(r1, r2)),
            patch.object(_m, "sorted_reminders", return_value=[r1, r2]),
            patch.object(_m, "now_ts", return_value=300),
            patch.object(_m, "reminder_uuid", side_effect=[r1["u"], r2["u"]]),
            patch.object(_m, "short_uuid", side_effect=["aaaaaaaa", "bbbbbbbb"]),
            patch.object(_m, "reminder_title", side_effect=["First", "Second"]),
            patch.object(_m, "reminder_due_ts", side_effect=[100, 200]),
            patch.object(_m, "fmt_ts", side_effect=["t1", "t2"]),
            patch.object(_m, "recur_label", return_value=None),
        ):
            result = pacemaker.ls()
        assert result[0]["index"] == 1
        assert result[1]["index"] == 2

    def test_recur_label_included(self):
        rem = _make_reminder("Repeat", rf="weekly")
        with (
            patch.object(_m, "read_db", return_value=_db(rem)),
            patch.object(_m, "sorted_reminders", return_value=[rem]),
            patch.object(_m, "now_ts", return_value=999),
            patch.object(_m, "reminder_uuid", return_value=rem["u"]),
            patch.object(_m, "short_uuid", return_value="abc12345"),
            patch.object(_m, "reminder_title", return_value="Repeat"),
            patch.object(_m, "reminder_due_ts", return_value=500),
            patch.object(_m, "fmt_ts", return_value="some-time"),
            patch.object(_m, "recur_label", return_value="weekly"),
        ):
            result = pacemaker.ls()
        assert result[0]["recur"] == "weekly"


# ===========================================================================
# rm()
# ===========================================================================


class TestRm:
    """Tests for pacemaker.rm()."""

    def test_delete_single_by_uuid_prefix(self):
        rem = _make_reminder("Delete me")
        with (
            patch.object(_m, "read_db", return_value=_db(rem)),
            patch.object(_m, "resolve_target", return_value=([(0, rem)], [])),
            patch.object(_m, "now_ts", return_value=1711785600),
            patch.object(_m, "reminder_uuid", return_value=rem["u"]),
            patch.object(_m, "reminder_title", return_value="Delete me"),
            patch.object(_m, "short_uuid", return_value="abc12345"),
            patch.object(_m, "reminders_mut", return_value=[rem]),
            patch.object(_m, "set_tombstone"),
            patch.object(_m, "write_db") as mock_write,
        ):
            result = pacemaker.rm("abc1")
        assert "Deleted" in result
        assert "Delete me" in result
        mock_write.assert_called_once()

    def test_delete_multiple_matches(self):
        r1 = _make_reminder("A", uuid="aa111111-1111")
        r2 = _make_reminder("B", uuid="bb222222-2222")
        # reminder_uuid is called in outer loop + inner loop per match
        with (
            patch.object(_m, "read_db", return_value=_db(r1, r2)),
            patch.object(_m, "resolve_target", return_value=([(0, r1), (1, r2)], [])),
            patch.object(_m, "now_ts", return_value=1711785600),
            patch.object(_m, "reminder_uuid", side_effect=[r1["u"], r1["u"], r2["u"], r2["u"]]),
            patch.object(_m, "reminder_title", side_effect=["A", "B"]),
            patch.object(_m, "short_uuid", side_effect=["aa111111", "bb222222"]),
            patch.object(_m, "reminders_mut", return_value=[r1, r2]),
            patch.object(_m, "set_tombstone"),
            patch.object(_m, "write_db"),
        ):
            result = pacemaker.rm("pattern")
        assert "A" in result
        assert "B" in result

    def test_raises_on_missing_uuid(self):
        rem = {"n": "No UUID", "d": 100}  # no "u" key
        with (
            patch.object(_m, "read_db", return_value=_db(rem)),
            patch.object(_m, "resolve_target", return_value=([(0, rem)], [])),
            patch.object(_m, "now_ts", return_value=1711785600),
            patch.object(_m, "reminder_uuid", return_value=None),
            patch.object(_m, "reminder_title", return_value="No UUID"),
        ):
            with pytest.raises(_m.MoneoError, match="missing UUID"):
                pacemaker.rm("No")


# ===========================================================================
# edit()
# ===========================================================================


class TestEdit:
    """Tests for pacemaker.edit()."""

    def _change_set(self, title="New Title", due_ts=1711785600, changed=("title",), recur=None):
        cs = MagicMock()
        cs.title = title
        cs.due_ts = due_ts
        cs.changed = list(changed)
        cs.recur = recur
        return cs

    def test_successful_edit(self):
        rem = _make_reminder("Old Title")
        cs = self._change_set()
        raw_list = [rem]
        with (
            patch.object(_m, "read_db", return_value=_db(rem)),
            patch.object(_m, "resolve_target", return_value=([(0, rem)], [])),
            patch.object(_m, "reminder_uuid", return_value=rem["u"]),
            patch.object(_m, "short_uuid", return_value="abc12345"),
            patch.object(_m, "build_change_set", return_value=cs, create=True),
            patch.object(_m, "ensure_no_duplicates"),
            patch.object(_m, "reminders_mut", return_value=raw_list),
            patch.object(_m, "now_ts", return_value=1711785600),
            patch.object(_m, "set_tombstone"),
            patch.object(_m, "add_direct"),
            patch.object(_m, "write_db") as mock_write,
        ):
            result = pacemaker.edit("abc1", title="New Title")
        assert "Updated" in result
        assert "abc12345" in result
        mock_write.assert_called_once()

    def test_rejects_multiple_matches(self):
        r1 = _make_reminder("A", uuid="a1111111-1111")
        r2 = _make_reminder("B", uuid="b2222222-2222")
        with (
            patch.object(_m, "read_db", return_value=_db(r1, r2)),
            patch.object(_m, "resolve_target", return_value=([(0, r1), (1, r2)], [])),
            patch.object(_m, "reminder_uuid", side_effect=[r1["u"], r2["u"]]),
            patch.object(_m, "short_uuid", side_effect=["a1111111", "b2222222"]),
            patch.object(_m, "reminder_title", side_effect=["A", "B"]),
        ):
            with pytest.raises(_m.MoneoError, match="Multiple matches"):
                pacemaker.edit("ab", title="X")

    def test_rejects_missing_uuid(self):
        rem = {"n": "No UUID", "d": 100}
        with (
            patch.object(_m, "read_db", return_value=_db(rem)),
            patch.object(_m, "resolve_target", return_value=([(0, rem)], [])),
            patch.object(_m, "reminder_uuid", return_value=None),
            patch.object(_m, "reminder_title", return_value="No UUID"),
        ):
            with pytest.raises(_m.MoneoError, match="missing UUID"):
                pacemaker.edit("x", title="Y")


# ===========================================================================
# log()
# ===========================================================================


class TestLog:
    """Tests for pacemaker.log()."""

    def test_empty_logbook(self):
        with patch.object(_m, "read_db", return_value={"r": [], "lb": []}):
            result = pacemaker.log()
        assert result == []

    def test_returns_sorted_entries(self):
        entries = [
            {"n": "Old", "m": 1000},
            {"n": "New", "m": 2000},
        ]
        with (
            patch.object(_m, "read_db", return_value={"r": [], "lb": entries}),
            patch.object(_m, "hkt_from_ts") as mock_hkt,
        ):
            from datetime import datetime

            mock_hkt.side_effect = [
                datetime(2026, 4, 1, 10, 0),
                datetime(2026, 3, 30, 8, 0),
            ]
            result = pacemaker.log()
        # Sorted desc by m, so "New" (m=2000) first
        assert result[0]["title"] == "New"
        assert result[1]["title"] == "Old"

    def test_limits_to_n(self):
        entries = [{"n": f"Item {i}", "m": i} for i in range(50)]
        with patch.object(_m, "read_db", return_value={"r": [], "lb": entries}):
            result = pacemaker.log(n=5)
        assert len(result) == 5

    def test_filters_by_string(self):
        entries = [
            {"n": "Buy groceries", "m": 2000},
            {"n": "Call dentist", "m": 1500},
            {"n": "Buy flowers", "m": 1000},
        ]
        with (
            patch.object(_m, "read_db", return_value={"r": [], "lb": entries}),
            patch.object(_m, "hkt_from_ts") as mock_hkt,
        ):
            from datetime import datetime

            mock_hkt.side_effect = [
                datetime(2026, 4, 1, 10, 0),
                datetime(2026, 3, 30, 8, 0),
            ]
            result = pacemaker.log(filter_str="buy")
        assert len(result) == 2
        assert all("Buy" in e["title"] for e in result)

    def test_handles_zero_timestamp(self):
        entries = [{"n": "Empty ts", "m": 0}]
        with patch.object(_m, "read_db", return_value={"r": [], "lb": entries}):
            result = pacemaker.log()
        assert result[0]["completed_ts"] == 0
        assert result[0]["completed_hkt"] is None


# ===========================================================================
# snapshot()
# ===========================================================================


class TestSnapshot:
    """Tests for pacemaker.snapshot()."""

    def test_successful_snapshot(self):
        data = {"r": [_make_reminder()]}
        with (
            patch.object(_m, "read_db", return_value=data),
            patch.object(_m, "git_snapshot"),
            patch.object(_m, "reminders_slice", return_value=[_make_reminder()]),
        ):
            result = pacemaker.snapshot()
        assert "Snapshot committed" in result
        assert "1 reminders" in result

    def test_rejects_empty_db(self):
        with patch.object(_m, "read_db", return_value={}):
            with pytest.raises(_m.MoneoError, match="Could not read"):
                pacemaker.snapshot()

    def test_rejects_non_dict_db(self):
        with patch.object(_m, "read_db", return_value=None):
            with pytest.raises(_m.MoneoError, match="Could not read"):
                pacemaker.snapshot()


# ===========================================================================
# _cli()
# ===========================================================================


class TestCli:
    """Tests for pacemaker._cli()."""

    def test_delegates_to_moneo_main(self):
        with patch.object(_m, "main", return_value=0, create=True) as mock_main:
            result = pacemaker._cli(["list"])
        assert result == 0
        mock_main.assert_called_once_with(["list"])

    def test_passes_none_argv(self):
        with patch.object(_m, "main", return_value=0, create=True) as mock_main:
            pacemaker._cli()
        mock_main.assert_called_once_with(None)
