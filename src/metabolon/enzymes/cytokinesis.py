"""cytokinesis — session consolidation MCP tool.

Actions: gather|verify|flush|wrap

gather: deterministic pre-wrap checks (repos, skills, memory, tonus, gates)
verify: re-check all gates, report DONE/PENDING
flush: commit dirty repos
wrap: gather + verify, refuses to return success until all gates pass
"""

import json
import subprocess
from pathlib import Path
from typing import Any

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations
from pydantic import Field

from metabolon.morphology import EffectorResult, Secretion

BINARY = str(Path.home() / "germline" / "effectors" / "cytokinesis")


class CytoResult(Secretion):
    """Structured output from cytokinesis."""

    output: str
    data: dict[str, Any] = Field(default_factory=dict)
    gates: dict[str, str] = Field(default_factory=dict)
    all_gates_passed: bool = False


def _run_cli(subcommand: str, extra_args: list[str] | None = None) -> tuple[int, str]:
    """Run cytokinesis CLI and return (exit_code, stdout)."""
    cmd = [BINARY, subcommand] + (extra_args or [])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        return result.returncode, result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return 1, str(exc)


@tool(
    name="cytokinesis",
    description="gather|verify|flush|wrap — session consolidation with enforced gates",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def cytokinesis(
    action: str = "gather",
) -> CytoResult | EffectorResult:
    """Session consolidation tool.

    Parameters
    ----------
    action : str
        gather: run pre-wrap checks, return gates status
        verify: re-check gates deterministically
        flush: commit dirty repos
        wrap: gather + verify, FAILS if any gate is PENDING
    """
    action = action.lower().strip()

    if action == "gather":
        exit_code, stdout = _run_cli("gather")
        if exit_code != 0:
            return EffectorResult(success=False, message=f"gather failed: {stdout[:500]}")
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return EffectorResult(
                success=False, message=f"gather returned invalid JSON: {stdout[:200]}"
            )
        gates = data.get("gates", {})
        pending = [gate_name for gate_name, status in gates.items() if "PENDING" in status]
        return CytoResult(
            output=f"{len(gates)} gates, {len(pending)} pending",
            data=data,
            gates=gates,
            all_gates_passed=len(pending) == 0,
        )

    if action == "verify":
        exit_code, stdout = _run_cli("verify")
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError:
            return EffectorResult(
                success=False, message=f"verify returned invalid JSON: {stdout[:200]}"
            )
        gates = data.get("gates", {})
        all_passed = data.get("all_passed", False)
        pending = [gate_name for gate_name, status in gates.items() if "PENDING" in status]
        if all_passed:
            return CytoResult(
                output="All gates passed. Session properly closed.",
                gates=gates,
                all_gates_passed=True,
            )
        return CytoResult(
            output=f"BLOCKED: {len(pending)} gates still pending: {', '.join(pending)}",
            gates=gates,
            all_gates_passed=False,
        )

    if action == "flush":
        exit_code, stdout = _run_cli("flush")
        return CytoResult(output=stdout.strip() or "flushed", data={"exit_code": exit_code})

    if action == "wrap":
        # Gather first
        exit_code, stdout = _run_cli("gather", ["--fast"])
        if exit_code != 0:
            return EffectorResult(success=False, message=f"gather failed: {stdout[:500]}")
        try:
            gather_data = json.loads(stdout)
        except json.JSONDecodeError:
            return EffectorResult(success=False, message="gather returned invalid JSON")

        # Then verify
        exit_code, stdout = _run_cli("verify")
        try:
            verify_data = json.loads(stdout)
        except json.JSONDecodeError:
            return EffectorResult(success=False, message="verify returned invalid JSON")

        gates = verify_data.get("gates", {})
        all_passed = verify_data.get("all_passed", False)
        pending = [gate_name for gate_name, status in gates.items() if "PENDING" in status]

        if all_passed:
            return CytoResult(
                output="Session wrapped. All gates passed.",
                data=gather_data,
                gates=gates,
                all_gates_passed=True,
            )
        return CytoResult(
            output=f"CANNOT WRAP: {len(pending)} gates pending: {', '.join(pending)}. Complete these before wrapping.",
            data=gather_data,
            gates=gates,
            all_gates_passed=False,
        )

    return EffectorResult(
        success=False,
        message="Unknown action. Valid: gather, verify, flush, wrap",
    )
