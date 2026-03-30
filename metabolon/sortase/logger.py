from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DEFAULT_LOG_PATH = Path.home() / ".local" / "share" / "sortase" / "log.jsonl"
DEFAULT_COACHING_PATH = Path.home() / "epigenome" / "marks" / "feedback_glm_coaching.md"


def resolve_log_path(path: str | os.PathLike[str] | None = None) -> Path:
    if path:
        return Path(path)
    override = os.environ.get("OPIFEX_LOG_PATH")
    return Path(override) if override else DEFAULT_LOG_PATH


def append_log(entry: dict[str, Any], path: str | os.PathLike[str] | None = None) -> Path:
    log_path = resolve_log_path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return log_path


def read_logs(path: str | os.PathLike[str] | None = None) -> list[dict[str, Any]]:
    log_path = resolve_log_path(path)
    if not log_path.exists():
        return []
    entries: list[dict[str, Any]] = []
    with log_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def aggregate_stats(entries: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now()
    cutoff_24h = (now - timedelta(hours=24)).isoformat()

    tool_totals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"runs": 0, "successes": 0, "durations": [], "last_24h": 0, "coaching_triggers": 0}
    )
    failure_reasons: Counter[str] = Counter()
    fallback_frequency: Counter[str] = Counter()

    for entry in entries:
        tool = entry.get("tool", "unknown")
        bucket = tool_totals[tool]
        bucket["runs"] += 1
        bucket["successes"] += 1 if entry.get("success") else 0
        d = entry.get("duration_s", 0)
        if d:
            bucket["durations"].append(float(d))

        if entry.get("timestamp", "") >= cutoff_24h:
            bucket["last_24h"] += 1
        if entry.get("failure_reason"):
            bucket["coaching_triggers"] += 1

        for fallback in entry.get("fallbacks", []) or []:
            fallback_frequency[fallback] += 1

        if not entry.get("success"):
            failure_reasons[entry.get("failure_reason", "unknown")] += 1

    per_tool = {}
    for tool, details in tool_totals.items():
        durations = sorted(details["durations"])
        n = len(durations)
        runs = details["runs"]
        per_tool[tool] = {
            "runs": runs,
            "success_rate": round(details["successes"] / runs, 3) if runs else 0.0,
            "avg_duration_s": round(sum(durations) / n, 1) if n else 0.0,
            "p50_duration_s": round(durations[n // 2], 1) if n else 0.0,
            "p90_duration_s": round(durations[int(n * 0.9)], 1) if n else 0.0,
            "last_24h": details["last_24h"],
            "coaching_triggers": details["coaching_triggers"],
        }

    return {
        "per_tool": per_tool,
        "failure_reasons": dict(failure_reasons.most_common()),
        "fallback_frequency": dict(fallback_frequency.most_common()),
        "total_runs": len(entries),
    }


def analyze_logs(
    log_path: str | os.PathLike[str] | None = None,
    coaching_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    """Analyze log.jsonl for patterns: success rates, durations, failures, coaching coverage.

    Returns a dict with keys:
      - success_rate_by_backend: {tool: float}
      - success_rate_by_hour: {HH: float}
      - avg_duration_by_task_count: {task_count: float}
      - failure_reasons: {reason: count}
      - coaching_coverage: float | None (None when no failures exist)
      - total_entries: int
    """
    entries = read_logs(log_path)
    if not entries:
        return {
            "success_rate_by_backend": {},
            "success_rate_by_hour": {},
            "avg_duration_by_task_count": {},
            "failure_reasons": {},
            "coaching_coverage": None,
            "total_entries": 0,
        }

    # Success rate by backend
    backend_runs: dict[str, dict[str, int]] = defaultdict(lambda: {"runs": 0, "successes": 0})
    # Success rate by hour
    hour_runs: dict[str, dict[str, int]] = defaultdict(lambda: {"runs": 0, "successes": 0})
    # Duration by task count (complexity)
    task_durations: dict[int, list[float]] = defaultdict(list)
    # Failure reasons
    failure_reasons: Counter[str] = Counter()
    # Coaching coverage tracking
    failure_timestamps: list[str] = []

    for entry in entries:
        tool = entry.get("tool", "unknown")
        backend_runs[tool]["runs"] += 1
        if entry.get("success"):
            backend_runs[tool]["successes"] += 1

        ts = entry.get("timestamp", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                hour_key = dt.strftime("%H")
                hour_runs[hour_key]["runs"] += 1
                if entry.get("success"):
                    hour_runs[hour_key]["successes"] += 1
            except (ValueError, TypeError):
                pass

        task_count = entry.get("tasks", 1)
        duration = entry.get("duration_s", 0)
        if duration:
            task_durations[int(task_count)].append(float(duration))

        if not entry.get("success"):
            reason = entry.get("failure_reason") or "unknown"
            failure_reasons[reason] += 1
            failure_timestamps.append(ts)

    success_rate_by_backend: dict[str, float] = {}
    for tool, counts in backend_runs.items():
        runs = counts["runs"]
        success_rate_by_backend[tool] = round(counts["successes"] / runs, 3) if runs else 0.0

    success_rate_by_hour: dict[str, float] = {}
    for hour, counts in sorted(hour_runs.items()):
        runs = counts["runs"]
        success_rate_by_hour[hour] = round(counts["successes"] / runs, 3) if runs else 0.0

    avg_duration_by_task_count: dict[int, float] = {}
    for task_count, durations in sorted(task_durations.items()):
        n = len(durations)
        avg_duration_by_task_count[task_count] = round(sum(durations) / n, 1) if n else 0.0

    # Coaching coverage: fraction of failures that occurred after coaching file existed
    coaching_coverage: float | None = None
    if failure_timestamps:
        resolved_coaching = Path(coaching_path) if coaching_path else DEFAULT_COACHING_PATH
        if resolved_coaching.exists():
            coaching_epoch = resolved_coaching.stat().st_mtime
            covered = 0
            for ts in failure_timestamps:
                try:
                    failure_dt = datetime.fromisoformat(ts)
                    if failure_dt.timestamp() >= coaching_epoch:
                        covered += 1
                except (ValueError, TypeError):
                    pass
            coaching_coverage = round(covered / len(failure_timestamps), 3)
        else:
            coaching_coverage = 0.0

    return {
        "success_rate_by_backend": success_rate_by_backend,
        "success_rate_by_hour": success_rate_by_hour,
        "avg_duration_by_task_count": avg_duration_by_task_count,
        "failure_reasons": dict(failure_reasons.most_common()),
        "coaching_coverage": coaching_coverage,
        "total_entries": len(entries),
    }
