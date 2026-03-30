from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DEFAULT_LOG_PATH = Path.home() / ".local" / "share" / "sortase" / "log.jsonl"


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
