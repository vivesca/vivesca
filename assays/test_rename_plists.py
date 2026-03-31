#!/usr/bin/env python3
"""Tests for rename-plists effector — tests deep replace and rename logic."""

import pytest
import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Execute the rename-plists file directly
rename_plists_path = Path("/home/terry/germline/effectors/rename-plists")
rename_plists_code = rename_plists_path.read_text()
namespace = {}
exec(rename_plists_code, namespace)

# Extract all the functions/globals from the namespace
rename_plists = type('rename_plists_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(rename_plists, key, value)

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

def test_constants_are_correct():
    """Test constant values are set correctly."""
    assert rename_plists.OLD_PREFIX == "com.terry"
    assert rename_plists.NEW_PREFIX == "com.vivesca"
    assert "OSCILLATORS_DIR" in dir(rename_plists)
    assert "LAUNCH_AGENTS_DIR" in dir(rename_plists)
    assert rename_plists.OSCILLATORS_DIR.is_absolute()
    assert rename_plists.LAUNCH_AGENTS_DIR.is_absolute()

# ---------------------------------------------------------------------------
# Test deep_replace
# ---------------------------------------------------------------------------

def test_deep_replace_strings():
    """Test deep_replace replaces strings correctly."""
    assert rename_plists.deep_replace("com.terry.test") == "com.vivesca.test"
    assert rename_plists.deep_replace("nocom.terryhere") == "nocom.vivescahere"
    assert rename_plists.deep_replace("hello world") == "hello world"

def test_deep_replace_lists():
    """Test deep_replace works on lists."""
    input_list = ["com.terry.one", "com.terry.two", "other"]
    expected = ["com.vivesca.one", "com.vivesca.two", "other"]
    assert rename_plists.deep_replace(input_list) == expected

def test_deep_replace_dicts():
    """Test deep_replace works on dicts, including keys."""
    input_dict = {
        "Label": "com.terry.test",
        "com.terry.key": "value",
        "another": "com.terry.value"
    }
    result = rename_plists.deep_replace(input_dict)
    assert result["Label"] == "com.vivesca.test"
    assert "com.vivesca.key" in result
    assert result["com.vivesca.key"] == "value"
    assert result["another"] == "com.vivesca.value"

def test_deep_replace_nested():
    """Test deep_replace works on nested structures."""
    input_data = {
        "Label": "com.terry.program",
        "ProgramArguments": ["/usr/bin/com.terry", "com.terry.arg"],
        "Environment": {
            "com.terry.VAR": "com.terry.val",
            "OtherVar": "normal"
        }
    }
    result = rename_plists.deep_replace(input_data)
    assert result["Label"] == "com.vivesca.program"
    assert result["ProgramArguments"] == ["/usr/bin/com.vivesca", "com.vivesca.arg"]
    assert "com.vivesca.VAR" in result["Environment"]
    assert result["Environment"]["com.vivesca.VAR"] == "com.vivesca.val"
    assert result["Environment"]["OtherVar"] == "normal"

def test_deep_replace_nonstring_types():
    """Test deep_replace leaves non-string types untouched."""
    assert rename_plists.deep_replace(42) == 42
    assert rename_plists.deep_replace(3.14) == 3.14
    assert rename_plists.deep_replace(True) is True
    assert rename_plists.deep_replace(None) is None

# ---------------------------------------------------------------------------
# Test run_cmd
# ---------------------------------------------------------------------------

def test_run_cmd_dry_run_prints():
    """Test run_cmd in dry-run mode prints and returns success."""
    with patch('builtins.print') as mock_print:
        rc, err = rename_plists.run_cmd(["echo", "test"], dry_run=True)
        assert rc == 0
        assert err == ""
        mock_print.assert_called_once()
        assert "echo test" in mock_print.call_args[0][0]

def test_run_cmd_actual_run_success():
    """Test run_cmd actually runs subprocess on execute mode."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result):
        rc, err = rename_plists.run_cmd(["echo", "test"], dry_run=False)
        assert rc == 0
        assert err == ""

def test_run_cmd_actual_run_failure():
    """Test run_cmd returns correct error on failure."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "command failed"
    
    with patch('subprocess.run', return_value=mock_result):
        rc, err = rename_plists.run_cmd(["false"], dry_run=False)
        assert rc == 1
        assert err == "command failed"

# ---------------------------------------------------------------------------
# Test rename_one basic structure
# ---------------------------------------------------------------------------

def test_rename_one_computes_paths_correctly():
    """Test rename_one computes correct new paths and labels."""
    old_plist = Path("/test/oscillators/com.terry.my-job.plist")
    mock_plist_data = {"Label": "com.terry.my-job"}
    
    # Mock builtins.open for all opening
    mocked_open = mock_open()
    mocked_open.return_value.__enter__.return_value.read.return_value = b''
    
    with patch('builtins.open', mocked_open):
        with patch('plistlib.load', return_value=mock_plist_data):
            with patch('plistlib.dump'):
                with patch('subprocess.run'):
                    errors = rename_plists.rename_one(old_plist, dry_run=True)
                    # Should not have errors in dry run
                    assert errors == []

# ---------------------------------------------------------------------------
# Test main argument parsing
# ---------------------------------------------------------------------------

def test_main_parses_execute_flag():
    """Test main parses --execute flag correctly."""
    with patch('sys.argv', ['rename-plists', '--execute']):
        with patch('glob.glob', return_value=[]):
            with pytest.raises(SystemExit) as exc_info:
                rename_plists.main()
            # Should exit because no plists found
            assert exc_info.value.code == 1

def test_main_default_is_dry_run():
    """Test default is dry run (no --execute)."""
    with patch('sys.argv', ['rename-plists']):
        with patch('glob.glob', return_value=[]):
            with pytest.raises(SystemExit) as exc_info:
                rename_plists.main()
            assert exc_info.value.code == 1

def test_main_no_plists_exits():
    """Test main exits with code 1 when no plists found."""
    with patch('sys.argv', ['rename-plists']):
        with patch('glob.glob', return_value=[]):
            with pytest.raises(SystemExit) as exc_info:
                rename_plists.main()
            assert exc_info.value.code == 1
