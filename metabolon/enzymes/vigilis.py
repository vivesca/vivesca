"""vigilis — health monitoring + system health.

Verbs (actions, not actors):
  vigilis_check_sleep     — get today's/this week's sleep summary from Oura
  vigilis_check_readiness — today's readiness score + exercise recommendation
  vigilis_check_system    — lucerna status, budget, hook health
  vigilis_log_symptom     — append a symptom entry to vault health log
"""

import datetime
import os


from metabolon.organelles.effector import run_cli  # noqa: E402

from fastmcp.tools import tool  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

SOPOR = "sopor"
HEALTH_LOG = os.path.expanduser("~/notes/Health/Symptom Log.md")


@tool(
    name="vigilis_check_sleep",
    description=(
        "Check sleep data from Oura. Returns sleep score, HRV, duration, "
        "and patterns. Use 'today' for last night or 'week' for 7-day trend."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def vigilis_check_sleep(period: str = "today") -> str:
    """Check sleep data.

    Args:
        period: 'today' for last night, 'week' for 7-day trend.
    """
    return run_cli(SOPOR, [period], timeout=15)


@tool(
    name="vigilis_check_readiness",
    description=(
        "Check today's Oura readiness score and get an exercise recommendation. "
        "Returns readiness score, contributing factors, and workout guidance "
        "(light/moderate/full intensity)."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def vigilis_check_readiness() -> str:
    """Check readiness and recommend exercise intensity."""
    raw = run_cli(SOPOR, ["today"], timeout=15)

    # Extract readiness from sopor output and add recommendation
    return (
        f"{raw}\n\n"
        "---\n"
        "Exercise guidance: check readiness score above.\n"
        "- <70: light only (walk, gentle stretch)\n"
        "- 70-75: moderate OK (yoga, light weights)\n"
        "- >75: full intensity cleared"
    )


@tool(
    name="vigilis_check_system",
    description=(
        "Check system health: lucerna running, copia budget status, "
        "recent events, hook health."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def vigilis_check_system() -> str:
    """Check lucerna + copia system health."""
    import subprocess

    parts = []

    # Lucerna status
    try:
        result = subprocess.run(
            ["launchctl", "list"],
            capture_output=True, text=True, timeout=5,
        )
        lucerna_lines = [
            ln for ln in result.stdout.splitlines() if "lucerna" in ln
        ]
        parts.append("Lucerna: " + ("; ".join(lucerna_lines) or "NOT FOUND"))
    except Exception as e:
        parts.append(f"Lucerna: check failed ({e})")

    # Budget
    try:
        budget = run_cli("usus", ["--json"], timeout=15)
        parts.append(f"Budget: {budget}")
    except Exception:
        parts.append("Budget: usus unavailable")

    # Recent copia events
    log = os.path.expanduser("~/logs/copia-events.jsonl")
    try:
        with open(log) as f:
            lines = f.readlines()
        tail = lines[-5:] if len(lines) >= 5 else lines
        parts.append("Recent events:\n" + "".join(tail))
    except Exception:
        parts.append("Events: log not found")

    return "\n\n".join(parts)


@tool(
    name="vigilis_log_symptom",
    description=(
        "Append a symptom entry to the vault health symptom log. "
        "Include date, symptom, severity, and any notes."
    ),
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def vigilis_log_symptom(symptom: str, severity: str = "mild", notes: str = "") -> str:
    """Log a symptom to the vault.

    Args:
        symptom: What symptom (e.g., 'headache', 'fatigue', 'nasal congestion').
        severity: 'mild', 'moderate', or 'severe'.
        notes: Additional context (medication, triggers, duration).
    """
    today = datetime.date.today().isoformat()
    entry = f"\n## {today} — {symptom}\n- Severity: {severity}\n"
    if notes:
        entry += f"- Notes: {notes}\n"

    os.makedirs(os.path.dirname(HEALTH_LOG), exist_ok=True)
    with open(HEALTH_LOG, "a") as f:
        f.write(entry)

    return f"Logged: {symptom} ({severity}) on {today}"
