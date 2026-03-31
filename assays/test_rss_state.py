"""Tests for endocytosis_rss/state.py - state management and refractory periods."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from metabolon.organelles.endocytosis_rss.state import (
    lockfile,
    restore_state,
    persist_state,
    refractory_elapsed,
    _CADENCE_DAYS,
)


def test_cadence_days_values():
    """Test _CADENCE_DAYS contains expected cadence mappings."""
    assert _CADENCE_DAYS["daily"] == 0
    assert _CADENCE_DAYS["weekly"] == 5
    assert _CADENCE_DAYS["biweekly"] == 10
    assert _CADENCE_DAYS["monthly"] == 25


def test_restore_state_nonexistent_file(tmp_path):
    """Test restore_state returns empty dict for nonexistent file."""
    result = restore_state(tmp_path / "nonexistent.json")
    assert result == {}


def test_restore_state_valid_file(tmp_path):
    """Test restore_state reads valid JSON state."""
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({"source1": "2024-01-15", "source2": "2024-01-10"}))
    
    result = restore_state(state_path)
    assert result["source1"] == "2024-01-15"
    assert result["source2"] == "2024-01-10"


def test_restore_state_invalid_json(tmp_path):
    """Test restore_state returns empty dict for invalid JSON."""
    state_path = tmp_path / "state.json"
    state_path.write_text("not valid json")
    
    result = restore_state(state_path)
    assert result == {}


def test_restore_state_non_dict(tmp_path):
    """Test restore_state returns empty dict if JSON is not a dict."""
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(["list", "not", "dict"]))
    
    result = restore_state(state_path)
    assert result == {}


def test_restore_state_filters_non_string_values(tmp_path):
    """Test restore_state only keeps string values."""
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({"str_key": "str_val", "num_key": 42, None: "val"}))
    
    result = restore_state(state_path)
    assert "str_key" in result
    assert "num_key" not in result


def test_persist_state_creates_file(tmp_path):
    """Test persist_state writes state to file."""
    state_path = tmp_path / "state.json"
    state = {"source1": "2024-01-15"}
    
    persist_state(state_path, state)
    assert state_path.exists()
    
    loaded = json.loads(state_path.read_text())
    assert loaded["source1"] == "2024-01-15"


def test_persist_state_creates_parent_dirs(tmp_path):
    """Test persist_state creates parent directories."""
    state_path = tmp_path / "nested" / "dir" / "state.json"
    
    persist_state(state_path, {"key": "val"})
    assert state_path.exists()


def test_refractory_elapsed_no_last_seen():
    """Test refractory_elapsed returns True when no last_seen."""
    assert refractory_elapsed({}, "source", "daily") is True


def test_refractory_elapsed_daily_cadence():
    """Test refractory_elapsed for daily cadence (0 days threshold)."""
    now = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)

    # Daily cadence has 0 days threshold, so any past time returns True
    state = {"source": "2024-01-15T10:00:00"}  # Same day, 2 hours ago
    assert refractory_elapsed(state, "source", "daily", now=now) is True

    # No last_seen means should fetch
    assert refractory_elapsed({}, "source", "daily", now=now) is True


def test_refractory_elapsed_weekly_cadence():
    """Test refractory_elapsed for weekly cadence (5 days)."""
    now = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)
    
    # 3 days ago - should be False (needs 5)
    state = {"source": "2024-01-12T00:00:00"}
    assert refractory_elapsed(state, "source", "weekly", now=now) is False
    
    # 6 days ago - should be True
    state = {"source": "2024-01-09T00:00:00"}
    assert refractory_elapsed(state, "source", "weekly", now=now) is True


def test_refractory_elapsed_invalid_date():
    """Test refractory_elapsed returns True for invalid date string."""
    state = {"source": "not-a-date"}
    assert refractory_elapsed(state, "source", "daily") is True


def test_refractory_elapsed_downregulation_high_noise():
    """Test refractory_elapsed extends period for low signal ratio (< 0.2)."""
    now = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)
    
    # Weekly = 5 days, +7 for high noise = 12 days
    state = {"source": "2024-01-10T00:00:00"}  # 5 days ago
    assert refractory_elapsed(state, "source", "weekly", now=now, signal_ratio=0.1) is False
    
    state = {"source": "2024-01-02T00:00:00"}  # 13 days ago
    assert refractory_elapsed(state, "source", "weekly", now=now, signal_ratio=0.1) is True


def test_refractory_elapsed_downregulation_moderate_noise():
    """Test refractory_elapsed extends period for moderate noise (0.2-0.5)."""
    now = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)
    
    # Weekly = 5 days, +2 for moderate noise = 7 days
    state = {"source": "2024-01-10T00:00:00"}  # 5 days ago
    assert refractory_elapsed(state, "source", "weekly", now=now, signal_ratio=0.3) is False
    
    state = {"source": "2024-01-07T00:00:00"}  # 8 days ago
    assert refractory_elapsed(state, "source", "weekly", now=now, signal_ratio=0.3) is True


def test_refractory_elapsed_high_signal_no_extension():
    """Test refractory_elapsed uses normal cadence for high signal."""
    now = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)
    
    # Weekly = 5 days, no extension for high signal
    state = {"source": "2024-01-10T00:00:00"}  # 5 days ago
    assert refractory_elapsed(state, "source", "weekly", now=now, signal_ratio=0.8) is True


def test_refractory_elapsed_handles_naive_datetime():
    """Test refractory_elapsed handles naive datetime by adding UTC."""
    now = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)
    state = {"source": "2024-01-10T00:00:00"}  # naive
    
    # Should not raise
    result = refractory_elapsed(state, "source", "weekly", now=now)
    assert isinstance(result, bool)


def test_lockfile_prevents_concurrent(tmp_path):
    """Test lockfile creates exclusive lock."""
    import fcntl
    
    lock_path = tmp_path / "state.json"
    
    with lockfile(lock_path):
        lock_file = lock_path.with_suffix(".lock")
        assert lock_file.exists()


def test_lockfile_releases_on_exit(tmp_path):
    """Test lockfile releases lock after context exit."""
    lock_path = tmp_path / "state.json"
    
    with lockfile(lock_path):
        pass
    
    lock_file = lock_path.with_suffix(".lock")
    # Lock file should be removed
    assert not lock_file.exists()
