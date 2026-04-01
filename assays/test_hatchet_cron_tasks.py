from __future__ import annotations

"""Tests for cron-triggered Hatchet tasks (golem-requeue, golem-health)."""

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

WORKER_PATH = str(Path.home() / "germline/effectors/hatchet-golem/worker.py")


def _make_mock_hatchet():
    """Build a mock Hatchet with capturable .task() and .rate_limits."""
    mock_hatchet = MagicMock()
    mock_hatchet.rate_limits = MagicMock()
    mock_hatchet.task.side_effect = lambda **kw: lambda fn: fn
    return mock_hatchet


def _exec_worker(mock_hatchet):
    """Exec the worker module with a mocked Hatchet and return the namespace."""
    ns: dict = {"__name__": "worker", "__file__": WORKER_PATH}
    with patch("hatchet_sdk.Hatchet", return_value=mock_hatchet):
        exec(open(WORKER_PATH).read(), ns)
    return ns


def _capture_task_calls():
    """Load worker and capture the kwargs passed to each @hatchet.task call."""
    decorator_calls: list[dict] = []

    def capture_task(**kw):
        decorator_calls.append(kw)
        return lambda fn: fn

    mock_hatchet = MagicMock()
    mock_hatchet.task = capture_task
    mock_hatchet.rate_limits = MagicMock()
    _exec_worker(mock_hatchet)
    return decorator_calls


# ── Task registration tests ─────────────────────────────────────────────


def test_seven_tasks_registered():
    """7 tasks total: 4 providers via @task + zhipu via @durable_task + 2 cron."""
    calls = _capture_task_calls()
    assert len(calls) == 6  # 4 provider + 2 cron (zhipu moved to durable_task)
    names = {c["name"] for c in calls}
    expected = {
        "golem-infini", "golem-volcano",
        "golem-gemini", "golem-codex",
        "golem-requeue", "golem-health",
    }
    assert names == expected


def test_golem_requeue_has_cron():
    """golem-requeue task has on_crons schedule."""
    calls = _capture_task_calls()
    rq = next(c for c in calls if c["name"] == "golem-requeue")
    assert rq["on_crons"] == ["*/30 * * * *"]


def test_golem_requeue_timeout():
    """golem-requeue has 5m execution timeout."""
    calls = _capture_task_calls()
    rq = next(c for c in calls if c["name"] == "golem-requeue")
    assert rq["execution_timeout"] == "5m"


def test_golem_health_has_cron():
    """golem-health task has on_crons schedule."""
    calls = _capture_task_calls()
    h = next(c for c in calls if c["name"] == "golem-health")
    assert h["on_crons"] == ["*/15 * * * *"]


def test_golem_health_timeout():
    """golem-health has 3m execution timeout."""
    calls = _capture_task_calls()
    h = next(c for c in calls if c["name"] == "golem-health")
    assert h["execution_timeout"] == "3m"


def test_cron_tasks_no_concurrency_limit():
    """Cron tasks should not have per-provider concurrency constraints."""
    calls = _capture_task_calls()
    for name in ("golem-requeue", "golem-health"):
        t = next(c for c in calls if c["name"] == name)
        assert "concurrency" not in t


def test_cron_tasks_no_rate_limits():
    """Cron tasks should not consume provider rate limits."""
    calls = _capture_task_calls()
    for name in ("golem-requeue", "golem-health"):
        t = next(c for c in calls if c["name"] == name)
        assert "rate_limits" not in t


# ── _count_pending tests ────────────────────────────────────────────────


