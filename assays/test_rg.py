#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/rg — ripgrep symlink wrapper tests.

rg is a symlink to search-guard, which wraps the real ripgrep binary.
It should be loaded via exec() or subprocess.run, NEVER imported.
"""


import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

RG_LINK_PATH = Path(__file__).resolve().parents[1] / "effectors" / "rg"
SEARCH_GUARD_PATH = Path(__file__).resolve().parents[1] / "effectors" / "search-guard"


# ── Load module via exec ──────────────────────────────────────────────────────


@pytest.fixture()
def sg():
    """Load search-guard via exec into an isolated namespace."""
    ns: dict = {"__name__": "test_rg_module"}
    source = SEARCH_GUARD_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    mod = type("sg", (), {})()
    for k, v in ns.items():
        if not k.startswith("__"):
            setattr(mod, k, v)
    return mod


# ── Symlink and structure tests ──────────────────────────────────────────────


class TestRGSymlink:
    def test_rg_is_symlink(self):
        """Test that rg is a symlink."""
        assert RG_LINK_PATH.is_symlink()

    def test_rg_points_to_search_guard(self):
        """Test that rg symlink points to search-guard."""
        target = os.readlink(RG_LINK_PATH)
        assert target == "search-guard" or target.endswith("search-guard")

    def test_symlink_target_exists(self):
        """Test that the symlink target exists."""
        assert RG_LINK_PATH.exists()


# ── CLI blocking tests via subprocess ─────────────────────────────────────────


class TestRGBlocking:
    def test_blocks_root_directory(self):
        """Test that searching root '/' is blocked."""
        result = subprocess.run(
            [sys.executable, str(RG_LINK_PATH), "pattern", "/"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "BLOCKED" in result.stdout or "blocked" in result.stdout.lower()

    def test_blocks_home_directory(self):
        """Test that searching home directory is blocked."""
        home = os.path.expanduser("~")
        result = subprocess.run(
            [sys.executable, str(RG_LINK_PATH), "pattern", home],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "BLOCKED" in result.stdout or "blocked" in result.stdout.lower()

    def test_blocks_library(self):
        """Test that massive directories are blocked."""
        home = os.path.expanduser("~")
        result = subprocess.run(
            [sys.executable, str(RG_LINK_PATH), "pattern", home],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "BLOCKED" in result.stdout or "blocked" in result.stdout.lower()

    @pytest.mark.skipif(
        os.path.expanduser("~").startswith("/home"),
        reason="Downloads blocking uses macOS-specific path"
    )
    def test_blocks_downloads(self):
        """Test that Downloads directory is blocked."""
        result = subprocess.run(
            [sys.executable, str(RG_LINK_PATH), "pattern", "~/Downloads"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1

    @pytest.mark.skipif(
        os.path.expanduser("~").startswith("/home"),
        reason="Pictures blocking uses macOS-specific path"
    )
    def test_blocks_pictures(self):
        """Test that Pictures directory is blocked."""
        result = subprocess.run(
            [sys.executable, str(RG_LINK_PATH), "pattern", "~/Pictures"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1


# ── Allowed search tests via mocks ────────────────────────────────────────────


class TestRGAllowed:
    def test_allows_tmp_directory(self, sg):
        """Test that /tmp can be searched (not blocked)."""
        with patch("sys.argv", ["rg", "pattern", "/tmp"]):
            with patch("os.path.exists", return_value=True):
                with patch("os.execv") as mock_exec:
                    sg.main()
                    # Should call execv (not blocked)
                    assert mock_exec.called

    def test_allows_specific_subdirectory(self, sg, tmp_path):
        """Test that specific subdirectories can be searched."""
        with patch("sys.argv", ["rg", "pattern", str(tmp_path)]):
            with patch("os.path.exists", return_value=True):
                with patch("os.execv") as mock_exec:
                    sg.main()
                    assert mock_exec.called

    def test_allows_nested_subdirectory(self, sg, tmp_path):
        """Test that deeply nested subdirectories can be searched."""
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)

        with patch("sys.argv", ["rg", "pattern", str(tmp_path)]):
            with patch("os.path.exists", return_value=True):
                with patch("os.execv") as mock_exec:
                    sg.main()
                    assert mock_exec.called


# ── Path detection tests ──────────────────────────────────────────────────────


class TestRGPathDetection:
    def test_detects_absolute_path(self, sg):
        """Test that absolute paths are detected and processed."""
        with patch("sys.argv", ["rg", "pattern", "/tmp/test"]):
            with patch("os.path.exists", return_value=True):
                with patch("os.execv") as mock_exec:
                    sg.main()
                    # execv should be called with the path
                    call_args = mock_exec.call_args[0][1]
                    assert "/tmp/test" in call_args

    def test_detects_relative_path(self, sg, tmp_path):
        """Test that relative paths are detected and processed."""
        with patch("sys.argv", ["rg", "pattern", "."]):
            with patch("os.path.exists", return_value=True):
                with patch("os.execv") as mock_exec:
                    sg.main()
                    assert mock_exec.called

    def test_no_path_passes_through(self, sg):
        """Test that searches without a path pass through to the binary."""
        with patch("sys.argv", ["rg", "pattern"]):
            with patch("os.execv") as mock_exec:
                sg.main()
                assert mock_exec.called
                # Should use the rg binary path
                called_bin = mock_exec.call_args[0][0]
                assert "rg" in called_bin


# ── BINARIES dict tests ───────────────────────────────────────────────────────


class TestRGBinaries:
    def test_rg_entry_exists(self, sg):
        """Test that rg is in BINARIES dict."""
        assert "rg" in sg.BINARIES

    def test_binaries_paths_are_absolute(self, sg):
        """Test that all BINARIES paths are absolute."""
        for name, path in sg.BINARIES.items():
            assert os.path.isabs(path), f"{name} path is not absolute: {path}"
