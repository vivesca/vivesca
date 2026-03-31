#!/usr/bin/env python3
"""Tests for telophase effector — mocks all external file I/O and subprocess."""

import pytest
import subprocess
import json
import time
import os
import tempfile
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from datetime import datetime
import argparse

# Execute the telophase file directly
telophase_path = Path("/home/terry/germline/effectors/telophase")
telophase_code = telophase_path.read_text()
namespace = {}
exec(telophase_code, namespace)

# Get references to the subprocess module used by telophase
telophase_subprocess = namespace['subprocess']


# Helper to get functions from namespace
def get_func(name):
    return namespace[name]


# ---------------------------------------------------------------------------
# Test git_status helper
# ---------------------------------------------------------------------------

def test_git_status_clean_repo():
    """Test git_status returns empty string for clean repo."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    
    with patch.object(telophase_subprocess, 'run', return_value=mock_result):
        result = get_func('git_status')(Path("/some/repo"))
        assert result == ""


def test_git_status_dirty_repo():
    """Test git_status returns status output for dirty repo."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = " M file1.txt\n?? file2.txt\n"
    
    with patch.object(telophase_subprocess, 'run', return_value=mock_result):
        result = get_func('git_status')(Path("/some/repo"))
        assert "M file1.txt" in result
        assert "?? file2.txt" in result


def test_git_status_not_a_repo():
    """Test git_status returns None when not a git repo."""
    mock_result = MagicMock()
    mock_result.returncode = 128  # Git error code for not a repo
    
    with patch.object(telophase_subprocess, 'run', return_value=mock_result):
        result = get_func('git_status')(Path("/not/a/repo"))
        assert result is None


def test_git_status_timeout():
    """Test git_status returns None on timeout."""
    with patch.object(telophase_subprocess, 'run', side_effect=subprocess.TimeoutExpired("git", 10)):
        result = get_func('git_status')(Path("/some/repo"))
        assert result is None


def test_git_status_git_not_found():
    """Test git_status returns None when git is not installed."""
    with patch.object(telophase_subprocess, 'run', side_effect=FileNotFoundError):
        result = get_func('git_status')(Path("/some/repo"))
        assert result is None


# ---------------------------------------------------------------------------
# Test now_age helper
# ---------------------------------------------------------------------------

def test_now_age_fresh():
    """Test now_age returns 'fresh' for recently modified file."""
    with patch('os.path.getmtime', return_value=time.time() - 300):  # 5 min ago
        label, secs = get_func('now_age')()
        assert label == "fresh"
        assert secs < 900


def test_now_age_recent():
    """Test now_age returns 'recent' for file modified 30 min ago."""
    with patch('os.path.getmtime', return_value=time.time() - 1800):  # 30 min ago
        label, secs = get_func('now_age')()
        assert label == "recent"
        assert 900 <= secs < 3600


def test_now_age_stale():
    """Test now_age returns 'stale' for file modified a few hours ago."""
    with patch('os.path.getmtime', return_value=time.time() - 7200):  # 2 hours ago
        label, secs = get_func('now_age')()
        assert label == "stale"
        assert 3600 <= secs < 86400


def test_now_age_very_stale():
    """Test now_age returns 'very stale' for file modified days ago."""
    with patch('os.path.getmtime', return_value=time.time() - 172800):  # 2 days ago
        label, secs = get_func('now_age')()
        assert label == "very stale"
        assert secs >= 86400


def test_now_age_missing_file():
    """Test now_age returns 'missing' when file doesn't exist."""
    with patch('os.path.getmtime', side_effect=FileNotFoundError):
        label, secs = get_func('now_age')()
        assert label == "missing"
        assert secs == -1


# ---------------------------------------------------------------------------
# Test memory_lines helper
# ---------------------------------------------------------------------------

def test_memory_lines_counts_correctly():
    """Test memory_lines counts lines in MEMORY.md."""
    mock_file = MagicMock()
    mock_file.__iter__ = lambda self: iter(["line1\n", "line2\n", "line3\n"])
    mock_file.__enter__ = lambda self: self
    mock_file.__exit__ = lambda self, *args: None
    
    with patch('builtins.open', return_value=mock_file):
        count = get_func('memory_lines')()
        assert count == 3


def test_memory_lines_empty_file():
    """Test memory_lines returns 0 for empty file."""
    mock_file = MagicMock()
    mock_file.__iter__ = lambda self: iter([])
    mock_file.__enter__ = lambda self: self
    mock_file.__exit__ = lambda self, *args: None
    
    with patch('builtins.open', return_value=mock_file):
        count = get_func('memory_lines')()
        assert count == 0


