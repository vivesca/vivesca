#!/usr/bin/env python3
"""Tests for find effector — tests search blocking logic and binary resolution."""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

# Execute the find file directly
find_path = Path("/home/terry/germline/effectors/find")
find_code = find_path.read_text()
namespace = {}
exec(find_code, namespace)

# Extract all the functions/globals from the namespace
find = type('find_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(find, key, value)

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

def test_binary_paths_defined():
    """Test BINARIES dict has all expected entries."""
    assert "grep" in find.BINARIES
    assert "rg" in find.BINARIES
    assert "find" in find.BINARIES
    assert find.BINARIES["grep"] == "/usr/bin/grep"
    assert find.BINARIES["find"] == "/usr/bin/find"

# ---------------------------------------------------------------------------
# Test search path blocking
# ---------------------------------------------------------------------------

def test_root_search_blocked(capsys):
    """Test search on root directory is blocked."""
    root_path = "/"
    with patch('sys.argv', ['find', root_path]):
        with patch('os.execv') as mock_execv:
            with pytest.raises(SystemExit) as exc_info:
                find.main()
            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "SEARCH BLOCKED" in captured.out
            assert "Performance bottleneck" in captured.out
            mock_execv.assert_not_called()

def test_home_search_blocked(capsys):
    """Test search on home directory is blocked."""
    home_path = str(Path.home())
    with patch('sys.argv', ['find', home_path]):
        with patch('os.execv') as mock_execv:
            with pytest.raises(SystemExit):
                find.main()
            mock_execv.assert_not_called()

def _create_test_massive_dir_path(dirname):
    """Helper to create absolute path matching what the code expects."""
    expanded = os.path.abspath(os.path.expanduser(dirname))
    return expanded

def test_library_search_blocked(capsys):
    """Test search on ~/Library is blocked."""
    library_path = str(Path.home() / "Library")
    full_path = _create_test_massive_dir_path("~/Library")
    with patch('sys.argv', ['find', full_path]):
        with patch('os.execv') as mock_execv:
            with pytest.raises(SystemExit):
                find.main()
            mock_execv.assert_not_called()

def test_pictures_search_blocked(capsys):
    """Test search on ~/Pictures is blocked."""
    pictures_path = _create_test_massive_dir_path("~/Pictures")
    with patch('sys.argv', ['find', pictures_path]):
        with patch('os.execv') as mock_execv:
            with pytest.raises(SystemExit):
                find.main()
            mock_execv.assert_not_called()

def test_downloads_search_blocked(capsys):
    """Test search on ~/Downloads is blocked."""
    downloads_path = _create_test_massive_dir_path("~/Downloads")
    with patch('sys.argv', ['find', downloads_path]):
        with patch('os.execv') as mock_execv:
            with pytest.raises(SystemExit):
                find.main()
            mock_execv.assert_not_called()

def test_allowed_subdirectory_passes():
    """Test search on a subdirectory goes through to real find."""
    test_dir = str(Path.home() / "germline")
    with patch('sys.argv', ['find', test_dir, "-name", "*.py"]):
        with patch('os.path.exists', return_value=True):
            with patch('os.execv') as mock_execv:
                find.main()
                mock_execv.assert_called_once()
                call_args = mock_execv.call_args[0]
                assert call_args[0] == find.BINARIES["find"]
                assert test_dir in call_args[1]

def test_no_path_allowed():
    """Test when no path is specified (reading from stdin), passes through."""
    with patch('sys.argv', ['grep', "pattern"]):
        with patch('os.execv') as mock_execv:
            find.main()
            mock_execv.assert_called_once()
            assert mock_execv.call_args[0][0] == find.BINARIES["grep"]

def test_relative_dot_search_allowed_when_subdirectory():
    """Test ./ (current directory) when it's not root/home is allowed."""
    # We're in /home/terry/germline which is not a blocked directory
    cwd = Path.cwd()
    if str(cwd) in [str(Path.home()), "/"]:
        pytest.skip("Running from blocked directory, can't test")
    with patch('sys.argv', ['find', ".", "-name", "test*"]):
        with patch('os.path.exists', return_value=True):
            with patch('os.execv') as mock_execv:
                find.main()
                mock_execv.assert_called_once()

def test_rig_fallback_which():
    """Test rg falls back to which when not in standard location."""
    with patch('sys.argv', ['rg', "pattern", str(Path.home() / "germline")]):
        with patch('os.path.exists', side_effect=[False, True]):  # real_bin doesn't exist, then after which...
            with patch('subprocess.check_output', return_value=b"/usr/local/bin/rg\n/usr/bin/rg\n"):
                with patch('os.execv') as mock_execv:
                    find.main()
                    mock_execv.assert_called_once()

def test_exec_exception_handled(capsys):
    """Test exceptions during exec are handled gracefully."""
    test_dir = str(Path.home() / "germline")
    with patch('sys.argv', ['find', test_dir]):
        with patch('os.path.exists', return_value=True):
            with patch('os.execv', side_effect=Exception("exec failed")):
                with pytest.raises(SystemExit) as exc_info:
                    find.main()
                assert exc_info.value.code == 1
                captured = capsys.readouterr()
                assert "Error executing" in captured.out
