from __future__ import annotations

"""histone — memory database (FTS5 + vector embeddings)."""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Secretion, Vital


class HistoneResult(Secretion):
    results: str


def _format_search_results(results: list[dict]) -> str:
    if not results:
        return "No results"
    lines = []
    for result in results:
        name = result.get("name", result.get("file", "unknown"))
        path = result.get("path", "")
        content = str(result.get("content", "")).strip().replace("\n", " ")
        if len(content) > 160:
            content = content[:157] + "..."
        lines.append(f"- {name}")
        lines.append(f"  path: {path}")
        lines.append(f"  content: {content}")
    return "\n".join(lines)


@tool(
    name="histone",
    description="Histone. Actions: search|mark|stats|status",
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
    action = action.lower().strip()

    if action == "search":
        if not query:
            return EffectorResult(success=False, message="search requires: query")
        from metabolon.organelles.chromatin import search

        results = search(
            query,
            category=category,
            source_enzyme=source,
            limit=limit,
            mode=mode,
            chromatin=chromatin,
        )
        return HistoneResult(results=_format_search_results(results))

    if action == "mark":
        if not content:
            return EffectorResult(success=False, message="mark requires: content")
        from metabolon.organelles.chromatin import add

        saved = add(content, category=category or "gotcha", confidence=confidence)
        return EffectorResult(success=True, message=f"Memory added: {saved['file']}", data=saved)

    if action == "stats":
        from metabolon.organelles.chromatin import stats

        data = stats()
        return HistoneResult(
            results=(
                f"Marks: {data['count']} files\n"
                f"Size: {data['size_kb']}KB\n"
                f"Path: {data['path']}"
            )
        )

    if action == "status":
        from metabolon.organelles.chromatin import status

        return Vital(status="ok", message=status())

    return EffectorResult(
        success=False,
        message="Unknown action. Valid: search, mark, stats, status",
    )
