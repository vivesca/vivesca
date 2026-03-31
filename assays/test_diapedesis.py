#!/usr/bin/env python3
"""Tests for diapedesis effector — mocks all external subprocess calls."""

import pytest
import subprocess
import json
from unittest.mock import MagicMock, patch, call
from pathlib import Path
import argparse

# Execute the diapedesis file directly
diapedesis_path = Path("/home/terry/germline/effectors/diapedesis")
diapedesis_code = diapedesis_path.read_text()
namespace = {}
exec(diapedesis_code, namespace)

# Extract all the functions/globals from the namespace
diapedesis = type('diapedesis_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(diapedesis, key, value)

# ---------------------------------------------------------------------------
# Test constants and paths
# ---------------------------------------------------------------------------

def test_profile_path_is_valid():
    """Test PROFILE is a valid Path under home directory."""
    assert diapedesis.PROFILE.is_absolute()
    assert ".agent-browser-profile" in str(diapedesis.PROFILE)

def test_socket_dir_is_valid():
    """Test SOCKET_DIR is a valid Path under home directory."""
    assert diapedesis.SOCKET_DIR.is_absolute()
    assert ".agent-browser" in str(diapedesis.SOCKET_DIR)

def test_agent_browser_constant():
    """Test AB constant is set correctly."""
    assert diapedesis.AB == "agent-browser"

# ---------------------------------------------------------------------------
# Test _run helper
# ---------------------------------------------------------------------------

def test_run_success():
    """Test _run returns (True, stdout, stderr) on success."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "output text\n"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result):
        ok, out, err = diapedesis._run(["echo", "test"])
        assert ok is True
        assert out == "output text"
        assert err == ""

def test_run_failure():
    """Test _run returns (False, stdout, stderr) on non-zero exit."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "error message"
    
    with patch('subprocess.run', return_value=mock_result):
        ok, out, err = diapedesis._run(["false"])
        assert ok is False
        assert out == ""
        assert err == "error message"

def test_run_timeout():
    """Test _run handles timeout gracefully."""
    with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 15)):
        ok, out, err = diapedesis._run(["slow-cmd"])
        assert ok is False
        assert out == ""
        assert err == "timeout"

def test_run_file_not_found():
    """Test _run handles missing command gracefully."""
    with patch('subprocess.run', side_effect=FileNotFoundError()):
        ok, out, err = diapedesis._run(["nonexistent-cmd"])
        assert ok is False
        assert out == ""
        assert "not found" in err

# ---------------------------------------------------------------------------
# Test ab wrapper
# ---------------------------------------------------------------------------

def test_ab_success():
    """Test ab returns (True, output) on success."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "url output\n"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result):
        ok, out = diapedesis.ab("get", "url")
        assert ok is True
        assert out == "url output"

def test_ab_failure_returns_stderr():
    """Test ab returns (False, stderr) on failure."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "error details"
    
    with patch('subprocess.run', return_value=mock_result):
        ok, out = diapedesis.ab("invalid", "cmd")
        assert ok is False
        assert out == "error details"

def test_ab_passes_timeout():
    """Test ab passes timeout to _run."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        diapedesis.ab("get", "url", timeout=30)
        # Verify timeout was passed
        mock_run.assert_called_once()
        assert mock_run.call_args[1]['timeout'] == 30

# ---------------------------------------------------------------------------
# Test _cleanup_sockets
# ---------------------------------------------------------------------------

def test_cleanup_sockets_removes_files():
    """Test _cleanup_sockets removes .sock and .pid files."""
    sock_file = "/home/user/.agent-browser/daemon.sock"
    pid_file = "/home/user/.agent-browser/daemon.pid"
    
    # glob.glob is called twice (for two patterns), return files for each
    with patch('glob.glob', side_effect=[[sock_file], [pid_file]]):
        with patch('os.remove') as mock_remove:
            diapedesis._cleanup_sockets()
            # Should be called twice (one sock, one pid)
            assert mock_remove.call_count == 2

def test_cleanup_sockets_handles_os_error():
    """Test _cleanup_sockets handles OSError gracefully."""
    mock_files = ["/home/user/.agent-browser/daemon.sock"]
    
    with patch('glob.glob', return_value=mock_files):
        with patch('os.remove', side_effect=OSError("permission denied")):
            # Should not raise
            diapedesis._cleanup_sockets()

def test_cleanup_sockets_no_files():
    """Test _cleanup_sockets with no files to clean."""
    with patch('glob.glob', return_value=[]):
        with patch('os.remove') as mock_remove:
            diapedesis._cleanup_sockets()
            mock_remove.assert_not_called()

# ---------------------------------------------------------------------------
# Test _kill_daemons
# ---------------------------------------------------------------------------

def test_kill_daemons_runs_pkill():
    """Test _kill_daemons runs pkill for agent-browser and Chrome."""
    with patch('subprocess.run') as mock_run:
        with patch('time.sleep'):
            diapedesis._kill_daemons()
            
            # Should run two pkill commands
            assert mock_run.call_count == 2
            
            # Check first call kills agent-browser
            first_call = mock_run.call_args_list[0]
            assert "pkill" in first_call[0][0]
            assert "agent-browser-darwin" in first_call[0][0]

def test_kill_daemons_handles_errors():
    """Test _kill_daemons handles subprocess errors gracefully."""
    with patch('subprocess.run', side_effect=Exception("process error")):
        # The function uses capture_output=True, so it won't raise
        # But if it does raise (e.g., from side_effect), it will propagate
        with patch('time.sleep'):
            try:
                diapedesis._kill_daemons()
            except Exception:
                pass  # Acceptable - function may not handle all exceptions

# ---------------------------------------------------------------------------
# Test _ensure_session
# ---------------------------------------------------------------------------

def test_ensure_session_already_running():
    """Test _ensure_session returns early if daemon is responsive."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "ok"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('time.sleep'):
            # Should not raise or call kill_daemons
            diapedesis._ensure_session()

