"""kinesin — session-independent agent dispatcher.

Tools:
  translocation_list    — list all kinesin tasks + status
  translocation_run     — dispatch a task immediately (detached)
  translocation_cancel  — cancel/disable a task
  translocation_results — view latest run output
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Secretion


class TranslocationResult(Secretion):
    """Kinesin task output."""

    output: str


@tool(
    name="translocation_list",
    description="List all kinesin tasks with schedule and status.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def translocation_list() -> TranslocationResult:
    """List all configured kinesin tasks."""
    from metabolon.organelles.dispatcher import list_tasks

    return TranslocationResult(output=list_tasks())


@tool(
    name="translocation_run",
    description="Dispatch a kinesin task immediately (detached, survives session).",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def translocation_run(name: str) -> EffectorResult:
    """Dispatch a kinesin task by name."""
    from metabolon.organelles.dispatcher import run_task

    result = run_task(name)
    return EffectorResult(success=True, message=result)


@tool(
    name="translocation_cancel",
    description="Cancel/disable a kinesin task.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def translocation_cancel(name: str) -> EffectorResult:
    """Cancel a kinesin task."""
    from metabolon.organelles.dispatcher import cancel_task

    result = cancel_task(name)
    return EffectorResult(success=True, message=result)


@tool(
    name="translocation_results",
    description="View latest kinesin run output for a task (or all tasks).",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def translocation_results(name: str = "") -> TranslocationResult:
    """View results of a kinesin task run."""
    from metabolon.organelles.dispatcher import get_results

    return TranslocationResult(output=get_results(name or None))
