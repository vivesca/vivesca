"""Tests for golem_dispatch MCP enzyme — direct Temporal dispatch.

Tests mock the Temporal client to avoid requiring a live server.
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── dispatch action ──────────────────────────────────────────────────────────


class TestDispatch:
    """dispatch() should start a Temporal workflow and return workflow_id."""

    def test_dispatch_single_task(self):
        """Single task dispatch returns workflow_id and status."""
        from metabolon.enzymes.golem_dispatch import golem_dispatch

        with patch("metabolon.enzymes.golem_dispatch._start_workflow") as mock_start:
            mock_start.return_value = {
                "workflow_id": "golem-zhipu-abc12345",
                "tasks_submitted": 1,
            }
            result = golem_dispatch(
                action="dispatch",
                prompt="Write tests for foo.py",
                provider="zhipu",
                max_turns=15,
            )
            assert "workflow_id" in result.data
            assert result.data["tasks_submitted"] == 1
            mock_start.assert_called_once()

    def test_dispatch_requires_prompt(self):
        """dispatch without prompt returns error."""
        from metabolon.enzymes.golem_dispatch import golem_dispatch

        result = golem_dispatch(action="dispatch", prompt="")
        assert not result.success

    def test_dispatch_default_provider_is_zhipu(self):
        """Default provider should be zhipu."""
        from metabolon.enzymes.golem_dispatch import golem_dispatch

        with patch("metabolon.enzymes.golem_dispatch._start_workflow") as mock_start:
            mock_start.return_value = {
                "workflow_id": "golem-zhipu-abc12345",
                "tasks_submitted": 1,
            }
            golem_dispatch(action="dispatch", prompt="test task")
            call_args = mock_start.call_args
            specs = call_args[0][0] if call_args[0] else call_args[1].get("specs", [])
            assert any(s.get("provider") == "zhipu" for s in specs)


# ── batch dispatch ───────────────────────────────────────────────────────────


class TestBatchDispatch:
    """dispatch_batch() should start one workflow with multiple specs."""

    def test_batch_dispatch_multiple_tasks(self):
        """Batch dispatch starts one workflow with N specs."""
        from metabolon.enzymes.golem_dispatch import golem_dispatch

        specs_json = json.dumps([
            {"prompt": "Task A", "provider": "zhipu", "max_turns": 15},
            {"prompt": "Task B", "provider": "zhipu", "max_turns": 20},
        ])
        with patch("metabolon.enzymes.golem_dispatch._start_workflow") as mock_start:
            mock_start.return_value = {
                "workflow_id": "golem-zhipu-batch123",
                "tasks_submitted": 2,
            }
            result = golem_dispatch(action="batch", specs=specs_json)
            assert result.data["tasks_submitted"] == 2

    def test_batch_dispatch_empty_specs_fails(self):
        """Empty specs list returns error."""
        from metabolon.enzymes.golem_dispatch import golem_dispatch

        result = golem_dispatch(action="batch", specs="[]")
        assert not result.success


# ── status action ────────────────────────────────────────────────────────────


class TestStatus:
    """status() should query a workflow by ID and return its state."""

    def test_status_returns_workflow_info(self):
        """status with valid workflow_id returns state."""
        from metabolon.enzymes.golem_dispatch import golem_dispatch

        with patch("metabolon.enzymes.golem_dispatch._get_workflow_status") as mock_status:
            mock_status.return_value = {
                "workflow_id": "golem-zhipu-abc12345",
                "status": "COMPLETED",
                "result": {"total": 1, "approved": 1},
            }
            result = golem_dispatch(action="status", workflow_id="golem-zhipu-abc12345")
            assert result.data["status"] == "COMPLETED"

    def test_status_requires_workflow_id(self):
        """status without workflow_id returns error."""
        from metabolon.enzymes.golem_dispatch import golem_dispatch

        result = golem_dispatch(action="status")
        assert not result.success


# ── list action ──────────────────────────────────────────────────────────────


class TestList:
    """list() should return recent workflows."""

    def test_list_returns_workflows(self):
        """list returns array of recent workflows."""
        from metabolon.enzymes.golem_dispatch import golem_dispatch

        with patch("metabolon.enzymes.golem_dispatch._list_workflows") as mock_list:
            mock_list.return_value = [
                {"workflow_id": "golem-zhipu-abc", "status": "COMPLETED"},
                {"workflow_id": "golem-zhipu-def", "status": "RUNNING"},
            ]
            result = golem_dispatch(action="list", limit=10)
            assert len(result.data["workflows"]) == 2

    def test_list_empty(self):
        """list with no workflows returns empty array."""
        from metabolon.enzymes.golem_dispatch import golem_dispatch

        with patch("metabolon.enzymes.golem_dispatch._list_workflows") as mock_list:
            mock_list.return_value = []
            result = golem_dispatch(action="list")
            assert result.data["workflows"] == []


# ── cancel action ────────────────────────────────────────────────────────────


class TestCancel:
    """cancel() should terminate a running workflow."""

    def test_cancel_workflow(self):
        """cancel with valid workflow_id succeeds."""
        from metabolon.enzymes.golem_dispatch import golem_dispatch

        with patch("metabolon.enzymes.golem_dispatch._cancel_workflow") as mock_cancel:
            mock_cancel.return_value = True
            result = golem_dispatch(action="cancel", workflow_id="golem-zhipu-abc12345")
            assert result.output
            mock_cancel.assert_called_once_with("golem-zhipu-abc12345")

    def test_cancel_requires_workflow_id(self):
        """cancel without workflow_id returns error."""
        from metabolon.enzymes.golem_dispatch import golem_dispatch

        result = golem_dispatch(action="cancel")
        assert not result.success


# ── temporal connection ──────────────────────────────────────────────────────


class TestTemporalConnection:
    """Connection helpers should target ganglion:7233."""

    def test_default_host(self):
        """Default Temporal host is ganglion:7233."""
        from metabolon.enzymes.golem_dispatch import TEMPORAL_HOST

        assert "7233" in TEMPORAL_HOST
        assert "ganglion" in TEMPORAL_HOST or "100.120.158.22" in TEMPORAL_HOST

    def test_host_configurable_via_env(self, monkeypatch):
        """TEMPORAL_HOST env var overrides default."""
        monkeypatch.setenv("TEMPORAL_HOST", "localhost:7233")
        # Re-import to pick up env
        import importlib
        import metabolon.enzymes.golem_dispatch as mod
        importlib.reload(mod)
        assert mod.TEMPORAL_HOST == "localhost:7233"
