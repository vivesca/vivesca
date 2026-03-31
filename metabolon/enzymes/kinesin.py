from __future__ import annotations

"""kinesin — session-independent agent dispatcher.

Tool:
  translocation — async tasks. Actions: list|run|cancel|results
"""


from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Secretion


class TranslocationResult(Secretion):
    """Kinesin task output."""

    output: str


@tool(
    name="translocation",
    description="Async tasks. Actions: list|run|cancel|results",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def translocation(action: str, name: str = "") -> TranslocationResult | EffectorResult:
    """Dispatch and manage async kinesin tasks.

    Actions:
      list    — list all kinesin tasks with schedule and status
      run     — dispatch a task immediately (detached, survives session); requires name
      cancel  — cancel/disable a task; requires name
      results — view latest run output; optional name (omit for all tasks)

    Args:
        action: One of list|run|cancel|results.
        name: Task name (required for run/cancel, optional for results, ignored for list).
    """
    if action == "list":
        from metabolon.organelles.gemmation import list_tasks

        return TranslocationResult(output=list_tasks())

    elif action == "run":
        from metabolon.organelles.gemmation import run_task

        result = run_task(name)
        return EffectorResult(success=True, message=result)

    elif action == "cancel":
        from metabolon.organelles.gemmation import cancel_task

        result = cancel_task(name)
        return EffectorResult(success=True, message=result)

    elif action == "results":
        from metabolon.organelles.gemmation import get_results

        return TranslocationResult(output=get_results(name or None))

    else:
        return TranslocationResult(output=f"Unknown action: {action}. Use list|run|cancel|results.")
