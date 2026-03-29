"""oghma — extracted memory database (FTS5 + vector embeddings).

Tools:
  oghma_search — search memories (keyword/vector/hybrid)
  oghma_stats  — database statistics
  oghma_status — DB path, count, daemon state
  oghma_add    — manually insert a memory

Resources:
  vivesca://oghma/stats — memory database overview
"""



from metabolon.organelles.effector import run_cli  # noqa: E402

from fastmcp.tools import tool  # noqa: E402
from fastmcp.resources import resource  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

BINARY = "~/bin/oghma"


@tool(
    name="oghma_search",
    description=(
        "Search extracted memories by keyword (FTS5), vector similarity, "
        "or hybrid RRF fusion. Use for recall of past sessions."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def oghma_search(
    query: str,
    category: str = "",
    source_tool: str = "",
    limit: int = 10,
    mode: str = "hybrid",
) -> str:
    """Search extracted memories.

    Args:
        query: The search query.
        category: Filter by category (e.g. 'gotcha', 'pattern', 'preference').
        source_tool: Filter by originating tool name.
        limit: Max results (default 10).
        mode: 'keyword' (FTS5), 'vector' (cosine), or 'hybrid' (RRF fusion, default).
    """
    args = ["search", query, "-n", str(limit), "--mode", mode]
    if category:
        args.extend(["-c", category])
    if source_tool:
        args.extend(["-t", source_tool])
    return run_cli(BINARY, args)


@tool(
    name="oghma_stats",
    description="Get memory database statistics: counts by category and source tool.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def oghma_stats() -> str:
    """Get memory database statistics."""
    return run_cli(BINARY, ["stats"])


@tool(
    name="oghma_status",
    description="Show DB path, memory count, daemon state, and last extraction time.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def oghma_status() -> str:
    """Show oghma daemon status."""
    return run_cli(BINARY, ["status"])


@tool(
    name="oghma_add",
    description="Manually add a memory to the database.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def oghma_add(content: str, category: str = "gotcha", confidence: float = 0.8) -> str:
    """Manually add a memory.

    Args:
        content: The memory content text.
        category: Category label (default 'gotcha').
        confidence: Confidence score 0.0-1.0 (default 0.8).
    """
    args = ["add", content, "-c", category, "--confidence", str(confidence)]
    return run_cli(BINARY, args)


@resource("vivesca://oghma/stats")
def oghma_stats_resource() -> str:
    """Returns current memory database statistics."""
    return run_cli(BINARY, ["stats"])
