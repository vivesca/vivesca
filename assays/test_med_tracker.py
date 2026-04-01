from __future__ import annotations

"""Tests for med-tracker — medication schedule CLI tool."""

import argparse
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest


def _load_med_tracker():
    """Load med-tracker by exec-ing its source."""
    source = open(str(Path.home() / "germline/effectors/med-tracker")).read()
    ns: dict = {"__name__": "med_tracker"}
    exec(source, ns)
    return ns


_mod = _load_med_tracker()
parse_schedule = _mod["parse_schedule"]
format_date = _mod["format_date"]
cmd_status = _mod["cmd_status"]
cmd_add = _mod["cmd_add"]
cmd_interactions = _mod["cmd_interactions"]
SCHEDULE_PATH = _mod["SCHEDULE_PATH"]


# ── helpers ────────────────────────────────────────────────────────────


def _make_schedule(tmp_path: Path, content: str) -> Path:
    """Create a medication-schedule.md in tmp_path and return its path."""
    sched_dir = tmp_path / "epigenome" / "chromatin" / "Health"
    sched_dir.mkdir(parents=True, exist_ok=True)
    sched = sched_dir / "medication-schedule.md"
    sched.write_text(content)
    return sched


SCHEDULE_TABLE = """\
# Medication Schedule

| drug | start | end | notes |
|------|-------|-----|-------|
| Amoxicillin | 2026-03-25 | 2026-04-08 | Antibiotic course |
| Itraconazole | 2026-03-20 | 2026-04-15 | CYP3A4 inhibitor |
| Omeprazole | 2026-03-01 | 2026-04-30 | CYP3A4 substrate, acid reflux |
| ExpiredDrug | 2026-01-01 | 2026-01-10 | Already finished |
"""

TODAY = date.today()


def _active_date_range(offset_start: int, offset_end: int):
    """Return (start_str, end_str) relative to today."""
    start = TODAY + timedelta(days=offset_start)
    end = TODAY + timedelta(days=offset_end)
    return start.isoformat(), end.isoformat()


# ── parse_schedule tests ──────────────────────────────────────────────


def test_parse_schedule_extracts_medications(tmp_path):
    """parse_schedule returns list of dicts from markdown table."""
    sched = _make_schedule(tmp_path, SCHEDULE_TABLE)
    _mod["SCHEDULE_PATH"] = sched
    try:
        meds = parse_schedule()
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    assert len(meds) == 4
    assert meds[0]["drug"] == "Amoxicillin"
    assert meds[0]["start"] == "2026-03-25"
    assert meds[0]["end"] == "2026-04-08"
    assert meds[0]["notes"] == "Antibiotic course"


def test_parse_schedule_missing_file(tmp_path):
    """parse_schedule returns empty list when schedule file doesn't exist."""
    missing = tmp_path / "nonexistent" / "medication-schedule.md"
    _mod["SCHEDULE_PATH"] = missing
    try:
        meds = parse_schedule()
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    assert meds == []


def test_parse_schedule_empty_file(tmp_path):
    """parse_schedule returns empty list for empty file."""
    sched = _make_schedule(tmp_path, "")
    _mod["SCHEDULE_PATH"] = sched
    try:
        meds = parse_schedule()
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    assert meds == []


def test_parse_schedule_no_table(tmp_path):
    """parse_schedule returns empty when file has no table header."""
    sched = _make_schedule(tmp_path, "# Just a title\n\nSome notes here.\n")
    _mod["SCHEDULE_PATH"] = sched
    try:
        meds = parse_schedule()
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    assert meds == []


def test_parse_schedule_short_rows_skipped(tmp_path):
    """parse_schedule skips rows with fewer than 4 columns."""
    content = """\
| drug | start | end | notes |
|------|-------|-----|-------|
| ShortRow | 2026-01-01 | 2026-01-02 |
| ValidDrug | 2026-03-01 | 2026-04-01 | ok |
"""
    sched = _make_schedule(tmp_path, content)
    _mod["SCHEDULE_PATH"] = sched
    try:
        meds = parse_schedule()
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    assert len(meds) == 1
    assert meds[0]["drug"] == "ValidDrug"


