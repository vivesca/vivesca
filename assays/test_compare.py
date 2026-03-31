from __future__ import annotations
"""Tests for metabolon.sortase.compare."""

import tempfile
from pathlib import Path

from metabolon.sortase.compare import (
    CompareDelta,
    compare_sessions,
    load_session_entries,
    format_compare_report,
    _delta_str,
    _session_stats,
    _failure_reasons,
)


def test_delta_str_increase():
    result = _delta_str(50.0, 75.0)
    assert "↑" in result
    assert "50%" in result


def test_delta_str_decrease():
    result = _delta_str(100.0, 80.0)
    assert "↓" in result
    assert "20%" in result


def test_delta_str_zero_base():
    assert _delta_str(0, 10) == ""


def test_delta_str_no_change():
    result = _delta_str(42.0, 42.0)
    assert "→" in result
    assert "0%" in result


def test_session_stats_empty():
    count, rate, avg = _session_stats([])
    assert count == 0
    assert rate == 0.0
    assert avg == 0.0


def test_session_stats_all_success():
    entries = [
        {"success": True, "duration_s": 10.0},
        {"success": True, "duration_s": 20.0},
    ]
    count, rate, avg = _session_stats(entries)
    assert count == 2
    assert rate == 1.0
    assert avg == 15.0


def test_session_stats_mixed():
    entries = [
        {"success": True, "duration_s": 10.0},
        {"success": False, "duration_s": 5.0},
    ]
    count, rate, avg = _session_stats(entries)
    assert count == 2
    assert rate == 0.5
    assert avg == 7.5


def test_failure_reasons_extraction():
    entries = [
        {"success": False, "failure_reason": "timeout"},
        {"success": False, "failure_reason": "syntax error"},
        {"success": True, "failure_reason": None},
        {"success": False, "failure_reason": "timeout"},
    ]
    reasons = _failure_reasons(entries)
    assert reasons == {"timeout", "syntax error"}


def test_load_session_entries_nonexistent():
    entries = load_session_entries(Path("/nonexistent.jsonl"), "2026-03-31")
    assert entries == []


def test_load_session_entries_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"timestamp": "2026-03-31T10:00:00", "success": true}\n')
        f.write('{"timestamp": "2026-03-30T09:00:00", "success": false}\n')
        f.write('{"timestamp": "2026-03-31T11:00:00", "success": false}\n')
    path = Path(f.name)
    try:
        entries = load_session_entries(path, "2026-03-31")
        assert len(entries) == 2
    finally:
        path.unlink()


def test_compare_sessions_both_empty():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        pass
    path = Path(f.name)
    try:
        delta = compare_sessions(path, "2026-03-30", "2026-03-31")
        assert isinstance(delta, CompareDelta)
        assert delta.task_count_a == 0
        assert delta.task_count_b == 0
        assert delta.success_rate_a == 0.0
        assert delta.success_rate_b == 0.0
        assert delta.new_failures == []
        assert delta.resolved_failures == []
    finally:
        path.unlink()


def test_compare_sessions_calculates_deltas():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"timestamp": "2026-03-30T10:00:00", "success": false, "failure_reason": "timeout", "duration_s": 30}\n')
        f.write('{"timestamp": "2026-03-30T11:00:00", "success": true, "duration_s": 20}\n')
        f.write('{"timestamp": "2026-03-31T10:00:00", "success": true, "duration_s": 25}\n')
        f.write('{"timestamp": "2026-03-31T11:00:00", "success": true, "duration_s": 15}\n')
        f.write('{"timestamp": "2026-03-31T12:00:00", "success": true, "duration_s": 20}\n')
    path = Path(f.name)
    try:
        delta = compare_sessions(path, "2026-03-30", "2026-03-31")
        assert delta.task_count_a == 2
        assert delta.task_count_b == 3
        assert delta.task_count_delta == 1
        assert delta.success_rate_a == 0.5
        assert delta.success_rate_b == 1.0
        assert delta.success_rate_delta == 0.5
        assert "timeout" in delta.resolved_failures
        assert delta.new_failures == []
    finally:
        path.unlink()


def test_format_compare_report():
    delta = CompareDelta(
        date_a="2026-03-30",
        date_b="2026-03-31",
        task_count_a=2,
        task_count_b=4,
        task_count_delta=2,
        success_rate_a=0.5,
        success_rate_b=0.75,
        success_rate_delta=0.25,
        avg_duration_a=30.0,
        avg_duration_b=25.0,
        avg_duration_delta=-5.0,
        new_failures=["network error"],
        resolved_failures=["timeout"],
    )
    report = format_compare_report(delta)
    assert "Session Comparison" in report
    assert "2026-03-30" in report
    assert "2026-03-31" in report
    assert "Success rate" in report
    assert "New failures introduced" in report
    assert "Resolved failures" in report
    assert "network error" in report
    assert "timeout" in report
