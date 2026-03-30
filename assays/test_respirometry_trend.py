"""Tests for respirometry trend subcommand."""

import json
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
import importlib.util
import importlib.machinery
import types

# Import the effector as a module (no .py extension, need SourceFileLoader)
_loader = importlib.machinery.SourceFileLoader(
    "respirometry", "/Users/terry/germline/effectors/respirometry"
)
_spec = importlib.util.spec_from_loader("respirometry", _loader)
resp = types.ModuleType("respirometry")
_loader.exec_module(resp)


@pytest.fixture
def tmp_history(tmp_path, monkeypatch):
    """Point usage-history.jsonl at a temp file."""
    history_file = tmp_path / "usage-history.jsonl"
    monkeypatch.setattr(resp, "USAGE_HISTORY", history_file)
    return history_file


def _make_row(date_str: str, weekly_pct: float, sonnet_pct: float,
              session_count: int, goose_dispatches: int) -> dict:
    return {
        "date": date_str,
        "weekly_pct": weekly_pct,
        "sonnet_pct": sonnet_pct,
        "session_count": session_count,
        "goose_dispatches": goose_dispatches,
    }


# ---------------------------------------------------------------------------
# Test 1: trend on empty history shows "no data" message
# ---------------------------------------------------------------------------

def test_trend_empty_history(tmp_history, capsys):
    """When no history file exists, trend reports no data."""
    resp.cmd_trend()
    captured = capsys.readouterr()
    assert "No usage history" in captured.out


# ---------------------------------------------------------------------------
# Test 2: trend renders table from existing history entries
# ---------------------------------------------------------------------------

def test_trend_renders_table(tmp_history, capsys):
    """Multiple weeks of data render as a formatted table."""
    rows = [
        _make_row("2026-03-24", 45.0, 12.0, 8, 260),
        _make_row("2026-03-17", 62.0, 25.0, 12, 45),
        _make_row("2026-03-10", 30.0, 8.0, 5, 100),
    ]
    for row in rows:
        tmp_history.write_text(
            tmp_history.read_text() + json.dumps(row) + "\n"
        )

    resp.cmd_trend()
    captured = capsys.readouterr()
    out = captured.out

    # Header row
    assert "Week" in out
    assert "All Models" in out
    assert "Sonnet" in out
    assert "Sessions" in out
    assert "Goose" in out

    # Most recent week first
    assert "45%" in out
    assert "12%" in out
    # Second week
    assert "62%" in out
    assert "25%" in out


# ---------------------------------------------------------------------------
# Test 3: record_snapshot appends a row to history
# ---------------------------------------------------------------------------

def test_record_snapshot_appends(tmp_history):
    """record_snapshot writes a valid JSONL entry."""
    fake_usage = {
        "seven_day": {"utilization": 0.55},
        "seven_day_sonnet": {"utilization": 0.18},
    }

    with patch.object(resp, "get_usage", return_value=fake_usage):
        with patch.object(resp, "_derive_session_stats", return_value=(7, 42)):
            resp.record_snapshot()

    assert tmp_history.exists()
    lines = tmp_history.read_text().strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["weekly_pct"] == 55.0
    assert row["sonnet_pct"] == 18.0
    assert row["session_count"] == 7
    assert row["goose_dispatches"] == 42
    assert "date" in row
