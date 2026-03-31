"""Tests for effectors/compound-engineering-test — bash script tested via subprocess."""
from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "effectors" / "compound-engineering-test"
AUTO_UPDATE_SCRIPT = Path(__file__).parent.parent / "effectors" / "auto-update-compound-engineering.sh"


# ── helpers ─────────────────────────────────────────────────────────────


def _run_script(
    args: list[str] | None = None,
    input_text: str | None = None,
    env_extra: dict | None = None,
    tmp_path: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run the script with optional input and environment."""
    env = os.environ.copy()
    # Unset HOME override if present so script uses tmp_path as HOME
    if tmp_path is not None:
        env["HOME"] = str(tmp_path)
    if env_extra:
        env.update(env_extra)
    cmd = ["bash", str(SCRIPT)] + (args or [])
    return subprocess.run(
        cmd, capture_output=True, text=True, input=input_text, env=env, timeout=10,
    )


def _mock_auto_update(tmp_path: Path, exit_code: int = 0) -> None:
    """Mock the auto-update script to record that it was called."""
    # Override the script location by putting our mock in a bin directory that's earlier in PATH
    # We need to keep $HOME pointing to tmp_path so script finds our mock
    mock_bin = tmp_path / "germline" / "effectors"
    mock_bin.mkdir(parents=True, exist_ok=True)
    mock_script = mock_bin / "auto-update-compound-engineering.sh"
    mock_script.write_text(f"""#!/bin/bash
echo "auto-update-compound-engineering.sh called with $*"
exit {exit_code}
""")
    mock_script.chmod(mock_script.stat().st_mode | stat.S_IEXEC)


# ── --help tests ────────────────────────────────────────────────────────


class TestHelpFlag:
    def test_help_exits_zero(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_h_short_flag_exits_zero(self, tmp_path):
        r = _run_script(["-h"], tmp_path=tmp_path)
        assert r.returncode == 0

    def test_help_shows_usage(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "Usage:" in r.stdout
        assert "compound-engineering-test" in r.stdout

    def test_help_describes_purpose(self, tmp_path):
        r = _run_script(["--help"], tmp_path=tmp_path)
        assert "Test the compound-engineering auto-update" in r.stdout


# ── option parsing tests ────────────────────────────────────────────────


class TestOptionParsing:
    def test_unknown_option_exits_two(self, tmp_path):
        r = _run_script(["--unknown-option"], tmp_path=tmp_path)
        assert r.returncode == 2
        assert "Unknown option:" in r.stderr

    def test_dry_run_flag_works(self, tmp_path):
        """Dry run shouldn't actually run the update."""
        r = _run_script(["-n"], tmp_path=tmp_path)
        assert r.returncode == 0
        assert "Dry run" in r.stdout
        assert "would execute" in r.stdout
        assert "auto-update-compound-engineering.sh" in r.stdout
        assert "Dry run complete" in r.stdout

    def test_dry_run_long_flag_works(self, tmp_path):
        r = _run_script(["--dry-run"], tmp_path=tmp_path)
        assert r.returncode == 0
        assert "Dry run" in r.stdout


# ── interactive tests ───────────────────────────────────────────────────


class TestInteractivePrompt:
    def test_prints_warning_when_non_interactive(self, tmp_path):
        """Non-interactive run (not a tty) just proceeds."""
        _mock_auto_update(tmp_path, exit_code=0)
        r = _run_script([], tmp_path=tmp_path)
        assert r.returncode == 0
        assert "Running non-interactively — proceeding" in r.stdout

    def test_cancelled_on_n_response(self, tmp_path):
        """User answers 'n' → script exits with 1."""
        r = _run_script([], input_text="n", tmp_path=tmp_path)
        assert r.returncode == 1
        assert "Test cancelled" in r.stdout

    def test_continues_on_y_response(self, tmp_path):
        """User answers 'y' → script runs update."""
        _mock_auto_update(tmp_path, exit_code=0)
        r = _run_script([], input_text="y", tmp_path=tmp_path)
        assert r.returncode == 0
        assert "Test complete" in r.stdout

    def test_uppercase_y_works(self, tmp_path):
        """User answers 'Y' → script runs update."""
        _mock_auto_update(tmp_path, exit_code=0)
        r = _run_script([], input_text="Y", tmp_path=tmp_path)
        assert r.returncode == 0
        assert "Test complete" in r.stdout


# ── execution tests ─────────────────────────────────────────────────────


class TestScriptExecution:
    def test_runs_auto_update_script_when_confirmed(self, tmp_path):
        """After confirmation, runs the actual auto-update script."""
        _mock_auto_update(tmp_path, exit_code=0)
        r = _run_script([], input_text="y", tmp_path=tmp_path)
        assert r.returncode == 0
        assert "Test complete!" in r.stdout
        # Check that our mock was called by looking at its output
        assert "auto-update-compound-engineering.sh called" in r.stdout

    def test_exits_with_same_code_as_auto_update(self, tmp_path):
        """If auto-update fails, test script should exit with failure too."""
        _mock_auto_update(tmp_path, exit_code=42)
        # Note: bash exits with the last command's exit code
        # But actually the script uses `set -e`, so it should exit immediately
        r = _run_script([], input_text="y", tmp_path=tmp_path)
        assert r.returncode == 42

    def test_prints_intro_message(self, tmp_path):
        r = _run_script(["--dry-run"], tmp_path=tmp_path)
        assert "Testing compound-engineering update script" in r.stdout
        assert "not waiting for Sunday 2 AM" in r.stdout
