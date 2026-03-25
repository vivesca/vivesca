"""metabolism tools — metabolic signal reporting.

Tools:
  metabolism_knowledge_signal — report whether a loaded knowledge substrate was useful
"""

from __future__ import annotations

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.metabolism.signals import Outcome, SensorySystem, Stimulus
from metabolon.morphology import EffectorResult


class MetabolicSignalResult(EffectorResult):
    """Result of recording a metabolic knowledge signal."""

    artifact: str
    recorded_outcome: str


@tool(
    name="metabolism_knowledge_signal",
    description="Report whether a loaded knowledge artifact was useful this session.",
    annotations=ToolAnnotations(readOnlyHint=False),
)
def metabolism_knowledge_signal(
    artifact: str,
    useful: bool,
    context: str = "",
) -> MetabolicSignalResult:
    """Record whether a knowledge substrate contributed to session quality.

    Call at session end for each memory file, reference doc, or skill
    that was loaded. Outcome = success if useful, error if loaded but
    not useful (wasted tokens).

    Args:
        artifact: Path or name of the knowledge artifact (e.g., "memory/user_health.md")
        useful: Whether the artifact contributed to the session outcome
        context: Optional note on how it was or wasn't useful
    """
    collector = SensorySystem()
    outcome = Outcome.success if useful else Outcome.error

    collector.append(
        Stimulus(
            tool=f"knowledge:{artifact}",
            outcome=outcome,
            substrate_consumed=0,
            product_released=0,
            response_latency=0,
            context=context,
        )
    )

    return MetabolicSignalResult(
        success=True,
        action="recorded",
        artifact=artifact,
        recorded_outcome=outcome.value,
        message=f"Knowledge signal recorded: {artifact} = {'useful' if useful else 'not useful'}",
    )
