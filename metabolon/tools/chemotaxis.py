"""chemotaxis — peer pattern scanning via parallel web research.

Tools:
  chemotaxis_scan — scan a domain for transferable peer patterns
"""

from __future__ import annotations

import json

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion


class ChemotaxisScanResult(Secretion):
    """Peer pattern scan result — extracted transferable patterns."""

    domain: str
    patterns: list[dict]
    raw: str


@tool(
    name="chemotaxis_scan",
    description="Scan a domain for transferable peer patterns. Returns structured findings.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def chemotaxis_scan(
    domain: str,
    targets: str = "",
    depth: str = "ask",
) -> ChemotaxisScanResult:
    """Peer pattern scanning — parallel web research across a domain.

    Args:
        domain: Domain to scan (e.g. "multi-agent frameworks", "consulting AI delivery").
        targets: Pipe-separated scan targets (e.g. "AutoGen|LangGraph|CrewAI"). Optional.
        depth: Search depth — "search" (quick, ~$0.006), "ask" (thorough, ~$0.01).
    """
    from metabolon.organelles.chemotaxis_engine import ask as _ask
    from metabolon.organelles.chemotaxis_engine import recall as _search

    _search_fn = _search if depth == "search" else _ask

    target_list = [t.strip() for t in targets.split("|") if t.strip()]
    target_clause = f" Focus on: {', '.join(target_list)}." if target_list else ""

    query = (
        f"What are the most transferable patterns, techniques, and practices in {domain}?"
        f"{target_clause} "
        "For each: name the pattern, what problem it solves, how it works, evidence, "
        "and how to adopt it. Structure as a list of discrete patterns."
    )

    raw = _search_fn(query)

    # Parse out discrete patterns from the raw result (heuristic extraction)
    patterns: list[dict] = []
    current: dict = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            if current:
                patterns.append(current)
                current = {}
            continue
        if line.startswith(("- ", "* ", "**", "###", "##")):
            if current:
                patterns.append(current)
            name = line.lstrip("-*# ").split(":")[0].strip().strip("*")
            current = {"name": name, "detail": line}
        elif current:
            current["detail"] = current.get("detail", "") + " " + line

    if current:
        patterns.append(current)

    return ChemotaxisScanResult(domain=domain, patterns=patterns[:20], raw=raw)
