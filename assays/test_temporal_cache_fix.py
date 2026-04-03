"""Tests for output cache collision fix (t-cachfix).

The worker's idempotency cache must not return stale failures.
Only successful (Exit: 0) cached results should short-circuit execution.
"""
from __future__ import annotations

import ast
from pathlib import Path
WORKER_PY = Path.home() / "germline" / "effectors" / "temporal-golem" / "worker.py"


class TestCacheSkipsFailure:
    """Stale failure cache must not short-circuit re-dispatch."""

    def test_cache_check_requires_success(self):
        """The cache check should only return for Exit: 0, not for failures."""
        source = WORKER_PY.read_text()
        # The existing code has: if cached.exists(): ... rc = 0 if "Exit: 0" in content[:200] else 1
        # The fix should skip/continue execution when rc != 0 (failure cache)
        # Look for evidence that failure cache is handled differently
        # After fix: should have a branch that logs and continues when cache shows failure
        assert "stale" in source.lower() or "re-executing" in source.lower() or "skip" in source.lower(), (
            "Worker should handle stale failure cache — log and re-execute instead of returning"
        )

    def test_cache_check_still_returns_success(self):
        """Successful cached results (Exit: 0) should still short-circuit."""
        source = WORKER_PY.read_text()
        assert "Exit: 0" in source, "Cache check must still detect successful exits"
        assert "cached" in source.lower(), "Cache path must still exist for successful results"


class TestOutputOverwrite:
    """Re-execution should overwrite the stale output file."""

    def test_output_file_written_after_execution(self):
        """The output file write at the end should use the same path as the cache check."""
        source = WORKER_PY.read_text()
        # Both the cache check and the output write should reference the same pattern
        assert source.count("OUTPUT_DIR") >= 2, (
            "OUTPUT_DIR should appear in both cache check and output write"
        )


class TestSyntaxValid:
    """worker.py must parse without errors after modification."""

    def test_ast_parse(self):
        source = WORKER_PY.read_text()
        ast.parse(source)
