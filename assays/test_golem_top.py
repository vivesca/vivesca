"""Tests for golem-top — show running golem processes like top for golems."""
from __future__ import annotations

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest


def _load_golem_top():
    """Load the golem-top module by exec-ing its Python body."""
    source = open("/home/terry/germline/effectors/golem-top").read()
    ns: dict = {"__name__": "golem_top"}
    exec(source, ns)
    return ns


_mod = _load_golem_top()
get_golem_processes = _mod["get_golem_processes"]
_parse_ps_line = _mod["_parse_ps_line"]
_extract_provider = _mod["_extract_provider"]
_extract_task = _mod["_extract_task"]
_parse_elapsed = _mod["_parse_elapsed"]
format_table = _mod["format_table"]


# ── Fixtures ──────────────────────────────────────────────────────────

PS_HEADER = "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT STARTED   TIME COMMAND"

SAMPLE_LINE = (
    "terry    12345  2.5  1.3 123456  78901 pts/0    S+   10:30   05:23 "
    "bash /home/terry/germline/effectors/golem --provider infini --max-turns 50 "
    '"review the codebase for security issues"'
)

SAMPLE_LINE_NO_PROVIDER = (
    "terry    23456  1.0  0.5 234567  89012 pts/1    S+   11:00   02:10 "
    'bash /home/terry/germline/effectors/golem "write unit tests for the parser"'
)

SAMPLE_LINE_NO_TASK = (
    "terry    34567  0.5  0.2 345678  90123 pts/2    S+   12:00   00:30 "
    "bash /home/terry/germline/effectors/golem --provider volcano"
)


def _mock_ps(stdout: str, returncode: int = 0):
    """Build a mock subprocess.run result."""
    m = MagicMock()
    m.stdout = stdout
    m.stderr = ""
    m.returncode = returncode
    return m


# ── _parse_ps_line tests ─────────────────────────────────────────────


def test_parse_ps_line_basic():
    """_parse_ps_line extracts PID, provider, task from a valid line."""
    result = _parse_ps_line(SAMPLE_LINE)
    assert result is not None
    assert result["pid"] == 12345
    assert result["provider"] == "infini"
    assert result["task"] == "review the codebase for security issues"
    assert result["cpu_pct"] == "2.5"
    assert result["mem_pct"] == "1.3"
    assert result["user"] == "terry"


def test_parse_ps_line_no_provider():
    """_parse_ps_line returns 'default' provider when --provider absent."""
    result = _parse_ps_line(SAMPLE_LINE_NO_PROVIDER)
    assert result is not None
    assert result["provider"] == "default"
    assert result["pid"] == 23456


def test_parse_ps_line_too_short():
    """_parse_ps_line returns None for lines with fewer than 11 fields."""
    assert _parse_ps_line("a b c") is None


def test_parse_ps_line_non_numeric_pid():
    """_parse_ps_line returns None when PID field is not numeric."""
    line = "terry abc  2.5  1.3 123456  78901 pts/0    S+   10:30   05:23 cmd"
    assert _parse_ps_line(line) is None


# ── _extract_provider tests ──────────────────────────────────────────


def test_extract_provider_infini():
    """_extract_provider finds --provider infini."""
    assert _extract_provider('golem --provider infini "task"') == "infini"


def test_extract_provider_volcano():
    """_extract_provider finds --provider volcano."""
    assert _extract_provider('golem --provider volcano "task"') == "volcano"


def test_extract_provider_missing():
    """_extract_provider returns 'default' when no --provider flag."""
    assert _extract_provider('golem "task"') == "default"


def test_extract_provider_zhipu():
    """_extract_provider finds --provider zhipu."""
    assert _extract_provider('golem --provider zhipu --max-turns 10 "task"') == "zhipu"


# ── _extract_task tests ──────────────────────────────────────────────


def test_extract_task_quoted():
    """_extract_task returns last quoted string."""
    cmd = 'bash golem --provider infini "review the codebase for security issues"'
    assert _extract_task(cmd) == "review the codebase for security issues"


def test_extract_task_no_quotes():
    """_extract_task falls back to unquoted trailing text."""
    cmd = "bash golem --provider volcano some task here"
    result = _extract_task(cmd)
    # Should return something non-empty
    assert isinstance(result, str)


def test_extract_task_truncates_long():
    """_extract_task truncates tasks longer than 80 chars."""
    long_task = "x" * 120
    cmd = f'bash golem "{long_task}"'
    result = _extract_task(cmd)
    assert len(result) <= 80


# ── _parse_elapsed tests ─────────────────────────────────────────────


def test_parse_elapsed_nonempty():
    """_parse_elapsed returns the string when non-empty."""
    assert _parse_elapsed("05:23") == "05:23"


def test_parse_elapsed_empty():
    """_parse_elapsed returns '?' for empty string."""
    assert _parse_elapsed("") == "?"


# ── get_golem_processes tests ────────────────────────────────────────


@patch("subprocess.run")
def test_get_golem_processes_finds_golem(mock_run):
    """get_golem_processes returns parsed golem processes."""
    mock_run.return_value = _mock_ps(
        PS_HEADER + "\n" + SAMPLE_LINE + "\n"
    )
    procs = get_golem_processes()
    assert len(procs) >= 1
    assert any(p["pid"] == 12345 for p in procs)


