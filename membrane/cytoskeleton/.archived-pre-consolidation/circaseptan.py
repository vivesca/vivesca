#!/usr/bin/env python3
from __future__ import annotations

"""
UserPromptSubmit hook — circaseptan rhythm (7-day cycle).
Nudges if it's Saturday+ and no weekly note exists for this week.
"""

from datetime import datetime
from pathlib import Path

WEEKLY_DIR = Path.home() / "notes" / "Weekly"
MARKER = Path.home() / ".claude" / ".weekly-reminded"


def current_iso_week() -> str:
    """Return e.g. '2026-W11'."""
    now = datetime.now()
    return now.strftime("%G-W%V")


def weekly_note_exists(week: str) -> bool:
    if not WEEKLY_DIR.exists():
        return False
    return any(week in f.name for f in WEEKLY_DIR.glob("*.md"))


def already_reminded_this_session() -> bool:
    if not MARKER.exists():
        return False
    # Marker is stale if older than 2 hours (new session)
    age = datetime.now().timestamp() - MARKER.stat().st_mtime
    return age < 7200


def main():
    now = datetime.now()
    week = current_iso_week()

    # Only nudge Saturday (5) or Sunday (6)
    if now.weekday() not in (5, 6):
        return

    if weekly_note_exists(week):
        return

    if already_reminded_this_session():
        return

    # Mark as reminded
    MARKER.touch()

    print(
        f"⚠ Weekly review for {week} not yet done. Weekly review time — run `/ecdysis` when ready."
    )


if __name__ == "__main__":
    main()