def test_memory_lines_missing_file():
    """Test memory_lines returns 0 when file doesn't exist."""
    with patch('builtins.open', side_effect=FileNotFoundError):
        count = get_func('memory_lines')()
        assert count == 0


# ---------------------------------------------------------------------------
# Test skill_gaps helper
# ---------------------------------------------------------------------------

def test_skill_gaps_no_gaps():
    """Test skill_gaps returns empty list when all skills are linked."""
    with patch('os.listdir') as mock_listdir:
        # Both directories have the same files
        mock_listdir.side_effect = [
            ["skill1", "skill2", ".hidden"],  # SKILLS directory
            ["skill1", "skill2", "other"],    # CLAUDE_SKILLS directory
        ]
        gaps = get_func('skill_gaps')()
        assert gaps == []


def test_skill_gaps_finds_gaps():
    """Test skill_gaps finds skills without symlinks."""
    with patch('os.listdir') as mock_listdir:
        mock_listdir.side_effect = [
            ["skill1", "skill2", "skill3", ".hidden"],  # SKILLS directory
            ["skill1", "other"],  # CLAUDE_SKILLS - missing skill2 and skill3
        ]
        gaps = get_func('skill_gaps')()
        assert sorted(gaps) == ["skill2", "skill3"]


def test_skill_gaps_missing_skills_dir():
    """Test skill_gaps returns empty list when SKILLS directory doesn't exist."""
    with patch('os.listdir', side_effect=FileNotFoundError):
        gaps = get_func('skill_gaps')()
        assert gaps == []


# ---------------------------------------------------------------------------
# Test dep_check helper
# ---------------------------------------------------------------------------

def test_dep_check_no_warnings():
    """Test dep_check returns empty list when no dependency issues."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    
    with patch.object(telophase_subprocess, 'run', return_value=mock_result):
        warnings = get_func('dep_check')()
        assert warnings == []


def test_dep_check_has_warnings():
    """Test dep_check returns warning lines."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "warning: pkg1 outdated\nwarning: pkg2 missing\n"
    
    with patch.object(telophase_subprocess, 'run', return_value=mock_result):
        warnings = get_func('dep_check')()
        assert len(warnings) == 2
        assert "pkg1 outdated" in warnings[0]


def test_dep_check_timeout():
    """Test dep_check returns empty list on timeout."""
    with patch.object(telophase_subprocess, 'run', side_effect=subprocess.TimeoutExpired("proteostasis", 30)):
        warnings = get_func('dep_check')()
        assert warnings == []


def test_dep_check_not_found():
    """Test dep_check returns empty list when command not found."""
    with patch.object(telophase_subprocess, 'run', side_effect=FileNotFoundError):
        warnings = get_func('dep_check')()
        assert warnings == []


# ---------------------------------------------------------------------------
# Test peira_status helper
# ---------------------------------------------------------------------------

def test_peira_status_active():
    """Test peira_status returns status output when experiment is active."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "experiment-123 running\n"
    
    with patch.object(telophase_subprocess, 'run', return_value=mock_result):
        status = get_func('peira_status')()
        assert "experiment-123" in status


def test_peira_status_no_experiment():
    """Test peira_status returns None when no experiment active."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    
    with patch.object(telophase_subprocess, 'run', return_value=mock_result):
        status = get_func('peira_status')()
        assert status is None


def test_peira_status_error():
    """Test peira_status returns None on error."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "error"
    
    with patch.object(telophase_subprocess, 'run', return_value=mock_result):
        status = get_func('peira_status')()
        assert status is None


def test_peira_status_timeout():
    """Test peira_status returns None on timeout."""
    with patch.object(telophase_subprocess, 'run', side_effect=subprocess.TimeoutExpired("peira", 10)):
        status = get_func('peira_status')()
        assert status is None


def test_peira_status_not_found():
    """Test peira_status returns None when command not found."""
    with patch.object(telophase_subprocess, 'run', side_effect=FileNotFoundError):
        status = get_func('peira_status')()
        assert status is None


# ---------------------------------------------------------------------------
# Test latest_session_id helper
# ---------------------------------------------------------------------------

def test_latest_session_id_found():
    """Test latest_session_id extracts session ID from anam output."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    # Lines are processed in reverse, so first match found is the LAST in the list
    # Note: regex only matches hex chars [a-f0-9], so use valid hex IDs
    mock_result.stdout = """Some header info
[a1b2c3d4] 5 prompts (2m) - Claude
[deadbeef] 3 prompts (1m) - Claude
"""

    with patch.object(telophase_subprocess, 'run', return_value=mock_result):
        sid = get_func('latest_session_id')()
        # When reversed, first match is from the last line with session ID
        # deadbeef is valid hex (only a-f, 0-9)
        assert sid == "deadbeef"