class TestCountPending:
    def test_missing_file(self, tmp_path):
        ns = _exec_worker(_make_mock_hatchet())
        result = ns["_count_pending"](tmp_path / "nope.md")
        assert result == 0

    def test_empty_file(self, tmp_path):
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text("")
        result = ns["_count_pending"](qf)
        assert result == 0

    def test_only_pending(self, tmp_path):
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text(textwrap.dedent("""\
            - [ ] `golem --provider zhipu "task A"`
            - [ ] `golem --provider volcano "task B"`
        """))
        result = ns["_count_pending"](qf)
        assert result == 2

    def test_high_priority_counted(self, tmp_path):
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text('- [!!] `golem --provider zhipu "urgent"`\n')
        result = ns["_count_pending"](qf)
        assert result == 1

    def test_mixed_pending_and_done(self, tmp_path):
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text(textwrap.dedent("""\
            - [ ] `golem --provider zhipu "pending"`
            - [x] `golem --provider zhipu "done"`
            - [!] `golem --provider zhipu "failed"`
            - [!!] `golem --provider zhipu "urgent"`
        """))
        result = ns["_count_pending"](qf)
        assert result == 2  # only [ ] and [!!]

    def test_lines_without_backticks_ignored(self, tmp_path):
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text("- [ ] This is a plain text task without backticks\n")
        result = ns["_count_pending"](qf)
        assert result == 0

    def test_no_done_counted(self, tmp_path):
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text(textwrap.dedent("""\
            - [x] `golem --provider zhipu "done A"`
            - [x] `golem --provider zhipu "done B"`
        """))
        result = ns["_count_pending"](qf)
        assert result == 0


# ── _auto_requeue tests ─────────────────────────────────────────────────


class TestAutoRequeue:
    def test_skips_when_enough_pending(self, tmp_path):
        """Returns 0 when pending count >= min_pending."""
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        # Write 25 pending tasks (> threshold of 20)
        lines = [f'- [ ] `golem --provider zhipu "task {i}"`' for i in range(25)]
        qf.write_text("\n".join(lines) + "\n")
        result = ns["_auto_requeue"](min_pending=20, queue_file=qf)
        assert result == 0

    def test_generates_when_below_threshold(self, tmp_path):
        """Generates tasks when pending < threshold."""
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text(textwrap.dedent("""\
            # Queue
            ## Pending
            - [ ] `golem --provider zhipu "only task"`
            ## Done
        """))
        result = ns["_auto_requeue"](min_pending=20, queue_file=qf)
        assert result > 0

    def test_writes_tasks_to_queue(self, tmp_path):
        """Appended tasks are written to the queue file."""
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text(textwrap.dedent("""\
            # Queue
            ## Pending
            - [ ] `golem --provider zhipu "existing"`
            ## Done
        """))
        added = ns["_auto_requeue"](min_pending=20, queue_file=qf)
        assert added > 0
        text = qf.read_text()
        assert "### Auto-requeue" in text
        assert text.count("- [ ]") >= 2  # original + new

    def test_inserts_before_done_section(self, tmp_path):
        """New tasks go before ## Done, not after."""
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text(textwrap.dedent("""\
            # Queue
            ## Pending
            - [ ] `golem --provider zhipu "existing"`
            ## Done
            - [x] `golem --provider zhipu "old"`
        """))
        ns["_auto_requeue"](min_pending=20, queue_file=qf)
        lines = qf.read_text().splitlines()
        done_idx = next(i for i, l in enumerate(lines) if l.strip() == "## Done")
        # Something should appear between pending and done (the header + tasks)
        requeue_idx = next(
            (i for i, l in enumerate(lines) if "Auto-requeue" in l),
            None,
        )
        assert requeue_idx is not None
        assert requeue_idx < done_idx

    def test_creates_queue_if_missing(self, tmp_path):
        """Creates queue file if it doesn't exist."""
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "new_queue.md"
        assert not qf.exists()
        result = ns["_auto_requeue"](min_pending=20, queue_file=qf)
        assert result > 0
        assert qf.exists()

    def test_returns_count_of_added_tasks(self, tmp_path):
        """Return value equals number of task lines added."""
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text("# Queue\n\n## Done\n")
        added = ns["_auto_requeue"](min_pending=20, queue_file=qf)
        text = qf.read_text()
        # Count lines matching the task pattern (excluding header)
        task_lines = [
            l for l in text.splitlines()
            if l.strip().startswith("- [ ] `golem")
        ]
        assert len(task_lines) == added

    def test_generated_tasks_have_provider(self, tmp_path):
        """Each generated task includes --provider flag."""
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text("# Queue\n\n## Done\n")
        ns["_auto_requeue"](min_pending=20, queue_file=qf)
        text = qf.read_text()
        task_lines = [
            l for l in text.splitlines()
            if l.strip().startswith("- [ ] `golem")
        ]
        for tl in task_lines:
            assert "--provider" in tl

    def test_generated_tasks_have_max_turns(self, tmp_path):
        """Each generated task includes --max-turns flag."""
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text("# Queue\n\n## Done\n")
        ns["_auto_requeue"](min_pending=20, queue_file=qf)
        text = qf.read_text()
        task_lines = [
            l for l in text.splitlines()
            if l.strip().startswith("- [ ] `golem")
        ]
        for tl in task_lines:
            assert "--max-turns" in tl


