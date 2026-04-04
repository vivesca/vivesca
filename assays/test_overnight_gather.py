#!/usr/bin/env python3
from __future__ import annotations

"""Tests for overnight-gather effector — mocks all external file I/O."""


from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Execute the overnight-gather file directly
overnight_code = Path(str(Path.home() / "germline/effectors/overnight-gather")).read_text()
namespace = {}
exec(overnight_code, namespace)

# Extract all the functions/globals from the namespace
overnight = type("overnight_module", (), {})()
for key, value in namespace.items():
    if not key.startswith("__"):
        setattr(overnight, key, value)

# ---------------------------------------------------------------------------
# Test helper functions
# ---------------------------------------------------------------------------


def test_parse_run_timestamp_valid():
    """Test parse_run_timestamp correctly formats valid timestamp names."""
    result = overnight.parse_run_timestamp("2026-03-31-0930")
    assert result == "2026-03-31 09:30"

    result = overnight.parse_run_timestamp("2026-01-01-0000")
    assert result == "2026-01-01 00:00"


def test_parse_run_timestamp_invalid():
    """Test parse_run_timestamp returns original for invalid formats."""
    assert overnight.parse_run_timestamp("not-a-timestamp") == "not-a-timestamp"
    assert overnight.parse_run_timestamp("2026-03-31") == "2026-03-31"
    assert overnight.parse_run_timestamp("2026-03-31-123") == "2026-03-31-123"


def test_read_text_missing_file():
    """Test read_text returns empty string when file not found."""
    result = overnight.read_text(Path("/nonexistent/path/file.txt"))
    assert result == ""


def test_extract_flagged_lines_finds_matches():
    """Test extract_flagged_lines finds lines with error patterns."""
    text = """Normal line
Line with ERROR here
Another normal line
NEEDS_ATTENTION this requires attention
Another line with FAIL
"""
    result = overnight.extract_flagged_lines(text)
    assert len(result) == 3
    assert "ERROR" in result[0]
    assert "NEEDS_ATTENTION" in result[1]
    assert "FAIL" in result[2]


def test_extract_flagged_lines_no_matches():
    """Test extract_flagged_lines returns empty list when no matches."""
    text = "All lines\nare normal\nno flags here"
    result = overnight.extract_flagged_lines(text)
    assert result == []


def test_discover_runs_directory_missing():
    """Test discover_runs returns empty list when directory doesn't exist."""
    with patch("pathlib.Path.exists", return_value=False):
        result = overnight.discover_runs()
        assert result == []


def test_latest_run_no_runs_returns_none():
    """Test latest_run returns None when no runs found."""
    with patch.object(overnight, "discover_runs", return_value=[]):
        assert overnight.latest_run() is None


# ---------------------------------------------------------------------------
# Test queue metadata parsing
# ---------------------------------------------------------------------------


def test_parse_queue_metadata_missing_file():
    """Test parse_queue_metadata returns empty dict when file missing."""
    with patch("pathlib.Path.exists", return_value=False):
        result = overnight.parse_queue_metadata()
        assert result == {}


def test_parse_queue_metadata_parses_correctly():
    """Test parse_queue_metadata correctly parses the YAML queue."""
    content = """
# This is a comment
morning-dashboard:
  title: "Morning Dashboard Summary"
  author: "golem"
chromatin-check:
  title: Check chromatin integrity
  priority: high
empty-task:
"""
    with patch("pathlib.Path.exists", return_value=True):
        with patch("pathlib.Path.read_text", return_value=content):
            meta = overnight.parse_queue_metadata()
            assert "morning-dashboard" in meta
            assert "chromatin-check" in meta
            assert meta["morning-dashboard"]["title"] == "Morning Dashboard Summary"
            assert meta["morning-dashboard"]["author"] == "golem"
            assert meta["chromatin-check"]["title"] == "Check chromatin integrity"
            assert meta["chromatin-check"]["priority"] == "high"
            assert meta["empty-task"] == {}


# ---------------------------------------------------------------------------
# Test task summarization
# ---------------------------------------------------------------------------


def test_summarize_task_completed_no_errors():
    """Test summarize_task correctly identifies completed task with no errors."""
    # Create a more proper mock that handles __truediv__ correctly
    mock_task_dir = MagicMock()
    mock_task_dir.name = "test-task"

    # When task_dir / "stdout.txt" is accessed, return mock with correct read_text
    mock_stdout = MagicMock()
    mock_stdout.read_text.return_value = "All completed successfully\nEverything looks good"
    mock_stderr = MagicMock()
    mock_stderr.read_text.return_value = ""

    mock_task_dir.__truediv__.side_effect = lambda other: (
        mock_stdout if "stdout" in other else mock_stderr
    )

    result = overnight.summarize_task(mock_task_dir, {})
    assert result.name == "test-task"
    assert result.status == "completed"
    assert not result.has_errors
    assert not result.flagged
    assert len(result.flagged_lines) == 0


