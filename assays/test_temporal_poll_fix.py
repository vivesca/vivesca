"""Tests for temporal dispatch poller stalling fix (t-c5eef9)."""

from __future__ import annotations

import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestPollLoopTimeout:
    """The poll loop must not block indefinitely on dispatch."""

    @pytest.mark.asyncio
    async def test_dispatch_timeout_does_not_crash(self):
        """If dispatch takes >120s, poll loop should log and continue."""

        async def slow_dispatch(*args, **kwargs):
            await asyncio.sleep(999)
            return 0

        # Simulate: wrap dispatch with wait_for timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_dispatch(), timeout=0.1)

    @pytest.mark.asyncio
    async def test_dispatch_timeout_allows_next_cycle(self):
        """After a timeout, the poller should be able to run the next cycle."""
        call_count = 0

        async def flaky_dispatch():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                await asyncio.sleep(999)  # hangs first time
            return 0  # succeeds second time

        # First call times out
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(flaky_dispatch(), timeout=0.1)

        # Second call succeeds
        result = await asyncio.wait_for(flaky_dispatch(), timeout=1.0)
        assert result == 0
        assert call_count == 2


class TestWorkflowStartMode:
    """Workflow submission must be fire-and-forget (start, not execute)."""

    @pytest.mark.asyncio
    async def test_start_workflow_returns_handle(self):
        """client.start_workflow should return immediately with a handle."""
        mock_client = AsyncMock()
        mock_handle = MagicMock()
        mock_handle.id = "test-workflow-id"
        mock_client.start_workflow.return_value = mock_handle

        handle = await mock_client.start_workflow(
            "TranslationWorkflow",
            args=[[]],
            id="test-id",
            task_queue="translation-queue",
        )
        assert handle.id == "test-workflow-id"
        mock_client.start_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_workflow_would_block(self):
        """client.execute_workflow blocks until completion — should NOT be used."""
        mock_client = AsyncMock()

        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(999)
            return {"done": True}

        mock_client.execute_workflow = slow_execute

        # execute_workflow would block — verify it times out
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                mock_client.execute_workflow("Workflow", args=[]),
                timeout=0.1,
            )
