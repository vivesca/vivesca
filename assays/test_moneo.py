#!/usr/bin/env -S uv run --script --python 3.13
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Tests for moneo — Due app reminder manager."""

# Import moneo by path (no .py extension — must use SourceFileLoader explicitly)
import importlib.machinery
import importlib.util
import sys
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

_moneo_path = str(Path.home() / "bin/moneo")
_loader = importlib.machinery.SourceFileLoader("moneo", _moneo_path)
_spec = importlib.util.spec_from_loader("moneo", _loader)
moneo = importlib.util.module_from_spec(_spec)
sys.modules["moneo"] = moneo
_loader.exec_module(moneo)

HKT = ZoneInfo("Asia/Hong_Kong")


def _make_db(*reminders) -> dict:
    """Build a minimal Due DB dict with given reminder dicts."""
    return {"re": list(reminders), "dl": {}}


def _reminder(title: str, due_ts: int, recur: str | None = None, uuid: str = "test-uuid") -> dict:
    now = int(time.time())
    r = {"n": title, "d": due_ts, "b": now, "m": now, "si": 300, "u": uuid}
    if recur:
        r["rf"] = recur
        r["rd"] = due_ts
    return r


def _ts(year: int, month: int, day: int, hour: int, minute: int) -> int:
    return int(datetime(year, month, day, hour, minute, tzinfo=HKT).timestamp())


class TestParseTime(unittest.TestCase):
    def setUp(self):
        self.moneo = moneo

    def test_relative_minutes(self):
        before = int(time.time())
        ts = self.moneo._parse_time("30m", None, None)
        self.assertAlmostEqual(ts, before + 1800, delta=5)

    def test_relative_hours(self):
        before = int(time.time())
        ts = self.moneo._parse_time("2h", None, None)
        self.assertAlmostEqual(ts, before + 7200, delta=5)

    def test_at_today(self):
        ts = self.moneo._parse_time(None, "14:30", None)
        dt = datetime.fromtimestamp(ts, tz=HKT)
        self.assertEqual(dt.hour, 14)
        self.assertEqual(dt.minute, 30)

    def test_date_and_at(self):
        ts = self.moneo._parse_time(None, "09:00", "2026-03-15")
        dt = datetime.fromtimestamp(ts, tz=HKT)
        self.assertEqual(dt.date().isoformat(), "2026-03-15")
        self.assertEqual(dt.hour, 9)

    def test_date_only_defaults_to_9am(self):
        ts = self.moneo._parse_time(None, None, "2026-03-15")
        dt = datetime.fromtimestamp(ts, tz=HKT)
        self.assertEqual(dt.hour, 9)
        self.assertEqual(dt.minute, 0)

    def test_invalid_relative(self):
        with self.assertRaises(SystemExit):
            self.moneo._parse_time("30x", None, None)

    def test_invalid_at(self):
        with self.assertRaises(SystemExit):
            self.moneo._parse_time(None, "25:00", None)


class TestSortedReminders(unittest.TestCase):
    def setUp(self):
        self.moneo = moneo

    def test_sorted_by_due(self):
        r1 = _reminder("Late", _ts(2026, 3, 15, 10, 0), uuid="uuid1")
        r2 = _reminder("Early", _ts(2026, 3, 12, 9, 0), uuid="uuid2")
        r3 = _reminder("Middle", _ts(2026, 3, 13, 14, 0), uuid="uuid3")
        db = _make_db(r1, r2, r3)
        sorted_r = self.moneo._sorted_reminders(db)
        self.assertEqual([r["n"] for r in sorted_r], ["Early", "Middle", "Late"])

    def test_empty(self):
        self.assertEqual(self.moneo._sorted_reminders({"re": []}), [])


class TestFindDuplicate(unittest.TestCase):
    def setUp(self):
        self.moneo = moneo

    def test_same_title_same_time_is_duplicate(self):
        ts = _ts(2026, 3, 15, 13, 0)
        r = _reminder("Take medicine", ts, uuid="uuid1")
        with patch.object(self.moneo, "read_db", return_value=_make_db(r)):
            result = self.moneo._find_duplicate("Take medicine", ts)
        self.assertIsNotNone(result)

    def test_same_title_different_time_is_not_duplicate(self):
        """Regression: same title at 13:00 and 19:00 on same day must be allowed."""
        ts1 = _ts(2026, 3, 15, 13, 0)
        ts2 = _ts(2026, 3, 15, 19, 0)
        r = _reminder("Take medicine", ts1, uuid="uuid1")
        with patch.object(self.moneo, "read_db", return_value=_make_db(r)):
            result = self.moneo._find_duplicate("Take medicine", ts2)
        self.assertIsNone(result)

    def test_same_title_different_day_is_not_duplicate(self):
        ts1 = _ts(2026, 3, 15, 13, 0)
        ts2 = _ts(2026, 3, 16, 13, 0)
        r = _reminder("Take medicine", ts1, uuid="uuid1")
        with patch.object(self.moneo, "read_db", return_value=_make_db(r)):
            result = self.moneo._find_duplicate("Take medicine", ts2)
        self.assertIsNone(result)

    def test_case_insensitive(self):
        ts = _ts(2026, 3, 15, 13, 0)
        r = _reminder("take medicine", ts, uuid="uuid1")
        with patch.object(self.moneo, "read_db", return_value=_make_db(r)):
            result = self.moneo._find_duplicate("TAKE MEDICINE", ts)
        self.assertIsNotNone(result)


class TestRmByTitle(unittest.TestCase):
    def setUp(self):
        self.moneo = moneo

    def test_rm_by_title_deletes_matching(self):
        r1 = _reminder("Beaflu Plus", _ts(2026, 3, 15, 13, 0), uuid="uuid1")
        r2 = _reminder("Beaflu Plus", _ts(2026, 3, 15, 19, 0), uuid="uuid2")
        r3 = _reminder("AIA interview", _ts(2026, 3, 12, 9, 45), uuid="uuid3")
        db = _make_db(r1, r2, r3)

        written = {}
        with (
            patch.object(self.moneo, "read_db", return_value=db),
            patch.object(self.moneo, "write_db", side_effect=lambda d: written.update(d)),
            patch.object(self.moneo, "_git_snapshot"),
        ):
            args = MagicMock()
            args.title = "beaflu"
            args.index = None
            self.moneo.cmd_rm(args)

        remaining = [r["n"] for r in written.get("re", db["re"])]
        self.assertNotIn("Beaflu Plus", remaining)
        self.assertIn("AIA interview", remaining)

    def test_rm_by_title_no_match_exits(self):
        db = _make_db(_reminder("AIA interview", _ts(2026, 3, 12, 9, 45), uuid="uuid1"))
        with patch.object(self.moneo, "read_db", return_value=db):
            args = MagicMock()
            args.title = "nonexistent"
            args.index = None
            with self.assertRaises(SystemExit):
                self.moneo.cmd_rm(args)

    def test_rm_by_index_does_not_shift(self):
        """Regression: deleting by index should use UUID lookup, not positional pop after sort."""
        r1 = _reminder("First", _ts(2026, 3, 10, 9, 0), uuid="uuid1")
        r2 = _reminder("Second", _ts(2026, 3, 11, 9, 0), uuid="uuid2")
        r3 = _reminder("Third", _ts(2026, 3, 12, 9, 0), uuid="uuid3")
        db = _make_db(r3, r1, r2)  # intentionally unsorted in raw array

        written = {}
        with (
            patch.object(self.moneo, "read_db", return_value=db),
            patch.object(self.moneo, "write_db", side_effect=lambda d: written.update(d)),
            patch.object(self.moneo, "_git_snapshot"),
        ):
            args = MagicMock()
            args.title = None
            args.index = 1  # should delete "First" (soonest)
            self.moneo.cmd_rm(args)

        remaining = [r["n"] for r in written.get("re", db["re"])]
        self.assertNotIn("First", remaining)
        self.assertIn("Second", remaining)
        self.assertIn("Third", remaining)


if __name__ == "__main__":
    unittest.main(verbosity=2)
