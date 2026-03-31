#!/usr/bin/env python3
"""Tests for commensal effector — mocks all external subprocess calls."""

import pytest
import subprocess
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import sys
import re

# Execute the commensal file directly into the namespace
commensal_path = Path("/home/terry/germline/effectors/commensal")
commensal_code = commensal_path.read_text()
_ns = {}
exec(commensal_code, _ns)

# Make attributes accessible via dot notation
class CommensalModule:
    def __getattr__(self, name):
        return _ns[name]
commensal = CommensalModule()

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

def test_backends_defined():
    """Test all expected backends are defined."""
    assert "opencode" in commensal.BACKENDS
    assert "gemini" in commensal.BACKENDS
    assert "codex" in commensal.BACKENDS

def test_pty_backends_defined():
    """Test PTY backends are correctly marked."""
    assert "opencode" in commensal.PTY_BACKENDS
    assert "codex" in commensal.PTY_BACKENDS
    assert "gemini" not in commensal.PTY_BACKENDS

def test_timeout_floor_set():
    """Test TIMEOUT_FLOOR has values for all backends."""
    for backend in commensal.BACKENDS:
        assert backend in commensal.TIMEOUT_FLOOR

# ---------------------------------------------------------------------------
# Test regex patterns
# ---------------------------------------------------------------------------

def test_ansi_re_matches_ansi_codes():
    """Test ANSI regex matches ANSI escape codes."""
    test_cases = [
        "\x1b[31mred text\x1b[0m",
        "\x1b]0;title\x07",
        "\x1b(B",
    ]
    for test in test_cases:
        matches = commensal._ANSI_RE.findall(test)
        assert len(matches) > 0

def test_ctrl_re_matches_control_chars():
    """Test CTRL regex matches control characters."""
    test_cases = [
        "\x00", "\x01", "\x08", "\x7f",
    ]
    for test in test_cases:
        matches = commensal._CTRL_RE.findall(test)
        assert len(matches) > 0

def test_tui_re_matches_block_elements():
    """Test TUI regex matches block drawing characters."""
    test_cases = ["█▀▄▐░▌▍"]
    for test in test_cases:
        matches = commensal._TUI_RE.findall(test)
        assert len(matches) > 0

# ---------------------------------------------------------------------------
# Test run_direct function
# ---------------------------------------------------------------------------

def test_run_direct_success():
    """Test run_direct returns output and exit code on success."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "  output line 1\noutput line 2  "
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result):
        output, code = commensal.run_direct(["echo", "test"], "/tmp", 30)
        assert code == 0
        assert output == "output line 1\noutput line 2"

def test_run_direct_failure():
    """Test run_direct returns output and non-zero exit code on failure."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "error message"
    
    with patch('subprocess.run', return_value=mock_result):
        output, code = commensal.run_direct(["false"], "/tmp", 30)
        assert code == 1
        assert output == ""

def test_run_direct_removes_claude_env_var():
    """Test run_direct removes CLAUDECODE from environment."""
    with patch.dict('os.environ', {'CLAUDECODE': '1', 'OTHER_VAR': 'value'}, clear=True):
        with patch('subprocess.run', return_value=MagicMock(returncode=0, stdout="", stderr="")) as mock_run:
            commensal.run_direct(["cmd"], "/tmp", 30)
            called_env = mock_run.call_args[1]['env']
            assert 'OTHER_VAR' in called_env
            assert 'CLAUDECODE' not in called_env

# ---------------------------------------------------------------------------
# Test argument parsing
# ---------------------------------------------------------------------------

def test_main_parses_required_args():
    """Test main parses required task argument."""
    with patch('sys.argv', ['commensal', "test task description"]):
        with patch.object(commensal, 'run_pty') as mock_run:
            mock_run.return_value = ("output", 0)
            with patch('subprocess.run') as mock_git:
                mock_git.return_value = MagicMock(stdout="", returncode=0)
                with patch('builtins.print'):
                    with patch('pathlib.Path.write_text'):
                        commensal.main()
                        # Should call with opencode backend and default cwd
                        assert mock_run.called