def test_parse_schedule_strips_whitespace(tmp_path):
    """parse_schedule strips whitespace from cell values."""
    content = """\
| drug | start | end | notes |
|------|-------|-----|-------|
|  DrugX  |  2026-03-01  |  2026-04-01  |  spaced notes  |
"""
    sched = _make_schedule(tmp_path, content)
    _mod["SCHEDULE_PATH"] = sched
    try:
        meds = parse_schedule()
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    assert meds[0]["drug"] == "DrugX"
    assert meds[0]["start"] == "2026-03-01"
    assert meds[0]["notes"] == "spaced notes"


# ── format_date tests ─────────────────────────────────────────────────


def test_format_date_valid():
    """format_date parses YYYY-MM-DD string to date."""
    d = format_date("2026-04-01")
    assert d == date(2026, 4, 1)


def test_format_date_invalid_raises():
    """format_date raises ValueError for bad format."""
    with pytest.raises(ValueError):
        format_date("not-a-date")


def test_format_date_empty_raises():
    """format_date raises ValueError for empty string."""
    with pytest.raises(ValueError):
        format_date("")


# ── cmd_status tests ──────────────────────────────────────────────────


def _mock_ns(**kwargs):
    """Create an argparse.Namespace with given attributes."""
    return argparse.Namespace(**kwargs)


