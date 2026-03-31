"""Tests for pinocytosis effector — web content extraction."""

from __future__ import annotations

import json
import pytest
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Execute the pinocytosis file directly
pinocytosis_path = Path("/home/terry/germline/effectors/pinocytosis")
pinocytosis_code = pinocytosis_path.read_text()

# Create module namespace and exec
namespace = {"__name__": "test_mod"}
exec(pinocytosis_code, namespace)

# Create a proper module-like object
pinocytosis = types.SimpleNamespace()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(pinocytosis, key, value)


# ---------------------------------------------------------------------------
# Test file existence
# ---------------------------------------------------------------------------

def test_pinocytosis_file_exists():
    """Test that pinocytosis effector file exists."""
    assert pinocytosis_path.exists()
    assert pinocytosis_path.is_file()


def test_pinocytosis_is_python_script():
    """Test that pinocytosis has shebang."""
    first_line = pinocytosis_code.split('\n')[0]
    assert first_line.startswith('#!/usr/bin/env python')


def test_pinocytosis_docstring():
    """Test that pinocytosis has docstring."""
    assert '"""' in pinocytosis_code
    assert 'pinocytosis' in pinocytosis_code.lower()


# ---------------------------------------------------------------------------
# Test _run helper
# ---------------------------------------------------------------------------

def test_run_success():
    """Test _run with successful command."""
    ok, output = pinocytosis._run(["echo", "hello"])
    assert ok is True
    assert "hello" in output


def test_run_failure():
    """Test _run with failing command."""
    ok, output = pinocytosis._run(["false"])
    assert ok is False


def test_run_nonexistent_command():
    """Test _run with nonexistent command."""
    ok, output = pinocytosis._run(["nonexistent_command_xyz_123"])
    assert ok is False
    assert output == ""


def test_run_timeout():
    """Test _run with command that times out."""
    # Use a short timeout with a long-running command
    ok, output = pinocytosis._run(["sleep", "10"], timeout=1)
    assert ok is False
    assert output == ""


def test_run_captures_stdout():
    """Test _run captures stdout."""
    ok, output = pinocytosis._run(["printf", "line1\nline2"])
    assert ok is True
    assert "line1" in output
    assert "line2" in output


# ---------------------------------------------------------------------------
# Test _defuddle (patching in namespace)
# ---------------------------------------------------------------------------

def test_defuddle_returns_empty_on_failure():
    """Test _defuddle returns empty string when defuddle fails."""
    original_run = namespace['_run']
    namespace['_run'] = MagicMock(return_value=(False, ""))
    try:
        result = namespace['_defuddle']("https://example.com")
        assert result == ""
    finally:
        namespace['_run'] = original_run


def test_defuddle_returns_empty_on_short_response():
    """Test _defuddle returns empty when response is too short."""
    original_run = namespace['_run']
    namespace['_run'] = MagicMock(return_value=(True, "short"))
    try:
        result = namespace['_defuddle']("https://example.com")
        assert result == ""
    finally:
        namespace['_run'] = original_run


def test_defuddle_returns_text_on_success():
    """Test _defuddle returns text when successful."""
    long_text = "x" * 200  # Long enough to pass min length check
    original_run = namespace['_run']
    namespace['_run'] = MagicMock(return_value=(True, long_text))
    try:
        result = namespace['_defuddle']("https://example.com")
        assert result == long_text
    finally:
        namespace['_run'] = original_run


def test_defuddle_detects_auth_gate_sign_in():
    """Test _defuddle returns empty for auth-gated content (sign in)."""
    long_text = "x" * 200 + " Please sign in to continue"
    original_run = namespace['_run']
    namespace['_run'] = MagicMock(return_value=(True, long_text))
    try:
        result = namespace['_defuddle']("https://example.com")
        assert result == ""
    finally:
        namespace['_run'] = original_run


def test_defuddle_detects_auth_gate_log_in():
    """Test _defuddle returns empty for auth-gated content (log in)."""
    long_text = "x" * 200 + " Please log in to view this page"
    original_run = namespace['_run']
    namespace['_run'] = MagicMock(return_value=(True, long_text))
    try:
        result = namespace['_defuddle']("https://example.com")
        assert result == ""
    finally:
        namespace['_run'] = original_run


def test_defuddle_detects_auth_gate_create_account():
    """Test _defuddle returns empty for auth-gated content (create account)."""
    long_text = "x" * 200 + " Create account to proceed"
    original_run = namespace['_run']
    namespace['_run'] = MagicMock(return_value=(True, long_text))
    try:
        result = namespace['_defuddle']("https://example.com")
        assert result == ""
    finally:
        namespace['_run'] = original_run


