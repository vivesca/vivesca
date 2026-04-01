"""Tests for metabolon.organelles.tachometer — organelle-level unit tests.

Mocks read_logs and _extract_coaching_notes so no filesystem I/O is needed.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _entry(
    ts: datetime | None = None,
    success: bool = True,
    duration_s: float = 10.0,
    plan: str = "plan-a",
    tool: str = "glm",
) -> dict:
    """Build a fake log entry."""
    e: dict = {
        "success": success,
        "duration_s": duration_s,
        "plan": plan,
        "tool": tool,
    }
    if ts is not None:
        e["timestamp"] = ts.isoformat()
    return e


NOW = datetime(2026, 4, 1, 12, 0, 0)


def _entries_last_hour(n: int, success: bool = True) -> list[dict]:
    """n entries spread over the last 50 minutes."""
    return [
        _entry(ts=NOW - timedelta(minutes=50 - i * 50 // max(n, 1)), success=success)
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# _parse_ts
# ---------------------------------------------------------------------------

class TestParseTs:
    def test_valid_iso(self):
        from metabolon.organelles.tachometer import _parse_ts
        ts = _parse_ts({"timestamp": "2026-04-01T10:30:00"})
        assert ts == datetime(2026, 4, 1, 10, 30, 0)

    def test_missing_key(self):
        from metabolon.organelles.tachometer import _parse_ts
        assert _parse_ts({}) is None

    def test_empty_string(self):
        from metabolon.organelles.tachometer import _parse_ts
        assert _parse_ts({"timestamp": ""}) is None

    def test_non_string(self):
        from metabolon.organelles.tachometer import _parse_ts
        assert _parse_ts({"timestamp": 12345}) is None

    def test_invalid_format(self):
        from metabolon.organelles.tachometer import _parse_ts
        assert _parse_ts({"timestamp": "not-a-date"}) is None


# ---------------------------------------------------------------------------
# current_rate
# ---------------------------------------------------------------------------

class TestCurrentRate:
    @patch("metabolon.organelles.tachometer.read_logs")
    @patch("metabolon.organelles.tachometer.datetime")
    def test_empty_logs(self, mock_dt, mock_rl):
        from metabolon.organelles.tachometer import current_rate
        mock_rl.return_value = []
        assert current_rate() == 0.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_entries_within_last_hour(self, mock_rl):
        from metabolon.organelles.tachometer import current_rate
        mock_rl.return_value = _entries_last_hour(5)
        with patch("metabolon.organelles.tachometer.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            mock_dt.fromisoformat = datetime.fromisoformat
            rate = current_rate()
        assert rate == 5.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_entries_all_old(self, mock_rl):
        from metabolon.organelles.tachometer import current_rate
        old = [_entry(ts=NOW - timedelta(hours=2))]
        mock_rl.return_value = old
        with patch("metabolon.organelles.tachometer.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            mock_dt.fromisoformat = datetime.fromisoformat
            rate = current_rate()
        assert rate == 0.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_mixed_timestamps(self, mock_rl):
        from metabolon.organelles.tachometer import current_rate
        entries = _entries_last_hour(3) + [_entry(ts=NOW - timedelta(hours=5))]
        mock_rl.return_value = entries
        with patch("metabolon.organelles.tachometer.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            mock_dt.fromisoformat = datetime.fromisoformat
            rate = current_rate()
        assert rate == 3.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_entries_with_missing_ts(self, mock_rl):
        from metabolon.organelles.tachometer import current_rate
        entries = _entries_last_hour(2) + [{"success": True}]
        mock_rl.return_value = entries
        with patch("metabolon.organelles.tachometer.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            mock_dt.fromisoformat = datetime.fromisoformat
            rate = current_rate()
        assert rate == 2.0


# ---------------------------------------------------------------------------
# success_trend
# ---------------------------------------------------------------------------

class TestSuccessTrend:
    @patch("metabolon.organelles.tachometer.read_logs")
    def test_empty_logs(self, mock_rl):
        from metabolon.organelles.tachometer import success_trend
        mock_rl.return_value = []
        result = success_trend()
        assert result["direction"] == "no data"
        assert result["recent_rate"] == 0.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_improving(self, mock_rl):
        from metabolon.organelles.tachometer import success_trend
        # last 10 all succeed, earlier 90 at 50% → improving
        recent = [_entry(success=True) for _ in range(10)]
        older = [_entry(success=(i % 2 == 0)) for i in range(90)]
        mock_rl.return_value = older + recent
        result = success_trend()
        assert result["direction"] == "improving"
        assert result["recent_rate"] == 1.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_declining(self, mock_rl):
        from metabolon.organelles.tachometer import success_trend
        # last 10 all fail, earlier 90 at 100% → declining
        recent = [_entry(success=False) for _ in range(10)]
        older = [_entry(success=True) for _ in range(90)]
        mock_rl.return_value = older + recent
        result = success_trend()
        assert result["direction"] == "declining"
        assert result["recent_rate"] == 0.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_stable(self, mock_rl):
        from metabolon.organelles.tachometer import success_trend
        entries = [_entry(success=True) for _ in range(20)]
        mock_rl.return_value = entries
        result = success_trend()
        assert result["direction"] == "stable"
        assert result["delta"] == 0.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_small_dataset(self, mock_rl):
        from metabolon.organelles.tachometer import success_trend
        entries = [_entry(success=True), _entry(success=False)]
        mock_rl.return_value = entries
        result = success_trend()
        # recent = last 2 (both), historical = last 100 (both) → same → stable
        assert result["direction"] == "stable"
        assert result["recent_count"] == 2
        assert result["historical_count"] == 2

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_counts(self, mock_rl):
        from metabolon.organelles.tachometer import success_trend
        entries = [_entry(success=True) for _ in range(50)]
        mock_rl.return_value = entries
        result = success_trend()
        assert result["recent_count"] == 10
        assert result["historical_count"] == 50


# ---------------------------------------------------------------------------
# slowest_recent
# ---------------------------------------------------------------------------

class TestSlowestRecent:
    @patch("metabolon.organelles.tachometer.read_logs")
    def test_empty_logs(self, mock_rl):
        from metabolon.organelles.tachometer import slowest_recent
        mock_rl.return_value = []
        assert slowest_recent() is None

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_finds_slowest(self, mock_rl):
        from metabolon.organelles.tachometer import slowest_recent
        entries = [
            _entry(ts=NOW - timedelta(minutes=10), duration_s=5.0, plan="fast"),
            _entry(ts=NOW - timedelta(minutes=5), duration_s=120.0, plan="slow", tool="deepseek"),
            _entry(ts=NOW - timedelta(minutes=1), duration_s=30.0, plan="mid"),
        ]
        mock_rl.return_value = entries
        with patch("metabolon.organelles.tachometer.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            mock_dt.fromisoformat = datetime.fromisoformat
            result = slowest_recent()
        assert result is not None
        assert result["plan"] == "slow"
        assert result["duration_s"] == 120.0
        assert result["tool"] == "deepseek"

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_all_outside_window(self, mock_rl):
        from metabolon.organelles.tachometer import slowest_recent
        entries = [_entry(ts=NOW - timedelta(hours=3), duration_s=200.0)]
        mock_rl.return_value = entries
        with patch("metabolon.organelles.tachometer.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            mock_dt.fromisoformat = datetime.fromisoformat
            assert slowest_recent() is None

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_custom_hours(self, mock_rl):
        from metabolon.organelles.tachometer import slowest_recent
        entries = [_entry(ts=NOW - timedelta(hours=3), duration_s=99.0, plan="old-slow")]
        mock_rl.return_value = entries
        with patch("metabolon.organelles.tachometer.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            mock_dt.fromisoformat = datetime.fromisoformat
            result = slowest_recent(hours=5)
        assert result is not None
        assert result["plan"] == "old-slow"

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_missing_duration(self, mock_rl):
        from metabolon.organelles.tachometer import slowest_recent
        entries = [_entry(ts=NOW - timedelta(minutes=5))]
        del entries[0]["duration_s"]
        mock_rl.return_value = entries
        with patch("metabolon.organelles.tachometer.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            mock_dt.fromisoformat = datetime.fromisoformat
            result = slowest_recent()
        # duration_s defaults to 0, so still found but with 0 duration
        assert result is not None
        assert result["duration_s"] == 0.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_returns_all_fields(self, mock_rl):
        from metabolon.organelles.tachometer import slowest_recent
        entries = [
            _entry(ts=NOW - timedelta(minutes=5), duration_s=50.0, plan="p",
                   tool="glm", success=False)
        ]
        mock_rl.return_value = entries
        with patch("metabolon.organelles.tachometer.datetime") as mock_dt:
            mock_dt.now.return_value = NOW
            mock_dt.fromisoformat = datetime.fromisoformat
            result = slowest_recent()
        assert result is not None
        assert result["success"] is False
        assert "timestamp" in result


# ---------------------------------------------------------------------------
# coaching_effectiveness
# ---------------------------------------------------------------------------

class TestCoachingEffectiveness:
    @patch("metabolon.organelles.tachometer._extract_coaching_notes")
    @patch("metabolon.organelles.tachometer.read_logs")
    def test_empty_logs(self, mock_rl, mock_cn):
        from metabolon.organelles.tachometer import coaching_effectiveness
        mock_rl.return_value = []
        mock_cn.return_value = [{"text": "note", "added_at": NOW}]
        result = coaching_effectiveness()
        assert result["before_failure_rate"] == 0.0
        assert result["after_failure_rate"] == 0.0

    @patch("metabolon.organelles.tachometer._extract_coaching_notes")
    @patch("metabolon.organelles.tachometer.read_logs")
    def test_no_coaching_notes(self, mock_rl, mock_cn):
        from metabolon.organelles.tachometer import coaching_effectiveness
        mock_rl.return_value = [_entry(success=True)]
        mock_cn.return_value = []
        result = coaching_effectiveness()
        assert result["improvement_pct"] == 0.0
        assert result["notes_analyzed"] == 0

    @patch("metabolon.organelles.tachometer._extract_coaching_notes")
    @patch("metabolon.organelles.tachometer.read_logs")
    def test_improvement(self, mock_rl, mock_cn):
        from metabolon.organelles.tachometer import coaching_effectiveness
        coaching_ts = NOW - timedelta(hours=2)
        before = [_entry(ts=coaching_ts - timedelta(minutes=i), success=(i % 2 == 0))
                  for i in range(1, 11)]
        after = [_entry(ts=coaching_ts + timedelta(minutes=i), success=True)
                 for i in range(10)]
        mock_rl.return_value = before + after
        mock_cn.return_value = [{"text": "fix x", "added_at": coaching_ts}]
        with patch("metabolon.organelles.tachometer.datetime") as mock_dt:
            mock_dt.fromisoformat = datetime.fromisoformat
            result = coaching_effectiveness()
        assert result["improvement_pct"] > 0
        assert result["notes_analyzed"] == 1

    @patch("metabolon.organelles.tachometer._extract_coaching_notes")
    @patch("metabolon.organelles.tachometer.read_logs")
    def test_regression(self, mock_rl, mock_cn):
        from metabolon.organelles.tachometer import coaching_effectiveness
        coaching_ts = NOW - timedelta(hours=2)
        before = [_entry(ts=coaching_ts - timedelta(minutes=i), success=True)
                  for i in range(1, 11)]
        after = [_entry(ts=coaching_ts + timedelta(minutes=i), success=False)
                 for i in range(10)]
        mock_rl.return_value = before + after
        mock_cn.return_value = [{"text": "broke x", "added_at": coaching_ts}]
        with patch("metabolon.organelles.tachometer.datetime") as mock_dt:
            mock_dt.fromisoformat = datetime.fromisoformat
            result = coaching_effectiveness()
        assert result["improvement_pct"] < 0

    @patch("metabolon.organelles.tachometer._extract_coaching_notes")
    @patch("metabolon.organelles.tachometer.read_logs")
    def test_total_entries_count(self, mock_rl, mock_cn):
        from metabolon.organelles.tachometer import coaching_effectiveness
        entries = [_entry(ts=NOW - timedelta(minutes=i)) for i in range(25)]
        mock_rl.return_value = entries
        mock_cn.return_value = [{"text": "n", "added_at": NOW - timedelta(hours=1)}]
        with patch("metabolon.organelles.tachometer.datetime") as mock_dt:
            mock_dt.fromisoformat = datetime.fromisoformat
            result = coaching_effectiveness()
        assert result["total_entries"] == 25

    @patch("metabolon.organelles.tachometer._extract_coaching_notes")
    @patch("metabolon.organelles.tachometer.read_logs")
    def test_custom_coaching_path(self, mock_rl, mock_cn):
        from metabolon.organelles.tachometer import coaching_effectiveness
        mock_rl.return_value = [_entry(ts=NOW)]
        mock_cn.return_value = [{"text": "n", "added_at": NOW}]
        with patch("metabolon.organelles.tachometer.datetime") as mock_dt:
            mock_dt.fromisoformat = datetime.fromisoformat
            coaching_effectiveness(coaching_path="/custom/path.md")
        mock_cn.assert_called_once()
        # The path argument should have been converted to Path
        import pathlib
        assert mock_cn.call_args[0][0] == pathlib.Path("/custom/path.md")


# ---------------------------------------------------------------------------
# estimate_completion
# ---------------------------------------------------------------------------

class TestEstimateCompletion:
    @patch("metabolon.organelles.tachometer.read_logs")
    def test_zero_remaining(self, mock_rl):
        from metabolon.organelles.tachometer import estimate_completion
        assert estimate_completion(remaining_tasks=0) == 0.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_negative_remaining(self, mock_rl):
        from metabolon.organelles.tachometer import estimate_completion
        assert estimate_completion(remaining_tasks=-5) == 0.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_empty_logs(self, mock_rl):
        from metabolon.organelles.tachometer import estimate_completion
        mock_rl.return_value = []
        assert estimate_completion(remaining_tasks=10) == 0.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_basic_estimate(self, mock_rl):
        from metabolon.organelles.tachometer import estimate_completion
        # 20 entries each with 360s duration → avg 360s → 10 tasks = 1.0 hour
        entries = [_entry(duration_s=360.0) for _ in range(20)]
        mock_rl.return_value = entries
        result = estimate_completion(remaining_tasks=10)
        assert result == 1.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_uses_last_20(self, mock_rl):
        from metabolon.organelles.tachometer import estimate_completion
        # 30 entries: first 10 with 10s, last 20 with 60s
        fast = [_entry(duration_s=10.0) for _ in range(10)]
        slow = [_entry(duration_s=60.0) for _ in range(20)]
        mock_rl.return_value = fast + slow
        # avg of last 20 = 60s → 6 tasks = 360s / 3600 = 0.1
        result = estimate_completion(remaining_tasks=6)
        assert result == 0.1

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_no_duration_entries(self, mock_rl):
        from metabolon.organelles.tachometer import estimate_completion
        entries = [{"success": True, "plan": "x"} for _ in range(5)]
        mock_rl.return_value = entries
        assert estimate_completion(remaining_tasks=10) == 0.0

    @patch("metabolon.organelles.tachometer.read_logs")
    def test_mixed_durations(self, mock_rl):
        from metabolon.organelles.tachometer import estimate_completion
        entries = [_entry(duration_s=60.0), _entry(duration_s=180.0)]
        mock_rl.return_value = entries
        # avg = 120s, 30 tasks → 3600s / 3600 = 1.0
        result = estimate_completion(remaining_tasks=30)
        assert result == 1.0
