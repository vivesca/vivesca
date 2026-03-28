"""differentiation — gym session support tools.

Deterministic actions for the differentiation gym-coaching skill:
- Read latest gym log (find + read most recent file)
- Get exercise readiness from Oura (via chemoreceptor organelle)
- Write completed gym session log
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.organelles import chemoreceptor

HEALTH_DIR = Path.home() / "epigenome" / "chromatin" / "Health"


@tool(
    name="differentiation_latest_log",
    description="Read the most recent gym log.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def differentiation_latest_log() -> str:
    """Return the content of the most recent Gym Log file."""
    logs = sorted(HEALTH_DIR.glob("Gym Log - *.md"))
    if not logs:
        return "No gym logs found."
    latest = logs[-1]
    return f"File: {latest.name}\n\n{latest.read_text()}"


@tool(
    name="differentiation_readiness",
    description="Get today's Oura readiness score and threshold guidance.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def differentiation_readiness() -> str:
    """Return readiness score with gym intensity recommendation.

    Thresholds: <70 light only, 70-75 moderate, >75 full session.
    """
    try:
        data = chemoreceptor.readiness()
    except Exception as exc:
        return f"Error fetching readiness: {exc}"

    score = data.get("score")
    if score is None:
        return "No readiness data available for today."

    if score < 70:
        guidance = "Light only — protect recovery. Skip heavy compounds."
    elif score < 75:
        guidance = "Moderate session OK. Reduce volume or weight by ~10%."
    else:
        guidance = "Full session. Follow working weights from last log."

    contributors = data.get("contributors", {})
    contribs_str = ", ".join(f"{k}: {v}" for k, v in contributors.items()) if contributors else "—"

    return (
        f"Readiness: {score}\n"
        f"Guidance: {guidance}\n"
        f"Contributors: {contribs_str}\n"
        f"Temperature deviation: {data.get('temperature_deviation', '—')}"
    )


@tool(
    name="differentiation_write_log",
    description="Write completed gym session log.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def differentiation_write_log(
    session_date: str,
    content: str,
) -> str:
    """Write a gym session log file.

    Args:
        session_date: ISO date string (YYYY-MM-DD) for the session.
        content: Full markdown content of the gym log (including frontmatter).
    """
    try:
        date.fromisoformat(session_date)
    except ValueError:
        return f"Invalid date format: {session_date!r}. Use YYYY-MM-DD."

    target = HEALTH_DIR / f"Gym Log - {session_date}.md"
    target.write_text(content)
    return f"Gym log written to {target}"
