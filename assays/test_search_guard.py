#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/search-guard — Search guard wrapper tests.

search-guard is a script that wraps grep/rg/find with safety checks.
rg, grep, and find are symlinks to this script.
It should be loaded via exec() or subprocess.run, NEVER imported.
"""


import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SEARCH_GUARD_PATH = Path(__file__).resolve().parents[1] / "effectors" / "search-guard"
RG_LINK_PATH = Path(__file__).resolve().parents[1] / "effectors" / "rg"
GREP_LINK_PATH = Path(__file__).resolve().parents[1] / "effectors" / "grep"


# ── Load module via exec ──────────────────────────────────────────────────────


@pytest.fixture()
def sg():
    """Load search-guard via exec into an isolated namespace."""
    ns: dict = {"__name__": "test_sg_module"}
    source = SEARCH_GUARD_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    mod = type("sg", (), {})()
    for k, v in ns.items():
        if not k.startswith("__"):
            setattr(mod, k, v)
    return mod


# ── File existence and structure ─────────────────────────────────────────────


class TestSearchGuardBasics:
    def test_file_exists(self):
        """Test that search-guard script exists."""
        assert SEARCH_GUARD_PATH.exists()
        assert SEARCH_GUARD_PATH.is_file()

    def test_is_python_script(self):
        """Test that search-guard has Python shebang."""
        first_line = SEARCH_GUARD_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/usr/bin/env python")

    def test_has_main_function(self):
        """Test that search-guard has a main function."""
        content = SEARCH_GUARD_PATH.read_text()
        assert "def main()" in content

    def test_has_known_wrappers_set(self):
        """Test that search-guard defines _KNOWN_WRAPPERS set."""
        content = SEARCH_GUARD_PATH.read_text()
        assert "_KNOWN_WRAPPERS" in content
        assert "grep" in content
        assert "rg" in content
        assert "find" in content


# ── Symlink verification ──────────────────────────────────────────────────────


class TestSymlinks:
    def test_rg_is_symlink_to_search_guard(self):
        """Test that rg is a symlink to search-guard."""
        assert RG_LINK_PATH.is_symlink()
        target = os.readlink(RG_LINK_PATH)
        assert target == "search-guard" or target.endswith("search-guard")

    def test_grep_is_symlink_to_search_guard(self):
        """Test that grep is a symlink to search-guard."""
        assert GREP_LINK_PATH.is_symlink()
        target = os.readlink(GREP_LINK_PATH)
        assert target == "search-guard" or target.endswith("search-guard")

    def test_find_is_symlink_to_search_guard(self):
        """Test that find is a symlink to search-guard."""
        find_link = Path(__file__).resolve().parents[1] / "effectors" / "find"
        assert find_link.is_symlink()
        target = os.readlink(find_link)
        assert target == "search-guard" or target.endswith("search-guard")


# ── Path blocking tests via CLI ──────────────────────────────────────────────


class TestPathBlocking:
    def test_blocks_root_directory_with_rg(self):
        """Test that searching root '/' via rg symlink is blocked."""
        result = subprocess.run(
            [sys.executable, str(RG_LINK_PATH), "pattern", "/"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "BLOCKED" in result.stdout or "blocked" in result.stdout.lower()

    def test_blocks_home_directory_with_grep(self):
        """Test that searching home directory via grep symlink is blocked."""
        home = os.path.expanduser("~")
        result = subprocess.run(
            [sys.executable, str(GREP_LINK_PATH), "-r", "pattern", home],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "BLOCKED" in result.stdout or "blocked" in result.stdout.lower()

    def test_blocks_library_directory(self):
        """Test that massive directories are blocked."""
        # Test with home directory which should always be blocked
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
    def test_blocks_downloads_directory(self):
        """Test that Downloads directory is blocked as too large."""
        result = subprocess.run(
            [sys.executable, str(RG_LINK_PATH), "pattern", "~/Downloads"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "too large" in result.stdout.lower() or "BLOCKED" in result.stdout

    @pytest.mark.skipif(
        os.path.expanduser("~").startswith("/home"),
        reason="Pictures blocking uses macOS-specific path"
    )
    def test_blocks_pictures_directory(self):
        """Test that Pictures directory is blocked as too large."""
        result = subprocess.run(
            [sys.executable, str(RG_LINK_PATH), "pattern", "~/Pictures"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 1
        assert "too large" in result.stdout.lower() or "BLOCKED" in result.stdout


# ── Allowed search tests via mocks ────────────────────────────────────────────


class TestAllowedSearch:
    def test_allows_tmp_directory(self, sg):
        """Test that /tmp can be searched (not blocked)."""
        with patch("sys.argv", ["rg", "pattern", "/tmp"]):
            with patch("os.path.exists", return_value=True):
                with patch("os.execv") as mock_exec:
                    sg.main()
                    assert mock_exec.called

    def test_allows_relative_path(self, sg, tmp_path):
        """Test that relative paths can be searched."""
        with patch("sys.argv", ["rg", "pattern", "."]):
            with patch("os.path.exists", return_value=True):
                with patch("os.execv") as mock_exec:
                    sg.main()
                    assert mock_exec.called

    def test_allows_search_without_path(self, sg):
        """Test that searches without a path argument are allowed (stdin mode)."""
        with patch("sys.argv", ["grep", "pattern"]):
            with patch("os.execv") as mock_exec:
                sg.main()
                assert mock_exec.called


# ── Internal function tests via exec ─────────────────────────────────────────


class TestInternalFunctions:
    def test_main_function_exists(self, sg):
        """Test that main function is defined."""
        assert hasattr(sg, "main")
        assert callable(sg.main)

    def test_known_wrappers_exists(self, sg):
        """Test that _KNOWN_WRAPPERS set is defined."""
        assert hasattr(sg, "_KNOWN_WRAPPERS")
        wrappers = sg._KNOWN_WRAPPERS
        assert isinstance(wrappers, set)
        assert "grep" in wrappers
        assert "rg" in wrappers
        assert "find" in wrappers

    def test_find_real_binary_is_callable(self, sg):
        """Test that _find_real_binary function exists."""
        assert hasattr(sg, "_find_real_binary")
        assert callable(sg._find_real_binary)


# ── Blocking logic tests via mocks ────────────────────────────────────────────


class TestBlockingLogic:
    def test_blocks_root_via_mock(self, sg, capsys):
        """Test root directory blocking via mock."""
        with patch("sys.argv", ["rg", "pattern", "/"]):
            with pytest.raises(SystemExit) as exc:
                sg.main()
            assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "BLOCKED" in out

    def test_blocks_home_via_mock(self, sg, capsys):
        """Test home directory blocking via mock."""
        home = str(Path.home())
        with patch("sys.argv", ["rg", "pattern", home]):
            with pytest.raises(SystemExit) as exc:
                sg.main()
            assert exc.value.code == 1
        out = capsys.readouterr().out
        assert "BLOCKED" in out

    @pytest.mark.skipif(
        os.path.expanduser("~").startswith("/home"),
        reason="~/Library blocking is macOS-specific"
    )
    def test_blocks_macos_library_via_mock(self, sg):
        """Test macOS Library path blocking via mock."""
        with patch("sys.argv", ["rg", "pattern", str(Path.home() / "Library")]):
            with pytest.raises(SystemExit) as exc:
                sg.main()
            assert exc.value.code == 1

    def test_blocks_downloads_via_mock(self, sg):
        """Test Downloads path blocking via mock."""
        with patch("sys.argv", ["rg", "pattern", str(Path.home() / "Downloads")]):
            with pytest.raises(SystemExit) as exc:
                sg.main()
            assert exc.value.code == 1

    def test_blocks_pictures_via_mock(self, sg):
        """Test Pictures path blocking via mock."""
        with patch("sys.argv", ["rg", "pattern", str(Path.home() / "Pictures")]):
            with pytest.raises(SystemExit) as exc:
                sg.main()
            assert exc.value.code == 1
