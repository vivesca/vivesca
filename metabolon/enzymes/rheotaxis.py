"""rheotaxis — multi-backend web search.

Parallel search across Perplexity, Exa, Tavily, Serper.
Multiple query framings triangulate facts that single searches miss.
"""

from __future__ import annotations

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.organelles import rheotaxis_engine


@tool(
    name="rheotaxis_search",
    description="Search across multiple backends in parallel. Returns results from Perplexity, Exa, Tavily, Serper.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def rheotaxis_search(
    query: str,
    backends: str = "perplexity,exa,tavily,serper",
    timeout: int = 20,
) -> str:
    """Single query across selected backends.

    Args:
        query: Search query.
        backends: Comma-separated backend names (default: all).
        timeout: Per-backend timeout in seconds.
    """
    backend_list = [b.strip() for b in backends.split(",")]
    results = rheotaxis_engine.parallel_search(query, backends=backend_list, timeout=timeout)
    return rheotaxis_engine.format_results(results)


@tool(
    name="rheotaxis_multi",
    description="Search multiple query framings across backends. Use when one framing might miss results.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def rheotaxis_multi(
    queries: str,
    backends: str = "perplexity,exa,tavily,serper",
    timeout: int = 20,
) -> str:
    """Multiple query framings across selected backends.

    Args:
        queries: Pipe-separated query framings (e.g. "JINS Hong Kong Island|JINS Wan Chai|JINS store locator HK").
        backends: Comma-separated backend names (default: all).
        timeout: Per-backend timeout in seconds.
    """
    query_list = [q.strip() for q in queries.split("|")]
    backend_list = [b.strip() for b in backends.split(",")]
    all_results = rheotaxis_engine.multi_query_search(
        query_list, backends=backend_list, timeout=timeout
    )
    lines = []
    for q, results in all_results.items():
        lines.append(f"# {q}")
        lines.append(rheotaxis_engine.format_results(results))
    return "\n".join(lines)
