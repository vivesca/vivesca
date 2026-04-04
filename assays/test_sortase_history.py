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
    build_history_entries,
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
# 6. build_history_entries returns raw dicts
# ---------------------------------------------------------------------------


class TestBuildHistoryEntries:
    def test_returns_list_of_dicts(self):
        rows = build_history_entries(SAMPLE_ENTRIES, limit=2)
        assert len(rows) == 2
        assert isinstance(rows[0], dict)

    def test_entry_keys(self):
        rows = build_history_entries(SAMPLE_ENTRIES, limit=1)
        entry = rows[0]
        for key in ("timestamp", "plan", "backend", "duration", "status", "files"):
            assert key in entry, f"Missing key: {key}"

    def test_status_mapping(self):
        rows = build_history_entries(SAMPLE_ENTRIES)
        statuses = [r["status"] for r in rows]
        assert "ok" in statuses
        assert "fail" in statuses

    def test_reversed_order(self):
        rows = build_history_entries(SAMPLE_ENTRIES)
        # Most recent entry first (reversed from chronological)
        assert rows[0]["plan"] == "refactor_api.md"

    def test_respects_limit(self):
        rows = build_history_entries(SAMPLE_ENTRIES, limit=1)
        assert len(rows) == 1

    def test_empty_entries(self):
        rows = build_history_entries([], limit=10)
        assert rows == []


# ---------------------------------------------------------------------------
# 7. CLI history --json-output flag
# ---------------------------------------------------------------------------


class TestHistoryJsonFlag:
    def test_history_json_flag(self):
        from click.testing import CliRunner

        from metabolon.sortase.cli import main

        runner = CliRunner()
        with patch("metabolon.sortase.cli.read_logs", return_value=SAMPLE_ENTRIES):
            result = runner.invoke(main, ["history", "--json-output", "--last", "2"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["plan"] in ("fix_lint.md", "refactor_api.md")

    def test_history_json_empty(self):
        from click.testing import CliRunner

        from metabolon.sortase.cli import main

        runner = CliRunner()
        with patch("metabolon.sortase.cli.read_logs", return_value=[]):
            result = runner.invoke(main, ["history", "--json-output"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data == []

    def test_history_default_unchanged(self):
        """Non-JSON output still renders a rich table."""
        from click.testing import CliRunner

        from metabolon.sortase.cli import main

        runner = CliRunner()
        with patch("metabolon.sortase.cli.read_logs", return_value=SAMPLE_ENTRIES):
            result = runner.invoke(main, ["history", "--last", "2"])
        assert result.exit_code == 0, result.output
        # Rich table output contains the plan names as plain text
        assert "add_auth.md" in result.output or "fix_lint.md" in result.output


# ---------------------------------------------------------------------------
# Module parses cleanly
# ---------------------------------------------------------------------------


def test_module_parses():
    source = Path(__file__).resolve().parent.parent / "metabolon" / "sortase" / "history.py"
    ast.parse(source.read_text(encoding="utf-8"))
