from __future__ import annotations

"""assay — life experiment tracker (wraps peira).

Single tool with action dispatch:
  list  — list all experiments (read-only)
  check — check-in on an experiment (appends data)
  close — close an experiment with final comparison (destructive)
"""

from metabolon.organelles.effector import run_cli
from fastmcp.tools import tool
from mcp.types import ToolAnnotations

BINARY = "/Users/terry/germline/effectors/assay"


@tool(
    name="assay",
    description="Experiment tracking. Actions: list|check|close",
    annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False, destructiveHint=True),
)
def assay(action: str, name: str = "") -> str:
    """Run an assay action.

    Args:
        action: One of list|check|close.
            list  — list all experiments and their status.
            check — pull latest data and append a check-in.
            close — close an experiment with final comparison (irreversible).
        name: Experiment name (required for check and close).
    """
    if action == "list":
        return run_cli(BINARY, ["list"], timeout=30)
    elif action == "check":
        if not name:
            return "Error: name is required for check action."
        return run_cli(BINARY, ["check", name], timeout=60)
    elif action == "close":
        if not name:
            return "Error: name is required for close action."
        return run_cli(BINARY, ["close", name], timeout=60)
    else:
        return f"Error: unknown action '{action}'. Use list|check|close."
