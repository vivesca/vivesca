"""Tests for metabolon/server.py request logging."""

from __future__ import annotations

import json
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
