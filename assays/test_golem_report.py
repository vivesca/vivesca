from __future__ import annotations

"""Tests for golem-report — analytics report from golem task logs."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_golem_report():
    """Load the golem-report module by exec-ing its Python body."""
    source = open(str(Path.home() / "germline/effectors/golem-report")).read()
    ns: dict = {"__name__": "golem_report"}
    exec(source, ns)
    return ns


_mod = _load_golem_report()
parse_timestamp = _mod["parse_timestamp"]
extract_task_id = _mod["extract_task_id"]
get_task_id = _mod["get_task_id"]
is_rate_limited = _mod["is_rate_limited"]
truncate_prompt = _mod["truncate_prompt"]
load_jsonl = _mod["load_jsonl"]
generate_report = _mod["generate_report"]
parse_args = _mod["parse_args"]
JSONL_FILE = _mod["JSONL_FILE"]
RATE_LIMIT_PATTERNS = _mod["RATE_LIMIT_PATTERNS"]


# ── parse_timestamp ──────────────────────────────────────────────────────


def test_parse_timestamp_utc_z_suffix():
    """Parses ISO timestamp with Z suffix."""
    dt = parse_timestamp("2026-04-01T12:30:00Z")
    assert dt is not None
    assert dt.year == 2026 and dt.month == 4 and dt.day == 1
    assert dt.hour == 12 and dt.minute == 30


def test_parse_timestamp_no_suffix():
    """Parses ISO timestamp without Z suffix."""
    dt = parse_timestamp("2026-04-01T12:30:00")
    assert dt is not None
    assert dt.year == 2026


def test_parse_timestamp_microseconds():
    """Parses ISO timestamp with microseconds and Z."""
    dt = parse_timestamp("2026-04-01T12:30:00.123456Z")
    assert dt is not None
    assert dt.year == 2026


def test_parse_timestamp_invalid_returns_none():
    """Returns None for unparseable strings."""
    assert parse_timestamp("not-a-date") is None
    assert parse_timestamp("") is None


# ── extract_task_id ─────────────────────────────────────────────────────


def test_extract_task_id_found():
    """Extracts [t-abc123] from prompt text."""
    assert extract_task_id("some prompt [t-deadbeef] rest") == "[t-deadbeef]"


def test_extract_task_id_not_found():
    """Returns empty string when no task ID present."""
    assert extract_task_id("plain prompt no id") == ""


def test_extract_task_id_hex_only():
    """Matches hex characters in task ID."""
    assert extract_task_id("[t-0123456789abcdef]") == "[t-0123456789abcdef]"


# ── get_task_id ──────────────────────────────────────────────────────────


def test_get_task_id_from_field():
    """Reads task_id field directly from record."""
    assert get_task_id({"task_id": "t-cafe"}) == "[t-cafe]"


def test_get_task_id_field_already_bracketed():
    """Does not double-bracket if task_id already has brackets."""
    assert get_task_id({"task_id": "[t-cafe]"}) == "[t-cafe]"


def test_get_task_id_from_prompt():
    """Falls back to extracting from prompt when no task_id field."""
    assert get_task_id({"prompt": "work [t-babe] done"}) == "[t-babe]"


def test_get_task_id_empty():
    """Returns empty string when no ID available."""
    assert get_task_id({"prompt": "no id here"}) == ""


# ── is_rate_limited ─────────────────────────────────────────────────────


def test_is_rate_limited_429():
    """Detects 429 in tail output."""
    assert is_rate_limited({"tail": "Error 429 Too Many Requests"}) is True


def test_is_rate_limited_quota_exceeded():
    """Detects AccountQuotaExceeded in tail."""
    assert is_rate_limited({"tail": "AccountQuotaExceeded for user"}) is True


def test_is_rate_limited_normal():
    """Returns False for normal (non-rate-limited) records."""
    assert is_rate_limited({"tail": "task completed successfully"}) is False


def test_is_rate_limited_exit1_short_empty():
    """Detects rate limit heuristic: exit=1, empty tail, short duration."""
    assert is_rate_limited({"exit": 1, "tail": "   ", "duration": 5}) is True


def test_is_rate_limited_exit1_long_not_rate():
    """Does not flag exit=1 with longer duration as rate limit."""
    assert is_rate_limited({"exit": 1, "tail": "   ", "duration": 60}) is False


# ── truncate_prompt ─────────────────────────────────────────────────────


def test_truncate_prompt_short():
    """Returns short prompt unchanged."""
    assert truncate_prompt("hello") == "hello"


def test_truncate_prompt_long():
    """Truncates long prompt with ellipsis."""
    long_text = "a" * 100
    result = truncate_prompt(long_text, max_len=60)
    assert len(result) == 60
    assert result.endswith("...")


def test_truncate_prompt_strips_coaching():
    """Removes <coaching-notes> blocks before truncating."""
    prompt = "<coaching-notes>stuff\n---\nreal prompt text here"
    result = truncate_prompt(prompt)
    assert "<coaching-notes>" not in result
    assert "real prompt text here" in result


# ── load_jsonl ──────────────────────────────────────────────────────────


def test_load_jsonl_file_not_found(tmp_path, monkeypatch):
    """Returns empty list when JSONL file does not exist."""
    monkeypatch.setattr(_mod["__name__"] + ".JSONL_FILE", tmp_path / "nope.jsonl")
    # Need to patch the module-level JSONL_FILE in the exec'd namespace
    _mod["JSONL_FILE"] = tmp_path / "nope.jsonl"
    try:
        result = load_jsonl(None)
        assert result == []
    finally:
        _mod["JSONL_FILE"] = JSONL_FILE


def test_load_jsonl_parses_records(tmp_path):
    """Parses valid JSONL records."""
    jf = tmp_path / "golem.jsonl"
    records = [
        {"ts": "2026-04-01T10:00:00Z", "provider": "volcano", "exit": 0, "duration": 120},
        {"ts": "2026-04-01T11:00:00Z", "provider": "infini", "exit": 1, "duration": 30},
    ]
    jf.write_text("\n".join(json.dumps(r) for r in records))
    _mod["JSONL_FILE"] = jf
    try:
        result = load_jsonl("2026-04-01")
        assert len(result) == 2
        assert result[0]["provider"] == "volcano"
        assert "_dt" in result[0]
    finally:
        _mod["JSONL_FILE"] = JSONL_FILE


def test_load_jsonl_date_filter(tmp_path):
    """Filters records by date string."""
    jf = tmp_path / "golem.jsonl"
    records = [
        {"ts": "2026-04-01T10:00:00Z", "provider": "a"},
        {"ts": "2026-04-02T10:00:00Z", "provider": "b"},
    ]
    jf.write_text("\n".join(json.dumps(r) for r in records))
    _mod["JSONL_FILE"] = jf
    try:
        result = load_jsonl("2026-04-01")
        assert len(result) == 1
        assert result[0]["provider"] == "a"
    finally:
        _mod["JSONL_FILE"] = JSONL_FILE


def test_load_jsonl_skips_bad_json(tmp_path):
    """Skips lines that are not valid JSON."""
    jf = tmp_path / "golem.jsonl"
    jf.write_text('{"ts":"2026-04-01T10:00:00Z","provider":"ok"}\nBADLINE\n')
    _mod["JSONL_FILE"] = jf
    try:
        result = load_jsonl("2026-04-01")
        assert len(result) == 1
    finally:
        _mod["JSONL_FILE"] = JSONL_FILE


def test_load_jsonl_no_filter(tmp_path):
    """Returns all records when no date filter is given."""
    jf = tmp_path / "golem.jsonl"
    records = [
        {"ts": "2026-03-30T10:00:00Z", "provider": "a"},
        {"ts": "2026-04-01T10:00:00Z", "provider": "b"},
    ]
    jf.write_text("\n".join(json.dumps(r) for r in records))
    _mod["JSONL_FILE"] = jf
    try:
        result = load_jsonl(None)
        assert len(result) == 2
    finally:
        _mod["JSONL_FILE"] = JSONL_FILE


# ── generate_report ─────────────────────────────────────────────────────


def test_generate_report_empty():
    """Generates report with no-data message for empty records."""
    report = generate_report([], "2026-04-01")
    assert "# Golem Report — 2026-04-01" in report
    assert "No tasks recorded" in report


def test_generate_report_summary_table():
    """Generates summary table with correct stats."""
    records = [
        {"exit": 0, "duration": 120, "provider": "volcano", "prompt": "task1"},
        {"exit": 1, "duration": 30, "provider": "infini", "prompt": "task2"},
    ]
    report = generate_report(records, "2026-04-01")
    assert "Total tasks | 2" in report
    assert "Succeeded | 1" in report
    assert "Failed | 1" in report
    assert "50.0%" in report


def test_generate_report_provider_breakdown():
    """Includes per-provider breakdown."""
    records = [
        {"exit": 0, "duration": 100, "provider": "volcano", "prompt": "a"},
        {"exit": 0, "duration": 200, "provider": "infini", "prompt": "b"},
        {"exit": 1, "duration": 50, "provider": "volcano", "prompt": "c"},
    ]
    report = generate_report(records, "2026-04-01")
    assert "## By Provider" in report
    assert "| volcano |" in report
    assert "| infini |" in report


def test_generate_report_top3_longest():
    """Lists top 3 longest tasks."""
    records = [
        {"exit": 0, "duration": d, "provider": "p", "prompt": f"task-{d}"}
        for d in [500, 400, 300, 200, 100]
    ]
    report = generate_report(records, "2026-04-01")
    assert "## Top 3 Longest Tasks" in report
    # First entry should be the 500s task
    assert "500s" in report


def test_generate_report_top3_retried():
    """Lists top 3 most-retried tasks by task_id."""
    records = [
        {"exit": 0, "duration": 10, "provider": "p", "prompt": "[t-aaa] do thing", "task_id": "t-aaa"},
        {"exit": 1, "duration": 10, "provider": "p", "prompt": "[t-aaa] do thing", "task_id": "t-aaa"},
        {"exit": 0, "duration": 10, "provider": "p", "prompt": "[t-bbb] other", "task_id": "t-bbb"},
    ]
    report = generate_report(records, "2026-04-01")
    assert "## Top 3 Most-Retried Tasks" in report
    assert "[t-aaa]" in report
    assert "2 attempts" in report


def test_generate_report_no_task_ids():
    """Shows fallback message when no task IDs found."""
    records = [
        {"exit": 0, "duration": 10, "provider": "p", "prompt": "no id"},
    ]
    report = generate_report(records, "2026-04-01")
    assert "No task IDs found" in report


def test_generate_report_rate_limits():
    """Counts rate-limit events in summary."""
    records = [
        {"exit": 0, "duration": 10, "provider": "p", "prompt": "ok", "tail": "done"},
        {"exit": 1, "duration": 5, "provider": "p", "prompt": "fail", "tail": "429 rate limited"},
    ]
    report = generate_report(records, "2026-04-01")
    assert "Rate-limit events | 1" in report


# ── parse_args ──────────────────────────────────────────────────────────


def test_parse_args_default():
    """Default args: no date, no json flag."""
    with patch("sys.argv", ["golem-report"]):
        args = parse_args()
    assert args.date is None
    assert args.json is False


def test_parse_args_with_date():
    """Accepts --date flag."""
    with patch("sys.argv", ["golem-report", "--date", "2026-04-01"]):
        args = parse_args()
    assert args.date == "2026-04-01"


def test_parse_args_json_flag():
    """Accepts --json flag."""
    with patch("sys.argv", ["golem-report", "--json"]):
        args = parse_args()
    assert args.json is True
