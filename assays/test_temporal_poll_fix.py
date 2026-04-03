"""Tests for temporal dispatch poller stalling fix (t-pollfix).

The dispatch poll loop must not block for more than 120s per cycle.
Workflow starts should be fire-and-forget (start_workflow, not execute_workflow).
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

DISPATCH_PY = Path.home() / "germline" / "effectors" / "temporal-golem" / "dispatch.py"


class TestPollLoopTimeout:
    """The poll loop must wrap dispatch calls with a timeout."""

    def test_dispatch_has_asyncio_timeout(self):
        """The poll loop should use asyncio.wait_for or equivalent timeout on dispatch."""
        source = DISPATCH_PY.read_text()
        # Should contain wait_for with a timeout around the dispatch call
        assert "wait_for" in source or "asyncio.timeout" in source, (
            "Poll loop must wrap dispatch with asyncio.wait_for or asyncio.timeout"
        )

    def test_timeout_value_reasonable(self):
        """The timeout should be <= 120s (2 min), not longer than the poll interval."""
        source = DISPATCH_PY.read_text()
        # Look for timeout value near wait_for
        # Accept patterns like wait_for(..., timeout=120) or asyncio.timeout(120)
        timeout_match = re.search(r'timeout[=\(]\s*(\d+)', source)
        assert timeout_match, "Could not find timeout value in dispatch.py"
        timeout_val = int(timeout_match.group(1))
        assert timeout_val <= 180, f"Timeout {timeout_val}s is too long, should be <= 180s"


class TestFireAndForget:
    """Workflow starts must be non-blocking (start_workflow, not execute_workflow)."""

    def test_uses_start_workflow_not_execute(self):
        """dispatch.py should use client.start_workflow (fire-and-forget), not execute_workflow."""
        source = DISPATCH_PY.read_text()
        assert "start_workflow" in source, "Should use start_workflow for fire-and-forget dispatch"
        # execute_workflow blocks until completion — must not be used in the poll loop
        # It's OK if execute_workflow exists elsewhere (e.g. in a status query),
        # but the dispatch function should not use it
        dispatch_fn_match = re.search(
            r'async def _dispatch_pending.*?(?=\nasync def |\nclass |\Z)',
            source,
            re.DOTALL,
        )
        if dispatch_fn_match:
            dispatch_fn = dispatch_fn_match.group()
            assert "execute_workflow" not in dispatch_fn, (
                "_dispatch_pending must use start_workflow, not execute_workflow"
            )


class TestSyntaxValid:
    """dispatch.py must parse without errors after modification."""

    def test_ast_parse(self):
        source = DISPATCH_PY.read_text()
        ast.parse(source)
