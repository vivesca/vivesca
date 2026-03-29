"""fasti — Google Calendar management.

Tools:
  fasti_list_events  — list events for a date (read-only)
  fasti_create_event — create a new event
  fasti_move_event   — reschedule an existing event
  fasti_delete_event — remove an event (destructive)
"""

from typing import Optional


from metabolon.organelles.effector import run_cli  # noqa: E402

from fastmcp.tools import tool  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

BINARY = "~/bin/fasti"


@tool(
    name="fasti_list_events",
    description=(
        "List Google Calendar events for a specific date. "
        "All times are in HKT (UTC+8). "
        "Always call this first to get event IDs before moving or deleting."
    ),
    annotations=ToolAnnotations(readOnlyHint=True),
)
def fasti_list_events(date: str = "today") -> str:
    """List Google Calendar events for a date.

    Args:
        date: 'today', 'tomorrow', or a date in 'YYYY-MM-DD' format.
    """
    return run_cli(BINARY, ["list", date])


@tool(
    name="fasti_create_event",
    description=(
        "Create a new Google Calendar event. "
        "Date format: YYYY-MM-DD or 'today'/'tomorrow'. Time format: 24h HH:MM."
    ),
    annotations=ToolAnnotations(idempotentHint=False),
)
def fasti_create_event(
    summary: str,
    date: str,
    from_time: str,
    to_time: str,
    description: Optional[str] = None,
    location: Optional[str] = None,
) -> str:
    """Create a new Google Calendar event.

    Args:
        summary: Short title for the event.
        date: Date in 'YYYY-MM-DD' format (or 'today'/'tomorrow').
        from_time: Start time in 24h format 'HH:MM'.
        to_time: End time in 24h format 'HH:MM'.
        description: Optional detailed notes for the event.
        location: Optional physical address or video link.
    """
    args = ["create", summary, "--date", date, "--from", from_time, "--to", to_time]
    if description:
        args.extend(["--description", description])
    if location:
        args.extend(["--location", location])
    return run_cli(BINARY, args)


@tool(
    name="fasti_move_event",
    description=(
        "Reschedule an existing Google Calendar event. "
        "event_id must be obtained from fasti_list_events — never guess it."
    ),
    annotations=ToolAnnotations(idempotentHint=True),
)
def fasti_move_event(event_id: str, date: str, time: str) -> str:
    """Reschedule an existing event.

    Args:
        event_id: Must be obtained from fasti_list_events — not guessable.
        date: New date in 'YYYY-MM-DD' format (or 'today'/'tomorrow').
        time: New start time in 24h format 'HH:MM'.
    """
    return run_cli(BINARY, ["move", event_id, date, time])


@tool(
    name="fasti_delete_event",
    description=(
        "Remove an event from Google Calendar. "
        "event_id must be obtained from fasti_list_events — never guess it."
    ),
    annotations=ToolAnnotations(destructiveHint=True),
)
def fasti_delete_event(event_id: str) -> str:
    """Remove an event from Google Calendar.

    Args:
        event_id: Must be obtained from fasti_list_events — not guessable.
    """
    return run_cli(BINARY, ["delete", event_id])
