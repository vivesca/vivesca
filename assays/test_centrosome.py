"""Tests for effectors/centrosome — which is a symlink to poiesis."""

import subprocess
from pathlib import Path

import pytest


def test_centrosome_exists_and_is_executable():
    """Verify that centrosome symlink exists and is executable."""
    effector_path = Path(__file__).resolve().parents[1] / "effectors" / "centrosome"
    assert effector_path.exists()
    assert effector_path.is_symlink()
    # Check it points to poiesis
    assert effector_path.readlink().name == "poiesis"
    # Check it's executable
    assert effector_path.stat().st_mode & 0o111 != 0  # at least one executable bit set


def test_centrosome_help():
    """Run centrosome with --help and verify output."""
    effector_path = Path(__file__).resolve().parents[1] / "effectors" / "centrosome"
    result = subprocess.run(
        [str(effector_path), "--help"],
        capture_output=True,
        text=True,
        check=True
    )
    assert result.returncode == 0
    assert "poiesis" in result.stdout
    assert "Usage" in result.stdout
    assert "search Capco vault notes by keyword" in result.stdout


def test_centrosome_list_cases():
    """Test that centrosome can list cases successfully."""
    effector_path = Path(__file__).resolve().parents[1] / "effectors" / "centrosome"
    result = subprocess.run(
        [str(effector_path), "--cases"],
        capture_output=True,
        text=True
    )
    # It will exit with 0 regardless
    assert result.returncode == 0
    # Should output at least some case headings
    assert len(result.stdout) > 0
    assert "Case Study" in result.stdout
    # No warnings if files exist (which they do in this environment)
    assert "Warning" not in result.stderr
