from __future__ import annotations
"""Tests for effectors/plan-exec — deprecated bash script tested via subprocess."""

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "plan-exec"


def run_plan_exec(args: list[str] | None = None) -> subprocess.CompletedProcess:
    """Run plan-exec with given arguments."""
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=5,
    )


class TestPlanExec:
    """Tests for the deprecated plan-exec script.

    The script should always output a deprecation message pointing to sortase
    and exit with non-zero code, except for --help/-h which exits zero.
    """

    def test_no_args_prints_deprecation_to_stderr(self):
        """Without arguments, prints deprecation to stderr and exit 1."""
        result = run_plan_exec()
        assert result.returncode == 1
        assert "deprecated" in result.stderr
        assert "sortase exec <plan> -p <project>" in result.stderr
        assert result.stdout == ""

    def test_help_flag_exits_zero_with_message(self):
        """With --help, prints message to stdout and exit 0."""
        result = run_plan_exec(["--help"])
        assert result.returncode == 0
        assert "deprecated" in result.stdout
        assert "sortase exec <plan> -p <project>" in result.stdout
        assert result.stderr == ""

    def test_h_flag_exits_zero_with_message(self):
        """With -h, prints message to stdout and exit 0."""
        result = run_plan_exec(["-h"])
        assert result.returncode == 0
        assert "deprecated" in result.stdout
        assert "sortase exec <plan> -p <project>" in result.stdout
        assert result.stderr == ""

    def test_any_other_arg_still_deprecates_stderr_exit_one(self):
        """Any other arguments still output deprecation to stderr and exit 1."""
        result = run_plan_exec(["some", "args", "--whatever"])
        assert result.returncode == 1
        assert "deprecated" in result.stderr
        assert "sortase exec <plan> -p <project>" in result.stderr
        assert result.stdout == ""