def test_latest_session_id_no_sessions():
    """Test latest_session_id returns None when no sessions found."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "No sessions today\n"
    
    with patch.object(telophase_subprocess, 'run', return_value=mock_result):
        sid = get_func('latest_session_id')()
        assert sid is None


def test_latest_session_id_error():
    """Test latest_session_id returns None on anam error."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "error"
    
    with patch.object(telophase_subprocess, 'run', return_value=mock_result):
        sid = get_func('latest_session_id')()
        assert sid is None


def test_latest_session_id_timeout():
    """Test latest_session_id returns None on timeout."""
    with patch.object(telophase_subprocess, 'run', side_effect=subprocess.TimeoutExpired("anam", 10)):
        sid = get_func('latest_session_id')()
        assert sid is None


def test_latest_session_id_not_found():
    """Test latest_session_id returns None when anam not found."""
    with patch.object(telophase_subprocess, 'run', side_effect=FileNotFoundError):
        sid = get_func('latest_session_id')()
        assert sid is None


# ---------------------------------------------------------------------------
# Test run_reflect helper
# ---------------------------------------------------------------------------

def test_run_reflect_success():
    """Test run_reflect parses and extracts findings."""
    anam_result = MagicMock()
    anam_result.returncode = 0
    anam_result.stdout = json.dumps([
        {"role": "user", "snippet": "Test snippet", "time": "10:00"},
        {"role": "assistant", "snippet": "Response here", "time": "10:01"}
    ])
    
    channel_result = MagicMock()
    channel_result.returncode = 0
    channel_result.stdout = """---
CATEGORY: discovery
QUOTE: Test quote
LESSON: Test lesson
MEMORY_TYPE: finding
---
---
CATEGORY: taste_calibration
QUOTE: Another quote
LESSON: Another lesson
MEMORY_TYPE: feedback
---
"""
    
    with patch.object(telophase_subprocess, 'run', side_effect=[anam_result, channel_result]):
        findings, usage = get_func('run_reflect')("test_session")
        assert len(findings) == 2
        assert findings[0]["category"] == "discovery"
        assert findings[1]["category"] == "taste_calibration"


def test_run_reflect_empty_messages():
    """Test run_reflect handles empty message list."""
    anam_result = MagicMock()
    anam_result.returncode = 0
    anam_result.stdout = "[]"
    
    with patch.object(telophase_subprocess, 'run', return_value=anam_result):
        findings, usage = get_func('run_reflect')("test_session")
        assert findings == []


