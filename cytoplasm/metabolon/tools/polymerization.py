"""polymerization -- Praxis.md TODO management via todo-cli.

Tools:
  polymerization  -- run todo-cli subcommands against Praxis.md
"""

import subprocess

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion

TODO_CLI = "todo-cli"
PRAXIS = "~/epigenome/chromatin/Praxis.md"

SUBCOMMANDS = ("today", "upcoming", "overdue", "someday", "all", "spare", "stats", "clean")


class PolymerizationResult(Secretion):
    """Output from todo-cli."""

    subcommand: str
    output: str


@tool(
    name="polymerization",
    description="Run todo-cli on Praxis.md. Subcommands: today/upcoming/overdue/all/stats/clean.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def polymerization(subcommand: str = "today") -> PolymerizationResult:
    """Invoke todo-cli against Praxis.md and return raw output.

    Valid subcommands: today, upcoming, overdue, someday, all, spare, stats, clean.
    """
    if subcommand not in SUBCOMMANDS:
        raise ValueError(f"Unknown subcommand '{subcommand}'. Valid: {', '.join(SUBCOMMANDS)}")

    try:
        result = subprocess.run(
            [TODO_CLI, subcommand],
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            stderr = result.stderr.strip()
            raise ValueError(f"todo-cli {subcommand} failed: {stderr or 'non-zero exit'}")
        return PolymerizationResult(subcommand=subcommand, output=output or "(no output)")
    except FileNotFoundError as exc:
        raise ValueError("todo-cli not found on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError("todo-cli timed out (15s)") from exc
