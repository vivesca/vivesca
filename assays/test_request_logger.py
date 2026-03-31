from __future__ import annotations

"""Tests for metabolon.server.RequestLogger — JSONL request log persistence."""

import json
from pathlib import Path

import pytest

from metabolon.server import DEFAULT_REQUEST_LOG, RequestLogger


# ── helpers ───────────────────────────────────────────────────────────

@pytest.fixture
def log_path(tmp_path: Path) -> Path:
    """Return a unique JSONL path inside pytest's tmpdir."""
    return tmp_path / "requests.jsonl"


def _read_lines(path: Path) -> list[dict]:
    """Parse every non-empty line of a JSONL file into a dict."""
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# ── construction ──────────────────────────────────────────────────────

def test_default_path_is_under_vivesca_share():
    """RequestLogger() defaults to ~/.local/share/vivesca/requests.jsonl."""
    logger = RequestLogger()
    assert logger._path == DEFAULT_REQUEST_LOG
    assert "vivesca" in str(DEFAULT_REQUEST_LOG)


def test_custom_path_accepted(log_path: Path):
    """RequestLogger(path=...) stores the given path."""
    logger = RequestLogger(log_path)
    assert logger._path == log_path


# ── log() basic behaviour ────────────────────────────────────────────

def test_log_creates_file_and_parent_dirs(tmp_path: Path):
    """log() creates intermediate directories and the JSONL file."""
    deep = tmp_path / "a" / "b" / "c" / "req.jsonl"
    logger = RequestLogger(deep)
    logger.log(tool="t1", duration_ms=42, success=True)

    assert deep.exists()
    entries = _read_lines(deep)
    assert len(entries) == 1
    assert entries[0]["tool"] == "t1"
    assert entries[0]["duration_ms"] == 42
    assert entries[0]["success"] is True


def test_log_appends_multiple_entries(log_path: Path):
    """Repeated log() calls append lines; they don't overwrite."""
    logger = RequestLogger(log_path)
    logger.log(tool="alpha", duration_ms=10, success=True)
    logger.log(tool="beta", duration_ms=20, success=False)
    logger.log(tool="gamma", duration_ms=30, success=True)

    entries = _read_lines(log_path)
    assert len(entries) == 3
    assert [e["tool"] for e in entries] == ["alpha", "beta", "gamma"]
    assert entries[1]["success"] is False


def test_log_entry_has_iso_timestamp(log_path: Path):
    """Each entry contains a valid ISO-8601 timestamp."""
    from datetime import datetime

    logger = RequestLogger(log_path)
    logger.log(tool="ts_test", duration_ms=1, success=True)

    entry = _read_lines(log_path)[0]
    # Should parse without error
    dt = datetime.fromisoformat(entry["ts"])
    assert dt.tzinfo is not None  # timezone-aware


def test_log_entry_schema(log_path: Path):
    """Each JSONL line has exactly the expected keys."""
    logger = RequestLogger(log_path)
    logger.log(tool="schema_check", duration_ms=99, success=False)

    entry = _read_lines(log_path)[0]
    expected_keys = {"ts", "tool", "duration_ms", "success"}
    assert set(entry.keys()) == expected_keys
    assert isinstance(entry["tool"], str)
    assert isinstance(entry["duration_ms"], int)
    assert isinstance(entry["success"], bool)


# ── edge cases ───────────────────────────────────────────────────────

def test_log_with_zero_duration(log_path: Path):
    """duration_ms=0 is a valid value (e.g. instant cache hit)."""
    logger = RequestLogger(log_path)
    logger.log(tool="cache_hit", duration_ms=0, success=True)

    entry = _read_lines(log_path)[0]
    assert entry["duration_ms"] == 0


def test_log_with_large_duration(log_path: Path):
    """Very large durations (slow upstream) are stored faithfully."""
    logger = RequestLogger(log_path)
    logger.log(tool="slow_call", duration_ms=300_000, success=True)

    entry = _read_lines(log_path)[0]
    assert entry["duration_ms"] == 300_000


def test_log_does_not_raise_on_permission_error(tmp_path: Path, caplog):
    """log() swallows write failures silently (logged at DEBUG)."""
    import logging

    read_only_dir = tmp_path / "readonly"
    read_only_dir.mkdir()
    log_file = read_only_dir / "req.jsonl"
    logger = RequestLogger(log_file)

    # Make directory read-only after creation
    read_only_dir.chmod(0o444)
    try:
        # Should NOT raise — exceptions are caught internally
        logger.log(tool="failing", duration_ms=1, success=True)
    finally:
        # Restore permissions so tmp_path cleanup can remove the dir
        read_only_dir.chmod(0o755)


def test_log_survives_concurrent_appends(log_path: Path):
    """Multiple loggers writing to the same file don't lose lines."""
    import concurrent.futures

    n = 50
    loggers = [RequestLogger(log_path) for _ in range(n)]

    def write_one(idx: int) -> None:
        loggers[idx].log(tool=f"concurrent_{idx}", duration_ms=idx, success=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(write_one, range(n)))

    entries = _read_lines(log_path)
    # We expect exactly n entries (appends are atomic for small writes)
    assert len(entries) == n
    tools = {e["tool"] for e in entries}
    assert tools == {f"concurrent_{i}" for i in range(n)}