def test_run_reflect_anam_error():
    """Test run_reflect handles anam search error."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "error"
    
    with patch.object(telophase_subprocess, 'run', return_value=mock_result):
        findings, usage = get_func('run_reflect')("test_session")
        assert findings == []


def test_run_reflect_channel_error():
    """Test run_reflect handles channel error."""
    anam_result = MagicMock()
    anam_result.returncode = 0
    anam_result.stdout = json.dumps([
        {"role": "user", "snippet": "Test", "time": "10:00"}
    ])
    
    channel_result = MagicMock()
    channel_result.returncode = 1
    channel_result.stderr = "error"
    
    with patch.object(telophase_subprocess, 'run', side_effect=[anam_result, channel_result]):
        findings, usage = get_func('run_reflect')("test_session")
        assert findings == []


def test_run_reflect_timeout():
    """Test run_reflect handles timeout."""
    with patch.object(telophase_subprocess, 'run', side_effect=subprocess.TimeoutExpired("anam", 30)):
        findings, usage = get_func('run_reflect')("test_session")
        assert findings == []


# ---------------------------------------------------------------------------
# Test cmd_gather
# ---------------------------------------------------------------------------

def test_cmd_gather_syntactic_output():
    """Test cmd_gather --syntactic produces valid JSON output."""
    args = argparse.Namespace(
        syntactic=True,
        perceptual=False,
        repos=None
    )
    
    # Mock all the helpers in namespace
    with patch.object(telophase_subprocess, 'run', return_value=MagicMock(returncode=0, stdout="")):
        with patch('os.path.getmtime', return_value=time.time()):
            with patch('os.listdir', return_value=[]):
                with patch('builtins.open', side_effect=FileNotFoundError):
                    with patch('builtins.print') as mock_print:
                        get_func('cmd_gather')(args)
                        # Verify print was called
                        assert mock_print.called


def test_cmd_gather_compact_output():
    """Test cmd_gather produces compact text output by default."""
    args = argparse.Namespace(
        syntactic=False,
        perceptual=False,
        repos=None
    )
    
    with patch.object(telophase_subprocess, 'run', return_value=MagicMock(returncode=0, stdout="")):
        with patch('os.path.getmtime', return_value=time.time()):
            with patch('os.listdir', return_value=[]):
                with patch('builtins.open', side_effect=FileNotFoundError):
                    with patch('builtins.print') as mock_print:
                        get_func('cmd_gather')(args)
                        
                        printed = [str(c.args[0]) if c.args else "" for c in mock_print.call_args_list]
                        assert any("memory:" in p for p in printed)
                        assert any("now:" in p for p in printed)


def test_cmd_gather_with_extra_repos():
    """Test cmd_gather handles extra repos argument."""
    args = argparse.Namespace(
        syntactic=False,
        perceptual=False,
        repos="/path/repo1,/path/repo2"
    )
    
    with patch.object(telophase_subprocess, 'run', return_value=MagicMock(returncode=0, stdout="")):
        with patch('os.path.getmtime', return_value=time.time()):
            with patch('os.listdir', return_value=[]):
                with patch('builtins.open', side_effect=FileNotFoundError):
                    with patch('builtins.print'):
                        # Should not raise
                        get_func('cmd_gather')(args)


def test_cmd_gather_perceptual_output():
    """Test cmd_gather --perceptual produces human-readable output."""
    args = argparse.Namespace(
        syntactic=False,
        perceptual=True,
        repos=None
    )
    
    with patch.object(telophase_subprocess, 'run', return_value=MagicMock(returncode=0, stdout="")):
        with patch('os.path.getmtime', return_value=time.time()):
            with patch('os.listdir', return_value=[]):
                with patch('builtins.open', side_effect=FileNotFoundError):
                    with patch('builtins.print') as mock_print:
                        get_func('cmd_gather')(args)
                        
                        printed = [str(c.args[0]) if c.args else "" for c in mock_print.call_args_list]
                        assert any("Legatum Gather" in p or "───" in p for p in printed)


def test_cmd_gather_dirty_repo():
    """Test cmd_gather reports dirty repo status."""
    args = argparse.Namespace(
        syntactic=False,
        perceptual=False,
        repos=None
    )
    
    # Mock git status to return dirty for first repo
    call_count = [0]
    def mock_run(*args, **kwargs):
        call_count[0] += 1
        result = MagicMock()
        result.returncode = 0
        if call_count[0] == 1:
            result.stdout = " M file.txt"  # First git call - dirty
        else:
            result.stdout = ""  # Other calls - clean or empty
        return result
    
    with patch.object(telophase_subprocess, 'run', side_effect=mock_run):
        with patch('os.path.getmtime', return_value=time.time()):
            with patch('os.listdir', return_value=[]):
                with patch('builtins.open', side_effect=FileNotFoundError):
                    with patch('builtins.print') as mock_print:
                        get_func('cmd_gather')(args)
                        
                        printed = [str(c.args[0]) if c.args else "" for c in mock_print.call_args_list]
                        assert any("dirty" in p for p in printed)


# ---------------------------------------------------------------------------
# Test cmd_archive
# ---------------------------------------------------------------------------

def test_cmd_archive_no_completed_items():
    """Test cmd_archive handles file with no completed items."""
    args = argparse.Namespace()
    
    # Create temp files and patch the namespace paths
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Praxis

- [ ] Task 1
- [ ] Task 2
""")
        praxis_path = Path(f.name)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Praxis Archive\n")
        archive_path = Path(f.name)
    
    try:
        # Save original values
        orig_praxis = namespace['PRAXIS']
        orig_archive = namespace['PRAXIS_ARCHIVE']
        
        # Set temp paths in namespace
        namespace['PRAXIS'] = praxis_path
        namespace['PRAXIS_ARCHIVE'] = archive_path
        
        with patch('builtins.print') as mock_print:
            get_func('cmd_archive')(args)
            
            printed = [str(c.args[0]) if c.args else "" for c in mock_print.call_args_list]
            assert any("No completed items" in p for p in printed)
        
        # Restore original values
        namespace['PRAXIS'] = orig_praxis
        namespace['PRAXIS_ARCHIVE'] = orig_archive
    finally:
        praxis_path.unlink(missing_ok=True)
        archive_path.unlink(missing_ok=True)


