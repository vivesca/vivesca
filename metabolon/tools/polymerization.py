"""polymerization -- Praxis.md TODO management via praxis organelle.

Tools:
  polymerization  -- run praxis subcommands against Praxis.md
"""

import json

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion

SUBCOMMANDS = ("today", "upcoming", "overdue", "someday", "all", "spare", "stats", "clean")


class PolymerizationResult(Secretion):
    """Output from praxis organelle."""

    subcommand: str
    output: str


@tool(
    name="polymerization",
    description="Run todo commands on Praxis.md. Subcommands: today/upcoming/overdue/all/stats/clean.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def polymerization(subcommand: str = "today") -> PolymerizationResult:
    """Invoke praxis organelle against Praxis.md and return formatted output.

    Valid subcommands: today, upcoming, overdue, someday, all, spare, stats, clean.
    """
    if subcommand not in SUBCOMMANDS:
        raise ValueError(f"Unknown subcommand '{subcommand}'. Valid: {', '.join(SUBCOMMANDS)}")

    from metabolon.organelles import praxis

    fn_map = {
        "today": praxis.today,
        "upcoming": praxis.upcoming,
        "overdue": praxis.overdue,
        "someday": praxis.someday,
        "all": praxis.all_items,
        "spare": praxis.spare,
        "stats": praxis.stats,
        "clean": praxis.clean,
    }

    result = fn_map[subcommand]()
    output = json.dumps(result, indent=2, default=str)
    return PolymerizationResult(subcommand=subcommand, output=output)
