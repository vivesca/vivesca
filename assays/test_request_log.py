from __future__ import annotations

"""Tests for request logging — JSONL file with tool name, duration, success/fail."""


import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context(tool_name: str, arguments: dict | None = None):
    """Build a minimal MiddlewareContext-like object for on_call_tool."""
    msg = MagicMock()
    msg.name = tool_name
    msg.arguments = arguments or {}
    ctx = MagicMock()
    ctx.message = msg
    return ctx


# ---------------------------------------------------------------------------
# Tests: log_request_to_jsonl
# ---------------------------------------------------------------------------


def test_log_request_success(tmp_path: Path):
    """A successful tool call appends a JSONL line with success=True."""
    log_path = tmp_path / "requests.jsonl"

    from metabolon.membrane import log_request_to_jsonl

    log_request_to_jsonl(
        tool="weather_fetch",
        duration_ms=150,
        success=True,
        error=None,
        log_path=log_path,
    )

    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["tool"] == "weather_fetch"
    assert entry["duration_ms"] == 150
    assert entry["success"] is True
    assert entry["error"] is None
    assert "ts" in entry


def test_log_request_failure(tmp_path: Path):
    """A failed tool call appends a JSONL line with success=False and error message."""
    log_path = tmp_path / "requests.jsonl"

    from metabolon.membrane import log_request_to_jsonl

    log_request_to_jsonl(
        tool="bad_tool",
        duration_ms=42,
        success=False,
        error="connection timeout",
        log_path=log_path,
    )

    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["tool"] == "bad_tool"
    assert entry["success"] is False
    assert entry["error"] == "connection timeout"


def test_log_request_appends(tmp_path: Path):
    """Multiple calls append multiple lines (not overwrite)."""
    log_path = tmp_path / "requests.jsonl"

    from metabolon.membrane import log_request_to_jsonl

    for i in range(3):
        log_request_to_jsonl(
            tool=f"tool_{i}",
            duration_ms=10 * i,
            success=True,
            error=None,
            log_path=log_path,
        )

    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 3
    for i, line in enumerate(lines):
        entry = json.loads(line)
        assert entry["tool"] == f"tool_{i}"


def test_log_request_creates_parent_dirs(tmp_path: Path):
    """Creates parent directories if they don't exist."""
    log_path = tmp_path / "deep" / "nested" / "requests.jsonl"

    from metabolon.membrane import log_request_to_jsonl

    log_request_to_jsonl(
        tool="x",
        duration_ms=1,
        success=True,
        error=None,
        log_path=log_path,
    )

    assert log_path.exists()


def test_log_request_never_raises(tmp_path: Path):
    """If the log path is unwritable, the function must not raise."""
    from metabolon.membrane import log_request_to_jsonl

    # Use a path whose parent doesn't exist and can't be created (/dev/null/dir)
    bad_path = Path("/dev/null/impossible/requests.jsonl")
    # Should silently swallow the error
    log_request_to_jsonl(
        tool="x",
        duration_ms=1,
        success=True,
        error=None,
        log_path=bad_path,
    )


def test_log_request_has_iso_timestamp(tmp_path: Path):
    """Timestamp is a valid ISO-8601 string."""
    log_path = tmp_path / "requests.jsonl"

    from metabolon.membrane import log_request_to_jsonl

    log_request_to_jsonl(
        tool="x",
        duration_ms=1,
        success=True,
        error=None,
        log_path=log_path,
    )

    entry = json.loads(log_path.read_text().strip())
    # Should parse without error
    from datetime import datetime

    datetime.fromisoformat(entry["ts"])


# ---------------------------------------------------------------------------
# Tests: middleware integration — on_call_tool writes to JSONL
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_middleware_writes_jsonl_on_success(tmp_path: Path):
    """SensoryMiddleware.on_call_tool logs a success entry to the JSONL file."""
    log_path = tmp_path / "requests.jsonl"

    from metabolon.membrane import SensoryMiddleware

    middleware = SensoryMiddleware(request_log_path=log_path)

    ctx = _make_context("test_tool", {"city": "HK"})
    call_next = AsyncMock(return_value=MagicMock())

    await middleware.on_call_tool(ctx, call_next)

    assert log_path.exists()
    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["tool"] == "test_tool"
    assert entry["success"] is True
    assert entry["duration_ms"] >= 0


@pytest.mark.asyncio
async def test_middleware_writes_jsonl_on_failure(tmp_path: Path):
    """SensoryMiddleware.on_call_tool logs a failure entry when tool raises."""
    log_path = tmp_path / "requests.jsonl"

    from metabolon.membrane import SensoryMiddleware

    middleware = SensoryMiddleware(request_log_path=log_path)

    ctx = _make_context("failing_tool")
    call_next = AsyncMock(side_effect=ValueError("boom"))

    with pytest.raises(Exception):
        await middleware.on_call_tool(ctx, call_next)

    lines = log_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["tool"] == "failing_tool"
    assert entry["success"] is False
    assert "boom" in entry["error"]