def test_cmd_archive_moves_completed_items():
    """Test cmd_archive moves completed items to archive."""
    args = argparse.Namespace()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Praxis

- [x] Done task 1
- [ ] Task 2
- [x] Done task 2
""")
        praxis_path = Path(f.name)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Praxis Archive

## January 2026

- [x] Old task `done:2026-01-15`
""")
        archive_path = Path(f.name)
    
    try:
        orig_praxis = namespace['PRAXIS']
        orig_archive = namespace['PRAXIS_ARCHIVE']
        
        namespace['PRAXIS'] = praxis_path
        namespace['PRAXIS_ARCHIVE'] = archive_path
        
        with patch('builtins.print'):
            get_func('cmd_archive')(args)
        
        # Check remaining content has no [x] items
        remaining = praxis_path.read_text()
        assert "[x]" not in remaining
        assert "[ ] Task 2" in remaining
        
        # Check archive has the completed items
        archive_content = archive_path.read_text()
        assert "Done task 1" in archive_content
        assert "Done task 2" in archive_content
        
        namespace['PRAXIS'] = orig_praxis
        namespace['PRAXIS_ARCHIVE'] = orig_archive
    finally:
        praxis_path.unlink(missing_ok=True)
        archive_path.unlink(missing_ok=True)


def test_cmd_archive_adds_done_tag():
    """Test cmd_archive adds done tag to completed items."""
    args = argparse.Namespace()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Praxis

- [x] Done task without tag
""")
        praxis_path = Path(f.name)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Praxis Archive\n")
        archive_path = Path(f.name)
    
    try:
        orig_praxis = namespace['PRAXIS']
        orig_archive = namespace['PRAXIS_ARCHIVE']
        
        namespace['PRAXIS'] = praxis_path
        namespace['PRAXIS_ARCHIVE'] = archive_path
        
        with patch('builtins.print'):
            get_func('cmd_archive')(args)
        
        # Check archive content has done tag
        archive_content = archive_path.read_text()
        assert "done:" in archive_content
        
        namespace['PRAXIS'] = orig_praxis
        namespace['PRAXIS_ARCHIVE'] = orig_archive
    finally:
        praxis_path.unlink(missing_ok=True)
        archive_path.unlink(missing_ok=True)


def test_cmd_archive_no_praxis_file():
    """Test cmd_archive exits when Praxis.md doesn't exist."""
    args = argparse.Namespace()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        orig_praxis = namespace['PRAXIS']
        namespace['PRAXIS'] = Path(tmpdir) / "nonexistent.md"
        
        try:
            with pytest.raises(SystemExit):
                get_func('cmd_archive')(args)
        finally:
            namespace['PRAXIS'] = orig_praxis


def test_cmd_archive_skips_children_of_completed():
    """Test cmd_archive skips indented children of completed items."""
    args = argparse.Namespace()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("""# Praxis

- [x] Done task
  - Child item 1
  - Child item 2
- [ ] Active task
  - Active child
""")
        praxis_path = Path(f.name)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write("# Praxis Archive\n")
        archive_path = Path(f.name)
    
    try:
        orig_praxis = namespace['PRAXIS']
        orig_archive = namespace['PRAXIS_ARCHIVE']
        
        namespace['PRAXIS'] = praxis_path
        namespace['PRAXIS_ARCHIVE'] = archive_path
        
        with patch('builtins.print'):
            get_func('cmd_archive')(args)
        
        # Check that children of completed item are not in remaining
        remaining = praxis_path.read_text()
        assert "Child item" not in remaining
        assert "Active child" in remaining
        
        namespace['PRAXIS'] = orig_praxis
        namespace['PRAXIS_ARCHIVE'] = orig_archive
    finally:
        praxis_path.unlink(missing_ok=True)
        archive_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Test cmd_daily
# ---------------------------------------------------------------------------

def test_cmd_daily_creates_new_file():
    """Test cmd_daily creates new daily note when it doesn't exist."""
    args = argparse.Namespace(title="Test Session")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        orig_daily_dir = namespace['DAILY_DIR']
        namespace['DAILY_DIR'] = Path(tmpdir)
        
        try:
            with patch('builtins.print'):
                get_func('cmd_daily')(args)
            
            # Check file was created
            today = datetime.now().strftime("%Y-%m-%d")
            daily_path = Path(tmpdir) / f"{today}.md"
            assert daily_path.exists()
            
            content = daily_path.read_text()
            assert "# " in content  # Has header
            assert "Test Session" in content
            
            namespace['DAILY_DIR'] = orig_daily_dir
        finally:
            namespace['DAILY_DIR'] = orig_daily_dir


