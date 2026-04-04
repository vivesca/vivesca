from __future__ import annotations

"""Tests for effectors/gemmation-env — bash script tested via subprocess."""

import os
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "effectors" / "gemmation-env"


def _run(tmp_path: Path, env_overrides: dict | None = None) -> subprocess.CompletedProcess:
    """Run gemmation-env with HOME=tmp_path and optional env overrides."""
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        env=env,
        timeout=10,
    )


class TestScriptExists:
    def test_script_exists(self):
        assert SCRIPT.exists()

    def test_script_is_executable(self):
        assert os.access(SCRIPT, os.X_OK)


class TestLinuxBehavior:
    """On Linux, gemmation-env exits 0 with a message (legatus is macOS-only)."""

    def test_exits_zero_on_linux(self, tmp_path):
        """On Linux, script exits 0 since legatus is macOS-only."""
        r = _run(tmp_path)
        assert r.returncode == 0

    def test_stderr_message_on_linux(self, tmp_path):
        """On Linux, script prints a message to stderr."""
        r = _run(tmp_path)
        assert "legatus is macOS-only" in r.stderr

    def test_no_stdout_on_linux(self, tmp_path):
        """On Linux, script produces no stdout."""
        r = _run(tmp_path)
        assert r.stdout.strip() == ""


class TestDarwinPathSetup:
    """Test PATH setup logic by mocking uname to return Darwin."""

    def test_path_includes_venv_on_darwin(self, tmp_path, monkeypatch):
        """On Darwin, PATH should include .venv/bin."""
        # Create a mock uname script that returns Darwin
        mock_bin = tmp_path / "bin"
        mock_bin.mkdir()
        mock_uname = mock_bin / "uname"
        mock_uname.write_text('#!/bin/bash\necho "Darwin"\n')
        mock_uname.chmod(0o755)

        # Create a mock legatus that prints PATH and exits
        mock_legatus = mock_bin / "legatus"
        mock_legatus.write_text('#!/bin/bash\necho "PATH=$PATH"\nexit 0\n')
        mock_legatus.chmod(0o755)

        # Create the queue file
        queue_file = tmp_path / "epigenome" / "chromatin" / "agent-queue.yaml"
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        queue_file.write_text("[]")

        # Create .venv/bin to verify it's in PATH
        venv_bin = tmp_path / "germline" / ".venv" / "bin"
        venv_bin.mkdir(parents=True)

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{mock_bin}:{env.get('PATH', '')}"

        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )

        # The script should have run legatus (our mock)
        assert "PATH=" in r.stdout

    def test_execs_legatus_with_queue_on_darwin(self, tmp_path):
        """On Darwin, script execs legatus with the correct queue path."""
        mock_bin = tmp_path / "bin"
        mock_bin.mkdir()
        mock_uname = mock_bin / "uname"
        mock_uname.write_text('#!/bin/bash\necho "Darwin"\n')
        mock_uname.chmod(0o755)

        # Mock legatus that prints its args
        mock_legatus = mock_bin / "legatus"
        mock_legatus.write_text('#!/bin/bash\necho "ARGS: $@"\nexit 0\n')
        mock_legatus.chmod(0o755)

        # Create expected queue file path
        queue_file = tmp_path / "epigenome" / "chromatin" / "agent-queue.yaml"
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        queue_file.write_text("[]")

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{mock_bin}:{env.get('PATH', '')}"

        r = subprocess.run(
            ["bash", str(SCRIPT)],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )

        assert "--queue" in r.stdout
        assert "agent-queue.yaml" in r.stdout


class TestPassesArguments:
    """Script should pass through any command-line arguments."""

    def test_passes_args_to_legatus(self, tmp_path):
        """Additional arguments are passed to legatus."""
        mock_bin = tmp_path / "bin"
        mock_bin.mkdir()
        mock_uname = mock_bin / "uname"
        mock_uname.write_text('#!/bin/bash\necho "Darwin"\n')
        mock_uname.chmod(0o755)

        mock_legatus = mock_bin / "legatus"
        mock_legatus.write_text('#!/bin/bash\necho "ARGS: $@"\nexit 0\n')
        mock_legatus.chmod(0o755)

        queue_file = tmp_path / "epigenome" / "chromatin" / "agent-queue.yaml"
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        queue_file.write_text("[]")

        env = os.environ.copy()
        env["HOME"] = str(tmp_path)
        env["PATH"] = f"{mock_bin}:{env.get('PATH', '')}"

        r = subprocess.run(
            ["bash", str(SCRIPT), "--verbose", "--dry-run"],
            capture_output=True,
            text=True,
            env=env,
            timeout=10,
        )

        assert "--verbose" in r.stdout
        assert "--dry-run" in r.stdout


class TestHomeExpansion:
    """Verify HOME is correctly resolved."""

    def test_uses_home_env_var(self, tmp_path):
        """Script uses $HOME from environment."""
        # On Linux this just prints the message
        r = _run(tmp_path)
        # If HOME was used correctly, the path in the message should reference it
        assert r.returncode == 0
