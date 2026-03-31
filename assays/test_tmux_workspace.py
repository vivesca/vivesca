"""Tests for effectors/tmux-workspace - Set up tmux workspace with tab layout."""

import os
import sys
from unittest.mock import patch, MagicMock, call

import pytest

# Add effectors directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'effectors')))

# Import module with hyphen in filename
import importlib.util
spec = importlib.util.spec_from_file_location("tmux_workspace", 
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'effectors', 'tmux-workspace.py')))
tmux_workspace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tmux_workspace)


# ─────────────────────────────────────────────────────────────────────────────
# Constant tests
# ─────────────────────────────────────────────────────────────────────────────

def test_layouts_defined():
    """Test LAYOUTS has expected structure."""
    assert "default" in tmux_workspace.LAYOUTS
    assert "dev" in tmux_workspace.LAYOUTS


def test_default_layout():
    """Test default layout has expected windows."""
    default = tmux_workspace.LAYOUTS["default"]
    assert len(default) == 2
    names = [w[0] for w in default]
    assert "main" in names
    assert "light" in names


def test_dev_layout():
    """Test dev layout has expected windows."""
    dev = tmux_workspace.LAYOUTS["dev"]
    assert len(dev) == 3
    names = [w[0] for w in dev]
    assert "main" in names
    assert "light" in names
    assert "shell" in names


# ─────────────────────────────────────────────────────────────────────────────
# run helper tests
# ─────────────────────────────────────────────────────────────────────────────

def test_run_default_check():
    """Test run with default check=True."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = tmux_workspace.run("echo test")
        mock_run.assert_called_once_with("echo test", shell=True, capture_output=True, text=True, check=True)


def test_run_no_check():
    """Test run with check=False."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        result = tmux_workspace.run("false", check=False)
        assert result.returncode == 1


# ─────────────────────────────────────────────────────────────────────────────
# get_current_session tests
# ─────────────────────────────────────────────────────────────────────────────

def test_get_current_session_outside_tmux():
    """Test get_current_session returns None outside tmux."""
    with patch.dict(os.environ, {}, clear=True):
        result = tmux_workspace.get_current_session()
        assert result is None


def test_get_current_session_inside_tmux():
    """Test get_current_session returns session name inside tmux."""
    with patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,1234,0"}):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="my-session\n"
            )
            result = tmux_workspace.get_current_session()
            assert result == "my-session"


def test_get_current_session_tmux_error():
    """Test get_current_session returns None on tmux error."""
    with patch.dict(os.environ, {"TMUX": "/tmp/tmux-1000/default,1234,0"}):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout=""
            )
            result = tmux_workspace.get_current_session()
            assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# get_existing_windows tests
# ─────────────────────────────────────────────────────────────────────────────

def test_get_existing_windows_success():
    """Test get_existing_windows returns window names."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="main\nlight\nshell\n"
        )
        result = tmux_workspace.get_existing_windows("test-session")
        assert result == ["main", "light", "shell"]


def test_get_existing_windows_empty():
    """Test get_existing_windows returns empty list on error."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=""
        )
        result = tmux_workspace.get_existing_windows("test-session")
        assert result == []


