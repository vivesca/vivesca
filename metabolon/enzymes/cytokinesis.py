"""cytokinesis — session consolidation pre-checks.

Wraps the cytokinesis CLI gather command as an MCP tool.
Returns structured JSON for skill consumption.
"""

from __future__ import annotations

import json
import subprocess

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion


class GatherResult(Secretion):
    """Structured output from cytokinesis gather."""

    status: str  # "ok", "warning", "error"
    message: str
    repos: dict = {}
    skills: dict = {}
    memory: dict = {}
    tonus: dict = {}
    rfts: list = []
    deps: list = []
    peira: str | None = None
    reflect: list = []
    methylation: list = []


@tool(
    name="cytokinesis_gather",
    description=(
        "Deterministic pre-wrap checks: dirty repos, "
        "skill gaps, memory budget, tonus age, stale marks."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def cytokinesis_gather() -> GatherResult:
    """Run all deterministic session-end checks via cytokinesis CLI."""
    try:
        result = subprocess.run(
            ["cytokinesis", "gather", "--syntactic"],
            capture_output=True,
            text=True,
            timeout=90,
        )
        if result.returncode != 0:
            return GatherResult(
                status="error",
                message=f"cytokinesis gather failed (exit {result.returncode})",
            )
        data = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        return GatherResult(
            status="error",
            message=f"cytokinesis gather failed: {e}",
        )

    # Derive status from findings
    warnings = []
    mem = data.get("memory", {})
    if mem.get("lines", 0) > mem.get("limit", 150):
        warnings.append(f"MEMORY.md {mem['lines']}/{mem['limit']}")
    now = data.get("now", {})
    if now.get("age_label") in ("stale", "very stale"):
        warnings.append("tonus stale")
    rfts = data.get("rfts", [])
    if rfts:
        warnings.append(f"{len(rfts)} stale marks")
    dirty = [k for k, v in data.get("repos", {}).items() if v.get("clean") is False]
    if dirty:
        warnings.append(f"dirty: {', '.join(dirty)}")

    return GatherResult(
        status="warning" if warnings else "ok",
        message="; ".join(warnings) if warnings else "clean",
        repos=data.get("repos", {}),
        skills=data.get("skills", {}),
        memory=mem,
        tonus=now,
        rfts=rfts,
        deps=data.get("deps", []),
        peira=data.get("peira"),
        reflect=data.get("reflect", []),
        methylation=data.get("methylation", []),
    )
