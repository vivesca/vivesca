"""circadian — calendar management (Google Calendar via fasti CLI).

Actions: list|set|move|delete|sleep|heartrate
Absorbs: chronobiology (circadian_*), fasti (fasti_*), circadian_sleep, circadian_heartrate from interoception.
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Secretion, Vital


class CircadianResult(Secretion):
    output: str


_ACTIONS = (
    "list — list events for a date (HKT). Call first to get event IDs. "
    "set — create a new event. Requires: summary, date, from_time, to_time. Optional: description, location. "
    "move — reschedule an event. Requires: event_id, date, time. "
    "delete — remove an event. Requires: event_id. "
    "sleep — Oura sleep data. Optional: period=today|week. "
    "heartrate — Oura HR time-series. Optional: start_datetime, end_datetime."
)


@tool(
    name="circadian",
    description=f"Calendar + sleep + HR. Actions: {_ACTIONS}",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def circadian(
    action: str,
    # list / set / move / delete
    date: str = "today",
    summary: str = "",
    from_time: str = "",
    to_time: str = "",
    description: str | None = None,
    location: str | None = None,
    event_id: str = "",
    time: str = "",
    # sleep / heartrate
    period: str = "today",
    start_datetime: str = "",
    end_datetime: str = "",
) -> CircadianResult:
    """Unified calendar + circadian rhythm tool."""
    action = action.lower().strip()

    if action == "list":
        from metabolon.organelles.circadian_clock import scheduled_events
        return CircadianResult(output=scheduled_events(date))

    elif action == "set":
        if not summary or not date or not from_time or not to_time:
            return CircadianResult(output="set requires: summary, date, from_time, to_time")
        from metabolon.organelles.circadian_clock import schedule_event
        result = schedule_event(summary, date, from_time)
        return CircadianResult(output=result)

    elif action == "move":
        if not event_id or not date or not time:
            return CircadianResult(output="move requires: event_id, date, time")
        from metabolon.organelles.circadian_clock import reschedule_event
        result = reschedule_event(event_id, date, time)
        return CircadianResult(output=result)

    elif action == "delete":
        if not event_id:
            return CircadianResult(output="delete requires: event_id")
        from metabolon.organelles.circadian_clock import cancel_event
        result = cancel_event(event_id)
        return CircadianResult(output=result)

    elif action == "sleep":
        from metabolon.organelles.chemoreceptor import sleep_summary
        return CircadianResult(output=sleep_summary(period))

    elif action == "heartrate":
        from metabolon.organelles.chemoreceptor import heartrate_series
        return CircadianResult(output=heartrate_series(start_datetime, end_datetime))

    else:
        return CircadianResult(output=f"Unknown action '{action}'. Valid: list, set, move, delete, sleep, heartrate")