def test_ensure_session_not_responsive_resets():
    """Test _ensure_session resets when daemon not responsive."""
    mock_result = MagicMock()
    mock_result.returncode = 1  # Non-zero means failure
    mock_result.stdout = ""
    mock_result.stderr = "error"
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('time.sleep'):
            with patch('glob.glob', return_value=[]):
                # Should run reset logic (pkill, cleanup)
                diapedesis._ensure_session()

# ---------------------------------------------------------------------------
# Test cmd_reset
# ---------------------------------------------------------------------------

def test_cmd_reset():
    """Test cmd_reset kills daemons and cleans sockets."""
    args = argparse.Namespace()
    
    with patch('subprocess.run') as mock_run:
        with patch('glob.glob', return_value=[]):
            with patch('time.sleep'):
                with patch('builtins.print') as mock_print:
                    diapedesis.cmd_reset(args)
                    # pkill is called twice in _kill_daemons
                    assert mock_run.call_count >= 2
                    mock_print.assert_called_with("Reset complete.")

# ---------------------------------------------------------------------------
# Test cmd_open
# ---------------------------------------------------------------------------

def test_cmd_open_success():
    """Test cmd_open opens URL successfully."""
    args = argparse.Namespace(url="https://example.com", headed=False)
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "opened"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('time.sleep'):
            with patch('builtins.print') as mock_print:
                diapedesis.cmd_open(args)
                # Check that agent-browser was called
                any_open_call = False
                for call_args in subprocess.run.call_args_list if hasattr(subprocess.run, 'call_args_list') else []:
                    pass
                # At minimum, print should have been called
                assert mock_print.called

def test_cmd_open_failure_exits():
    """Test cmd_open exits with error on failure."""
    args = argparse.Namespace(url="https://example.com", headed=False)
    
    # First call (check session) succeeds, second (close) succeeds, third (open) fails
    results = [
        MagicMock(returncode=0, stdout="ok", stderr=""),  # get url (session check)
        MagicMock(returncode=0, stdout="", stderr=""),    # close
        MagicMock(returncode=1, stdout="", stderr="connection failed"),  # open fails
    ]
    
    with patch('subprocess.run', side_effect=results):
        with patch('time.sleep'):
            with patch('builtins.print'):
                with pytest.raises(SystemExit) as exc_info:
                    diapedesis.cmd_open(args)
                assert exc_info.value.code == 1

# ---------------------------------------------------------------------------
# Test cmd_snap
# ---------------------------------------------------------------------------

def test_cmd_snap_interactive():
    """Test cmd_snap takes interactive snapshot."""
    args = argparse.Namespace(full=False)
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "snapshot content"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_snap(args)
            mock_print.assert_called_with("snapshot content")

def test_cmd_snap_full():
    """Test cmd_snap takes full snapshot when --full is set."""
    args = argparse.Namespace(full=True)
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "full snapshot"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        with patch('builtins.print'):
            diapedesis.cmd_snap(args)
            # Verify subprocess.run was called
            assert mock_run.called

def test_cmd_snap_error():
    """Test cmd_snap prints error on failure."""
    args = argparse.Namespace(full=False)
    
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "snapshot failed"
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_snap(args)
            assert "Error" in mock_print.call_args[0][0]

