from __future__ import annotations

"""Tests for golem-report — analytics report generator from golem task logs."""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest


# ── Load effector via exec ────────────────────────────────────────────


def _load_golem_report() -> dict:
    """Load the golem-report module by exec-ing its Python body."""
    source = (Path.home() / "germline/effectors/golem-report").read_text()
    ns: dict = {"__name__": "golem_report_test"}
    exec(source, ns)
    return ns


_mod = _load_golem_report()

parse_timestamp = _mod["parse_timestamp"]
load_jsonl = _mod["load_jsonl"]
extract_task_id = _mod["extract_task_id"]
get_task_id = _mod["get_task_id"]
is_rate_limited = _mod["is_rate_limited"]
truncate_prompt = _mod["truncate_prompt"]
generate_report = _mod["generate_report"]
RATE_LIMIT_PATTERNS = _mod["RATE_LIMIT_PATTERNS"]
JSONL_FILE = _mod["JSONL_FILE"]
QUEUE_FILE = _mod["QUEUE_FILE"]


# ── Helpers ───────────────────────────────────────────────────────────


def _make_jsonl(tmp_path: Path, records: list[dict]) -> Path:
    """Create a fake golem.jsonl in tmp_path and return its path."""
    vivesca_dir = tmp_path / ".local" / "share" / "vivesca"
    vivesca_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = vivesca_dir / "golem.jsonl"
    jsonl_path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return jsonl_path


def _sample_records(date_str: str = "2026-04-01") -> list[dict]:
    """Return a list of sample JSONL records for testing."""
    return [
        {
            "ts": f"{date_str}T10:00:00Z",
            "task_id": "t-abc123",
            "provider": "zhipu",
            "exit": 0,
            "duration": 120,
            "prompt": "implement feature X",
            "tail": "All tests passed",
        },
        {
            "ts": f"{date_str}T10:05:00Z",
            "task_id": "t-def456",
            "provider": "infini",
            "exit": 0,
            "duration": 180,
            "prompt": "refactor module Y",
            "tail": "success",
        },
        {
            "ts": f"{date_str}T10:10:00Z",
            "task_id": "t-ghi789",
            "provider": "infini",
            "exit": 1,
            "duration": 5,
            "prompt": "fix bug Z",
            "tail": "",
        },
        {
            "ts": f"{date_str}T11:00:00Z",
            "task_id": "t-jkl012",
            "provider": "volcano",
            "exit": 0,
            "duration": 300,
            "prompt": "[t-jkl012] research topic A",
            "tail": "done",
        },
        {
            "ts": f"{date_str}T11:30:00Z",
            "task_id": "t-abc123",
            "provider": "zhipu",
            "exit": 1,
            "duration": 90,
            "prompt": "implement feature X (retry)",
            "tail": "429 rate limit exceeded",
        },
    ]


# ── parse_timestamp tests ─────────────────────────────────────────────


class TestParseTimestamp:
    """Tests for parse_timestamp: ISO format handling."""

    def test_utc_with_z_suffix(self):
        """parse_timestamp handles YYYY-MM-DDTHH:MM:SSZ format."""
        result = parse_timestamp("2026-04-01T10:00:00Z")
        assert result is not None
        assert result.year == 2026
        assert result.month == 4
        assert result.day == 1
        assert result.hour == 10
        assert result.tzinfo == timezone.utc

    def test_without_z_suffix(self):
        """parse_timestamp handles YYYY-MM-DDTHH:MM:SS format."""
        result = parse_timestamp("2026-04-01T10:00:00")
        assert result is not None
        assert result.year == 2026
        assert result.hour == 10

    def test_microseconds_with_z(self):
        """parse_timestamp handles YYYY-MM-DDTHH:MM:SS.ffffffZ format."""
        result = parse_timestamp("2026-04-01T10:00:00.123456Z")
        assert result is not None
        assert result.microsecond == 123456

    def test_invalid_string_returns_none(self):
        """parse_timestamp returns None for unparseable strings."""
        assert parse_timestamp("not-a-date") is None
        assert parse_timestamp("") is None
        assert parse_timestamp("2026/04/01") is None

    def test_partial_timestamp_returns_none(self):
        """parse_timestamp returns None for partial formats."""
        assert parse_timestamp("2026-04-01") is None
        assert parse_timestamp("10:00:00") is None


# ── extract_task_id tests ─────────────────────────────────────────────


class TestExtractTaskId:
    """Tests for extract_task_id: regex extraction from prompt."""

    def test_extracts_bracketed_task_id(self):
        """extract_task_id finds [t-abc123] in prompt."""
        assert extract_task_id("do something [t-abc123]") == "[t-abc123]"

    def test_extracts_from_middle(self):
        """extract_task_id finds ID embedded in prompt text."""
        prompt = "golem [t-def456] implement feature X"
        assert extract_task_id(prompt) == "[t-def456]"

    def test_no_task_id_returns_empty(self):
        """extract_task_id returns empty string when no match."""
        assert extract_task_id("no task id here") == ""

    def test_multiple_ids_returns_first(self):
        """extract_task_id returns first match when multiple IDs present."""
        prompt = "[t-aaa] and [t-bbb]"
        result = extract_task_id(prompt)
        assert result == "[t-aaa]"

    def test_hex_task_id(self):
        """extract_task_id handles various hex IDs."""
        assert extract_task_id("[t-deadbeef]") == "[t-deadbeef]"
        assert extract_task_id("[t-0123456789abcdef]") == "[t-0123456789abcdef]"

    def test_uppercase_hex_not_matched(self):
        """extract_task_id only matches lowercase hex digits."""
        # The regex uses [a-f0-9], uppercase A-F should not match
        assert extract_task_id("[T-ABC]") == ""


