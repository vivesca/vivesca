from __future__ import annotations

"""Tests for metabolon.organelles.gemmation — background AI agent job queue."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from metabolon.organelles.gemmation import (
    BACKENDS,
    RUNS_DIR,
    _build_cmd,
    _find_task,
    _full_prompt,
    _load_queue,
    _log_path,
    _output_dir,
    _prepend_coaching,
    _save_queue,
    _working_dir,
    cancel_task,
    get_results,
    list_tasks,
    run_task,
)

# ── fixtures ──────────────────────────────────────────────────────────────

SAMPLE_TASKS = [
    {
        "name": "alpha",
        "prompt": "do alpha things",
        "backend": "claude",
        "timeout": 300,
        "run_now": True,
        "enabled": True,
        "schedule": "daily",
    },
    {
        "name": "beta",
        "prompt": "do beta things",
        "backend": "opencode",
        "enabled": True,
    },
    {
        "name": "gamma",
        "prompt": "do gamma things",
        "backend": "gemini",
        "timeout": 120,
    },
]


@pytest.fixture
def tmp_queue(tmp_path):
    """Create a temporary YAML queue file with SAMPLE_TASKS."""
    q = tmp_path / "queue.yaml"
    q.write_text(yaml.dump({"tasks": SAMPLE_TASKS}, default_flow_style=False, sort_keys=False))
    return q


@pytest.fixture
def empty_queue(tmp_path):
    """Create an empty (missing) queue path."""
    return tmp_path / "nonexistent.yaml"


# ── _prepend_coaching ────────────────────────────────────────────────────


class TestPrependCoaching:
    def test_no_coaching_file_returns_prompt_unchanged(self, tmp_path):
        fake = tmp_path / "nope.md"
        with patch("metabolon.organelles.gemmation._COACHING_NOTES", fake):
            assert _prepend_coaching("hello world") == "hello world"

    def test_coaching_file_prepended(self, tmp_path):
        f = tmp_path / "coaching.md"
        f.write_text("---\nname: test\n---\nBe good.\n")
        with patch("metabolon.organelles.gemmation._COACHING_NOTES", f):
            result = _prepend_coaching("do task")
        assert result.startswith("Be good.")
        assert "---" in result
        assert "do task" in result

    def test_coaching_file_without_frontmatter(self, tmp_path):
        f = tmp_path / "coaching.md"
        f.write_text("Just plain notes.\n")
        with patch("metabolon.organelles.gemmation._COACHING_NOTES", f):
            result = _prepend_coaching("do task")
        assert "Just plain notes." in result
        assert "do task" in result

    def test_coaching_file_read_error_returns_prompt(self, tmp_path):
        f = tmp_path / "coaching.md"
        f.write_text("content")
        f.chmod(0o000)
        try:
            with patch("metabolon.organelles.gemmation._COACHING_NOTES", f):
                assert _prepend_coaching("do task") == "do task"
        finally:
            f.chmod(0o644)


# ── _load_queue ──────────────────────────────────────────────────────────


class TestLoadQueue:
    def test_loads_existing_queue(self, tmp_queue):
        tasks = _load_queue(tmp_queue)
        assert len(tasks) == 3
        assert tasks[0]["name"] == "alpha"
        assert tasks[1]["name"] == "beta"

    def test_missing_file_returns_empty(self, empty_queue):
        assert _load_queue(empty_queue) == []

    def test_empty_yaml_returns_empty(self, tmp_path):
        q = tmp_path / "empty.yaml"
        q.write_text("")
        assert _load_queue(q) == []

    def test_yaml_with_no_tasks_key_returns_empty(self, tmp_path):
        q = tmp_path / "notasks.yaml"
        q.write_text(yaml.dump({"other": [1, 2]}))
        assert _load_queue(q) == []

    def test_default_path_uses_queue_path(self, tmp_queue):
        with patch("metabolon.organelles.gemmation.QUEUE_PATH", tmp_queue):
            tasks = _load_queue()
        assert len(tasks) == 3


# ── _save_queue ──────────────────────────────────────────────────────────


class TestSaveQueue:
    def test_saves_and_roundtrips(self, tmp_path):
        q = tmp_path / "out.yaml"
        tasks = [{"name": "x", "backend": "claude"}]
        _save_queue(tasks, q)
        data = yaml.safe_load(q.read_text())
        assert data["tasks"] == tasks

    def test_creates_parent_dirs(self, tmp_path):
        q = tmp_path / "deep" / "nested" / "queue.yaml"
        _save_queue([{"name": "z"}], q)
        assert q.exists()

    def test_default_path(self, tmp_queue):
        with patch("metabolon.organelles.gemmation.QUEUE_PATH", tmp_queue):
            _save_queue([{"name": "w"}])
        tasks = _load_queue(tmp_queue)
        assert tasks[0]["name"] == "w"


# ── _find_task ───────────────────────────────────────────────────────────


class TestFindTask:
    def test_finds_existing_task(self):
        task = _find_task(SAMPLE_TASKS, "beta")
        assert task["name"] == "beta"
        assert task["backend"] == "opencode"

    def test_raises_on_missing_task(self):
        with pytest.raises(ValueError, match="Task 'nope' not found"):
            _find_task(SAMPLE_TASKS, "nope")

    def test_error_message_lists_available(self):
        with pytest.raises(ValueError, match="alpha, beta, gamma"):
            _find_task(SAMPLE_TASKS, "missing")


# ── _output_dir / _log_path ──────────────────────────────────────────────


class TestOutputPaths:
    @patch("metabolon.organelles.gemmation.datetime")
    def test_output_dir_uses_timestamp(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 1, 15, 9, 30)
        result = _output_dir("mytask")
        assert result == RUNS_DIR / "2026-01-15-0930" / "mytask"

    def test_log_path(self):
        result = _log_path("mytask")
        assert result == RUNS_DIR / "hot-mytask.log"


# ── _full_prompt ─────────────────────────────────────────────────────────


class TestFullPrompt:
    def test_includes_task_prompt(self):
        task = {"prompt": "Analyze the genome", "name": "t"}
        result = _full_prompt(task, Path("/out"))
        assert "Analyze the genome" in result

    def test_includes_output_dir(self):
        task = {"prompt": "p", "name": "t"}
        result = _full_prompt(task, Path("/data/run1"))
        assert "/data/run1" in result

    def test_includes_summary_instructions(self):
        task = {"prompt": "p", "name": "t"}
        result = _full_prompt(task, Path("/out"))
        assert "summary.md" in result
        assert "PASS/FAIL" in result


# ── _build_cmd ───────────────────────────────────────────────────────────


class TestBuildCmd:
    def _task(self, backend="opencode", **kw):
        return {"name": "test", "prompt": "do stuff", "backend": backend, **kw}

    def test_claude_backend(self):
        with patch("shutil.which", return_value="/usr/bin/claude"):
            cmd = _build_cmd(self._task("claude"), Path("/out"))
        assert cmd[0] == "/usr/bin/claude"
        assert "--dangerously-skip-permissions" in cmd
        assert "-p" in cmd

    def test_claude_fallback_path(self):
        with patch("shutil.which", return_value=None):
            cmd = _build_cmd(self._task("claude"), Path("/out"))
        expected = str(Path.home() / ".local/bin/claude")
        assert cmd[0] == expected

    def test_gemini_backend(self):
        cmd = _build_cmd(self._task("gemini"), Path("/out"))
        assert cmd[0] == "gemini"
        assert "--yolo" in cmd

    def test_codex_backend(self):
        cmd = _build_cmd(self._task("codex"), Path("/out"))
        assert cmd[0] == "codex"
        assert "exec" in cmd
        assert "--full-auto" in cmd

    def test_opencode_backend_uses_name_as_title(self):
        cmd = _build_cmd(self._task("opencode"), Path("/out"))
        assert cmd[0] == "opencode"
        assert "run" in cmd
        assert "test" in cmd  # name used as title

    def test_opencode_backend_uses_title_if_present(self):
        cmd = _build_cmd(self._task("opencode", title="My Title"), Path("/out"))
        assert "My Title" in cmd

    @patch("metabolon.organelles.gemmation._prepend_coaching", return_value="prompt+notes")
    def test_goose_backend_prepends_coaching(self, mock_pc):
        cmd = _build_cmd(self._task("goose"), Path("/out"))
        assert cmd[0] == "goose"
        assert cmd[-1] == "prompt+notes"
        mock_pc.assert_called_once()

    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError, match="Unknown backend"):
            _build_cmd(self._task("nonexistent"), Path("/out"))

    def test_default_backend_is_opencode(self):
        task = {"name": "t", "prompt": "p"}  # no backend key
        cmd = _build_cmd(task, Path("/out"))
        assert cmd[0] == "opencode"


# ── _working_dir ─────────────────────────────────────────────────────────


class TestWorkingDir:
    def test_explicit_working_dir(self):
        task = {"name": "t", "working_dir": "/tmp/project"}
        assert _working_dir(task) == Path("/tmp/project")

    def test_tilde_expansion(self):
        task = {"name": "t", "working_dir": "~/code"}
        result = _working_dir(task)
        assert str(result).startswith(str(Path.home()))

    def test_defaults_to_home(self):
        assert _working_dir({"name": "t"}) == Path.home()


# ── list_tasks ───────────────────────────────────────────────────────────


class TestListTasks:
    def test_empty_queue(self, empty_queue):
        assert list_tasks(empty_queue) == "No tasks in queue."

    def test_formats_task_table(self, tmp_queue):
        output = list_tasks(tmp_queue)
        assert "alpha" in output
        assert "beta" in output
        assert "gamma" in output
        assert "claude" in output
        assert "opencode" in output

    def test_hot_status_for_run_now(self, tmp_queue):
        output = list_tasks(tmp_queue)
        # alpha has run_now=True
        assert "hot" in output

    def test_timeout_displayed(self, tmp_queue):
        output = list_tasks(tmp_queue)
        assert "300s" in output

    def test_schedule_displayed(self, tmp_queue):
        output = list_tasks(tmp_queue)
        assert "daily" in output

    def test_header_line_present(self, tmp_queue):
        output = list_tasks(tmp_queue)
        assert "NAME" in output
        assert "BACKEND" in output
        assert "STATUS" in output


# ── cancel_task ──────────────────────────────────────────────────────────


class TestCancelTask:
    def test_cancels_existing_task(self, tmp_queue):
        result = cancel_task("alpha", tmp_queue)
        assert "Cancelled task 'alpha'" in result
        tasks = _load_queue(tmp_queue)
        t = _find_task(tasks, "alpha")
        assert t["enabled"] is False
        assert t["run_now"] is False

    def test_cancel_missing_task_raises(self, tmp_queue):
        with pytest.raises(ValueError):
            cancel_task("nonexistent", tmp_queue)

    def test_cancel_persists_to_disk(self, tmp_queue):
        cancel_task("alpha", tmp_queue)
        # Re-read from disk
        tasks = _load_queue(tmp_queue)
        t = _find_task(tasks, "alpha")
        assert t["enabled"] is False


# ── run_task ─────────────────────────────────────────────────────────────


class TestRunTask:
    """All tests patch subprocess.Popen and capture the class-level mock."""

    def test_dispatches_claude_task(self, tmp_queue, tmp_path):
        with (
            patch("metabolon.organelles.gemmation.subprocess.Popen") as popen_cls,
            patch("metabolon.organelles.gemmation.RUNS_DIR", tmp_path / "runs"),
            patch("metabolon.organelles.gemmation.datetime") as mock_dt,
        ):
            popen_cls.return_value.pid = 12345
            mock_dt.now.return_value = datetime(2026, 4, 1, 12, 0)
            result = run_task("alpha", tmp_queue)

        assert "Dispatched 'alpha'" in result
        assert "claude" in result
        assert "12345" in result
        popen_cls.assert_called_once()
        _, kwargs = popen_cls.call_args
        assert kwargs["start_new_session"] is True

    def test_dispatches_opencode_task(self, tmp_queue, tmp_path):
        with (
            patch("metabolon.organelles.gemmation.subprocess.Popen") as popen_cls,
            patch("metabolon.organelles.gemmation.RUNS_DIR", tmp_path / "runs"),
            patch("metabolon.organelles.gemmation.datetime") as mock_dt,
        ):
            popen_cls.return_value.pid = 99
            mock_dt.now.return_value = datetime(2026, 4, 1, 12, 0)
            result = run_task("beta", tmp_queue)

        assert "Dispatched 'beta'" in result
        assert "opencode" in result
        args, _ = popen_cls.call_args
        monitor_script = args[0][2]
        assert "opencode" in monitor_script

    def test_missing_task_raises(self, tmp_queue):
        with pytest.raises(ValueError):
            run_task("nonexistent", tmp_queue)

    def test_creates_output_dirs(self, tmp_queue, tmp_path):
        runs = tmp_path / "runs"
        with (
            patch("metabolon.organelles.gemmation.subprocess.Popen"),
            patch("metabolon.organelles.gemmation.RUNS_DIR", runs),
            patch("metabolon.organelles.gemmation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = datetime(2026, 4, 1, 12, 0)
            run_task("alpha", tmp_queue)

        assert (runs / "2026-04-01-1200" / "alpha").exists()

    def test_monitor_script_contains_paracrine_signal(self, tmp_queue, tmp_path):
        with (
            patch("metabolon.organelles.gemmation.subprocess.Popen") as popen_cls,
            patch("metabolon.organelles.gemmation.RUNS_DIR", tmp_path / "runs"),
            patch("metabolon.organelles.gemmation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = datetime(2026, 4, 1, 12, 0)
            run_task("alpha", tmp_queue)

        args, _ = popen_cls.call_args
        monitor_script = args[0][2]
        assert "emit_signal" in monitor_script
        assert "gemmation-alpha" in monitor_script

    def test_claude_env_sets_claudecode(self, tmp_queue, tmp_path):
        with (
            patch("metabolon.organelles.gemmation.subprocess.Popen") as popen_cls,
            patch("metabolon.organelles.gemmation.RUNS_DIR", tmp_path / "runs"),
            patch("metabolon.organelles.gemmation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = datetime(2026, 4, 1, 12, 0)
            run_task("alpha", tmp_queue)

        _, kwargs = popen_cls.call_args
        env = kwargs["env"]
        assert "CLAUDECODE" in env

    def test_opencode_env_sets_opencode_home(self, tmp_queue, tmp_path):
        with (
            patch("metabolon.organelles.gemmation.subprocess.Popen") as popen_cls,
            patch("metabolon.organelles.gemmation.RUNS_DIR", tmp_path / "runs"),
            patch("metabolon.organelles.gemmation.datetime") as mock_dt,
        ):
            mock_dt.now.return_value = datetime(2026, 4, 1, 12, 0)
            run_task("beta", tmp_queue)

        _, kwargs = popen_cls.call_args
        env = kwargs["env"]
        assert "OPENCODE_HOME" in env
        assert ".opencode-lean" in env["OPENCODE_HOME"]


# ── get_results ──────────────────────────────────────────────────────────


class TestGetResults:
    def test_no_results_dir(self, tmp_path):
        with patch("metabolon.organelles.gemmation.RUNS_DIR", tmp_path / "nope"):
            assert "No results found" in get_results()

    def test_list_all_results(self, tmp_path):
        runs = tmp_path / "runs"
        (runs / "2026-04-01-1200" / "alpha").mkdir(parents=True)
        (runs / "2026-04-01-1200" / "beta").mkdir(parents=True)
        with patch("metabolon.organelles.gemmation.RUNS_DIR", runs):
            result = get_results()
        assert "alpha" in result
        assert "beta" in result
        assert "Latest run: 2026-04-01-1200" in result

    def test_get_named_results_summary(self, tmp_path):
        runs = tmp_path / "runs"
        task_dir = runs / "2026-04-01-1200" / "alpha"
        task_dir.mkdir(parents=True)
        (task_dir / "summary.md").write_text("All tests passed.")
        with patch("metabolon.organelles.gemmation.RUNS_DIR", runs):
            result = get_results("alpha")
        assert "All tests passed." in result

    def test_get_named_results_report_fallback(self, tmp_path):
        runs = tmp_path / "runs"
        task_dir = runs / "2026-04-01-1200" / "alpha"
        task_dir.mkdir(parents=True)
        (task_dir / "report.md").write_text("Report content.")
        with patch("metabolon.organelles.gemmation.RUNS_DIR", runs):
            result = get_results("alpha")
        assert "Report content." in result

    def test_get_named_results_stdout_fallback(self, tmp_path):
        runs = tmp_path / "runs"
        task_dir = runs / "2026-04-01-1200" / "alpha"
        task_dir.mkdir(parents=True)
        (task_dir / "stdout.txt").write_text("stdout output.")
        with patch("metabolon.organelles.gemmation.RUNS_DIR", runs):
            result = get_results("alpha")
        assert "stdout output." in result

    def test_get_named_results_not_found(self, tmp_path):
        runs = tmp_path / "runs"
        (runs / "2026-04-01-1200" / "other").mkdir(parents=True)
        with patch("metabolon.organelles.gemmation.RUNS_DIR", runs):
            result = get_results("alpha")
        assert "No results found for 'alpha'" in result

    def test_skips_hot_log_files(self, tmp_path):
        runs = tmp_path / "runs"
        (runs / "2026-04-01-1200" / "alpha").mkdir(parents=True)
        (runs / "hot-alpha.log").write_text("log")
        with patch("metabolon.organelles.gemmation.RUNS_DIR", runs):
            result = get_results()
        assert "alpha" in result
        assert "hot" not in result.split("\n")[1]

    def test_uses_latest_run_dir(self, tmp_path):
        runs = tmp_path / "runs"
        (runs / "2026-04-01-1000" / "alpha").mkdir(parents=True)
        latest_dir = runs / "2026-04-01-1200" / "alpha"
        latest_dir.mkdir(parents=True)
        (latest_dir / "summary.md").write_text("Latest result.")
        with patch("metabolon.organelles.gemmation.RUNS_DIR", runs):
            result = get_results("alpha")
        assert "Latest result." in result

    def test_empty_results_dir(self, tmp_path):
        runs = tmp_path / "runs"
        runs.mkdir()
        with patch("metabolon.organelles.gemmation.RUNS_DIR", runs):
            result = get_results()
        assert "No results found" in result


# ── BACKENDS constant ────────────────────────────────────────────────────


class TestBackends:
    def test_backends_tuple_contains_expected(self):
        assert "claude" in BACKENDS
        assert "gemini" in BACKENDS
        assert "codex" in BACKENDS
        assert "opencode" in BACKENDS
        assert "goose" in BACKENDS
        assert len(BACKENDS) == 5
