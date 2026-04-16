"""rheotaxis — web search. Default: all cheap backends + synthesis. Named modes for expensive ones."""

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.organelles import rheotaxis_engine


@tool(
    name="rheotaxis",
    description="Web search. Default: 7 backends parallel (~$0.03). mode=research: Perplexity deep ($0.40). exclude: skip backends by name.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
async def rheotaxis(
    query: str,
    mode: str = "",
    exclude: str = "",
    json_output: bool = False,
) -> str:
    """Web search.

    Args:
        query: Search query. Pipe-separate for multi-framing.
        mode: Empty (default) = 7 backends parallel (~$0.03).
              'research' = Perplexity deep research (~$0.40).
        exclude: Comma-separated backend names to skip (e.g. 'zhipu' for English-only queries).
                 Available: grok, exa, perplexity, tavily, serper, zhipu, jina.
        json_output: Return structured JSON instead of markdown prose.
    """
    if mode == "research":
        return rheotaxis_engine.perplexity_deep(query)

    from metabolon.enzymes._parallel_search import _report, _run_all

    exclude_set = (
        {name.strip().lower() for name in exclude.split(",") if name.strip()} if exclude else set()
    )
    results = await _run_all(query, exclude=exclude_set)
    return _report(query, results, json_output=json_output)