# ── get_task_id tests ─────────────────────────────────────────────────


class TestGetTaskId:
    """Tests for get_task_id: task ID from record field or prompt."""

    def test_from_task_id_field(self):
        """get_task_id returns task_id field when present."""
        rec = {"task_id": "t-abc123", "prompt": "no id here"}
        assert get_task_id(rec) == "[t-abc123]"

    def test_from_task_id_field_already_bracketed(self):
        """get_task_id doesn't double-bracket already bracketed task_id."""
        rec = {"task_id": "[t-abc123]"}
        assert get_task_id(rec) == "[t-abc123]"

    def test_from_prompt_when_no_task_id_field(self):
        """get_task_id extracts from prompt when task_id absent."""
        rec = {"prompt": "do [t-def456] something"}
        assert get_task_id(rec) == "[t-def456]"

    def test_empty_when_neither_present(self):
        """get_task_id returns empty string when no ID anywhere."""
        rec = {"prompt": "no id"}
        assert get_task_id(rec) == ""

    def test_task_id_field_takes_priority(self):
        """get_task_id prefers task_id field over prompt."""
        rec = {"task_id": "t-aaa", "prompt": "do [t-bbb] something"}
        assert get_task_id(rec) == "[t-aaa]"


# ── is_rate_limited tests ─────────────────────────────────────────────


class TestIsRateLimited:
    """Tests for is_rate_limited: rate-limit detection patterns."""

    def test_429_in_tail(self):
        """is_rate_limited detects 429 status code in tail."""
        rec = {"tail": "Error: HTTP 429 Too Many Requests", "exit": 1, "duration": 30}
        assert is_rate_limited(rec) is True

    def test_rate_limit_keyword(self):
        """is_rate_limited detects 'rate limit' in tail."""
        rec = {"tail": "rate limit exceeded for this account", "exit": 1, "duration": 30}
        assert is_rate_limited(rec) is True

    def test_quota_exceeded(self):
        """is_rate_limited detects 'quota exceeded' in tail."""
        rec = {"tail": "AccountQuotaExceeded for API usage", "exit": 1, "duration": 30}
        assert is_rate_limited(rec) is True

    def test_too_many_requests(self):
        """is_rate_limited detects 'TooManyRequests' in tail."""
        rec = {"tail": "TooManyRequests: try again later", "exit": 1, "duration": 30}
        assert is_rate_limited(rec) is True

    def test_try_again_at(self):
        """is_rate_limited detects 'try again at' in tail."""
        rec = {"tail": "try again at 2026-04-01T12:00:00Z", "exit": 1, "duration": 30}
        assert is_rate_limited(rec) is True

    def test_exit_1_empty_tail_short_duration(self):
        """is_rate_limited detects exit=1 with empty tail and short duration."""
        rec = {"tail": "  ", "exit": 1, "duration": 5}
        assert is_rate_limited(rec) is True

    def test_exit_1_empty_tail_long_duration_not_rate_limited(self):
        """is_rate_limited does NOT flag exit=1 with empty tail if duration >= 10."""
        rec = {"tail": "", "exit": 1, "duration": 15}
        assert is_rate_limited(rec) is False

    def test_normal_failure_not_rate_limited(self):
        """is_rate_limited returns False for normal failures with informative tail."""
        rec = {"tail": "SyntaxError in test_foo.py", "exit": 1, "duration": 30}
        assert is_rate_limited(rec) is False

    def test_successful_task_not_rate_limited(self):
        """is_rate_limited returns False for successful tasks."""
        rec = {"tail": "All tests passed", "exit": 0, "duration": 120}
        assert is_rate_limited(rec) is False

    def test_usage_limit(self):
        """is_rate_limited detects 'usage limit' pattern."""
        rec = {"tail": "You have hit your usage limit", "exit": 1, "duration": 3}
        assert is_rate_limited(rec) is True

    def test_empty_tail_exit_0(self):
        """is_rate_limited returns False for successful task with empty tail."""
        rec = {"tail": "", "exit": 0, "duration": 5}
        assert is_rate_limited(rec) is False

    def test_case_insensitive(self):
        """is_rate_limited matches patterns case-insensitively."""
        rec = {"tail": "RATE LIMIT exceeded", "exit": 1, "duration": 30}
        assert is_rate_limited(rec) is True


# ── truncate_prompt tests ─────────────────────────────────────────────


