"""Tests for effectors/log-summary — golem-daemon log analyzer."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest


def _load_module():
    """Load log-summary by exec-ing its source."""
    source = Path("/home/terry/germline/effectors/log-summary").read_text()
    ns: dict = {"__name__": "log_summary"}
    exec(source, ns)
    return ns


_mod = _load_module()
parse_timestamp = _mod["parse_timestamp"]
read_log_lines = _mod["read_log_lines"]
classify_events = _mod["classify_events"]
window_filter = _mod["window_filter"]
compute_window_stats = _mod["compute_window_stats"]
format_report = _mod["format_report"]
run = _mod["run"]


SAMPLE_LOG = """\
[2026-03-31 10:00:00] Daemon started
[2026-03-31 10:00:01] Queued [infini]: golem --provider infini --max-turns 50 "Do task A"
[2026-03-31 10:00:01] Starting: golem --provider infini --max-turns 50 "Do task A"
[2026-03-31 10:00:01] Running: 1 tasks (infini:1), 0 pending
[2026-03-31 10:03:21] Finished (200s, exit=0): golem --provider infini --max-turns 50 "Do task A..."
[2026-03-31 10:03:22] Queued [volcano]: golem --provider volcano --max-turns 20 "Health-check effectors/foo"
[2026-03-31 10:03:22] Starting: golem --provider volcano --max-turns 20 "Health-check effectors/foo"
[2026-03-31 10:05:00] Finished (98s, exit=1): golem --provider volcano --max-turns 20 "Health-check effectors/foo..."
[2026-03-31 10:05:01] FAILED (exit=1): golem --provider volcano --max-turns 20 "Health-check effectors/foo..."
[2026-03-31 10:05:10] Re-queued (retry): golem --provider volcano --max-turns 20 "Health-check effectors/foo..."
[2026-03-31 10:10:00] TIMEOUT (1800s): golem --provider zhipu --max-turns 50 "Slow task..."
[2026-03-31 10:10:05] FAILED (exit=127): golem --provider zhipu --max-turns 50 "Slow task..."
[2026-03-31 10:10:06] FAILED (exit=2): golem --provider infini "Bad command..."
[2026-03-31 10:11:00] ERROR: subprocess failed unexpectedly
[2026-03-31 10:12:00] auto-commit (5 tasks): abc1234
[2026-03-31 10:13:00] WARNING: Low disk space (0.50GB free), pausing task dispatch
[2026-03-31 10:14:00] Idle: 0 pending
[2026-03-31 10:15:00] Daemon stopped
[2026-03-31 10:20:00] Fatal error: disk full
"""


@pytest.fixture
def log_file(tmp_path):
    """Write sample log to a temp file and return its path."""
    p = tmp_path / "golem-daemon.log"
    p.write_text(SAMPLE_LOG)
    return p


def _read_lines_from(path: Path):
    """Read log lines by patching module globals directly."""
    old_main = _mod["LOGFILE"]
    old_rotated = _mod["ROTATED_LOGFILE"]
    _mod["LOGFILE"] = path
    _mod["ROTATED_LOGFILE"] = Path(str(path) + ".1")
    try:
        return _mod["read_log_lines"]()
    finally:
        _mod["LOGFILE"] = old_main
        _mod["ROTATED_LOGFILE"] = old_rotated


# ── parse_timestamp ──────────────────────────────────────────────


def test_parse_timestamp_valid():
    """parse_timestamp returns correct datetime."""
    dt = parse_timestamp("2026-03-31 10:05:01")
    assert dt.year == 2026
    assert dt.month == 3
    assert dt.day == 31
    assert dt.hour == 10
    assert dt.minute == 5
    assert dt.second == 1


def test_parse_timestamp_invalid_raises():
    """parse_timestamp raises ValueError on bad input."""
    with pytest.raises(ValueError):
        parse_timestamp("not-a-date")


# ── read_log_lines ───────────────────────────────────────────────


def test_read_log_lines_empty(tmp_path):
    """read_log_lines returns empty list when no log file exists."""
    output = run(logpath=tmp_path / "missing.log")
    assert "No log entries" in output


def test_read_log_lines_merges_rotated(log_file):
    """read_log_lines merges main and rotated log files."""
    rotated = Path(str(log_file) + ".1")
    rotated.write_text("[2026-03-30 09:00:00] Daemon started\n")
    entries = _read_lines_from(log_file)
    # Should have entries from both files
    assert len(entries) > 20  # 19 from SAMPLE_LOG + 1 from rotated
    # Rotated entry should come first (sorted by timestamp)
    assert entries[0][1] == "Daemon started"
    assert entries[0][0].day == 30


# ── classify_events ──────────────────────────────────────────────


def test_classify_events_counts(log_file):
    """classify_events correctly categorizes all event types."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    assert len(events["starts"]) == 3
    assert len(events["finishes"]) == 2
    assert len(events["failures"]) == 3
    assert len(events["timeouts"]) == 1
    assert len(events["errors"]) == 1
    assert len(events["queued"]) == 2
    assert len(events["running"]) == 1
    assert len(events["idle"]) == 1
    assert len(events["daemon"]) == 2
    assert len(events["autocommits"]) == 1
    assert len(events["warnings"]) == 1
    assert len(events["fatals"]) == 1


