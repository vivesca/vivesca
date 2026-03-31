"""Tests for effectors/log-summary — golem-daemon log analyzer."""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest


def _load_log_summary():
    """Load log-summary module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/log-summary").read()
    ns: dict = {"__name__": "log_summary"}
    exec(source, ns)
    return ns


_mod = _load_log_summary()
parse_log = _mod["parse_log"]
task_counts = _mod["task_counts"]
failure_rate_trend = _mod["failure_rate_trend"]
top_errors = _mod["top_errors"]
format_summary = _mod["format_summary"]
format_json = _mod["format_json"]


# ── Helpers ─────────────────────────────────────────────────────────────


def _make_log(tmp_path: Path, lines: list[str]) -> Path:
    """Write log lines to a temp file and return its path."""
    logfile = tmp_path / "golem-daemon.log"
    logfile.write_text("\n".join(lines) + "\n")
    return logfile


def _ts(minutes_ago: int = 0) -> str:
    """Return a timestamp string N minutes ago from now."""
    ts = datetime.now() - timedelta(minutes=minutes_ago)
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def _starting_line(minutes_ago: int, provider: str = "infini") -> str:
    return f"[{_ts(minutes_ago)}] Starting: golem --provider {provider} \"task\""


def _finished_line(minutes_ago: int, duration: int = 100, exit_code: int = 0, provider: str = "infini") -> str:
    return (
        f"[{_ts(minutes_ago)}] Finished ({duration}s, exit={exit_code}): "
        f"golem --provider {provider} \"task\""
    )


def _failed_line(minutes_ago: int, exit_code: int = 1, provider: str = "infini") -> str:
    return (
        f"[{_ts(minutes_ago)}] FAILED (exit={exit_code}): "
        f"golem --provider {provider} \"task\""
    )


def _timeout_line(minutes_ago: int, provider: str = "infini") -> str:
    return (
        f"[{_ts(minutes_ago)}] TIMEOUT (1800s): "
        f"golem --provider {provider} \"long task\""
    )


def _idle_line(minutes_ago: int) -> str:
    return f"[{_ts(minutes_ago)}] Idle: 0 pending"


def _error_line(minutes_ago: int) -> str:
    return f"[{_ts(minutes_ago)}] ERROR: golem --provider infini \"task\" - something broke"


# ── parse_log tests ─────────────────────────────────────────────────────


class TestParseLog:
    def test_parse_finished_entry(self, tmp_path):
        """parse_log extracts Finished entries with duration and exit_code."""
        logfile = _make_log(tmp_path, [_finished_line(0, duration=200, exit_code=0)])
        entries = parse_log(logfile)
        assert len(entries) == 1
        assert entries[0]["type"] == "finished"
        assert entries[0]["duration"] == 200
        assert entries[0]["exit_code"] == 0
        assert entries[0]["provider"] == "infini"

    def test_parse_failed_entry(self, tmp_path):
        """parse_log extracts FAILED entries with exit_code."""
        logfile = _make_log(tmp_path, [_failed_line(5, exit_code=1)])
        entries = parse_log(logfile)
        assert len(entries) == 1
        assert entries[0]["type"] == "failed"
        assert entries[0]["exit_code"] == 1

    def test_parse_timeout_entry(self, tmp_path):
        """parse_log extracts TIMEOUT entries with duration."""
        logfile = _make_log(tmp_path, [_timeout_line(10)])
        entries = parse_log(logfile)
        assert len(entries) == 1
        assert entries[0]["type"] == "timeout"
        assert entries[0]["duration"] == 1800

    def test_parse_starting_entry(self, tmp_path):
        """parse_log extracts Starting entries."""
        logfile = _make_log(tmp_path, [_starting_line(0)])
        entries = parse_log(logfile)
        assert len(entries) == 1
        assert entries[0]["type"] == "starting"
        assert entries[0]["provider"] == "infini"

    def test_parse_error_entry(self, tmp_path):
        """parse_log extracts ERROR entries."""
        logfile = _make_log(tmp_path, [_error_line(0)])
        entries = parse_log(logfile)
        assert len(entries) == 1
        assert entries[0]["type"] == "error"

    def test_parse_idle_entry(self, tmp_path):
        """parse_log classifies Idle as 'other'."""
        logfile = _make_log(tmp_path, [_idle_line(0)])
        entries = parse_log(logfile)
        assert len(entries) == 1
        assert entries[0]["type"] == "other"

    def test_parse_empty_file(self, tmp_path):
        """parse_log returns empty list for empty file."""
        logfile = _make_log(tmp_path, [])
        entries = parse_log(logfile)
        assert entries == []

    def test_parse_nonexistent_file(self, tmp_path):
        """parse_log returns empty list for missing file."""
        entries = parse_log(tmp_path / "nonexistent.log")
        assert entries == []

    def test_parse_malformed_line_skipped(self, tmp_path):
        """parse_log skips lines that don't match the timestamp format."""
        logfile = _make_log(tmp_path, [
            "this is not a log line",
            _finished_line(0),
        ])
        entries = parse_log(logfile)
        assert len(entries) == 1

    def test_parse_provider_extraction(self, tmp_path):
        """parse_log extracts --provider from commands."""
        logfile = _make_log(tmp_path, [
            _finished_line(0, provider="volcano"),
            _finished_line(0, provider="zhipu"),
        ])
        entries = parse_log(logfile)
        assert entries[0]["provider"] == "volcano"
        assert entries[1]["provider"] == "zhipu"

    def test_parse_no_provider_returns_none(self, tmp_path):
        """parse_log returns None for provider when no --provider flag."""
        ts = _ts(0)
        line = f"[{ts}] Starting: golem \"task without provider\""
        logfile = _make_log(tmp_path, [line])
        entries = parse_log(logfile)
        assert entries[0]["provider"] is None

    def test_parse_validation_warn(self, tmp_path):
        """parse_log extracts VALIDATION WARN entries."""
        ts = _ts(0)
        line = f"[{ts}] VALIDATION WARN: golem ... → SyntaxError in foo.py"
        logfile = _make_log(tmp_path, [line])
        entries = parse_log(logfile)
        assert entries[0]["type"] == "validation_warn"
        assert "SyntaxError" in entries[0]["detail"]

    def test_parse_pytest_warn(self, tmp_path):
        """parse_log extracts PYTEST WARN entries."""
        ts = _ts(0)
        line = f"[{ts}] PYTEST WARN: golem ... → pytest failed: 3 failed"
        logfile = _make_log(tmp_path, [line])
        entries = parse_log(logfile)
        assert entries[0]["type"] == "pytest_warn"

    def test_parse_multiple_entries(self, tmp_path):
        """parse_log correctly parses a realistic multi-line log."""
        lines = [
            _starting_line(120),
            _finished_line(119, exit_code=0),
            _starting_line(30, provider="volcano"),
            _finished_line(28, exit_code=1),
            _failed_line(28, exit_code=1, provider="volcano"),
            _idle_line(0),
        ]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        assert len(entries) == 6
        types = [e["type"] for e in entries]
        assert "starting" in types
        assert "finished" in types
        assert "failed" in types
        assert "other" in types