def test_cmd_daily_appends_to_existing():
    """Test cmd_daily appends to existing daily note."""
    args = argparse.Namespace(title="Afternoon Session")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        today = datetime.now().strftime("%Y-%m-%d")
        daily_path = Path(tmpdir) / f"{today}.md"
        daily_path.write_text("# 2026-03-31 — Tuesday\n\nExisting content\n")
        
        orig_daily_dir = namespace['DAILY_DIR']
        namespace['DAILY_DIR'] = Path(tmpdir)
        
        try:
            with patch('builtins.print'):
                get_func('cmd_daily')(args)
            
            content = daily_path.read_text()
            assert "Existing content" in content
            assert "Afternoon Session" in content
            
            namespace['DAILY_DIR'] = orig_daily_dir
        finally:
            namespace['DAILY_DIR'] = orig_daily_dir


def test_cmd_daily_default_title():
    """Test cmd_daily uses 'Session' as default title."""
    args = argparse.Namespace(title=None)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        orig_daily_dir = namespace['DAILY_DIR']
        namespace['DAILY_DIR'] = Path(tmpdir)
        
        try:
            with patch('builtins.print'):
                get_func('cmd_daily')(args)
            
            today = datetime.now().strftime("%Y-%m-%d")
            daily_path = Path(tmpdir) / f"{today}.md"
            content = daily_path.read_text()
            assert "Session" in content
            
            namespace['DAILY_DIR'] = orig_daily_dir
        finally:
            namespace['DAILY_DIR'] = orig_daily_dir


# ---------------------------------------------------------------------------
# Test cmd_reflect
# ---------------------------------------------------------------------------

def test_cmd_reflect_success():
    """Test cmd_reflect runs reflection and outputs findings."""
    args = argparse.Namespace(session="test123", json=False)
    
    findings = [
        {"category": "discovery", "lesson": "Found something"},
        {"category": "taste_calibration", "lesson": "Taste adjusted"}
    ]
    usage = {"input_tokens": 100, "output_tokens": 50}
    
    # Patch the function in namespace
    orig_run_reflect = namespace['run_reflect']
    namespace['run_reflect'] = lambda sid: (findings, usage)
    
    try:
        with patch('builtins.print') as mock_print:
            get_func('cmd_reflect')(args)
            
            printed = [str(c.args[0]) if c.args else "" for c in mock_print.call_args_list]
            assert any("discovery" in p or "Found something" in p for p in printed)
    finally:
        namespace['run_reflect'] = orig_run_reflect


def test_cmd_reflect_json_output():
    """Test cmd_reflect --json outputs JSON."""
    args = argparse.Namespace(session="test123", json=True)
    
    findings = [{"category": "discovery", "lesson": "Test"}]
    usage = {"input_tokens": 100, "output_tokens": 50}
    
    orig_run_reflect = namespace['run_reflect']
    namespace['run_reflect'] = lambda sid: (findings, usage)
    
    try:
        with patch('builtins.print') as mock_print:
            get_func('cmd_reflect')(args)
            
            # Should print JSON
            printed = mock_print.call_args_list[0].args[0]
            # Should be valid JSON
            parsed = json.loads(printed)
            assert len(parsed) == 1
    finally:
        namespace['run_reflect'] = orig_run_reflect


def test_cmd_reflect_no_findings():
    """Test cmd_reflect handles no findings gracefully."""
    args = argparse.Namespace(session="test123", json=False)
    
    orig_run_reflect = namespace['run_reflect']
    namespace['run_reflect'] = lambda sid: ([], {})
    
    try:
        with patch('builtins.print') as mock_print:
            get_func('cmd_reflect')(args)
            
            printed = [str(c.args[0]) if c.args else "" for c in mock_print.call_args_list]
            assert any("No messages found" in p for p in printed)
    finally:
        namespace['run_reflect'] = orig_run_reflect


# ---------------------------------------------------------------------------
# Test cmd_extract
# ---------------------------------------------------------------------------