class TestTruncatePrompt:
    """Tests for truncate_prompt: display-friendly prompt truncation."""

    def test_short_prompt_unchanged(self):
        """truncate_prompt leaves short prompts unchanged."""
        assert truncate_prompt("short prompt") == "short prompt"

    def test_long_prompt_truncated(self):
        """truncate_prompt truncates long prompts and adds ellipsis."""
        long_prompt = "x" * 100
        result = truncate_prompt(long_prompt)
        assert len(result) == 60
        assert result.endswith("...")

    def test_exactly_max_len_unchanged(self):
        """truncate_prompt does not truncate at exactly max_len."""
        prompt = "x" * 60
        assert truncate_prompt(prompt) == prompt

    def test_custom_max_len(self):
        """truncate_prompt respects custom max_len parameter."""
        prompt = "x" * 50
        result = truncate_prompt(prompt, max_len=30)
        assert len(result) == 30
        assert result.endswith("...")

    def test_strips_coaching_notes(self):
        """truncate_prompt removes <coaching-notes> blocks."""
        prompt = "<coaching-notes>\nSome long coaching\n---\nActual prompt here"
        result = truncate_prompt(prompt)
        assert "<coaching-notes>" not in result
        assert "Actual prompt here" in result

    def test_strips_coaching_notes_then_truncates(self):
        """truncate_prompt strips coaching then truncates remaining text."""
        prompt = "<coaching-notes>\nblah\n---\n" + "x" * 100
        result = truncate_prompt(prompt)
        assert len(result) == 60
        assert "<coaching-notes>" not in result

    def test_empty_prompt(self):
        """truncate_prompt handles empty string."""
        assert truncate_prompt("") == ""

    def test_prompt_with_only_coaching_notes(self):
        """truncate_prompt handles prompt that is entirely coaching notes."""
        prompt = "<coaching-notes>\nall coaching\n---\n"
        result = truncate_prompt(prompt)
        # After stripping and trimming, should be empty
        assert result == ""


# ── load_jsonl tests ──────────────────────────────────────────────────