# ── golem_requeue task function tests ───────────────────────────────────


class TestGolemRequeueTask:
    def test_returns_pending_count_and_added(self, tmp_path):
        """Task returns dict with pending_count and added keys."""
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text(textwrap.dedent("""\
            # Queue
            ## Pending
            - [ ] `golem --provider zhipu "task A"`
            - [ ] `golem --provider zhipu "task B"`
            ## Done
        """))
        # Override QUEUE_FILE in namespace so _count_pending uses it
        ns["QUEUE_FILE"] = qf
        result = ns["golem_requeue"]({}, {})
        assert "pending_count" in result
        assert "added" in result
        assert isinstance(result["pending_count"], int)
        assert isinstance(result["added"], int)

    def test_added_is_zero_when_enough_pending(self, tmp_path):
        """No tasks added when queue already has enough."""
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        lines = [f'- [ ] `golem --provider zhipu "task {i}"`' for i in range(25)]
        qf.write_text("\n".join(lines) + "\n")
        ns["QUEUE_FILE"] = qf
        result = ns["golem_requeue"]({}, {})
        assert result["added"] == 0

    def test_added_positive_when_low(self, tmp_path):
        """Tasks are added when queue is low."""
        ns = _exec_worker(_make_mock_hatchet())
        qf = tmp_path / "queue.md"
        qf.write_text('- [ ] `golem --provider zhipu "only one"`\n')
        ns["QUEUE_FILE"] = qf
        result = ns["golem_requeue"]({}, {})
        assert result["added"] > 0
        assert result["pending_count"] > 1


# ── golem_health task function tests ────────────────────────────────────


