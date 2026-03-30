"""translocon_metrics — per-dispatch metrics collection and reporting.

Records prompt length, output length, duration, model, backend, and
success for each translocon dispatch. Provides percentile statistics
grouped by backend.

Storage: ~/.local/share/translocon/metrics.jsonl
"""

from __future__ import annotations

import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

METRICS_PATH = Path.home() / ".local/share/translocon/metrics.jsonl"


def record(
    *,
    backend: str,
    model: str,
    prompt_length: int,
    output_length: int,
    duration_s: float,
    success: bool,
    mode: str = "",
) -> None:
    """Append a single dispatch metric entry to the JSONL file."""
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "backend": backend,
        "model": model,
        "prompt_length": prompt_length,
        "output_length": output_length,
        "duration_s": round(duration_s, 3),
        "success": success,
        "mode": mode,
    }
    with open(METRICS_PATH, "a") as fh:
        fh.write(json.dumps(entry) + "\n")


def _load_entries(days: int | None = None) -> list[dict[str, Any]]:
    """Read all metric entries, optionally filtered to the last N days."""
    if not METRICS_PATH.exists():
        return []
    cutoff: datetime | None = None
    if days is not None:
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)

    entries: list[dict[str, Any]] = []
    with open(METRICS_PATH) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if cutoff is not None:
                ts = entry.get("timestamp", "")
                try:
                    entry_dt = datetime.fromisoformat(ts)
                    if entry_dt < cutoff:
                        continue
                except (ValueError, TypeError):
                    pass  # include unparseable entries
            entries.append(entry)
    return entries


def _percentile(sorted_vals: list[float], pct: float) -> float:
    """Compute a percentile from a pre-sorted list of floats."""
    if not sorted_vals:
        return 0.0
    idx = (pct / 100) * (len(sorted_vals) - 1)
    lower = int(idx)
    upper = lower + 1
    if upper >= len(sorted_vals):
        return sorted_vals[-1]
    frac = idx - lower
    return round(sorted_vals[lower] + frac * (sorted_vals[upper] - sorted_vals[lower]), 2)


def stats_by_backend(days: int | None = None) -> dict[str, dict[str, Any]]:
    """Compute avg/p50/p95 duration and counts grouped by backend.

    Returns dict mapping backend name to stats dict with keys:
    count, success_count, avg_duration, p50_duration, p95_duration.
    """
    entries = _load_entries(days)
    if not entries:
        return {}

    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        backend = entry.get("backend", "unknown")
        grouped.setdefault(backend, []).append(entry)

    result: dict[str, dict[str, Any]] = {}
    for backend, group in sorted(grouped.items()):
        durations = sorted(
            float(e.get("duration_s", 0)) for e in group if e.get("duration_s") is not None
        )
        successes = sum(1 for e in group if e.get("success"))
        result[backend] = {
            "count": len(group),
            "success_count": successes,
            "avg_duration": round(statistics.mean(durations), 2) if durations else 0.0,
            "p50_duration": _percentile(durations, 50),
            "p95_duration": _percentile(durations, 95),
        }
    return result


def format_report(days: int | None = None) -> str:
    """Format a human-readable metrics report."""
    backend_stats = stats_by_backend(days)
    if not backend_stats:
        window = f"last {days} days" if days is not None else "all time"
        return f"No translocon metrics recorded ({window})."

    lines: list[str] = []
    window = f"last {days} days" if days is not None else "all time"
    lines.append(f"Translocon Metrics ({window})")
    lines.append("")

    for backend, stats in backend_stats.items():
        success_pct = (stats["success_count"] / stats["count"] * 100) if stats["count"] else 0
        lines.append(f"  {backend}:")
        lines.append(f"    Dispatches: {stats['count']} ({stats['success_count']} ok, {success_pct:.0f}%)")
        lines.append(f"    Avg duration:  {stats['avg_duration']:.1f}s")
        lines.append(f"    P50 duration:  {stats['p50_duration']:.1f}s")
        lines.append(f"    P95 duration:  {stats['p95_duration']:.1f}s")

    return "\n".join(lines)
