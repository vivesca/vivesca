from __future__ import annotations

import ast
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from metabolon.sortase.history import (
    _format_duration,
    _format_files_changed,
    _format_timestamp,
    build_history_table,
    display_history,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_ENTRIES = [
    {
        "timestamp": "2026-03-30T14:00:00",
        "plan": "add_auth.md",
        "tool": "droid",
        "duration_s": 45.2,
        "success": True,
        "files_changed": 3,
    },
    {
        "timestamp": "2026-03-30T15:10:00",
        "plan": "fix_lint.md",
        "tool": "gemini",
        "duration_s": 120.0,
        "success": False,
        "files_changed": ["src/main.py", "tests/test_main.py"],
        "failure_reason": "tests",
    },
    {
        "timestamp": "2026-03-30T16:30:00",
        "plan": "refactor_api.md",
        "tool": "codex",
        "duration_s": 0,
        "success": True,
        "files_changed": 0,
    },
]

TWO_ENTRY_JSONL = "\n".join(json.dumps(e) for e in SAMPLE_ENTRIES[:2]) + "\n"


@pytest.fixture
def log_file(tmp_path: Path):
    p = tmp_path / "log.jsonl"
    p.write_text(TWO_ENTRY_JSONL, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# 1. _format_timestamp parses ISO or returns raw string
# ---------------------------------------------------------------------------

class TestFormatTimestamp:
    def test_valid_iso(self):
        result = _format_timestamp("2026-03-30T14:00:00")
        assert result == "2026-03-30 14:00"

    def test_invalid_string(self):
        assert _format_timestamp("not-a-date") == "not-a-date"

    def test_empty(self):
        assert _format_timestamp("") == ""


# ---------------------------------------------------------------------------
# 2. _format_duration handles seconds, minutes, and None
# ---------------------------------------------------------------------------

class TestFormatDuration:
    def test_seconds_only(self):
        assert _format_duration(45.2) == "45.2s"

    def test_minutes_and_seconds(self):
        assert _format_duration(125) == "2m 5s"

    def test_none(self):
        assert _format_duration(None) == "-"


# ---------------------------------------------------------------------------
# 3. _format_files_changed handles int, list, and fallback
# ---------------------------------------------------------------------------

class TestFormatFilesChanged:
    def test_integer(self):
        assert _format_files_changed(3) == "3"

    def test_list(self):
        assert _format_files_changed(["a.py", "b.py"]) == "2"

    def test_none(self):
        assert _format_files_changed(None) == "-"


# ---------------------------------------------------------------------------
# 4. build_history_table respects limit and column count
# ---------------------------------------------------------------------------

class TestBuildHistoryTable:
    def test_limits_rows(self):
        table = build_history_table(SAMPLE_ENTRIES, limit=2)
        assert table.row_count == 2

    def test_column_count(self):
        table = build_history_table(SAMPLE_ENTRIES)
        assert len(table.columns) == 7

    def test_full_count(self):
        table = build_history_table(SAMPLE_ENTRIES)
        assert table.row_count == 3


# ---------------------------------------------------------------------------
# 5. display_history reads logs and prints (integration)
# ---------------------------------------------------------------------------

class TestDisplayHistory:
    def test_prints_table(self, log_file, capsys):
        with patch("metabolon.sortase.history.read_logs", return_value=SAMPLE_ENTRIES):
            display_history(limit=2)
        output = capsys.readouterr().out
        assert "add_auth.md" in output or "fix_lint.md" in output

    def test_empty_logs(self, capsys):
        with patch("metabolon.sortase.history.read_logs", return_value=[]):
            display_history()
        output = capsys.readouterr().out
        assert "No dispatch history found" in output


# ---------------------------------------------------------------------------
# Module parses cleanly
# ---------------------------------------------------------------------------

def test_module_parses():
    source = Path(__file__).resolve().parent.parent / "metabolon" / "sortase" / "history.py"
    ast.parse(source.read_text(encoding="utf-8"))
