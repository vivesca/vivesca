from __future__ import annotations

"""rheotaxis — multi-backend web search.

Parallel search across Perplexity, Exa, Tavily, Serper.
Pipe-separated queries triangulate facts that single searches miss.
Depth tiers (quick/thorough/deep) control Perplexity model selection.
"""


from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.organelles import rheotaxis_engine


@tool(
    name="rheotaxis_search",
    description="Multi-backend web search. Pipe-separate queries for multi-framing. depth=quick|thorough|deep for Perplexity tier.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def rheotaxis_search(
    query: str,
    backends: str = "perplexity,exa,tavily,serper",
    depth: str = "quick",
    timeout: int = 20,
) -> str:
    """Search across backends in parallel.

    Args:
        query: Search query. Pipe-separate for multi-framing
               (e.g. "JINS Hong Kong|JINS store locator HK").
        backends: Comma-separated backend names (default: all).
        depth: Perplexity tier — quick (~$0.006), thorough (~$0.01),
               deep (~$0.40 EXPENSIVE). Only affects perplexity backend.
        timeout: Per-backend timeout in seconds.
    """
    backend_list = [b.strip() for b in backends.split(",")]
    queries = [q.strip() for q in query.split("|")]

    if len(queries) == 1:
        results = rheotaxis_engine.parallel_search(
            queries[0], backends=backend_list, depth=depth, timeout=timeout,
        )
        return rheotaxis_engine.format_results(results)
    else:
        all_results = rheotaxis_engine.multi_query_search(
            queries, backends=backend_list, depth=depth, timeout=timeout,
        )
        lines = []
        for q, results in all_results.items():
            lines.append(f"# {q}")
            lines.append(rheotaxis_engine.format_results(results))
        return "\n".join(lines)
