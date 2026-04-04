"""Tests for ribosome_dispatch MCP enzyme — direct Temporal dispatch.

Tests mock the Temporal client to avoid requiring a live server.
"""

import json
from unittest.mock import patch

# ── dispatch action ──────────────────────────────────────────────────────────


class TestDispatch:
    """dispatch() should start a Temporal workflow and return workflow_id."""

    def test_dispatch_single_task(self):
        """Single task dispatch returns workflow_id and status."""
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._start_workflow") as mock_start:
            mock_start.return_value = {
                "workflow_id": "ribosome-zhipu-abc12345",
                "tasks_submitted": 1,
            }
            result = ribosome_dispatch(
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
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        result = ribosome_dispatch(action="dispatch", prompt="")
        assert not result.success

    def test_dispatch_default_provider_is_zhipu(self):
        """Default provider should be zhipu."""
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._start_workflow") as mock_start:
            mock_start.return_value = {
                "workflow_id": "ribosome-zhipu-abc12345",
                "tasks_submitted": 1,
            }
            ribosome_dispatch(action="dispatch", prompt="test task")
            call_args = mock_start.call_args
            specs = call_args[0][0] if call_args[0] else call_args[1].get("specs", [])
            assert any(s.get("provider") == "zhipu" for s in specs)


# ── batch dispatch ───────────────────────────────────────────────────────────


class TestBatchDispatch:
    """dispatch_batch() should start one workflow with multiple specs."""

    def test_batch_dispatch_multiple_tasks(self):
        """Batch dispatch starts one workflow with N specs."""
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        specs_json = json.dumps(
            [
                {"prompt": "Task A", "provider": "zhipu", "max_turns": 15},
                {"prompt": "Task B", "provider": "zhipu", "max_turns": 20},
            ]
        )
        with patch("metabolon.enzymes.ribosome_dispatch._start_workflow") as mock_start:
            mock_start.return_value = {
                "workflow_id": "ribosome-zhipu-batch123",
                "tasks_submitted": 2,
            }
            result = ribosome_dispatch(action="batch", specs=specs_json)
            assert result.data["tasks_submitted"] == 2

    def test_batch_dispatch_empty_specs_fails(self):
        """Empty specs list returns error."""
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        result = ribosome_dispatch(action="batch", specs="[]")
        assert not result.success


# ── status action ────────────────────────────────────────────────────────────


class TestStatus:
    """status() should query a workflow by ID and return its state."""

    def test_status_returns_workflow_info(self):
        """status with valid workflow_id returns state."""
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._get_workflow_status") as mock_status:
            mock_status.return_value = {
                "workflow_id": "ribosome-zhipu-abc12345",
                "status": "COMPLETED",
                "result": {"total": 1, "approved": 1},
            }
            result = ribosome_dispatch(action="status", workflow_id="ribosome-zhipu-abc12345")
            assert result.data["status"] == "COMPLETED"

    def test_status_requires_workflow_id(self):
        """status without workflow_id returns error."""
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        result = ribosome_dispatch(action="status")
        assert not result.success


# ── list action ──────────────────────────────────────────────────────────────


class TestList:
    """list() should return recent workflows."""

    def test_list_returns_workflows(self):
        """list returns array of recent workflows."""
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._list_workflows") as mock_list:
            mock_list.return_value = [
                {"workflow_id": "ribosome-zhipu-abc", "status": "COMPLETED"},
                {"workflow_id": "ribosome-zhipu-def", "status": "RUNNING"},
            ]
            result = ribosome_dispatch(action="list", limit=10)
            assert len(result.data["workflows"]) == 2

    def test_list_empty(self):
        """list with no workflows returns empty array."""
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._list_workflows") as mock_list:
            mock_list.return_value = []
            result = ribosome_dispatch(action="list")
            assert result.data["workflows"] == []


# ── cancel action ────────────────────────────────────────────────────────────


class TestCancel:
    """cancel() should terminate a running workflow."""

    def test_cancel_workflow(self):
        """cancel with valid workflow_id succeeds."""
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._cancel_workflow") as mock_cancel:
            mock_cancel.return_value = True
            result = ribosome_dispatch(action="cancel", workflow_id="ribosome-zhipu-abc12345")
            assert result.output
            mock_cancel.assert_called_once_with("ribosome-zhipu-abc12345")

    def test_cancel_requires_workflow_id(self):
        """cancel without workflow_id returns error."""
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        result = ribosome_dispatch(action="cancel")
        assert not result.success


# ── temporal connection ──────────────────────────────────────────────────────


class TestTemporalConnection:
    """Connection helpers should target ganglion:7233."""

    def test_default_host(self):
        """Default Temporal host is ganglion:7233."""
        from metabolon.enzymes.ribosome_dispatch import TEMPORAL_HOST

        assert "7233" in TEMPORAL_HOST
        assert "ganglion" in TEMPORAL_HOST or "100.120.158.22" in TEMPORAL_HOST

    def test_host_configurable_via_env(self, monkeypatch):
        """TEMPORAL_HOST env var overrides default."""
        import importlib

        import metabolon.enzymes.ribosome_dispatch as mod

        monkeypatch.setenv("TEMPORAL_HOST", "localhost:7233")
        importlib.reload(mod)
        assert mod.TEMPORAL_HOST == "localhost:7233"
        # Restore original state so other tests see the real default
        monkeypatch.delenv("TEMPORAL_HOST")
        importlib.reload(mod)


# ── running / failed convenience actions ────────────────────────────────────


class TestRunning:
    """running action should filter to RUNNING workflows only."""

    def test_running_returns_only_running(self):
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._list_workflows") as mock_list:
            mock_list.return_value = [
                {"workflow_id": "ribosome-zhipu-aaa", "status": "RUNNING"},
            ]
            result = ribosome_dispatch(action="running")
            assert "1 running" in result.output
            mock_list.assert_called_once_with(limit=10, status="Running")


class TestFailed:
    """failed action should filter to FAILED workflows only."""

    def test_failed_returns_only_failed(self):
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._list_workflows") as mock_list:
            mock_list.return_value = []
            result = ribosome_dispatch(action="failed")
            assert "0 failed" in result.output
            mock_list.assert_called_once_with(limit=10, status="Failed")


class TestListFilters:
    """list action should support status_filter and provider params."""

    def test_list_with_status_filter(self):
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._list_workflows") as mock_list:
            mock_list.return_value = []
            ribosome_dispatch(action="list", status_filter="Completed")
            mock_list.assert_called_once_with(limit=10, status="Completed", provider="")

    def test_list_with_provider_filter(self):
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._list_workflows") as mock_list:
            mock_list.return_value = []
            ribosome_dispatch(action="list", provider="volcano")
            mock_list.assert_called_once_with(limit=10, status="", provider="volcano")


# ── result action ───────────────────────────────────────────────────────────


class TestResult:
    """result action should return full workflow output."""

    def test_result_completed(self):
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._get_workflow_result") as mock_res:
            mock_res.return_value = {
                "workflow_id": "ribosome-zhipu-aaa",
                "status": "COMPLETED",
                "result": {"total": 1, "approved": 1},
            }
            result = ribosome_dispatch(action="result", workflow_id="ribosome-zhipu-aaa")
            assert "completed" in result.output

    def test_result_not_done(self):
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._get_workflow_result") as mock_res:
            mock_res.return_value = {
                "workflow_id": "ribosome-zhipu-bbb",
                "status": "RUNNING",
                "result": None,
            }
            result = ribosome_dispatch(action="result", workflow_id="ribosome-zhipu-bbb")
            assert "RUNNING" in result.output

    def test_result_requires_workflow_id(self):
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        result = ribosome_dispatch(action="result")
        assert not result.success


# ── approve / reject actions ────────────────────────────────────────────────


class TestSignals:
    """approve/reject should send signals to workflows."""

    def test_approve_sends_signal(self):
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._signal_workflow") as mock_sig:
            mock_sig.return_value = True
            result = ribosome_dispatch(action="approve", workflow_id="ribosome-zhipu-aaa")
            assert "approve" in result.output
            mock_sig.assert_called_once_with("ribosome-zhipu-aaa", "approve")

    def test_reject_sends_signal(self):
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        with patch("metabolon.enzymes.ribosome_dispatch._signal_workflow") as mock_sig:
            mock_sig.return_value = True
            result = ribosome_dispatch(action="reject", workflow_id="ribosome-zhipu-aaa")
            assert "reject" in result.output

    def test_signal_requires_workflow_id(self):
        from metabolon.enzymes.ribosome_dispatch import ribosome_dispatch

        result = ribosome_dispatch(action="approve")
        assert not result.success