# ── task_counts tests ───────────────────────────────────────────────────


class TestTaskCounts:
    def test_counts_within_windows(self, tmp_path):
        """task_counts correctly bins entries into 1h/6h/24h windows."""
        lines = [
            # 30 min ago: within all windows
            _starting_line(30),
            _finished_line(29, exit_code=0),
            # 120 min ago: within 6h and 24h, not 1h
            _starting_line(120),
            _finished_line(119, exit_code=1),
            _failed_line(119, exit_code=1),
            # 1500 min ago (25h): outside all windows
            _starting_line(1500),
            _finished_line(1499, exit_code=0),
        ]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        counts = task_counts(entries)

        # 1h window: only the 30-min-ago entries
        assert counts["1h"]["started"] == 1
        assert counts["1h"]["finished"] == 1
        assert counts["1h"]["failed"] == 0

        # 6h window: 30min + 120min entries
        assert counts["6h"]["started"] == 2
        assert counts["6h"]["finished"] == 2
        assert counts["6h"]["failed"] == 1

        # 24h window: all entries (25h entry might not make it due to timing)
        assert counts["24h"]["started"] >= 2

    def test_counts_empty_entries(self):
        """task_counts returns zeros when no entries."""
        counts = task_counts([])
        assert counts["1h"]["started"] == 0
        assert counts["6h"]["finished"] == 0
        assert counts["24h"]["failed"] == 0

    def test_counts_timeout_tracked(self, tmp_path):
        """task_counts counts timeouts."""
        lines = [
            _starting_line(10),
            _timeout_line(9),
        ]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        counts = task_counts(entries)
        assert counts["1h"]["timeout"] == 1


