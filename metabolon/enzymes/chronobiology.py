"""fasti — circadian schedule management (Google Calendar).

Tools:
  circadian_list   — list events for a date (read-only)
  circadian_set    — schedule a new event
  circadian_move   — reschedule an existing event
  circadian_delete — remove an event (destructive)
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Secretion


class CircadianList(Secretion):
    """Circadian listing — scheduled events for a date."""

    events: str


class CircadianAction(EffectorResult):
    """Result of a circadian schedule mutation."""

    pass


@tool(
    name="circadian_list",
    description="List calendar events for a date (HKT). Call first to get event IDs.",
    annotations=ToolAnnotations(readOnlyHint=True),
)
def circadian_list(date: str = "today") -> CircadianList:
    """List circadian events for a date."""
    from metabolon.organelles.circadian_clock import scheduled_events

    result = scheduled_events(date)
    return CircadianList(events=result)


@tool(
    name="circadian_set",
    description="Create a calendar event. Date: YYYY-MM-DD. Time: 24h HH:MM.",
    annotations=ToolAnnotations(idempotentHint=False),
)
def circadian_set(
    summary: str,
    date: str,
    from_time: str,
    to_time: str,
    description: str | None = None,
    location: str | None = None,
) -> CircadianAction:
    """Schedule a new circadian event."""
    args = ["create", summary, "--date", date, "--from", from_time, "--to", to_time]
    if description:
        args.extend(["--description", description])
    if location:
        args.extend(["--location", location])
    from metabolon.organelles.circadian_clock import schedule_event

    result = schedule_event(summary, date, from_time)
    return CircadianAction(success=True, message=result)


@tool(
    name="circadian_move",
    description="Reschedule an event. event_id from circadian_list — never guess.",
    annotations=ToolAnnotations(idempotentHint=True),
)
def circadian_move(event_id: str, date: str, time: str) -> CircadianAction:
    """Reschedule an existing circadian event."""
    from metabolon.organelles.circadian_clock import reschedule_event

    result = reschedule_event(event_id, date, time)
    return CircadianAction(success=True, message=result)


@tool(
    name="circadian_delete",
    description="Delete an event. event_id from circadian_list — never guess.",
    annotations=ToolAnnotations(destructiveHint=True),
)
def circadian_delete(event_id: str) -> CircadianAction:
    """Remove a circadian event."""
    from metabolon.organelles.circadian_clock import cancel_event

    result = cancel_event(event_id)
    return CircadianAction(success=True, message=result)
