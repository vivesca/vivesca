from __future__ import annotations

"""Tests for golem-dash — live dashboard for golem task queue."""

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest


def _load_golem_dash():
    """Load golem-dash by exec-ing its source (effector, not importable)."""
    source = open(str(Path.home() / "germline/effectors/golem-dash")).read()
    ns: dict = {"__name__": "golem_dash_test"}
    exec(source, ns)
    return ns


_mod = _load_golem_dash()
parse_ts = _mod["parse_ts"]
is_rate_limited = _mod["is_rate_limited"]
fmt_duration = _mod["fmt_duration"]
fmt_eta = _mod["fmt_eta"]
sparkline = _mod["sparkline"]
compute_provider_stats = _mod["compute_provider_stats"]
compute_eta = _mod["compute_eta"]
compute_per_provider_eta = _mod["compute_per_provider_eta"]
compute_throughput_trend = _mod["compute_throughput_trend"]
compute_avg_duration_by_provider = _mod["compute_avg_duration_by_provider"]
estimate_task_progress = _mod["estimate_task_progress"]
compute_completions_per_minute = _mod["compute_completions_per_minute"]
build_running_tasks_table = _mod["build_running_tasks_table"]
build_drain_progress = _mod["build_drain_progress"]
count_pending_by_provider = _mod["count_pending_by_provider"]
count_total_pending = _mod["count_total_pending"]
count_total_completed = _mod["count_total_completed"]


# ── parse_ts ────────────────────────────────────────────────────────


def test_parse_ts_iso_with_z():
    """parse_ts handles ISO format with Z suffix."""
    dt = parse_ts("2025-06-15T12:30:00Z")
    assert dt.year == 2025
    assert dt.month == 6
    assert dt.hour == 12
    assert dt.tzinfo == timezone.utc


def test_parse_ts_iso_no_z():
    """parse_ts handles ISO format without Z."""
    dt = parse_ts("2025-06-15T12:30:00")
    assert dt.year == 2025
    assert dt.hour == 12


def test_parse_ts_space_separated():
    """parse_ts handles space-separated datetime."""
    dt = parse_ts("2025-06-15 12:30:00")
    assert dt.year == 2025


def test_parse_ts_invalid_returns_min():
    """parse_ts returns datetime.min for unparseable strings."""
    dt = parse_ts("not-a-date")
    assert dt == datetime.min.replace(tzinfo=timezone.utc)


# ── is_rate_limited ──────────────────────────────────────────────────


def test_rate_limited_429_in_tail():
    """Detects 429 in output tail."""
    rec = {"exit": 1, "duration": 30, "tail": "Error 429 Too Many Requests"}
    assert is_rate_limited(rec) is True


def test_rate_limited_quota_exceeded():
    """Detects quota exceeded."""
    rec = {"exit": 1, "duration": 5, "tail": "AccountQuotaExceeded for user"}
    assert is_rate_limited(rec) is True


def test_rate_limited_success_not_rl():
    """Successful task is never rate-limited."""
    rec = {"exit": 0, "duration": 60, "tail": "all good"}
    assert is_rate_limited(rec) is False


def test_rate_limited_fast_exit_empty():
    """Fast exit (<10s) with empty tail is rate-limit signal."""
    rec = {"exit": 1, "duration": 3, "tail": " "}
    assert is_rate_limited(rec) is True


def test_rate_limited_slow_failure():
    """Slow failure with non-RL error message is not rate-limited."""
    rec = {"exit": 1, "duration": 120, "tail": "syntax error in file"}
    assert is_rate_limited(rec) is False


def test_rate_limited_pattern_too_many_requests():
    """Detects 'too many requests' pattern."""
    rec = {"exit": 1, "duration": 30, "tail": "too many requests, slow down"}
    assert is_rate_limited(rec) is True


# ── fmt_duration / fmt_eta ──────────────────────────────────────────


def test_fmt_duration_seconds():
    assert fmt_duration(45) == "45s"


def test_fmt_duration_minutes():
    assert fmt_duration(180) == "3.0m"


def test_fmt_duration_hours():
    assert fmt_duration(7200) == "2.0h"


def test_fmt_eta_zero():
    assert fmt_eta(0) == "—"


def test_fmt_eta_negative():
    assert fmt_eta(-5) == "—"


def test_fmt_eta_seconds():
    assert fmt_eta(30) == "30s"


def test_fmt_eta_minutes():
    assert fmt_eta(300) == "5m"


def test_fmt_eta_hours():
    assert fmt_eta(7200) == "2.0h"


def test_fmt_eta_days():
    assert fmt_eta(172800) == "2.0d"


