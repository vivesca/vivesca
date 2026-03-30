"""Tests for metabolon.sortase.compare module."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from metabolon.sortase.compare import (
    CompareDelta,
    compare_sessions,
    format_compare_report,
    load_session_entries,
)


def _make_entry(
    timestamp: str,
    success: bool = True,
    tool: str = "droid",
    duration_s: float = 120.0,
    plan: str = "test-plan.md",
    project: str = "test-project",
    failure_reason: str | None = None,
    files_changed: int = 3,
) -> dict:
    entry = {
        "timestamp": timestamp,
        "success": success,
        "tool": tool,
        "duration_s": duration_s,
        "plan": plan,
        "project": project,
        "files_changed": files_changed,
    }
    if failure_reason:
        entry["failure_reason"] = failure_reason
    return entry


def _write_log(path: Path, entries: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")


class TestLoadSessionEntries:
    def test_loads_entries_for_given_date(self, tmp_path: Path) -> None:
        log_path = tmp_path / "log.jsonl"
        target_ts = "2026-03-30T02:15:00"
        other_ts = "2026-03-31T02:15:00"
        entries = [
            _make_entry(target_ts, plan="target.md"),
            _make_entry(other_ts, plan="other.md"),
        ]
        _write_log(log_path, entries)

        result = load_session_entries(log_path, "2026-03-30")
        assert len(result) == 1
        assert result[0]["plan"] == "target.md"

    def test_includes_entries_matching_date_prefix(self, tmp_path: Path) -> None:
        log_path = tmp_path / "log.jsonl"
        entries = [
            _make_entry("2026-03-30T01:00:00", plan="early.md"),
            _make_entry("2026-03-30T12:30:00", plan="midday.md"),
            _make_entry("2026-03-30T23:59:00", plan="late.md"),
        ]
        _write_log(log_path, entries)

        result = load_session_entries(log_path, "2026-03-30")
        assert len(result) == 3

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        log_path = tmp_path / "nonexistent.jsonl"
        result = load_session_entries(log_path, "2026-03-30")
        assert result == []

    def test_skips_malformed_lines(self, tmp_path: Path) -> None:
        log_path = tmp_path / "log.jsonl"
        with log_path.open("w", encoding="utf-8") as handle:
            handle.write("not json\n")
            handle.write(json.dumps(_make_entry("2026-03-30T01:00:00")) + "\n")
            handle.write("\n")

        result = load_session_entries(log_path, "2026-03-30")
        assert len(result) == 1


class TestCompareSessions:
    def test_improvement_across_sessions(self, tmp_path: Path) -> None:
        log_path = tmp_path / "log.jsonl"
        day_a = [
            _make_entry("2026-03-30T01:00:00", success=True, duration_s=100.0, plan="a1.md"),
            _make_entry("2026-03-30T02:00:00", success=False, duration_s=200.0, plan="a2.md", failure_reason="tests"),
            _make_entry("2026-03-30T03:00:00", success=True, duration_s=150.0, plan="a3.md"),
        ]
        day_b = [
            _make_entry("2026-03-31T01:00:00", success=True, duration_s=90.0, plan="b1.md"),
            _make_entry("2026-03-31T02:00:00", success=True, duration_s=110.0, plan="b2.md"),
        ]
        _write_log(log_path, day_a + day_b)

        delta = compare_sessions(log_path, "2026-03-30", "2026-03-31")

        assert delta.date_a == "2026-03-30"
        assert delta.date_b == "2026-03-31"
        assert delta.task_count_a == 3
        assert delta.task_count_b == 2
        assert delta.task_count_delta == -1
        assert delta.success_rate_a == pytest.approx(2 / 3)
        assert delta.success_rate_b == pytest.approx(1.0)
        assert delta.success_rate_delta == pytest.approx(1.0 - 2 / 3)
        assert delta.avg_duration_a == pytest.approx((100 + 200 + 150) / 3)
        assert delta.avg_duration_b == pytest.approx((90 + 110) / 2)
        assert delta.avg_duration_delta == pytest.approx(100.0 - 150.0)
        assert delta.new_failures == []
        assert delta.resolved_failures == ["tests"]

    def test_new_failures_detected(self, tmp_path: Path) -> None:
        log_path = tmp_path / "log.jsonl"
        day_a = [
            _make_entry("2026-03-30T01:00:00", success=True, duration_s=100.0, plan="a1.md"),
        ]
        day_b = [
            _make_entry("2026-03-31T01:00:00", success=False, duration_s=100.0, plan="b1.md", failure_reason="auth"),
            _make_entry("2026-03-31T02:00:00", success=False, duration_s=100.0, plan="b2.md", failure_reason="auth"),
            _make_entry("2026-03-31T03:00:00", success=True, duration_s=100.0, plan="b3.md"),
        ]
        _write_log(log_path, day_a + day_b)

        delta = compare_sessions(log_path, "2026-03-30", "2026-03-31")

        assert delta.new_failures == ["auth"]
        assert delta.resolved_failures == []
        assert delta.success_rate_delta < 0

    def test_empty_date_a(self, tmp_path: Path) -> None:
        log_path = tmp_path / "log.jsonl"
        day_b = [
            _make_entry("2026-03-31T01:00:00", success=True, duration_s=100.0, plan="b1.md"),
        ]
        _write_log(log_path, day_b)

        delta = compare_sessions(log_path, "2026-03-30", "2026-03-31")

        assert delta.task_count_a == 0
        assert delta.task_count_b == 1
        assert delta.success_rate_a == 0.0
        assert delta.success_rate_b == 1.0
        assert delta.avg_duration_a == 0.0
        assert delta.new_failures == []
        assert delta.resolved_failures == []


class TestFormatCompareReport:
    def test_formats_full_report(self, tmp_path: Path) -> None:
        log_path = tmp_path / "log.jsonl"
        day_a = [
            _make_entry("2026-03-30T01:00:00", success=True, duration_s=100.0, plan="a1.md"),
            _make_entry("2026-03-30T02:00:00", success=False, duration_s=200.0, plan="a2.md", failure_reason="tests"),
        ]
        day_b = [
            _make_entry("2026-03-31T01:00:00", success=True, duration_s=80.0, plan="b1.md"),
            _make_entry("2026-03-31T02:00:00", success=True, duration_s=90.0, plan="b2.md"),
        ]
        _write_log(log_path, day_a + day_b)
        delta = compare_sessions(log_path, "2026-03-30", "2026-03-31")
        report = format_compare_report(delta)

        assert "2026-03-30" in report
        assert "2026-03-31" in report
        assert "50.0%" in report  # success rate A
        assert "100.0%" in report  # success rate B
        assert "tests" in report  # resolved failure
        assert "Session Comparison" in report
