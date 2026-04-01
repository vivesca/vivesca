from __future__ import annotations

"""assay — life experiment tracker (N=1 self-experiments with Oura Ring).

Tools:
  assay — track life experiments: list, check, close
"""


from pathlib import Path

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.organelles.effector import run_cli

BINARY = str(Path.home() / "germline" / "effectors" / "assay")


@tool(
    name="assay",
    description="Life experiment tracker. Actions: list|check|close",
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, destructiveHint=False),
)
def assay(action: str, name: str = "") -> str:
    """Manage N=1 self-experiments with Oura Ring data.

    Args:
        action: "list" to list experiments, "check" to pull latest data,
                "close" to close with final comparison.
        name: Experiment name (used with check and close actions).
    """
    if action == "list":
        return run_cli(BINARY, ["list"], timeout=60)
    elif action == "check":
        args = ["check"]
        if name:
            args.append(name)
        return run_cli(BINARY, args, timeout=120)
    elif action == "close":
        args = ["close"]
        if name:
            args.append(name)
        return run_cli(BINARY, args, timeout=120)
    else:
        return f"Error: unknown action '{action}'. Use 'list', 'check', or 'close'."
