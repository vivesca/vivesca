"""lysis — Firecrawl URL scraper, fallback for bot-protected pages.

Extends navigator with Firecrawl-backed scraping for sites that block
headless browsers. Returns clean markdown.

Tools:
  lysis_scrape  — scrape a URL through Firecrawl
  lysis_search  — web search + scrape via Firecrawl
"""


from metabolon.organelles.effector import run_cli  # noqa: E402

from fastmcp.tools import tool  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

BINARY = "/Users/terry/germline/effectors/lysis"


@tool(
    name="lysis_scrape",
    description="Scrape a URL via Firecrawl, bypassing bot protection. Returns markdown.",
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, destructiveHint=False),
)
def lysis_scrape(url: str) -> str:
    """Scrape a URL through Firecrawl.

    Args:
        url: The URL to scrape.
    """
    return run_cli(BINARY, [url], timeout=60)


@tool(
    name="lysis_search",
    description="Web search + scrape via Firecrawl. Returns markdown from top results.",
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True, destructiveHint=False),
)
def lysis_search(query: str) -> str:
    """Web search and scrape results via Firecrawl.

    Args:
        query: The search query.
    """
    return run_cli(BINARY, ["search", query], timeout=60)