# ── sparkline ────────────────────────────────────────────────────────


def test_sparkline_empty():
    assert sparkline([]) == ""


def test_sparkline_all_zero():
    assert sparkline([0, 0, 0]) == "▁▁▁"


def test_sparkline_rising():
    s = sparkline([1, 2, 3, 4])
    assert len(s) == 4
    # Each char should be different (rising)
    assert s[0] != s[-1]


def test_sparkline_single():
    assert sparkline([5]) == "█"


# ── compute_avg_duration_by_provider ────────────────────────────────


def test_avg_duration_single_provider():
    """Compute average duration for a provider from records."""
    now = datetime.now(timezone.utc)
    records = [
        {"provider": "infini", "exit": 0, "duration": 120, "ts": now.isoformat()},
        {"provider": "infini", "exit": 0, "duration": 180, "ts": now.isoformat()},
        {"provider": "infini", "exit": 1, "duration": 60, "ts": now.isoformat()},  # failed, excluded
    ]
    avg = compute_avg_duration_by_provider(records)
    assert avg["infini"] == pytest.approx(150.0)


def test_avg_duration_no_successful():
    """No successful tasks returns empty dict."""
    records = [{"provider": "zhipu", "exit": 1, "duration": 60}]
    avg = compute_avg_duration_by_provider(records)
    assert "zhipu" not in avg


def test_avg_duration_multiple_providers():
    """Separate averages per provider."""
    records = [
        {"provider": "infini", "exit": 0, "duration": 100},
        {"provider": "volcano", "exit": 0, "duration": 200},
    ]
    avg = compute_avg_duration_by_provider(records)
    assert avg["infini"] == pytest.approx(100.0)
    assert avg["volcano"] == pytest.approx(200.0)


# ── estimate_task_progress ───────────────────────────────────────────


def test_task_progress_zero_elapsed():
    """No elapsed time = 0% progress."""
    assert estimate_task_progress(0, 120) == pytest.approx(0.0)


def test_task_progress_halfway():
    """Half avg duration = ~50% progress."""
    assert estimate_task_progress(60, 120) == pytest.approx(0.5)


def test_task_progress_full():
    """At avg duration = 100% capped."""
    assert estimate_task_progress(120, 120) == pytest.approx(1.0)


def test_task_progress_over_capped():
    """Beyond avg duration is capped at 1.0."""
    assert estimate_task_progress(300, 120) == pytest.approx(1.0)


def test_task_progress_no_avg():
    """No average duration available = 0 progress."""
    assert estimate_task_progress(60, 0) == pytest.approx(0.0)


# ── compute_completions_per_minute ──────────────────────────────────


def test_completions_per_minute_basic():
    """Count completions per minute over last N minutes."""
    now = datetime.now(timezone.utc)
    records = []
    # 6 completions in last 30 minutes
    for i in range(6):
        ts = (now - timedelta(minutes=i * 5)).isoformat()
        records.append({"exit": 0, "ts": ts, "provider": "infini"})
    # 1 failure (not counted)
    records.append({"exit": 1, "ts": now.isoformat(), "provider": "infini"})

    rate = compute_completions_per_minute(records, window_minutes=30)
    assert rate == pytest.approx(6 / 30)


def test_completions_per_minute_empty():
    """No records = 0 rate."""
    rate = compute_completions_per_minute([], window_minutes=30)
    assert rate == 0.0


# ── compute_provider_stats ──────────────────────────────────────────


def test_provider_stats_aggregation():
    """Correctly aggregates completed/failed/rate_limited per provider."""
    records = [
        {"provider": "zhipu", "exit": 0, "duration": 100},
        {"provider": "zhipu", "exit": 0, "duration": 200},
        {"provider": "zhipu", "exit": 1, "duration": 50, "tail": "syntax error"},
    ]
    stats = compute_provider_stats(records, [])
    s = stats["zhipu"]
    assert s["completed"] == 2
    assert s["failed"] == 1
    assert s["rate_limited"] == 0
    assert s["total_duration"] == pytest.approx(350.0)


def test_provider_stats_with_running():
    """Running tasks counted as active."""
    running = [{"task_id": "t1", "provider": "infini"}]
    stats = compute_provider_stats([], running)
    assert stats["infini"]["active"] == 1


# ── compute_eta ─────────────────────────────────────────────────────


def test_eta_no_pending():
    """No pending tasks = 0 ETA."""
    eta = compute_eta({}, {}, [])
    assert eta == 0.0


