"""Tests for membrane._acute_immune_response — honest infection logging."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from metabolon.membrane import SensoryMiddleware
from metabolon.metabolism.signals import SensorySystem

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _middleware(tmp_path):
    log = tmp_path / "signals.jsonl"
    return SensoryMiddleware(collector=SensorySystem(cortex_path=log))


# ---------------------------------------------------------------------------
# Infection logging
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_infection_logged_when_repair_skipped(tmp_path):
    """Errors on tools not in the Genome still get an infection record."""
    tmp_path / "infections.jsonl"
    mw = _middleware(tmp_path)

    with (
        patch("metabolon.membrane.record_infection") as mock_log,
        patch("metabolon.metabolism.variants.Genome") as MockGenome,
    ):
        # Tool not in genome — repair is skipped, but infection must be logged.
        MockGenome.return_value.expressed_tools.return_value = []
        await mw._acute_immune_response("unknown_tool", "something broke")

    mock_log.assert_called_once()
    call_kwargs = mock_log.call_args
    assert call_kwargs.args[0] == "unknown_tool"
    assert call_kwargs.kwargs.get("healed") is False or call_kwargs.args[2] is False


@pytest.mark.asyncio
async def test_infection_marked_healed_when_repair_succeeds(tmp_path):
    """When LLM repair is accepted and promoted, infection is logged as healed."""
    mw = _middleware(tmp_path)

    mock_repair_result = MagicMock()
    mock_repair_result.accepted = True
    mock_repair_result.candidate = "Better description that prevents failures."

    mock_judge = MagicMock()
    mock_judge.passed = True

    with (
        patch("metabolon.membrane.record_infection") as mock_log,
        patch("metabolon.metabolism.variants.Genome") as MockGenome,
        patch(
            "metabolon.metabolism.repair.immune_response",
            new_callable=AsyncMock,
            return_value=mock_repair_result,
        ),
        patch(
            "metabolon.metabolism.gates.taste",
            new_callable=AsyncMock,
            return_value=mock_judge,
        ),
    ):
        store = MockGenome.return_value
        store.expressed_tools.return_value = ["my_tool"]
        store.active_allele.return_value = "Current description."
        store.founding_allele.return_value = "Founding description."
        store.express_variant.return_value = 2

        await mw._acute_immune_response("my_tool", "auth failed")

    mock_log.assert_called_once()
    # healed=True should be passed
    call_kwargs = mock_log.call_args
    healed = call_kwargs.kwargs.get("healed") or (
        len(call_kwargs.args) > 2 and call_kwargs.args[2]
    )
    assert healed is True


@pytest.mark.asyncio
async def test_infection_logged_even_when_repair_fails(tmp_path):
    """If LLM repair raises, infection is still logged as unhealed."""
    mw = _middleware(tmp_path)

    with (
        patch("metabolon.membrane.record_infection") as mock_log,
        patch("metabolon.metabolism.variants.Genome") as MockGenome,
        patch(
            "metabolon.metabolism.repair.immune_response",
            new_callable=AsyncMock,
            side_effect=RuntimeError("LLM unavailable"),
        ),
    ):
        store = MockGenome.return_value
        store.expressed_tools.return_value = ["broken_tool"]
        store.active_allele.return_value = "desc"

        await mw._acute_immune_response("broken_tool", "network timeout")

    mock_log.assert_called_once()
    call_kwargs = mock_log.call_args
    healed = call_kwargs.kwargs.get("healed") or (
        len(call_kwargs.args) > 2 and call_kwargs.args[2]
    )
    assert healed is False
