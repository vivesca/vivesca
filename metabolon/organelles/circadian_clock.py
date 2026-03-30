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


# ---------------------------------------------------------------------------
# Phase detection
# ---------------------------------------------------------------------------


def is_weekend(target_date: date | None = None) -> bool:
    """Return True if the given date is Saturday or Sunday (HKT)."""
    if target_date is None:
        target_date = datetime.now(HKT).date()
    return target_date.weekday() >= 5


def is_holiday(target_date: date | None = None) -> bool:
    """Return True if the calendar has an all-day event matching holiday keywords.

    Falls back to False on any error (network, parse, etc.).
    """
    if target_date is None:
        target_date = datetime.now(HKT).date()

    date_iso = target_date.isoformat()
    try:
        raw = _gog(["calendar", "list", "--from", date_iso, "--to", date_iso, "--json", "--max", "25"])
        data = json.loads(raw)
    except Exception as exc:
        logger.debug("Holiday check failed for %s: %s", date_iso, exc)
        return False

    for event in data.get("events", []):
        start = event.get("start", {})
        # All-day events use "date" key; timed events use "dateTime"
        if "date" not in start:
            continue
        summary = (event.get("summary") or "").lower()
        if any(kw in summary for kw in _HOLIDAY_KEYWORDS):
            return True
    return False


def detect_phase(now: datetime | None = None) -> dict[str, str | bool]:
    """Return the current circadian phase and day-type flags.

    Returns dict with keys:
        phase: "dawn" | "day" | "dusk" | "night"
        is_weekend: bool
        is_holiday: bool
        is_workday: bool  (True only on weekdays that are not holidays)
        hkt_hour: int
        weekday: str (full day name)
    """
    if now is None:
        now = datetime.now(HKT)

    target_date = now.date()
    hour = now.hour
    weekday_name = now.strftime("%A")
    weekend = is_weekend(target_date)
    holiday = is_holiday(target_date)
    workday = not weekend and not holiday

    if 6 <= hour < 10:
        phase = "dawn"
    elif 10 <= hour < 17:
        phase = "day"
    elif 17 <= hour < 21:
        phase = "dusk"
    else:
        phase = "night"

    return {
        "phase": phase,
        "is_weekend": weekend,
        "is_holiday": holiday,
        "is_workday": workday,
        "hkt_hour": hour,
        "weekday": weekday_name,
    }