class TestLoadJsonl:
    """Tests for load_jsonl: reading and filtering JSONL records."""

    def test_nonexistent_file_returns_empty(self, tmp_path):
        """load_jsonl returns empty list when JSONL file doesn't exist."""
        fake_path = tmp_path / "nonexistent.jsonl"
        original = _mod["JSONL_FILE"]
        try:
            _mod["JSONL_FILE"] = fake_path
            result = load_jsonl("2026-04-01")
        finally:
            _mod["JSONL_FILE"] = original
        assert result == []

    def test_loads_valid_records(self, tmp_path):
        """load_jsonl returns records matching date filter."""
        jsonl_path = _make_jsonl(tmp_path, _sample_records("2026-04-01"))
        original = _mod["JSONL_FILE"]
        try:
            _mod["JSONL_FILE"] = jsonl_path
            result = load_jsonl("2026-04-01")
        finally:
            _mod["JSONL_FILE"] = original
        assert len(result) == 5

    def test_filters_by_date(self, tmp_path):
        """load_jsonl only returns records matching the date filter."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "zhipu", "exit": 0},
            {"ts": "2026-04-02T10:00:00Z", "provider": "infini", "exit": 0},
        ]
        jsonl_path = _make_jsonl(tmp_path, records)
        original = _mod["JSONL_FILE"]
        try:
            _mod["JSONL_FILE"] = jsonl_path
            result = load_jsonl("2026-04-01")
        finally:
            _mod["JSONL_FILE"] = original
        assert len(result) == 1
        assert result[0]["provider"] == "zhipu"

    def test_no_date_filter_returns_all(self, tmp_path):
        """load_jsonl returns all records when date_filter is None."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "zhipu"},
            {"ts": "2026-04-02T10:00:00Z", "provider": "infini"},
        ]
        jsonl_path = _make_jsonl(tmp_path, records)
        original = _mod["JSONL_FILE"]
        try:
            _mod["JSONL_FILE"] = jsonl_path
            result = load_jsonl(None)
        finally:
            _mod["JSONL_FILE"] = original
        assert len(result) == 2

    def test_skips_malformed_json(self, tmp_path):
        """load_jsonl skips lines that aren't valid JSON."""
        vivesca_dir = tmp_path / ".local" / "share" / "vivesca"
        vivesca_dir.mkdir(parents=True)
        jsonl_path = vivesca_dir / "golem.jsonl"
        content = (
            '{"ts": "2026-04-01T10:00:00Z", "provider": "zhipu"}\n'
            "not valid json\n"
            '{"ts": "2026-04-01T11:00:00Z", "provider": "infini"}\n'
        )
        jsonl_path.write_text(content)
        original = _mod["JSONL_FILE"]
        try:
            _mod["JSONL_FILE"] = jsonl_path
            result = load_jsonl("2026-04-01")
        finally:
            _mod["JSONL_FILE"] = original
        assert len(result) == 2

    def test_skips_records_without_timestamp(self, tmp_path):
        """load_jsonl skips records with no parseable ts field."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "zhipu"},
            {"provider": "infini"},  # no ts
            {"ts": "bad-format", "provider": "volcano"},
        ]
        jsonl_path = _make_jsonl(tmp_path, records)
        original = _mod["JSONL_FILE"]
        try:
            _mod["JSONL_FILE"] = jsonl_path
            result = load_jsonl("2026-04-01")
        finally:
            _mod["JSONL_FILE"] = original
        assert len(result) == 1

    def test_empty_jsonl_file(self, tmp_path):
        """load_jsonl returns empty list for empty file."""
        vivesca_dir = tmp_path / ".local" / "share" / "vivesca"
        vivesca_dir.mkdir(parents=True)
        jsonl_path = vivesca_dir / "golem.jsonl"
        jsonl_path.write_text("")
        original = _mod["JSONL_FILE"]
        try:
            _mod["JSONL_FILE"] = jsonl_path
            result = load_jsonl("2026-04-01")
        finally:
            _mod["JSONL_FILE"] = original
        assert result == []

    def test_records_have_dt_field(self, tmp_path):
        """load_jsonl adds _dt field to parsed records."""
        records = [{"ts": "2026-04-01T10:00:00Z", "provider": "zhipu"}]
        jsonl_path = _make_jsonl(tmp_path, records)
        original = _mod["JSONL_FILE"]
        try:
            _mod["JSONL_FILE"] = jsonl_path
            result = load_jsonl("2026-04-01")
        finally:
            _mod["JSONL_FILE"] = original
        assert len(result) == 1
        assert "_dt" in result[0]
        assert isinstance(result[0]["_dt"], datetime)


# ── generate_report tests ─────────────────────────────────────────────


class TestGenerateReport:
    """Tests for generate_report: markdown report generation."""

    def test_empty_records(self):
        """generate_report shows 'no tasks' message for empty records."""
        report = generate_report([], "2026-04-01")
        assert "# Golem Report — 2026-04-01" in report
        assert "*No tasks recorded for this date.*" in report
        assert "## Summary" not in report

    def test_report_header(self):
        """generate_report has correct header with date."""
        report = generate_report(_sample_records(), "2026-04-01")
        assert "# Golem Report — 2026-04-01" in report

    def test_summary_section_counts(self):
        """generate_report shows correct total, succeeded, failed."""
        records = _sample_records()
        report = generate_report(records, "2026-04-01")
        assert "| Total tasks | 5 |" in report
        assert "| Succeeded | 3 |" in report
        assert "| Failed | 2 |" in report

    def test_summary_success_rate(self):
        """generate_report calculates correct success rate."""
        records = _sample_records()
        report = generate_report(records, "2026-04-01")
        # 3 success / 5 total = 60.0%
        assert "| Success rate | 60.0% |" in report

    def test_summary_rate_limits(self):
        """generate_report counts rate-limit events correctly."""
        records = _sample_records()
        report = generate_report(records, "2026-04-01")
        # Record 2: exit=1, empty tail, duration=5 → rate limited
        # Record 4: tail="429 rate limit exceeded" → rate limited
        assert "| Rate-limit events | 2 |" in report

    def test_by_provider_section(self):
        """generate_report includes per-provider breakdown."""
        records = _sample_records()
        report = generate_report(records, "2026-04-01")
        assert "## By Provider" in report
        assert "infini" in report
        assert "zhipu" in report
        assert "volcano" in report

    def test_by_provider_sorted_alphabetically(self):
        """generate_report sorts providers alphabetically."""
        records = _sample_records()
        report = generate_report(records, "2026-04-01")
        lines = report.split("\n")
        provider_lines = [l for l in lines if l.startswith("| ") and "infini" in l or "volcano" in l or "zhipu" in l]
        # Find positions of provider names in the report body
        infini_pos = report.index("| infini")
        volcano_pos = report.index("| volcano")
        zhipu_pos = report.index("| zhipu")
        assert infini_pos < volcano_pos < zhipu_pos

    def test_top_3_longest_tasks(self):
        """generate_report shows top 3 longest tasks."""
        records = _sample_records()
        report = generate_report(records, "2026-04-01")
        assert "## Top 3 Longest Tasks" in report
        # Longest: volcano 300s, then infini 180s, then zhipu 120s
        assert "300s" in report
        assert "180s" in report
        assert "120s" in report

    def test_top_3_longest_shows_status(self):
        """generate_report shows ✓/✗ status for longest tasks."""
        # Need a failed task with high duration to appear in top 3
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "a", "exit": 0, "duration": 300, "prompt": "task1"},
            {"ts": "2026-04-01T10:05:00Z", "provider": "b", "exit": 1, "duration": 200, "prompt": "task2"},
            {"ts": "2026-04-01T10:10:00Z", "provider": "c", "exit": 0, "duration": 100, "prompt": "task3"},
        ]
        report = generate_report(records, "2026-04-01")
        assert "[✓]" in report
        assert "[✗]" in report

    def test_top_3_most_retried_tasks(self):
        """generate_report shows most-retried tasks by task_id."""
        records = _sample_records()
        report = generate_report(records, "2026-04-01")
        assert "## Top 3 Most-Retried Tasks" in report
        # t-abc123 appears twice (records 0 and 4)
        assert "t-abc123" in report
        assert "2 attempts" in report

    def test_most_retried_shows_success_count(self):
        """generate_report shows success count for retried tasks."""
        records = _sample_records()
        report = generate_report(records, "2026-04-01")
        # t-abc123: 2 attempts, 1 success (first exit=0, second exit=1)
        assert "1 success" in report

    def test_no_retried_tasks(self):
        """generate_report shows fallback when no task IDs found."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "zhipu", "exit": 0, "duration": 60, "prompt": "no id"},
        ]
        report = generate_report(records, "2026-04-01")
        assert "*No task IDs found in records.*" in report

    def test_single_record_report(self):
        """generate_report handles a single record correctly."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "zhipu", "exit": 0, "duration": 60, "prompt": "task"},
        ]
        report = generate_report(records, "2026-04-01")
        assert "| Total tasks | 1 |" in report
        assert "| Succeeded | 1 |" in report
        assert "| Failed | 0 |" in report
        assert "| Success rate | 100.0% |" in report

    def test_all_failed_report(self):
        """generate_report handles all-failed records."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "infini", "exit": 1, "duration": 10, "prompt": "fail"},
            {"ts": "2026-04-01T10:05:00Z", "provider": "infini", "exit": 1, "duration": 20, "prompt": "fail2"},
        ]
        report = generate_report(records, "2026-04-01")
        assert "| Success rate | 0.0% |" in report
        assert "| Failed | 2 |" in report

    def test_avg_duration_calculation(self):
        """generate_report calculates average duration correctly."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "a", "exit": 0, "duration": 60},
            {"ts": "2026-04-01T10:05:00Z", "provider": "b", "exit": 0, "duration": 180},
        ]
        report = generate_report(records, "2026-04-01")
        # avg = (60 + 180) / 2 = 120s = 2.0m
        assert "| Avg duration | 120s (2.0m) |" in report

    def test_zero_duration_excluded_from_avg(self):
        """generate_report excludes zero-duration records from average."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "a", "exit": 0, "duration": 120},
            {"ts": "2026-04-01T10:05:00Z", "provider": "b", "exit": 0, "duration": 0},
        ]
        report = generate_report(records, "2026-04-01")
        # avg = 120 / 1 = 120s (0-duration excluded)
        assert "| Avg duration | 120s (2.0m) |" in report

    def test_provider_unknown_when_missing(self):
        """generate_report uses 'unknown' when provider field is absent."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "exit": 0, "duration": 60, "prompt": "task"},
        ]
        report = generate_report(records, "2026-04-01")
        assert "| unknown |" in report


# ── main() / CLI integration tests ────────────────────────────────────


class TestMainCli:
    """Tests for main() via subprocess.run — end-to-end CLI tests."""

    REPORT_PATH = Path.home() / "germline/effectors/golem-report"

    def _run(self, args: list[str]) -> subprocess.CompletedProcess:
        """Run golem-report with given args via subprocess."""
        cmd = [sys.executable, str(self.REPORT_PATH)] + args
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10)

    def test_help_flag(self):
        """golem-report --help exits 0 and shows usage."""
        result = self._run(["--help"])
        assert result.returncode == 0
        assert "Generate analytics report" in result.stdout

    def test_default_today_report(self, tmp_path):
        """golem-report with no args generates report for today."""
        # Point JSONL_FILE at empty dir so we get "no tasks" message
        vivesca_dir = tmp_path / ".local" / "share" / "vivesca"
        vivesca_dir.mkdir(parents=True)
        jsonl_path = vivesca_dir / "golem.jsonl"
        jsonl_path.write_text("")

        # We can't easily override paths in subprocess, so just verify it runs
        result = self._run(["--date", "2099-12-31"])
        assert result.returncode == 0
        assert "Golem Report" in result.stdout

    def test_specific_date_report(self):
        """golem-report --date YYYY-MM-DD generates report for that date."""
        result = self._run(["--date", "2020-01-01"])
        assert result.returncode == 0
        assert "Golem Report — 2020-01-01" in result.stdout
        assert "No tasks recorded" in result.stdout

    def test_json_output_flag(self):
        """golem-report --json outputs valid JSON."""
        result = self._run(["--date", "2020-01-01", "--json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "date" in data
        assert data["date"] == "2020-01-01"
        assert "total" in data
        assert "records" in data


# ── Edge case tests ───────────────────────────────────────────────────


class TestEdgeCases:
    """Edge cases: malformed data, boundary values, concurrent access."""

    def test_generate_report_with_many_providers(self):
        """generate_report handles many different providers."""
        records = []
        for i in range(10):
            records.append({
                "ts": "2026-04-01T10:00:00Z",
                "provider": f"provider-{i}",
                "exit": 0,
                "duration": 60,
                "prompt": f"task {i}",
            })
        report = generate_report(records, "2026-04-01")
        assert "| Total tasks | 10 |" in report
        for i in range(10):
            assert f"provider-{i}" in report

    def test_generate_report_more_than_3_longest(self):
        """generate_report shows only top 3 even with many tasks."""
        records = []
        for i in range(10):
            records.append({
                "ts": "2026-04-01T10:00:00Z",
                "provider": "test",
                "exit": 0,
                "duration": (i + 1) * 100,
                "prompt": f"task {i}",
            })
        report = generate_report(records, "2026-04-01")
        # Should show top 3 longest: 1000s, 900s, 800s
        assert "1000s" in report
        assert "900s" in report
        assert "800s" in report
        # Should NOT show 700s (4th longest)
        assert "700s" not in report

    def test_generate_report_more_than_3_retried(self):
        """generate_report shows only top 3 most-retried even with many."""
        records = []
        for i in range(5):
            for _ in range(i + 2):  # 2, 3, 4, 5, 6 attempts
                records.append({
                    "ts": "2026-04-01T10:00:00Z",
                    "task_id": f"t-aaaa{i:x}",
                    "provider": "test",
                    "exit": 0,
                    "duration": 60,
                    "prompt": f"[t-aaaa{i:x}] task {i}",
                })
        report = generate_report(records, "2026-04-01")
        # Should show top 3: t-aaaa4 (6), t-aaaa3 (5), t-aaaa2 (4)
        assert "6 attempts" in report
        assert "5 attempts" in report
        assert "4 attempts" in report
        # Should NOT show t-aaaa0 (2 attempts, 5th most retried)
        assert "2 attempts" not in report

    def test_generate_report_very_long_prompt(self):
        """generate_report truncates long prompts in longest tasks section."""
        records = [
            {
                "ts": "2026-04-01T10:00:00Z",
                "provider": "test",
                "exit": 0,
                "duration": 999,
                "prompt": "x" * 500,
            },
        ]
        report = generate_report(records, "2026-04-01")
        # The prompt should be truncated to 60 chars with "..."
        lines = report.split("\n")
        # Find the task line in Top 3 Longest section (starts with "1.")
        task_lines = [l for l in lines if l.startswith("1.") and "999s" in l]
        assert len(task_lines) == 1
        assert "..." in task_lines[0]

    def test_generate_report_prompt_with_coaching_notes(self):
        """generate_report strips coaching notes from prompts in output."""
        records = [
            {
                "ts": "2026-04-01T10:00:00Z",
                "provider": "test",
                "exit": 0,
                "duration": 999,
                "prompt": "<coaching-notes>\nblah\n---\nactual prompt text",
            },
        ]
        report = generate_report(records, "2026-04-01")
        assert "<coaching-notes>" not in report
        assert "actual prompt text" in report

    def test_load_jsonl_unreadable_file(self, tmp_path):
        """load_jsonl returns empty when file exists but is unreadable."""
        vivesca_dir = tmp_path / ".local" / "share" / "vivesca"
        vivesca_dir.mkdir(parents=True)
        jsonl_path = vivesca_dir / "golem.jsonl"
        jsonl_path.write_text('{"ts": "2026-04-01T10:00:00Z"}\n')
        jsonl_path.chmod(0o000)
        original = _mod["JSONL_FILE"]
        try:
            _mod["JSONL_FILE"] = jsonl_path
            result = load_jsonl("2026-04-01")
        finally:
            _mod["JSONL_FILE"] = original
            jsonl_path.chmod(0o644)
        assert result == []

    def test_generate_report_with_only_zero_durations(self):
        """generate_report handles all records with duration=0."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "a", "exit": 0, "duration": 0, "prompt": "x"},
            {"ts": "2026-04-01T10:05:00Z", "provider": "b", "exit": 0, "duration": 0, "prompt": "y"},
        ]
        report = generate_report(records, "2026-04-01")
        # avg should be 0 since all durations are 0
        assert "| Avg duration | 0s (0.0m) |" in report


