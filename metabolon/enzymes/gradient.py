"""proprioception_gradient — direction maker pattern (Andrews et al. 2024).

Thin enzyme wrapper around the gradient_sense organelle.
Business logic lives in metabolon.organelles.gradient_sense.
"""

from __future__ import annotations

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.organelles.gradient_sense import (
    GradientReport,
    build_gradient_report,
)


@tool(
    name="proprioception_gradient",
    description="Detect trending domains across RSS, tool usage, and search. Surfaces the organism's polarity vector.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def proprioception_gradient(days: int = 7) -> GradientReport:
    """Sense directional gradients across the organism's sensor arrays.

    Reads three signal sources — lustro RSS relevance scores, tool invocation
    frequency, and search query text — then detects which topic domains are
    co-trending. Returns the polarity vector: the domain(s) the organism is
    orienting toward.

    Biology: implements the Direction Maker pattern (Andrews et al. 2024).
    Small asymmetric signals are detected and compared across sensors.
    The domain with highest sensor coverage is the polarity axis.

    Args:
        days: Rolling window in days to consider (default 7).
    """
    return build_gradient_report(days)
