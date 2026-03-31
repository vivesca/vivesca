#!/usr/bin/env python3
"""Tests for respirometry effector — mocks all external file I/O and API calls."""

from __future__ import annotations

import json
import pytest
import subprocess
from unittest.mock import MagicMock, patch
from datetime import UTC, datetime, timedelta, date
from pathlib import Path

# Execute the respirometry file directly
respirometry_code = Path("/home/terry/germline/effectors/respirometry").read_text()
namespace = {}
exec(respirometry_code, namespace)

# Extract all the functions/globals from the namespace
respirometry = type('respirometry_module', (), {})()
for key, value in namespace.items():
    if not key.startswith('__'):
        setattr(respirometry, key, value)

# ---------------------------------------------------------------------------
# Test formatting
# ---------------------------------------------------------------------------

def test_format_age_seconds():
    """Test format_age formats seconds correctly."""
    assert respirometry.format_age(30) == "30s ago"
    assert respirometry.format_age(59) == "59s ago"

def test_format_age_minutes():
    """Test format_age formats minutes correctly."""
    assert respirometry.format_age(60) == "1m ago"
    assert respirometry.format_age(3599) == "59m ago"

def test_format_age_hours():
    """Test format_age formats hours correctly."""
    assert respirometry.format_age(3600) == "1h ago"
    assert respirometry.format_age(86399) == "23h ago"

def test_format_age_days():
    """Test format_age formats days correctly."""
    assert respirometry.format_age(86400) == "1d ago"
    assert respirometry.format_age(172800) == "2d ago"

# ---------------------------------------------------------------------------
# Test parsing and normalization
# ---------------------------------------------------------------------------

def test_parse_metered_cost_valid():
    """Test _parse_metered_cost correctly parses valid cost strings."""
    assert respirometry._parse_metered_cost("$0.00") == 0.0
    assert respirometry._parse_metered_cost("$10.50") == 10.50
    assert respirometry._parse_metered_cost("$5") == 5.0

def test_parse_metered_cost_invalid():
    """Test _parse_metered_cost returns None for invalid cost strings."""
    assert respirometry._parse_metered_cost("") is None
    assert respirometry._parse_metered_cost("flat-rate") is None
    assert respirometry._parse_metered_cost("10.50") is None
    assert respirometry._parse_metered_cost("USD 10") is None

def test_normalise_pct_decimal():
    """Test _normalise_pct converts 0-1 decimal to percentage."""
    assert respirometry._normalise_pct(0.5) == 50.0
    assert respirometry._normalise_pct(1.0) == 100.0
    assert respirometry._normalise_pct(0.0) == 0.0

def test_normalise_pct_already_percentage():
    """Test _normalise_pct leaves percentage values as-is."""
    assert respirometry._normalise_pct(50.0) == 50.0
    assert respirometry._normalise_pct(100) == 100

def test_normalise_pct_invalid():
    """Test _normalise_pct returns -1 for invalid values."""
    assert respirometry._normalise_pct(None) == -1.0
    assert respirometry._normalise_pct("not a number") == -1.0

def test_normalise_cached_new_format():
    """Test _normalise_cached handles the new format with metrics key."""
    entry = {
        "ts": "2026-03-31T10:00:00Z",
        "metrics": {
            "seven_day": {"utilization": 0.5},
            "seven_day_sonnet": {"utilization": 0.3}
        }
    }
    result = respirometry._normalise_cached(entry)
    assert result["seven_day"]["utilization"] == 0.5
    assert result["seven_day_sonnet"]["utilization"] == 0.3

def test_normalise_cached_old_format():
    """Test _normalise_cached handles the old flat format."""
    entry = {
        "weekly_pct": 50,
        "sonnet_pct": 30
    }
    result = respirometry._normalise_cached(entry)
    assert result["seven_day"]["utilization"] == 50
    assert result["seven_day_sonnet"]["utilization"] == 30

# ---------------------------------------------------------------------------
# Test cost classification
# ---------------------------------------------------------------------------

def test_classify_cost_mode_flat_rate_tool():
    """Test _classify_cost_mode classifies known flat-rate tools correctly."""
    for tool in respirometry.FLAT_RATE_TOOLS:
        row = {"tool": tool, "cost_estimate": "$0.00"}
        assert respirometry._classify_cost_mode(row) == "flat-rate"

def test_classify_cost_mode_flat_rate_in_estimate():
    """Test _classify_cost_mode detects 'flat-rate' in cost estimate."""
    row = {"tool": "custom", "cost_estimate": "flat-rate (goose)"}
    assert respirometry._classify_cost_mode(row) == "flat-rate"