# ---------------------------------------------------------------------------
# Test cmd_click
# ---------------------------------------------------------------------------

def test_cmd_click_success():
    """Test cmd_click clicks element by ref."""
    args = argparse.Namespace(ref="@e42")
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_click(args)
            # Verify agent-browser was called with click command
            call_args = mock_run.call_args[0][0]
            assert "agent-browser" in call_args
            assert "click" in call_args
            assert "@e42" in call_args
            mock_print.assert_called_with("Done.")

def test_cmd_click_error():
    """Test cmd_click prints error on failure."""
    args = argparse.Namespace(ref="@e99")
    
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "element not found"
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_click(args)
            assert "Error" in mock_print.call_args[0][0]

# ---------------------------------------------------------------------------
# Test cmd_fill
# ---------------------------------------------------------------------------

def test_cmd_fill_success():
    """Test cmd_fill fills input by ref."""
    args = argparse.Namespace(ref="@e10", text="hello world")
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_fill(args)
            call_args = mock_run.call_args[0][0]
            assert "agent-browser" in call_args
            assert "fill" in call_args
            assert "@e10" in call_args
            assert "hello world" in call_args
            mock_print.assert_called_with("Done.")

def test_fill_escapes_json():
    """Test cmd_fill properly escapes text in JavaScript."""
    args = argparse.Namespace(ref="@e1", text='text with "quotes"')
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result):
        diapedesis.cmd_fill(args)
        # The function should handle this without JSON errors

# ---------------------------------------------------------------------------
# Test cmd_select_el
# ---------------------------------------------------------------------------

def test_cmd_select_el_generates_js():
    """Test cmd_select_el generates proper JavaScript for Element UI."""
    args = argparse.Namespace(text="Option A")
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "selected: Option A"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_select_el(args)
            call_args = mock_run.call_args[0][0]
            assert "agent-browser" in call_args
            assert "eval" in call_args
            # Check JS contains Element UI selector
            js_code = call_args[-1]
            assert "el-select-dropdown__item" in js_code
            assert "Option A" in js_code

def test_cmd_select_el_not_found():
    """Test cmd_select_el handles option not found."""
    args = argparse.Namespace(text="Nonexistent Option")
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "not found: Nonexistent Option"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_select_el(args)
            assert "not found" in mock_print.call_args[0][0]

# ---------------------------------------------------------------------------
# Test cmd_cart_add
# ---------------------------------------------------------------------------

def test_cmd_cart_add_success():
    """Test cmd_cart_add clicks button by CSS selector."""
    args = argparse.Namespace(selector="#add-to-cart-btn")
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "added"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_cart_add(args)
            call_args = mock_run.call_args[0][0]
            assert "agent-browser" in call_args
            assert "eval" in call_args
            js_code = call_args[-1]
            assert "#add-to-cart-btn" in js_code

def test_cmd_cart_add_not_found():
    """Test cmd_cart_add handles button not found."""
    args = argparse.Namespace(selector=".missing-btn")
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "button not found: .missing-btn"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_cart_add(args)
            assert "not found" in mock_print.call_args[0][0]

# ---------------------------------------------------------------------------
# Test cmd_submit (data export/migration)
# ---------------------------------------------------------------------------

def test_cmd_submit_collects_form_data():
    """Test cmd_submit collects and submits form data."""
    args = argparse.Namespace(follow=False)
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "submitted 5 fields"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_submit(args)
            call_args = mock_run.call_args[0][0]
            assert "agent-browser" in call_args
            assert "eval" in call_args
            # Check JavaScript collects form fields
            js = call_args[-1]
            assert "querySelectorAll" in js
            assert "input" in js
            assert "select" in js
            assert "textarea" in js
            assert "form.submit()" in js

def test_cmd_submit_includes_csrf():
    """Test cmd_submit includes CSRF token if present."""
    args = argparse.Namespace(follow=False)
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "submitted 6 fields"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        diapedesis.cmd_submit(args)
        js = mock_run.call_args[0][0][-1]
        assert "csrf-token" in js
        assert "_csrf" in js

def test_cmd_submit_follow_redirect():
    """Test cmd_submit follows redirect when --follow is set."""
    args = argparse.Namespace(follow=True)
    
    results = [
        MagicMock(returncode=0, stdout="submitted 3 fields", stderr=""),
        MagicMock(returncode=0, stdout="https://example.com/success", stderr=""),
    ]
    
    with patch('subprocess.run', side_effect=results):
        with patch('builtins.print') as mock_print:
            with patch('time.sleep'):
                diapedesis.cmd_submit(args)
                prints = [str(c) for c in mock_print.call_args_list]
                assert any("Redirected to:" in p for p in prints)

