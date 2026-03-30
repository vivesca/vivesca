from __future__ import annotations

"""pseudopod — browser cookie bridge + translocon dispatch for LLM tasks."""

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


@tool(
    name="translocon_dispatch",
    description="Dispatch cheap LLM task via goose/droid on ZhiPu coding plan.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def translocon_dispatch(
    prompt: str,
    mode: str = "explore",
    skill: str = "",
    model: str = "",
    backend: str = "",
    directory: str = ".",
) -> EffectorResult:
    from metabolon.organelles.translocon import dispatch

    result = dispatch(
        prompt=prompt,
        mode=mode,
        skill=skill or None,
        model=model or None,
        backend=backend or None,
        directory=directory,
    )
    return EffectorResult(
        success=result["success"],
        message=result["output"][:200],
        data=result,
    )
