#!/usr/bin/env python3
"""Tests for methylation effector — mocks all external file I/O and subprocess."""

import json
import pytest
import subprocess
import importlib.util
from unittest.mock import MagicMock, mock_open, patch, PropertyMock
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Execute the methylation file directly
methylation_code = Path("/home/terry/germline/effectors/methylation").read_text()
namespace = {}
exec(methylation_code, namespace)

# Extract all the functions/globals from the namespace
methylation = type('methylation_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(methylation, key, value)

# ---------------------------------------------------------------------------
# Test parsing and signal reading
# ---------------------------------------------------------------------------

def test_cutoff_is_seven_days_ago():
    """Test _cutoff returns a datetime 7 days before now."""
    before = datetime.now(UTC) - timedelta(days=methylation.WINDOW_DAYS)
    cutoff = methylation._cutoff()
    after = datetime.now(UTC) - timedelta(days=methylation.WINDOW_DAYS)
    # Should be between before and after (small tolerance for test execution)
    assert before <= cutoff <= after + timedelta(seconds=1)

def test_parse_ts_valid_iso():
    """Test _parse_ts correctly parses valid ISO timestamps."""
    # No timezone
    dt = methylation._parse_ts("2026-03-25T10:00:00")
    assert dt is not None
    assert dt.year == 2026
    assert dt.tzinfo is not None  # Should add UTC
    
    # With timezone
    dt2 = methylation._parse_ts("2026-03-25T10:00:00Z")
    assert dt2 is not None
    
def test_parse_ts_invalid():
    """Test _parse_ts returns None for invalid timestamps."""
    assert methylation._parse_ts("") is None
    assert methylation._parse_ts("not-a-timestamp") is None
    assert methylation._parse_ts("2026/03/25") is None

def test_read_methylation_candidates_file_missing():
    """Test read_methylation_candidates returns empty list when file missing."""
    with patch.object(type(methylation.METHYLATION_CANDIDATES), 'exists', return_value=False):
        result = methylation.read_methylation_candidates()
        assert result == []

def test_read_methylation_candidates_parses_valid_entries():
    """Test read_methylation_candidates correctly parses recent valid entries."""
    recent_ts = (datetime.now(UTC) - timedelta(days=3)).isoformat()
    old_ts = (datetime.now(UTC) - timedelta(days=10)).isoformat()
    
    lines = [
        json.dumps({"ts": recent_ts, "probe": "chromatin", "repair_label": "fix_permissions"}),
        json.dumps({"ts": old_ts, "probe": "network", "repair_label": "reset_socket"}),  # Too old
        json.dumps({"ts": "invalid", "probe": "bad"}),  # Invalid ts
        "not valid json",  # Invalid json
        "",  # Empty line
    ]
    
    mock_content = "\n".join(lines)
    
    with patch.object(type(methylation.METHYLATION_CANDIDATES), 'exists', return_value=True):
        with patch.object(type(methylation.METHYLATION_CANDIDATES), 'read_text', return_value=mock_content):
            result = methylation.read_methylation_candidates()
            assert len(result) == 1
            assert result[0]["probe"] == "chromatin"

def test_read_infections_file_missing():
    """Test read_infections returns empty list when file missing."""
    with patch.object(type(methylation.INFECTION_LOG), 'exists', return_value=False):
        result = methylation.read_infections()
        assert result == []

def test_read_inflammasome_log_parses_failures():
    """Test read_inflammasome_log extracts FAIL lines correctly."""
    recent_ts = (datetime.now(UTC) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    old_ts = (datetime.now(UTC) - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    lines = [
        f"[{recent_ts}] [FAIL] chromatin_check — could not access /data/methylation (123ms)",
        f"[{old_ts}] [FAIL] network_ping — timeout connecting (456ms)",
        f"[{recent_ts}] [INFO] everything ok — no problem here",
        "[not-a-timestamp] [FAIL] bad_probe — invalid timestamp but still parsed",
        f"[{recent_ts}] [FAIL] bare_failure",  # No separator
    ]
    
    mock_content = "\n".join(lines)
    
    with patch.object(type(methylation.INFLAMMASOME_LOG), 'exists', return_value=True):
        with patch.object(type(methylation.INFLAMMASOME_LOG), 'read_text', return_value=mock_content):
            failures = methylation.read_inflammasome_log()
            # Should get 3 recent failures (the invalid ts is still included as ts_str)
            assert len(failures) == 3
            probes = {f["probe"] for f in failures}
            assert "chromatin_check" in probes
            assert "bad_probe" in probes
            assert "bare_failure" in probes
            assert "network_ping" not in probes  # Too old
            
            # Check message extraction
            chromatin = next(f for f in failures if f["probe"] == "chromatin_check")
            assert "could not access" in chromatin["message"]

def test_read_inflammasome_log_file_missing():
    """Test read_inflammasome_log returns empty list when file missing."""
    with patch.object(type(methylation.INFLAMMASOME_LOG), 'exists', return_value=False):
        result = methylation.read_inflammasome_log()
        assert result == []

# ---------------------------------------------------------------------------
# Test pattern extraction from inflammasome.py
# ---------------------------------------------------------------------------

def test_extract_probe_names_basic():
    """Test extract_probe_names extracts probe names from _PROBES definition."""
    mock_src = '''
    _PROBES = list[
        ("chromatin", probe_chromatin),
        ("network", probe_network),
        ("disk_space", probe_disk_space),
    ]
    '''
    
    with patch.object(type(methylation.INFLAMMASOME_PY), 'read_text', return_value=mock_src):
        probes = methylation.extract_probe_names()
        assert probes == ["chromatin", "network", "disk_space"]

def test_extract_probe_names_file_error():
    """Test extract_probe_names returns empty list on file error."""
    with patch.object(type(methylation.INFLAMMASOME_PY), 'read_text', side_effect=Exception("file not found")):
        probes = methylation.extract_probe_names()
        assert probes == []

def test_extract_repair_pattern_labels():
    """Test extract_repair_pattern_labels extracts labels correctly."""
    # The parser looks for lines that start with " and end with ",
    mock_src = '''
    _REPAIR_PATTERNS = list[
        ("fix_permissions", lambda p: fix_perms(p), _fix_generic,
        "fix_permissions",
        ),
        ("reset_socket", lambda p: reset_sock(p), _reset_socket,
        "reset_socket",
        ),
    ]
    '''

    with patch.object(type(methylation.INFLAMMASOME_PY), 'read_text', return_value=mock_src):
        labels = methylation.extract_repair_pattern_labels()
        # The labels are on separate lines, so should extract both
        assert "fix_permissions" in labels
        assert "reset_socket" in labels

def test_extract_repair_pattern_labels_file_error():
    """Test extract_repair_pattern_labels returns empty list on error."""
    with patch.object(type(methylation.INFLAMMASOME_PY), 'read_text', side_effect=Exception("read error")):
        labels = methylation.extract_repair_pattern_labels()
        assert labels == []

# ---------------------------------------------------------------------------
# Test summarization
# ---------------------------------------------------------------------------

def test_summarize_repairs_empty():
    """Test summarize_repairs with no candidates."""
    summary = methylation.summarize_repairs([])
    assert "No successful repairs" in summary

def test_summarize_repairs_with_data():
    """Test summarize_repairs groups by key correctly."""
    candidates = [
        {"probe": "chromatin", "ts": "2026-03-25T10:00:00"},
        {"probe": "chromatin", "ts": "2026-03-26T10:00:00"},
        {"probe": "disk", "ts": "2026-03-27T10:00:00"},
    ]
    summary = methylation.summarize_repairs(candidates)
    assert "chromatin: 2x" in summary
    assert "disk: 1x" in summary

def test_summarize_infections_empty():
    """Test summarize_infections with no data."""
    summary = methylation.summarize_infections([], [])
    assert "No infection events" in summary
    assert "No probe failures" in summary

def test_summarize_infections_with_data():
    """Test summarize_infections counts healed vs unhealed."""
    infections = [
        {"tool": "malware_scanner", "healed": True},
        {"tool": "malware_scanner", "healed": True},
        {"tool": "rootkit", "healed": False},
    ]
    failures = [
        {"probe": "chromatin"},
        {"probe": "chromatin"},
        {"probe": "network"},
    ]
    summary = methylation.summarize_infections(infections, failures)
    assert "malware_scanner: 2x (2 healed)" in summary
    assert "rootkit: 1x (0 healed)" in summary
    assert "chromatin: 2x" in summary

# ---------------------------------------------------------------------------
# Test crystallizable pattern detection
# ---------------------------------------------------------------------------

def test_find_crystallizable_patterns_none_above_threshold():
    """Test find_crystallizable_patterns returns empty when no patterns meet min count."""
    # Current MIN_PATTERN_COUNT is 2
    candidates = [{"probe": "a"}]
    infections = [{"tool": "b"}]
    failures = [{"probe": "c"}]
    
    patterns = methylation.find_crystallizable_patterns(candidates, infections, failures)
    assert not any(patterns[k] for k in patterns)
    assert len(patterns["repair_candidates"]) == 0
    assert len(patterns["probe_failures"]) == 0
    assert len(patterns["infection_tools"]) == 0

def test_find_crystallizable_patterns_some_above_threshold():
    """Test find_crystallizable_patterns correctly identifies patterns above threshold."""
    candidates = [{"probe": "a"}, {"probe": "a"}, {"probe": "b"}]
    infections = [{"tool": "c"}, {"tool": "c"}, {"tool": "c"}]
    failures = [{"probe": "d"}, {"probe": "d"}]
    
    patterns = methylation.find_crystallizable_patterns(candidates, infections, failures)
    assert patterns["repair_candidates"]["a"] == 2
    assert patterns["infection_tools"]["c"] == 3
    assert patterns["probe_failures"]["d"] == 2
    assert "b" not in patterns["repair_candidates"]  # Only 1 occurrence

# ---------------------------------------------------------------------------
# Test auto-apply safety gate
# ---------------------------------------------------------------------------

def test_is_safe_to_autoapply_not_probe():
    """Test is_safe_to_autoapply returns False if not a probe type."""
    response = """TYPE: repair
NAME: fix_permissions
CODE: def fix_permissions():
    os.chmod("/", 0o777)
RATIONALE: fix everything
"""
    assert not methylation.is_safe_to_autoapply(response)

def test_is_safe_to_autoapply_safe_probe():
    """Test is_safe_to_autoapply accepts safe probe that just checks Path.exists."""
    response = """TYPE: probe
NAME: check_data_dir
CODE: def probe_data_dir_exists():
    data_dir = Path.home() / "data"
    return data_dir.exists()
RATIONALE: We need to check if data dir exists before proceeding
"""
    assert methylation.is_safe_to_autoapply(response) is True

def test_is_safe_to_autoapply_unsafe_subprocess():
    """Test is_safe_to_autoapply rejects code that uses subprocess."""
    response = """TYPE: probe
NAME: run_system_check
CODE: def probe_system():
    result = subprocess.run(["df", "-h"], capture_output=True)
    return result.returncode == 0
RATIONALE: check disk usage
"""
    assert not methylation.is_safe_to_autoapply(response)

def test_is_safe_to_autoapply_unsafe_write():
    """Test is_safe_to_autoapply rejects code that writes files."""
    response = """TYPE: probe
NAME: write_log
CODE: def probe_log():
    with open("/tmp/log.txt", "w") as f:
        f.write("probe ran\n")
    return True
RATIONALE: write log
"""
    assert not methylation.is_safe_to_autoapply(response)

# ---------------------------------------------------------------------------
# Test hybridization
# ---------------------------------------------------------------------------

def test_hybridization_pass_no_gap():
    """Test hybridization_pass returns None when no gap found."""
    patterns = {
        "repair_candidates": {},
        "probe_failures": {},
        "infection_tools": {},
    }
    gap = methylation.hybridization_pass(patterns, [], [], [])
    assert gap is None

def test_hybridization_pass_cross_subsystem_gap():
    """Test hybridization_pass identifies cross-subsystem gaps."""
    patterns = {
        "repair_candidates": {},
        "probe_failures": {"novel_tool": 2},
        "infection_tools": {"novel_tool": 3},
    }
    infections = [
        {"tool": "novel_tool", "healed": False},
        {"tool": "novel_tool", "healed": False},
    ]
    failures = [{"probe": "novel_tool"}, {"probe": "novel_tool"}]
    
    gap = methylation.hybridization_pass(patterns, [], infections, failures)
    assert gap is not None
    assert "novel_tool" in gap
    assert "probe failure" in gap
    assert "unhealed infection" in gap

# ---------------------------------------------------------------------------
# Test write proposals
# ---------------------------------------------------------------------------

def test_write_proposal_creates_correct_content():
    """Test write_proposal writes expected content to temp file."""
    patterns = {
        "repair_candidates": {"chromatin_fix": 2},
        "probe_failures": {"network_check": 3},
        "infection_tools": {},
    }
    response = "**TYPE: probe**  \n**NAME: network_check**  \n**CODE:** def probe_network():\n    return True\n**RATIONALE:** need better checks"
    
    with patch('pathlib.Path.mkdir'):
        with patch('pathlib.Path.write_text') as mock_write:
            result_path = methylation.write_proposal(response, patterns, "2026-03-31")
            # Verify write_text was called
            assert mock_write.called
            # Get the written content
            written_content = mock_write.call_args[0][0]
            assert "Methylation Proposal" in written_content
            assert "chromatin_fix" in written_content
            assert "network_check" in written_content
            assert "Sonnet synthesis" in written_content
            assert "2026-03-31" in written_content
            assert str(result_path).endswith("2026-03-31.md")

# ---------------------------------------------------------------------------
# Test dispatch_sonnet
# ---------------------------------------------------------------------------

def test_dispatch_sonnet_channel_missing():
    """Test dispatch_sonnet returns None when channel is missing."""
    with patch.object(type(methylation.CHANNEL), 'exists', return_value=False):
        result = methylation.dispatch_sonnet("test prompt")
        assert result is None

def test_dispatch_sonnet_success():
    """Test dispatch_sonnet returns output on successful subprocess run."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "TYPE: probe\nNAME: test\nCODE: def probe():\n    return True\nRATIONALE: test"
    mock_result.stderr = ""

    with patch.object(type(methylation.CHANNEL), 'exists', return_value=True):
        with patch('subprocess.run', return_value=mock_result):
            result = methylation.dispatch_sonnet("test prompt")
            assert result is not None
            assert "TYPE: probe" in result

def test_dispatch_sonnet_timeout():
    """Test dispatch_sonnet handles timeout gracefully and returns None."""
    with patch.object(type(methylation.CHANNEL), 'exists', return_value=True):
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 120)):
            result = methylation.dispatch_sonnet("test prompt")
            assert result is None

def test_dispatch_sonnet_non_zero_exit():
    """Test dispatch_sonnet returns None when channel exits with error."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "error occurred"
    
    with patch.object(type(methylation.CHANNEL), 'exists', return_value=True):
        with patch('subprocess.run', return_value=mock_result):
            result = methylation.dispatch_sonnet("test prompt")
            assert result is None

# ---------------------------------------------------------------------------
# Test tissue routing
# ---------------------------------------------------------------------------

def test_tissue_route_fallback():
    """Test _tissue_route returns fallback when import fails."""
    with patch('builtins.__import__', side_effect=ImportError("no module")):
        result = methylation._tissue_route("methylation")
        assert result == "glm"

# ---------------------------------------------------------------------------
# Test main
# ---------------------------------------------------------------------------

def test_main_no_patterns(capsys):
    """Test main exits early when no patterns above threshold."""
    # Patch at the file level since exec'd code has direct references
    with patch.object(type(methylation.METHYLATION_CANDIDATES), 'exists', return_value=False):
        with patch.object(type(methylation.INFECTION_LOG), 'exists', return_value=False):
            with patch.object(type(methylation.INFLAMMASOME_LOG), 'exists', return_value=False):
                methylation.main()
                # Check that the expected message was logged
                captured = capsys.readouterr()
                assert "no patterns above threshold" in captured.out