# ── failure_rate_trend tests ────────────────────────────────────────────


class TestFailureRateTrend:
    def test_trend_returns_hourly_buckets(self, tmp_path):
        """failure_rate_trend returns 12 hourly buckets."""
        lines = [_finished_line(30, exit_code=0)]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        trend = failure_rate_trend(entries)
        assert len(trend) == 12

    def test_trend_computes_rate(self, tmp_path):
        """failure_rate_trend computes correct failure rate."""
        lines = [
            _finished_line(30, exit_code=0),
            _finished_line(29, exit_code=0),
            _failed_line(28, exit_code=1),
        ]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        trend = failure_rate_trend(entries)
        # Find the current-hour bucket
        current_hour = datetime.now().strftime("%Y-%m-%d %H:00")
        bucket = [b for b in trend if b["hour"] == current_hour][0]
        assert bucket["total"] == 3
        assert bucket["failed"] == 1
        assert abs(bucket["rate"] - 33.3) < 1.0

    def test_trend_empty_entries(self):
        """failure_rate_trend returns empty list for no entries."""
        trend = failure_rate_trend([])
        assert trend == []

    def test_trend_zero_rate_when_all_pass(self, tmp_path):
        """failure_rate_trend shows 0% when all tasks succeed."""
        lines = [
            _finished_line(10, exit_code=0),
            _finished_line(9, exit_code=0),
        ]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        trend = failure_rate_trend(entries)
        current_hour = datetime.now().strftime("%Y-%m-%d %H:00")
        bucket = [b for b in trend if b["hour"] == current_hour][0]
        assert bucket["rate"] == 0.0

    def test_trend_100_percent_when_all_fail(self, tmp_path):
        """failure_rate_trend shows 100% when all tasks fail."""
        lines = [
            _failed_line(10, exit_code=1),
            _failed_line(9, exit_code=1),
        ]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        trend = failure_rate_trend(entries)
        current_hour = datetime.now().strftime("%Y-%m-%d %H:00")
        bucket = [b for b in trend if b["hour"] == current_hour][0]
        assert bucket["rate"] == 100.0


# ── top_errors tests ────────────────────────────────────────────────────