def test_eta_with_recent_completions():
    """ETA based on recent completions."""
    now = datetime.now(timezone.utc)
    all_records = []
    for i in range(5):
        ts = (now - timedelta(minutes=i * 10)).isoformat()
        all_records.append({"exit": 0, "ts": ts, "provider": "infini", "duration": 100})

    pending = {"infini": 10}
    stats = {"infini": {"active": 1, "completed": 5, "failed": 0, "rate_limited": 0,
                        "killed": 0, "total_duration": 500, "success_count": 5, "total_count": 5}}
    eta = compute_eta(stats, pending, all_records)
    # 5 completed in 1hr, 10 pending → (10/5)*3600 = 7200s = 2h
    assert eta == pytest.approx(7200.0)


def test_eta_no_recent_completions_uses_avg():
    """ETA falls back to avg duration when no recent completions."""
    all_records = [
        {"exit": 0, "ts": "2020-01-01T00:00:00Z", "provider": "infini", "duration": 300},
    ]
    pending = {"infini": 4}
    stats = {"infini": {"active": 2, "completed": 0, "failed": 0, "rate_limited": 0,
                        "killed": 0, "total_duration": 300, "success_count": 1, "total_count": 1}}
    eta = compute_eta(stats, pending, all_records)
    # avg=300s, active=2, pending=4 → (4/2)*300 = 600s
    assert eta == pytest.approx(600.0)


# ── build_drain_progress ────────────────────────────────────────────


def test_drain_progress_no_tasks():
    """No tasks = graceful message."""
    result = build_drain_progress(0, 0, 0.0)
    assert "No tasks" in result.plain


def test_drain_progress_partial():
    """Shows percentage and ETA."""
    result = build_drain_progress(5, 5, 3600.0)
    text = result.plain
    assert "50%" in text
    assert "1.0h" in text


# ── count_pending_by_provider (mocked) ──────────────────────────────


def test_count_pending_by_provider(tmp_path):
    """Count pending checkboxes by provider."""
    queue = tmp_path / "golem-queue.md"
    queue.write_text(
        "- [ ] task1 --provider infini\n"
        "- [ ] task2 --provider zhipu\n"
        "- [x] task3 --provider infini\n"
        "- [ ] task4 --provider infini\n"
    )
    # Patch the module-level constant via the exec'd namespace
    _mod["QUEUE_PATH"] = queue
    counts = count_pending_by_provider()
    assert counts["infini"] == 2
    assert counts["zhipu"] == 1


def test_count_total_pending(tmp_path):
    """Count total pending tasks."""
    queue = tmp_path / "golem-queue.md"
    queue.write_text(
        "- [ ] task1\n"
        "- [x] task2\n"
        "- [ ] task3\n"
    )
    _mod["QUEUE_PATH"] = queue
    assert count_total_pending() == 2


def test_count_total_completed(tmp_path):
    """Count total completed tasks."""
    queue = tmp_path / "golem-queue.md"
    queue.write_text(
        "- [ ] task1\n"
        "- [x] task2\n"
        "- [x] task3\n"
    )
    _mod["QUEUE_PATH"] = queue
    assert count_total_completed() == 2


# ── build_running_tasks_table includes progress ─────────────────────


def test_running_tasks_table_has_progress_column():
    """Running tasks table should include a progress column."""
    running = [
        {"task_id": "abc123", "provider": "infini", "cmd": '"do stuff"', "dispatch_provider": "infini"},
    ]
    # Set avg durations for the provider
    _mod["compute_avg_duration_by_provider"] = lambda recs: {"infini": 120.0}
    table = build_running_tasks_table(running)
    col_names = [c.header for c in table.columns]
    assert "Progress" in col_names


# ── Verify ast.parse on effector ────────────────────────────────────

def test_golem_dash_syntax_valid():
    """Verify the effector parses without syntax errors."""
    import ast
    source = Path.home().joinpath("germline/effectors/golem-dash").read_text()
    ast.parse(source)


# ── New: throughput_per_hour ─────────────────────────────────────────


def test_throughput_per_hour_basic():
    """Compute tasks/hr from recent completions."""
    now = datetime.now(timezone.utc)
    records = []
    for i in range(4):
        ts = (now - timedelta(minutes=i * 15)).isoformat()
        records.append({"exit": 0, "ts": ts, "provider": "zhipu", "duration": 100})
    rate = _mod["compute_throughput_per_hour"](records, provider="zhipu")
    assert rate == pytest.approx(4.0)


def test_throughput_per_hour_no_completions():
    """No completions = 0 rate."""
    rate = _mod["compute_throughput_per_hour"]([], provider="infini")
    assert rate == 0.0