def test_main_parses_backend_flag():
    """Test main parses -b/--backend flag."""
    for flag in ['-b', '--backend']:
        with patch('sys.argv', ['commensal', flag, 'gemini', "test task"]):
            with patch.object(commensal, 'run_pty') as mock_pty:
                with patch.object(commensal, 'run_direct') as mock_direct:
                    mock_direct.return_value = ("output", 0)
                    with patch('subprocess.run') as mock_git:
                        mock_git.return_value = MagicMock(stdout="", returncode=0)
                        with patch('builtins.print'):
                            with patch('pathlib.Path.write_text'):
                                commensal.main()
                                # gemini doesn't use PTY
                                assert mock_direct.called
                                assert not mock_pty.called

def test_main_parses_custom_cwd():
    """Test main parses --cwd with custom directory."""
    custom_cwd = "/tmp/custom/dir"
    with patch('sys.argv', ['commensal', '--cwd', custom_cwd, "test task"]):
        with patch.object(commensal, 'run_pty') as mock_run:
            mock_run.return_value = ("output", 0)
            with patch('subprocess.run') as mock_git:
                mock_git.return_value = MagicMock(stdout="", returncode=0)
                with patch('builtins.print'):
                    with patch('pathlib.Path.write_text'):
                        commensal.main()
                        # Check cwd was passed through
                        called_args = mock_run.call_args[0][2]
                        assert called_args == custom_cwd

def test_main_parses_custom_timeout():
    """Test main parses --timeout flag."""
    with patch('sys.argv', ['commensal', '--timeout', '300', "test task"]):
        with patch.object(commensal, 'run_pty') as mock_run:
            mock_run.return_value = ("output", 0)
            with patch('subprocess.run') as mock_git:
                mock_git.return_value = MagicMock(stdout="", returncode=0)
                with patch('builtins.print'):
                    with patch('pathlib.Path.write_text'):
                        commensal.main()
                        # Should respect the custom timeout (above floor)
                        called_timeout = mock_run.call_args[0][2]
                        assert called_timeout == max(300, commensal.TIMEOUT_FLOOR['opencode'])

def test_main_applies_timeout_floor():
    """Test main enforces minimum timeout floor per backend."""
    with patch('sys.argv', ['commensal', '--timeout', '10', "test task"]):
        with patch.object(commensal, 'run_pty') as mock_run:
            mock_run.return_value = ("output", 0)
            with patch('subprocess.run') as mock_git:
                mock_git.return_value = MagicMock(stdout="", returncode=0)
                with patch('builtins.print'):
                    with patch('pathlib.Path.write_text'):
                        commensal.main()
                        # floor for opencode is 180, so 10 -> 180
                        called_timeout = mock_run.call_args[0][2]
                        assert called_timeout == commensal.TIMEOUT_FLOOR['opencode']
                        assert called_timeout == 180

# ---------------------------------------------------------------------------
# Test backend routing - PTY vs direct
# ---------------------------------------------------------------------------

def test_opencode_uses_run_pty():
    """Test opencode uses run_pty."""
    with patch('sys.argv', ['commensal', '-b', 'opencode', "test task"]):
        with patch.object(commensal, 'run_pty') as mock_pty:
            mock_pty.return_value = ("output", 0)
            with patch.object(commensal, 'run_direct') as mock_direct:
                with patch('subprocess.run') as mock_git:
                    mock_git.return_value = MagicMock(stdout="", returncode=0)
                    with patch('builtins.print'):
                        with patch('pathlib.Path.write_text'):
                            commensal.main()
                            assert mock_pty.called
                            assert not mock_direct.called

def test_gemini_uses_run_direct():
    """Test gemini uses run_direct."""
    with patch('sys.argv', ['commensal', '-b', 'gemini', "test task"]):
        with patch.object(commensal, 'run_pty') as mock_pty:
            with patch.object(commensal, 'run_direct') as mock_direct:
                mock_direct.return_value = ("output", 0)
                with patch('subprocess.run') as mock_git:
                    mock_git.return_value = MagicMock(stdout="", returncode=0)
                    with patch('builtins.print'):
                        with patch('pathlib.Path.write_text'):
                            commensal.main()
                            assert not mock_pty.called
                            assert mock_direct.called

