"""Tests for metabolon/server.py request logging."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import pytest


@pytest.fixture
def log_file(tmp_path):
    return tmp_path / "requests.jsonl"


def _load_jsonl(path: Path) -> list[dict]:
    entries = []
    for line in path.read_text().splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


# --- RequestLogger basics ---


def test_log_success_entry(log_file):
    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)
    logger.log(tool="navigator_search", duration_ms=42, success=True)

    entries = _load_jsonl(log_file)
    assert len(entries) == 1
    e = entries[0]
    assert e["tool"] == "navigator_search"
    assert e["duration_ms"] == 42
    assert e["success"] is True
    assert "ts" in e


def test_log_failure_entry(log_file):
    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)
    logger.log(tool="histone_query", duration_ms=200, success=False)

    entries = _load_jsonl(log_file)
    assert len(entries) == 1
    assert entries[0]["success"] is False


def test_log_appends_multiple_entries(log_file):
    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)
    logger.log(tool="a", duration_ms=10, success=True)
    logger.log(tool="b", duration_ms=20, success=False)
    logger.log(tool="c", duration_ms=30, success=True)

    entries = _load_jsonl(log_file)
    assert len(entries) == 3
    assert [e["tool"] for e in entries] == ["a", "b", "c"]


def test_log_creates_parent_dirs(tmp_path):
    from metabolon.server import RequestLogger

    nested = tmp_path / "deep" / "sub" / "requests.jsonl"
    logger = RequestLogger(nested)
    logger.log(tool="x", duration_ms=1, success=True)

    assert nested.exists()
    entries = _load_jsonl(nested)
    assert len(entries) == 1


def test_log_entry_is_valid_json(log_file):
    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)
    logger.log(tool="test", duration_ms=5, success=True)

    line = log_file.read_text().strip()
    parsed = json.loads(line)
    assert isinstance(parsed["ts"], str)
    # Verify ts is ISO-8601
    datetime.fromisoformat(parsed["ts"])


def test_log_does_not_overwrite_existing(log_file):
    from metabolon.server import RequestLogger

    log_file.write_text('{"existing": true}\n')
    logger = RequestLogger(log_file)
    logger.log(tool="new", duration_ms=1, success=True)

    entries = _load_jsonl(log_file)
    assert len(entries) == 2
    assert entries[0]["existing"] is True
    assert entries[1]["tool"] == "new"


# --- Integration: SensoryMiddleware uses RequestLogger ---


def test_middleware_writes_request_log(log_file):
    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)

    # Simulate what SensoryMiddleware does in its finally block
    logger.log(tool="demo_tool", duration_ms=123, success=True)
    logger.log(tool="failing_tool", duration_ms=456, success=False)

    entries = _load_jsonl(log_file)
    assert len(entries) == 2
    assert entries[0]["tool"] == "demo_tool"
    assert entries[0]["success"] is True
    assert entries[0]["duration_ms"] == 123
    assert entries[1]["tool"] == "failing_tool"
    assert entries[1]["success"] is False
    assert entries[1]["duration_ms"] == 456


# --- Default path ---


def test_default_log_path():
    from metabolon.server import DEFAULT_REQUEST_LOG

    assert DEFAULT_REQUEST_LOG.name == "requests.jsonl"
    assert "vivesca" in str(DEFAULT_REQUEST_LOG)


# --- Additional coverage ---


def test_log_swallows_write_error(tmp_path, caplog):
    """Write to a path inside a read-only directory should not raise."""
    import os
    import stat

    from metabolon.server import RequestLogger

    ro_dir = tmp_path / "readonly"
    ro_dir.mkdir()
    # Make directory read-only
    ro_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        logger = RequestLogger(ro_dir / "requests.jsonl")
        with caplog.at_level(logging.DEBUG, logger="metabolon.server"):
            logger.log(tool="bad", duration_ms=1, success=True)
        # Should NOT raise — exception is caught internally
        # File must not exist since write should have failed
        assert not (ro_dir / "requests.jsonl").exists()
    finally:
        # Restore permissions so tmp_path cleanup can remove it
        ro_dir.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


def test_log_requires_keyword_args(log_file):
    """log() uses *, so positional args should raise TypeError."""
    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)
    with pytest.raises(TypeError):
        logger.log("tool_name", 10, True)


def test_constructor_accepts_string_path(tmp_path):
    """Constructor wraps input with Path(), so a plain string works."""
    from metabolon.server import RequestLogger

    path_str = str(tmp_path / "requests.jsonl")
    logger = RequestLogger(path_str)
    logger.log(tool="str_path", duration_ms=5, success=True)

    entries = _load_jsonl(Path(path_str))
    assert len(entries) == 1
    assert entries[0]["tool"] == "str_path"


def test_log_entry_fields_exact(log_file):
    """Verify every expected key is present and no extras."""
    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)
    logger.log(tool="exact", duration_ms=99, success=False)

    entries = _load_jsonl(log_file)
    assert len(entries) == 1
    assert set(entries[0].keys()) == {"ts", "tool", "duration_ms", "success"}


def test_log_timestamp_is_recent_utc(log_file):
    """The 'ts' field should be a UTC datetime within the last few seconds."""
    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)
    before = datetime.now(UTC)
    logger.log(tool="ts_check", duration_ms=1, success=True)
    after = datetime.now(UTC)

    entries = _load_jsonl(log_file)
    ts = datetime.fromisoformat(entries[0]["ts"])
    assert before <= ts <= after


def test_log_zero_duration(log_file):
    """Zero duration is a valid edge case."""
    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)
    logger.log(tool="instant", duration_ms=0, success=True)

    entries = _load_jsonl(log_file)
    assert entries[0]["duration_ms"] == 0


def test_log_large_duration(log_file):
    """Large duration values should round-trip without overflow."""
    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)
    logger.log(tool="slow", duration_ms=999_999_999, success=False)

    entries = _load_jsonl(log_file)
    assert entries[0]["duration_ms"] == 999_999_999


def test_log_empty_tool_name(log_file):
    """Empty string is a valid (if unusual) tool name."""
    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)
    logger.log(tool="", duration_ms=10, success=True)

    entries = _load_jsonl(log_file)
    assert entries[0]["tool"] == ""


def test_log_entry_field_types(log_file):
    """Each field should have the expected Python type."""
    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)
    logger.log(tool="typecheck", duration_ms=42, success=True)

    e = _load_jsonl(log_file)[0]
    assert isinstance(e["ts"], str)
    assert isinstance(e["tool"], str)
    assert isinstance(e["duration_ms"], int)
    assert isinstance(e["success"], bool)


def test_timestamps_are_monotonic(log_file):
    """Successive log calls should produce non-decreasing timestamps."""
    import time

    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)
    for i in range(5):
        logger.log(tool=f"t{i}", duration_ms=i, success=True)
        time.sleep(0.01)

    timestamps = [datetime.fromisoformat(e["ts"]) for e in _load_jsonl(log_file)]
    for earlier, later in zip(timestamps, timestamps[1:]):
        assert later >= earlier


def test_constructor_with_path_object(log_file):
    """Passing a Path object (not string) should work identically."""
    from metabolon.server import RequestLogger

    logger = RequestLogger(log_file)  # already a Path from fixture
    logger.log(tool="path_obj", duration_ms=3, success=True)

    entries = _load_jsonl(log_file)
    assert len(entries) == 1
    assert entries[0]["tool"] == "path_obj"