def test_throughput_per_hour_mixed_providers():
    """Only counts the specified provider."""
    now = datetime.now(timezone.utc)
    records = [
        {"exit": 0, "ts": now.isoformat(), "provider": "infini", "duration": 100},
        {"exit": 0, "ts": now.isoformat(), "provider": "zhipu", "duration": 100},
    ]
    rate = _mod["compute_throughput_per_hour"](records, provider="infini")
    assert rate == pytest.approx(1.0)


# ── New: detect_stale_tasks ─────────────────────────────────────────


def test_detect_stale_tasks_none_running():
    """No running tasks = no stale tasks."""
    stale = _mod["detect_stale_tasks"]([], {"infini": 120.0})
    assert stale == []


def test_detect_stale_tasks_fresh():
    """Running task within normal range is not stale."""
    # Manually inject first-seen timestamp
    tid = "t-fresh"
    _mod["_task_first_seen"][tid] = time.time() - 60  # 60s ago
    running = [{"task_id": tid, "provider": "infini"}]
    stale = _mod["detect_stale_tasks"](running, {"infini": 120.0})
    assert stale == []
    del _mod["_task_first_seen"][tid]


def test_detect_stale_tasks_over_2x():
    """Running task >2× avg duration is stale."""
    tid = "t-stale"
    _mod["_task_first_seen"][tid] = time.time() - 300  # 300s ago
    running = [{"task_id": tid, "provider": "infini"}]
    stale = _mod["detect_stale_tasks"](running, {"infini": 100.0})
    assert len(stale) == 1
    assert stale[0]["task_id"] == tid
    assert stale[0]["elapsed"] > 200
    del _mod["_task_first_seen"][tid]


def test_detect_stale_tasks_no_avg():
    """No avg duration = not stale (can't judge)."""
    tid = "t-noavg"
    _mod["_task_first_seen"][tid] = time.time() - 500
    running = [{"task_id": tid, "provider": "gemini"}]
    stale = _mod["detect_stale_tasks"](running, {})
    assert stale == []
    del _mod["_task_first_seen"][tid]


# ── New: fmt_wallclock_eta ──────────────────────────────────────────


def test_wallclock_eta_positive():
    """Returns HH:MM formatted wall-clock time."""
    result = _mod["fmt_wallclock_eta"](3600)
    # Should be a time string like "HH:MM" ~1hr from now
    assert ":" in result
    assert len(result) == 5  # "HH:MM"


def test_wallclock_eta_zero():
    """Zero ETA = dash."""
    result = _mod["fmt_wallclock_eta"](0)
    assert result == "—"


def test_wallclock_eta_negative():
    """Negative ETA = dash."""
    result = _mod["fmt_wallclock_eta"](-10)
    assert result == "—"


def test_wallclock_eta_inf():
    """Infinity ETA = special marker."""
    result = _mod["fmt_wallclock_eta"](float("inf"))
    assert result == "∞"


# ── New: compute_eta_confidence ─────────────────────────────────────


def test_eta_confidence_high():
    """Many recent completions = high confidence."""
    now = datetime.now(timezone.utc)
    records = []
    for i in range(20):
        ts = (now - timedelta(minutes=i * 3)).isoformat()
        records.append({"exit": 0, "ts": ts, "provider": "infini", "duration": 100})
    conf = _mod["compute_eta_confidence"](records)
    assert conf == "high"


def test_eta_confidence_medium():
    """Few completions = medium confidence."""
    now = datetime.now(timezone.utc)
    records = [
        {"exit": 0, "ts": (now - timedelta(minutes=30)).isoformat(), "provider": "infini", "duration": 100},
        {"exit": 0, "ts": (now - timedelta(minutes=45)).isoformat(), "provider": "infini", "duration": 100},
    ]
    conf = _mod["compute_eta_confidence"](records)
    assert conf == "medium"


def test_eta_confidence_low():
    """No recent completions = low confidence."""
    conf = _mod["compute_eta_confidence"]([])
    assert conf == "low"


def test_eta_confidence_with_rate_limits():
    """Rate-limited entries reduce confidence."""
    now = datetime.now(timezone.utc)
    records = []
    for i in range(10):
        ts = (now - timedelta(minutes=i * 5)).isoformat()
        records.append({"exit": 0, "ts": ts, "provider": "infini", "duration": 100})
    for i in range(8):
        ts = (now - timedelta(minutes=i * 5)).isoformat()
        records.append({"exit": 1, "ts": ts, "provider": "infini", "duration": 3,
                         "tail": "429 too many requests"})
    conf = _mod["compute_eta_confidence"](records)
    # Many RL entries should drop confidence from "high" to "medium"
    assert conf in ("medium", "low")