def test_classify_cost_mode_matched_metered():
    """Test _classify_cost_mode classifies metered cost strings correctly."""
    row = {"tool": "opus", "cost_estimate": "$0.1234"}
    assert respirometry._classify_cost_mode(row) == "metered"

def test_classify_cost_mode_metered_by_tool_present():
    """Test _classify_cost_mode classifies as metered if tool is present but no cost pattern."""
    row = {"tool": "custom-model", "cost_estimate": ""}
    assert respirometry._classify_cost_mode(row) == "metered"

def test_classify_cost_mode_unknown():
    """Test _classify_cost_mode returns unknown when no tool or identifiable pattern."""
    row = {"tool": "", "cost_estimate": ""}
    assert respirometry._classify_cost_mode(row) == "unknown"

# ---------------------------------------------------------------------------
# Test reading cost rows
# ---------------------------------------------------------------------------

def test_read_cost_rows_file_missing():
    """Test _read_cost_rows returns empty list when file doesn't exist."""
    with patch.object(Path, 'exists', return_value=False):
        result = respirometry._read_cost_rows(Path("/nonexistent"))
        assert result == []

def test_read_cost_rows_parses_valid():
    """Test _read_cost_rows correctly parses valid JSON lines."""
    now = datetime.now(UTC).isoformat()
    lines = [
        json.dumps({"timestamp": now, "tool": "goose", "duration_s": 120}),
        json.dumps({"timestamp": now, "tool": "opus", "duration_s": 300}),
        "not valid json",
        json.dumps({"timestamp": "invalid-iso", "tool": "bad"}),
        json.dumps({"not-timestamp": "oops"}),
        "",
    ]
    mock_content = "\n".join(lines)

    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=mock_content):
            result = respirometry._read_cost_rows(Path("/fake"))
            assert len(result) == 2
            assert result[0]["tool"] == "goose"
            assert "_parsed_timestamp" in result[0]

# ---------------------------------------------------------------------------
# Test cost summarization
# ---------------------------------------------------------------------------

def test_summarize_cost_rows_empty():
    """Test _summarize_cost_rows with empty input returns zeros."""
    result = respirometry._summarize_cost_rows([])
    assert result["runs"] == 0
    assert result["metered_cost_usd"] == 0.0
    assert result["flat_rate_runs"] == 0
    assert result["metered_runs"] == 0

def test_summarize_cost_rows_mixed():
    """Test _summarize_costrows correctly classifies mixed runs."""
    now = datetime.now(UTC)
    rows = [
        {"timestamp": now.isoformat(), "_parsed_timestamp": now,
         "tool": "goose", "duration_s": 3600, "tasks": 5, "success": True,
         "cost_estimate": "flat-rate"},
        {"timestamp": now.isoformat(), "_parsed_timestamp": now,
         "tool": "opus", "duration_s": 1800, "tasks": 3, "success": True,
         "cost_estimate": "$0.1234"},
        {"timestamp": now.isoformat(), "_parsed_timestamp": now,
         "tool": "sonnet", "duration_s": 900, "tasks": 2, "success": True,
         "cost_estimate": "$0.0456"},
    ]
    result = respirometry._summarize_cost_rows(rows)
    assert result["runs"] == 3
    assert result["flat_rate_runs"] == 1
    assert result["metered_runs"] == 2
    assert result["metered_cost_usd"] == pytest.approx(0.1690)
    assert result["duration_hours"] == pytest.approx((3600 + 1800 + 900) / 3600)
    assert result["tasks"] == 10
    assert result["flat_rate_pct"] == pytest.approx(33.3)
    assert result["metered_pct"] == pytest.approx(66.7)
    assert "goose" in result["flat_rate_tools"]
    assert "opus" in result["metered_tools"]
    assert "sonnet" in result["metered_tools"]

# ---------------------------------------------------------------------------
# Test budget classification
# ---------------------------------------------------------------------------

def test_get_budget_interactive_green():
    """Test get_budget returns green under 50% interactive mode."""
    mock_usage = {
        "seven_day": {"utilization": 0.3},
        "seven_day_sonnet": {"utilization": 0.2},
    }
    namespace['get_usage'] = lambda: mock_usage
    assert namespace['get_budget']("interactive") == "green"

def test_get_budget_interactive_yellow():
    """Test get_budget returns yellow between 50-70% interactive mode."""
    mock_usage = {
        "seven_day": {"utilization": 0.6},
        "seven_day_sonnet": {"utilization": 0.2},
    }
    namespace['get_usage'] = lambda: mock_usage
    assert namespace['get_budget']("interactive") == "yellow"

