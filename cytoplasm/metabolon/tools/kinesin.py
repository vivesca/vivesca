"""kinesin — session-independent agent dispatcher.

Tools:
  translocation_list    — list all kinesin tasks + status
  translocation_run     — dispatch a task immediately (detached)
  translocation_cancel  — cancel/disable a task
  translocation_results — view latest run output
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.cytosol import invoke_organelle
from metabolon.morphology import EffectorResult, Secretion

KINESIN = "kinesin"


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
    result = invoke_organelle(KINESIN, ["list"], timeout=15)
    return TranslocationResult(output=result)


@tool(
    name="translocation_run",
    description="Dispatch a kinesin task immediately (detached, survives session).",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def translocation_run(name: str) -> EffectorResult:
    """Dispatch a kinesin task by name."""
    result = invoke_organelle(KINESIN, ["run", name], timeout=30)
    return EffectorResult(success=True, message=result)


@tool(
    name="translocation_cancel",
    description="Cancel/disable a kinesin task.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def translocation_cancel(name: str) -> EffectorResult:
    """Cancel a kinesin task."""
    result = invoke_organelle(KINESIN, ["cancel", name], timeout=15)
    return EffectorResult(success=True, message=result)


@tool(
    name="translocation_results",
    description="View latest kinesin run output for a task (or all tasks).",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def translocation_results(name: str = "") -> TranslocationResult:
    """View results of a kinesin task run."""
    args = ["results"]
    if name:
        args.append(name)
    result = invoke_organelle(KINESIN, args, timeout=15)
    return TranslocationResult(output=result)
