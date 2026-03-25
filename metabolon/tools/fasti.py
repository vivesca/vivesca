"""fasti — cell cycle checkpoint management (Google Calendar).

Tools:
  checkpoint_list   — list checkpoints for a date (read-only)
  checkpoint_set    — set a new checkpoint
  checkpoint_move   — reschedule an existing checkpoint
  checkpoint_delete — remove a checkpoint (destructive)
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Secretion


class CheckpointList(Secretion):
    """Checkpoint listing — scheduled cell cycle events."""

    events: str


class CheckpointAction(EffectorResult):
    """Result of a checkpoint mutation."""

    pass


@tool(
    name="checkpoint_list",
    description="List calendar events for a date (HKT). Call first to get event IDs.",
    annotations=ToolAnnotations(readOnlyHint=True),
)
def checkpoint_list(date: str = "today") -> CheckpointList:
    """List cell cycle checkpoints for a date."""
    from metabolon.organelles.circadian_clock import scheduled_events

    result = scheduled_events(date)
    return CheckpointList(events=result)


@tool(
    name="checkpoint_set",
    description="Create a calendar event. Date: YYYY-MM-DD. Time: 24h HH:MM.",
    annotations=ToolAnnotations(idempotentHint=False),
)
def checkpoint_set(
    summary: str,
    date: str,
    from_time: str,
    to_time: str,
    description: str | None = None,
    location: str | None = None,
) -> CheckpointAction:
    """Set a new cell cycle checkpoint."""
    args = ["create", summary, "--date", date, "--from", from_time, "--to", to_time]
    if description:
        args.extend(["--description", description])
    if location:
        args.extend(["--location", location])
    from metabolon.organelles.circadian_clock import schedule_event

    result = schedule_event(summary, date, from_time)
    return CheckpointAction(success=True, message=result)


@tool(
    name="checkpoint_move",
    description="Reschedule an event. event_id from checkpoint_list — never guess.",
    annotations=ToolAnnotations(idempotentHint=True),
)
def checkpoint_move(event_id: str, date: str, time: str) -> CheckpointAction:
    """Reschedule an existing checkpoint."""
    from metabolon.organelles.circadian_clock import reschedule_event

    result = reschedule_event(event_id, date, time)
    return CheckpointAction(success=True, message=result)


@tool(
    name="checkpoint_delete",
    description="Delete an event. event_id from checkpoint_list — never guess.",
    annotations=ToolAnnotations(destructiveHint=True),
)
def checkpoint_delete(event_id: str) -> CheckpointAction:
    """Remove a checkpoint from the cell cycle."""
    from metabolon.organelles.circadian_clock import cancel_event

    result = cancel_event(event_id)
    return CheckpointAction(success=True, message=result)
