#!/usr/bin/env python3
"""Tests for dr-sync effector — disaster recovery sync backup tests."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Execute the dr-sync file directly
dr_sync_path = Path("/home/terry/germline/effectors/dr-sync")
dr_sync_code = dr_sync_path.read_text()
namespace = {}
exec(dr_sync_code, namespace)

# Extract all the functions/globals from the namespace
dr_sync = type('dr_sync_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(dr_sync, key, value)

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

def test_dest_path_correct():
    """Test DEST is correct path under officina."""
    expected = Path.home() / "officina" / "claude-backup"
    assert dr_sync.DEST == expected

# ---------------------------------------------------------------------------
# Test sync function with mocks
# ---------------------------------------------------------------------------

def test_no_files_to_backup():
    """Test when no source files exist, nothing is copied."""
    with patch('pathlib.Path.exists', return_value=False):
        with patch('subprocess.run') as mock_run:
            dr_sync.sync()
            # Still runs brew bundle dump
            assert mock_run.call_count >= 1

def test_claude_settings_copied():
    """Test Claude settings.json is copied when it exists."""
    calls = []
    def mock_copy2(src, dst):
        calls.append((src, dst))
    
    # Patch exists to return True only for settings.json
    exists_orig = Path.exists
    def mock_exists(self):
        if str(self).endswith("settings.json") or str(self).endswith("settings.local.json"):
            return True
        return False
    
    with patch('shutil.copy2', side_effect=mock_copy2):
        with patch('shutil.copytree'):
            with patch('pathlib.Path.exists', mock_exists):
                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(stdout='')
                    dr_sync.sync()
                    # Should copy settings.json
                    assert any('settings.json' in str(call[0]) for call in calls)

def test_claude_memory_copied():
    """Test Claude project memory is copied when exists."""
    mock_copytree = MagicMock()
    exists_calls = []
    def mock_exists(self):
        exists_calls.append(str(self))
        if 'memory' in str(self) and 'src' not in str(self):  # mem_dst exists: we return True to trigger rm
            return True
        if 'mem_src' in str(self) or str(self).endswith("projects/-Users-terry/memory"):
            return True
        return False
    
    with patch('shutil.copy2'):
        with patch('shutil.copytree', mock_copytree):
            with patch('shutil.rmtree'):
                with patch('pathlib.Path.exists', mock_exists):
                    with patch('subprocess.run'):
                        dr_sync.sync()
                        mock_copytree.assert_called_once()

def test_zshenv_copied():
    """Test .zshenv.local is copied when exists."""
    calls = []
    def mock_copy2(src, dst):
        calls.append((src, dst))
    
    def mock_exists(self):
        return str(self).endswith('.zshenv.local')
    
    with patch('shutil.copy2', side_effect=mock_copy2):
        with patch('shutil.copytree'):
            with patch('pathlib.Path.exists', mock_exists):
                with patch('subprocess.run'):
                    dr_sync.sync()
                    assert any('zshenv.local' in str(call[1]) for call in calls)

def test_synaxis_config_copied():
    """Test Synaxis config is copied to correct destination."""
    calls = []
    def mock_copy2(src, dst):
        calls.append((src, dst))
    
    def mock_exists(self):
        return str(self).endswith('config.toml') and 'synaxis' in str(self)
    
    with patch('shutil.copy2', side_effect=mock_copy2):
        with patch('shutil.copytree'):
            with patch('pathlib.Path.exists', mock_exists):
                with patch('pathlib.Path.mkdir'):
                    with patch('subprocess.run'):
                        dr_sync.sync()
                        assert any('config.toml' in str(call[0]) for call in calls)

def test_brewfile_dump_called():
    """Test brew bundle dump is called to refresh Brewfile."""
    with patch('shutil.copy2'):
        with patch('shutil.copytree'):
            with patch('pathlib.Path.exists', return_value=False):
                with patch('subprocess.run') as mock_run:
                    dr_sync.sync()
                    # Check brew bundle dump was called
                    brew_called = any("brew" in call[0][0] and "bundle" in call[0][0] and "dump" in call[0][0] 
                                     for call in mock_run.call_args_list)
                    assert brew_called

def test_no_changes_no_commit(capsys):
    """Test when no changes detected, doesn't commit/push."""
    with patch('shutil.copy2'):
        with patch('shutil.copytree'):
            with patch('pathlib.Path.exists', return_value=False):
                mock_result = MagicMock()
                mock_result.stdout = ""  # No changes
                with patch('subprocess.run', return_value=mock_result):
                    dr_sync.sync()
                    captured = capsys.readouterr()
                    assert "no changes" in captured.out

def test_changes_committed_and_pushed(capsys):
    """Test when changes detected, commits and pushes."""
    with patch('shutil.copy2'):
        with patch('shutil.copytree'):
            with patch('pathlib.Path.exists', return_value=False):
                # First call: git status outputs something (changes exist)
                mock_status_result = MagicMock()
                mock_status_result.stdout = " M claude-backup/settings.json\n"
                
                # Subsequent calls are ok
                def mock_run_side_effect(*args, **kwargs):
                    if 'git' in args[0] and 'status' in args[0]:
                        return mock_status_result
                    return MagicMock(stdout='', returncode=0)
                
                with patch('subprocess.run', side_effect=mock_run_side_effect):
                    dr_sync.sync()
                    captured = capsys.readouterr()
                    assert "committed and pushed" in captured.out
