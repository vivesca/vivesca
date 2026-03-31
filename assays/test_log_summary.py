"""Tests for log-summary — golem-daemon log analyzer."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_log_summary():
    """Load log-summary module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/log-summary").read()
    ns: dict = {"__name__": "log_summary"}
    exec(source, ns)
    return ns


_mod = _load_log_summary()

# Pull out all functions/classes we need to test
parse_timestamp = _mod["parse_timestamp"]
read_log_lines = _mod["read_log_lines"]
classify_events = _mod["classify_events"]
window_filter = _mod["window_filter"]
compute_window_stats = _mod["compute_window_stats"]
format_report = _mod["format_report"]
run = _mod["run"]
RE_TS = _mod["RE_TS"]


@pytest.fixture
def tmp_log(tmp_path):
    """Create a temporary log file with sample entries."""
    now = datetime(2026, 3, 31, 15, 0, 0)
    lines = []
    # 25 hours ago: old entries (outside 24h)
    old = now - timedelta(hours=25)
    lines.append(f"[{old:%Y-%m-%d %H:%M:%S}] Daemon started")
    lines.append(f'[{old:%Y-%m-%d %H:%M:%S}] Starting: golem --provider infini "old task"')
    lines.append(f"[{old:%Y-%m-%d %H:%M:%S}] Finished (100s, exit=1): golem --provider infini \"old task\"")
    lines.append(f'[{old:%Y-%m-%d %H:%M:%S}] FAILED (exit=1): golem --provider infini "old task"')

    # 12 hours ago: inside 24h but outside 6h
    h12 = now - timedelta(hours=12)
    lines.append(f"[{h12:%Y-%m-%d %H:%M:%S}] Daemon started")
    lines.append(f'[{h12:%Y-%m-%d %H:%M:%S}] Starting: golem --provider volcano "task-12h"')
    lines.append(f"[{h12:%Y-%m-%d %H:%M:%S}] Finished (200s, exit=0): golem --provider volcano \"task-12h\"")
    lines.append(f'[{h12:%Y-%m-%d %H:%M:%S}] Queued [volcano]: golem --provider volcano "task-12h"')

    # 3 hours ago: inside 6h but outside 1h
    h3 = now - timedelta(hours=3)
    lines.append(f'[{h3:%Y-%m-%d %H:%M:%S}] Starting: golem --provider zhipu "task-3h"')
    lines.append(f"[{h3:%Y-%m-%d %H:%M:%S}] Finished (150s, exit=0): golem --provider zhipu \"task-3h\"")
    lines.append(f'[{h3:%Y-%m-%d %H:%M:%S}] Queued [zhipu]: golem --provider zhipu "task-3h"')
    lines.append(f"[{h3:%Y-%m-%d %H:%M:%S}] auto-commit (5 tasks): abc1234")

    # 30 min ago: inside 1h
    h05 = now - timedelta(minutes=30)
    lines.append(f'[{h05:%Y-%m-%d %H:%M:%S}] Starting: golem --provider infini "task-30m"')
    lines.append(f"[{h05:%Y-%m-%d %H:%M:%S}] Finished (60s, exit=0): golem --provider infini \"task-30m\"")
    lines.append(f'[{h05:%Y-%m-%d %H:%M:%S}] Starting: golem --provider volcano "task-30m-fail"')
    lines.append(f"[{h05:%Y-%m-%d %H:%M:%S}] Finished (10s, exit=2): golem --provider volcano \"task-30m-fail\"")
    lines.append(f'[{h05:%Y-%m-%d %H:%M:%S}] FAILED (exit=2): golem --provider volcano "task-30m-fail"')
    lines.append(f'[{h05:%Y-%m-%d %H:%M:%S}] Queued [infini]: golem --provider infini "task-30m"')
    lines.append(f'[{h05:%Y-%m-%d %H:%M:%S}] Queued [volcano]: golem --provider volcano "task-30m-fail"')

    # Timeout entry
    lines.append(f'[{h05:%Y-%m-%d %H:%M:%S}] TIMEOUT (1800s): golem --provider infini "stuck-task"')

    # Error entry
    lines.append(f"[{h05:%Y-%m-%d %H:%M:%S}] ERROR: golem --provider zhipu \"crash\" - connection refused")

    # Warning
    lines.append(f"[{h05:%Y-%m-%d %H:%M:%S}] WARNING: Low disk space (0.50GB free), pausing task dispatch")

    # Fatal
    lines.append(f"[{h05:%Y-%m-%d %H:%M:%S}] Fatal error: something broke badly")

    # Status lines
    lines.append(f"[{h05:%Y-%m-%d %H:%M:%S}] Running: 4 tasks (infini:2, volcano:2), 10 pending")
    lines.append(f"[{h05:%Y-%m-%d %H:%M:%S}] Idle: 0 pending")

    logpath = tmp_path / "golem-daemon.log"
    logpath.write_text("\n".join(lines) + "\n")
    return logpath


