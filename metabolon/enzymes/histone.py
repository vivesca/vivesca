"""histone — memory database (FTS5 + vector embeddings).

Actions: search|mark|stats|status
Absorbs: oghma (same DB, different CLI frontend).
"""

from __future__ import annotations

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Secretion, Vital


class HistoneResult(Secretion):
    results: str


_ACTIONS = (
    "search — search memories (keyword/vector/hybrid). Requires: query. Optional: category, source, limit, mode, chromatin. "
    "mark — add a memory manually. Requires: content. Optional: category, confidence. "
    "stats — database statistics. "
    "status — DB path, count, daemon state."
)


@tool(
    name="histone",
    description=f"Memory database. Actions: {_ACTIONS}",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def histone(
    action: str,
    query: str = "",
    content: str = "",
    category: str = "",
    source: str = "",
    limit: int = 10,
    mode: str = "hybrid",
    chromatin: str = "open",
    confidence: float = 0.8,
) -> HistoneResult | Vital | EffectorResult:
    """Unified memory tool."""
    action = action.lower().strip()

    if action == "search":
        if not query:
            return EffectorResult(success=False, message="search requires: query")
        from metabolon.organelles.chromatin import search as _search
        results = _search(
            query,
            category=category,
            source_enzyme=source,
            limit=limit,
            mode=mode,
            chromatin=chromatin,
        )
        formatted = "\n".join(str(r) for r in results) if results else "No results"
        return HistoneResult(results=formatted)

    elif action == "mark":
        if not content:
            return EffectorResult(success=False, message="mark requires: content")
        from metabolon.organelles.chromatin import add as _add
        _add(content, category=category or "gotcha", confidence=confidence)
        return EffectorResult(success=True, message="Memory added")

    elif action == "stats":
        from metabolon.organelles.chromatin import status as _status
        return HistoneResult(results=_status())

    elif action == "status":
        from metabolon.organelles.chromatin import status as _status
        return Vital(status="ok", message=_status())

    else:
        return EffectorResult(success=False, message=f"Unknown action '{action}'. Valid: search, mark, stats, status")
