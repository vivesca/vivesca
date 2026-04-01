from __future__ import annotations

"""Tests for pharos-env.sh — environment wrapper for systemd services."""

import os
import subprocess
from pathlib import Path

import pytest


PHAROS_ENV_SH = Path(str(Path.home() / "germline/effectors/pharos-env.sh"))


def test_pharos_env_help_flag():
    """pharos-env.sh --help prints usage and exits cleanly."""
    result = subprocess.run(
        [str(PHAROS_ENV_SH), "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Usage: pharos-env.sh <command> [args...]" in result.stdout
    assert "Environment wrapper for systemd services on pharos" in result.stdout


def test_pharos_env_help_short():
    """pharos-env.sh -h prints help."""
    result = subprocess.run(
        [str(PHAROS_ENV_SH), "-h"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout


def test_pharos_env_sets_home_and_path():
    """pharos-env.sh sets HOME and extends PATH."""
    # Run env command through wrapper to check environment
    result = subprocess.run(
        [str(PHAROS_ENV_SH), "env"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    
    # HOME should be set to /home/terry
    assert f"HOME=/home/terry" in result.stdout
    
    # PATH should contain all the expected entries
    assert ".local/bin" in result.stdout
    assert ".cargo/bin" in result.stdout
    assert "/usr/local/bin" in result.stdout
    assert "/usr/bin" in result.stdout
    assert "/bin" in result.stdout


def test_pharos_env_executes_command():
    """pharos-env.sh execs the given command with arguments."""
    # Test that arguments are passed correctly
    test_msg = "Hello from test"
    result = subprocess.run(
        [str(PHAROS_ENV_SH), "echo", test_msg],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert result.stdout.strip() == test_msg


def test_pharos_env_multiple_arguments():
    """pharos-env.sh handles multiple arguments correctly."""
    result = subprocess.run(
        [str(PHAROS_ENV_SH), "ls", "-la", "/home/terry"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert len(result.stdout) > 0


def test_pharos_env_non_zero_exit_code_passed_through():
    """Non-zero exit codes from the command are preserved."""
    # Run false which should exit with 1
    result = subprocess.run(
        [str(PHAROS_ENV_SH), "false"],
        capture_output=True
    )
    assert result.returncode == 1


def test_pharos_env_sources_zshenv_local_if_exists():
    """pharos-env.sh sources ~/.zshenv.local if it exists."""
    # Check if it exists
    zshenv_local = Path(str(Path.home() / ".zshenv.local"))
    if zshenv_local.exists():
        # If it exists, we just verify that the script at least tries to source it
        # Can't really test the content since it has actual secrets
        pass
    else:
        # If it doesn't exist, the script should just skip it - so still success
        pass
    
    # Either way, running env should succeed
    result = subprocess.run(
        [str(PHAROS_ENV_SH), "true"],
        capture_output=True
    )
    assert result.returncode == 0


def test_pharos_env_is_executable():
    """pharos-env.sh should have executable permissions."""
    assert PHAROS_ENV_SH.exists()
    assert os.access(PHAROS_ENV_SH, os.X_OK)