def test_codex_uses_run_pty():
    """Test codex uses run_pty."""
    with patch('sys.argv', ['commensal', '-b', 'codex', "test task"]):
        with patch.object(commensal, 'run_pty') as mock_pty:
            mock_pty.return_value = ("output", 0)
            with patch.object(commensal, 'run_direct') as mock_direct:
                with patch('subprocess.run') as mock_git:
                    mock_git.return_value = MagicMock(stdout="", returncode=0)
                    with patch('builtins.print'):
                        with patch('pathlib.Path.write_text'):
                            commensal.main()
                            assert mock_pty.called
                            assert not mock_direct.called

# ---------------------------------------------------------------------------
# Test output cleaning in run_pty
# ---------------------------------------------------------------------------

def test_output_cleans_ansi_codes():
    """Test run_pty cleans ANSI codes from output."""
    # We can't easily test PTY without actually creating a PTY
    # but let's test the output cleaning logic directly
    dirty_output = "\x1b[31mred\x1b[0m text"
    clean = commensal._ANSI_RE.sub('', dirty_output)
    clean = commensal._CTRL_RE.sub('', clean)
    clean = commensal._TUI_RE.sub(' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    assert clean == "red text"

def test_output_cleans_tui_blocks():
    """Test TUI block characters are removed."""
    dirty_output = "█▓▒░ selection ░▒▓█"
    clean = commensal._ANSI_RE.sub('', dirty_output)
    clean = commensal._CTRL_RE.sub('', clean)
    clean = commensal._TUI_RE.sub(' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    # All the blocks become spaces, collapsed to single space
    assert "selection" in clean

# ---------------------------------------------------------------------------
# Test git diff output
# ---------------------------------------------------------------------------

def test_main_shows_git_diff_when_files_modified():
    """Test main shows git diff when files were modified."""
    with patch('sys.argv', ['commensal', "test task"]):
        with patch.object(commensal, 'run_pty', return_value=("output", 0)):
            mock_diff = MagicMock()
            mock_diff.stdout = " file1.txt | 2 +-\n 1 file changed, 1 insertion(+), 1 deletion(-)\n "
            mock_diff.returncode = 0
            with patch('subprocess.run', return_value=mock_diff):
                with patch('builtins.print') as mock_print:
                    with patch('pathlib.Path.write_text'):
                        commensal.main()
                        # Should have printed the modified files
                        printed = [str(call[0]) for call in mock_print.call_args_list]
                        assert any("Files modified" in p for p in printed)

def test_main_handles_git_diff_error():
    """Test main handles git diff failure gracefully."""
    with patch('sys.argv', ['commensal', "test task"]):
        with patch.object(commensal, 'run_pty', return_value=("output", 0)):
            with patch('subprocess.run', side_effect=Exception("git not found")):
                with patch('builtins.print'):
                    with patch('pathlib.Path.write_text'):
                        # Should not raise exception
                        commensal.main()
                        assert True

# ---------------------------------------------------------------------------
# Test output saving
# ---------------------------------------------------------------------------

def test_main_saves_output_when_long():
    """Test long output is saved to tmp directory."""
    long_output = "x" * 1000  # longer than 50 chars
    with patch('sys.argv', ['commensal', "test task"]):
        with patch.object(commensal, 'run_pty', return_value=(long_output, 0)):
            with patch('subprocess.run', return_value=MagicMock(stdout="", returncode=0)):
                with patch('builtins.print'):
                    with patch('pathlib.Path.write_text') as mock_write:
                        commensal.main()
                        assert mock_write.called

def test_main_exit_code_propagation():
    """Test main displays the correct exit code."""
    exit_code = 123
    with patch('sys.argv', ['commensal', "test task"]):
        with patch.object(commensal, 'run_pty', return_value=("output", exit_code)):
            with patch('subprocess.run', return_value=MagicMock(stdout="", returncode=0)):
                with patch('builtins.print') as mock_print:
                    with patch('pathlib.Path.write_text'):
                        commensal.main()
                        printed = [str(call[0]) for call in mock_print.call_args_list]
                        assert any(f"Done (exit {exit_code})" in p for p in printed)
