"""Tests for golem-dash — dashboard for golem task queue status."""
from __future__ import annotations

import json
import shutil
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_golem_dash():
    """Load the golem-dash module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/golem-dash").read()
    ns: dict = {"__name__": "golem_dash"}
    exec(source, ns)
    return ns


_mod = _load_golem_dash()
load_jsonl = _mod["load_jsonl"]
load_queue = _mod["load_queue"]
load_daemon_log_tail = _mod["load_daemon_log_tail"]
compute_provider_stats = _mod["compute_provider_stats"]
fmt_duration = _mod["fmt_duration"]
fmt_bytes = _mod["fmt_bytes"]
colorize = _mod["colorize"]
run = _mod["run"]
JSONL_FILE = _mod["JSONL_FILE"]
LOG_FILE = _mod["LOG_FILE"]
QUEUE_FILE = _mod["QUEUE_FILE"]


# ── load_jsonl tests ──────────────────────────────────────────────────


def test_load_jsonl_parses_valid_entries(tmp_path):
    """load_jsonl parses valid JSONL lines."""
    f = tmp_path / "test.jsonl"
    f.write_text(
        '{"ts":"2026-01-01","provider":"zhipu","duration":10,"exit":0}\n'
        '{"ts":"2026-01-01","provider":"volcano","duration":20,"exit":1}\n'
    )
    entries = load_jsonl(f)
    assert len(entries) == 2
    assert entries[0]["provider"] == "zhipu"
    assert entries[1]["provider"] == "volcano"


def test_load_jsonl_skips_malformed(tmp_path):
    """load_jsonl skips malformed lines."""
    f = tmp_path / "bad.jsonl"
    f.write_text('{"ok":1}\nBAD LINE\n{"ok":2}\n\n')
    entries = load_jsonl(f)
    assert len(entries) == 2


def test_load_jsonl_missing_file(tmp_path):
    """load_jsonl returns empty list for missing file."""
    entries = load_jsonl(tmp_path / "nope.jsonl")
    assert entries == []


def test_load_jsonl_handles_encoding_errors(tmp_path):
    """load_jsonl handles files with bad encoding."""
    f = tmp_path / "mixed.jsonl"
    f.write_bytes(b'{"a":1}\n\x92\n{"b":2}\n')
    entries = load_jsonl(f)
    assert len(entries) == 2


# ── load_queue tests ──────────────────────────────────────────────────


_SAMPLE_QUEUE = textwrap.dedent("""\
    # Golem Task Queue

    ## Pending

    - [ ] `golem --provider infini "task 1"`
    - [ ] `golem --provider volcano "task 2"`

    ## Done

    - [x] `golem --provider zhipu "completed"` → exit=0
    - [x] `golem --provider infini "another done"`

    ## Failed

    - [!] `golem --provider volcano "failed task"`
