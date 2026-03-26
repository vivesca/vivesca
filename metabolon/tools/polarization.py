"""polarization — North star agent dispatch pre-flight and guard control.

Wraps the deterministic polarization-gather CLI:
  preflight  — consumption check, budget, guard status, north stars, manifest
  guard      — activate / deactivate the stop guard

Orchestration (agent dispatch, flywheel, systole management) stays in the skill.
These tools give the skill grounded facts and guard control before dispatch.
"""

from __future__ import annotations

import json
import shutil
import subprocess

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Secretion

_CLI = "polarization-gather"


def _find_cli() -> str | None:
    return shutil.which(_CLI)


class PolarizationPreflightResult(Secretion):
    """Pre-flight check results for polarization dispatch."""

    raw: str
    data: dict
    summary: str


@tool(
    name="polarization_preflight",
    description="Consumption check, budget, guard status, north stars before dispatch.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def polarization_preflight() -> PolarizationPreflightResult:
    """Run polarization-gather preflight checks.

    Checks: review queue consumption, budget, guard status, manifest,
    north stars, TODO agent:claude items, NOW.md.

    Returns structured JSON data from the CLI plus a human-readable summary.
    Use this before dispatching any agent teams to verify backlog state.
    """
    cli = _find_cli()
    if not cli:
        return PolarizationPreflightResult(
            raw="",
            data={"error": f"'{_CLI}' not found on PATH"},
            summary=f"ERROR: {_CLI} not found on PATH. Is it installed?",
        )

    try:
        result = subprocess.run(
            [cli, "preflight", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        raw_output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            return PolarizationPreflightResult(
                raw=raw_output,
                data={"error": stderr or f"exit {result.returncode}"},
                summary=f"preflight failed (exit {result.returncode}): {stderr or raw_output}",
            )

        # Parse JSON if available
        data: dict = {}
        try:
            data = json.loads(raw_output)
        except (json.JSONDecodeError, ValueError):
            # Fall back to plain text
            data = {"raw_text": raw_output}

        # Build summary
        if "raw_text" in data:
            summary = raw_output
        else:
            lines = ["Polarization pre-flight:"]
            for key, value in data.items():
                lines.append(f"  {key}: {value}")
            summary = "\n".join(lines)

        return PolarizationPreflightResult(
            raw=raw_output,
            data=data,
            summary=summary,
        )

    except subprocess.TimeoutExpired:
        return PolarizationPreflightResult(
            raw="",
            data={"error": "timeout"},
            summary="preflight timed out after 30s.",
        )


@tool(
    name="polarization_guard",
    description="Activate or deactivate the polarization stop guard.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def polarization_guard(action: str) -> EffectorResult:
    """Toggle the polarization stop guard on or off.

    The guard is a Stop hook that prevents the model from stopping while
    budget is green. Activate at session start; deactivate at session end
    (done automatically in Wrap, or manually here).

    Args:
        action: 'on' to activate the guard, 'off' to deactivate.
    """
    action = action.lower().strip()
    if action not in ("on", "off"):
        return EffectorResult(
            success=False,
            message=f"Invalid action '{action}'. Use 'on' or 'off'.",
        )

    cli = _find_cli()
    if not cli:
        return EffectorResult(
            success=False,
            message=f"'{_CLI}' not found on PATH. Is it installed?",
        )

    try:
        result = subprocess.run(
            [cli, "guard", action],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            state = "activated" if action == "on" else "deactivated"
            return EffectorResult(
                success=True,
                message=f"Polarization guard {state}.",
                data={"action": action, "guard_state": action},
            )
        else:
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()
            return EffectorResult(
                success=False,
                message=f"guard {action} failed (exit {result.returncode}): {stderr or stdout}",
                data={"action": action, "stderr": stderr},
            )
    except subprocess.TimeoutExpired:
        return EffectorResult(
            success=False,
            message=f"guard {action} timed out.",
        )
