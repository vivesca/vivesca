
"""circadian_clock — Google Calendar API client for headless environments.

Direct Google Calendar API access — no gog CLI dependency.
Auth: refresh token from env vars or gog's token.json. No browser needed.

Phase detection: dawn (06–10), day (10–17), dusk (17–21), night (21–06).
Weekend and holiday awareness for schedule-sensitive routing.
"""

import logging
import os
import threading
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

HKT = timezone(timedelta(hours=8))

logger = logging.getLogger(__name__)

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]
GOG_TOKEN_FILE = Path.home() / ".config" / "gog" / "token.json"
_service_lock = threading.Lock()
_cached_service = None


def _get_credentials() -> Credentials:
    """Build credentials from env vars or gog token file."""
    client_id = os.environ.get("GCAL_CLIENT_ID", "")
    client_secret = os.environ.get("GCAL_CLIENT_SECRET", "")
    refresh_token = os.environ.get("GCAL_REFRESH_TOKEN", "")

    if client_id and client_secret and refresh_token:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=CALENDAR_SCOPES,
        )
        creds.refresh(Request())
        return creds

    if GOG_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(GOG_TOKEN_FILE), CALENDAR_SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if creds and creds.valid:
            return creds

    raise RuntimeError(
        "Calendar auth failed. Set GCAL_CLIENT_ID, GCAL_CLIENT_SECRET, "
        "GCAL_REFRESH_TOKEN env vars, or place a valid token.json at "
        f"{GOG_TOKEN_FILE}"
    )


def service():
    """Return an authenticated Calendar API service. Rebuilds on token expiry."""
    global _cached_service
    with _service_lock:
        if _cached_service is not None:
            creds = _cached_service._http.credentials
            if creds.valid:
                return _cached_service
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                return _cached_service
        _cached_service = build("calendar", "v3", credentials=_get_credentials())
        return _cached_service


def _resolve_date(date_str: str) -> tuple[datetime, datetime]:
    """Resolve a date string to (start, end) datetime pair in HKT."""
    now = datetime.now(HKT)
    if date_str in ("today", ""):
        day = now.date()
    elif date_str == "tomorrow":
        day = (now + timedelta(days=1)).date()
    elif date_str == "yesterday":
        day = (now - timedelta(days=1)).date()
    else:
        day = date.fromisoformat(date_str)
    start = datetime(day.year, day.month, day.day, tzinfo=HKT)
    end = start + timedelta(days=1)
    return start, end


def scheduled_events(date_str: str = "today") -> str:
    """List calendar events for a date as formatted text."""
    events = scheduled_events_json(date_str)
    if not events:
        return "No events."
    lines = []
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date", ""))
        summary = event.get("summary", "(no title)")
        if "T" in start:
            time_part = start.split("T")[1][:5]
            lines.append(f"{time_part}  {summary}")
        else:
            lines.append(f"all-day  {summary}")
    return "\n".join(lines)


def scheduled_events_json(date_str: str = "today") -> list[dict]:
    """List events as structured data."""
    try:
        start, end = _resolve_date(date_str)
        svc = service()
        result = (
            svc.events()
            .list(
                calendarId="primary",
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return result.get("items", [])
    except Exception as exc:
        logger.debug("Calendar list failed: %s", exc)
        return []


def schedule_event(title: str, date_str: str, time_str: str, duration: int = 60) -> str:
    """Create a calendar event. Returns event ID."""
    day = date.fromisoformat(date_str)
    hour, minute = (int(p) for p in time_str.split(":"))
    start_dt = datetime(day.year, day.month, day.day, hour, minute, tzinfo=HKT)
    end_dt = start_dt + timedelta(minutes=duration)
    body = {
        "summary": title,
        "start": {"dateTime": start_dt.isoformat()},
        "end": {"dateTime": end_dt.isoformat()},
    }
    event = service().events().insert(calendarId="primary", body=body).execute()
    return event.get("id", "")


def reschedule_event(event_id: str, date_str: str, time_str: str) -> str:
    """Move an event to a new date/time."""
    day = date.fromisoformat(date_str)
    hour, minute = (int(p) for p in time_str.split(":"))
    start_dt = datetime(day.year, day.month, day.day, hour, minute, tzinfo=HKT)
    svc = service()
    existing = svc.events().get(calendarId="primary", eventId=event_id).execute()
    old_start = existing["start"].get("dateTime", "")
    old_end = existing["end"].get("dateTime", "")
    if old_start and old_end:
        old_duration = datetime.fromisoformat(old_end) - datetime.fromisoformat(old_start)
    else:
        old_duration = timedelta(hours=1)
    end_dt = start_dt + old_duration
    existing["start"] = {"dateTime": start_dt.isoformat()}
    existing["end"] = {"dateTime": end_dt.isoformat()}
    svc.events().update(calendarId="primary", eventId=event_id, body=existing).execute()
    return event_id


def cancel_event(event_id: str) -> str:
    """Delete a calendar event."""
    service().events().delete(calendarId="primary", eventId=event_id).execute()
    return event_id


# ---------------------------------------------------------------------------
# Phase detection
# ---------------------------------------------------------------------------


def is_weekend(target_date: date | None = None) -> bool:
    """Return True if the given date is Saturday or Sunday (HKT)."""
    if target_date is None:
        target_date = datetime.now(HKT).date()
    return target_date.weekday() >= 5


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


def is_holiday(target_date: date | None = None) -> bool:
    """Return True if the calendar has an all-day event matching holiday keywords.

    Falls back to False on any error (network, parse, etc.).
    """
    if target_date is None:
        target_date = datetime.now(HKT).date()

    try:
        events = scheduled_events_json(target_date.isoformat())
    except Exception as exc:
        logger.debug("Holiday check failed for %s: %s", target_date, exc)
        return False

    for event in events:
        start = event.get("start", {})
        if "date" not in start:
            continue
        summary = (event.get("summary") or "").lower()
        if any(kw in summary for kw in _HOLIDAY_KEYWORDS):
            return True
    return False


def detect_phase(now: datetime | None = None) -> dict[str, str | bool | int]:
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
