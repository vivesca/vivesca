"""Tests for sortase watch command improvements."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from metabolon.sortase.cli import main


def _make_plan(directory: Path, name: str, content: str = "# Plan\nDo the thing.") -> Path:
    """Create a plan file in the watch directory."""
    plan_path = directory / name
    plan_path.write_text(content, encoding="utf-8")
    return plan_path


def test_watch_moves_done_on_success(tmp_path: Path) -> None:
    """Successful plans move to done/ subdirectory."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".git").mkdir()  # make it a git repo for worktree checks

    _make_plan(watch_dir, "plan-a.md")

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.task_name = "plan-a"
    mock_result.tool = "droid"
    mock_result.attempts = [MagicMock(duration_s=5.0)]
    mock_result.output = "done"

    runner = CliRunner()
    with (
        patch("metabolon.sortase.cli.decompose_plan", return_value=[MagicMock(name="plan-a", description="do stuff")]),
        patch("metabolon.sortase.cli.route_description", return_value=MagicMock(tool="droid")),
        patch("metabolon.sortase.cli.execute_tasks", return_value=[mock_result]),
        patch("time.sleep", side_effect=KeyboardInterrupt),
    ):
        result = runner.invoke(
            main,
            ["watch", str(watch_dir), "-p", str(project_dir), "--interval", "5"],
            catch_exceptions=False,
        )

    done_dir = watch_dir / "done"
    assert done_dir.exists()
    assert (done_dir / "plan-a.md").exists()
    assert not (watch_dir / "plan-a.md").exists()


def test_watch_moves_failed_on_error(tmp_path: Path) -> None:
    """Failed plans move to failed/ subdirectory."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    _make_plan(watch_dir, "plan-b.md")

    mock_result = MagicMock()
    mock_result.success = False
    mock_result.task_name = "plan-b"
    mock_result.tool = "droid"
    mock_result.attempts = [MagicMock(duration_s=10.0)]
    mock_result.output = "error"

    runner = CliRunner()
    with (
        patch("metabolon.sortase.cli.decompose_plan", return_value=[MagicMock(name="plan-b", description="do stuff")]),
        patch("metabolon.sortase.cli.route_description", return_value=MagicMock(tool="droid")),
        patch("metabolon.sortase.cli.execute_tasks", return_value=[mock_result]),
        patch("time.sleep", side_effect=KeyboardInterrupt),
    ):
        result = runner.invoke(
            main,
            ["watch", str(watch_dir), "-p", str(project_dir)],
            catch_exceptions=False,
        )

    failed_dir = watch_dir / "failed"
    assert failed_dir.exists()
    assert (failed_dir / "plan-b.md").exists()
    assert not (watch_dir / "plan-b.md").exists()


def test_watch_summary_line(tmp_path: Path) -> None:
    """Watch prints one-line summary per task."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    _make_plan(watch_dir, "plan-c.md")

    mock_attempt = MagicMock()
    mock_attempt.duration_s = 12.3
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.task_name = "plan-c"
    mock_result.tool = "droid"
    mock_result.attempts = [mock_attempt]
    mock_result.output = "done"

    runner = CliRunner()
    with (
        patch("metabolon.sortase.cli.decompose_plan", return_value=[MagicMock(name="plan-c", description="do stuff")]),
        patch("metabolon.sortase.cli.route_description", return_value=MagicMock(tool="droid")),
        patch("metabolon.sortase.cli.execute_tasks", return_value=[mock_result]),
        patch("time.sleep", side_effect=KeyboardInterrupt),
    ):
        result = runner.invoke(
            main,
            ["watch", str(watch_dir), "-p", str(project_dir)],
            catch_exceptions=False,
        )

    assert "TASK: plan-c.md | RESULT: success | DURATION: 12.3s" in result.output


def test_watch_summary_line_failure(tmp_path: Path) -> None:
    """Watch prints failure summary with correct duration."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    _make_plan(watch_dir, "plan-d.md")

    mock_attempt = MagicMock()
    mock_attempt.duration_s = 45.7
    mock_result = MagicMock()
    mock_result.success = False
    mock_result.task_name = "plan-d"
    mock_result.tool = "gemini"
    mock_result.attempts = [mock_attempt]
    mock_result.output = "failed"

    runner = CliRunner()
    with (
        patch("metabolon.sortase.cli.decompose_plan", return_value=[MagicMock(name="plan-d", description="do stuff")]),
        patch("metabolon.sortase.cli.route_description", return_value=MagicMock(tool="gemini")),
        patch("metabolon.sortase.cli.execute_tasks", return_value=[mock_result]),
        patch("time.sleep", side_effect=KeyboardInterrupt),
    ):
        result = runner.invoke(
            main,
            ["watch", str(watch_dir), "-p", str(project_dir)],
            catch_exceptions=False,
        )

    assert "TASK: plan-d.md | RESULT: fail | DURATION: 45.7s" in result.output


def test_watch_log_file(tmp_path: Path) -> None:
    """Watch writes per-task JSONL entries to --log-file."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    _make_plan(watch_dir, "plan-e.md")

    mock_attempt = MagicMock()
    mock_attempt.duration_s = 8.1
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.task_name = "plan-e"
    mock_result.tool = "droid"
    mock_result.attempts = [mock_attempt]
    mock_result.output = "done"
    mock_result.fallbacks = []

    log_file = tmp_path / "overnight.jsonl"

    runner = CliRunner()
    with (
        patch("metabolon.sortase.cli.decompose_plan", return_value=[MagicMock(name="plan-e", description="do stuff")]),
        patch("metabolon.sortase.cli.route_description", return_value=MagicMock(tool="droid")),
        patch("metabolon.sortase.cli.execute_tasks", return_value=[mock_result]),
        patch("time.sleep", side_effect=KeyboardInterrupt),
    ):
        result = runner.invoke(
            main,
            ["watch", str(watch_dir), "-p", str(project_dir), "--log-file", str(log_file)],
            catch_exceptions=False,
        )

    assert log_file.exists()
    entries = [json.loads(line) for line in log_file.read_text(encoding="utf-8").strip().splitlines()]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["plan"] == "plan-e.md"
    assert entry["success"] is True
    assert entry["duration_s"] == 8.1
    assert "timestamp" in entry