# ── Additional rate-limit pattern tests ──────────────────────────────────


class TestRateLimitPatternsExtra:
    """Tests for less-common RATE_LIMIT_PATTERNS substrings."""

    def test_20013_error_code(self):
        """is_rate_limited detects 20013 error code in tail."""
        rec = {"tail": "Error code 20013 from upstream provider", "exit": 1, "duration": 30}
        assert is_rate_limited(rec) is True

    def test_request_limit_exceeded(self):
        """is_rate_limited detects 'request limit exceeded' in tail."""
        rec = {"tail": "request limit exceeded for this endpoint", "exit": 1, "duration": 30}
        assert is_rate_limited(rec) is True

    def test_api_error_429(self):
        """is_rate_limited detects 'API Error: 429' in tail."""
        rec = {"tail": "API Error 429: too many requests", "exit": 1, "duration": 30}
        assert is_rate_limited(rec) is True

    def test_hit_your_limit(self):
        """is_rate_limited detects 'hit your limit' in tail."""
        rec = {"tail": "You have hit your limit for this billing period", "exit": 1, "duration": 3}
        assert is_rate_limited(rec) is True

    def test_quota_will_reset(self):
        """is_rate_limited detects 'quota will reset' in tail."""
        rec = {"tail": "Your quota will reset at midnight UTC", "exit": 1, "duration": 5}
        assert is_rate_limited(rec) is True

    def test_missing_fields_defaults(self):
        """is_rate_limited handles records with missing fields gracefully."""
        rec = {}
        assert is_rate_limited(rec) is False

    def test_tail_missing_not_rate_limited(self):
        """is_rate_limited returns False when tail field is absent and exit is 0."""
        rec = {"exit": 0, "duration": 5}
        assert is_rate_limited(rec) is False

    def test_rate_limit_patterns_compiled(self):
        """RATE_LIMIT_PATTERNS is a compiled regex object."""
        import re
        assert hasattr(RATE_LIMIT_PATTERNS, "search")
        assert RATE_LIMIT_PATTERNS.flags & re.IGNORECASE


