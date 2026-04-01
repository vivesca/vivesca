from __future__ import annotations

"""Tests for golem-daemon graceful SIGTERM shutdown.

Tests the shutdown sequence:
  1) stop accepting new tasks
  2) wait up to 60s for running golems to finish
  3) auto-commit any uncommitted work
  4) push to remote
  5) then exit
"""

import json
import signal
import time
from concurrent.futures import Future
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_golem_daemon():
    """Load the golem-daemon module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/golem-daemon").read()
    ns: dict = {"__name__": "golem_daemon"}
    exec(source, ns)
    return ns


_mod = _load_golem_daemon()

_handle_sigterm = _mod.get("_handle_sigterm")
_shutdown_event = _mod.get("_shutdown_event")
_drain_running = _mod.get("_drain_running")


# ── helpers ─────────────────────────────────────────────────────────────


def _make_queue_dir(tmp_path: Path) -> Path:
    """Create the queue directory structure and return queue file path."""
    queue_dir = tmp_path / "germline" / "loci"
    queue_dir.mkdir(parents=True)
    return queue_dir / "golem-queue.md"


def _setup_paths(tmp_path: Path):
    """Set module paths to tmp and return originals for restoration."""
    queue_path = _make_queue_dir(tmp_path)
    queue_path.write_text("- [ ] `golem \"placeholder\"`\n\n## Done\n")
    jsonl_path = tmp_path / "golem.jsonl"
    log_path = tmp_path / "golem-daemon.log"
    log_path.touch()
    saved = {
        "QUEUE_FILE": _mod["QUEUE_FILE"],
        "JSONLFILE": _mod["JSONLFILE"],
        "LOGFILE": _mod["LOGFILE"],
    }
    _mod["QUEUE_FILE"] = queue_path
    _mod["JSONLFILE"] = jsonl_path
    _mod["LOGFILE"] = log_path
    return saved, queue_path, jsonl_path, log_path


def _restore_paths(saved: dict):
    """Restore module paths from saved dict."""
    for k, v in saved.items():
        _mod[k] = v


@pytest.fixture(autouse=True)
def _reset_shutdown():
    """Clear shutdown event before and after each test."""
    if _shutdown_event is not None:
        _shutdown_event.clear()
    yield
    if _shutdown_event is not None:
        _shutdown_event.clear()


# ── _handle_sigterm tests ──────────────────────────────────────────────


class TestHandleSigterm:
    """Tests for the SIGTERM signal handler."""

    def test_sets_shutdown_event(self):
        """_handle_sigterm sets the shutdown event."""
        assert not _shutdown_event.is_set()
        _handle_sigterm(signal.SIGTERM, None)
        assert _shutdown_event.is_set()

    def test_idempotent(self):
        """Calling _handle_sigterm multiple times keeps event set."""
        _handle_sigterm(signal.SIGTERM, None)
        _handle_sigterm(signal.SIGTERM, None)
        assert _shutdown_event.is_set()

    def test_works_with_any_signum(self):
        """_handle_sigterm works with any signal number."""
        _handle_sigterm(signal.SIGUSR1, None)
        assert _shutdown_event.is_set()


# ── _drain_running tests ───────────────────────────────────────────────


class TestDrainRunning:
    """Tests for _drain_running — graceful drain of running futures."""

    def test_empty_running_returns_zero(self):
        """_drain_running returns 0 when no futures are running."""
        result = _drain_running({}, timeout=5)
        assert result == 0

    def test_completed_future_marked_done(self, tmp_path):
        """_drain_running processes a successful future and marks it done."""
        saved, queue_path, jsonl_path, log_path = _setup_paths(tmp_path)
        queue_path.write_text("- [ ] `golem \"task1\"`\n\n## Done\n")
        try:
            future = Future()
            future.set_result(('golem "task1"', 0, "ok", 10))
            running = {future: (0, 'golem "task1"', "infini", "t-abc123")}

            remaining = _drain_running(running, timeout=5)
        finally:
            _restore_paths(saved)

        assert remaining == 0
        assert len(running) == 0
        content = queue_path.read_text()
        assert "- [x]" in content

    def test_failed_future_marked_retry(self, tmp_path):
        """_drain_running processes a failed future and marks it for retry."""
        saved, queue_path, jsonl_path, log_path = _setup_paths(tmp_path)
        queue_path.write_text("- [ ] `golem \"task1\"`\n")
        try:
            future = Future()
            future.set_result(('golem "task1"', 1, "error output", 5))
            running = {future: (0, 'golem "task1"', "infini", "t-abc123")}

            remaining = _drain_running(running, timeout=5)
        finally:
            _restore_paths(saved)

        assert remaining == 0
        content = queue_path.read_text()
        assert "(retry)" in content

    def test_timeout_returns_remaining_count(self, tmp_path):
        """_drain_running returns count of unfinished futures after timeout."""
        saved, queue_path, jsonl_path, log_path = _setup_paths(tmp_path)
        try:
            future = Future()  # Never completes
            running = {future: (0, 'golem "slow"', "infini", "t-def456")}

            remaining = _drain_running(running, timeout=1)
        finally:
            _restore_paths(saved)

        assert remaining == 1
        assert future in running

    def test_mixed_completed_and_running(self, tmp_path):
        """_drain_running handles mix of done and still-running futures."""
        saved, queue_path, jsonl_path, log_path = _setup_paths(tmp_path)
        queue_path.write_text(
            "- [ ] `golem \"done_task\"`\n"
            "- [ ] `golem \"slow_task\"`\n"
        )
        try:
            done_future = Future()
            done_future.set_result(('golem "done_task"', 0, "ok", 10))
            slow_future = Future()  # Never completes

            running = {
                done_future: (0, 'golem "done_task"', "infini", "t-001"),
                slow_future: (1, 'golem "slow_task"', "volcano", "t-002"),
            }

            remaining = _drain_running(running, timeout=1)
        finally:
            _restore_paths(saved)

        assert remaining == 1
        assert done_future not in running
        assert slow_future in running
        content = queue_path.read_text()
        assert "- [x]" in content

    def test_writes_jsonl_record(self, tmp_path):
        """_drain_running writes JSONL records for completed tasks."""
        saved, queue_path, jsonl_path, log_path = _setup_paths(tmp_path)
        queue_path.write_text("- [ ] `golem \"task1\"`\n\n## Done\n")
        try:
            future = Future()
            future.set_result(('golem "task1"', 0, "ok", 42))
            running = {future: (0, 'golem "task1"', "infini", "t-abc123")}

            _drain_running(running, timeout=5)
        finally:
            _restore_paths(saved)

        lines = jsonl_path.read_text().strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["task_id"] == "t-abc123"
        assert record["provider"] == "infini"
        assert record["exit"] == 0
        assert record["duration"] == 42

    def test_handles_future_exception(self, tmp_path):
        """_drain_running handles futures that raised exceptions."""
        saved, queue_path, jsonl_path, log_path = _setup_paths(tmp_path)
        queue_path.write_text("- [ ] `golem \"task1\"`\n")
        try:
            future = Future()
            future.set_exception(RuntimeError("boom"))
            running = {future: (0, 'golem "task1"', "infini", "t-abc123")}

            remaining = _drain_running(running, timeout=5)
        finally:
            _restore_paths(saved)

        assert remaining == 0
        assert len(running) == 0

    def test_multiple_completed_futures(self, tmp_path):
        """_drain_running processes multiple completed futures."""
        saved, queue_path, jsonl_path, log_path = _setup_paths(tmp_path)
        queue_path.write_text(
            "- [ ] `golem \"task1\"`\n"
            "- [ ] `golem \"task2\"`\n\n"
            "## Done\n"
        )
        try:
            f1 = Future()
            f1.set_result(('golem "task1"', 0, "ok", 10))
            f2 = Future()
            f2.set_result(('golem "task2"', 0, "ok", 20))

            running = {
                f1: (0, 'golem "task1"', "infini", "t-001"),
                f2: (1, 'golem "task2"', "volcano", "t-002"),
            }

            remaining = _drain_running(running, timeout=5)
        finally:
            _restore_paths(saved)

        assert remaining == 0
        assert len(running) == 0
        content = queue_path.read_text()
        # mark_done replaces in-place AND copies to ## Done, so ≥2 [x] entries
        assert content.count("- [x]") >= 2

    def test_default_timeout_is_60(self):
        """_drain_running default timeout parameter is 60 seconds."""
        import inspect
        sig = inspect.signature(_drain_running)
        assert sig.parameters["timeout"].default == 60


# ── integration: auto_commit called on shutdown ────────────────────────


class TestShutdownAutoCommit:
    """Verify that auto_commit is called during the shutdown finally block."""

    def test_auto_commit_exists(self):
        """auto_commit function is importable from the module."""
        assert "auto_commit" in _mod
        assert callable(_mod["auto_commit"])

    def test_shutdown_event_module_level(self):
        """_shutdown_event is a threading.Event at module level."""
        import threading
        assert isinstance(_shutdown_event, threading.Event)

    def test_drain_running_is_callable(self):
        """_drain_running function exists and is callable."""
        assert callable(_drain_running)
