from __future__ import annotations

"""Tests for pacemaker — reminder signaling organelle."""

from unittest.mock import patch

import pytest

from metabolon.organelles.moneo import MoneoError


class TestAdd:
    def test_rejects_due_with_at(self):
        from metabolon.organelles.pacemaker import add

        with pytest.raises(MoneoError, match="cannot be combined"):
            add("test", due="today 10:00", at="10:00")

    def test_rejects_due_with_date(self):
        from metabolon.organelles.pacemaker import add

        with pytest.raises(MoneoError, match="cannot be combined"):
            add("test", due="today 10:00", date="2026-04-01")

    def test_rejects_invalid_recur(self):
        import metabolon.organelles.moneo as m
        from metabolon.organelles.pacemaker import add

        with (
            patch.object(m, "parse_time", return_value=1000),
            patch.object(m, "read_db", return_value={}),
            patch.object(m, "find_duplicate", return_value=None),
        ):
            with pytest.raises(MoneoError, match="Invalid"):
                add("test", rel="30m", recur="biweekly")

    def test_rejects_invalid_autosnooze(self):
        import metabolon.organelles.moneo as m
        from metabolon.organelles.pacemaker import add

        with (
            patch.object(m, "parse_time", return_value=1000),
            patch.object(m, "read_db", return_value={}),
            patch.object(m, "find_duplicate", return_value=None),
        ):
            with pytest.raises(MoneoError, match="autosnooze"):
                add("test", rel="30m", autosnooze=99)

    def test_successful_add(self):
        import metabolon.organelles.moneo as m
        from metabolon.organelles.pacemaker import add

        with (
            patch.object(m, "parse_time", return_value=1711785600),
            patch.object(m, "read_db", return_value={}),
            patch.object(m, "find_duplicate", return_value=None),
            patch.object(m, "add_direct"),
            patch.object(m, "write_db"),
            patch.object(m, "fmt_ts", return_value="2026-03-30 10:00"),
        ):
            result = add("Test Reminder", rel="30m")
        assert "Added" in result
        assert "Test Reminder" in result