# ── Additional parse_timestamp tests ─────────────────────────────────────


class TestParseTimestampExtra:
    """Additional edge cases for parse_timestamp."""

    def test_none_input_raises_typeerror(self):
        """parse_timestamp raises TypeError for None input."""
        with pytest.raises(TypeError):
            parse_timestamp(None)

    def test_numeric_input_raises_typeerror(self):
        """parse_timestamp raises TypeError for numeric input."""
        with pytest.raises(TypeError):
            parse_timestamp(12345)

    def test_microseconds_no_z_suffix(self):
        """parse_timestamp returns None for microseconds without Z."""
        # The format '%Y-%m-%dT%H:%M:%S.%f' is not in the supported list
        result = parse_timestamp("2026-04-01T10:00:00.123456")
        assert result is None

    def test_timestamp_with_timezone_offset(self):
        """parse_timestamp returns None for +00:00 timezone offset."""
        result = parse_timestamp("2026-04-01T10:00:00+00:00")
        assert result is None

    def test_whitespace_timestamp(self):
        """parse_timestamp returns None for whitespace-only input."""
        result = parse_timestamp("   ")
        assert result is None


# ── Additional truncate_prompt tests ─────────────────────────────────────


class TestTruncatePromptExtra:
    """Additional edge cases for truncate_prompt."""

    def test_max_len_less_than_ellipsis(self):
        """truncate_prompt with max_len < 3 still produces output."""
        result = truncate_prompt("hello world", max_len=2)
        # len > 2 so truncation happens: prompt[:2-3] + "..." = "" + "..." = "..."
        # But prompt[:max_len-3] = prompt[:-1] = "hello worl" when max_len=2? No,
        # max_len-3 = -1, so prompt[:-1] = "hello worl" — actually len of that > max_len
        assert len(result) > 0

    def test_prompt_with_newlines(self):
        """truncate_prompt handles prompts containing newlines."""
        prompt = "line one\nline two\nline three"
        result = truncate_prompt(prompt)
        assert "line one" in result

    def test_prompt_with_unicode(self):
        """truncate_prompt handles unicode characters correctly."""
        prompt = "Implement feature: résumé builder 🚀"
        result = truncate_prompt(prompt)
        assert len(result) <= 60

    def test_coaching_notes_multiline_separator(self):
        """truncate_prompt strips coaching notes with multi-line content."""
        prompt = "<coaching-notes>\nline1\nline2\nline3\n---\nactual task"
        result = truncate_prompt(prompt)
        assert result == "actual task"

    def test_exact_boundary_61_chars(self):
        """truncate_prompt truncates at 61 chars (one over max_len)."""
        prompt = "x" * 61
        result = truncate_prompt(prompt)
        assert len(result) == 60
        assert result.endswith("...")