def test_classify_events_finish_details(log_file):
    """classify_events captures duration and exit code from finishes."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    first_finish = events["finishes"][0]
    assert first_finish[1] == 200  # duration_s
    assert first_finish[2] == 0    # exit_code
    second_finish = events["finishes"][1]
    assert second_finish[1] == 98
    assert second_finish[2] == 1


def test_classify_events_failure_exit_codes(log_file):
    """classify_events captures exit codes from failures."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    codes = {f[1] for f in events["failures"]}
    assert 1 in codes
    assert 127 in codes
    assert 2 in codes


def test_classify_events_autocommit(log_file):
    """classify_events captures auto-commit details."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    ac = events["autocommits"][0]
    assert ac[1] == 5          # n_tasks
    assert ac[2] == "abc1234"  # hash


# ── window_filter ────────────────────────────────────────────────


def test_window_filter_includes_at_cutoff():
    """window_filter keeps items at or after cutoff."""
    items = [
        (datetime(2026, 3, 31, 9, 0), "old"),
        (datetime(2026, 3, 31, 10, 0), "new"),
    ]
    cutoff = datetime(2026, 3, 31, 10, 0)
    result = window_filter(items, 0, cutoff)
    assert len(result) == 1
    assert result[0][1] == "new"


def test_window_filter_excludes_before_cutoff():
    """window_filter excludes items before cutoff."""
    items = [
        (datetime(2026, 3, 31, 9, 0), "old"),
    ]
    cutoff = datetime(2026, 3, 31, 10, 0)
    result = window_filter(items, 0, cutoff)
    assert len(result) == 0


def test_window_filter_empty():
    """window_filter returns empty list for empty input."""
    result = window_filter([], 0, datetime(2026, 3, 31, 10, 0))
    assert result == []


# ── compute_window_stats ─────────────────────────────────────────


def test_compute_window_stats_full_window(log_file):
    """compute_window_stats produces correct counts for the full sample."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    cutoff = datetime(2026, 3, 30, 0, 0)
    stats = compute_window_stats(events, "24h", cutoff)
    assert stats["tasks_started"] == 3
    assert stats["tasks_finished"] == 2
    assert stats["tasks_succeeded"] == 1
    assert stats["tasks_failed"] == 4   # 3 explicit failures + 1 finish exit=1
    assert stats["tasks_timed_out"] == 1


def test_compute_window_stats_failure_rate(log_file):
    """compute_window_stats computes correct failure rate."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    cutoff = datetime(2026, 3, 30, 0, 0)
    stats = compute_window_stats(events, "24h", cutoff)
    # 4 failed / 2 finished = 200%
    assert stats["failure_rate_pct"] == 200.0


def test_compute_window_stats_avg_duration(log_file):
    """compute_window_stats computes avg duration from successful finishes."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    cutoff = datetime(2026, 3, 30, 0, 0)
    stats = compute_window_stats(events, "24h", cutoff)
    # Only 1 success with duration 200s
    assert stats["avg_duration_s"] == 200.0


def test_compute_window_stats_top_errors(log_file):
    """compute_window_stats reports top error patterns."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    cutoff = datetime(2026, 3, 30, 0, 0)
    stats = compute_window_stats(events, "24h", cutoff)
    assert len(stats["top_errors"]) > 0
    error_descs = [desc for desc, _ in stats["top_errors"]]
    assert any("exit=1" in d for d in error_descs)
    assert any("timeout" in d for d in error_descs)


def test_compute_window_stats_providers(log_file):
    """compute_window_stats reports provider breakdown."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    cutoff = datetime(2026, 3, 30, 0, 0)
    stats = compute_window_stats(events, "24h", cutoff)
    assert "infini" in stats["providers"]
    assert "volcano" in stats["providers"]


def test_compute_window_stats_autocommits(log_file):
    """compute_window_stats counts auto-commits."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    cutoff = datetime(2026, 3, 30, 0, 0)
    stats = compute_window_stats(events, "24h", cutoff)
    assert stats["autocommits"] == 1
    assert stats["autocommit_tasks"] == 5


def test_compute_window_stats_warnings(log_file):
    """compute_window_stats counts warnings."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    cutoff = datetime(2026, 3, 30, 0, 0)
    stats = compute_window_stats(events, "24h", cutoff)
    assert stats["warnings"] == 1