def test_watch_max_concurrent_flag(tmp_path: Path) -> None:
    """Watch accepts --max-concurrent and respects it."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    for i in range(4):
        _make_plan(watch_dir, f"plan-{i}.md")

    results_sequence = []
    call_log = []

    def fake_execute_tasks(tasks, project_dir_arg, tool_by_task, **kwargs):
        max_concurrent = kwargs.get("max_concurrent", 1)
        call_log.append({"n_tasks": len(tasks), "max_concurrent": max_concurrent})
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.task_name = tasks[0].name
        mock_result.tool = "droid"
        mock_result.attempts = [MagicMock(duration_s=1.0)]
        mock_result.output = "done"
        mock_result.fallbacks = []
        return [mock_result]

    runner = CliRunner()
    with (
        patch("metabolon.sortase.cli.decompose_plan", return_value=[MagicMock(name="plan-x", description="do stuff")]),
        patch("metabolon.sortase.cli.route_description", return_value=MagicMock(tool="droid")),
        patch("metabolon.sortase.cli.execute_tasks", side_effect=fake_execute_tasks),
        patch("time.sleep", side_effect=KeyboardInterrupt),
    ):
        result = runner.invoke(
            main,
            ["watch", str(watch_dir), "-p", str(project_dir), "--max-concurrent", "2"],
            catch_exceptions=False,
        )

    # All 4 plans should have been discovered and executed
    assert len(call_log) == 4


def test_watch_exception_moves_to_failed(tmp_path: Path) -> None:
    """Plans that raise exceptions move to failed/ and get logged."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    _make_plan(watch_dir, "plan-f.md")

    log_file = tmp_path / "overnight.jsonl"

    runner = CliRunner()
    with (
        patch("metabolon.sortase.cli.decompose_plan", side_effect=RuntimeError("boom")),
        patch("time.sleep", side_effect=KeyboardInterrupt),
    ):
        result = runner.invoke(
            main,
            ["watch", str(watch_dir), "-p", str(project_dir), "--log-file", str(log_file)],
            catch_exceptions=False,
        )

    failed_dir = watch_dir / "failed"
    assert (failed_dir / "plan-f.md").exists()
    # Exception path should still write log entry
    entries = [json.loads(line) for line in log_file.read_text(encoding="utf-8").strip().splitlines()]
    assert len(entries) == 1
    assert entries[0]["success"] is False
    assert "boom" in entries[0].get("error", "")


def test_watch_log_file_with_exception(tmp_path: Path) -> None:
    """Exception-based failures log error message and duration."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    _make_plan(watch_dir, "plan-g.md")
    log_file = tmp_path / "results.jsonl"

    runner = CliRunner()
    with (
        patch("metabolon.sortase.cli.decompose_plan", side_effect=ValueError("parse error")),
        patch("time.sleep", side_effect=KeyboardInterrupt),
    ):
        result = runner.invoke(
            main,
            ["watch", str(watch_dir), "-p", str(project_dir), "--log-file", str(log_file)],
            catch_exceptions=False,
        )

    entries = [json.loads(line) for line in log_file.read_text(encoding="utf-8").strip().splitlines()]
    entry = entries[0]
    assert entry["plan"] == "plan-g.md"
    assert entry["success"] is False
    assert "parse error" in entry["error"]


def test_watch_no_log_file_by_default(tmp_path: Path) -> None:
    """Without --log-file, no extra log file is created."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    _make_plan(watch_dir, "plan-h.md")

    mock_result = MagicMock()
    mock_result.success = True
    mock_result.task_name = "plan-h"
    mock_result.tool = "droid"
    mock_result.attempts = [MagicMock(duration_s=2.0)]
    mock_result.output = "done"

    runner = CliRunner()
    with (
        patch("metabolon.sortase.cli.decompose_plan", return_value=[MagicMock(name="plan-h", description="do stuff")]),
        patch("metabolon.sortase.cli.route_description", return_value=MagicMock(tool="droid")),
        patch("metabolon.sortase.cli.execute_tasks", return_value=[mock_result]),
        patch("time.sleep", side_effect=KeyboardInterrupt),
    ):
        result = runner.invoke(
            main,
            ["watch", str(watch_dir), "-p", str(project_dir)],
            catch_exceptions=False,
        )

    # Should not create any extra log files in tmp_path
    jsonl_files = list(tmp_path.glob("*.jsonl"))
    assert len(jsonl_files) == 0