# ── Additional get_task_id tests ─────────────────────────────────────────


class TestGetTaskIdExtra:
    """Additional edge cases for get_task_id."""

    def test_empty_string_task_id_field(self):
        """get_task_id falls through to prompt when task_id is empty string."""
        rec = {"task_id": "", "prompt": "do [t-abc999] something"}
        assert get_task_id(rec) == "[t-abc999]"

    def test_none_task_id_field(self):
        """get_task_id falls through when task_id is None."""
        rec = {"task_id": None, "prompt": "do [t-abc111] something"}
        assert get_task_id(rec) == "[t-abc111]"

    def test_missing_both_fields(self):
        """get_task_id returns empty when neither task_id nor prompt field."""
        rec = {"exit": 0}
        assert get_task_id(rec) == ""

    def test_numeric_task_id(self):
        """get_task_id handles numeric task_id by wrapping in brackets."""
        rec = {"task_id": "t-123456", "prompt": ""}
        assert get_task_id(rec) == "[t-123456]"


# ── Additional load_jsonl tests ──────────────────────────────────────────


class TestLoadJsonlExtra:
    """Additional edge cases for load_jsonl."""

    def test_extra_fields_preserved(self, tmp_path):
        """load_jsonl preserves extra fields in records."""
        records = [
            {
                "ts": "2026-04-01T10:00:00Z",
                "provider": "zhipu",
                "custom_field": "custom_value",
                "nested": {"key": "val"},
            },
        ]
        jsonl_path = _make_jsonl(tmp_path, records)
        original = _mod["JSONL_FILE"]
        try:
            _mod["JSONL_FILE"] = jsonl_path
            result = load_jsonl("2026-04-01")
        finally:
            _mod["JSONL_FILE"] = original
        assert len(result) == 1
        assert result[0]["custom_field"] == "custom_value"
        assert result[0]["nested"]["key"] == "val"

    def test_multiple_records_same_timestamp(self, tmp_path):
        """load_jsonl handles multiple records with identical timestamps."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "zhipu"},
            {"ts": "2026-04-01T10:00:00Z", "provider": "infini"},
            {"ts": "2026-04-01T10:00:00Z", "provider": "volcano"},
        ]
        jsonl_path = _make_jsonl(tmp_path, records)
        original = _mod["JSONL_FILE"]
        try:
            _mod["JSONL_FILE"] = jsonl_path
            result = load_jsonl("2026-04-01")
        finally:
            _mod["JSONL_FILE"] = original
        assert len(result) == 3

    def test_large_file_many_records(self, tmp_path):
        """load_jsonl handles files with many records."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": f"p{i % 5}", "exit": i % 2}
            for i in range(500)
        ]
        jsonl_path = _make_jsonl(tmp_path, records)
        original = _mod["JSONL_FILE"]
        try:
            _mod["JSONL_FILE"] = jsonl_path
            result = load_jsonl("2026-04-01")
        finally:
            _mod["JSONL_FILE"] = original
        assert len(result) == 500