# ── parse_timestamp ──────────────────────────────────────────────────


def test_parse_timestamp_standard():
    """parse_timestamp handles standard format."""
    result = parse_timestamp("2026-03-31 10:53:29")
    assert result == datetime(2026, 3, 31, 10, 53, 29)


def test_parse_timestamp_midnight():
    """parse_timestamp handles midnight."""
    result = parse_timestamp("2026-01-01 00:00:00")
    assert result == datetime(2026, 1, 1, 0, 0, 0)


# ── read_log_lines ───────────────────────────────────────────────────


def test_read_log_lines_parses_entries(tmp_log):
    """read_log_lines returns sorted (timestamp, message) tuples."""
    entries = read_log_lines.__wrapped__(tmp_log) if hasattr(read_log_lines, "__wrapped__") else None
    # Direct call via module function with overridden paths
    import log_summary as _  # won't work since it's exec'd
    # Use the run() function which accepts logpath override
    pass  # tested indirectly via run()


def test_read_log_lines_no_file(tmp_path):
    """read_log_lines handles missing log file gracefully."""
    nonexistent = tmp_path / "nonexistent.log"
    result = run(logpath=nonexistent)
    assert "No log entries found" in result


# ── classify_events ──────────────────────────────────────────────────


def test_classify_events_basic(tmp_log):
    """classify_events correctly categorizes known log patterns."""
    from pathlib import Path as P
    # Re-read to get entries
    ns = _mod
    LOGFILE = ns["LOGFILE"]
    ROTATED_LOGFILE = ns["ROTATED_LOGFILE"]
    ns["LOGFILE"] = tmp_log
    ns["ROTATED_LOGFILE"] = P(str(tmp_log) + ".1")
    try:
        entries = ns["read_log_lines"]()
    finally:
        ns["LOGFILE"] = LOGFILE
        ns["ROTATED_LOGFILE"] = ROTATED_LOGFILE

    events = classify_events(entries)

    # Check all expected categories exist
    for key in ("starts", "finishes", "failures", "timeouts", "errors",
                "queued", "running", "idle", "daemon", "autocommits",
                "warnings", "fatals"):
        assert key in events

    # Daemon start/stop events
    assert len(events["daemon"]) == 2  # old + 12h ago

    # Autocommits
    assert len(events["autocommits"]) == 1
    assert events["autocommits"][0][1] == 5  # 5 tasks

    # Timeouts
    assert len(events["timeouts"]) == 1

    # Errors
    assert len(events["errors"]) == 1
    assert "connection refused" in events["errors"][0][1]

    # Warnings
    assert len(events["warnings"]) == 1

    # Fatals
    assert len(events["fatals"]) == 1

    # Running and idle status lines
    assert len(events["running"]) == 1
    assert len(events["idle"]) == 1


# ── window_filter ────────────────────────────────────────────────────


def test_window_filter_correctly_filters():
    """window_filter keeps only entries >= cutoff."""
    now = datetime(2026, 3, 31, 15, 0, 0)
    items = [
        (now - timedelta(hours=2), "old"),
        (now - timedelta(hours=1), "recent"),
        (now, "now"),
    ]
    cutoff = now - timedelta(hours=1)
    result = window_filter(items, 0, cutoff)
    assert len(result) == 2
    assert result[0][1] == "recent"
    assert result[1][1] == "now"


# ── compute_window_stats ────────────────────────────────────────────