def test_defuddle_detects_auth_gate_please_login():
    """Test _defuddle returns empty for auth-gated content (please login)."""
    long_text = "x" * 200 + " please login to access content"
    original_run = namespace['_run']
    namespace['_run'] = MagicMock(return_value=(True, long_text))
    try:
        result = namespace['_defuddle']("https://example.com")
        assert result == ""
    finally:
        namespace['_run'] = original_run


def test_defuddle_passes_non_gated_content():
    """Test _defuddle returns content when not auth-gated."""
    long_text = "This is a great article " + "x" * 200
    original_run = namespace['_run']
    namespace['_run'] = MagicMock(return_value=(True, long_text))
    try:
        result = namespace['_defuddle']("https://example.com")
        assert result == long_text
    finally:
        namespace['_run'] = original_run


# ---------------------------------------------------------------------------
# Test _agent_browser_eval
# ---------------------------------------------------------------------------

def test_agent_browser_eval_returns_empty_on_open_failure():
    """Test _agent_browser_eval returns empty when browser fails to open."""
    original_run = namespace['_run']
    # close succeeds, open fails
    namespace['_run'] = MagicMock(side_effect=[
        (True, ""),  # close
        (False, ""),  # open fails
    ])
    try:
        with patch('time.sleep'):
            result = namespace['_agent_browser_eval']("https://example.com")
        assert result == ""
    finally:
        namespace['_run'] = original_run


def test_agent_browser_eval_returns_empty_on_empty_text():
    """Test _agent_browser_eval returns empty when no text extracted."""
    original_run = namespace['_run']
    # close, open, wait, eval (short), get (empty)
    namespace['_run'] = MagicMock(side_effect=[
        (True, ""),  # close
        (True, ""),  # open
        (True, ""),  # wait
        (True, "short"),  # eval - short response
        (True, ""),  # get - empty
    ])
    try:
        with patch('time.sleep'):
            result = namespace['_agent_browser_eval']("https://example.com")
        assert result == ""
    finally:
        namespace['_run'] = original_run


def test_agent_browser_eval_returns_text_from_eval():
    """Test _agent_browser_eval returns text from eval."""
    long_text = "x" * 100
    original_run = namespace['_run']
    namespace['_run'] = MagicMock(side_effect=[
        (True, ""),  # close
        (True, ""),  # open
        (True, ""),  # wait
        (True, long_text),  # eval succeeds
    ])
    try:
        with patch('time.sleep'):
            result = namespace['_agent_browser_eval']("https://example.com")
        assert result == long_text
    finally:
        namespace['_run'] = original_run


def test_agent_browser_eval_returns_text_from_get():
    """Test _agent_browser_eval returns text from get when eval fails."""
    long_text = "x" * 100
    original_run = namespace['_run']
    namespace['_run'] = MagicMock(side_effect=[
        (True, ""),  # close
        (True, ""),  # open
        (True, ""),  # wait
        (False, ""),  # eval fails
        (True, long_text),  # get succeeds
    ])
    try:
        with patch('time.sleep'):
            result = namespace['_agent_browser_eval']("https://example.com")
        assert result == long_text
    finally:
        namespace['_run'] = original_run


# ---------------------------------------------------------------------------
# Test _screenshot
# ---------------------------------------------------------------------------

def test_screenshot_returns_false_on_open_failure():
    """Test _screenshot returns False when browser fails to open."""
    original_run = namespace['_run']
    namespace['_run'] = MagicMock(side_effect=[
        (True, ""),  # close
        (False, ""),  # open fails
    ])
    try:
        with patch('time.sleep'):
            result = namespace['_screenshot']("https://example.com", "/tmp/test.png")
        assert result is False
    finally:
        namespace['_run'] = original_run


def test_screenshot_returns_true_on_success():
    """Test _screenshot returns True on successful screenshot."""
    original_run = namespace['_run']
    namespace['_run'] = MagicMock(side_effect=[
        (True, ""),  # close
        (True, ""),  # open
        (True, ""),  # wait
        (True, ""),  # caffeinate
        (True, ""),  # screenshot
    ])
    try:
        with patch('time.sleep'):
            result = namespace['_screenshot']("https://example.com", "/tmp/test.png")
        assert result is True
    finally:
        namespace['_run'] = original_run


# ---------------------------------------------------------------------------
# Test fetch_url
# ---------------------------------------------------------------------------

