#!/usr/bin/env python3
"""Tests for methylation-review effector — tests data gathering and synthesis."""

import pytest
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Execute the methylation-review file directly
methylation_review_path = Path("/home/terry/germline/effectors/methylation-review")
methylation_review_code = methylation_review_path.read_text()
namespace = {}
exec(methylation_review_code, namespace)

# Extract all the functions/globals from the namespace
methylation_review = type('methylation_review_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(methylation_review, key, value)

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

def test_paths_are_absolute():
    """Test all paths are absolute and correctly set."""
    assert methylation_review.METHYLATION_JSONL.is_absolute()
    assert methylation_review.METHYLATION_EFFECTOR.is_absolute()
    assert methylation_review.TMP_DIR.is_absolute()
    assert methylation_review.CHANNEL.is_absolute()
    assert methylation_review.METHYLATION_EFFECTOR.exists()

# ---------------------------------------------------------------------------
# Test run_cmd
# ---------------------------------------------------------------------------

def test_run_cmd_success():
    """Test run_cmd returns correct tuple on success."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "output"
    mock_result.stderr = "stderr"
    
    with patch('subprocess.run', return_value=mock_result):
        code, out, err = methylation_review.run_cmd(["echo", "test"])
        assert code == 0
        assert out == "output"
        assert err == "stderr"

def test_run_cmd_exception():
    """Test run_cmd handles exceptions gracefully."""
    with patch('subprocess.run', side_effect=Exception("timeout")):
        code, out, err = methylation_review.run_cmd(["slow-command"])
        assert code == -1
        assert out == ""
        assert "timeout" in err

# ---------------------------------------------------------------------------
# Test gather_effector_proposals
# ---------------------------------------------------------------------------

def test_gather_effector_proposals_runs_effector():
    """Test gather_effector_proposals runs the methylation effector."""
    # Save original run_cmd
    original_run_cmd = namespace['run_cmd']
    namespace['run_cmd'] = lambda cmd, timeout=180: (0, "", "")
    
    with patch.object(Path, 'exists', return_value=False):
        content = methylation_review.gather_effector_proposals()
        # With no files, returns empty string with two newlines
        assert content.strip() == ""
    
    namespace['run_cmd'] = original_run_cmd

# ---------------------------------------------------------------------------
# Test gather_jsonl_observations
# ---------------------------------------------------------------------------

def test_gather_jsonl_no_file_returns_message():
    """Test gather_jsonl_observations returns message when no file exists."""
    with patch.object(Path, 'exists', return_value=False):
        result = methylation_review.gather_jsonl_observations()
        assert "(no methylation.jsonl found)" in result

def test_gather_jsonl_filters_recent_events():
    """Test gather_jsonl_observations only includes recent events."""
    now = datetime.now(timezone.utc)
    old_ts = (now - timedelta(days=10)).isoformat()
    new_ts = (now - timedelta(days=2)).isoformat()
    
    jsonl_content = f'''
{{"ts": "{old_ts}", "type": "crystallize", "text": "old thing"}}
{{"ts": "{new_ts}", "type": "crystallize", "text": "new thing"}}
    '''
    
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=jsonl_content):
            result = methylation_review.gather_jsonl_observations(days=7)
            # Only the new one should be included
            assert "new thing" in result
            assert "old thing" not in result

def test_gather_jsonl_handles_invalid_lines():
    """Test gather_jsonl_observations skips invalid JSON lines."""
    now = datetime.now(timezone.utc)
    recent_ts = (now - timedelta(days=2)).isoformat()
    
    jsonl_content = f'''
not valid json
{{"ts": "{recent_ts}", "type": "valid"}}
'''
    
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=jsonl_content):
            # Should not raise, just skip invalid line
            result = methylation_review.gather_jsonl_observations()
            assert "valid" in result

# ---------------------------------------------------------------------------
# Test synthesize_review
# ---------------------------------------------------------------------------

def test_synthesize_review_calls_channel_opus():
    """Test synthesize_review calls channel effector with opus model."""
    original_run_cmd = namespace['run_cmd']
    namespace['run_cmd'] = lambda cmd, timeout=180: (0, "synthesized review content", "")
    
    result = methylation_review.synthesize_review("proposals", "observations")
    
    namespace['run_cmd'] = original_run_cmd
    assert "synthesized review content" == result.strip()

def test_synthesize_review_handles_failure():
    """Test synthesize_review returns error message on failure."""
    original_run_cmd = namespace['run_cmd']
    namespace['run_cmd'] = lambda cmd, timeout=180: (1, "", "channel failed")
    
    result = methylation_review.synthesize_review("proposals", "observations")
    
    namespace['run_cmd'] = original_run_cmd
    assert "Error: Synthesis failed" in result
    assert "proposals" in result

# ---------------------------------------------------------------------------
# Test main writes output
# ---------------------------------------------------------------------------

def test_main_writes_review_to_tmp():
    """Test main writes the generated review to /tmp directory."""
    original_gather = namespace['gather_effector_proposals']
    original_observations = namespace['gather_jsonl_observations']
    original_synthesize = namespace['synthesize_review']
    
    namespace['gather_effector_proposals'] = lambda: "proposals"
    namespace['gather_jsonl_observations'] = lambda: "observations"
    namespace['synthesize_review'] = lambda p, o: "# Review\n\n- item 1\n- item 2"
    
    mock_write = MagicMock()
    original_write = Path.write_text
    Path.write_text = mock_write
    
    methylation_review.main()
    
    # Restore
    Path.write_text = original_write
    namespace['gather_effector_proposals'] = original_gather
    namespace['gather_jsonl_observations'] = original_observations
    namespace['synthesize_review'] = original_synthesize
    
    # Should write to tmp
    assert mock_write.called