def test_cmd_status_no_active_medications(tmp_path, capsys):
    """cmd_status shows 'No active medications' when none are current."""
    sched = _make_schedule(tmp_path, """\
| drug | start | end | notes |
|------|-------|-----|-------|
| ExpiredDrug | 2026-01-01 | 2026-01-10 | Done |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_status(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "No active medications" in out


def test_cmd_status_shows_active_medications(tmp_path, capsys):
    """cmd_status lists active medications with days remaining."""
    start, end = _active_date_range(-5, 10)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| TestDrug | {start} | {end} | Test notes |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_status(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "TestDrug" in out
    assert "10" in out  # days remaining
    assert "Test notes" in out
    assert "| Drug |" in out


def test_cmd_status_sorted_by_days_remaining(tmp_path, capsys):
    """cmd_status sorts active medications by days remaining ascending."""
    s1, e1 = _active_date_range(-5, 3)
    s2, e2 = _active_date_range(-2, 15)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| DrugShort | {s1} | {e1} | Ending soon |
| DrugLong | {s2} | {e2} | Longer course |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_status(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    # DrugShort (3 days left) should appear before DrugLong (15 days left)
    pos_short = out.index("DrugShort")
    pos_long = out.index("DrugLong")
    assert pos_short < pos_long


def test_cmd_status_shows_today_date(tmp_path, capsys):
    """cmd_status includes today's date in output."""
    start, end = _active_date_range(-1, 5)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| AnyDrug | {start} | {end} | Notes |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_status(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert TODAY.isoformat() in out


def test_cmd_status_skips_bad_dates(tmp_path, capsys):
    """cmd_status silently skips rows with unparseable dates."""
    start, end = _active_date_range(-1, 5)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| BadDate | not-a-date | also-bad | Bad row |
| GoodDrug | {start} | {end} | Good row |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_status(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "GoodDrug" in out
    assert "BadDate" not in out


def test_cmd_status_no_schedule_file(tmp_path, capsys):
    """cmd_status shows 'No active medications' when file missing."""
    _mod["SCHEDULE_PATH"] = tmp_path / "nonexistent" / "schedule.md"
    try:
        cmd_status(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "No active medications" in out


# ── cmd_add tests ─────────────────────────────────────────────────────


def test_cmd_add_appends_to_file(tmp_path, capsys):
    """cmd_add appends a new row to the schedule file."""
    sched = _make_schedule(tmp_path, """\
| drug | start | end | notes |
|------|-------|-----|-------|
| Existing | 2026-01-01 | 2026-01-10 | Old |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        args = _mock_ns(drug="NewDrug", start="2026-05-01", end="2026-05-15", notes="Test note")
        cmd_add(args)
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "Added NewDrug" in out

    content = sched.read_text()
    assert "NewDrug" in content
    assert "2026-05-01" in content
    assert "2026-05-15" in content
    assert "Test note" in content


def test_cmd_add_no_notes(tmp_path, capsys):
    """cmd_add writes empty string when notes is None."""
    sched = _make_schedule(tmp_path, """\
| drug | start | end | notes |
|------|-------|-----|-------|
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        args = _mock_ns(drug="Plain", start="2026-06-01", end="2026-06-10", notes=None)
        cmd_add(args)
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    content = sched.read_text()
    assert "| Plain | 2026-06-01 | 2026-06-10 |  |" in content


def test_cmd_add_rejects_duplicate(tmp_path):
    """cmd_add exits with error when drug already exists (case-insensitive)."""
    sched = _make_schedule(tmp_path, """\
| drug | start | end | notes |
|------|-------|-----|-------|
| Ibuprofen | 2026-01-01 | 2026-01-10 | Pain |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        args = _mock_ns(drug="ibuprofen", start="2026-07-01", end="2026-07-10", notes="")
        with pytest.raises(SystemExit) as exc_info:
            cmd_add(args)
        assert exc_info.value.code == 1
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    # File should be unchanged
    content = sched.read_text()
    assert "2026-07-01" not in content


def test_cmd_add_creates_file_if_missing(tmp_path, capsys):
    """cmd_add creates the file if it doesn't exist."""
    sched = tmp_path / "epigenome" / "chromatin" / "Health" / "medication-schedule.md"
    sched.parent.mkdir(parents=True, exist_ok=True)
    # File does NOT exist yet
    assert not sched.exists()

    _mod["SCHEDULE_PATH"] = sched
    try:
        args = _mock_ns(drug="FirstDrug", start="2026-08-01", end="2026-08-10", notes="First")
        cmd_add(args)
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    assert sched.exists()
    content = sched.read_text()
    assert "FirstDrug" in content


# ── cmd_interactions tests ────────────────────────────────────────────


def test_cmd_interactions_no_active_cyp3a4(tmp_path, capsys):
    """cmd_interactions reports no concerns when only one or zero CYP3A4 meds."""
    start, end = _active_date_range(-5, 10)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| PlainDrug | {start} | {end} | Nothing special |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_interactions(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "No CYP3A4 interaction concerns" in out


def test_cmd_interactions_single_cyp3a4(tmp_path, capsys):
    """cmd_interactions lists single CYP3A4 med but no warning."""
    start, end = _active_date_range(-5, 10)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| Ketoconazole | {start} | {end} | CYP3A4 inhibitor |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_interactions(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "No CYP3A4 interaction concerns" in out
    assert "Ketoconazole" in out


def test_cmd_interactions_multiple_cyp3a4_warning(tmp_path, capsys):
    """cmd_interactions shows warning when multiple CYP3A4 meds are active."""
    start1, end1 = _active_date_range(-5, 10)
    start2, end2 = _active_date_range(-3, 12)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| Itraconazole | {start1} | {end1} | CYP3A4 inhibitor |
| Simvastatin | {start2} | {end2} | CYP3A4 substrate |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_interactions(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "CYP3A4 Interaction Warning" in out
    assert "Itraconazole" in out
    assert "Simvastatin" in out
    assert "pharmacist" in out.lower() or "physician" in out.lower()


def test_cmd_interactions_detects_lowercase_cyp3a4(tmp_path, capsys):
    """cmd_interactions detects cyp3a4 in lowercase notes."""
    start1, end1 = _active_date_range(-5, 10)
    start2, end2 = _active_date_range(-3, 12)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| DrugA | {start1} | {end1} | cyp3a4 inhibitor |
| DrugB | {start2} | {end2} | 3A4 substrate |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_interactions(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "CYP3A4 Interaction Warning" in out


def test_cmd_interactions_skips_expired(tmp_path, capsys):
    """cmd_interactions ignores expired CYP3A4 medications."""
    start, end = _active_date_range(-5, 10)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| OldInhibitor | 2026-01-01 | 2026-01-10 | CYP3A4 inhibitor |
| CurrentDrug | {start} | {end} | CYP3A4 substrate |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_interactions(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    # Only one active CYP3A4 med — no warning
    assert "No CYP3A4 interaction concerns" in out
    assert "CurrentDrug" in out


def test_cmd_interactions_no_schedule_file(tmp_path, capsys):
    """cmd_interactions handles missing schedule file gracefully."""
    _mod["SCHEDULE_PATH"] = tmp_path / "nonexistent" / "schedule.md"
    try:
        cmd_interactions(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "No CYP3A4 interaction concerns" in out


# ── Edge case: boundary dates ──────────────────────────────────────────


def test_cmd_status_medication_starts_today(tmp_path, capsys):
    """A medication that starts today is shown as active."""
    start, end = _active_date_range(0, 7)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| StartingToday | {start} | {end} | New |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_status(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "StartingToday" in out


def test_cmd_status_medication_ends_today(tmp_path, capsys):
    """A medication that ends today is shown as active (0 days left)."""
    start, end = _active_date_range(-5, 0)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| EndingToday | {start} | {end} | Last day |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_status(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "EndingToday" in out


def test_cmd_status_medication_ended_yesterday(tmp_path, capsys):
    """A medication that ended yesterday is NOT shown."""
    start, end = _active_date_range(-5, -1)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| EndedYesterday | {start} | {end} | Done |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_status(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "EndedYesterday" not in out


def test_cmd_status_medication_not_started_yet(tmp_path, capsys):
    """A medication that starts tomorrow is NOT shown."""
    start, end = _active_date_range(1, 10)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| Future | {start} | {end} | Not yet |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_status(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "Future" not in out


# ── main() CLI entry-point tests (via exec namespace) ──────────────────


def _run_main(*argv: str, schedule_path: Path | None = None):
    """Run main() in the exec'd namespace with given argv.

    Returns (stdout, stderr, exit_code).  exit_code is None if no SystemExit.
    """
    import io

    old_argv = _mod["sys"].argv
    if schedule_path is not None:
        old_sched = _mod["SCHEDULE_PATH"]
        _mod["SCHEDULE_PATH"] = schedule_path

    _mod["sys"].argv = ["med-tracker", *argv]
    captured_out = io.StringIO()
    captured_err = io.StringIO()
    _mod["sys"].stdout = captured_out
    _mod["sys"].stderr = captured_err

    exit_code = None
    try:
        _mod["main"]()
    except SystemExit as e:
        exit_code = e.code
    finally:
        _mod["sys"].argv = old_argv
        _mod["sys"].stdout = sys.stdout
        _mod["sys"].stderr = sys.stderr
        if schedule_path is not None:
            _mod["SCHEDULE_PATH"] = old_sched

    return captured_out.getvalue(), captured_err.getvalue(), exit_code


def test_main_no_args_exits():
    """main() with no arguments exits with error (argparse required=True)."""
    _, err, code = _run_main()
    assert code == 2  # argparse exits 2 for missing required subcommand


def test_main_status_subcommand(tmp_path):
    """main() dispatches 'status' subcommand correctly."""
    start, end = _active_date_range(-1, 5)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| MainDrug | {start} | {end} | Via main |
""")
    out, _, code = _run_main("status", schedule_path=sched)
    assert code is None
    assert "MainDrug" in out
    assert "Via main" in out


def test_main_add_subcommand(tmp_path):
    """main() dispatches 'add' subcommand and writes to file."""
    sched = _make_schedule(tmp_path, """\
| drug | start | end | notes |
|------|-------|-----|-------|
""")
    out, _, code = _run_main(
        "add", "AddedDrug", "--start", "2026-09-01", "--end", "2026-09-10",
        "--notes", "from CLI", schedule_path=sched,
    )
    assert code is None
    assert "Added AddedDrug" in out
    assert "AddedDrug" in sched.read_text()


def test_main_add_missing_start_exits():
    """main() 'add' without --start exits with error."""
    _, _, code = _run_main("add", "Drug", "--end", "2026-09-10")
    assert code == 2  # argparse error for missing required arg


def test_main_interactions_subcommand(tmp_path):
    """main() dispatches 'interactions' subcommand."""
    start, end = _active_date_range(-1, 5)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| Plain | {start} | {end} | No interactions |
""")
    out, _, code = _run_main("interactions", schedule_path=sched)
    assert code is None
    assert "No CYP3A4 interaction concerns" in out


def test_main_add_duplicate_exits(tmp_path):
    """main() 'add' with duplicate drug exits via sys.exit(1)."""
    sched = _make_schedule(tmp_path, """\
| drug | start | end | notes |
|------|-------|-----|-------|
| Dup | 2026-01-01 | 2026-01-10 | Original |
""")
    _, err, code = _run_main(
        "add", "dup", "--start", "2026-10-01", "--end", "2026-10-10",
        schedule_path=sched,
    )
    assert code == 1
    assert "already exists" in err


# ── cmd_add with empty-string notes ────────────────────────────────────


def test_cmd_add_empty_string_notes(tmp_path, capsys):
    """cmd_add writes empty notes field when notes is '' (not None)."""
    sched = _make_schedule(tmp_path, """\
| drug | start | end | notes |
|------|-------|-----|-------|
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        args = _mock_ns(drug="NoNotes", start="2026-07-01", end="2026-07-10", notes="")
        cmd_add(args)
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    content = sched.read_text()
    assert "| NoNotes | 2026-07-01 | 2026-07-10 |  |" in content


# ── parse_schedule with preamble content ───────────────────────────────


def test_parse_schedule_table_after_preamble(tmp_path):
    """parse_schedule finds table even when preceded by paragraphs."""
    content = """\
# Medication Schedule

This file tracks current medications.
Last updated by Dr. Smith.

| drug | start | end | notes |
|------|-------|-----|-------|
| BuriedDrug | 2026-03-01 | 2026-04-01 | Found it |
"""
    sched = _make_schedule(tmp_path, content)
    _mod["SCHEDULE_PATH"] = sched
    try:
        meds = parse_schedule()
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    assert len(meds) == 1
    assert meds[0]["drug"] == "BuriedDrug"


# ── cmd_interactions keyword variants ─────────────────────────────────


def test_cmd_interactions_inhibitor_keyword(tmp_path, capsys):
    """cmd_interactions detects 'inhibitor' keyword alone."""
    start1, end1 = _active_date_range(-5, 10)
    start2, end2 = _active_date_range(-3, 12)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| DrugA | {start1} | {end1} | strong inhibitor of metabolism |
| DrugB | {start2} | {end2} | CYP3A4 substrate |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_interactions(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "CYP3A4 Interaction Warning" in out
    assert "DrugA" in out


def test_cmd_interactions_substrate_keyword(tmp_path, capsys):
    """cmd_interactions detects 'substrate' keyword alone."""
    start1, end1 = _active_date_range(-5, 10)
    start2, end2 = _active_date_range(-3, 12)
    sched = _make_schedule(tmp_path, f"""\
| drug | start | end | notes |
|------|-------|-----|-------|
| DrugX | {start1} | {end1} | substrate of CYP enzymes |
| DrugY | {start2} | {end2} | 3A4 related |
""")
    _mod["SCHEDULE_PATH"] = sched
    try:
        cmd_interactions(_mock_ns())
    finally:
        _mod["SCHEDULE_PATH"] = SCHEDULE_PATH

    out = capsys.readouterr().out
    assert "CYP3A4 Interaction Warning" in out


# ── subprocess invocation ──────────────────────────────────────────────


def test_subprocess_help():
    """med-tracker --help exits 0 and shows usage."""
    import subprocess
    result = subprocess.run(
        ["python3", str(Path.home() / "germline/effectors/med-tracker"), "--help"],
        capture_output=True, text=True, timeout=10,
    )
    assert result.returncode == 0
    assert "med-tracker" in result.stdout.lower() or "medication" in result.stdout.lower()


def test_subprocess_status_no_file(tmp_path, monkeypatch):
    """med-tracker status runs via subprocess and handles missing file."""
    import subprocess
    env = {**os.environ, "HOME": str(tmp_path)}
    result = subprocess.run(
        ["python3", str(Path.home() / "germline/effectors/med-tracker"), "status"],
        capture_output=True, text=True, timeout=10, env=env,
    )
    assert result.returncode == 0
    assert "No active medications" in result.stdout
