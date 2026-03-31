from __future__ import annotations

"""Tests for praxis — Praxis.md TODO list management."""

from unittest.mock import patch

import pytest


class TestParseDate:
    def test_valid_date(self):
        from metabolon.organelles.praxis import _parse_date
        from datetime import date
        result = _parse_date("2026-04-01")
        assert result == date(2026, 4, 1)

    def test_none(self):
        from metabolon.organelles.praxis import _parse_date
        assert _parse_date(None) is None

    def test_invalid(self):
        from metabolon.organelles.praxis import _parse_date
        assert _parse_date("not-a-date") is None

    def test_empty_string(self):
        from metabolon.organelles.praxis import _parse_date
        assert _parse_date("") is None


class TestIsOverdue:
    def test_past_date_is_overdue(self):
        from metabolon.organelles.praxis import _is_overdue
        from datetime import date
        item = {"due": "2026-01-01"}
        assert _is_overdue(item, date(2026, 3, 30)) is True

    def test_future_date_not_overdue(self):
        from metabolon.organelles.praxis import _is_overdue
        from datetime import date
        item = {"due": "2026-12-31"}
        assert _is_overdue(item, date(2026, 3, 30)) is False

    def test_no_due_date(self):
        from metabolon.organelles.praxis import _is_overdue
        from datetime import date
        assert _is_overdue({}, date(2026, 3, 30)) is False

    def test_today_not_overdue(self):
        from metabolon.organelles.praxis import _is_overdue
        from datetime import date
        item = {"due": "2026-03-30"}
        assert _is_overdue(item, date(2026, 3, 30)) is False
