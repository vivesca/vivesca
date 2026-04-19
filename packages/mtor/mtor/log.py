"""Structured JSON log — append, query, and filter task results."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class LogEntry:
    timestamp: str
    provider: str
    duration: int
    exit_code: int
    files_created: int
    reflection: str
    stall: str
    tail: str

    @classmethod
    def from_dict(cls, data: dict) -> LogEntry:
        return cls(
            timestamp=data.get("ts", ""),
            provider=data.get("provider", ""),
            duration=data.get("duration", 0),
            exit_code=data.get("exit", 0),
            files_created=data.get("files_created", 0),
            reflection=data.get("reflection", ""),
            stall=data.get("stall", ""),
            tail=data.get("tail", ""),
        )

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0

    @property
    def is_stalled(self) -> bool:
        return self.stall not in ("", "none")


def read_log(log_file: Path, limit: int = 50) -> list[LogEntry]:
    if not log_file.exists():
        return []
    lines = log_file.read_text().strip().split("\n")
    entries = []
    for line in lines[-limit:]:
        if not line.strip():
            continue
        try:
            entries.append(LogEntry.from_dict(json.loads(line)))
        except (json.JSONDecodeError, KeyError):
            continue
    return entries


def filter_stalls(entries: list[LogEntry]) -> list[LogEntry]:
    return [e for e in entries if e.is_stalled]


def filter_reflections(entries: list[LogEntry]) -> list[LogEntry]:
    return [e for e in entries if e.reflection]


def summary_stats(entries: list[LogEntry]) -> dict:
    if not entries:
        return {"total": 0, "success": 0, "failed": 0, "stalled": 0, "avg_duration": 0}
    succeeded = sum(1 for e in entries if e.succeeded)
    stalled = sum(1 for e in entries if e.is_stalled)
    avg_duration = sum(e.duration for e in entries) // len(entries)
    return {
        "total": len(entries),
        "success": succeeded,
        "failed": len(entries) - succeeded,
        "stalled": stalled,
        "avg_duration": avg_duration,
        "success_rate": f"{succeeded / len(entries) * 100:.0f}%",
    }
