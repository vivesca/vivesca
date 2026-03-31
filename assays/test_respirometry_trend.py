"""Tests for respirometry trend subcommand."""

import importlib.machinery
import importlib.util
import json
import types
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the effector as a module (no .py extension, need SourceFileLoader)
_loader = importlib.machinery.SourceFileLoader(
    "respirometry", "/home/terry/germline/effectors/respirometry"
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


def _make_row(
    date_str: str,
    weekly_pct: float,
    sonnet_pct: float,
    session_count: int,
    goose_dispatches: int,
) -> dict:
    return {
        "date": date_str,
        "weekly_pct": weekly_pct,
        "sonnet_pct": sonnet_pct,
        "session_count": session_count,
        "goose_dispatches": goose_dispatches,
    }


def test_trend_empty_history(tmp_history, capsys):
    """Trend reports a clear message when no history exists."""
    resp.cmd_trend()
    captured = capsys.readouterr()
    assert "No usage history" in captured.out


def test_trend_renders_table(tmp_history, capsys):
    """Trend renders latest weekly rows in reverse chronological order."""
    rows = [
        _make_row("2026-03-24", 45.0, 12.0, 8, 260),
        _make_row("2026-03-17", 62.0, 25.0, 12, 45),
        _make_row("2026-03-24", 47.0, 13.0, 9, 270),
    ]
    tmp_history.write_text("".join(json.dumps(row) + "\n" for row in rows))

    resp.cmd_trend()
    captured = capsys.readouterr()
    output_lines = captured.out.strip().splitlines()

    assert output_lines[0] == "Week      | All Models | Sonnet | Sessions | Goose"
    assert "Mar 24-30 |       47% |   13% |        9 |    270" == output_lines[2]
    assert "Mar 17-23 |       62% |   25% |       12 |     45" == output_lines[3]


def test_record_snapshot_creates_history_with_windowed_stats(tmp_history, monkeypatch):
    """Snapshot creation seeds the history file with the current seven-day window."""
    fake_usage = {
        "seven_day": {"utilization": 0.55},
        "seven_day_sonnet": {"utilization": 0.18},
    }
    reference_time = datetime(2026, 3, 31, 9, 0, 0)
    sortase_log = tmp_history.parent / "sortase.jsonl"
    rows = [
        {"timestamp": "2026-03-24T09:00:00", "tool": "goose"},
        {"timestamp": "2026-03-24T17:00:00", "tool": "droid"},
        {"timestamp": "2026-03-28T12:00:00", "tool": "goose"},
        {"timestamp": "2026-03-30T08:30:00", "tool": "goose"},
        {"timestamp": "2026-03-31T10:00:00", "tool": "goose"},
        {"timestamp": "2026-03-23T10:00:00", "tool": "goose"},
    ]
    sortase_log.write_text("".join(json.dumps(row) + "\n" for row in rows))
    monkeypatch.setattr(resp, "SORTASE_LOG", sortase_log)

    with patch.object(resp, "get_usage", return_value=fake_usage):
        resp.record_snapshot(reference_time=reference_time)

    assert tmp_history.exists()
    lines = tmp_history.read_text().strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["weekly_pct"] == 55.0
    assert row["sonnet_pct"] == 18.0
    assert row["session_count"] == 3
    assert row["goose_dispatches"] == 3
    assert row["date"] == "2026-03-24"
