"""circadian_clock — Google Calendar via gog CLI (formerly fasti).

Endosymbiosis: Rust binary → Python organelle.
Still wraps gog (Go CLI) for GCal API access. The Rust layer
was just formatting — Python handles that directly now.

Phase detection: dawn (06–10), day (10–17), dusk (17–21), night (21–06).
Weekend and holiday awareness for schedule-sensitive routing.
"""

from __future__ import annotations

import json
import logging
import subprocess
from datetime import date, datetime, timedelta, timezone

HKT = timezone(timedelta(hours=8))

logger = logging.getLogger(__name__)

# All-day event title keywords indicating a non-working day
_HOLIDAY_KEYWORDS = (
    "holiday",
    "public holiday",
    "day off",
    "leave",
    "annual leave",
    "al",
    "休假",
    "假期",
    "放假",
    "替假",
)


def _gog(args: list[str], timeout: int = 15) -> str:
    """Call gog CLI."""
    r = subprocess.run(
        ["gog", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if r.returncode != 0:
        raise ValueError(f"gog failed: {r.stderr.strip()}")
    return r.stdout.strip()


def scheduled_events(date: str = "today") -> str:
    """List calendar events for a date."""
    return _gog(["calendar", "list", "--json" if date == "today" else date])


def scheduled_events_json(date: str = "today") -> list[dict]:
    """List events as structured data."""
    raw = _gog(["calendar", "list", "--json"])
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def schedule_event(title: str, date: str, time: str, duration: int = 60) -> str:
    """Create a calendar event."""
    return _gog(
        ["calendar", "create", title, "--date", date, "--time", time, "--duration", str(duration)]
    )


def reschedule_event(event_id: str, date: str, time: str) -> str:
    """Move an event to a new date/time."""
    return _gog(["calendar", "update", event_id, "--from", f"{date}T{time}"])


def cancel_event(event_id: str) -> str:
    """Delete a calendar event."""
    return _gog(["calendar", "delete", event_id, "--force"])
