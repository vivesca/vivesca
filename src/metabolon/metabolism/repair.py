"""Immune system — metaprompt-driven healing."""

import asyncio
import configparser
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

from metabolon.metabolism.gates import GateResult, reflex_check

_CONF_PATH = Path(__file__).with_suffix(".conf")
_DEFAULTS = {"adaptation": {"max_adaptation_cycles": "3"}}


def _load_conf() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read_dict(_DEFAULTS)
    if _CONF_PATH.exists():
        cfg.read(_CONF_PATH)
    return cfg


_MAX_ADAPTATION_CYCLES = _load_conf().getint("adaptation", "max_adaptation_cycles")


class ImmuneRequest(BaseModel):
    """Input for a targeted repair attempt."""

    tool: str
    current_description: str
    failure_reason: str
    context: str | None = None


@dataclass
class ImmuneResult:
    candidate: str | None
    accepted: bool
    gate_result: GateResult
    attempts: int


async def _mutate(request: ImmuneRequest) -> str:
    """Single LLM call to generate a revised description."""

    from metabolon.symbiont import transduce

    prompt = (
        f"You are revising an MCP tool description to fix a specific failure.\n\n"
        f"Tool: {request.tool}\n"
        f"Current description: {request.current_description}\n"
        f"Failure reason: {request.failure_reason}\n"
        f"Context: {request.context or 'N/A'}\n\n"
        f"Write an improved description that would prevent this failure. "
        f"Change as little as possible. Output ONLY the new description, nothing else."
    )

    result = await asyncio.to_thread(transduce, "glm", prompt)
    return result.strip()


async def immune_response(
    request: ImmuneRequest,
    max_adaptation_cycles: int | None = None,
) -> ImmuneResult:
    """Attempt targeted repair, retrying up to max_adaptation_cycles on gate failure."""
    if max_adaptation_cycles is None:
        max_adaptation_cycles = _MAX_ADAPTATION_CYCLES
    gate = GateResult(False, "no attempts made")
    for cycle in range(1, max_adaptation_cycles + 1):
        candidate_allele = await _mutate(request)
        gate = reflex_check(candidate_allele)

        if gate.passed:
            return ImmuneResult(
                candidate=candidate_allele,
                accepted=True,
                gate_result=gate,
                attempts=cycle,
            )

    return ImmuneResult(
        candidate=None,
        accepted=False,
        gate_result=gate,
        attempts=max_adaptation_cycles,
    )
