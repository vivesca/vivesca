"""lysozyme — Firecrawl URL scraper, fallback for bot-protected pages.

Extends chemotaxis with Firecrawl-backed scraping for sites that block
headless browsers. Returns clean markdown.
"""

from pathlib import Path

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.organelles.effector import run_cli

BINARY = str(Path.home() / "germline/effectors/lysozyme")


@tool(
    name="lysozyme",
    description="Web content extraction. Actions: scrape|search",
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, destructiveHint=False),
)
def lysozyme(action: str, url: str = "", query: str = "") -> str:
    """Scrape or search via Firecrawl.

    Args:
        action: "scrape" to scrape a URL, "search" for web search + scrape.
        url: The URL to scrape (action="scrape").
        query: The search query (action="search").
    """
    if action == "scrape":
        return run_cli(BINARY, [url], timeout=60)
    elif action == "search":
        return run_cli(BINARY, ["search", query], timeout=60)
    else:
        return f"Error: unknown action '{action}'. Use 'scrape' or 'search'."
