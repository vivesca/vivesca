#!/usr/bin/env python3
"""Tests for paracrine effector — mocks all external file I/O and subprocess."""

import pytest
import subprocess
import yaml
from unittest.mock import MagicMock, patch
from pathlib import Path

# Execute the paracrine file directly
paracrine_path = Path("/home/terry/germline/effectors/paracrine")
paracrine_code = paracrine_path.read_text()
namespace = {}
exec(paracrine_code, namespace)

# Extract all the functions/globals from the namespace
paracrine = type('paracrine_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(paracrine, key, value)

# ---------------------------------------------------------------------------
# Test AXES definition
# ---------------------------------------------------------------------------

def test_axes_has_correct_keys():
    """Test that AXES has all expected behavioral axes defined."""
    expected_axes = [
        "autonomy", "verbosity", "speed_vs_quality", "scope",
        "routing", "capture_vs_flow", "intervention"
    ]
    assert sorted(paracrine.AXES.keys()) == sorted(expected_axes)
    for axis, keywords in paracrine.AXES.items():
        assert len(keywords) > 0
        assert all(isinstance(kw, str) for kw in keywords)

# ---------------------------------------------------------------------------
# Test load_feedback_memories
# ---------------------------------------------------------------------------

def test_load_feedback_memories_no_files():
    """Test load_feedback_memories returns empty list when no files exist."""
    with patch('pathlib.Path.glob', return_value=[]):
        memories = paracrine.load_feedback_memories()
        assert memories == []

def test_load_feedback_memories_parses_frontmatter_correctly():
    """Test load_feedback_memories correctly parses YAML frontmatter."""
    mock_path = MagicMock()
    mock_path.name = "feedback_test.md"
    mock_path.stem = "feedback_test"
    mock_path.read_text.return_value = """---
name: Test Feedback
description: This is a test
---
This is the body content.
"""
    
    with patch('pathlib.Path.glob', return_value=[mock_path]):
        memories = paracrine.load_feedback_memories()
        assert len(memories) == 1
        mem = memories[0]
        assert mem["file"] == "feedback_test.md"
        assert mem["name"] == "Test Feedback"
        assert mem["description"] == "This is a test"
        assert mem["body"] == "This is the body content."
        assert "test feedback" in mem["full_text"]

def test_load_feedback_memories_no_frontmatter():
    """Test load_feedback_memories handles files without YAML frontmatter."""
    mock_path = MagicMock()
    mock_path.name = "feedback_no_front.md"
    mock_path.stem = "feedback_no_front"
    mock_path.read_text.return_value = "Just plain text content here."
    
    with patch('pathlib.Path.glob', return_value=[mock_path]):
        memories = paracrine.load_feedback_memories()
        assert len(memories) == 1
        mem = memories[0]
        assert "plain text" in mem["full_text"]

def test_load_feedback_memories_invalid_yaml():
    """Test load_feedback_memories handles invalid YAML gracefully."""
    mock_path = MagicMock()
    mock_path.name = "feedback_bad_yaml.md"
    mock_path.stem = "feedback_bad_yaml"
    mock_path.read_text.return_value = """---
bad: yaml: here
- not closed
---
Body here.
"""
    
    with patch('pathlib.Path.glob', return_value=[mock_path]):
        memories = paracrine.load_feedback_memories()
        assert len(memories) == 1
        # Should get empty meta on YAML error
        assert memories[0]["name"] == "feedback_bad_yaml"

# ---------------------------------------------------------------------------
# Test cluster_by_axis
# ---------------------------------------------------------------------------

def test_cluster_by_axis_no_matches():
    """Test cluster_by_axis returns empty dict when no memories match any axis."""
    memories = [{
        "full_text": "this has no keywords from any axis",
        "file": "feedback_test.md"
    }]
    clusters = paracrine.cluster_by_axis(memories)
    assert len(clusters) == 0

def test_cluster_by_axis_matches_correct_axes():
    """Test cluster_by_axis correctly assigns memories to axes based on keywords."""
    # Memory that matches both autonomy and speed_vs_quality
    memory1 = {
        "full_text": "please act autonomously and do it quickly".lower(),
        "file": "feedback_1.md"
    }
    # Memory that matches verbosity
    memory2 = {
        "full_text": "please be more verbose and explain in detail".lower(),
        "file": "feedback_2.md"
    }
    
    clusters = paracrine.cluster_by_axis([memory1, memory2])
    
    assert "autonomy" in clusters
    assert "speed_vs_quality" in clusters
    assert "verbosity" in clusters
    assert len(clusters["autonomy"]) == 1
    assert len(clusters["speed_vs_quality"]) == 1
    assert len(clusters["verbosity"]) == 1
    assert clusters["autonomy"][0] == memory1

def test_cluster_by_axis_multiple_matches_same_axis():
    """Test multiple memories are correctly clustered to the same axis."""
    mem1 = {"full_text": "just do it".lower(), "file": "f1.md"}
    mem2 = {"full_text": "stop asking".lower(), "file": "f2.md"}
    mem3 = {"full_text": "something else".lower(), "file": "f3.md"}
    
    clusters = paracrine.cluster_by_axis([mem1, mem2, mem3])
    assert len(clusters["autonomy"]) == 2

# ---------------------------------------------------------------------------
# Test detect_tensions
# ---------------------------------------------------------------------------

def test_detect_tensions_no_clusters():
    """Test detect_tensions returns empty list with no clusters."""
    tensions = paracrine.detect_tensions({})
    assert tensions == []

def test_detect_tensions_autonomy_tension():
    """Test detect_tensions finds autonomy tension when both sides exist."""
    do_it_mem = {
        "file": "do_it.md",
        "full_text": "just do it".lower()
    }
    hold_mem = {
        "file": "hold.md",
        "full_text": "hold and gate".lower()
    }
    
    clusters = {
        "autonomy": [do_it_mem, hold_mem],
    }
    
    tensions = paracrine.detect_tensions(clusters)
    assert len(tensions) == 1
    tension = tensions[0]
    assert tension["axis"] == "autonomy"
    assert tension["label_a"] == "act immediately"
    assert tension["label_b"] == "gate on judgment"
    assert "do_it.md" in tension["pull_a"]
    assert "hold.md" in tension["pull_b"]
    assert tension["count"] == 2

def test_detect_tensions_autonomy_one_side():
    """Test no tension detected when only one side of autonomy exists."""
    only_do_it = [{
        "file": "do_it.md",
        "full_text": "just do it".lower()
    }]
    clusters = {"autonomy": only_do_it}
    tensions = paracrine.detect_tensions(clusters)
    assert len(tensions) == 0

def test_detect_tensions_speed_vs_quality_tension():
    """Test detect_tensions finds speed vs quality tension."""
    fast_mem = {
        "file": "fast.md",
        "full_text": "do it quickly immediately".lower()
    }
    careful_mem = {
        "file": "careful.md",
        "full_text": "verify and check thoroughly".lower()
    }
    
    clusters = {"speed_vs_quality": [fast_mem, careful_mem]}
    tensions = paracrine.detect_tensions(clusters)
    
    assert len(tensions) == 1
    tension = tensions[0]
    assert tension["axis"] == "speed_vs_quality"
    assert tension["label_a"] == "act fast"
    assert tension["label_b"] == "verify first"

def test_detect_tensions_capture_vs_flow_tension():
    """Test detect_tensions finds capture vs flow tension."""
    capture_mem = {
        "file": "capture.md",
        "full_text": "capture and save everything".lower()
    }
    flow_mem = {
        "file": "flow.md",
        "full_text": "keep the energy flowing don't cut".lower()
    }
    
    clusters = {"capture_vs_flow": [capture_mem, flow_mem]}
    tensions = paracrine.detect_tensions(clusters)
    
    assert len(tensions) == 1
    tension = tensions[0]
    assert tension["axis"] == "capture_vs_flow"
    assert tension["label_a"] == "capture everything"
    assert tension["label_b"] == "protect flow"

def test_detect_tensions_multiple_axes():
    """Test detect_tensions finds tensions on multiple axes."""
    # Autonomy tension
    do_it = {"file": "a1.md", "full_text": "just do it"}
    hold = {"file": "a2.md", "full_text": "hold gate"}
    
    # Speed vs quality tension
    fast = {"file": "s1.md", "full_text": "quick fast"}
    careful = {"file": "s2.md", "full_text": "verify check"}
    
    clusters = {
        "autonomy": [do_it, hold],
        "speed_vs_quality": [fast, careful],
        "verbosity": []  # Empty cluster won't be detected
    }
    
    tensions = paracrine.detect_tensions(clusters)
    assert len(tensions) == 2
    axes = {t["axis"] for t in tensions}
    assert "autonomy" in axes
    assert "speed_vs_quality" in axes

def test_detect_tensions_no_tension_when_only_one_side():
    """Test no tension detected when cluster exists but only one direction."""
    only_fast = [{"file": "f.md", "full_text": "quickly fast"}]
    clusters = {"speed_vs_quality": only_fast}
    tensions = paracrine.detect_tensions(clusters)
    assert len(tensions) == 0

# ---------------------------------------------------------------------------
# Test reconcile_tension
# ---------------------------------------------------------------------------

def test_reconcile_tension_handles_subprocess_success():
    """Test reconcile_tension gets and returns result from subprocess."""
    tension = {
        "axis": "autonomy",
        "pull_a": ["doit.md"],
        "pull_b": ["hold.md"],
        "label_a": "act",
        "label_b": "hold"
    }
    memories = [
        {"file": "doit.md", "body": "Just do it autonomously"},
        {"file": "hold.md", "body": "Hold and gate before acting"}
    ]
    
    mock_result = MagicMock()
    mock_result.stdout = "FALSE POSITIVE: No real contradiction here"
    mock_result.stderr = ""
    
    with patch('subprocess.run', return_value=mock_result):
        verdict = paracrine.reconcile_tension(tension, memories)
        assert "FALSE POSITIVE" in verdict

def test_reconcile_tension_handles_file_not_found():
    """Test reconcile_tension handles case when 'channel' command not found."""
    tension = {
        "axis": "autonomy",
        "pull_a": ["a.md"],
        "pull_b": ["b.md"],
        "label_a": "a",
        "label_b": "b"
    }
    memories = [{"file": "a.md", "body": "a"}, {"file": "b.md", "body": "b"}]
    
    with patch('subprocess.run', side_effect=FileNotFoundError("no command")):
        verdict = paracrine.reconcile_tension(tension, memories)
        assert "ERROR" in verdict
        assert "no command" in verdict

def test_reconcile_tension_handles_timeout():
    """Test reconcile_tension handles timeout gracefully."""
    tension = {
        "axis": "autonomy",
        "pull_a": ["a.md"],
        "pull_b": ["b.md"],
        "label_a": "a",
        "label_b": "b"
    }
    memories = [{"file": "a.md", "body": "a"}, {"file": "b.md", "body": "b"}]
    
    with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 60)):
        verdict = paracrine.reconcile_tension(tension, memories)
        assert "ERROR" in verdict
        assert "timed out" in verdict