def test_get_budget_interactive_red():
    """Test get_budget returns red over 70% interactive mode."""
    mock_usage = {
        "seven_day": {"utilization": 0.8},
        "seven_day_sonnet": {"utilization": 0.2},
    }
    namespace['get_usage'] = lambda: mock_usage
    assert namespace['get_budget']("interactive") == "red"

def test_get_budget_overnight_green():
    """Test get_budget uses different thresholds for overnight."""
    mock_usage = {
        "seven_day": {"utilization": 90},
        "seven_day_sonnet": {"utilization": 20},
    }
    namespace['get_usage'] = lambda: mock_usage
    assert namespace['get_budget']("overnight") == "green"

def test_get_budget_overnight_yellow():
    """Test get_budget returns yellow 95-98% for overnight."""
    mock_usage = {
        "seven_day": {"utilization": 96},
        "seven_day_sonnet": {"utilization": 20},
    }
    namespace['get_usage'] = lambda: mock_usage
    assert namespace['get_budget']("overnight") == "yellow"

def test_get_budget_overnight_red():
    """Test get_budget returns red >=98% for overnight."""
    mock_usage = {
        "seven_day": {"utilization": 98},
        "seven_day_sonnet": {"utilization": 20},
    }
    namespace['get_usage'] = lambda: mock_usage
    assert namespace['get_budget']("overnight") == "red"

def test_get_budget_unknown_on_error():
    """Test get_budget returns unknown when usage has error."""
    mock_usage = {"error": "no data"}
    namespace['get_usage'] = lambda: mock_usage
    assert namespace['get_budget']() == "unknown"

# ---------------------------------------------------------------------------
# Test window calculation
# ---------------------------------------------------------------------------

def test_snapshot_window():
    """Test _snapshot_window returns correct 7-day window."""
    ref = datetime(2026, 3, 31, 12, 0, 0, tzinfo=UTC)
    start, end = respirometry._snapshot_window(ref)
    assert start == date(2026, 3, 24)
    assert end == date(2026, 3, 31)

# ---------------------------------------------------------------------------
# Test cache reading
# ---------------------------------------------------------------------------

def test_read_last_line_file_missing():
    """Test _read_last_line returns None when file missing."""
    with patch.object(Path, 'exists', return_value=False):
        assert respirometry._read_last_line(Path("/missing")) is None

def test_read_last_line_empty_file():
    """Test _read_last_line returns None when file is empty."""
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=""):
            assert respirometry._read_last_line(Path("/empty")) is None

def test_read_last_line_single_line():
    """Test _read_last_line correctly reads a single JSON line."""
    test_data = {"test": "value"}
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value=json.dumps(test_data) + "\n"):
            result = respirometry._read_last_line(Path("/test"))
            assert result == test_data

def test_read_last_line_multiple_lines():
    """Test _read_last_line returns last of multiple lines."""
    lines = [
        json.dumps({"line": 1}),
        json.dumps({"line": 2}),
        json.dumps({"line": 3}),
    ]
    with patch.object(Path, 'exists', return_value=True):
        with patch.object(Path, 'read_text', return_value="\n".join(lines)):
            result = respirometry._read_last_line(Path("/test"))
            assert result["line"] == 3

# ---------------------------------------------------------------------------
# Test derive session stats
# ---------------------------------------------------------------------------

def test_derive_session_stats_empty():
    """Test _derive_session_stats returns zero when no data."""
    with patch.object(Path, 'exists', return_value=False):
        sessions, goose = respirometry._derive_session_stats()
        assert sessions == 0
        assert goose == 0

# ---------------------------------------------------------------------------
# Test subprocess execution via main (smoke test)
# ---------------------------------------------------------------------------

def test_main_help():
    """Test that respirometry --help exits successfully."""
    result = subprocess.run(
        ["/home/terry/germline/effectors/respirometry", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Claude Code" in result.stdout

def test_main_budget_flag_works():
    """Test that --budget outputs one of the expected values."""
    # Since there's no credentials in test environment, it should output "unknown"
    result = subprocess.run(
        ["/home/terry/germline/effectors/respirometry", "--budget"],
        capture_output=True,
        text=True
    )
    # The command succeeds even when it's unknown
    assert result.returncode == 0
    output = result.stdout.strip()
    assert output in ["green", "yellow", "red", "unknown"]

def test_command_trend_no_file():
    """Test cmd_trend handles missing history file gracefully."""
    with patch.object(Path, 'exists', return_value=False):
        # Should just print message and not crash
        respirometry.cmd_trend()
        # If we got here, it didn't crash, so test passes