def test_fetch_url_returns_defuddle_on_success():
    """Test fetch_url returns defuddle result when successful."""
    long_text = "x" * 200
    original_defuddle = namespace['_defuddle']
    namespace['_defuddle'] = MagicMock(return_value=long_text)
    try:
        result = namespace['fetch_url']("https://example.com")
        assert result["success"] is True
        assert result["text"] == long_text
        assert result["method"] == "defuddle"
        assert result["url"] == "https://example.com"
    finally:
        namespace['_defuddle'] = original_defuddle


def test_fetch_url_falls_back_to_agent_browser():
    """Test fetch_url falls back to agent-browser when defuddle fails."""
    long_text = "x" * 100
    original_defuddle = namespace['_defuddle']
    original_agent_browser = namespace['_agent_browser_eval']
    namespace['_defuddle'] = MagicMock(return_value="")
    namespace['_agent_browser_eval'] = MagicMock(return_value=long_text)
    try:
        result = namespace['fetch_url']("https://example.com")
        assert result["success"] is True
        assert result["text"] == long_text
        assert result["method"] == "agent-browser"
    finally:
        namespace['_defuddle'] = original_defuddle
        namespace['_agent_browser_eval'] = original_agent_browser


def test_fetch_url_returns_failure_when_all_fail():
    """Test fetch_url returns failure when all methods fail."""
    original_defuddle = namespace['_defuddle']
    original_agent_browser = namespace['_agent_browser_eval']
    namespace['_defuddle'] = MagicMock(return_value="")
    namespace['_agent_browser_eval'] = MagicMock(return_value="")
    try:
        result = namespace['fetch_url']("https://example.com")
        assert result["success"] is False
        assert result["text"] == ""
        assert result["method"] == "none"
        assert "error" in result
    finally:
        namespace['_defuddle'] = original_defuddle
        namespace['_agent_browser_eval'] = original_agent_browser


# ---------------------------------------------------------------------------
# Test CLI via subprocess
# ---------------------------------------------------------------------------

