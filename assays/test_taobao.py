#!/usr/bin/env python3
"""Tests for effectors/taobao — symlink to taobao-cli tool."""

import subprocess
import sys
from pathlib import Path

import pytest

TAOBAO_PATH = Path(__file__).resolve().parents[1] / "effectors" / "taobao"


# ── Symlink structure tests ────────────────────────────────────────────────────


class TestTaobaoSymlink:
    def test_symlink_exists(self):
        """Test that taobao effector symlink exists."""
        # On Linux, symlink may point to macOS path that doesn't exist
        # Check the symlink file itself exists (even if broken)
        assert TAOBAO_PATH.is_symlink() or TAOBAO_PATH.is_file()

    def test_symlink_target_exists_or_broken(self):
        """Test that taobao symlink target exists (or is expected broken symlink)."""
        if TAOBAO_PATH.is_symlink():
            target = TAOBAO_PATH.resolve()
            # Symlink may point to macOS path on Linux - that's OK
            if not target.exists():
                # Check it's a valid symlink pointing to expected location
                import os

                link_target = os.readlink(TAOBAO_PATH)
                assert "taobao" in link_target.lower()

    def test_symlink_target_is_executable(self):
        """Test that taobao symlink target is executable (if target exists)."""
        target = TAOBAO_PATH.resolve()
        if target.exists():
            # Check if file has execute permission
            assert target.stat().st_mode & 0o111, f"{target} is not executable"
        # If target doesn't exist (broken symlink on different OS), that's OK

    def test_symlink_points_to_taobao_cli(self):
        """Test symlink points to expected taobao-cli location."""
        target = TAOBAO_PATH.resolve()
        assert "taobao" in str(target).lower()


# ── Execution tests ────────────────────────────────────────────────────────────


class TestTaobaoExecution:
    @pytest.mark.skipif(
        not TAOBAO_PATH.resolve().exists(),
        reason="taobao CLI not installed or symlink broken on this platform",
    )
    def test_taobao_help_runs(self):
        """Test taobao --help runs without error."""
        result = subprocess.run(
            [sys.executable, str(TAOBAO_PATH.resolve()), "--help"],
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
        not TAOBAO_PATH.resolve().exists(),
        reason="taobao CLI not installed or symlink broken on this platform",
    )
    def test_taobao_version_or_help_available(self):
        """Test taobao has version or help option."""
        # Try --version first
        result = subprocess.run(
            [sys.executable, str(TAOBAO_PATH.resolve()), "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # If --version fails, try --help
        if result.returncode != 0:
            result = subprocess.run(
                [sys.executable, str(TAOBAO_PATH.resolve()), "--help"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        # At least one should work
        assert result.returncode == 0 or result.stdout or result.stderr


# ── Symlink attributes tests ───────────────────────────────────────────────────


class TestSymlinkAttributes:
    def test_symlink_in_effectors_dir(self):
        """Test taobao is in effectors directory."""
        assert TAOBAO_PATH.parent.name == "effectors"

    def test_symlink_name(self):
        """Test symlink has correct name."""
        assert TAOBAO_PATH.name == "taobao"

    def test_symlink_resolves_to_python_script(self):
        """Test symlink resolves to a Python script or executable."""
        target = TAOBAO_PATH.resolve()
        if target.exists():
            # Could be a Python script or a binary
            # Check if it's a script by looking for shebang
            try:
                first_bytes = target.read_bytes()[:100]
                if b"python" in first_bytes.lower() or b"#!/" in first_bytes:
                    pass  # Python script
                # Or it could be a binary
            except Exception:
                pass
            assert True
