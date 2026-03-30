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


def _preflight() -> PolarizationPreflightResult:
    """Run polarization-gather preflight checks."""
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


def _guard(guard_action: str) -> EffectorResult:
    """Toggle the polarization stop guard on or off."""
    guard_action = guard_action.lower().strip()
    if guard_action not in ("on", "off"):
        return EffectorResult(
            success=False,
            message=f"Invalid guard_action '{guard_action}'. Use 'on' or 'off'.",
        )

    cli = _find_cli()
    if not cli:
        return EffectorResult(
            success=False,
            message=f"'{_CLI}' not found on PATH. Is it installed?",
        )

    try:
        result = subprocess.run(
            [cli, "guard", guard_action],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            state = "activated" if guard_action == "on" else "deactivated"
            return EffectorResult(
                success=True,
                message=f"Polarization guard {state}.",
                data={"action": guard_action, "guard_state": guard_action},
            )
        else:
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()
            return EffectorResult(
                success=False,
                message=f"guard {guard_action} failed (exit {result.returncode}): {stderr or stdout}",
                data={"action": guard_action, "stderr": stderr},
            )
    except subprocess.TimeoutExpired:
        return EffectorResult(
            success=False,
            message=f"guard {guard_action} timed out.",
        )


@tool(
    name="polarization",
    description="Overnight teams. Actions: preflight|guard",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def polarization(action: str, guard_action: str = "") -> PolarizationPreflightResult | EffectorResult:
    """Polarization pre-flight checks and guard control.

    Args:
        action: 'preflight' for consumption/budget/guard check, 'guard' to toggle guard.
        guard_action: When action='guard', 'on' to activate or 'off' to deactivate.
    """
    if action == "preflight":
        return _preflight()
    elif action == "guard":
        return _guard(guard_action)
    else:
        return EffectorResult(
            success=False,
            message=f"Unknown action '{action}'. Use 'preflight' or 'guard'.",
        )
