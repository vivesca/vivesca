#!/usr/bin/env python3
"""Tests for respirometry effector cost tracking functionality."""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

# Load effector via exec (no .py extension)
_effector_path = Path(__file__).parent.parent / "effectors" / "respirometry"
_ns = {"__name__": "respirometry"}
exec(open(_effector_path).read(), _ns)

get_cost_tracking = _ns["get_cost_tracking"]
_read_cost_rows = _ns["_read_cost_rows"]
_summarize_cost_rows = _ns["_summarize_cost_rows"]
_classify_cost_mode = _ns["_classify_cost_mode"]
_parse_metered_cost = _ns["_parse_metered_cost"]
FLAT_RATE_TOOLS = _ns["FLAT_RATE_TOOLS"]
COST_WINDOW_DAYS = _ns["COST_WINDOW_DAYS"]


def test_parse_metered_cost():
    """Test parsing metered cost from strings."""
    assert _parse_metered_cost("$0.05") == 0.05
    assert _parse_metered_cost("$1.234") == 1.234
    assert _parse_metered_cost("$10") == 10.0
    assert _parse_metered_cost("flat-rate") is None
    assert _parse_metered_cost("") is None
    assert _parse_metered_cost("invalid") is None


def test_classify_cost_mode():
    """Test classification of cost modes."""
    assert _classify_cost_mode({"cost_estimate": "$0.05", "tool": ""}) == "metered"
    assert _classify_cost_mode({"cost_estimate": "flat-rate", "tool": ""}) == "flat-rate"
    
    # Flat rate tools should always be flat-rate regardless of cost_estimate
    for tool in FLAT_RATE_TOOLS:
        assert _classify_cost_mode({"cost_estimate": "$0.00", "tool": tool}) == "flat-rate"
    
    # Should detect metered even without dollar sign if tool is specified
    assert _classify_cost_mode({"cost_estimate": "", "tool": "test"}) == "metered"
    assert _classify_cost_mode({"cost_estimate": "", "tool": ""}) == "unknown"


def test_summarize_cost_rows_empty():
    """Test summarization of empty rows."""
    summary = _summarize_cost_rows([])
    assert summary["runs"] == 0
    assert summary["successful_runs"] == 0
    assert summary["metered_cost_usd"] == 0.0
    assert summary["flat_rate_runs"] == 0
    assert summary["metered_runs"] == 0


def test_summarize_cost_rows_mixed():
    """Test summarization with mixed flat-rate and metered rows."""
    now = datetime.now(timezone.utc)
    
    rows = [
        {
            "timestamp": now.isoformat(),
            "tool": "goose",
            "duration_s": "300",
            "tasks": 5,
            "success": True,
            "cost_estimate": "$0.00",
            "_parsed_timestamp": now,
        },
        {
            "timestamp": now.isoformat(),
            "tool": "anthropic",
            "duration_s": "150",
            "tasks": 2,
            "success": True,
            "cost_estimate": "$0.03",
            "_parsed_timestamp": now,
        },
        {
            "timestamp": now.isoformat(),
            "tool": "openai",
            "duration_s": "200",
            "tasks": 3,
            "success": True,
            "cost_estimate": "$0.07",
            "_parsed_timestamp": now,
        },
    ]
    
    summary = _summarize_cost_rows(rows)
    assert summary["runs"] == 3
    assert summary["successful_runs"] == 3
    assert summary["flat_rate_runs"] == 1
    assert summary["metered_runs"] == 2
    assert summary["metered_cost_usd"] == 0.10
    assert summary["duration_s"] == 650.0
    assert summary["duration_hours"] == round(650 / 3600.0, 2)
    assert summary["tasks"] == 10
    assert "goose" in summary["flat_rate_tools"]
    assert summary["flat_rate_tools"]["goose"] == 1
    assert "anthropic" in summary["metered_tools"]
    assert "openai" in summary["metered_tools"]


def test_get_cost_tracking_no_file():
    """Test cost tracking when log file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily patch the path
        import respirometry
        original_path = respirometry.SORTASE_LOG
        respirometry.SORTASE_LOG = Path(tmpdir) / "nonexistent.jsonl"
        
        result = get_cost_tracking()
        assert result["available"] is False
        assert result["source"] == "sortase"
        assert result["lookback_days"] == COST_WINDOW_DAYS
        
        # Restore original
        respirometry.SORTASE_LOG = original_path


def test_get_cost_tracking_with_data():
    """Test cost tracking with sample data in the log."""
    now = datetime.now(timezone.utc)
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        # Write some test entries - one within window, one outside
        recent = now - timedelta(days=3)
        older = now - timedelta(days=10)
        
        json.dump({
            "timestamp": recent.isoformat(),
            "tool": "goose",
            "duration_s": 400,
            "tasks": 8,
            "success": True,
            "cost_estimate": "flat-rate",
        }, f)
        f.write('\n')
        
        json.dump({
            "timestamp": recent.isoformat(),
            "tool": "anthropic",
            "duration_s": 100,
            "tasks": 1,
            "success": True,
            "cost_estimate": "$0.025",
        }, f)
        f.write('\n')
        
        json.dump({
            "timestamp": older.isoformat(),
            "tool": "anthropic",
            "duration_s": 200,
            "tasks": 2,
            "success": True,
            "cost_estimate": "$0.05",
        }, f)
        f.write('\n')
    
    try:
        import respirometry
        original_path = respirometry.SORTASE_LOG
        respirometry.SORTASE_LOG = Path(f.name)
        
        result = get_cost_tracking(now=now)
        assert result["available"] is True
        assert result["current_7d"]["runs"] == 2
        assert result["current_7d"]["metered_cost_usd"] == 0.025
        assert result["previous_7d"]["runs"] == 1
        assert result["previous_7d"]["metered_cost_usd"] == 0.05
        assert "trend" in result
        assert result["trend"]["metered_cost_usd_delta"] == -0.025
        
        respirometry.SORTASE_LOG = original_path
    finally:
        Path(f.name).unlink()


if __name__ == "__main__":
    # Run tests
    test_parse_metered_cost()
    print("✓ test_parse_metered_cost passed")
    
    test_classify_cost_mode()
    print("✓ test_classify_cost_mode passed")
    
    test_summarize_cost_rows_empty()
    print("✓ test_summarize_cost_rows_empty passed")
    
    test_summarize_cost_rows_mixed()
    print("✓ test_summarize_cost_rows_mixed passed")
    
    test_get_cost_tracking_no_file()
    print("✓ test_get_cost_tracking_no_file passed")
    
    test_get_cost_tracking_with_data()
    print("✓ test_get_cost_tracking_with_data passed")
    
    print("\nAll tests passed!")
