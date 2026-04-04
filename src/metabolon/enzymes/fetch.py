from __future__ import annotations

"""fetch — URL content extraction via pinocytosis effector.

Parallel fast tier (defuddle + jina + microlink) → firecrawl → agent-browser.
"""

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.organelles.effector import run_cli


@tool(
    name="fetch",
    description="Fetch URL content. Parallel fast tier (defuddle + jina + microlink) → firecrawl → agent-browser.",
    annotations=ToolAnnotations(readOnlyHint=True),
)
def fetch(url: str) -> str:
    """Extract text content from a URL.

    Args:
        url: The URL to fetch.
    """
    return run_cli("~/germline/effectors/pinocytosis", [url], timeout=60)