""")


def test_load_queue_counts(tmp_path):
    """load_queue counts pending/done/failed correctly."""
    qf = tmp_path / "q.md"
    qf.write_text(_SAMPLE_QUEUE)
    result = load_queue(qf)
    assert result["pending"] == 2
    assert result["done"] == 2
    assert result["failed"] == 1


def test_load_queue_last_done_extracts_results(tmp_path):
    """load_queue extracts last_done commands and results."""
    qf = tmp_path / "q.md"
    qf.write_text(_SAMPLE_QUEUE)
    result = load_queue(qf)
    assert len(result["last_done"]) == 2
    # First done entry has arrow result
    cmds = [cmd for cmd, _ in result["last_done"]]
    assert any("zhipu" in c for c in cmds)
    # Check result extraction
    results = [r for _, r in result["last_done"]]
    assert any("exit=0" in r for r in results)


def test_load_queue_missing_file(tmp_path):
    """load_queue returns zeros for missing file."""
    result = load_queue(tmp_path / "nope.md")
    assert result["pending"] == 0
    assert result["done"] == 0
    assert result["failed"] == 0
    assert result["last_done"] == []


def test_load_queue_empty_file(tmp_path):
    """load_queue handles empty queue file."""
    qf = tmp_path / "empty.md"
    qf.write_text("")
    result = load_queue(qf)
    assert result["pending"] == 0


# ── load_daemon_log_tail tests ────────────────────────────────────────


def test_load_daemon_log_tail(tmp_path):
    """load_daemon_log_tail returns last N lines."""
    lf = tmp_path / "daemon.log"
    lf.write_text("line1\nline2\nline3\nline4\nline5\nline6\n")
    lines = load_daemon_log_tail(lf, 3)
    assert lines == ["line4", "line5", "line6"]


def test_load_daemon_log_tail_missing(tmp_path):
    """load_daemon_log_tail returns empty for missing file."""
    lines = load_daemon_log_tail(tmp_path / "nope.log", 5)
    assert lines == []


def test_load_daemon_log_tail_short_file(tmp_path):
    """load_daemon_log_tail returns all lines if file < N."""
    lf = tmp_path / "short.log"
    lf.write_text("only\n")
    lines = load_daemon_log_tail(lf, 5)
    assert lines == ["only"]


# ── compute_provider_stats tests ──────────────────────────────────────


def test_compute_provider_stats_basic():
    """compute_provider_stats groups by provider and computes stats."""
    entries = [
        {"provider": "zhipu", "exit": 0, "duration": 100},
        {"provider": "zhipu", "exit": 1, "duration": 200},
        {"provider": "volcano", "exit": 0, "duration": 50},
    ]
    rows = compute_provider_stats(entries)
    assert len(rows) == 2

    zhipu = next(r for r in rows if r["provider"] == "zhipu")
    assert zhipu["pass"] == 1
    assert zhipu["fail"] == 1
    assert zhipu["total"] == 2
    assert zhipu["rate"] == 50.0
    assert zhipu["avg_dur"] == 150  # (100+200)/2

    volcano = next(r for r in rows if r["provider"] == "volcano")
    assert volcano["pass"] == 1
    assert volcano["fail"] == 0
    assert volcano["rate"] == 100.0


def test_compute_provider_stats_empty():
    """compute_provider_stats returns empty for no entries."""
    rows = compute_provider_stats([])
    assert rows == []


def test_compute_provider_stats_all_pass():
    """compute_provider_stats with 100% pass rate."""
    entries = [
        {"provider": "zhipu", "exit": 0, "duration": 60},
        {"provider": "zhipu", "exit": 0, "duration": 120},
    ]
    rows = compute_provider_stats(entries)
    assert len(rows) == 1
    assert rows[0]["rate"] == 100.0
    assert rows[0]["avg_dur"] == 90


def test_compute_provider_stats_all_fail():
    """compute_provider_stats with 0% pass rate."""
    entries = [
        {"provider": "infini", "exit": 1, "duration": 30},
        {"provider": "infini", "exit": 2, "duration": 30},
    ]
    rows = compute_provider_stats(entries)
    assert rows[0]["rate"] == 0.0
    assert rows[0]["fail"] == 2


def test_compute_provider_stats_unknown_provider():
    """compute_provider_stats handles missing provider field."""
    entries = [
        {"exit": 0, "duration": 10},
    ]
    rows = compute_provider_stats(entries)
    assert rows[0]["provider"] == "unknown"


# ── fmt_duration tests ────────────────────────────────────────────────


def test_fmt_duration_seconds():
    assert fmt_duration(0) == "0s"
    assert fmt_duration(45) == "45s"


def test_fmt_duration_minutes():
    assert fmt_duration(60) == "1m00s"
    assert fmt_duration(125) == "2m05s"


def test_fmt_duration_hours():
    assert fmt_duration(3600) == "1h00m"
    assert fmt_duration(3661) == "1h01m"


# ── fmt_bytes tests ───────────────────────────────────────────────────


def test_fmt_bytes_gb():
    assert fmt_bytes(2 * 1024 ** 3) == "2.0 GB"
    assert fmt_bytes(512 * 1024 ** 3) == "512.0 GB"


def test_fmt_bytes_mb():
    assert fmt_bytes(500 * 1024 ** 2) == "500 MB"
    assert fmt_bytes(100 * 1024 ** 2) == "100 MB"


def test_fmt_bytes_unknown():
    assert fmt_bytes(-1) == "unknown"


# ── colorize tests ────────────────────────────────────────────────────


def test_colorize_no_color():
    """colorize returns blank strings when --no-color."""
    c = _mod["colorize"](False)
    assert c["green"] == ""
    assert c["red"] == ""
    assert c["reset"] == ""


def test_colorize_with_color_when_tty():
    """colorize returns ANSI codes when stdout is a tty."""
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = True
        c = _mod["colorize"](True)
        assert c["green"] == "\033[32m"
        assert c["red"] == "\033[31m"


def test_colorize_no_tty():
    """colorize returns blank when not a tty."""
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = False
        c = _mod["colorize"](True)
        assert c["green"] == ""


# ── Integration: run() with mocked data ───────────────────────────────


def test_run_with_sample_data(tmp_path, capsys):
    """run() prints all four sections with sample data."""
    jsonl = tmp_path / "golem.jsonl"
    jsonl.write_text(
        '{"ts":"2026-01-01T00:00:00Z","provider":"zhipu","duration":120,"exit":0,"turns":10,"prompt":"test","tail":"ok","files_created":1,"tests_passed":2,"tests_failed":0,"pytest_exit":0}\n'
        '{"ts":"2026-01-01T00:05:00Z","provider":"zhipu","duration":60,"exit":1,"turns":5,"prompt":"fail","tail":"err","files_created":0,"tests_passed":0,"tests_failed":1,"pytest_exit":1}\n'
        '{"ts":"2026-01-01T00:10:00Z","provider":"volcano","duration":30,"exit":0,"turns":3,"prompt":"fast","tail":"done","files_created":1,"tests_passed":1,"tests_failed":0,"pytest_exit":0}\n'
    )

    queue = tmp_path / "golem-queue.md"
    queue.write_text(
        "- [ ] `golem --provider zhipu \"pending task\"`\n"
        "- [x] `golem --provider zhipu \"done task\"` → exit=0\n"
        "- [!] `golem --provider volcano \"failed task\"`\n"
    )

    orig_jsonl = _mod["JSONL_FILE"]
    orig_queue = _mod["QUEUE_FILE"]
    try:
        _mod["JSONL_FILE"] = jsonl
        _mod["QUEUE_FILE"] = queue
        rc = run(["--no-color"])
    finally:
        _mod["JSONL_FILE"] = orig_jsonl
        _mod["QUEUE_FILE"] = orig_queue

    assert rc == 0
    out = capsys.readouterr().out

    # Section headers should appear
    assert "Provider Stats" in out
    assert "Queue Status" in out
    assert "Last 5 Completed" in out
    assert "Disk Free" in out

    # Provider stats should show zhipu and volcano
    assert "zhipu" in out
    assert "volcano" in out

    # Queue counts
    assert "Pending:" in out
    assert "Done:" in out
    assert "Failed:" in out


def test_run_empty_data(tmp_path, capsys):
    """run() handles missing files gracefully."""
    orig_jsonl = _mod["JSONL_FILE"]
    orig_queue = _mod["QUEUE_FILE"]
    try:
        _mod["JSONL_FILE"] = tmp_path / "nope.jsonl"
        _mod["QUEUE_FILE"] = tmp_path / "nope.md"
        rc = run(["--no-color"])
    finally:
        _mod["JSONL_FILE"] = orig_jsonl
        _mod["QUEUE_FILE"] = orig_queue

    assert rc == 0
    out = capsys.readouterr().out
    assert "Provider Stats" in out
    assert "no completed tasks" in out


def test_run_help(capsys):
    """run() with --help prints docstring."""
    rc = run(["--help"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "golem-dash" in out
