"""ecphory — deterministic memory retrieval across stores.

Actions: engram|chromatin|logs
"""

from __future__ import annotations

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion


class EcphoryResult(Secretion):
    results: str


_ACTIONS = (
    "engram — search session transcripts (episodic memory). Requires: query. Optional: days, deep, role. "
    "chromatin — search oghma semantic memory store. Requires: query. Optional: category, limit, mode, accessibility. "
    "logs — search structured log files. Requires: query. Optional: days."
)


@tool(
    name="ecphory",
    description=f"Memory retrieval. Actions: {_ACTIONS}",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def ecphory(
    action: str,
    query: str = "",
    # engram params
    days: int = 7,
    deep: bool = True,
    role: str = "",
    # chromatin params
    category: str = "",
    limit: int = 10,
    mode: str = "hybrid",
    accessibility: str = "open",
) -> EcphoryResult:
    """Unified memory retrieval tool."""
    action = action.lower().strip()

    if action == "engram":
        if not query:
            return EcphoryResult(results="engram requires: query")
        from metabolon.organelles.engram import search as _engram_search
        results = _engram_search(query, days=days, deep=deep, role=role or None)
        return EcphoryResult(results=results)

    elif action == "chromatin":
        if not query:
            return EcphoryResult(results="chromatin requires: query")
        from metabolon.organelles.chromatin import search as _chromatin_search
        results = _chromatin_search(
            query,
            category=category,
            limit=limit,
            mode=mode,
            chromatin=accessibility,
        )
        formatted = "\n".join(str(r) for r in results) if results else "No results"
        return EcphoryResult(results=formatted)

    elif action == "logs":
        if not query:
            return EcphoryResult(results="logs requires: query")
        from metabolon.organelles.engram import search_logs
        results = search_logs(query, days=days)
        return EcphoryResult(results=results)

    else:
        return EcphoryResult(results=f"Unknown action '{action}'. Valid: engram, chromatin, logs")
