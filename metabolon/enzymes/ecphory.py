from __future__ import annotations

"""ecphory — deterministic memory retrieval across stores.

Actions: engram|chromatin|logs
"""


import re

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon import locus
from metabolon.morphology import Secretion


class EcphoryResult(Secretion):
    results: str


_ACTIONS = (
    "engram — search session transcripts (episodic memory). Requires: query. Optional: days, deep, role. "
    "chromatin — search oghma semantic memory store. Requires: query. Optional: category, limit, mode, accessibility. "
    "logs — search structured log files. Requires: query. Optional: days."
)


@tool(
    name="ecphory",
    description=f"Memory retrieval. Actions: {_ACTIONS}",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def ecphory(
    action: str,
    query: str = "",
    # engram params
    days: int = 7,
    deep: bool = True,
    role: str = "",
    # chromatin params
    category: str = "",
    limit: int = 10,
    mode: str = "hybrid",
    accessibility: str = "open",
) -> EcphoryResult:
    """Unified memory retrieval tool."""
    action = action.lower().strip()

    if action == "engram":
        if not query:
            return EcphoryResult(results="engram requires: query")
        from metabolon.organelles.engram import TraceFragment
        from metabolon.organelles.engram import search as _engram_search
        fragments: list[TraceFragment] = _engram_search(query, days=days, deep=deep, role=role or None)
        if not fragments:
            return EcphoryResult(results=f"No matches for '{query}' in last {days} days.")
        lines = [f"{len(fragments)} match(es) for '{query}':"]
        for m in fragments:
            lines.append(f"  [{m.date} {m.time_str}] [{m.role}] {m.snippet}")
        return EcphoryResult(results="\n".join(lines))

    elif action == "chromatin":
        if not query:
            return EcphoryResult(results="chromatin requires: query")
        from metabolon.organelles.chromatin import search as _chromatin_search
        results = _chromatin_search(
            query,
            category=category,
            limit=limit,
            mode=mode,
            chromatin=accessibility,
        )
        if not results:
            return EcphoryResult(results=f"No memories found for '{query}'.")
        lines = [f"{len(results)} memory result(s) for '{query}':"]
        for r in results:
            lines.append(f"  [{r['name']}] {r['file']}")
            snippet = r.get("content", "")[:120].strip()
            if snippet:
                lines.append(f"    {snippet}")
        return EcphoryResult(results="\n".join(lines))

    elif action == "logs":
        if not query:
            return EcphoryResult(results="logs requires: query")
        pattern = re.compile(query, re.IGNORECASE)
        targets = [("meal_plan", locus.meal_plan), ("symptom_log", locus.symptom_log)]
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
            return EcphoryResult(results=f"No matches for '{query}' in log files.")
        lines = [f"{len(matches)} match(es) for '{query}' in log files:"]
        lines.extend(matches)
        return EcphoryResult(results="\n".join(lines))

    else:
        return EcphoryResult(results=f"Unknown action '{action}'. Valid: engram, chromatin, logs")
