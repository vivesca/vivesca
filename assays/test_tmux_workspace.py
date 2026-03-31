#!/usr/bin/env python3
from __future__ import annotations
"""Tests for effectors/tmux-workspace.py — tmux workspace layout manager."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

EFFECTOR_PATH = Path(__file__).resolve().parents[1] / "effectors" / "tmux-workspace.py"


def _load_module():
    """Load tmux-workspace via exec (effector pattern, not importable)."""
    source = EFFECTOR_PATH.read_text(encoding="utf-8")
    ns: dict = {"__name__": "tmux_workspace", "__file__": str(EFFECTOR_PATH)}
    exec(source, ns)
    return ns


_mod = _load_module()
run = _mod["run"]
get_current_session = _mod["get_current_session"]
get_existing_windows = _mod["get_existing_windows"]
setup_windows = _mod["setup_windows"]
create_and_attach = _mod["create_and_attach"]
main = _mod["main"]
LAYOUTS = _mod["LAYOUTS"]


# ── File-level tests ────────────────────────────────────────────────────────


class TestFileBasics:
    def test_file_exists(self):
        assert EFFECTOR_PATH.exists()
        assert EFFECTOR_PATH.is_file()

    def test_is_python_script(self):
        first_line = EFFECTOR_PATH.read_text().split("\n")[0]
        assert first_line.startswith("#!/usr/bin/env python")

    def test_has_docstring(self):
        source = EFFECTOR_PATH.read_text()
        assert "tmux workspace" in source


# ── LAYOUTS constant tests ──────────────────────────────────────────────────


class TestLayouts:
    def test_default_layout_exists(self):
        assert "default" in LAYOUTS

    def test_dev_layout_exists(self):
        assert "dev" in LAYOUTS

    def test_default_has_two_windows(self):
        assert len(LAYOUTS["default"]) == 2

    def test_dev_has_three_windows(self):
        assert len(LAYOUTS["dev"]) == 3

    def test_default_windows_named(self):
        names = [w[0] for w in LAYOUTS["default"]]
        assert names == ["main", "light"]

    def test_dev_windows_named(self):
        names = [w[0] for w in LAYOUTS["dev"]]
        assert names == ["main", "light", "shell"]


# ── run() helper tests ──────────────────────────────────────────────────────


class TestRun:
    def test_run_calls_subprocess(self):
        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="", stderr="")) as mock:
            result = run("echo hello")
            mock.assert_called_once_with("echo hello", shell=True, capture_output=True, text=True, check=True)

    def test_run_no_check(self):
        with patch("subprocess.run", return_value=MagicMock(returncode=1, stdout="", stderr="err")) as mock:
            result = run("false", check=False)
            assert result.returncode == 1

    def test_run_returns_completed_process(self):
        mock_cp = MagicMock(returncode=0, stdout="out", stderr="")
        with patch("subprocess.run", return_value=mock_cp):
            result = run("true")
            assert result.stdout == "out"


# ── get_current_session tests ───────────────────────────────────────────────


class TestGetCurrentSession:
    def test_outside_tmux(self):
        with patch.dict(os.environ, {}, clear=True):
            assert get_current_session() is None

    def test_inside_tmux(self):
        with patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,1234,0"}):
            with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="sess\n")):
                assert get_current_session() == "sess"

    def test_tmux_error_returns_none(self):
        with patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,1234,0"}):
            with patch("subprocess.run", return_value=MagicMock(returncode=1, stdout="")):
                assert get_current_session() is None


# ── get_existing_windows tests ──────────────────────────────────────────────


class TestGetExistingWindows:
    def test_returns_window_names(self):
        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="main\nlight\n")):
            assert get_existing_windows("s") == ["main", "light"]

    def test_empty_on_error(self):
        with patch("subprocess.run", return_value=MagicMock(returncode=1, stdout="")):
            assert get_existing_windows("s") == []

    def test_single_window(self):
        with patch("subprocess.run", return_value=MagicMock(returncode=0, stdout="main")):
            assert get_existing_windows("s") == ["main"]


# ── setup_windows tests ─────────────────────────────────────────────────────


class TestSetupWindows:
    def test_renames_first_window(self, monkeypatch):
        mock_run = MagicMock()
        monkeypatch.setitem(_mod, "run", mock_run)
        monkeypatch.setitem(_mod, "get_existing_windows", MagicMock(return_value=["old"]))
        setup_windows("sess", "default")
        rename_calls = [c for c in mock_run.call_args_list if "rename-window" in str(c)]
        assert any("sess:1" in str(c) for c in rename_calls)

    def test_creates_missing_window(self, monkeypatch):
        mock_run = MagicMock()
        monkeypatch.setitem(_mod, "run", mock_run)
        monkeypatch.setitem(_mod, "get_existing_windows", MagicMock(return_value=["main"]))
        setup_windows("sess", "default")
        new_calls = [c for c in mock_run.call_args_list if "new-window" in str(c)]
        assert len(new_calls) == 1  # 'light' needs creating

    def test_selects_first_window(self, monkeypatch):
        mock_run = MagicMock()
        monkeypatch.setitem(_mod, "run", mock_run)
        monkeypatch.setitem(_mod, "get_existing_windows", MagicMock(return_value=["main", "light"]))
        setup_windows("sess", "default")
        select_calls = [c for c in mock_run.call_args_list if "select-window" in str(c)]
        assert len(select_calls) == 1
        assert "sess:1" in str(select_calls[0])

    def test_renames_existing_by_index(self, monkeypatch):
        mock_run = MagicMock()
        monkeypatch.setitem(_mod, "run", mock_run)
        monkeypatch.setitem(_mod, "get_existing_windows", MagicMock(return_value=["main", "old"]))
        setup_windows("sess", "default")
        assert any("rename-window" in str(c) and "sess:2" in str(c) for c in mock_run.call_args_list)


# ── create_and_attach tests ─────────────────────────────────────────────────


class TestCreateAndAttach:
    def test_creates_session(self, monkeypatch):
        mock_run = MagicMock()
        monkeypatch.setitem(_mod, "run", mock_run)
        monkeypatch.setitem(_mod, "subprocess", type("sp", (), {"run": MagicMock()})())

        create_and_attach("new-sess", "default")

        session_calls = [c for c in mock_run.call_args_list if "new-session" in str(c)]
        assert len(session_calls) == 1
        assert "-s new-sess" in str(session_calls[0])

    def test_creates_additional_windows_for_dev(self, monkeypatch):
        mock_run = MagicMock()
        monkeypatch.setitem(_mod, "run", mock_run)
        monkeypatch.setitem(_mod, "subprocess", type("sp", (), {"run": MagicMock()})())

        create_and_attach("dev-sess", "dev")

        new_win_calls = [c for c in mock_run.call_args_list if "new-window" in str(c) and "dev-sess" in str(c)]
        assert len(new_win_calls) == 2  # light + shell

    def test_attaches_to_session(self, monkeypatch):
        mock_sp_run = MagicMock()
        monkeypatch.setitem(_mod, "run", MagicMock())
        import subprocess as sp_mod
        monkeypatch.setitem(_mod, "subprocess", sp_mod)

        with patch("subprocess.run", return_value=MagicMock(returncode=0)) as mock_sp:
            create_and_attach("sess", "default")
            attach_calls = [c for c in mock_sp.call_args_list if "attach-session" in str(c)]
            assert len(attach_calls) == 1


# ── main() tests ────────────────────────────────────────────────────────────


class TestMain:
    def test_help_flag(self, capsys):
        with patch("sys.argv", ["tmux-workspace", "--help"]):
            main()
        captured = capsys.readouterr()
        assert "Set up tmux workspace" in captured.out

    def test_h_flag(self, capsys):
        with patch("sys.argv", ["tmux-workspace", "-h"]):
            main()
        captured = capsys.readouterr()
        assert "Available layouts" in captured.out

    def test_inside_tmux_calls_setup(self, monkeypatch):
        monkeypatch.setitem(_mod, "get_current_session", MagicMock(return_value="cur"))
        mock_setup = MagicMock()
        monkeypatch.setitem(_mod, "setup_windows", mock_setup)

        with patch("sys.argv", ["tmux-workspace"]):
            main()

        mock_setup.assert_called_once_with("cur", "default")

    def test_outside_tmux_creates_session(self, monkeypatch):
        monkeypatch.setitem(_mod, "get_current_session", MagicMock(return_value=None))
        monkeypatch.setitem(_mod, "run", MagicMock(return_value=MagicMock(returncode=1)))
        mock_create = MagicMock()
        monkeypatch.setitem(_mod, "create_and_attach", mock_create)

        with patch("sys.argv", ["tmux-workspace"]):
            main()

        mock_create.assert_called_once_with("main", "default")

    def test_outside_tmux_existing_session(self, monkeypatch):
        monkeypatch.setitem(_mod, "get_current_session", MagicMock(return_value=None))
        monkeypatch.setitem(_mod, "run", MagicMock(return_value=MagicMock(returncode=0)))
        mock_setup = MagicMock()
        monkeypatch.setitem(_mod, "setup_windows", mock_setup)

        with patch("sys.argv", ["tmux-workspace"]):
            with patch("subprocess.run"):
                main()

        mock_setup.assert_called_once_with("main", "default")

    def test_layout_arg_inside_tmux(self, monkeypatch):
        monkeypatch.setitem(_mod, "get_current_session", MagicMock(return_value="cur"))
        mock_setup = MagicMock()
        monkeypatch.setitem(_mod, "setup_windows", mock_setup)

        with patch("sys.argv", ["tmux-workspace", "dev"]):
            main()

        mock_setup.assert_called_once_with("cur", "dev")

    def test_non_layout_arg_becomes_session_name(self, monkeypatch):
        monkeypatch.setitem(_mod, "get_current_session", MagicMock(return_value=None))
        monkeypatch.setitem(_mod, "run", MagicMock(return_value=MagicMock(returncode=1)))
        mock_create = MagicMock()
        monkeypatch.setitem(_mod, "create_and_attach", mock_create)

        with patch("sys.argv", ["tmux-workspace", "my-work"]):
            main()

        mock_create.assert_called_once_with("my-work", "default")
