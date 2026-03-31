from __future__ import annotations

"""differentiation — gym session support tool.

Consolidated tool for the differentiation gym-coaching skill:
- latest_log: read most recent gym log file
- readiness: get Oura readiness score with intensity guidance
- write_log: write a completed gym session log
"""


from datetime import date
from pathlib import Path

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.organelles import chemoreceptor

HEALTH_DIR = Path.home() / "epigenome" / "chromatin" / "Health"


@tool(
    name="differentiation",
    description="Gym coaching. Actions: latest_log|readiness|write_log",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def differentiation(
    action: str,
    session_date: str = "",
    content: str = "",
) -> str:
    """Gym coaching tool with action dispatch.

    Args:
        action: One of latest_log, readiness, write_log.
        session_date: ISO date (YYYY-MM-DD). Required for write_log.
        content: Full markdown content of the gym log. Required for write_log.
    """
    if action == "latest_log":
        logs = sorted(HEALTH_DIR.glob("Gym Log - *.md"))
        if not logs:
            return "No gym logs found."
        latest = logs[-1]
        return f"File: {latest.name}\n\n{latest.read_text()}"

    elif action == "readiness":
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

    elif action == "write_log":
        try:
            date.fromisoformat(session_date)
        except ValueError:
            return f"Invalid date format: {session_date!r}. Use YYYY-MM-DD."

        target = HEALTH_DIR / f"Gym Log - {session_date}.md"
        if target.exists():
            tmp = target.with_suffix(".md.tmp")
            tmp.write_text(content)
            tmp.replace(target)
        else:
            target.write_text(content)
        return f"Gym log written to {target}"

    else:
        return f"Unknown action: {action!r}. Use latest_log, readiness, or write_log."
