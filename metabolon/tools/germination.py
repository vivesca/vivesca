"""germination — overnight agent results with conditions-triggered surfacing.

Biology: spores germinate when CONDITIONS are right (nutrients, moisture,
temperature), not on a timer. Results surface when ready, not when asked.

Tools:
  germination_brief   — morning dashboard: latest overnight run summary
  germination_results — drill into individual task outputs
  germination_list    — recent run history
"""

import os

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.cytosol import invoke_organelle
from metabolon.morphology import Secretion

OVERNIGHT = "overnight-gather"
_GERMINATION_FLAG = os.path.expanduser("~/logs/germination-pending.flag")


class GerminationResult(Secretion):
    """Overnight agent output."""

    output: str


def check_germination() -> str | None:
    """Check if overnight results need attention. Called by pulse.

    Returns a summary if NEEDS_ATTENTION is flagged, None otherwise.
    This is the conditions-triggered germination — results surface
    when ready, not when the user asks.
    """
    try:
        result = invoke_organelle(OVERNIGHT, ["brief"], timeout=10)
    except (ValueError, TimeoutError):
        return None

    if "NEEDS_ATTENTION" in result:
        # Write flag for interphase/session-start to pick up
        with open(_GERMINATION_FLAG, "w") as f:
            f.write(result[:500])
        return result
    else:
        # Clear flag if nothing pending
        if os.path.exists(_GERMINATION_FLAG):
            os.remove(_GERMINATION_FLAG)
        return None


def has_pending_germination() -> str | None:
    """Quick check: is there a pending germination flag? Non-blocking."""
    try:
        with open(_GERMINATION_FLAG) as f:
            return f.read()
    except FileNotFoundError:
        return None


@tool(
    name="germination_brief",
    description="Morning brief: latest overnight run summary, flags NEEDS_ATTENTION.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def germination_brief() -> GerminationResult:
    """Show the latest morning-dashboard output."""
    result = invoke_organelle(OVERNIGHT, ["brief"], timeout=15)
    return GerminationResult(output=result)


@tool(
    name="germination_results",
    description="Overnight task results. Name for one task, empty for all.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def germination_results(task: str = "") -> GerminationResult:
    """Drill into individual overnight task outputs."""
    args = ["results"]
    if task:
        args.extend(["--task", task])
    result = invoke_organelle(OVERNIGHT, args, timeout=15)
    return GerminationResult(output=result)


@tool(
    name="germination_list",
    description="Last 5 overnight runs with pass/fail per task.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def germination_list() -> GerminationResult:
    """Show recent overnight run history."""
    result = invoke_organelle(OVERNIGHT, ["list"], timeout=15)
    return GerminationResult(output=result)
