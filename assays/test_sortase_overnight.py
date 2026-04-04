from __future__ import annotations

"""Tests for metabolon.sortase.overnight module."""


import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from metabolon.sortase.overnight import (
    compute_overnight_stats,
    format_overnight_report,
    load_overnight_entries,
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


class TestLoadOvernightEntries:
    def test_load_overnight_entries_filters_by_time(self, tmp_path: Path) -> None:
        log_path = tmp_path / "log.jsonl"
        now = datetime.now()
        recent = now - timedelta(hours=2)
        old = now - timedelta(hours=12)
        entries = [
            _make_entry(recent.isoformat(timespec="seconds"), plan="recent.md"),
            _make_entry(old.isoformat(timespec="seconds"), plan="old.md"),
        ]
        _write_log(log_path, entries)

        result = load_overnight_entries(log_path, since_hours=8)
        assert len(result) == 1
        assert result[0]["plan"] == "recent.md"

    def test_load_overnight_entries_returns_all_within_window(self, tmp_path: Path) -> None:
        log_path = tmp_path / "log.jsonl"
        now = datetime.now()
        entries = [
            _make_entry(
                (now - timedelta(hours=h)).isoformat(timespec="seconds"), plan=f"plan-{h}.md"
            )
            for h in [1, 3, 5, 7]
        ]
        _write_log(log_path, entries)

        result = load_overnight_entries(log_path, since_hours=8)
        assert len(result) == 4

    def test_load_overnight_entries_empty_log(self, tmp_path: Path) -> None:
        log_path = tmp_path / "log.jsonl"
        _write_log(log_path, [])

        result = load_overnight_entries(log_path, since_hours=8)
        assert result == []

    def test_load_overnight_entries_malformed_line_skipped(self, tmp_path: Path) -> None:
        log_path = tmp_path / "log.jsonl"
        now = datetime.now()
        with log_path.open("w", encoding="utf-8") as handle:
            handle.write("not json\n")
            handle.write(json.dumps(_make_entry(now.isoformat(timespec="seconds"))) + "\n")
            handle.write("\n")

        result = load_overnight_entries(log_path, since_hours=8)
        assert len(result) == 1

    def test_load_overnight_entries_missing_log_file(self, tmp_path: Path) -> None:
        log_path = tmp_path / "nonexistent.jsonl"
        result = load_overnight_entries(log_path, since_hours=8)
        assert result == []


class TestComputeOvernightStats:
    def test_compute_overnight_stats_success_rate(self) -> None:
        entries = [
            _make_entry("2026-03-31T01:00:00", success=True),
            _make_entry("2026-03-31T02:00:00", success=True),
            _make_entry("2026-03-31T03:00:00", success=False, failure_reason="placeholder-scan"),
        ]
        stats = compute_overnight_stats(entries)
        assert stats["total"] == 3
        assert stats["successes"] == 2
        assert stats["failures"] == 1
        assert stats["success_rate"] == pytest.approx(2 / 3, abs=0.01)

    def test_compute_overnight_stats_empty_log(self) -> None:
        stats = compute_overnight_stats([])
        assert stats["total"] == 0
        assert stats["successes"] == 0
        assert stats["failures"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["avg_duration_s"] == 0.0
        assert stats["backend_distribution"] == {}
        assert stats["failure_reasons"] == {}
        assert stats["plans"] == []
        assert stats["projects"] == []

    def test_compute_overnight_stats_backend_distribution(self) -> None:
        entries = [
            _make_entry("2026-03-31T01:00:00", tool="droid"),
            _make_entry("2026-03-31T02:00:00", tool="droid"),
            _make_entry("2026-03-31T03:00:00", tool="gemini"),
        ]
        stats = compute_overnight_stats(entries)
        assert stats["backend_distribution"]["droid"] == 2
        assert stats["backend_distribution"]["gemini"] == 1

    def test_compute_overnight_stats_avg_duration(self) -> None:
        entries = [
            _make_entry("2026-03-31T01:00:00", duration_s=100.0),
            _make_entry("2026-03-31T02:00:00", duration_s=200.0),
        ]
        stats = compute_overnight_stats(entries)
        assert stats["avg_duration_s"] == pytest.approx(150.0)

    def test_compute_overnight_stats_failure_reasons(self) -> None:
        entries = [
            _make_entry("2026-03-31T01:00:00", success=False, failure_reason="placeholder-scan"),
            _make_entry("2026-03-31T02:00:00", success=False, failure_reason="placeholder-scan"),
            _make_entry("2026-03-31T03:00:00", success=False, failure_reason="tests"),
        ]
        stats = compute_overnight_stats(entries)
        assert stats["failure_reasons"]["placeholder-scan"] == 2
        assert stats["failure_reasons"]["tests"] == 1

    def test_compute_overnight_stats_plans_and_projects(self) -> None:
        entries = [
            _make_entry("2026-03-31T01:00:00", plan="plan-a.md", project="proj-x"),
            _make_entry("2026-03-31T02:00:00", plan="plan-b.md", project="proj-x"),
            _make_entry("2026-03-31T03:00:00", plan="plan-a.md", project="proj-y"),
        ]
        stats = compute_overnight_stats(entries)
        assert sorted(stats["plans"]) == ["plan-a.md", "plan-b.md"]
        assert sorted(stats["projects"]) == ["proj-x", "proj-y"]


class TestFormatOvernightReport:
    def test_format_overnight_report_contains_key_sections(self) -> None:
        entries = [
            _make_entry(
                "2026-03-31T01:00:00",
                success=True,
                tool="droid",
                plan="alpha.md",
                project="germline",
            ),
            _make_entry(
                "2026-03-31T02:00:00",
                success=False,
                tool="gemini",
                failure_reason="placeholder-scan",
                plan="beta.md",
                project="germline",
            ),
        ]
        stats = compute_overnight_stats(entries)
        report = format_overnight_report(stats, entries)

        assert "# Overnight Report" in report
        assert "Summary" in report
        assert "Backend Distribution" in report
        assert "Failure Reasons" in report
        assert "Plans Executed" in report
        assert "droid" in report
        assert "gemini" in report
        assert "placeholder-scan" in report
        assert "alpha.md" in report
        assert "beta.md" in report

    def test_format_overnight_report_empty_entries(self) -> None:
        stats = compute_overnight_stats([])
        report = format_overnight_report(stats, [])
        assert "No entries found" in report

    def test_format_overnight_report_success_rate_displayed(self) -> None:
        entries = [
            _make_entry("2026-03-31T01:00:00", success=True),
            _make_entry("2026-03-31T02:00:00", success=True),
        ]
        stats = compute_overnight_stats(entries)
        report = format_overnight_report(stats, entries)
        assert "100.0%" in report

    def test_format_overnight_report_duration_displayed(self) -> None:
        entries = [
            _make_entry("2026-03-31T01:00:00", duration_s=45.0),
        ]
        stats = compute_overnight_stats(entries)
        report = format_overnight_report(stats, entries)
        assert "45.0s" in report
