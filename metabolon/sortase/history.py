from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table

from metabolon.sortase.logger import _parse_iso_timestamp, read_logs

DEFAULT_LIMIT = 20


def _format_timestamp(raw: str) -> str:
    parsed = _parse_iso_timestamp(raw)
    if parsed is None:
        return raw
    return parsed.strftime("%Y-%m-%d %H:%M")


def _format_duration(seconds: float | int | None) -> str:
    if seconds is None:
        return "-"
    value = float(seconds)
    if value < 60:
        return f"{value:.1f}s"
    minutes = int(value // 60)
    secs = value % 60
    return f"{minutes}m {secs:.0f}s"


def _format_files_changed(files_changed: Any) -> str:
    if isinstance(files_changed, list):
        count = len([v for v in files_changed if str(v).strip()])
    elif isinstance(files_changed, (int, float)):
        count = int(files_changed)
    else:
        return "-"
    return str(count)


def build_history_entries(entries: list[dict[str, Any]], limit: int = DEFAULT_LIMIT) -> list[dict[str, Any]]:
    """Return history entries as a list of dicts for machine-readable output."""
    recent = entries[-limit:] if len(entries) > limit else list(entries)
    recent.reverse()

    result: list[dict[str, Any]] = []
    for entry in recent:
        success = entry.get("success")
        if success is True:
            status_str = "ok"
        elif success is False:
            status_str = "fail"
        else:
            status_str = "unknown"

        result.append({
            "timestamp": _format_timestamp(entry.get("timestamp", "")),
            "plan": entry.get("plan", "-"),
            "backend": entry.get("tool", "-"),
            "duration": _format_duration(entry.get("duration_s")),
            "status": status_str,
            "files": _format_files_changed(entry.get("files_changed")),
        })
    return result


def build_history_table(entries: list[dict[str, Any]], limit: int = DEFAULT_LIMIT) -> Table:
    recent = entries[-limit:] if len(entries) > limit else list(entries)
    recent.reverse()

    table = Table(title="sortase history")
    table.add_column("#", style="dim", justify="right")
    table.add_column("Timestamp")
    table.add_column("Plan")
    table.add_column("Backend")
    table.add_column("Duration", justify="right")
    table.add_column("Status")
    table.add_column("Files", justify="right")

    for idx, entry in enumerate(recent, 1):
        success = entry.get("success")
        if success is True:
            status_str = "[green]ok[/green]"
        elif success is False:
            status_str = "[red]fail[/red]"
        else:
            status_str = "[yellow]?[/yellow]"

        table.add_row(
            str(idx),
            _format_timestamp(entry.get("timestamp", "")),
            entry.get("plan", "-"),
            entry.get("tool", "-"),
            _format_duration(entry.get("duration_s")),
            status_str,
            _format_files_changed(entry.get("files_changed")),
        )

    return table


def display_history(limit: int = DEFAULT_LIMIT) -> None:
    entries = read_logs()
    if not entries:
        Console().print("[dim]No dispatch history found.[/dim]")
        return
    Console().print(build_history_table(entries, limit))
