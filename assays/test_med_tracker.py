#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/med-tracker — medication schedule CLI tool."""

import argparse
import subprocess
import sys
from datetime import date, timedelta
from io import StringIO
from pathlib import Path

import pytest

# Load effector via exec (no .py extension)
_effector_path = Path(__file__).parent.parent / "effectors" / "med-tracker"
_ns: dict = {"__name__": "med_tracker_test"}
exec(open(_effector_path).read(), _ns)

parse_schedule = _ns["parse_schedule"]
format_date = _ns["format_date"]
cmd_status = _ns["cmd_status"]
cmd_add = _ns["cmd_add"]
cmd_interactions = _ns["cmd_interactions"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FixedDate(date):
    """A date subclass whose today() returns a fixed value."""
    _fixed: date = date(2026, 4, 2)

    @classmethod
    def today(cls) -> date:
        return cls._fixed


def _write_schedule(path: Path, rows: list[list[str]]) -> None:
    """Write a minimal medication-schedule.md table to *path*."""
    lines = ["# Medication Schedule\n", "| drug | start | end | notes |", "|------|-------|-----|-------|"]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


@pytest.fixture(autouse=True)
def _isolate_schedule(tmp_path, monkeypatch):
    """Redirect SCHEDULE_PATH to a temp file for every test."""
    schedule_file = tmp_path / "medication-schedule.md"
    _ns["SCHEDULE_PATH"] = schedule_file
    yield schedule_file
    # Restore
    _ns["SCHEDULE_PATH"] = Path.home() / "epigenome/chromatin/Health/medication-schedule.md"


@pytest.fixture(autouse=True)
def _fix_today():
    """Freeze date.today() inside the effector namespace."""
    original_date = _ns["date"]
    _ns["date"] = FixedDate
    yield
    _ns["date"] = original_date


def _namespace(drug="Aspirin", start="2026-03-25", end="2026-04-10", notes="", command="add"):
    return argparse.Namespace(command=command, drug=drug, start=start, end=end, notes=notes)


def _capture_stdout(func, *args, **kwargs) -> str:
    """Run func capturing stdout."""
    old_stdout = _ns.get("sys", sys).stdout
    buf = StringIO()
    _ns["sys"].stdout = buf
    try:
        func(*args, **kwargs)
    finally:
        _ns["sys"].stdout = old_stdout
    return buf.getvalue()


# ---------------------------------------------------------------------------
# parse_schedule
# ---------------------------------------------------------------------------

def test_parse_schedule_no_file(tmp_path):
    """Returns empty list when schedule file doesn't exist."""
    assert parse_schedule() == []


def test_parse_schedule_valid_table(_isolate_schedule):
    """Parses a well-formed table correctly."""
    _write_schedule(_isolate_schedule, [
        ["Amoxicillin", "2026-03-01", "2026-03-10", "take with food"],
        ["Ibuprofen", "2026-04-01", "2026-04-05", "CYP3A4 substrate"],
    ])
    meds = parse_schedule()
    assert len(meds) == 2
    assert meds[0]["drug"] == "Amoxicillin"
    assert meds[0]["start"] == "2026-03-01"
    assert meds[0]["end"] == "2026-03-10"
    assert meds[0]["notes"] == "take with food"
    assert meds[1]["notes"] == "CYP3A4 substrate"


def test_parse_schedule_skips_malformed_rows(_isolate_schedule):
    """Rows with fewer than 4 columns are ignored."""
    path = _isolate_schedule
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([
        "| drug | start | end | notes |",
        "|------|-------|-----|-------|",
        "| OnlyTwo | Columns |",
        "| Good | 2026-01-01 | 2026-01-02 | ok |",
    ]))
    meds = parse_schedule()
    assert len(meds) == 1
    assert meds[0]["drug"] == "Good"


# ---------------------------------------------------------------------------
# format_date
# ---------------------------------------------------------------------------

def test_format_date_valid():
    assert format_date("2026-04-02") == date(2026, 4, 2)


def test_format_date_invalid():
    with pytest.raises(ValueError):
        format_date("not-a-date")


def test_format_date_wrong_format():
    with pytest.raises(ValueError):
        format_date("04/02/2026")


# ---------------------------------------------------------------------------
# cmd_status
# ---------------------------------------------------------------------------

def test_status_no_active_meds(_isolate_schedule):
    """When no medications are currently active."""
    _write_schedule(_isolate_schedule, [
        ["OldDrug", "2026-01-01", "2026-01-15", "done"],
    ])
    out = _capture_stdout(cmd_status, argparse.Namespace(command="status"))
    assert "No active medications" in out
    assert "Today" in out


def test_status_with_active_meds(_isolate_schedule):
    """Active medications appear sorted by days remaining."""
    _write_schedule(_isolate_schedule, [
        ["DrugA", "2026-03-25", "2026-04-05", "note A"],
        ["DrugB", "2026-04-01", "2026-04-10", "note B"],
    ])
    out = _capture_stdout(cmd_status, argparse.Namespace(command="status"))
    assert "DrugA" in out
    assert "DrugB" in out
    assert "Days Left" in out
    # DrugA ends sooner (Apr 5 = 3 days left), should appear first
    assert out.index("DrugA") < out.index("DrugB")


def test_status_empty_schedule(_isolate_schedule):
    """Empty schedule yields no-active message."""
    _isolate_schedule.parent.mkdir(parents=True, exist_ok=True)
    _isolate_schedule.write_text("| drug | start | end | notes |\n|------|-------|-----|-------|\n")
    out = _capture_stdout(cmd_status, argparse.Namespace(command="status"))
    assert "No active medications" in out