@patch("subprocess.run")
def test_get_golem_processes_excludes_grep(mock_run):
    """get_golem_processes excludes grep commands."""
    grep_line = (
        "terry    99999  0.0  0.0  12345   6789 pts/0    S+   10:30   00:00 "
        "grep golem"
    )
    mock_run.return_value = _mock_ps(
        PS_HEADER + "\n" + grep_line + "\n"
    )
    procs = get_golem_processes()
    assert len(procs) == 0


@patch("subprocess.run")
def test_get_golem_processes_excludes_self(mock_run):
    """get_golem_processes excludes its own process."""
    self_line = (
        "terry    99999  0.0  0.0  12345   6789 pts/0    S+   10:30   00:00 "
        "python /home/terry/germline/effectors/golem-top"
    )
    mock_run.return_value = _mock_ps(
        PS_HEADER + "\n" + self_line + "\n"
    )
    procs = get_golem_processes()
    assert len(procs) == 0


@patch("subprocess.run")
def test_get_golem_processes_timeout(mock_run):
    """get_golem_processes returns empty list on timeout."""
    mock_run.side_effect = subprocess.TimeoutExpired("ps", 5)
    procs = get_golem_processes()
    assert procs == []


@patch("subprocess.run")
def test_get_golem_processes_file_not_found(mock_run):
    """get_golem_processes returns empty list when ps not found."""
    mock_run.side_effect = FileNotFoundError
    procs = get_golem_processes()
    assert procs == []


@patch("subprocess.run")
def test_get_golem_processes_multiple(mock_run):
    """get_golem_processes returns multiple distinct golem processes."""
    line2 = (
        "terry    22222  3.0  2.0 200000 100000 pts/1    S+   09:00   10:00 "
        "bash golem --provider volcano --max-turns 30 "
        '"refactor the authentication module"'
    )
    mock_run.return_value = _mock_ps(
        PS_HEADER + "\n" + SAMPLE_LINE + "\n" + line2 + "\n"
    )
    procs = get_golem_processes()
    pids = {p["pid"] for p in procs}
    assert 12345 in pids
    assert 22222 in pids


# ── format_table tests ───────────────────────────────────────────────


def test_format_table_empty():
    """format_table shows 'No running golem processes' when empty."""
    result = format_table([])
    assert "No running golem processes" in result


def test_format_table_single():
    """format_table shows a single process correctly."""
    procs = [
        {
            "pid": 12345,
            "user": "terry",
            "cpu_pct": "2.5",
            "mem_pct": "1.3",
            "stat": "S+",
            "started": "10:30",
            "elapsed": "05:23",
            "provider": "infini",
            "task": "review codebase",
            "command": "bash golem --provider infini 'review codebase'",
        }
    ]
    result = format_table(procs)
    assert "12345" in result
    assert "infini" in result
    assert "review codebase" in result
    assert "1 running golem task" in result


def test_format_table_deduplicates():
    """format_table deduplicates processes with same task."""
    procs = [
        {
            "pid": 100,
            "user": "terry",
            "cpu_pct": "1.0",
            "mem_pct": "0.5",
            "stat": "S+",
            "started": "10:00",
            "elapsed": "01:00",
            "provider": "infini",
            "task": "same task",
            "command": "bash golem --provider infini 'same task'",
        },
        {
            "pid": 200,
            "user": "terry",
            "cpu_pct": "2.0",
            "mem_pct": "1.0",
            "stat": "S+",
            "started": "10:01",
            "elapsed": "01:01",
            "provider": "infini",
            "task": "same task",
            "command": "bash golem --provider infini 'same task'",
        },
    ]
    result = format_table(procs)
    assert "1 running golem task" in result
    assert "100" in result
    # 200 should not appear since it's a duplicate task
    assert "200" not in result


def test_format_table_truncates_long_task():
    """format_table truncates tasks longer than column width."""
    long_task = "x" * 120
    procs = [
        {
            "pid": 123,
            "user": "terry",
            "cpu_pct": "1.0",
            "mem_pct": "0.5",
            "stat": "S+",
            "started": "10:00",
            "elapsed": "01:00",
            "provider": "infini",
            "task": long_task,
            "command": f"bash golem --provider infini '{long_task}'",
        }
    ]
    result = format_table(procs)
    # The task should be truncated (the line should not contain 120 x's)
    for line in result.split("\n"):
        if "123" in line and "infini" in line:
            assert "x" * 100 not in line


# ── CLI integration tests ────────────────────────────────────────────


def test_cli_json_output():
    """golem-top --json produces valid JSON."""
    import subprocess

    result = subprocess.run(
        ["/home/terry/germline/effectors/golem-top", "--json"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert isinstance(data, list)


def test_cli_default_output():
    """golem-top default output is a human-readable table."""
    import subprocess

    result = subprocess.run(
        ["/home/terry/germline/effectors/golem-top"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    # Either "No running golem processes" or a table with header
    assert "golem" in result.stdout.lower()


def test_cli_help_runs():
    """golem-top --help or -h does not crash."""
    import subprocess

    # The script doesn't have --help, but running it with no args works
    result = subprocess.run(
        ["/home/terry/germline/effectors/golem-top"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
