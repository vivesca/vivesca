
"""Compare two overnight sessions for coaching effectiveness measurement.

Loads entries for two dates, computes deltas for task count, success rate,
duration, and identifies new/resolved failure reasons.
"""


import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CompareDelta:
    """Comparison result between two overnight sessions."""

    date_a: str
    date_b: str
    task_count_a: int
    task_count_b: int
    task_count_delta: int
    success_rate_a: float
    success_rate_b: float
    success_rate_delta: float
    avg_duration_a: float
    avg_duration_b: float
    avg_duration_delta: float
    new_failures: list[str] = field(default_factory=list)
    resolved_failures: list[str] = field(default_factory=list)


def load_session_entries(log_path: Path, date: str) -> list[dict[str, Any]]:
    """Load log entries whose timestamp starts with the given date.

    Args:
        log_path: Path to log.jsonl file.
        date: Date string in YYYY-MM-DD format.

    Returns:
        List of log entry dicts matching the date.
    """
    if not log_path.exists():
        return []

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
            timestamp = entry.get("timestamp", "")
            if timestamp.startswith(date):
                entries.append(entry)

    return entries


def _session_stats(entries: list[dict[str, Any]]) -> tuple[int, float, float]:
    """Compute task count, success rate, and avg duration from entries.

    Returns:
        (task_count, success_rate, avg_duration_s)
    """
    task_count = len(entries)
    if task_count == 0:
        return 0, 0.0, 0.0

    successes = sum(1 for entry in entries if entry.get("success"))
    success_rate = successes / task_count

    durations = [float(entry.get("duration_s", 0)) for entry in entries if entry.get("duration_s")]
    avg_duration = sum(durations) / len(durations) if durations else 0.0

    return task_count, success_rate, avg_duration


def _failure_reasons(entries: list[dict[str, Any]]) -> set[str]:
    """Extract unique failure reasons from entries."""
    reasons: set[str] = set()
    for entry in entries:
        if not entry.get("success"):
            reason = entry.get("failure_reason", "unknown")
            if reason:
                reasons.add(reason)
    return reasons


def compare_sessions(log_path: Path, date_a: str, date_b: str) -> CompareDelta:
    """Compare two overnight sessions and compute deltas.

    Args:
        log_path: Path to log.jsonl file.
        date_a: First session date (YYYY-MM-DD).
        date_b: Second session date (YYYY-MM-DD).

    Returns:
        CompareDelta with all comparison metrics.
    """
    entries_a = load_session_entries(log_path, date_a)
    entries_b = load_session_entries(log_path, date_b)

    count_a, rate_a, dur_a = _session_stats(entries_a)
    count_b, rate_b, dur_b = _session_stats(entries_b)

    failures_a = _failure_reasons(entries_a)
    failures_b = _failure_reasons(entries_b)

    return CompareDelta(
        date_a=date_a,
        date_b=date_b,
        task_count_a=count_a,
        task_count_b=count_b,
        task_count_delta=count_b - count_a,
        success_rate_a=rate_a,
        success_rate_b=rate_b,
        success_rate_delta=rate_b - rate_a,
        avg_duration_a=dur_a,
        avg_duration_b=dur_b,
        avg_duration_delta=dur_b - dur_a,
        new_failures=sorted(failures_b - failures_a),
        resolved_failures=sorted(failures_a - failures_b),
    )


def _delta_str(old: float, new: float) -> str:
    """Return a percentage-change indicator like ' (↑50%)'.

    Returns empty string if *old* is zero (division undefined).
    """
    if old == 0:
        return ""
    pct = (new - old) / old * 100
    arrow = "↑" if pct > 0 else "↓" if pct < 0 else "→"
    return f" ({arrow}{abs(pct):.0f}%)"


def format_compare_report(delta: CompareDelta) -> str:
    """Format a CompareDelta as a human-readable markdown report.

    Args:
        delta: The comparison result to format.

    Returns:
        Markdown-formatted report string.
    """
    rate_a_str = f"{delta.success_rate_a:.1%}"
    rate_b_str = f"{delta.success_rate_b:.1%}"
    rate_delta_sign = "+" if delta.success_rate_delta >= 0 else ""
    rate_delta_str = f"{rate_delta_sign}{delta.success_rate_delta:.1%}"

    dur_delta_sign = "+" if delta.avg_duration_delta >= 0 else ""
    dur_delta_str = f"{dur_delta_sign}{delta.avg_duration_delta:.1f}s"

    count_delta_sign = "+" if delta.task_count_delta >= 0 else ""
    count_delta_str = f"{count_delta_sign}{delta.task_count_delta}"

    count_pct = _delta_str(float(delta.task_count_a), float(delta.task_count_b))
    rate_pct = _delta_str(delta.success_rate_a, delta.success_rate_b)
    dur_pct = _delta_str(delta.avg_duration_a, delta.avg_duration_b)

    lines: list[str] = [
        "# Session Comparison",
        "",
        f"**{delta.date_a}** → **{delta.date_b}**",
        "",
        f"| Metric | {delta.date_a} | {delta.date_b} | Delta |",
        "|--------|------|------|-------|",
        f"| Tasks | {delta.task_count_a} | {delta.task_count_b} | {count_delta_str}{count_pct} |",
        f"| Success rate | {rate_a_str} | {rate_b_str} | {rate_delta_str}{rate_pct} |",
        f"| Avg duration | {delta.avg_duration_a:.1f}s | {delta.avg_duration_b:.1f}s | {dur_delta_str}{dur_pct} |",
        "",
    ]

    if delta.new_failures:
        lines.append("**New failures introduced:**")
        for reason in delta.new_failures:
            lines.append(f"- {reason}")
        lines.append("")

    if delta.resolved_failures:
        lines.append("**Resolved failures:**")
        for reason in delta.resolved_failures:
            lines.append(f"- {reason}")
        lines.append("")

    if not delta.new_failures and not delta.resolved_failures:
        lines.append("No change in failure reasons.")
        lines.append("")

    return "\n".join(lines)