# ---------------------------------------------------------------------------
# Test JSON output pathway
# ---------------------------------------------------------------------------

def test_json_output_integration():
    """Test that the JSON output pathway structures data correctly."""
    # We'll test the structure that would be printed to stdout
    test_memories = [
        {
            "file": "autonomy_justdo.md",
            "name": "Just do it",
            "description": "Act autonomously",
            "body": "Just do it without asking",
            "full_text": "just do it autonomously act".lower()
        },
        {
            "file": "autonomy_hold.md",
            "name": "Hold and gate",
            "description": "Check before acting",
            "body": "Always hold and confirm before acting",
            "full_text": "hold gate confirm check".lower()
        }
    ]
    
    clusters = paracrine.cluster_by_axis(test_memories)
    tensions = paracrine.detect_tensions(clusters)
    
    # Should have one tension
    assert len(tensions) == 1
    assert tensions[0]["axis"] == "autonomy"
    
    # Check that structure matches what main() would output
    output = {
        "total": len(test_memories),
        "clusters": {k: [m["file"] for m in v] for k, v in clusters.items()},
        "tensions": tensions,
    }
    
    assert output["total"] == 2
    assert "autonomy" in output["clusters"]
    assert len(output["clusters"]["autonomy"]) == 2

# ---------------------------------------------------------------------------
# Test main behavior
# ---------------------------------------------------------------------------

def test_main_no_memories():
    """Test main works when no feedback memories found."""
    with patch('pathlib.Path.glob', return_value=[]):
        # Just test that it runs without error
        paracrine.main()

def test_main_with_memories_no_tensions():
    """Test main runs successfully when there are memories but no tensions."""
    mock_path = MagicMock()
    mock_path.name = "test.md"
    mock_path.stem = "test"
    mock_path.read_text.return_value = "routing delegate to sonnet"
    
    with patch('pathlib.Path.glob', return_value=[mock_path]):
        # Just test that it runs without error
        paracrine.main()
