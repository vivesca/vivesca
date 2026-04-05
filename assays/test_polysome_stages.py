"""Tests for polysome staged execution — Temporal-native dependency ordering."""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

import pytest

# Path setup — add polysome to sys.path so imports work
_POLYSOME_DIR = Path(__file__).resolve().parent.parent / "effectors" / "polysome"
sys.path.insert(0, str(_POLYSOME_DIR))

from workflow import TranslationWorkflow


def _make_result(task: str, approved: bool = True) -> dict:
    """Build a mock _execute_one result."""
    return {
        "task": task,
        "provider": "zhipu",
        "success": approved,
        "exit_code": 0 if approved else -1,
        "mode": "raw",
        "review": {
            "approved": approved,
            "verdict": "approved" if approved else "rejected",
            "flags": [],
        },
    }


class TestStagedExecution:
    """Test staged execution in TranslationWorkflow.run."""

    async def test_flat_list_shim_runs_single_stage(self):
        """Flat list of 2 specs auto-wrapped as single stage, both execute."""
        wf = TranslationWorkflow()
        executed = []

        async def mock_execute_one(spec):
            executed.append(spec["task"])
            return _make_result(spec["task"])

        wf._execute_one = mock_execute_one

        result = await wf.run([
            {"task": "task_a"},
            {"task": "task_b"},
        ])

        assert set(executed) == {"task_a", "task_b"}
        assert result["total"] == 2
        assert result["succeeded"] == 2
        assert result["approved"] == 2

    async def test_two_stages_run_sequentially(self):
        """[[s1], [s2]] — s1 completes before s2 starts."""
        wf = TranslationWorkflow()
        order = []

        async def mock_execute_one(spec):
            name = spec["task"]
            order.append(f"start_{name}")
            await asyncio.sleep(0.05)
            order.append(f"end_{name}")
            return _make_result(name)

        wf._execute_one = mock_execute_one

        result = await wf.run([[{"task": "s1"}], [{"task": "s2"}]])

        assert order == ["start_s1", "end_s1", "start_s2", "end_s2"]
        assert result["total"] == 2
        assert result["approved"] == 2

    async def test_stage_parallel_within_stage(self):
        """[[s1, s2], [s3]] — s1 and s2 overlap in execution (concurrent)."""
        wf = TranslationWorkflow()
        times = {}

        async def mock_execute_one(spec):
            name = spec["task"]
            times[f"{name}_start"] = time.monotonic()
            await asyncio.sleep(0.05)
            times[f"{name}_end"] = time.monotonic()
            return _make_result(name)

        wf._execute_one = mock_execute_one

        result = await wf.run([
            [{"task": "s1"}, {"task": "s2"}],
            [{"task": "s3"}],
        ])

        assert result["total"] == 3
        # s1 and s2 overlapped (concurrent within stage)
        assert times["s2_start"] < times["s1_end"]
        assert times["s1_start"] < times["s2_end"]
        # s3 started after both s1 and s2 finished (sequential stages)
        assert times["s3_start"] > times["s1_end"]
        assert times["s3_start"] > times["s2_end"]

    async def test_stage_failure_skips_downstream(self):
        """Reject s_fail → downstream stage appears with predecessor_failed."""
        wf = TranslationWorkflow()
        executed = []

        async def mock_execute_one(spec):
            name = spec["task"]
            executed.append(name)
            approved = name != "s_fail"
            return _make_result(name, approved=approved)

        wf._execute_one = mock_execute_one

        result = await wf.run([
            [{"task": "s_fail"}, {"task": "s_ok"}],
            [{"task": "s_downstream"}],
        ])

        # Only stage-1 specs were actually executed
        assert set(executed) == {"s_fail", "s_ok"}
        assert result["total"] == 3

        # Find the downstream result
        downstream = [r for r in result["results"] if r["task"] == "s_downstream"]
        assert len(downstream) == 1
        d = downstream[0]
        assert d["mode"] == "skipped"
        assert d["success"] is False
        assert d["review"]["verdict"] == "predecessor_failed"
        assert d["review"]["approved"] is False
        assert any("skipped_stage_1" in f for f in d["review"]["flags"])

    async def test_backwards_compat_flat_list(self):
        """Existing flat-list callers get identical results to before."""
        wf = TranslationWorkflow()

        async def mock_execute_one(spec):
            return _make_result(spec["task"])

        wf._execute_one = mock_execute_one

        flat_input = [
            {"task": "legacy_a", "provider": "zhipu"},
            {"task": "legacy_b", "provider": "volcano"},
        ]

        result = await wf.run(flat_input)

        assert result["total"] == 2
        assert result["succeeded"] == 2
        assert result["approved"] == 2
        assert result["rejected"] == 0
        tasks = [r["task"] for r in result["results"]]
        assert "legacy_a" in tasks
        assert "legacy_b" in tasks
