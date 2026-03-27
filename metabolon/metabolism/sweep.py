"""Cold path — weekly differential evolution sweep."""

from __future__ import annotations

import configparser
import statistics
from dataclasses import dataclass
from pathlib import Path

from metabolon.metabolism.fitness import Emotion

_CONF_PATH = Path(__file__).with_suffix(".conf")
_DEFAULTS = {
    "selection": {
        "min_phenotypes": "3",
        "max_retries": "3",
        "fitness_plateau": "0.8",
        "offspring_per_generation": "2",
    }
}


def _load_conf() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read_dict(_DEFAULTS)
    if _CONF_PATH.exists():
        cfg.read(_CONF_PATH)
    return cfg


def _default_sweep_config() -> SweepConfig:
    cfg = _load_conf()
    return SweepConfig(
        min_phenotypes=cfg.getint("selection", "min_phenotypes"),
        max_retries=cfg.getint("selection", "max_retries"),
        fitness_plateau=cfg.getfloat("selection", "fitness_plateau"),
        offspring_per_generation=cfg.getint("selection", "offspring_per_generation"),
    )


@dataclass
class SweepConfig:
    """Configuration for the weekly sweep. Defaults loaded from sweep.conf."""

    min_phenotypes: int = 3  # minimum observed phenotypes to evaluate
    max_retries: int = 3
    fitness_plateau: float = 0.8  # fitness stabilisation threshold
    offspring_per_generation: int = 2  # new candidates generated per sweep

    @classmethod
    def from_conf(cls) -> SweepConfig:
        """Load a SweepConfig from sweep.conf (falls back to dataclass defaults)."""
        return _default_sweep_config()


def select(
    emotions: dict[str, Emotion],
) -> list[str]:
    """Identify tools that need optimisation.

    Candidates: valence below median, zero activations, or None valence (insufficient data).
    """
    valence_map = {t: e.valence for t, e in emotions.items() if e.valence is not None}

    if valence_map:
        median = statistics.median(valence_map.values())
        low_valence_loci = {t for t, f in valence_map.items() if f < median}
    else:
        low_valence_loci = set()

    # Also flag tools with None valence (zero activations or insufficient data)
    immature_loci = {t for t, e in emotions.items() if e.valence is None}

    return sorted(low_valence_loci | immature_loci)


async def recombine(
    tool: str,
    parent_a: str,
    parent_b: str,
    reference_phenotype: str,
) -> str:
    """Differential evolution: diff two parent alleles, splice delta into reference.

    Returns a new candidate description.
    """

    from metabolon.symbiont import transduce

    prompt = (
        f"You are performing differential evolution on an MCP tool description.\n\n"
        f"Tool: {tool}\n"
        f"Parent A: {parent_a}\n"
        f"Parent B: {parent_b}\n"
        f"Current best: {reference_phenotype}\n\n"
        f"Identify what differs between A and B. Apply that difference to the current best "
        f"to produce a new variant. Output ONLY the new description."
    )
    return (await transduce(prompt, model="haiku")).strip()


async def mutate(tool: str, description: str, selection_pressure: str) -> str:
    """Derive a mutation instruction from the selection pressure, then apply it."""

    from metabolon.symbiont import transduce

    prompt = (
        f"An MCP tool has this description:\n{description}\n\n"
        f"It has been failing because: {selection_pressure}\n\n"
        f"First, derive a specific mutation instruction (what to change and why). "
        f"Then apply it. Output ONLY the revised description."
    )
    return (await transduce(prompt, model="haiku")).strip()
