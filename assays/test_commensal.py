"""Tests for effectors/commensal - Route coding task to free model backends."""

import os
import sys
import time
from unittest.mock import patch, MagicMock, call

import pytest

# Add effectors directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'effectors')))

import commensal


# ─────────────────────────────────────────────────────────────────────────────
# Constant tests
# ─────────────────────────────────────────────────────────────────────────────

def test_home_path():
    """Test HOME is set."""
    assert commensal.HOME.exists()


def test_backends_defined():
    """Test all backends are defined."""
    assert "opencode" in commensal.BACKENDS
    assert "gemini" in commensal.BACKENDS
    assert "codex" in commensal.BACKENDS


def test_pty_backends():
    """Test PTY backends are identified correctly."""
    assert "opencode" in commensal.PTY_BACKENDS
    assert "codex" in commensal.PTY_BACKENDS
    assert "gemini" not in commensal.PTY_BACKENDS


def test_timeout_floor():
    """Test timeout floor values are set."""
    assert commensal.TIMEOUT_FLOOR["opencode"] == 180
    assert commensal.TIMEOUT_FLOOR["gemini"] == 120
    assert commensal.TIMEOUT_FLOOR["codex"] == 180


# ─────────────────────────────────────────────────────────────────────────────
# Regex tests
# ─────────────────────────────────────────────────────────────────────────────

def test_ansi_re_matches_escape_codes():
    """Test _ANSI_RE matches ANSI escape codes."""
    assert commensal._ANSI_RE.search("\x1b[32m")  # Green
    assert commensal._ANSI_RE.search("\x1b[0m")   # Reset
    assert commensal._ANSI_RE.search("\x1b[1;31m")  # Bold red


def test_ctrl_re_matches_control_chars():
    """Test _CTRL_RE matches control characters."""
    assert commensal._CTRL_RE.search("\x00")  # NUL
    assert commensal._CTRL_RE.search("\x07")  # BEL
    assert not commensal._CTRL_RE.search("A")  # Normal char


def test_tui_re_matches_box_chars():
    """Test _TUI_RE matches TUI box drawing characters."""
    assert commensal._TUI_RE.search("█")
    assert commensal._TUI_RE.search("▀")
    assert commensal._TUI_RE.search("░")


# ─────────────────────────────────────────────────────────────────────────────
# run_direct tests
# ─────────────────────────────────────────────────────────────────────────────

def test_run_direct_success():
    """Test run_direct returns output and exit code."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="  output text  \n",
            returncode=0
        )
        output, code = commensal.run_direct(
            ["echo", "test"], "/tmp", 60
        )
        assert output == "output text"
        assert code == 0


def test_run_direct_strips_claud_ecode():
    """Test run_direct removes CLAUDECODE from env."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        commensal.run_direct(["test"], "/tmp", 60)
        call_env = mock_run.call_args[1]["env"]
        assert "CLAUDECODE" not in call_env