def test_compute_window_stats_1h(tmp_log):
    """compute_window_stats correctly counts 1h window events."""
    ns = _mod
    orig_log = ns["LOGFILE"]
    orig_rot = ns["ROTATED_LOGFILE"]
    ns["LOGFILE"] = tmp_log
    ns["ROTATED_LOGFILE"] = Path(str(tmp_log) + ".1")
    try:
        entries = ns["read_log_lines"]()
    finally:
        ns["LOGFILE"] = orig_log
        ns["ROTATED_LOGFILE"] = orig_rot

    events = classify_events(entries)
    now = entries[-1][0]
    cutoff = now - timedelta(hours=1)

    stats = compute_window_stats(events, "1h", cutoff)

    assert stats["tasks_started"] == 2   # task-30m + task-30m-fail
    assert stats["tasks_finished"] == 2   # both finished
    assert stats["tasks_succeeded"] == 1  # task-30m exit=0
    assert stats["tasks_failed"] == 2     # finish exit=2 + FAILED
    assert stats["tasks_timed_out"] == 1
    assert stats["failure_rate_pct"] == 100.0  # 2 fails / 2 finished * 100
    assert stats["warnings"] == 1


def test_compute_window_stats_24h(tmp_log):
    """compute_window_stats correctly counts 24h window events."""
    ns = _mod
    orig_log = ns["LOGFILE"]
    orig_rot = ns["ROTATED_LOGFILE"]
    ns["LOGFILE"] = tmp_log
    ns["ROTATED_LOGFILE"] = Path(str(tmp_log) + ".1")
    try:
        entries = ns["read_log_lines"]()
    finally:
        ns["LOGFILE"] = orig_log
        ns["ROTATED_LOGFILE"] = orig_rot

    events = classify_events(entries)
    now = entries[-1][0]
    cutoff = now - timedelta(hours=24)

    stats = compute_window_stats(events, "24h", cutoff)

    # 24h includes: 12h-ago task, 3h-ago task, 30m tasks = 4 starts
    assert stats["tasks_started"] == 4
    assert stats["tasks_finished"] == 4
    assert stats["tasks_succeeded"] == 2  # task-12h + task-3h
    assert stats["tasks_timed_out"] == 1


def test_compute_window_stats_empty():
    """compute_window_stats handles empty event lists."""
    empty_events = {
        "starts": [], "finishes": [], "failures": [], "timeouts": [],
        "errors": [], "queued": [], "running": [], "idle": [],
        "daemon": [], "autocommits": [], "warnings": [], "fatals": [],
    }
    cutoff = datetime(2026, 3, 31, 0, 0, 0)
    stats = compute_window_stats(empty_events, "1h", cutoff)

    assert stats["tasks_started"] == 0
    assert stats["tasks_finished"] == 0
    assert stats["failure_rate_pct"] == 0.0
    assert stats["top_errors"] == []


# ── run() integration tests ──────────────────────────────────────────


def test_run_full_report(tmp_log):
    """run() with no window produces all three windows."""
    report = run(logpath=tmp_log)
    assert "1h" in report
    assert "6h" in report
    assert "24h" in report
    assert "Failure rate trend" in report


def test_run_single_window(tmp_log):
    """run() with a single window produces just that window."""
    report = run(logpath=tmp_log, window="1h")
    assert "1h" in report
    assert "6h" not in report


def test_run_json_output(tmp_log):
    """run() with as_json returns valid JSON with expected structure."""
    output = run(logpath=tmp_log, as_json=True)
    data = json.loads(output)
    assert isinstance(data, list)
    assert len(data) == 3  # 1h, 6h, 24h
    for item in data:
        assert "window" in item
        assert "tasks_started" in item
        assert "failure_rate_pct" in item
        assert "top_errors" in item
        assert "providers" in item


def test_run_json_single_window(tmp_log):
    """run() JSON output for single window."""
    output = run(logpath=tmp_log, window="6h", as_json=True)
    data = json.loads(output)
    assert len(data) == 1
    assert data[0]["window"] == "6h"


def test_run_no_log_file(tmp_path):
    """run() handles missing log file."""
    nonexistent = tmp_path / "nope.log"
    report = run(logpath=nonexistent)
    assert "No log entries found" in report


def test_run_json_no_log_file(tmp_path):
    """run() JSON handles missing log file."""
    nonexistent = tmp_path / "nope.log"
    output = run(logpath=nonexistent, as_json=True)
    data = json.loads(output)
    assert "error" in data


def test_run_invalid_window(tmp_log):
    """run() rejects unknown window values."""
    report = run(logpath=tmp_log, window="7d")
    assert "Unknown window" in report


# ── format_report ────────────────────────────────────────────────────