def test_get_existing_windows_single():
    """Test get_existing_windows with single window."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="main"
        )
        result = tmux_workspace.get_existing_windows("test-session")
        assert result == ["main"]


# ─────────────────────────────────────────────────────────────────────────────
# setup_windows tests
# ─────────────────────────────────────────────────────────────────────────────

def test_setup_windows_renames_first():
    """Test setup_windows renames first window."""
    with patch("tmux_workspace.run") as mock_run:
        with patch("tmux_workspace.get_existing_windows", return_value=["bash"]):
            with patch("builtins.print"):
                tmux_workspace.setup_windows("test-session", "default")
                
                # Should rename first window
                rename_calls = [c for c in mock_run.call_args_list 
                               if "rename-window" in str(c)]
                assert len(rename_calls) > 0


def test_setup_windows_creates_missing():
    """Test setup_windows creates missing windows."""
    with patch("tmux_workspace.run") as mock_run:
        with patch("tmux_workspace.get_existing_windows", return_value=["main"]):
            with patch("builtins.print"):
                tmux_workspace.setup_windows("test-session", "default")
                
                # Should create second window
                new_window_calls = [c for c in mock_run.call_args_list 
                                   if "new-window" in str(c)]
                assert len(new_window_calls) == 1


def test_setup_windows_selects_first():
    """Test setup_windows selects first window at end."""
    with patch("tmux_workspace.run") as mock_run:
        with patch("tmux_workspace.get_existing_windows", return_value=["main", "light"]):
            with patch("builtins.print"):
                tmux_workspace.setup_windows("test-session", "default")
                
                select_calls = [c for c in mock_run.call_args_list 
                               if "select-window" in str(c)]
                assert len(select_calls) == 1
                assert "test-session:1" in str(select_calls[0])


def test_setup_windows_renames_existing():
    """Test setup_windows renames existing windows by index."""
    with patch("tmux_workspace.run") as mock_run:
        with patch("tmux_workspace.get_existing_windows", return_value=["main", "oldname"]):
            with patch("builtins.print"):
                tmux_workspace.setup_windows("test-session", "default")
                
                # Should rename second window to 'light'
                rename_calls = [str(c) for c in mock_run.call_args_list]
                assert any("rename-window" in c and "test-session:2" in c for c in rename_calls)


# ─────────────────────────────────────────────────────────────────────────────
# create_and_attach tests
# ─────────────────────────────────────────────────────────────────────────────

def test_create_and_attach_creates_session():
    """Test create_and_attach creates new session."""
    with patch("tmux_workspace.run") as mock_run:
        with patch("subprocess.run") as mock_subprocess:
            with patch("builtins.print"):
                tmux_workspace.create_and_attach("new-session", "default")
                
                # Should create session with first window
                session_calls = [c for c in mock_run.call_args_list 
                                if "new-session" in str(c)]
                assert len(session_calls) == 1
                assert "-s new-session" in str(session_calls[0])


def test_create_and_attach_creates_additional_windows():
    """Test create_and_attach creates additional windows."""
    with patch("tmux_workspace.run") as mock_run:
        with patch("subprocess.run") as mock_subprocess:
            with patch("builtins.print"):
                tmux_workspace.create_and_attach("new-session", "dev")  # 3 windows
                
                # Should create 2 additional windows (first created with session)
                new_window_calls = [c for c in mock_run.call_args_list 
                                   if "new-window" in str(c) and "new-session" in str(c)]
                assert len(new_window_calls) == 2


def test_create_and_attach_attaches():
    """Test create_and_attach attaches to session."""
    with patch("tmux_workspace.run") as mock_run:
        with patch("subprocess.run") as mock_subprocess:
            with patch("builtins.print"):
                tmux_workspace.create_and_attach("new-session", "default")
                
                # Should attach
                attach_calls = [c for c in mock_subprocess.call_args_list 
                               if "attach-session" in str(c)]
                assert len(attach_calls) == 1


# ─────────────────────────────────────────────────────────────────────────────
# Main function tests
# ─────────────────────────────────────────────────────────────────────────────

def test_main_help():
    """Test main shows help with --help flag."""
    with patch("sys.argv", ["tmux-workspace", "--help"]):
        with patch("builtins.print") as mock_print:
            tmux_workspace.main()
            prints = [str(c) for c in mock_print.call_args_list]
            assert any("Set up tmux workspace" in p for p in prints)


def test_main_h_flag():
    """Test main shows help with -h flag."""
    with patch("sys.argv", ["tmux-workspace", "-h"]):
        with patch("builtins.print") as mock_print:
            tmux_workspace.main()
            prints = [str(c) for c in mock_print.call_args_list]
            assert any("Available layouts" in p for p in prints)


def test_main_inside_tmux():
    """Test main sets up windows when inside tmux."""
    with patch("sys.argv", ["tmux-workspace"]):
        with patch("tmux_workspace.get_current_session", return_value="current-session"):
            with patch("tmux_workspace.setup_windows") as mock_setup:
                with patch("builtins.print"):
                    tmux_workspace.main()
                    mock_setup.assert_called_once_with("current-session", "default")


def test_main_outside_tmux_creates_session():
    """Test main creates new session when outside tmux."""
    with patch("sys.argv", ["tmux-workspace"]):
        with patch("tmux_workspace.get_current_session", return_value=None):
            with patch("tmux_workspace.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1)  # Session doesn't exist
                
                with patch("tmux_workspace.create_and_attach") as mock_create:
                    tmux_workspace.main()
                    mock_create.assert_called_once_with("main", "default")


def test_main_outside_tmux_existing_session():
    """Test main attaches to existing session when outside tmux."""
    with patch("sys.argv", ["tmux-workspace"]):
        with patch("tmux_workspace.get_current_session", return_value=None):
            with patch("tmux_workspace.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)  # Session exists
                
                with patch("tmux_workspace.setup_windows") as mock_setup:
                    with patch("subprocess.run") as mock_subprocess:
                        tmux_workspace.main()
                        mock_setup.assert_called_once_with("main", "default")
                        # Should attach
                        attach_calls = [c for c in mock_subprocess.call_args_list 
                                       if "attach-session" in str(c)]
                        assert len(attach_calls) == 1


def test_main_with_layout_arg():
    """Test main uses specified layout."""
    with patch("sys.argv", ["tmux-workspace", "dev"]):
        with patch("tmux_workspace.get_current_session", return_value="current"):
            with patch("tmux_workspace.setup_windows") as mock_setup:
                with patch("builtins.print"):
                    tmux_workspace.main()
                    mock_setup.assert_called_once_with("current", "dev")


def test_main_with_session_name():
    """Test main creates session with custom name."""
    with patch("sys.argv", ["tmux-workspace", "my-work"]):
        with patch("tmux_workspace.get_current_session", return_value=None):
            with patch("tmux_workspace.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=1)  # Doesn't exist
                
                with patch("tmux_workspace.create_and_attach") as mock_create:
                    tmux_workspace.main()
                    # my-work is not a layout name, so it becomes session name
                    mock_create.assert_called_once_with("my-work", "default")