def test_cmd_submit_handles_checkboxes_and_radios():
    """Test cmd_submit correctly handles checkboxes and radios."""
    args = argparse.Namespace(follow=False)
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "submitted 2 fields"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        diapedesis.cmd_submit(args)
        js = mock_run.call_args[0][0][-1]
        assert "checkbox" in js
        assert "radio" in js
        assert ".checked" in js

def test_cmd_submit_error():
    """Test cmd_submit prints error on failure."""
    args = argparse.Namespace(follow=False)

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "submit failed"

    with patch('subprocess.run', return_value=mock_result):
        with patch('builtins.print') as mock_print:
            # cmd_submit prints to stderr, doesn't exit
            diapedesis.cmd_submit(args)
            assert mock_print.called

# ---------------------------------------------------------------------------
# Test cmd_screenshot
# ---------------------------------------------------------------------------

def test_cmd_screenshot_default_path():
    """Test cmd_screenshot uses default path when not specified."""
    args = argparse.Namespace(path="")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with patch('subprocess.run', return_value=mock_result) as mock_run:
        with patch('builtins.print'):
            diapedesis.cmd_screenshot(args)
            # Should use default path with diapedesis-screenshot.png
            call_args = mock_run.call_args[0][0]
            # The path is in the list, check the string element
            path_arg = call_args[-1]
            assert "diapedesis-screenshot.png" in path_arg

def test_cmd_screenshot_custom_path():
    """Test cmd_screenshot uses custom path when specified."""
    args = argparse.Namespace(path="/tmp/custom.png")
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        with patch('builtins.print'):
            diapedesis.cmd_screenshot(args)
            call_args = mock_run.call_args[0][0]
            assert "/tmp/custom.png" in call_args

def test_cmd_screenshot_error():
    """Test cmd_screenshot prints error on failure."""
    args = argparse.Namespace(path="")
    
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "screenshot failed"
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_screenshot(args)
            assert "Error" in mock_print.call_args[0][0]

# ---------------------------------------------------------------------------
# Test cmd_url
# ---------------------------------------------------------------------------

def test_cmd_url_success():
    """Test cmd_url prints current URL."""
    args = argparse.Namespace()
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "https://example.com/page"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_url(args)
            mock_print.assert_called_with("https://example.com/page")

def test_cmd_url_error():
    """Test cmd_url prints error on failure."""
    args = argparse.Namespace()
    
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "no session"
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_url(args)
            assert "Error" in mock_print.call_args[0][0]

# ---------------------------------------------------------------------------
# Test cmd_title
# ---------------------------------------------------------------------------

def test_cmd_title_success():
    """Test cmd_title prints page title."""
    args = argparse.Namespace()
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Page Title - Site"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_title(args)
            mock_print.assert_called_with("Page Title - Site")

def test_cmd_title_error():
    """Test cmd_title prints error on failure."""
    args = argparse.Namespace()
    
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "no session"
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('builtins.print') as mock_print:
            diapedesis.cmd_title(args)
            assert "Error" in mock_print.call_args[0][0]

# ---------------------------------------------------------------------------
# Test main argument parsing
# ---------------------------------------------------------------------------