class TestGolemHealthTask:
    def test_returns_success_on_zero_exit(self):
        """Returns success dict when health script exits 0."""
        ns = _exec_worker(_make_mock_hatchet())
        mock_proc = MagicMock(returncode=0, stdout="all systems go", stderr="")
        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = mock_proc
        mock_subprocess.TimeoutExpired = Exception
        ns["subprocess"] = mock_subprocess
        result = ns["golem_health"]({}, {})
        assert result["success"] is True
        assert result["exit_code"] == 0
        assert "all systems go" in result["output"]

    def test_returns_success_on_exit_two(self):
        """Exit code 2 (critical) is also logged as success (not a crash)."""
        ns = _exec_worker(_make_mock_hatchet())
        mock_proc = MagicMock(returncode=2, stdout="CRITICAL: disk full", stderr="")
        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = mock_proc
        mock_subprocess.TimeoutExpired = Exception
        ns["subprocess"] = mock_subprocess
        result = ns["golem_health"]({}, {})
        assert result["success"] is True
        assert result["exit_code"] == 2

    def test_returns_failure_on_nonzero_exit(self):
        """Non-zero, non-2 exit code is not success."""
        ns = _exec_worker(_make_mock_hatchet())
        mock_proc = MagicMock(returncode=1, stdout="warning", stderr="err")
        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = mock_proc
        mock_subprocess.TimeoutExpired = Exception
        ns["subprocess"] = mock_subprocess
        result = ns["golem_health"]({}, {})
        assert result["success"] is False
        assert result["exit_code"] == 1

    def test_handles_timeout(self):
        """Returns error dict on timeout."""
        ns = _exec_worker(_make_mock_hatchet())
        mock_subprocess = MagicMock()
        mock_subprocess.TimeoutExpired = type("TimeoutExpired", (Exception,), {})
        mock_subprocess.run.side_effect = mock_subprocess.TimeoutExpired()
        ns["subprocess"] = mock_subprocess
        result = ns["golem_health"]({}, {})
        assert result["success"] is False
        assert result["exit_code"] == -1
        assert result["error"] == "timeout"

    def test_handles_exception(self):
        """Returns error dict on generic exception."""
        ns = _exec_worker(_make_mock_hatchet())
        mock_subprocess = MagicMock()
        mock_subprocess.TimeoutExpired = type("TimeoutExpired", (Exception,), {})
        mock_subprocess.run.side_effect = FileNotFoundError("script missing")
        ns["subprocess"] = mock_subprocess
        result = ns["golem_health"]({}, {})
        assert result["success"] is False
        assert result["exit_code"] == -1
        assert "script missing" in result["error"]

    def test_truncates_long_output(self):
        """Output is truncated to 2000 chars."""
        ns = _exec_worker(_make_mock_hatchet())
        mock_proc = MagicMock(returncode=0, stdout="x" * 5000, stderr="")
        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = mock_proc
        mock_subprocess.TimeoutExpired = Exception
        ns["subprocess"] = mock_subprocess
        result = ns["golem_health"]({}, {})
        assert len(result["output"]) <= 2000

    def test_calls_correct_script(self):
        """Invokes gemmule-health with --daemon flag."""
        ns = _exec_worker(_make_mock_hatchet())
        mock_proc = MagicMock(returncode=0, stdout="ok", stderr="")
        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = mock_proc
        mock_subprocess.TimeoutExpired = Exception
        ns["subprocess"] = mock_subprocess
        ns["golem_health"]({}, {})
        call_args = mock_subprocess.run.call_args
        cmd = call_args[0][0]
        assert "gemmule-health" in cmd[1]
        assert "--daemon" in cmd

    def test_result_has_expected_keys(self):
        """Result dict has all expected keys."""
        ns = _exec_worker(_make_mock_hatchet())
        mock_proc = MagicMock(returncode=0, stdout="ok", stderr="")
        mock_subprocess = MagicMock()
        mock_subprocess.run.return_value = mock_proc
        mock_subprocess.TimeoutExpired = Exception
        ns["subprocess"] = mock_subprocess
        result = ns["golem_health"]({}, {})
        assert "exit_code" in result
        assert "output" in result
        assert "success" in result


# ── Worker registration tests ───────────────────────────────────────────


class TestWorkerRegistration:
    def test_main_registers_all_tasks(self):
        """main() passes all 7 tasks to hatchet.worker()."""
        mock_hatchet = _make_mock_hatchet()
        mock_worker = MagicMock()
        mock_hatchet.worker.return_value = mock_worker
        ns = _exec_worker(mock_hatchet)
        ns["main"]()
        mock_hatchet.worker.assert_called_once()
        call_kwargs = mock_hatchet.worker.call_args
        workflows = call_kwargs[1]["workflows"] if "workflows" in call_kwargs[1] else call_kwargs[0][1]
        assert len(workflows) == 7  # 5 providers + requeue + health

    def test_worker_name_is_golem_worker(self):
        """Worker is named 'golem-worker'."""
        mock_hatchet = _make_mock_hatchet()
        mock_worker = MagicMock()
        mock_hatchet.worker.return_value = mock_worker
        ns = _exec_worker(mock_hatchet)
        ns["main"]()
        call_args = mock_hatchet.worker.call_args
        assert call_args[0][0] == "golem-worker" or call_args[1].get("name") == "golem-worker" or "golem-worker" in str(call_args)


# ── REQUEUE_THRESHOLD constant test ─────────────────────────────────────


def test_requeue_threshold_is_twenty():
    """REQUEUE_THRESHOLD constant is 20."""
    ns = _exec_worker(_make_mock_hatchet())
    assert ns["REQUEUE_THRESHOLD"] == 20


def test_constants_define_health_script():
    """GEMMULE_HEALTH_SCRIPT constant points to gemmule-health."""
    ns = _exec_worker(_make_mock_hatchet())
    assert "gemmule-health" in str(ns["GEMMULE_HEALTH_SCRIPT"])