def test_run_direct_nonzero_exit():
    """Test run_direct returns nonzero exit code."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout="error output",
            returncode=1
        )
        output, code = commensal.run_direct(["test"], "/tmp", 60)
        assert code == 1


# ─────────────────────────────────────────────────────────────────────────────
# run_pty tests
# ─────────────────────────────────────────────────────────────────────────────

def test_run_pty_success():
    """Test run_pty returns cleaned output."""
    with patch("pty.openpty") as mock_openpty:
        mock_openpty.return_value = (10, 11)  # master, slave fd
        
        with patch("os.close") as mock_close:
            with patch("subprocess.Popen") as mock_popen:
                mock_proc = MagicMock()
                mock_proc.poll.return_value = 0  # Process done
                mock_proc.returncode = 0
                mock_popen.return_value = mock_proc
                
                with patch("select.select") as mock_select:
                    # No data to read, just exit
                    mock_select.return_value = ([], [], [])
                    
                    with patch("os.read") as mock_read:
                        output, code = commensal.run_pty(
                            ["opencode", "--prompt", "test"], "/tmp", 60
                        )
                        assert code == 0


def test_run_pty_cleans_ansi():
    """Test run_pty strips ANSI codes from output."""
    with patch("pty.openpty") as mock_openpty:
        mock_openpty.return_value = (10, 11)
        
        with patch("os.close"):
            with patch("subprocess.Popen") as mock_popen:
                mock_proc = MagicMock()
                mock_proc.poll.side_effect = [None, 0]  # First not done, then done
                mock_proc.returncode = 0
                mock_popen.return_value = mock_proc
                
                with patch("select.select") as mock_select:
                    mock_select.side_effect = [
                        ([10], [], []),  # Data available
                        ([], [], []),     # No more data
                    ]
                    
                    with patch("os.read") as mock_read:
                        mock_read.return_value = b"\x1b[32mHello\x1b[0m World"
                        
                        output, code = commensal.run_pty(
                            ["test"], "/tmp", 60
                        )
                        assert "\x1b[" not in output
                        assert "Hello" in output


def test_run_pty_timeout_kills_process():
    """Test run_pty kills process on timeout."""
    with patch("pty.openpty") as mock_openpty:
        mock_openpty.return_value = (10, 11)
        
        with patch("os.close"):
            with patch("subprocess.Popen") as mock_popen:
                mock_proc = MagicMock()
                mock_proc.poll.return_value = None  # Still running
                mock_proc.returncode = None
                mock_popen.return_value = mock_proc
                
                with patch("select.select") as mock_select:
                    mock_select.return_value = ([], [], [])  # No data
                    
                    with patch("time.time") as mock_time:
                        # Simulate timeout
                        mock_time.side_effect = [0, 1000]  # Way past deadline
                        
                        output, code = commensal.run_pty(
                            ["test"], "/tmp", 60
                        )
                        mock_proc.kill.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# Main function tests
# ─────────────────────────────────────────────────────────────────────────────

def test_main_default_backend():
    """Test main uses opencode as default backend."""
    with patch("sys.argv", ["commensal", "test task"]):
        with patch("commensal.run_pty") as mock_run:
            mock_run.return_value = ("output", 0)
            
            with patch("subprocess.run") as mock_git:
                mock_git.return_value = MagicMock(stdout="", returncode=0)
                
                with patch("builtins.print"):
                    commensal.main()
                    
                    mock_run.assert_called_once()
                    call_args = mock_run.call_args[0][0]
                    assert "opencode" in call_args


def test_main_gemini_backend():
    """Test main uses run_direct for gemini backend."""
    with patch("sys.argv", ["commensal", "-b", "gemini", "test task"]):
        with patch("commensal.run_direct") as mock_run:
            mock_run.return_value = ("output", 0)
            
            with patch("subprocess.run") as mock_git:
                mock_git.return_value = MagicMock(stdout="", returncode=0)
                
                with patch("builtins.print"):
                    commensal.main()
                    
                    mock_run.assert_called_once()
                    call_args = mock_run.call_args[0][0]
                    assert "gemini" in call_args


def test_main_custom_cwd():
    """Test main respects --cwd flag."""
    with patch("sys.argv", ["commensal", "--cwd", "/custom/path", "test task"]):
        with patch("commensal.run_pty") as mock_run:
            mock_run.return_value = ("output", 0)
            
            with patch("subprocess.run") as mock_git:
                mock_git.return_value = MagicMock(stdout="", returncode=0)
                
                with patch("builtins.print"):
                    commensal.main()
                    
                    assert mock_run.call_args[0][1] == "/custom/path"


def test_main_custom_timeout():
    """Test main respects --timeout flag."""
    with patch("sys.argv", ["commensal", "--timeout", "300", "test task"]):
        with patch("commensal.run_pty") as mock_run:
            mock_run.return_value = ("output", 0)
            
            with patch("subprocess.run") as mock_git:
                mock_git.return_value = MagicMock(stdout="", returncode=0)
                
                with patch("builtins.print"):
                    commensal.main()
                    
                    assert mock_run.call_args[0][2] == 300


def test_main_timeout_floor_applied():
    """Test main applies timeout floor for backends."""
    with patch("sys.argv", ["commensal", "-b", "opencode", "--timeout", "30", "test task"]):
        # opencode has timeout floor of 180
        with patch("commensal.run_pty") as mock_run:
            mock_run.return_value = ("output", 0)
            
            with patch("subprocess.run") as mock_git:
                mock_git.return_value = MagicMock(stdout="", returncode=0)
                
                with patch("builtins.print"):
                    commensal.main()
                    
                    # Should use floor of 180, not 30
                    assert mock_run.call_args[0][2] == 180


def test_main_shows_modified_files():
    """Test main shows git diff when files modified."""
    with patch("sys.argv", ["commensal", "test task"]):
        with patch("commensal.run_pty") as mock_run:
            mock_run.return_value = ("output", 0)
            
            with patch("subprocess.run") as mock_git:
                mock_git.return_value = MagicMock(
                    stdout="file1.py | 5 +-\nfile2.py | 10 ++--\n",
                    returncode=0
                )
                
                with patch("builtins.print") as mock_print:
                    commensal.main()
                    
                    prints = [str(c) for c in mock_print.call_args_list]
                    assert any("Files modified" in p for p in prints)


def test_main_saves_long_output():
    """Test main saves output to file when long."""
    with patch("sys.argv", ["commensal", "test task"]):
        with patch("commensal.run_pty") as mock_run:
            # Output longer than 50 chars
            mock_run.return_value = ("x" * 100, 0)
            
            with patch("subprocess.run") as mock_git:
                mock_git.return_value = MagicMock(stdout="", returncode=0)
                
                with patch("builtins.print"):
                    with patch("pathlib.Path.write_text") as mock_write:
                        commensal.main()
                        mock_write.assert_called_once()
