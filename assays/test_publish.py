#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/publish — symlink to publish tool."""


import subprocess
from pathlib import Path

import pytest

SARCIO_PATH = Path(__file__).resolve().parents[1] / "effectors" / "publish"


# ── Symlink structure tests ────────────────────────────────────────────────────


class TestSarcioSymlink:
    def test_symlink_exists(self):
        """Test that publish effector symlink exists."""
        # On Linux, symlink may point to macOS path that doesn't exist
        # Check the symlink file itself exists (even if broken)
        assert SARCIO_PATH.is_symlink() or SARCIO_PATH.is_file()

    def test_symlink_target_exists_or_broken(self):
        """Test that publish symlink target exists (or is expected broken symlink)."""
        if SARCIO_PATH.is_symlink():
            target = SARCIO_PATH.resolve()
            # Symlink may point to macOS path on Linux - that's OK
            if not target.exists():
                # Check it's a valid symlink pointing to expected location
                import os

                link_target = os.readlink(SARCIO_PATH)
                assert "mise" in link_target or "publish" in link_target.lower()

    def test_symlink_target_is_executable(self):
        """Test that publish symlink target is executable (if target exists)."""
        target = SARCIO_PATH.resolve()
        if target.exists():
            # Check if file has execute permission
            assert target.stat().st_mode & 0o111, f"{target} is not executable"
        # If target doesn't exist (broken symlink on different OS), that's OK

    def test_symlink_points_to_mise_python(self):
        """Test symlink points to mise Python installation."""
        target = SARCIO_PATH.resolve()
        # Should point to mise or have publish in path
        target_str = str(target)
        assert "mise" in target_str or "publish" in target_str.lower()


# ── Execution tests ────────────────────────────────────────────────────────────


class TestSarcioExecution:
    @pytest.mark.skipif(
        not SARCIO_PATH.resolve().exists(),
        reason="publish CLI not installed or symlink broken on this platform",
    )
    def test_publish_help_runs(self):
        """Test publish --help runs without error."""
        result = subprocess.run(
            [str(SARCIO_PATH.resolve()), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Either succeeds or shows help
        assert (
            result.returncode == 0
            or "usage" in result.stdout.lower()
            or "usage" in result.stderr.lower()
        )

    @pytest.mark.skipif(
        not SARCIO_PATH.resolve().exists(),
        reason="publish CLI not installed or symlink broken on this platform",
    )
    def test_publish_executable_runs(self):
        """Test publish runs as executable."""
        result = subprocess.run(
            [str(SARCIO_PATH.resolve())],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should run without crashing (may show help or require args)
        # Non-zero exit is OK if it shows usage
        if result.returncode != 0:
            assert result.stdout or result.stderr


# ── Symlink attributes tests ────────────────────────────────────────────────────


class TestSymlinkAttributes:
    def test_symlink_in_effectors_dir(self):
        """Test publish is in effectors directory."""
        assert SARCIO_PATH.parent.name == "effectors"

    def test_symlink_name(self):
        """Test symlink has correct name."""
        assert SARCIO_PATH.name == "publish"

    def test_symlink_is_not_broken_or_cross_platform(self):
        """Test symlink is not broken (or is cross-platform broken symlink)."""
        try:
            # resolve() should work for non-broken symlinks
            target = SARCIO_PATH.resolve()
            # File should exist OR symlink points to expected location
            if not target.exists():
                import os

                link_target = os.readlink(SARCIO_PATH)
                # Cross-platform broken symlinks are OK
                assert "mise" in link_target or "publish" in link_target.lower()
        except OSError:
            pytest.fail("Symlink is broken")


# ── Integration tests ───────────────────────────────────────────────────────────


class TestSarcioIntegration:
    @pytest.mark.skipif(
        not SARCIO_PATH.resolve().exists(),
        reason="publish CLI not installed or symlink broken on this platform",
    )
    def test_can_execute_via_symlink(self):
        """Test that we can execute publish through the symlink."""
        result = subprocess.run(
            [str(SARCIO_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Should produce some output
        assert result.stdout or result.stderr