# ---------------------------------------------------------------------------
# cmd_add
# ---------------------------------------------------------------------------

def test_add_new_med(_isolate_schedule, capsys):
    """Adds a new row to the schedule file."""
    _write_schedule(_isolate_schedule, [])
    cmd_add(_namespace(drug="NewMed", start="2026-04-01", end="2026-04-15"))
    captured = capsys.readouterr()
    assert "Added NewMed" in captured.out

    meds = parse_schedule()
    assert len(meds) == 1
    assert meds[0]["drug"] == "NewMed"


def test_add_duplicate_med_exits(_isolate_schedule):
    """Adding a duplicate drug name exits with code 1."""
    _write_schedule(_isolate_schedule, [
        ["DupMed", "2026-03-01", "2026-03-10", ""],
    ])
    with pytest.raises(SystemExit) as exc_info:
        cmd_add(_namespace(drug="DupMed"))
    assert exc_info.value.code == 1


def test_add_duplicate_case_insensitive(_isolate_schedule):
    """Duplicate detection is case-insensitive."""
    _write_schedule(_isolate_schedule, [
        ["CaseMed", "2026-03-01", "2026-03-10", ""],
    ])
    with pytest.raises(SystemExit) as exc_info:
        cmd_add(_namespace(drug="casemed"))
    assert exc_info.value.code == 1


def test_add_creates_file_if_missing(_isolate_schedule, capsys):
    """Add works even when the schedule file doesn't exist yet."""
    # File does not exist — parse_schedule returns [], add should create it
    assert not _isolate_schedule.exists()
    cmd_add(_namespace(drug="FirstMed", start="2026-04-01", end="2026-04-10"))
    captured = capsys.readouterr()
    assert "Added FirstMed" in captured.out
    assert _isolate_schedule.exists()


def test_add_with_notes(_isolate_schedule, capsys):
    """Notes are persisted in the new row."""
    _write_schedule(_isolate_schedule, [])
    cmd_add(_namespace(drug="NoteMed", notes="take with food"))
    captured = capsys.readouterr()
    assert "Added NoteMed" in captured.out
    meds = parse_schedule()
    assert meds[0]["notes"] == "take with food"


# ---------------------------------------------------------------------------
# cmd_interactions
# ---------------------------------------------------------------------------

def test_interactions_no_concerns(_isolate_schedule):
    """Single CYP3A4 med → no warning."""
    _write_schedule(_isolate_schedule, [
        ["DrugX", "2026-03-25", "2026-04-10", "CYP3A4 inhibitor"],
    ])
    out = _capture_stdout(cmd_interactions, argparse.Namespace(command="interactions"))
    assert "No CYP3A4 interaction concerns" in out


def test_interactions_multiple_cyp3a4(_isolate_schedule):
    """Two+ active CYP3A4 meds triggers a warning."""
    _write_schedule(_isolate_schedule, [
        ["MedA", "2026-03-25", "2026-04-10", "CYP3A4 substrate"],
        ["MedB", "2026-04-01", "2026-04-15", "3A4 inhibitor"],
    ])
    out = _capture_stdout(cmd_interactions, argparse.Namespace(command="interactions"))
    assert "CYP3A4 Interaction Warning" in out
    assert "MedA" in out
    assert "MedB" in out
    assert "Consult your pharmacist" in out


def test_interactions_no_cyp3a4_meds(_isolate_schedule):
    """No CYP3A4 meds → clean report."""
    _write_schedule(_isolate_schedule, [
        ["PlainMed", "2026-03-25", "2026-04-10", "take with water"],
    ])
    out = _capture_stdout(cmd_interactions, argparse.Namespace(command="interactions"))
    assert "No CYP3A4 interaction concerns" in out


def test_interactions_case_insensitive_keywords(_isolate_schedule):
    """CYP3A4 keywords matched case-insensitively."""
    _write_schedule(_isolate_schedule, [
        ["MedLow", "2026-03-25", "2026-04-10", "cyp3a4 something"],
        ["MedUp", "2026-04-01", "2026-04-15", "CYP3A4 other"],
    ])
    out = _capture_stdout(cmd_interactions, argparse.Namespace(command="interactions"))
    assert "CYP3A4 Interaction Warning" in out


def test_interactions_expired_cyp3a4_ignored(_isolate_schedule):
    """Expired CYP3A4 meds don't trigger warnings."""
    _write_schedule(_isolate_schedule, [
        ["OldCYP", "2026-01-01", "2026-01-15", "CYP3A4 substrate"],
    ])
    out = _capture_stdout(cmd_interactions, argparse.Namespace(command="interactions"))
    assert "No CYP3A4 interaction concerns" in out


# ---------------------------------------------------------------------------
# CLI via subprocess (integration)
# ---------------------------------------------------------------------------

def test_cli_help():
    """--help returns 0 and shows usage."""
    result = subprocess.run(
        [str(_effector_path), "--help"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "med-tracker" in result.stdout or "Medication" in result.stdout


def test_cli_status_no_file(tmp_path):
    """status subcommand works when schedule file is missing."""
    env = __import__("os").environ.copy()
    # We can't easily redirect SCHEDULE_PATH via env for this script,
    # so just verify the command doesn't crash (exit 0).
    # The script prints "No active medications" when file is missing.
    result = subprocess.run(
        [str(_effector_path), "status"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
