"""lysin — fetch real biology for a term before naming.

Tools:
  lysin -- look up definition, mechanism, and source URL from UniProt/Reactome/Wikipedia
"""

from fastmcp.tools.function_tool import tool


@tool()
async def lysin(term: str) -> str:
    """Look up real cell biology for a term. Use before naming any component to verify the analogy is grounded.

    Returns definition, mechanism, and source URL from UniProt, Reactome, or Wikipedia.
    """
    from metabolon.lysin.fetch import fetch_summary

    try:
        article = fetch_summary(term)
    except LookupError as exc:
        return str(exc)

    parts = [
        f"# {article.title}",
        f"Source: {', '.join(article.sources)}",
        "",
        f"**Definition:** {article.definition}",
        "",
        f"**Mechanism:** {article.mechanism}",
        "",
        f"**URL:** {article.url}",
    ]
    return "\n".join(parts)
