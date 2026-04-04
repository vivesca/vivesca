
"""noesis — Perplexity-powered AI search tool.

Tools:
  noesis        — search / ask / research via the noesis CLI binary
  noesis_search_log — resource returning recent search history
"""

import os
import subprocess

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.organelles.effector import run_cli

BINARY = "~/.cargo/bin/noesis"
_RESEARCH_TIMEOUT = 300

_VALID_ACTIONS = ("search", "ask", "research")


@tool(
    name="noesis",
    description="Perplexity-powered AI search. Actions: search, ask, research.",
    annotations=ToolAnnotations(readOnlyHint=True),
)
def noesis(action: str, query: str = "") -> str:
    """Run a noesis CLI action.

    Args:
        action: One of 'search', 'ask', or 'research'.
        query:  The search query or question.
    """
    if action not in _VALID_ACTIONS:
        return f"Unknown action '{action}'. Choose from: {', '.join(_VALID_ACTIONS)}"

    if action == "research":
        return run_cli(BINARY, ["research", "--save", query], timeout=_RESEARCH_TIMEOUT)

    return run_cli(BINARY, [action, query])


def noesis_search_log() -> str:
    """Return recent noesis search log entries (last 10 lines)."""
    try:
        result = subprocess.run(
            [os.path.expanduser(BINARY), "log"],
            check=True,
            timeout=10,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        error_msg = (e.stderr or "").strip() or str(e)
        raise ValueError(f"noesis log error: {error_msg}") from e

    output = result.stdout.strip()
    if not output:
        return ""

    lines = output.split("\n")
    if len(lines) > 10:
        lines = lines[-10:]

    return "\n".join(lines)
