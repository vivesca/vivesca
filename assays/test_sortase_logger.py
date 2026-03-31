from __future__ import annotations
"""Tests for sortase logger."""

from datetime import datetime

from metabolon.sortase.logger import aggregate_stats, append_log, read_logs


def test_append_and_read(tmp_path):
    log_file = tmp_path / "log.jsonl"
    entry = {"timestamp": "2026-03-30T00:00:00", "tool": "droid", "success": True, "duration_s": 30.0}
    append_log(entry, path=str(log_file))
    logs = read_logs(path=str(log_file))
    assert len(logs) == 1
    assert logs[0]["tool"] == "droid"


def test_read_empty(tmp_path):
    log_file = tmp_path / "log.jsonl"
    logs = read_logs(path=str(log_file))
    assert logs == []


def test_aggregate_stats_basic():
    now = datetime.now()
    entries = [
        {"tool": "droid", "success": True, "duration_s": 30.0, "timestamp": now.isoformat(), "fallbacks": [], "failure_reason": None},
        {"tool": "droid", "success": True, "duration_s": 60.0, "timestamp": now.isoformat(), "fallbacks": [], "failure_reason": None},
        {"tool": "droid", "success": False, "duration_s": 90.0, "timestamp": now.isoformat(), "fallbacks": ["gemini"], "failure_reason": "process-error"},
    ]
    stats = aggregate_stats(entries)
    droid = stats["per_tool"]["droid"]
    assert droid["runs"] == 3
    assert droid["success_rate"] == round(2 / 3, 3)
    assert droid["p50_duration_s"] == 60.0
    assert droid["last_24h"] == 3
    assert droid["coaching_triggers"] == 1


def test_aggregate_stats_empty():
    stats = aggregate_stats([])
    assert stats["per_tool"] == {}


def test_aggregate_stats_fallback_frequency():
    entries = [
        {"tool": "droid", "success": True, "duration_s": 10, "timestamp": "2026-01-01T00:00:00", "fallbacks": ["gemini", "codex"], "failure_reason": None},
    ]
    stats = aggregate_stats(entries)
    assert stats["fallback_frequency"]["gemini"] == 1
    assert stats["fallback_frequency"]["codex"] == 1