def test_compute_window_stats_narrow_window_excludes(log_file):
    """compute_window_stats with narrow window excludes old entries."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    cutoff = datetime(2026, 3, 31, 10, 15)
    stats = compute_window_stats(events, "narrow", cutoff)
    assert stats["tasks_started"] == 0
    assert stats["tasks_finished"] == 0


def test_compute_window_stats_empty_events():
    """compute_window_stats handles empty events gracefully."""
    empty = {
        "starts": [], "finishes": [], "failures": [], "timeouts": [],
        "errors": [], "queued": [], "running": [], "idle": [],
        "daemon": [], "autocommits": [], "warnings": [], "fatals": [],
    }
    stats = compute_window_stats(empty, "1h", datetime(2026, 1, 1))
    assert stats["tasks_started"] == 0
    assert stats["failure_rate_pct"] == 0.0
    assert stats["avg_duration_s"] == 0


# ── format_report ────────────────────────────────────────────────


def test_format_report_single_window(log_file):
    """format_report renders a single window correctly."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    cutoff = datetime(2026, 3, 30, 0, 0)
    stats = compute_window_stats(events, "24h", cutoff)
    report = format_report([stats])
    assert "24h" in report
    assert "Tasks started:" in report
    assert "succeeded:" in report
    assert "failed:" in report
    assert "Failure rate:" in report
    assert "Avg duration:" in report
    assert "Top errors:" in report


def test_format_report_multiple_windows_includes_trend(log_file):
    """format_report includes failure rate trend for multiple windows."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    s1 = compute_window_stats(events, "1h", datetime(2026, 3, 31, 9, 20))
    s6 = compute_window_stats(events, "6h", datetime(2026, 3, 31, 4, 20))
    report = format_report([s1, s6])
    assert "Failure rate trend" in report


def test_format_report_single_window_no_trend(log_file):
    """format_report skips trend section for a single window."""
    entries = _read_lines_from(log_file)
    events = classify_events(entries)
    stats = compute_window_stats(events, "24h", datetime(2026, 3, 30, 0, 0))
    report = format_report([stats])
    assert "Failure rate trend" not in report


# ── run() integration tests ──────────────────────────────────────


def test_run_human_readable(log_file):
    """run() returns human-readable report by default."""
    output = run(logpath=log_file)
    assert isinstance(output, str)
    assert "GOLEM DAEMON LOG SUMMARY" in output
    assert "1h" in output
    assert "6h" in output
    assert "24h" in output


def test_run_json_output(log_file):
    """run() returns valid JSON when as_json=True."""
    output = run(logpath=log_file, as_json=True)
    data = json.loads(output)
    assert isinstance(data, list)
    assert len(data) == 3
    for item in data:
        assert "window" in item
        assert "tasks_started" in item
        assert "failure_rate_pct" in item
        assert "top_errors" in item


def test_run_single_window(log_file):
    """run() with window= returns a single window report."""
    output = run(logpath=log_file, window="1h")
    assert "1h" in output


def test_run_no_log_file(tmp_path):
    """run() handles missing log file gracefully."""
    output = run(logpath=tmp_path / "missing.log")
    assert "No log entries" in output


def test_run_unknown_window(log_file):
    """run() rejects unknown window names."""
    output = run(logpath=log_file, window="99h")
    assert "Unknown window" in output


# ── main() CLI tests ─────────────────────────────────────────────


def test_main_default(capsys, log_file):
    """main() prints full report by default."""
    _mod["LOGFILE"] = log_file
    _mod["ROTATED_LOGFILE"] = Path(str(log_file) + ".1")
    _mod["sys"] = _mod["sys"]  # ensure sys is the real module
    try:
        rc = _mod["main"]()
    finally:
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"
        _mod["ROTATED_LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log.1"
    assert rc == 0
    captured = capsys.readouterr().out
    assert "GOLEM DAEMON LOG SUMMARY" in captured


def test_main_json_flag(capsys, log_file):
    """main() --json outputs valid JSON."""
    import sys as real_sys
    _mod["LOGFILE"] = log_file
    _mod["ROTATED_LOGFILE"] = Path(str(log_file) + ".1")
    old_argv = real_sys.argv
    real_sys.argv = ["log-summary", "--json"]
    try:
        rc = _mod["main"]()
    finally:
        real_sys.argv = old_argv
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"
        _mod["ROTATED_LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log.1"
    assert rc == 0
    output = capsys.readouterr().out
    data = json.loads(output)
    assert isinstance(data, list)


def test_main_window_flag(capsys, log_file):
    """main() --window=6h selects a single window."""
    import sys as real_sys
    _mod["LOGFILE"] = log_file
    _mod["ROTATED_LOGFILE"] = Path(str(log_file) + ".1")
    old_argv = real_sys.argv
    real_sys.argv = ["log-summary", "--window=6h"]
    try:
        rc = _mod["main"]()
    finally:
        real_sys.argv = old_argv
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"
        _mod["ROTATED_LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log.1"
    assert rc == 0
    captured = capsys.readouterr().out
    assert "6h" in captured


def test_main_bad_window(capsys, log_file):
    """main() rejects unknown window values."""
    import sys as real_sys
    _mod["LOGFILE"] = log_file
    _mod["ROTATED_LOGFILE"] = Path(str(log_file) + ".1")
    old_argv = real_sys.argv
    real_sys.argv = ["log-summary", "--window=99h"]
    try:
        rc = _mod["main"]()
    finally:
        real_sys.argv = old_argv
        _mod["LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log"
        _mod["ROTATED_LOGFILE"] = Path.home() / ".local" / "share" / "vivesca" / "golem-daemon.log.1"
    assert rc == 1
