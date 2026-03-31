#!/usr/bin/env python3
"""Tests for phagocytosis.py — Obsidian lastOpenFiles logging tests."""

import pytest
import json
import io
from unittest.mock import patch, mock_open
from pathlib import Path

# Execute the phagocytosis file directly
phago_path = Path("/home/terry/germline/effectors/phagocytosis.py")
phago_code = phago_path.read_text()
namespace = {}
exec(phago_code, namespace)

# Extract all the functions/globals from the namespace
phagocytosis = type('phago_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(phagocytosis, key, value)

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

def test_paths_resolved():
    """Test all paths are correctly constructed."""
    assert str(phagocytosis.CHROMATIN).endswith("epigenome/chromatin")
    assert phagocytosis.WORKSPACE == phagocytosis.CHROMATIN / ".obsidian" / "workspace.json"
    assert phagocytosis.LOG_FILE == phagocytosis.CHROMATIN / ".consumption-log.jsonl"

# ---------------------------------------------------------------------------
# Test read_last_open_files
# ---------------------------------------------------------------------------

def test_read_last_open_files_extracts_correctly():
    """Test reads and extracts lastOpenFiles from workspace."""
    workspace_data = {
        "lastOpenFiles": [
            "/note1.md",
            "/note2.md",
            "/note3.md"
        ]
    }
    mock_text = json.dumps(workspace_data)
    
    with patch('pathlib.Path.read_text', return_value=mock_text):
        result = phagocytosis.read_last_open_files()
        assert len(result) == 3
        assert result[0] == "/note1.md"

def test_read_last_open_files_handles_empty():
    """Test when no lastOpenFiles key, returns empty list."""
    workspace_data = {}
    mock_text = json.dumps(workspace_data)
    
    with patch('pathlib.Path.read_text', return_value=mock_text):
        result = phagocytosis.read_last_open_files()
        assert result == []

# ---------------------------------------------------------------------------
# Test read_last_snapshot
# ---------------------------------------------------------------------------

def test_read_last_snapshot_returns_none_when_no_file():
    """Test returns None when log file doesn't exist."""
    with patch('pathlib.Path.exists', return_value=False):
        result = phagocytosis.read_last_snapshot()
        assert result is None

def test_read_last_snapshot_returns_none_when_empty():
    """Test returns None when log file is empty."""
    # Create a BytesIO object that supports seek
    class EmptySeekableBytesIO(io.BytesIO):
        def seek(self, offset, whence=0):
            return super().seek(offset, whence)
    
    mock_io = EmptySeekableBytesIO()
    mock_file = mock_open()
    mock_file.return_value = mock_io
    
    with patch('pathlib.Path.exists', return_value=True):
        with patch('builtins.open', mock_file):
            result = phagocytosis.read_last_snapshot()
            assert result is None

def test_read_last_snapshot_reads_last_line():
    """Test correctly reads the last line from log file."""
    entry1 = json.dumps({"ts": 1234567890, "files": ["a.md", "b.md"]})
    entry2 = json.dumps({"ts": 1234567891, "files": ["b.md", "c.md"]})
    content = f"{entry1}\n{entry2}\n".encode('utf-8')
    
    # Create a proper seekable BytesIO
    import io
    mock_io = io.BytesIO(content)
    
    mock_file = mock_open()
    mock_file.return_value = mock_io
    
    with patch('pathlib.Path.exists', return_value=True):
        with patch('builtins.open', mock_file):
            result = phagocytosis.read_last_snapshot()
            assert result == ["b.md", "c.md"]

# ---------------------------------------------------------------------------
# Test main function
# ---------------------------------------------------------------------------

def test_main_exits_if_workspace_missing():
    """Test main returns early when workspace file doesn't exist."""
    with patch('pathlib.Path.exists', return_value=False):
        # Should not throw
        phagocytosis.main()

def test_main_exits_if_no_current_files():
    """Test main returns early when empty file list."""
    with patch('pathlib.Path.exists', return_value=True):
        with patch.object(phagocytosis, 'read_last_open_files', return_value=[]):
            # Should not throw
            phagocytosis.main()

def test_main_skips_if_same_as_last():
    """Test skips writing when files haven't changed."""
    file_list = ["/a.md", "/b.md"]
    with patch('pathlib.Path.exists', return_value=True):
        with patch.object(phagocytosis, 'read_last_open_files', return_value=file_list):
            with patch.object(phagocytosis, 'read_last_snapshot', return_value=file_list):
                with patch('builtins.open', mock_open()) as mock_file:
                    phagocytosis.main()
                    # Should not write
                    handle = mock_file()
                    handle.write.assert_not_called()

def test_main_writes_entry_when_changed():
    """Test writes new entry when files changed."""
    last_files = ["/a.md", "/b.md"]
    current_files = ["/b.md", "/c.md"]
    
    with patch('pathlib.Path.exists', return_value=True):
        with patch.object(phagocytosis, 'read_last_open_files', return_value=current_files):
            with patch.object(phagocytosis, 'read_last_snapshot', return_value=last_files):
                mock_file_handle = mock_open()
                with patch('builtins.open', mock_file_handle):
                    with patch('time.time', return_value=1234567890.0):
                        phagocytosis.main()
                        # Should write new entry
                        handle = mock_file_handle()
                        handle.write.assert_called_once()
                        written = handle.write.call_args[0][0]
                        # Should be valid JSON
                        data = json.loads(written.strip())
                        assert data['ts'] == 1234567890
                        assert data['files'] == current_files
