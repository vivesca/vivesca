"""ecphory — deterministic memory retrieval across stores.

Exposes the two searchable stores that ecphory routes between:
  ecphory_engram  — search session transcripts (episodic memory)
  ecphory_chromatin — search oghma semantic memory store
  ecphory_logs — search structured log files (meals, symptoms, experiments)

The skill layer (SKILL.md) handles cue classification and fan-out routing.
These tools are the deterministic search primitives it dispatches to.
"""

from __future__ import annotations

import re
from typing import Any

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon import locus
from metabolon.organelles import chromatin as _chromatin
from metabolon.organelles import engram as _engram


@tool(
    name="ecphory_engram",
    description="Search session transcripts (episodic memory). Use for 'we talked about X'.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def ecphory_engram(
    query: str,
    days: int = 7,
    deep: bool = True,
    role: str = "",
) -> str:
    """Search chat history (Claude + Codex + OpenCode) for a pattern.

    Args:
        query: Search term or regex.
        days: How many days back to search (default 7).
        deep: True = search full transcripts; False = prompts only.
        role: Filter by speaker — 'user', 'assistant', or '' for all.
    """
    matches = _engram.search(
        query,
        days=days,
        deep=deep,
        role=role or None,
    )
    if not matches:
        return f"No matches for '{query}' in last {days} days."

    lines = [f"{len(matches)} match(es) for '{query}':"]
    for m in matches:
        lines.append(f"  [{m.date} {m.time_str}] [{m.role}] {m.snippet}")
    return "\n".join(lines)


@tool(
    name="ecphory_chromatin",
    description="Search oghma semantic memory store. Use for saved facts and decisions.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def ecphory_chromatin(
    query: str,
    category: str = "",
    limit: int = 10,
    mode: str = "hybrid",
    accessibility: str = "open",
) -> str:
    """Search the chromatin (oghma) semantic memory store.

    Args:
        query: Search query (natural language or keyword).
        category: Filter by memory category (leave blank for all).
        limit: Maximum results to return (default 10).
        mode: Search mode — 'hybrid', 'semantic', or 'keyword'.
        accessibility: 'open' (active), 'closed' (archived), or 'all'.
    """
    results = _chromatin.recall(
        query,
        category=category,
        limit=limit,
        mode=mode,
        chromatin=accessibility,
    )
    if not results:
        return f"No memories found for '{query}'."

    lines = [f"{len(results)} memory result(s) for '{query}':"]
    for r in results:
        title = r.get("title") or r.get("content", "")[:60]
        cat = r.get("category", "")
        source = r.get("source_tool", "")
        score = r.get("score", "")
        meta = " | ".join(
            filter(None, [cat, source, f"score={score:.2f}" if isinstance(score, float) else ""])
        )
        lines.append(f"  [{meta}] {title}")
        # Include a content snippet if present and different from title
        content = r.get("content", "")
        if content and content[:60] != title:
            lines.append(f"    {content[:120].strip()}")
    return "\n".join(lines)


@tool(
    name="ecphory_logs",
    description="Search log files (meals, symptoms, experiments). Use for 'we logged X'.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def ecphory_logs(
    query: str,
    days: int = 30,
) -> str:
    """Search structured log files for a pattern.

    Args:
        query: Search term or regex (case-insensitive).
        days: Not used for filtering (logs have no date index); reserved for
              future windowing. Passed through for API consistency.
    """
    pattern = re.compile(query, re.IGNORECASE)

    # Collect (label, path) pairs for all target files
    targets: list[tuple[str, Any]] = [
        ("meal_plan", locus.meal_plan),
        ("symptom_log", locus.symptom_log),
    ]
    if locus.experiments.is_dir():
        for exp_path in sorted(locus.experiments.glob("assay-*.md")):
            targets.append((f"experiments/{exp_path.name}", exp_path))

    matches: list[str] = []
    for label, file_path in targets:
        if not file_path.exists():
            continue
        try:
            for lineno, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line):
                    matches.append(f"  [{label}:{lineno}] {line.strip()}")
        except OSError:
            continue

    if not matches:
        return f"No matches for '{query}' in log files."

    lines = [f"{len(matches)} match(es) for '{query}' in log files:"]
    lines.extend(matches)
    return "\n".join(lines)