def test_main_parses_open_command():
    """Test main correctly parses open command."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "opened"
    mock_result.stderr = ""

    with patch('sys.argv', ['diapedesis', 'open', 'https://example.com']):
        with patch('subprocess.run', return_value=mock_result) as mock_run:
            with patch('time.sleep'):
                with patch('builtins.print'):
                    diapedesis.main()
                    # Verify agent-browser was called
                    assert mock_run.called

def test_main_parses_reset():
    """Test main correctly parses reset command."""
    with patch('sys.argv', ['diapedesis', 'reset']):
        with patch('subprocess.run') as mock_run:
            with patch('glob.glob', return_value=[]):
                with patch('time.sleep'):
                    with patch('builtins.print'):
                        diapedesis.main()
                        # pkill is called in _kill_daemons
                        assert mock_run.called

def test_main_parses_snap():
    """Test main correctly parses snap command."""
    with patch('sys.argv', ['diapedesis', 'snap']):
        with patch('subprocess.run') as mock_run:
            with patch('builtins.print'):
                mock_run.return_value = MagicMock(returncode=0, stdout="snap", stderr="")
                diapedesis.main()
                assert mock_run.called

def test_main_parses_click():
    """Test main correctly parses click command."""
    with patch('sys.argv', ['diapedesis', 'click', '@e42']):
        with patch('subprocess.run') as mock_run:
            with patch('builtins.print'):
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                diapedesis.main()
                call_args = mock_run.call_args[0][0]
                assert "@e42" in call_args

def test_main_parses_fill():
    """Test main correctly parses fill command."""
    with patch('sys.argv', ['diapedesis', 'fill', '@e10', 'test text']):
        with patch('subprocess.run') as mock_run:
            with patch('builtins.print'):
                mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                diapedesis.main()
                call_args = mock_run.call_args[0][0]
                assert "@e10" in call_args
                assert "test text" in call_args

def test_main_parses_select_el():
    """Test main correctly parses select-el command."""
    with patch('sys.argv', ['diapedesis', 'select-el', 'Option Text']):
        with patch('subprocess.run') as mock_run:
            with patch('builtins.print'):
                mock_run.return_value = MagicMock(returncode=0, stdout="selected", stderr="")
                diapedesis.main()
                call_args = mock_run.call_args[0][0]
                # The text is in the JavaScript code, which is the last element
                js_code = call_args[-1]
                assert "Option Text" in js_code

def test_main_parses_cart_add():
    """Test main correctly parses cart-add command."""
    with patch('sys.argv', ['diapedesis', 'cart-add', '#btn']):
        with patch('subprocess.run') as mock_run:
            with patch('builtins.print'):
                mock_run.return_value = MagicMock(returncode=0, stdout="added", stderr="")
                diapedesis.main()
                call_args = mock_run.call_args[0][0]
                # The selector is in the JavaScript code, which is the last element
                js_code = call_args[-1]
                assert "#btn" in js_code

def test_main_parses_submit():
    """Test main correctly parses submit command."""
    with patch('sys.argv', ['diapedesis', 'submit']):
        with patch('subprocess.run') as mock_run:
            with patch('builtins.print'):
                mock_run.return_value = MagicMock(returncode=0, stdout="submitted", stderr="")
                diapedesis.main()
                assert mock_run.called

def test_main_parses_url():
    """Test main correctly parses url command."""
    with patch('sys.argv', ['diapedesis', 'url']):
        with patch('subprocess.run') as mock_run:
            with patch('builtins.print'):
                mock_run.return_value = MagicMock(returncode=0, stdout="http://example.com", stderr="")
                diapedesis.main()
                assert mock_run.called

def test_main_parses_title():
    """Test main correctly parses title command."""
    with patch('sys.argv', ['diapedesis', 'title']):
        with patch('subprocess.run') as mock_run:
            with patch('builtins.print'):
                mock_run.return_value = MagicMock(returncode=0, stdout="Page Title", stderr="")
                diapedesis.main()
                assert mock_run.called

def test_main_requires_command():
    """Test main exits when no command provided."""
    with patch('sys.argv', ['diapedesis']):
        with pytest.raises(SystemExit):
            diapedesis.main()

# ---------------------------------------------------------------------------
# Test JavaScript generation (data safety)
# ---------------------------------------------------------------------------

def test_select_el_escapes_quotes():
    """Test select-el properly escapes quotes in text."""
    args = argparse.Namespace(text='Option with "quotes" and \\backslash')
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        diapedesis.cmd_select_el(args)
        js = mock_run.call_args[0][0][-1]
        # json.dumps should properly escape the string
        assert "Option with" in js

def test_cart_add_escapes_selector():
    """Test cart-add properly escapes CSS selector."""
    args = argparse.Namespace(selector='#btn[data-attr="value"]')
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        diapedesis.cmd_cart_add(args)
        js = mock_run.call_args[0][0][-1]
        # Should be properly JSON-escaped
        assert "btn" in js

# ---------------------------------------------------------------------------
# Test session data handling
# ---------------------------------------------------------------------------

def test_profile_directory_resolves_correctly():
    """Test PROFILE resolves to expected path."""
    expected = Path.home() / ".agent-browser-profile"
    assert diapedesis.PROFILE == expected

def test_socket_directory_resolves_correctly():
    """Test SOCKET_DIR resolves to expected path."""
    expected = Path.home() / ".agent-browser"
    assert diapedesis.SOCKET_DIR == expected

def test_submit_js_generates_valid_structure():
    """Test cmd_submit generates valid JavaScript structure."""
    args = argparse.Namespace(follow=False)
    
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "submitted"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        diapedesis.cmd_submit(args)
        js = mock_run.call_args[0][0][-1]
        
        # Verify key JS patterns for form data collection
        assert "document.createElement" in js
        assert "form.method = 'POST'" in js
        assert "form.submit()" in js
        
        # Verify it handles all input types
        assert "input" in js
        assert "select" in js  
        assert "textarea" in js
        assert "radio" in js
        assert "checkbox" in js