def test_pinocytosis_help():
    """Test that pinocytosis --help runs without error."""
    result = subprocess.run(
        [sys.executable, str(pinocytosis_path), "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Web content extraction" in result.stdout


def test_pinocytosis_shows_url_argument():
    """Test that help shows URL positional argument."""
    result = subprocess.run(
        [sys.executable, str(pinocytosis_path), "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "url" in result.stdout.lower()


def test_pinocytosis_shows_options():
    """Test that help shows available options."""
    result = subprocess.run(
        [sys.executable, str(pinocytosis_path), "--help"],
        capture_output=True,
        text=True
    )
    assert "--screenshot" in result.stdout
    assert "--json" in result.stdout


# ---------------------------------------------------------------------------
# Test function signatures and structure
# ---------------------------------------------------------------------------

def test_fetch_url_signature():
    """Test fetch_url returns dict with expected keys."""
    # We can test the return structure even with a failing fetch
    result = namespace['fetch_url']("https://nonexistent.invalid")
    assert "success" in result
    assert "text" in result
    assert "method" in result
    assert "url" in result


def test_run_accepts_timeout():
    """Test _run accepts timeout parameter."""
    # Quick test with valid command
    ok, output = namespace['_run'](["echo", "test"], timeout=5)
    assert ok is True


# ---------------------------------------------------------------------------
# Test auth signal detection
# ---------------------------------------------------------------------------

def test_auth_signals_list():
    """Test that auth signals are defined correctly in the code."""
    # Check the code contains the expected auth signals
    assert "sign in" in pinocytosis_code.lower()
    assert "log in" in pinocytosis_code.lower()
    assert "create account" in pinocytosis_code.lower()


# ---------------------------------------------------------------------------
# Test error handling in fetch_url
# ---------------------------------------------------------------------------

def test_fetch_url_includes_error_message():
    """Test fetch_url includes error message on failure."""
    original_defuddle = namespace['_defuddle']
    original_agent_browser = namespace['_agent_browser_eval']
    namespace['_defuddle'] = MagicMock(return_value="")
    namespace['_agent_browser_eval'] = MagicMock(return_value="")
    try:
        result = namespace['fetch_url']("https://example.com")
        assert result["success"] is False
        assert "error" in result
        assert result["error"]  # Error message is non-empty
    finally:
        namespace['_defuddle'] = original_defuddle
        namespace['_agent_browser_eval'] = original_agent_browser


# ---------------------------------------------------------------------------
# Additional edge case tests
# ---------------------------------------------------------------------------


def test_run_with_env_command():
    """Test _run with a command that uses environment variables."""
    import os
    ok, output = pinocytosis._run(["sh", "-c", "echo $HOME"])
    assert ok is True
    assert output  # Should have some output


def test_defuddle_exact_threshold():
    """Test _defuddle at exactly 100 characters."""
    # Exactly 100 characters should fail (needs > 100)
    text_99 = "x" * 99
    text_100 = "x" * 100
    text_101 = "x" * 101

    original_run = namespace['_run']

    # 99 chars should fail
    namespace['_run'] = MagicMock(return_value=(True, text_99))
    try:
        result = namespace['_defuddle']("https://example.com")
        assert result == ""
    finally:
        pass

    # 100 chars should fail (not > 100)
    namespace['_run'] = MagicMock(return_value=(True, text_100))
    try:
        result = namespace['_defuddle']("https://example.com")
        assert result == ""
    finally:
        pass

    # 101 chars should succeed
    namespace['_run'] = MagicMock(return_value=(True, text_101))
    try:
        result = namespace['_defuddle']("https://example.com")
        assert result == text_101
    finally:
        namespace['_run'] = original_run


def test_agent_browser_eval_short_text():
    """Test _agent_browser_eval with text under 50 chars from eval."""
    original_run = namespace['_run']
    short_text = "x" * 49  # Under 50 chars

    # eval returns short text (too short), get returns empty
    namespace['_run'] = MagicMock(side_effect=[
        (True, ""),  # close
        (True, ""),  # open
        (True, ""),  # wait
        (True, short_text),  # eval - too short, doesn't return
        (True, ""),  # get - empty, doesn't return
    ])
    try:
        with patch('time.sleep'):
            result = namespace['_agent_browser_eval']("https://example.com")
        assert result == ""
    finally:
        namespace['_run'] = original_run


def test_agent_browser_eval_exactly_50_chars():
    """Test _agent_browser_eval with exactly 50 characters."""
    original_run = namespace['_run']
    text_50 = "x" * 50  # Exactly 50 chars (should fail, needs > 50)
    text_51 = "x" * 51  # 51 chars should succeed

    # 50 chars should fail
    namespace['_run'] = MagicMock(side_effect=[
        (True, ""),  # close
        (True, ""),  # open
        (True, ""),  # wait
        (True, text_50),  # eval - exactly 50, too short
        (True, ""),  # get - empty
    ])
    try:
        with patch('time.sleep'):
            result = namespace['_agent_browser_eval']("https://example.com")
        assert result == ""
    finally:
        pass

    # 51 chars should succeed
    namespace['_run'] = MagicMock(side_effect=[
        (True, ""),  # close
        (True, ""),  # open
        (True, ""),  # wait
        (True, text_51),  # eval - 51 chars, success
    ])
    try:
        with patch('time.sleep'):
            result = namespace['_agent_browser_eval']("https://example.com")
        assert result == text_51
    finally:
        namespace['_run'] = original_run


def test_fetch_url_url_preserved():
    """Test fetch_url preserves the URL in the result."""
    original_defuddle = namespace['_defuddle']
    namespace['_defuddle'] = MagicMock(return_value="x" * 200)
    try:
        result = namespace['fetch_url']("https://example.com/test")
        assert result["url"] == "https://example.com/test"
    finally:
        namespace['_defuddle'] = original_defuddle


# ---------------------------------------------------------------------------
# Test main function argument parsing
# ---------------------------------------------------------------------------


def test_main_json_output():
    """Test main function with --json flag."""
    original_argv = sys.argv
    original_defuddle = namespace['_defuddle']
    namespace['_defuddle'] = MagicMock(return_value="x" * 200)

    try:
        sys.argv = ["pinocytosis", "--json", "https://example.com"]
        # Capture stdout
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            namespace['main']()
        output = f.getvalue()
        # Should be valid JSON
        import json
        data = json.loads(output)
        assert data["success"] is True
        assert data["method"] == "defuddle"
    finally:
        sys.argv = original_argv
        namespace['_defuddle'] = original_defuddle


def test_main_failure_exits_nonzero():
    """Test main function exits with code 1 on failure."""
    original_argv = sys.argv
    original_defuddle = namespace['_defuddle']
    original_agent_browser = namespace['_agent_browser_eval']
    namespace['_defuddle'] = MagicMock(return_value="")
    namespace['_agent_browser_eval'] = MagicMock(return_value="")

    try:
        sys.argv = ["pinocytosis", "https://example.com"]
        with pytest.raises(SystemExit) as exc_info:
            namespace['main']()
        assert exc_info.value.code == 1
    finally:
        sys.argv = original_argv
        namespace['_defuddle'] = original_defuddle
        namespace['_agent_browser_eval'] = original_agent_browser
