"""assay — life experiment tracker (wraps peira).

Tools:
  assay_list  — list all experiments (read-only)
  assay_check — check-in on an experiment (appends data)
  assay_close — close an experiment with final comparison (destructive)
"""



from metabolon.organelles.effector import run_cli  # noqa: E402

from fastmcp.tools import tool  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

BINARY = "/Users/terry/germline/effectors/assay"


@tool(
    name="assay_list",
    description="List all life experiments and their current status.",
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, destructiveHint=False),
)
def assay_list() -> str:
    """List all experiments."""
    return run_cli(BINARY, ["list"], timeout=30)


@tool(
    name="assay_check",
    description="Pull latest data and append a check-in to an experiment.",
    annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False, destructiveHint=False),
)
def assay_check(name: str) -> str:
    """Check in on an experiment.

    Args:
        name: Experiment name as shown by assay_list.
    """
    return run_cli(BINARY, ["check", name], timeout=60)


@tool(
    name="assay_close",
    description="Close an experiment with a final comparison. Irreversible.",
    annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False, destructiveHint=True),
)
def assay_close(name: str) -> str:
    """Close an experiment.

    Args:
        name: Experiment name as shown by assay_list.
    """
    return run_cli(BINARY, ["close", name], timeout=60)