def test_summarize_task_with_errors():
    """Test summarize_task correctly identifies task with errors."""
    mock_task_dir = MagicMock()
    mock_task_dir.name = "test-task"

    mock_stdout = MagicMock()
    mock_stdout.read_text.return_value = ""
    mock_stderr = MagicMock()
    mock_stderr.read_text.return_value = "ERROR: Task failed to complete"

    mock_task_dir.__truediv__.side_effect = lambda other: (
        mock_stdout if "stdout" in other else mock_stderr
    )

    result = overnight.summarize_task(mock_task_dir, {})
    assert result.status == "has errors"
    assert result.has_errors
    assert result.flagged
    assert "ERROR" in result.flagged_lines[0]


def test_summarize_task_no_output():
    """Test summarize_task correctly identifies task with no output."""
    mock_task_dir = MagicMock()
    mock_task_dir.name = "test-task"

    mock_stdout = MagicMock()
    mock_stdout.read_text.return_value = ""
    mock_stderr = MagicMock()
    mock_stderr.read_text.return_value = ""

    mock_task_dir.__truediv__.side_effect = lambda other: (
        mock_stdout if "stdout" in other else mock_stderr
    )

    result = overnight.summarize_task(mock_task_dir, {})
    assert result.status == "no output"
    assert not result.has_errors


def test_summarize_task_extracts_metadata():
    """Test summarize_task includes metadata from queue."""
    mock_task_dir = MagicMock()
    mock_task_dir.name = "my-task"

    mock_stdout = MagicMock()
    mock_stdout.read_text.return_value = "Done"
    mock_stderr = MagicMock()
    mock_stderr.read_text.return_value = ""

    mock_task_dir.__truediv__.side_effect = lambda other: (
        mock_stdout if "stdout" in other else mock_stderr
    )

    metadata = {"my-task": {"title": "My Important Task"}}

    result = overnight.summarize_task(mock_task_dir, metadata)
    assert result.title == "My Important Task"


# ---------------------------------------------------------------------------
# Test status icons and rendering
# ---------------------------------------------------------------------------


def test_status_icon_completed_no_flags():
    """Test status_icon returns OK for completed clean task."""
    task = overnight.TaskSummary(
        name="test",
        title=None,
        status="completed",
        has_errors=False,
        flagged=False,
        flagged_lines=[],
        stdout="done",
        stderr="",
    )
    assert overnight.status_icon(task) == overnight.OK


def test_status_icon_flagged_returns_warn():
    """Test status_icon returns WARN when flagged or has errors."""
    task = overnight.TaskSummary(
        name="test",
        title=None,
        status="completed",
        has_errors=False,
        flagged=True,
        flagged_lines=[],
        stdout="done",
        stderr="",
    )
    assert overnight.status_icon(task) == overnight.WARN

    task2 = overnight.TaskSummary(
        name="test",
        title=None,
        status="completed",
        has_errors=True,
        flagged=False,
        flagged_lines=[],
        stdout="done",
        stderr="error",
    )
    assert overnight.status_icon(task2) == overnight.WARN


def test_render_task_label_with_title():
    """Test render_task_label includes title when present."""
    task = overnight.TaskSummary(
        name="test-task",
        title="Test Task",
        status="completed",
        has_errors=False,
        flagged=False,
        flagged_lines=[],
        stdout="",
        stderr="",
    )
    result = overnight.render_task_label(task)
    assert result == "test-task (Test Task)"


def test_render_task_label_no_title():
    """Test render_task_label just returns name when no title."""
    task = overnight.TaskSummary(
        name="test-task",
        title=None,
        status="completed",
        has_errors=False,
        flagged=False,
        flagged_lines=[],
        stdout="",
        stderr="",
    )
    result = overnight.render_task_label(task)
    assert result == "test-task"


# ---------------------------------------------------------------------------
# Test command argument parsing (smoke test)
# ---------------------------------------------------------------------------


def test_help_flag_exists():
    """Test that the parser has --help flag."""
    import sys

    original_argv = sys.argv
    try:
        sys.argv = ["overnight-gather", "--help"]
        with pytest.raises(SystemExit):
            overnight.main()
    finally:
        sys.argv = original_argv

    """Test that no command defaults to brief."""
    # We just need to test dispatch - we just care that cmd_brief was called
    with patch("argparse.ArgumentParser.parse_args") as mock_parser:
        args = MagicMock()
        args.command = None
        args.json = False
        mock_parser.return_value = args

        called = False

        def mock_cmd_brief(a):
            nonlocal called
            called = True
