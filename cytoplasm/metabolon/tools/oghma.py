"""oghma — histone memory database (FTS5 + vector embeddings).

Chromatin-level storage: memories are histone marks that regulate
which knowledge is accessible for transcription.

Tools:
  histone_search — search memories (keyword/vector/hybrid)
  histone_stats  — database statistics
  histone_status — DB path, count, daemon state
  histone_mark   — manually inscribe a memory
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Secretion, Vital


class HistoneSearchResult(Secretion):
    """Histone search results — recalled memory marks."""

    results: str


class HistoneStatsResult(Secretion):
    """Histone database statistics."""

    stats: str


@tool(
    name="histone_search",
    description="Search memories: keyword/vector/hybrid. Use for past session recall.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def histone_search(
    query: str,
    category: str = "",
    source_enzyme: str = "",
    limit: int = 10,
    mode: str = "hybrid",
    chromatin: str = "open",
) -> HistoneSearchResult:
    """Search histone marks. chromatin='open' (active), 'closed' (archived), 'all'."""
    from metabolon.organelles.chromatin import search as _search

    results = _search(
        query,
        category=category,
        source_enzyme=source_enzyme,
        limit=limit,
        mode=mode,
        chromatin=chromatin,
    )
    formatted = "\n".join(str(r) for r in results) if results else "No results"
    return HistoneSearchResult(results=formatted)


@tool(
    name="histone_stats",
    description="Memory DB stats: counts by category and source.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def histone_stats() -> HistoneStatsResult:
    """Get histone database statistics."""
    from metabolon.organelles.chromatin import status as _status

    return HistoneStatsResult(stats=_status())


@tool(
    name="histone_status",
    description="Memory DB status: path, count, daemon state.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def histone_status() -> Vital:
    """Show histone daemon vital signs."""
    from metabolon.organelles.chromatin import status as _status

    return Vital(status="ok", message=_status())


@tool(
    name="histone_mark",
    description="Add a memory manually.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def histone_mark(
    content: str, category: str = "gotcha", confidence: float = 0.8
) -> EffectorResult:
    """Manually inscribe a histone mark."""
    from metabolon.organelles.chromatin import add as _add

    _add(content, category=category, confidence=confidence)
    return EffectorResult(success=True, message="Memory added")
