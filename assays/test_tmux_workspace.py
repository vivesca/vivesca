"""Tests for effectors/tmux-workspace.py — set up tmux workspace with tab layout."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

EFFECTOR = Path(__file__).resolve().parent.parent / "effectors" / "tmux-workspace.py"

@pytest.fixture()
def mod():
    """Load tmux-workspace.py via exec."""
    ns: dict = {}
    code = EFFECTOR.read_text()
    exec(code, ns)
    return ns


# ── LAYOUTS ─────────────────────────────────────────────────────────────────

class TestLayouts:
    def test_layouts_defined(self, mod):
        assert "default" in mod["LAYOUTS"]
        assert "dev" in mod["LAYOUTS"]

    def test_default_layout_has_main_light(self, mod):
        names = [w[0] for w in mod["LAYOUTS"]["default"]]
        assert names == ["main", "light"]

    def test_dev_layout_has_three_windows(self, mod):
        names = [w[0] for w in mod["LAYOUTS"]["dev"]]
        assert "main" in names
        assert "light" in names
        assert "shell" in names
        assert len(names) == 3


# ── run() helper ────────────────────────────────────────────────────────────

class TestRun:
    def test_run_default_check(self, mod):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            mod["run"]("echo hi")
            mock_run.assert_called_once_with(
                "echo hi", shell=True, capture_output=True, text=True, check=True
            )

    def test_run_no_check(self, mod):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="err")
            result = mod["run"]("false", check=False)
            assert result.returncode == 1


# ── get_current_session ────────────────────────────────────────────────────

class TestGetCurrentSession:
    def test_outside_tmux_returns_none(self, mod):
        with patch.dict(os.environ, {}, clear=True):
            assert mod["get_current_session"]() is None

    def test_inside_tmux_returns_name(self, mod):
        with patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,1234,0"}):
            with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="sess\n")):
                assert mod["get_current_session"]() == "sess"

    def test_tmux_error_returns_none(self, mod):
        with patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,1234,0"}):
            with patch("subprocess.run", return_value=MagicMock(returncode=1, stdout="")):
                assert mod["get_current_session"]() is None


# ── get_existing_windows ────────────────────────────────────────────────────

class TestGetExistingWindows:
    def test_success(self, mod):
        with patch.object(mod, "run", return_value=MagicMock(returncode=0, stdout="a\nb\n")):
            assert mod["get_existing_windows"]("s") == ["a", "b"]

    def test_error_returns_empty(self, mod):
        with patch.object(mod, "run", return_value=MagicMock(returncode=1, stdout="")):
            assert mod["get_existing_windows"]("s") == []

    def test_single_window(self, mod):
        with patch.object(mod, "run", return_value=MagicMock(returncode=0, stdout="main")):
            assert mod["get_existing_windows"]("s") == ["main"]


# ── setup_windows ───────────────────────────────────────────────────────────

class TestSetupWindows:
    def test_renames_first_window(self, mod):
        with patch.object(mod, "run") as mock_run:
            mod["setup_windows"]("sess", "default")
            cmds = [str(c) for c in mock_run.call_args_list]
            assert any("rename-window" in c and "sess:1" in c for c in cmds)

    def test_creates_missing_windows(self, mod):
        with patch.object(mod, "get_existing_windows", return_value=["main"]):
            with patch.object(mod, "run") as mock_run:
                mod["setup_windows"]("sess", "default")
                cmds = [str(c) for c in mock_run.call_args_list]
                assert any("new-window" in c for c in cmds)

    def test_selects_first_window(self, mod):
        with patch.object(mod, "run") as mock_run:
            mod["setup_windows"]("sess", "default")
            cmds = [str(c) for c in mock_run.call_args_list]
            assert any("select-window" in c and "sess:1" in c for c in cmds)

    def test_renames_existing_second_window(self, mod):
        with patch.object(mod, "get_existing_windows", return_value=["main", "old"]):
            with patch.object(mod, "run") as mock_run:
                mod["setup_windows"]("sess", "default")
                cmds = [str(c) for c in mock_run.call_args_list]
                assert any("rename-window" in c and "sess:2" in c for c in cmds)

    def test_dev_creates_two_extra(self, mod):
        """dev layout has 3 windows, so 2 new-window calls when session is empty."""
        with patch.object(mod, "get_existing_windows", return_value=["main"]):
            with patch.object(mod, "run") as mock_run:
                mod["setup_windows"]("sess", "dev")
                nw = [c for c in mock_run.call_args_list if "new-window" in str(c)]
                assert len(nw) == 2


# ── create_and_attach ───────────────────────────────────────────────────────

class TestCreateAndAttach:
    def test_creates_session(self, mod):
        with patch.object(mod, "run") as mock_run:
            with patch("subprocess.run"):
                mod["create_and_attach"]("ns", "default")
                cmds = [str(c) for c in mock_run.call_args_list]
                assert any("new-session" in c and "-s ns" in c for c in cmds)

    def test_creates_additional_windows(self, mod):
        with patch.object(mod, "run") as mock_run:
            with patch("subprocess.run"):
                mod["create_and_attach"]("ns", "dev")
                nw = [c for c in mock_run.call_args_list if "new-window" in str(c) and "ns" in str(c)]
                assert len(nw) == 2  # light + shell

    def test_attaches(self, mod):
        with patch.object(mod, "run"):
            with patch("subprocess.run") as sp:
                mod["create_and_attach"]("ns", "default")
                cmds = [str(c) for c in sp.call_args_list]
                assert any("attach-session" in c for c in cmds)


# ── main ────────────────────────────────────────────────────────────────────

class TestMain:
    def test_help_shows_docstring(self, mod, capsys):
        with patch.object(sys, "argv", ["tmux-workspace", "--help"]):
            mod["main"]()
        assert "tmux workspace" in capsys.readouterr().out.lower()

    def test_h_flag(self, mod, capsys):
        with patch.object(sys, "argv", ["tmux-workspace", "-h"]):
            mod["main"]()
        assert "Available layouts" in capsys.readouterr().out

    def test_inside_tmux_calls_setup(self, mod):
        with patch.object(sys, "argv", ["tmux-workspace"]):
            with patch.object(mod, "get_current_session", return_value="cur"):
                with patch.object(mod, "setup_windows") as sw:
                    mod["main"]()
                    sw.assert_called_once_with("cur", "default")

    def test_outside_tmux_creates_session(self, mod):
        with patch.object(sys, "argv", ["tmux-workspace"]):
            with patch.object(mod, "get_current_session", return_value=None):
                with patch.object(mod, "run", return_value=MagicMock(returncode=1)):
                    with patch.object(mod, "create_and_attach") as ca:
                        mod["main"]()
                        ca.assert_called_once_with("main", "default")

    def test_outside_tmux_existing_session(self, mod):
        with patch.object(sys, "argv", ["tmux-workspace"]):
            with patch.object(mod, "get_current_session", return_value=None):
                with patch.object(mod, "run", return_value=MagicMock(returncode=0)):
                    with patch.object(mod, "setup_windows") as sw:
                        with patch("subprocess.run") as sp:
                            mod["main"]()
                            sw.assert_called_once_with("main", "default")
                            assert any("attach-session" in str(c) for c in sp.call_args_list)

    def test_layout_arg(self, mod):
        with patch.object(sys, "argv", ["tmux-workspace", "dev"]):
            with patch.object(mod, "get_current_session", return_value="cur"):
                with patch.object(mod, "setup_windows") as sw:
                    mod["main"]()
                    sw.assert_called_once_with("cur", "dev")

    def test_custom_session_name(self, mod):
        with patch.object(sys, "argv", ["tmux-workspace", "my-work"]):
            with patch.object(mod, "get_current_session", return_value=None):
                with patch.object(mod, "run", return_value=MagicMock(returncode=1)):
                    with patch.object(mod, "create_and_attach") as ca:
                        mod["main"]()
                        ca.assert_called_once_with("my-work", "default")
