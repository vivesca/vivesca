from __future__ import annotations

"""rheotaxis — web search. Default: all cheap backends + synthesis. Named modes for expensive ones."""


from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.organelles import rheotaxis_engine


@tool(
    name="rheotaxis",
    description="Web search. Default: 8 backends parallel (~$0.03). mode=research: Perplexity deep ($0.40).",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
async def rheotaxis(
    query: str,
    mode: str = "",
) -> str:
    """Web search.

    Args:
        query: Search query. Pipe-separate for multi-framing.
        mode: Empty (default) = 8 backends parallel (~$0.03).
              'research' = Perplexity deep research (~$0.40).
    """
    if mode == "research":
        return rheotaxis_engine.perplexity_deep(query)

    from metabolon.enzymes._parallel_search import _report, _run_all

    results = await _run_all(query)
    return _report(query, results)
