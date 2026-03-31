from __future__ import annotations

"""noesis — web-grounded search via Perplexity API.

Tools:
  noesis — action: search|ask|research

Resources:
  vivesca://noesis/search-log — last 10 search queries
"""


import subprocess

from metabolon.organelles.effector import run_cli  # noqa: E402

from fastmcp.tools import tool  # noqa: E402
from fastmcp.resources import resource  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

BINARY = "~/.cargo/bin/noesis"

# Deep research can take minutes; override the default timeout.
_RESEARCH_TIMEOUT = 300


@tool(
    name="noesis",
    description="AI search. Actions: search|ask|research",
    annotations=ToolAnnotations(readOnlyHint=False),
)
def noesis(action: str, query: str = "") -> str:
    """AI-powered web search via Perplexity API.

    Args:
        action: One of search, ask, research.
            search   — quick search via sonar (~$0.006).
            ask      — thorough survey via sonar-pro (~$0.01).
            research — deep research via sonar-deep-research (~$0.40, EXPENSIVE).
        query: The search query or question.
    """
    if action == "search":
        return run_cli(BINARY, ["search", query])
    elif action == "ask":
        return run_cli(BINARY, ["ask", query])
    elif action == "research":
        return run_cli(BINARY, ["research", "--save", query], timeout=_RESEARCH_TIMEOUT)
    else:
        return f"Unknown action '{action}'. Use one of: search, ask, research."


@resource("vivesca://noesis/search-log")
def noesis_search_log() -> str:
    """Returns the last 10 noesis queries from the usage log."""
    import os

    path = os.path.expanduser(BINARY)
    try:
        result = subprocess.run(
            [path, "log"],
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
        lines = result.stdout.strip().splitlines()
        return "\n".join(lines[-10:]) if len(lines) > 10 else result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_msg = (e.stderr or "").strip() or str(e)
        raise ValueError(f"noesis log error: {error_msg}")
