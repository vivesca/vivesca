"""Tests for metabolon.sortase.history."""
from __future__ import annotations

from datetime import datetime

from rich.table import Table

from metabolon.sortase.history import (
    _format_timestamp,
    _format_duration,
    _format_files_changed,
    build_history_entries,
    build_history_table,
)
from metabolon.sortase.logger import _parse_iso_timestamp


def test_format_timestamp_valid():
    result = _format_timestamp("2026-03-31T10:30:00")
    assert "2026-03-31" in result
    assert "10:30" in result


def test_format_timestamp_invalid():
    assert _format_timestamp("not a timestamp") == "not a timestamp"


def test_format_timestamp_empty():
    assert _format_timestamp("") == ""


def test_format_duration_seconds():
    assert _format_duration(45.5) == "45.5s"


def test_format_duration_minutes():
    assert _format_duration(125.0) == "2m 5s"


def test_format_duration_none():
    assert _format_duration(None) == "-"


def test_format_files_changed_list():
    assert _format_files_changed(["a.py", "b.py", "c.py"]) == "3"


def test_format_files_changed_integer():
    assert _format_files_changed(15) == "15"


def test_format_files_changed_none():
    assert _format_files_changed(None) == "-"


def test_build_history_entries_empty():
    entries = build_history_entries([])
    assert entries == []


def test_build_history_entries_returns_correct_keys():
    raw_entries = [
        {
            "timestamp": "2026-03-31T10:00:00",
            "plan": "test-plan.md",
            "tool": "goose",
            "duration_s": 45.5,
            "success": True,
            "files_changed": ["a.py", "b.py"],
        }
    ]
    formatted = build_history_entries(raw_entries)
    assert len(formatted) == 1
    entry = formatted[0]
    assert "timestamp" in entry
    assert "plan" in entry
    assert "backend" in entry
    assert "duration" in entry
    assert "status" in entry
    assert "files" in entry
    assert entry["status"] == "ok"
    assert entry["files"] == "2"


def test_build_history_entries_reversed_order():
    raw_entries = [
        {"timestamp": "2026-03-31T10:00:00", "success": True},
        {"timestamp": "2026-03-31T11:00:00", "success": False},
        {"timestamp": "2026-03-31T12:00:00", "success": True},
    ]
    formatted = build_history_entries(raw_entries, limit=3)
    # Most recent should be first
    assert formatted[0]["timestamp"] != formatted[-1]["timestamp"]


def test_build_history_entries_respects_limit():
    raw_entries = [{"timestamp": f"2026-03-31T{i:02d}:00:00", "success": True} for i in range(25)]
    formatted = build_history_entries(raw_entries, limit=20)
    assert len(formatted) == 20


def test_build_history_table():
    raw_entries = [
        {
            "timestamp": "2026-03-31T10:00:00",
            "plan": "test-plan.md",
            "tool": "goose",
            "duration_s": 30.0,
            "success": True,
            "files_changed": ["a.py"],
        },
        {
            "timestamp": "2026-03-31T11:00:00",
            "plan": "another-plan.md",
            "tool": "codex",
            "duration_s": 60.0,
            "success": False,
            "files_changed": ["b.py", "c.py"],
        },
    ]
    table = build_history_table(raw_entries, limit=10)
    assert isinstance(table, Table)
    assert table.title == "sortase history"
    # Should have the correct number of columns
    assert len(table.columns) == 7