def test_cmd_extract_from_file():
    """Test cmd_extract reads gather JSON from file."""
    args = argparse.Namespace(input="/tmp/gather.json")
    
    gather_json = json.dumps({
        "reflect": [
            {"category": "discovery", "lesson": "Test lesson"}
        ]
    })
    
    channel_result = MagicMock()
    channel_result.returncode = 0
    channel_result.stdout = "1. FILE: finding | test.md | Test lesson\n"
    
    with patch('pathlib.Path.read_text', return_value=gather_json), \
         patch.object(telophase_subprocess, 'run', return_value=channel_result), \
         patch('builtins.print') as mock_print:
        
        get_func('cmd_extract')(args)
        
        assert mock_print.called


def test_cmd_extract_from_stdin():
    """Test cmd_extract reads gather JSON from stdin."""
    args = argparse.Namespace(input=None)
    
    gather_json = json.dumps({
        "reflect": [
            {"category": "discovery", "lesson": "Test lesson"}
        ]
    })
    
    channel_result = MagicMock()
    channel_result.returncode = 0
    channel_result.stdout = "1. SKIP: already known\n"
    
    with patch('sys.stdin.read', return_value=gather_json), \
         patch.object(telophase_subprocess, 'run', return_value=channel_result), \
         patch('builtins.print') as mock_print:
        
        get_func('cmd_extract')(args)
        
        assert mock_print.called


def test_cmd_extract_no_candidates():
    """Test cmd_extract handles no candidates."""
    args = argparse.Namespace(input=None)
    
    gather_json = json.dumps({"reflect": []})
    
    with patch('sys.stdin.read', return_value=gather_json), \
         patch('builtins.print') as mock_print:
        
        get_func('cmd_extract')(args)
        
        printed = [str(c.args[0]) if c.args else "" for c in mock_print.call_args_list]
        assert any("no candidates" in p for p in printed)


def test_cmd_extract_invalid_json():
    """Test cmd_extract exits on invalid JSON."""
    args = argparse.Namespace(input=None)
    
    with patch('sys.stdin.read', return_value="not valid json"), \
         pytest.raises(SystemExit):
        get_func('cmd_extract')(args)


def test_cmd_extract_channel_error():
    """Test cmd_extract handles channel error."""
    args = argparse.Namespace(input=None)
    
    gather_json = json.dumps({
        "reflect": [{"category": "discovery", "lesson": "Test"}]
    })
    
    channel_result = MagicMock()
    channel_result.returncode = 1
    channel_result.stderr = "API error"
    
    with patch('sys.stdin.read', return_value=gather_json), \
         patch.object(telophase_subprocess, 'run', return_value=channel_result), \
         pytest.raises(SystemExit):
        get_func('cmd_extract')(args)


# ---------------------------------------------------------------------------
# Test main argument parsing
# ---------------------------------------------------------------------------

def test_main_no_command_exits():
    """Test main exits when no command provided."""
    with patch('sys.argv', ['telophase']), \
         pytest.raises(SystemExit):
        get_func('main')()


def test_main_gather_command():
    """Test main routes to cmd_gather."""
    # Patch cmd_gather in namespace
    called = []
    orig_cmd_gather = namespace['cmd_gather']
    namespace['cmd_gather'] = lambda args: called.append(True)
    
    try:
        with patch('sys.argv', ['telophase', 'gather', '--syntactic']):
            get_func('main')()
            assert called
    finally:
        namespace['cmd_gather'] = orig_cmd_gather


def test_main_archive_command():
    """Test main routes to cmd_archive."""
    called = []
    orig_cmd_archive = namespace['cmd_archive']
    namespace['cmd_archive'] = lambda args: called.append(True)
    
    try:
        with patch('sys.argv', ['telophase', 'archive']):
            get_func('main')()
            assert called
    finally:
        namespace['cmd_archive'] = orig_cmd_archive


def test_main_daily_command():
    """Test main routes to cmd_daily."""
    called = []
    orig_cmd_daily = namespace['cmd_daily']
    namespace['cmd_daily'] = lambda args: called.append(True)
    
    try:
        with patch('sys.argv', ['telophase', 'daily', 'My Session']):
            get_func('main')()
            assert called
    finally:
        namespace['cmd_daily'] = orig_cmd_daily


def test_main_reflect_command():
    """Test main routes to cmd_reflect."""
    called = []
    orig_cmd_reflect = namespace['cmd_reflect']
    namespace['cmd_reflect'] = lambda args: called.append(True)
    
    try:
        with patch('sys.argv', ['telophase', 'reflect', 'session123']):
            get_func('main')()
            assert called
    finally:
        namespace['cmd_reflect'] = orig_cmd_reflect


