"""Tests for metabolon.organelles.tachometer."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from metabolon.organelles.tachometer import (
    coaching_effectiveness,
    current_rate,
    estimate_completion,
    slowest_recent,
    success_trend,
)


def _write_log(path: Path, entries: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")


def _make_entry(
    offset_minutes: int = 0,
    success: bool = True,
    duration_s: float = 100.0,
    plan: str = "test-plan",
    tool: str = "droid",
    failure_reason: str | None = None,
) -> dict:
    ts = (datetime.now() - timedelta(minutes=offset_minutes)).isoformat()
    entry: dict = {
        "duration_s": duration_s,
        "success": success,
        "plan": plan,
        "tool": tool,
        "timestamp": ts,
        "files_changed": 1,
        "tasks": 1,
        "tests_passed": 1,
        "fallbacks": [],
    }
    if failure_reason:
        entry["failure_reason"] = failure_reason
    return entry


# ---------------------------------------------------------------------------
# current_rate
# ---------------------------------------------------------------------------


def test_current_rate_with_entries(tmp_path: Path) -> None:
    log = tmp_path / "log.jsonl"
    entries = [_make_entry(offset_minutes=5), _make_entry(offset_minutes=30), _make_entry(offset_minutes=55)]
    _write_log(log, entries)

    rate = current_rate(log_path=log)
    assert rate == 3.0


def test_current_rate_empty_log(tmp_path: Path) -> None:
    log = tmp_path / "log.jsonl"
    log.touch()

    rate = current_rate(log_path=log)
    assert rate == 0.0


# ---------------------------------------------------------------------------
# success_trend
# ---------------------------------------------------------------------------


def test_success_trend(tmp_path: Path) -> None:
    log = tmp_path / "log.jsonl"
    # 8 successes + 2 failures in last 10; 13 successes + 2 failures in last 100 (15 total)
    entries = [
        *[_make_entry(offset_minutes=i, success=True) for i in range(100, 85, -1)],  # 15 old successes
        _make_entry(offset_minutes=80, success=False, failure_reason="tests"),
        _make_entry(offset_minutes=70, success=False, failure_reason="placeholder-scan"),
        *[_make_entry(offset_minutes=i, success=True) for i in range(8)],  # 8 recent successes
        _make_entry(offset_minutes=9, success=False, failure_reason="tests"),
        _make_entry(offset_minutes=10, success=False, failure_reason="quota"),
    ]
    _write_log(log, entries)

    trend = success_trend(log_path=log)
    assert trend["recent_count"] == 10
    assert trend["recent_rate"] == 0.8  # 8/10
    assert trend["direction"] in ("stable", "improving", "declining")


# ---------------------------------------------------------------------------
# slowest_recent
# ---------------------------------------------------------------------------


def test_slowest_recent(tmp_path: Path) -> None:
    log = tmp_path / "log.jsonl"
    entries = [
        _make_entry(offset_minutes=5, duration_s=50.0, plan="fast-plan"),
        _make_entry(offset_minutes=10, duration_s=300.0, plan="slow-plan"),
        _make_entry(offset_minutes=120, duration_s=999.0, plan="old-plan"),  # outside 1h window
    ]
    _write_log(log, entries)

    slowest = slowest_recent(log_path=log, hours=1)
    assert slowest is not None
    assert slowest["plan"] == "slow-plan"
    assert slowest["duration_s"] == 300.0


# ---------------------------------------------------------------------------
# estimate_completion
# ---------------------------------------------------------------------------


def test_estimate_completion(tmp_path: Path) -> None:
    log = tmp_path / "log.jsonl"
    # 4 entries, each 360s = 6 min. avg = 360s. 10 tasks = 3600s = 1.0 hour
    entries = [_make_entry(offset_minutes=i, duration_s=360.0) for i in range(4)]
    _write_log(log, entries)

    hours = estimate_completion(log_path=log, remaining_tasks=10)
    assert hours == 1.0
