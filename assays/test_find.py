#!/usr/bin/env python3
from __future__ import annotations

"""Tests for effectors/find — search-guard find wrapper unit tests.

find is a symlink to search-guard, which wraps the real find binary.
Loaded via exec() with all external calls mocked.
"""


import os
from pathlib import Path
from unittest.mock import patch

import pytest

SEARCH_GUARD_PATH = Path(__file__).resolve().parents[1] / "effectors" / "search-guard"
FIND_LINK_PATH = Path(__file__).resolve().parents[1] / "effectors" / "find"


# ── Load module via exec ────────────────────────────────────────────────────


@pytest.fixture()
def sg():
    """Load search-guard via exec into an isolated namespace."""
    ns: dict = {"__name__": "sg_module"}
    source = SEARCH_GUARD_PATH.read_text(encoding="utf-8")
    exec(source, ns)
    mod = type("sg", (), {})()
    for k, v in ns.items():
        if not k.startswith("__"):
            setattr(mod, k, v)
    return mod


# ── Symlink structure ───────────────────────────────────────────────────────


class TestFindSymlink:
    def test_find_is_symlink(self):
        assert FIND_LINK_PATH.is_symlink()

    def test_find_points_to_search_guard(self):
        target = os.readlink(FIND_LINK_PATH)
        assert target == "search-guard" or target.endswith("search-guard")

    def test_symlink_target_exists(self):
        assert FIND_LINK_PATH.exists()


# ── BINARIES dict ────────────────────────────────────────────────────────────


class TestFindBinaries:
    def test_find_entry_exists(self, sg):
        assert "find" in sg._KNOWN_WRAPPERS

    def test_all_three_binaries_defined(self, sg):
        assert {"grep", "rg", "find"} == sg._KNOWN_WRAPPERS


# ── Root/home blocking ──────────────────────────────────────────────────────


class TestFindBlocking:
    def test_blocks_root(self, sg, capsys):
        with patch("sys.argv", ["find", "/"]):
            with pytest.raises(SystemExit) as exc:
                sg.main()
            assert exc.value.code == 1
        assert "BLOCKED" in capsys.readouterr().out

    def test_blocks_home(self, sg):
        home = str(Path.home())
        with patch("sys.argv", ["find", home]):
            with pytest.raises(SystemExit) as exc:
                sg.main()
            assert exc.value.code == 1

    def test_blocks_library(self, sg):
        """Massive-dir block uses source's hardcoded path."""
        with patch("sys.argv", ["find", str(Path.home() / "Library")]):
            with pytest.raises(SystemExit) as exc:
                sg.main()
            assert exc.value.code == 1

    def test_blocks_pictures(self, sg):
        with patch("sys.argv", ["find", str(Path.home() / "Pictures")]):
            with pytest.raises(SystemExit) as exc:
                sg.main()
            assert exc.value.code == 1

    def test_blocks_downloads(self, sg):
        with patch("sys.argv", ["find", str(Path.home() / "Downloads")]):
            with pytest.raises(SystemExit) as exc:
                sg.main()
            assert exc.value.code == 1

    def test_blocks_with_extra_args(self, sg):
        """Even with -name and -type flags, blocking still applies."""
        with patch("sys.argv", ["find", "/", "-name", "*.py"]):
            with pytest.raises(SystemExit) as exc:
                sg.main()
            assert exc.value.code == 1


# ── Allowed paths pass through ──────────────────────────────────────────────


class TestFindAllowed:
    def test_allows_subdirectory(self, sg):
        target = str(Path.home() / "germline")
        with patch("sys.argv", ["find", target, "-name", "*.py"]):
            with patch("os.path.exists", return_value=True):
                with patch("os.execv") as mock_exec:
                    sg.main()
                    mock_exec.assert_called_once()
                    # Verify it passes all args including -name
                    passed_args = mock_exec.call_args[0][1]
                    assert "-name" in passed_args
                    assert "*.py" in passed_args

    def test_allows_tmp(self, sg):
        with patch("sys.argv", ["find", "/tmp", "-name", "x"]):
            with patch("os.path.exists", return_value=True):
                with patch("os.execv") as mock_exec:
                    sg.main()
                    mock_exec.assert_called_once()

    def test_no_path_passes_through(self, sg):
        """No path arg → stdin mode, calls execv directly."""
        with patch("sys.argv", ["find"]):
            with patch("os.execv") as mock_exec:
                sg.main()
                mock_exec.assert_called_once()
                called_bin = mock_exec.call_args[0][0]
                assert called_bin == "/usr/bin/find"

    def test_relative_path_allowed(self, sg):
        cwd = str(Path.cwd())
        if cwd in (str(Path.home()), "/"):
            pytest.skip("CWD is blocked")
        with patch("sys.argv", ["find", ".", "-name", "test*"]):
            with patch("os.path.exists", return_value=True):
                with patch("os.execv") as mock_exec:
                    sg.main()
                    mock_exec.assert_called_once()


# ── rg fallback ─────────────────────────────────────────────────────────────


class TestFindRgFallback:
    def test_rg_fallback_which(self, sg):
        """rg binary falls back to `which -a rg` if not at standard path."""
        target = str(Path.home() / "germline")
        with patch("sys.argv", ["rg", "pattern", target]):
            with patch("os.path.exists", side_effect=[False, True]):
                with patch(
                    "subprocess.check_output",
                    return_value=b"/usr/local/bin/rg\n/usr/bin/rg\n",
                ):
                    with patch("os.execv") as mock_exec:
                        sg.main()
                        mock_exec.assert_called_once()
                        called_bin = mock_exec.call_args[0][0]
                        assert "rg" in called_bin


# ── Error handling ──────────────────────────────────────────────────────────


class TestFindErrors:
    def test_execv_exception_handled(self, sg, capsys):
        target = str(Path.home() / "germline")
        with patch("sys.argv", ["find", target]):
            with patch("os.path.exists", return_value=True):
                with patch("os.execv", side_effect=Exception("exec failed")):
                    with pytest.raises(SystemExit) as exc:
                        sg.main()
                    assert exc.value.code == 1
        assert "Error" in capsys.readouterr().out
