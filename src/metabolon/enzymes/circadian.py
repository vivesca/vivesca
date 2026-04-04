"""circadian — calendar management plus sleep and heart-rate sensing."""

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Secretion


class CircadianResult(Secretion):
    output: str


@tool(
    name="circadian",
    description="Circadian. Actions: list|set|move|delete|sleep|heartrate",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def circadian(
    action: str,
    date: str = "today",
    summary: str = "",
    from_time: str = "",
    to_time: str = "",
    description: str | None = None,
    location: str | None = None,
    event_id: str = "",
    time: str = "",
    period: str = "today",
    start_datetime: str = "",
    end_datetime: str = "",
) -> CircadianResult | EffectorResult:
    action = action.lower().strip()

    if action == "list":
        from metabolon.organelles.circadian_clock import scheduled_events

        return CircadianResult(output=scheduled_events(date))

    if action == "set":
        if not summary or not date or not from_time or not to_time:
            return EffectorResult(
                success=False, message="set requires: summary, date, from_time, to_time"
            )
        from metabolon.organelles.circadian_clock import schedule_event

        duration_minutes = 60
        try:
            start_hour, start_minute = map(int, from_time.split(":", 1))
            end_hour, end_minute = map(int, to_time.split(":", 1))
            duration_minutes = (end_hour * 60 + end_minute) - (start_hour * 60 + start_minute)
            if duration_minutes <= 0:
                duration_minutes = 60
        except ValueError:
            duration_minutes = 60
        details = []
        if description:
            details.append(f"description ignored by circadian_clock: {description}")
        if location:
            details.append(f"location ignored by circadian_clock: {location}")
        result = schedule_event(summary, date, from_time, duration=duration_minutes)
        if details:
            result = result + "\n" + "\n".join(details)
        return CircadianResult(output=result)

    if action == "move":
        if not event_id or not date or not time:
            return EffectorResult(success=False, message="move requires: event_id, date, time")
        from metabolon.organelles.circadian_clock import reschedule_event

        return CircadianResult(output=reschedule_event(event_id, date, time))

    if action == "delete":
        if not event_id:
            return EffectorResult(success=False, message="delete requires: event_id")
        from metabolon.organelles.circadian_clock import cancel_event

        return CircadianResult(output=cancel_event(event_id))

    if action == "sleep":
        from metabolon.enzymes.interoception import _sleep_result

        return CircadianResult(output=_sleep_result(period).summary)

    if action == "heartrate":
        from metabolon.enzymes.interoception import _heartrate_result

        return CircadianResult(output=_heartrate_result(start_datetime, end_datetime).summary)

    return EffectorResult(
        success=False,
        message="Unknown action. Valid: list, set, move, delete, sleep, heartrate",
    )