def test_main_extract_command():
    """Test main routes to cmd_extract."""
    called = []
    orig_cmd_extract = namespace['cmd_extract']
    namespace['cmd_extract'] = lambda args: called.append(True)
    
    try:
        with patch('sys.argv', ['telophase', 'extract', '--input', '/tmp/gather.json']):
            get_func('main')()
            assert called
    finally:
        namespace['cmd_extract'] = orig_cmd_extract


# ---------------------------------------------------------------------------
# Test constants and paths
# ---------------------------------------------------------------------------

def test_constants_defined():
    """Test that all expected constants are defined."""
    assert 'HOME' in namespace
    assert 'NOTES' in namespace
    assert 'PRAXIS' in namespace
    assert 'PRAXIS_ARCHIVE' in namespace
    assert 'DAILY_DIR' in namespace
    assert 'NOW_MD' in namespace
    assert 'SKILLS' in namespace
    assert 'CLAUDE_SKILLS' in namespace
    assert 'MEMORY' in namespace
    assert 'MEMORY_LIMIT' in namespace
    assert 'DEFAULT_REPOS' in namespace


def test_default_repos_structure():
    """Test DEFAULT_REPOS has expected structure."""
    default_repos = namespace['DEFAULT_REPOS']
    assert 'skills' in default_repos
    assert 'officina' in default_repos
    assert 'scripts' in default_repos


def test_color_constants():
    """Test color constants are defined."""
    assert 'RESET' in namespace
    assert 'BOLD' in namespace
    assert 'GREEN' in namespace
    assert 'YELLOW' in namespace
    assert 'RED' in namespace
    assert 'OK' in namespace
    assert 'WARN' in namespace
    assert 'ERR' in namespace


# ---------------------------------------------------------------------------
# Test _print_human helper
# ---------------------------------------------------------------------------

def test_print_human_formats_output():
    """Test _print_human produces formatted output."""
    results = {
        "repos": {
            "skills": {"clean": True, "status": ""},
            "officina": {"clean": False, "status": "M file.txt"}
        },
        "skills": {"gaps": ["skill1"]},
        "memory": {"lines": 100, "limit": 150},
        "now": {"age_label": "fresh", "age_seconds": 100},
        "deps": [],
        "peira": None,
        "reflect": []
    }
    
    with patch('builtins.print') as mock_print:
        get_func('_print_human')(results, "test_session")
        
        printed = [str(c.args[0]) if c.args else "" for c in mock_print.call_args_list]
        # Should have header and status lines
        assert any("───" in p or "Legatum" in p for p in printed)


def test_print_human_with_reflection():
    """Test _print_human includes reflection candidates."""
    results = {
        "repos": {},
        "skills": {"gaps": []},
        "memory": {"lines": 50, "limit": 150},
        "now": {"age_label": "fresh", "age_seconds": 100},
        "deps": [],
        "peira": None,
        "reflect": [
            {"category": "discovery", "lesson": "Found something cool"}
        ]
    }
    
    with patch('builtins.print') as mock_print:
        get_func('_print_human')(results, "test_session")
        
        printed = [str(c.args[0]) if c.args else "" for c in mock_print.call_args_list]
        assert any("discovery" in p.lower() or "Found" in p for p in printed)


# ---------------------------------------------------------------------------
# Integration tests (subprocess-based)
# ---------------------------------------------------------------------------

class TestTelophaseSubprocess:
    """Test telophase via subprocess to catch import/runtime errors."""
    
    def test_script_is_executable(self):
        """Test that telophase script can be parsed."""
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(telophase_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"
    
    def test_help_output(self):
        """Test --help works."""
        result = subprocess.run(
            ["python3", str(telophase_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Should exit with 0 or print help to stdout
        assert "usage:" in result.stdout.lower() or result.returncode == 0
    
    def test_gather_help(self):
        """Test gather --help works."""
        result = subprocess.run(
            ["python3", str(telophase_path), "gather", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert "gather" in result.stdout.lower() or "repos" in result.stdout.lower()
    
    def test_archive_help(self):
        """Test archive --help works."""
        result = subprocess.run(
            ["python3", str(telophase_path), "archive", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
    
    def test_daily_help(self):
        """Test daily --help works."""
        result = subprocess.run(
            ["python3", str(telophase_path), "daily", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
    
    def test_reflect_help(self):
        """Test reflect --help works."""
        result = subprocess.run(
            ["python3", str(telophase_path), "reflect", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
    
    def test_extract_help(self):
        """Test extract --help works."""
        result = subprocess.run(
            ["python3", str(telophase_path), "extract", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