class TestTopErrors:
    def test_top_errors_groups_by_type_and_exit_code(self, tmp_path):
        """top_errors groups errors by (type, exit_code) pair."""
        lines = [
            _failed_line(30, exit_code=1),
            _failed_line(29, exit_code=1),
            _failed_line(28, exit_code=2),
        ]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        errors = top_errors(entries)
        # Should have 2 groups: (failed, 1) and (failed, 2)
        assert len(errors) == 2
        # exit=1 should be first (count=2)
        assert errors[0]["exit_code"] == 1
        assert errors[0]["count"] == 2

    def test_top_errors_includes_timeouts(self, tmp_path):
        """top_errors includes timeout entries."""
        lines = [
            _timeout_line(10),
            _failed_line(9, exit_code=1),
        ]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        errors = top_errors(entries)
        types = {e["type"] for e in errors}
        assert "timeout" in types
        assert "failed" in types

    def test_top_errors_includes_error_type(self, tmp_path):
        """top_errors includes ERROR entries."""
        lines = [_error_line(5)]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        errors = top_errors(entries)
        assert any(e["type"] == "error" for e in errors)

    def test_top_errors_respects_limit(self, tmp_path):
        """top_errors limits output to the requested count."""
        lines = [_failed_line(i, exit_code=i) for i in range(20)]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        errors = top_errors(entries, limit=5)
        assert len(errors) <= 5

    def test_top_errors_empty(self):
        """top_errors returns empty list when no errors."""
        errors = top_errors([])
        assert errors == []

    def test_top_errors_ignores_finished(self, tmp_path):
        """top_errors excludes successful finished entries."""
        lines = [_finished_line(0, exit_code=0)]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        errors = top_errors(entries)
        assert errors == []

    def test_top_errors_sample_message(self, tmp_path):
        """top_errors includes a sample detail string."""
        lines = [_failed_line(5, exit_code=1)]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        errors = top_errors(entries)
        assert len(errors) == 1
        assert errors[0]["sample"] != ""


# ── format_summary tests ────────────────────────────────────────────────


class TestFormatSummary:
    def test_format_summary_empty(self):
        """format_summary handles empty entries gracefully."""
        output = format_summary([])
        assert "No log entries found" in output

    def test_format_summary_has_sections(self, tmp_path):
        """format_summary includes all three report sections."""
        lines = [
            _starting_line(30),
            _finished_line(29, exit_code=0),
            _failed_line(28, exit_code=1),
        ]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        output = format_summary(entries)
        assert "Task Counts" in output
        assert "Failure Rate Trend" in output
        assert "Top Errors" in output

    def test_format_summary_task_count_table(self, tmp_path):
        """format_summary shows the window labels in the table."""
        lines = [_finished_line(0, exit_code=0)]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        output = format_summary(entries)
        assert "1h" in output
        assert "6h" in output
        assert "24h" in output


# ── format_json tests ───────────────────────────────────────────────────


class TestFormatJson:
    def test_format_json_parseable(self, tmp_path):
        """format_json produces valid JSON."""
        import json
        lines = [_finished_line(0, exit_code=0)]
        logfile = _make_log(tmp_path, lines)
        entries = parse_log(logfile)
        output = format_json(entries)
        data = json.loads(output)
        assert "task_counts" in data
        assert "failure_rate_trend" in data
        assert "top_errors" in data
        assert data["total_entries"] == 1

    def test_format_json_empty(self):
        """format_json handles empty entries."""
        import json
        output = format_json([])
        data = json.loads(output)
        assert data["total_entries"] == 0


# ── Integration: subprocess run ─────────────────────────────────────────


class TestCliRun:
    def test_cli_runs_successfully(self):
        """log-summary exits with code 0 against real log."""
        import subprocess
        result = subprocess.run(
            ["/home/terry/germline/effectors/log-summary"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0

    def test_cli_json_flag(self):
        """log-summary --json produces valid JSON."""
        import json, subprocess
        result = subprocess.run(
            ["/home/terry/germline/effectors/log-summary", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "task_counts" in data

    def test_cli_errors_flag(self):
        """log-summary --errors shows error list."""
        import subprocess
        result = subprocess.run(
            ["/home/terry/germline/effectors/log-summary", "--errors"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        # Should have at least one error line from real log
        assert result.stdout.strip() != ""

    def test_cli_trend_flag(self):
        """log-summary --trend shows hourly buckets."""
        import subprocess
        result = subprocess.run(
            ["/home/terry/germline/effectors/log-summary", "--trend"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 12  # 12 hourly buckets
