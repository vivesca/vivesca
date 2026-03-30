"""tachometer — sortase dispatch throughput monitor.

Reads log.jsonl and computes real-time dispatch metrics:
rate, success trends, slowest tasks, coaching effectiveness,
and estimated completion times.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from metabolon.sortase.logger import (
    DEFAULT_COACHING_PATH,
    DEFAULT_LOG_PATH,
    _extract_coaching_notes,
    read_logs,
    resolve_log_path,
)


def _parse_ts(entry: dict[str, Any]) -> datetime | None:
    ts = entry.get("timestamp")
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def current_rate(log_path: str | Path | None = None) -> float:
    """Dispatch rate in tasks per hour over the last hour."""
    entries = read_logs(log_path)
    if not entries:
        return 0.0
    cutoff = datetime.now() - timedelta(hours=1)
    count = 0
    for entry in entries:
        ts = _parse_ts(entry)
        if ts is not None and ts >= cutoff:
            count += 1
    return float(count)


def success_trend(log_path: str | Path | None = None) -> dict[str, Any]:
    """Compare recent success rate (last 10) vs historical (last 100).

    Returns dict with keys: recent_rate, recent_count, historical_rate,
    historical_count, delta (recent - historical), direction.
    """
    entries = read_logs(log_path)
    if not entries:
        return {
            "recent_rate": 0.0,
            "recent_count": 0,
            "historical_rate": 0.0,
            "historical_count": 0,
            "delta": 0.0,
            "direction": "no data",
        }

    recent = entries[-10:]
    historical = entries[-100:]

    def _rate(batch: list[dict[str, Any]]) -> float:
        if not batch:
            return 0.0
        successes = sum(1 for e in batch if e.get("success"))
        return round(successes / len(batch), 3)

    recent_rate = _rate(recent)
    historical_rate = _rate(historical)
    delta = round(recent_rate - historical_rate, 3)
    if delta > 0.01:
        direction = "improving"
    elif delta < -0.01:
        direction = "declining"
    else:
        direction = "stable"

    return {
        "recent_rate": recent_rate,
        "recent_count": len(recent),
        "historical_rate": historical_rate,
        "historical_count": len(historical),
        "delta": delta,
        "direction": direction,
    }


def slowest_recent(
    log_path: str | Path | None = None,
    hours: int = 1,
) -> dict[str, Any] | None:
    """Find the slowest task within the last N hours.

    Returns dict with plan, duration_s, tool, timestamp, success or None.
    """
    entries = read_logs(log_path)
    if not entries:
        return None
    cutoff = datetime.now() - timedelta(hours=hours)
    slowest: dict[str, Any] | None = None
    slowest_dur = 0.0
    for entry in entries:
        ts = _parse_ts(entry)
        if ts is None or ts < cutoff:
            continue
        dur = float(entry.get("duration_s", 0))
        if dur > slowest_dur:
            slowest_dur = dur
            slowest = {
                "plan": entry.get("plan", "unknown"),
                "duration_s": dur,
                "tool": entry.get("tool", "unknown"),
                "timestamp": entry.get("timestamp", ""),
                "success": entry.get("success", False),
            }
    return slowest


def coaching_effectiveness(
    log_path: str | Path | None = None,
    coaching_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compare failure rate before vs after each coaching note.

    Returns dict with before_failure_rate, after_failure_rate,
    improvement_pct, notes_analyzed, total_entries.
    """
    entries = read_logs(log_path)
    resolved_coaching = Path(coaching_path) if coaching_path else DEFAULT_COACHING_PATH
    notes = _extract_coaching_notes(resolved_coaching)

    if not entries or not notes:
        return {
            "before_failure_rate": 0.0,
            "after_failure_rate": 0.0,
            "improvement_pct": 0.0,
            "notes_analyzed": len(notes),
            "total_entries": len(entries),
        }

    # Use the earliest coaching note timestamp as the dividing line.
    earliest_note = min(n["added_at"] for n in notes)

    before_entries: list[dict[str, Any]] = []
    after_entries: list[dict[str, Any]] = []

    for entry in entries:
        ts = _parse_ts(entry)
        if ts is None:
            continue
        if ts < earliest_note:
            before_entries.append(entry)
        else:
            after_entries.append(entry)

    def _failure_rate(batch: list[dict[str, Any]]) -> float:
        if not batch:
            return 0.0
        failures = sum(1 for e in batch if not e.get("success"))
        return round(failures / len(batch), 3)

    before_rate = _failure_rate(before_entries)
    after_rate = _failure_rate(after_entries)
    improvement = round((before_rate - after_rate) * 100, 1)

    return {
        "before_failure_rate": before_rate,
        "after_failure_rate": after_rate,
        "improvement_pct": improvement,
        "notes_analyzed": len(notes),
        "total_entries": len(entries),
    }


def estimate_completion(
    log_path: str | Path | None = None,
    remaining_tasks: int = 0,
) -> float:
    """Estimated hours to complete N remaining tasks at current rate.

    Uses average duration of the last 20 entries. Returns 0.0 if
    insufficient data or no remaining tasks.
    """
    if remaining_tasks <= 0:
        return 0.0
    entries = read_logs(log_path)
    if not entries:
        return 0.0

    recent = entries[-20:]
    durations = [float(e.get("duration_s", 0)) for e in recent if e.get("duration_s")]
    if not durations:
        return 0.0

    avg_seconds = sum(durations) / len(durations)
    return round(avg_seconds * remaining_tasks / 3600, 1)
