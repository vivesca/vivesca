from __future__ import annotations

"""Overnight session report generator for sortase.

Analyzes sortase log entries from the last N hours to produce a summary
report covering success rates, backend distribution, and failure reasons.
"""


import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def load_overnight_entries(log_path: Path, since_hours: int = 8) -> list[dict[str, Any]]:
    """Filter log entries from the last N hours.

    Args:
        log_path: Path to log.jsonl file.
        since_hours: How many hours back to include.

    Returns:
        List of log entry dicts within the time window.
    """
    if not log_path.exists():
        return []

    cutoff = datetime.now() - timedelta(hours=since_hours)
    entries: list[dict[str, Any]] = []

    with log_path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            timestamp_str = entry.get("timestamp", "")
            if not timestamp_str:
                continue
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                continue

            if timestamp >= cutoff:
                entries.append(entry)

    return entries


def compute_overnight_stats(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute statistics from overnight log entries.

    Args:
        entries: List of log entry dicts.

    Returns:
        Dict with total, successes, failures, success_rate, avg_duration_s,
        backend_distribution, failure_reasons, plans, projects.
    """
    if not entries:
        return {
            "total": 0,
            "successes": 0,
            "failures": 0,
            "success_rate": 0.0,
            "avg_duration_s": 0.0,
            "backend_distribution": {},
            "failure_reasons": {},
            "plans": [],
            "projects": [],
        }

    total = len(entries)
    successes = sum(1 for entry in entries if entry.get("success"))
    failures = total - successes
    success_rate = successes / total if total else 0.0

    durations = [float(entry.get("duration_s", 0)) for entry in entries if entry.get("duration_s")]
    avg_duration_s = sum(durations) / len(durations) if durations else 0.0

    backend_distribution: dict[str, int] = dict(
        Counter(entry.get("tool", "unknown") for entry in entries)
    )

    failure_reasons: dict[str, int] = dict(
        Counter(
            entry.get("failure_reason", "unknown") for entry in entries if not entry.get("success")
        )
    )

    plans = sorted({entry.get("plan", "unknown") for entry in entries})
    projects = sorted({entry.get("project", "unknown") for entry in entries})

    return {
        "total": total,
        "successes": successes,
        "failures": failures,
        "success_rate": success_rate,
        "avg_duration_s": avg_duration_s,
        "backend_distribution": backend_distribution,
        "failure_reasons": failure_reasons,
        "plans": plans,
        "projects": projects,
    }


def format_overnight_report(stats: dict[str, Any], entries: list[dict[str, Any]]) -> str:
    """Format overnight statistics as a markdown report.

    Args:
        stats: Output of compute_overnight_stats.
        entries: The filtered entries (used for per-entry details).

    Returns:
        Markdown-formatted report string.
    """
    if stats["total"] == 0:
        return "# Overnight Report\n\nNo entries found in the specified time window.\n"

    lines: list[str] = [
        "# Overnight Report",
        "",
        "## Summary",
        "",
        f"- **Total executions:** {stats['total']}",
        f"- **Successes:** {stats['successes']}",
        f"- **Failures:** {stats['failures']}",
        f"- **Success rate:** {stats['success_rate']:.1%}",
        f"- **Avg duration:** {stats['avg_duration_s']:.1f}s",
        "",
    ]

    backend_dist = stats["backend_distribution"]
    if backend_dist:
        lines.append("## Backend Distribution")
        lines.append("")
        for backend, count in sorted(backend_dist.items(), key=lambda item: item[1], reverse=True):
            lines.append(f"- **{backend}:** {count} run(s)")
        lines.append("")

    failure_reasons = stats["failure_reasons"]
    if failure_reasons:
        lines.append("## Failure Reasons")
        lines.append("")
        for reason, count in sorted(
            failure_reasons.items(), key=lambda item: item[1], reverse=True
        ):
            lines.append(f"- **{reason}:** {count}")
        lines.append("")

    plans = stats["plans"]
    if plans:
        lines.append("## Plans Executed")
        lines.append("")
        for plan in plans:
            lines.append(f"- {plan}")
        lines.append("")

    projects = stats["projects"]
    if projects:
        lines.append("## Projects")
        lines.append("")
        for project in projects:
            lines.append(f"- {project}")
        lines.append("")

    if entries:
        lines.append("## Execution Log")
        lines.append("")
        for entry in entries:
            timestamp = entry.get("timestamp", "unknown")
            plan = entry.get("plan", "unknown")
            tool = entry.get("tool", "unknown")
            duration = entry.get("duration_s", 0)
            success = entry.get("success", False)
            status_label = "success" if success else "FAILED"
            reason = ""
            if not success and entry.get("failure_reason"):
                reason = f" ({entry['failure_reason']})"
            lines.append(
                f"- `{timestamp}` **{plan}** [{tool}] {duration:.1f}s — {status_label}{reason}"
            )
        lines.append("")

    return "\n".join(lines)