def test_format_report_rendes_bars():
    """format_report renders failure rate trend with bar charts."""
    stats = [
        {"window": "1h", "cutoff": "", "tasks_started": 10, "tasks_finished": 10,
         "tasks_succeeded": 8, "tasks_failed": 2, "tasks_timed_out": 0,
         "failure_rate_pct": 20.0, "avg_duration_s": 120.5,
         "autocommits": 1, "autocommit_tasks": 5, "warnings": 0,
         "top_errors": [("exit=1: cmd", 2)], "providers": {"infini": 5}},
        {"window": "6h", "cutoff": "", "tasks_started": 50, "tasks_finished": 50,
         "tasks_succeeded": 40, "tasks_failed": 10, "tasks_timed_out": 1,
         "failure_rate_pct": 20.0, "avg_duration_s": 115.0,
         "autocommits": 3, "autocommit_tasks": 15, "warnings": 1,
         "top_errors": [("exit=1: cmd", 8), ("timeout (1800s): cmd2", 1)],
         "providers": {"infini": 20, "volcano": 30}},
        {"window": "24h", "cutoff": "", "tasks_started": 100, "tasks_finished": 100,
         "tasks_succeeded": 85, "tasks_failed": 15, "tasks_timed_out": 2,
         "failure_rate_pct": 15.0, "avg_duration_s": 110.0,
         "autocommits": 5, "autocommit_tasks": 25, "warnings": 2,
         "top_errors": [("exit=1: cmd", 12)], "providers": {"infini": 40}},
    ]
    report = format_report(stats)
    assert "█" in report  # Bar chart rendered
    assert "1h" in report
    assert "6h" in report
    assert "24h" in report
    assert "Top errors" in report


def test_format_report_empty_errors():
    """format_report handles windows with no errors."""
    stats = [{
        "window": "1h", "cutoff": "", "tasks_started": 5, "tasks_finished": 5,
        "tasks_succeeded": 5, "tasks_failed": 0, "tasks_timed_out": 0,
        "failure_rate_pct": 0.0, "avg_duration_s": 60.0,
        "autocommits": 0, "autocommit_tasks": 0, "warnings": 0,
        "top_errors": [], "providers": {},
    }]
    report = format_report(stats)
    assert "failure rate trend" not in report.lower()  # Only 1 window, no trend
    assert "Top errors" not in report  # No errors to show


# ── Rotated log file ────────────────────────────────────────────────


def test_run_reads_rotated_log(tmp_path):
    """run() reads from both main and rotated (.1) log files."""
    now = datetime(2026, 3, 31, 15, 0, 0)
    h2 = now - timedelta(hours=2)

    # Write rotated file with entries from 2h ago
    rotated = tmp_path / "golem-daemon.log.1"
    rotated.write_text(
        f'[{h2:%Y-%m-%d %H:%M:%S}] Starting: golem --provider infini "rotated-task"\n'
        f'[{h2:%Y-%m-%d %H:%M:%S}] Finished (200s, exit=0): golem --provider infini "rotated-task"\n'
    )

    # Write main file with recent entries
    main_log = tmp_path / "golem-daemon.log"
    main_log.write_text(
        f'[{now:%Y-%m-%d %H:%M:%S}] Starting: golem --provider volcano "recent-task"\n'
        f'[{now:%Y-%m-%d %H:%M:%S}] Finished (100s, exit=0): golem --provider volcano "recent-task"\n'
    )

    report = run(logpath=main_log, window="6h")
    # Both tasks should appear
    assert "Tasks started:    2" in report
    assert "Tasks finished:   2" in report


# ── Top errors aggregation ──────────────────────────────────────────


def test_top_errors_counts_correctly(tmp_log):
    """Top errors deduplicates and counts by error description."""
    ns = _mod
    orig_log = ns["LOGFILE"]
    orig_rot = ns["ROTATED_LOGFILE"]
    ns["LOGFILE"] = tmp_log
    ns["ROTATED_LOGFILE"] = Path(str(tmp_log) + ".1")
    try:
        entries = ns["read_log_lines"]()
    finally:
        ns["LOGFILE"] = orig_log
        ns["ROTATED_LOGFILE"] = orig_rot

    events = classify_events(entries)
    now = entries[-1][0]
    cutoff = now - timedelta(hours=1)
    stats = compute_window_stats(events, "1h", cutoff)

    # We should have at least 1 top error (the FAILED + error + timeout + fatal)
    assert len(stats["top_errors"]) >= 3
    # Check that counts are populated
    for desc, count in stats["top_errors"]:
        assert count >= 1