# ── Additional generate_report tests ─────────────────────────────────────


class TestGenerateReportExtra:
    """Additional edge cases for generate_report."""

    def test_records_without_prompt_field(self):
        """generate_report handles records missing prompt field."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "zhipu", "exit": 0, "duration": 60},
        ]
        report = generate_report(records, "2026-04-01")
        assert "| Total tasks | 1 |" in report
        assert "| Succeeded | 1 |" in report

    def test_fewer_than_3_tasks_for_longest(self):
        """generate_report shows only available tasks when < 3 total."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "zhipu", "exit": 0, "duration": 60, "prompt": "task1"},
        ]
        report = generate_report(records, "2026-04-01")
        assert "## Top 3 Longest Tasks" in report
        assert "1." in report
        assert "2." not in report

    def test_fewer_than_3_retried_tasks(self):
        """generate_report shows available retried tasks when < 3 unique IDs."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "task_id": "t-aaa", "provider": "zhipu", "exit": 0, "duration": 60, "prompt": "[t-aaa] task"},
            {"ts": "2026-04-01T10:05:00Z", "task_id": "t-aaa", "provider": "zhipu", "exit": 1, "duration": 30, "prompt": "[t-aaa] retry"},
        ]
        report = generate_report(records, "2026-04-01")
        assert "## Top 3 Most-Retried Tasks" in report
        assert "2 attempts" in report
        # Only 1 unique task ID, so only "1." entry
        assert "2. " not in report.split("## Top 3 Most-Retried Tasks")[1].split("##")[0]

    def test_provider_stats_accuracy(self):
        """generate_report shows correct per-provider stats."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "alpha", "exit": 0, "duration": 100, "prompt": "t1"},
            {"ts": "2026-04-01T10:05:00Z", "provider": "alpha", "exit": 1, "duration": 50, "prompt": "t2"},
            {"ts": "2026-04-01T10:10:00Z", "provider": "beta", "exit": 0, "duration": 200, "prompt": "t3"},
        ]
        report = generate_report(records, "2026-04-01")
        # alpha: 2 tasks, 1 success = 50%, avg dur = 75s
        assert "| alpha | 2 | 1 | 50% | 75s | 0 |" in report
        # beta: 1 task, 1 success = 100%, avg dur = 200s
        assert "| beta | 1 | 1 | 100% | 200s | 0 |" in report

    def test_longest_tasks_with_tie_duration(self):
        """generate_report handles ties in duration for top 3."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "a", "exit": 0, "duration": 100, "prompt": "t1"},
            {"ts": "2026-04-01T10:05:00Z", "provider": "b", "exit": 0, "duration": 100, "prompt": "t2"},
            {"ts": "2026-04-01T10:10:00Z", "provider": "c", "exit": 0, "duration": 50, "prompt": "t3"},
        ]
        report = generate_report(records, "2026-04-01")
        assert "100s" in report
        assert "50s" in report

    def test_duration_minutes_formatting(self):
        """generate_report formats large durations as minutes correctly."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "a", "exit": 0, "duration": 3600, "prompt": "t1"},
        ]
        report = generate_report(records, "2026-04-01")
        assert "3600s (60.0m)" in report

    def test_all_succeeded_rate_limits_zero(self):
        """generate_report shows 0 rate-limit events when all tasks succeed."""
        records = [
            {"ts": "2026-04-01T10:00:00Z", "provider": "zhipu", "exit": 0, "duration": 60, "prompt": "t1"},
            {"ts": "2026-04-01T10:05:00Z", "provider": "infini", "exit": 0, "duration": 90, "prompt": "t2"},
        ]
        report = generate_report(records, "2026-04-01")
        assert "| Rate-limit events | 0 |" in report


# ── Additional CLI tests ─────────────────────────────────────────────────


class TestMainCliExtra:
    """Additional CLI integration tests via subprocess.run."""

    REPORT_PATH = Path.home() / "germline/effectors/golem-report"

    def _run(self, args: list[str]) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(self.REPORT_PATH)] + args
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10)

    def test_json_output_structure_empty(self):
        """golem-report --json with no matching records has correct structure."""
        result = self._run(["--date", "2099-06-15", "--json"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["date"] == "2099-06-15"
        assert data["total"] == 0
        assert isinstance(data["records"], list)

    def test_help_shows_date_and_json_options(self):
        """golem-report --help documents --date and --json flags."""
        result = self._run(["--help"])
        assert "--date" in result.stdout
        assert "--json" in result.stdout

    def test_no_args_uses_today(self):
        """golem-report with no args generates a report for today."""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        result = self._run([])
        assert result.returncode == 0
        assert today in result.stdout

    def test_markdown_output_default(self):
        """golem-report outputs markdown by default (not JSON)."""
        result = self._run(["--date", "2099-01-01"])
        assert result.returncode == 0
        assert "# Golem Report" in result.stdout
        # Should not be valid JSON (no surrounding braces)
        assert not result.stdout.strip().startswith("{")

    def test_exit_code_success(self):
        """golem-report exits with code 0 on normal invocation."""
        result = self._run(["--date", "2020-01-01"])
        assert result.returncode == 0
