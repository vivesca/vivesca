"""gather — deterministic context gathering for skills.

Exposes the gather scripts as MCP tools so skills (and the LLM)
can call the deterministic stage independently.

Tools:
  pinocytosis_photoreception — morning brief context (weather, sleep, calendar, health)
  pinocytosis_ultradian   — situational snapshot (calendar, TODO, NOW, alerts)
  pinocytosis_interphase  — evening routine context (inbox, WhatsApp, calendar, TODO)
  pinocytosis_weekly      — weekly review context (next week calendar, TODO, Oura, garden)
  pinocytosis_polarization — overnight flywheel preflight (consumption, guard, north stars)
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.cytosol import invoke_organelle
from metabolon.morphology import Secretion


class PinocytosisResult(Secretion):
    """Deterministic context output from a gather script."""

    output: str


@tool(
    name="pinocytosis_photoreception",
    description="Morning brief: weather, sleep, calendar, health. Sends weather to Tara.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def pinocytosis_photoreception(
    send_weather: bool = False, json_output: bool = True
) -> PinocytosisResult:
    """Gather context for the photoreception morning brief."""
    args = []
    if json_output:
        args.append("--json")
    if send_weather:
        args.append("--send")
    result = invoke_organelle("photoreception-gather", args, timeout=30)
    return PinocytosisResult(output=result)


@tool(
    name="pinocytosis_ultradian",
    description="Situational snapshot: calendar, TODO, NOW.md, job alerts, ACTA.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def pinocytosis_ultradian(json_output: bool = True) -> PinocytosisResult:
    """Gather context for ultradian/kairos situational snapshot."""
    args = ["--json"] if json_output else []
    result = invoke_organelle("kairos-gather", args, timeout=30)
    return PinocytosisResult(output=result)


@tool(
    name="pinocytosis_interphase",
    description="Evening context: inbox, WhatsApp, calendar, TODO, archived emails.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def pinocytosis_interphase(json_output: bool = True) -> PinocytosisResult:
    """Gather context for the interphase evening routine."""
    args = ["--json"] if json_output else []
    result = invoke_organelle("interphase-gather", args, timeout=30)
    return PinocytosisResult(output=result)


@tool(
    name="pinocytosis_weekly",
    description="Weekly review context: next week calendar, TODO, Oura, spores.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def pinocytosis_weekly(json_output: bool = True) -> PinocytosisResult:
    """Gather context for the ecdysis weekly review."""
    args = ["--json"] if json_output else []
    result = invoke_organelle("weekly-gather", args, timeout=30)
    return PinocytosisResult(output=result)


@tool(
    name="pinocytosis_polarization",
    description="Overnight flywheel preflight: consumption check, guard, north stars.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def pinocytosis_polarization(json_output: bool = True) -> PinocytosisResult:
    """Gather preflight context for the polarization overnight flywheel."""
    args = ["preflight"]
    if json_output:
        args.append("--json")
    result = invoke_organelle("copia-gather", args, timeout=30)
    return PinocytosisResult(output=result)


@tool(
    name="polarization_guard",
    description="Manage overnight flywheel guard: on, off, or status.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def polarization_guard(action: str = "status") -> PinocytosisResult:
    """Control the polarization guard file (on/off/status)."""
    result = invoke_organelle("copia-gather", ["guard", action], timeout=10)
    return PinocytosisResult(output=result)
