"""Pinocytosis — deterministic context gathering as MCP tools.

Direct imports from the pinocytosis package. No shelling out to binaries.

Tools:
  pinocytosis_photoreception — morning brief context
  pinocytosis_ultradian     — situational snapshot
  pinocytosis_interphase    — evening routine context
  pinocytosis_ecdysis       — weekly review context
  pinocytosis_polarization  — overnight flywheel preflight
"""

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion
from metabolon.pinocytosis import interphase, photoreception, polarization, ultradian, ecdysis


class PinocytosisResult(Secretion):
    """Deterministic context output from a gather routine."""

    output: str


@tool(
    name="pinocytosis_photoreception",
    description="Morning brief: weather, sleep, calendar, health.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def pinocytosis_photoreception(
    send_weather: bool = False, json_output: bool = True
) -> PinocytosisResult:
    """Gather context for the photoreception morning brief."""
    result = photoreception.intake(as_json=json_output, send_weather=send_weather)
    return PinocytosisResult(output=result)


@tool(
    name="pinocytosis_ultradian",
    description="Situational snapshot: calendar, TODO, Tonus, alerts.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def pinocytosis_ultradian(json_output: bool = True) -> PinocytosisResult:
    """Gather context for ultradian situational snapshot."""
    result = ultradian.intake(as_json=json_output)
    return PinocytosisResult(output=result)


@tool(
    name="pinocytosis_interphase",
    description="Evening context: inbox, WhatsApp, calendar, TODO, archived emails.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def pinocytosis_interphase(json_output: bool = True) -> PinocytosisResult:
    """Gather context for the interphase evening routine."""
    result = interphase.intake(as_json=json_output)
    return PinocytosisResult(output=result)


@tool(
    name="pinocytosis_ecdysis",
    description="Weekly review context: next week calendar, TODO, Oura, spores.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def pinocytosis_ecdysis(json_output: bool = True) -> PinocytosisResult:
    """Gather context for the ecdysis weekly review."""
    result = ecdysis.intake(as_json=json_output)
    return PinocytosisResult(output=result)


@tool(
    name="pinocytosis_polarization",
    description="Overnight flywheel preflight: consumption, guard, north stars.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def pinocytosis_polarization(json_output: bool = True) -> PinocytosisResult:
    """Gather preflight context for the polarization overnight flywheel."""
    result = polarization.intake(as_json=json_output)
    return PinocytosisResult(output=result)


@tool(
    name="polarization_guard",
    description="Manage overnight flywheel guard: on, off, or status.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def polarization_guard_tool(action: str = "status") -> PinocytosisResult:
    """Control the polarization guard file (on/off/status)."""
    result = polarization.guard(action=action)
    return PinocytosisResult(output=result)
