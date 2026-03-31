"""Tests for ck effector script — Moonshot/Kimi Claude wrapper."""
from __future__ import annotations

import os
import subprocess
import pytest

CK_PATH = "/home/terry/germline/effectors/ck"


def test_ck_fails_without_api_key():
    """Test ck exits with error when no Moonshot API key is found."""
    # Copy current env and remove MOONSHOT_API_KEY
    env = os.environ.copy()
    env.pop("MOONSHOT_API_KEY", None)
    # Also remove any possible key from secret-tool but keep PATH etc.
    result = subprocess.run(
        [CK_PATH, "--help"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert "error: no Moonshot API key found" in result.stderr


def test_ck_is_executable():
    """Test ck script has executable permissions."""
    result = subprocess.run(
        ["test", "-x", CK_PATH],
        capture_output=True,
    )
    assert result.returncode == 0, "ck script is not executable"


def test_ck_contains_valid_syntax():
    """Check that bash syntax is valid."""
    result = subprocess.run(
        ["bash", "-n", CK_PATH],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Syntax errors in ck script: {result.stderr}"
