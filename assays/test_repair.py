from __future__ import annotations

"""Tests for hot-path metaprompt repair."""


from unittest.mock import AsyncMock, patch

import pytest

from metabolon.metabolism.repair import ImmuneRequest, immune_response


def test_repair_request_model():
    r = ImmuneRequest(
        tool="fasti_list_events",
        current_description="List calendar events.",
        failure_reason="Returned HTML instead of event list",
        context="User asked for today's meetings",
    )
    assert r.tool == "fasti_list_events"


@pytest.mark.asyncio
@patch("metabolon.metabolism.repair._mutate", new_callable=AsyncMock)
async def test_generate_repair_passes_gate(mock_mutator):
    mock_mutator.return_value = (
        "List calendar events for a given date in HKT timezone, returning structured event data."
    )
    result = await immune_response(
        ImmuneRequest(
            tool="t",
            current_description="List events.",
            failure_reason="too vague",
        )
    )
    assert result.candidate is not None
    assert result.accepted is True


@pytest.mark.asyncio
@patch("metabolon.metabolism.repair._mutate", new_callable=AsyncMock)
async def test_generate_repair_retries_on_gate_fail(mock_mutator):
    mock_mutator.return_value = "Bad."

    result = await immune_response(
        ImmuneRequest(
            tool="t",
            current_description="List events.",
            failure_reason="too vague",
        ),
        max_adaptation_cycles=2,
    )
    assert result.accepted is False
    assert mock_mutator.call_count == 2
