"""Reflection capture — read worker self-reports after task completion."""

from __future__ import annotations

from pathlib import Path

REFLECTION_FILE = Path("/tmp/mtor-reflection.md")
STALL_FILE = Path("/tmp/mtor-stall.txt")


def capture_reflection(reflection_path: Path = REFLECTION_FILE) -> str | None:
    if not reflection_path.exists():
        return None
    content = reflection_path.read_text(encoding="utf-8").strip()
    reflection_path.unlink(missing_ok=True)
    return content or None


def capture_stall_report(stall_path: Path = STALL_FILE) -> str | None:
    if not stall_path.exists():
        return None
    content = stall_path.read_text(encoding="utf-8").strip()
    stall_path.unlink(missing_ok=True)
    return content or None
