"""Per-enzyme emotion computation from sensory aggregates."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from metabolon.metabolism.signals import Stimulus


@dataclass
class Emotion:
    """Emotion (crystallised value signal) for a single enzyme."""

    tool: str
    activations: int  # enzyme activation count
    success_rate: float
    metabolic_cost: float  # cellular energy expenditure per activation
    valence: float | None  # None if insufficient data


def sense_affect(
    stimuli: list[Stimulus],
    min_stimuli: int = 3,
) -> dict[str, Emotion]:
    """Compute emotion (value signal) per enzyme from a list of stimuli.

    Valence = success_rate * (1 / log2(metabolic_cost + 1)).
    Higher is better. Rewards quality and parsimony.
    """
    by_enzyme: dict[str, list[Stimulus]] = defaultdict(list)
    for s in stimuli:
        by_enzyme[s.tool].append(s)

    result = {}
    for tool, tool_stimuli in by_enzyme.items():
        n = len(tool_stimuli)
        successes = sum(1 for s in tool_stimuli if s.outcome == "success")
        success_rate = successes / n
        metabolic_cost = sum(s.substrate_consumed + s.product_released for s in tool_stimuli) / n

        # log2(cost+2) so zero cost doesn't blow up, higher cost = lower valence
        valence = None if n < min_stimuli else success_rate * (1.0 / math.log2(metabolic_cost + 2))

        result[tool] = Emotion(
            tool=tool,
            activations=n,
            success_rate=success_rate,
            metabolic_cost=metabolic_cost,
            valence=valence,
        )
    return result
