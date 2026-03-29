from __future__ import annotations

"""pseudopod — remaining browser cookie bridge for auth injection."""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult


@tool(
    name="porta_inject",
    description="Inject Chrome cookies into agent-browser for a domain.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def porta_inject(domain: str) -> EffectorResult:
    from metabolon.organelles.porta import inject

    result = inject(domain)
    return EffectorResult(
        success=result["success"],
        message=result["message"],
        data={"count": result["count"], "domain": domain},
    )
