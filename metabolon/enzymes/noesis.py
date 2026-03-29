"""noesis — web-grounded search via Perplexity API.

Tools:
  noesis_search   — quick search (~$0.006)
  noesis_ask      — thorough survey (~$0.01)
  noesis_research — deep research (~$0.40, EXPENSIVE)

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
    name="noesis_search",
    description=(
        "Quick web search via Perplexity sonar model (~$0.006 per query). "
        "Returns a concise cited synthesis. Good for factual lookups."
    ),
    annotations=ToolAnnotations(readOnlyHint=False),
)
def noesis_search(query: str) -> str:
    """Quick web search.

    Args:
        query: The search query.
    """
    return run_cli(BINARY, ["search", query])


@tool(
    name="noesis_ask",
    description=(
        "Thorough web search via Perplexity sonar-pro (~$0.01 per query). "
        "Returns a structured survey with citations. Use for nuanced questions."
    ),
    annotations=ToolAnnotations(readOnlyHint=False),
)
def noesis_ask(query: str) -> str:
    """Thorough web search.

    Args:
        query: The question to research.
    """
    return run_cli(BINARY, ["ask", query])


@tool(
    name="noesis_research",
    description=(
        "Deep research via Perplexity sonar-deep-research (~$0.40 per query). "
        "EXPENSIVE — use only when the depth justifies the cost. "
        "Output is saved to ~/docs/solutions/research/."
    ),
    annotations=ToolAnnotations(readOnlyHint=False),
)
def noesis_research(query: str) -> str:
    """Deep research (expensive).

    Args:
        query: The research question requiring deep investigation.
    """
    return run_cli(BINARY, ["research", "--save", query], timeout=_RESEARCH_TIMEOUT)


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
        error_msg = e.stderr.strip() or str(e)
        raise ValueError(f"noesis log error: {error_msg}")
