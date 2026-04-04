"""Selection pressure — reflex checks + taste."""

import asyncio
import configparser
from dataclasses import dataclass
from pathlib import Path

_CONF_PATH = Path(__file__).parent / "gating.conf"
_conf = configparser.ConfigParser()
_conf.read(_CONF_PATH)

MIN_WORDS = _conf.getint("reflex", "min_words", fallback=5)
MAX_WORDS = _conf.getint("reflex", "max_words", fallback=200)


@dataclass
class GateResult:
    passed: bool
    reason: str


def reflex_check(allele: str) -> GateResult:
    """Fast, cheap checks before LLM judge — screens candidate variant descriptions."""
    text = allele.strip()
    if not text:
        return GateResult(False, "Empty description")

    words = text.split()
    if len(words) < MIN_WORDS:
        return GateResult(False, f"Too short ({len(words)} words, min {MIN_WORDS})")
    if len(words) > MAX_WORDS:
        return GateResult(False, f"Too long ({len(words)} words, max {MAX_WORDS})")

    return GateResult(True, "OK")


async def taste(
    tool_name: str,
    founder_sequence: str,
    variant_sequence: str,
) -> GateResult:
    """LLM-based holistic check: does the variant still accurately
    describe what the tool does? Compares against the founder genotype.

    Uses metabolon.symbiont for the LLM call.
    """

    from metabolon.symbiont import transduce

    prompt = (
        f"You are evaluating a proposed tool description change.\n\n"
        f"Tool: {tool_name}\n"
        f"Original description: {founder_sequence}\n"
        f"Proposed description: {variant_sequence}\n\n"
        f"Does the proposed description still accurately convey what the tool does? "
        f"Is it clear, specific, and not misleading?\n\n"
        f"Reply with exactly 'PASS' or 'FAIL: <reason>'."
    )

    response = await asyncio.to_thread(transduce, "haiku", prompt)
    text = response.strip()

    if text.startswith("PASS"):
        return GateResult(True, "LLM judge: PASS")
    else:
        reason = text.removeprefix("FAIL:").strip() or "LLM judge rejected"
        return GateResult(False, f"LLM judge: {reason}")
