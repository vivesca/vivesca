"""Tests for SensoryMiddleware — verify tool calls emit signals."""

from __future__ import annotations

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from metabolon.membrane import SensoryMiddleware
from metabolon.metabolism.signals import SensorySystem


def _make_server(collector: SensorySystem) -> FastMCP:
    """Minimal server with one tool and the signal middleware."""
    mcp = FastMCP("test-signals")

    @mcp.tool()
    def echo(text: str) -> str:
        """Return the input text."""
        return text

    @mcp.tool()
    def fail_tool() -> str:
        """Always raises."""
        raise RuntimeError("intentional failure")

    mcp.add_middleware(SensoryMiddleware(collector=collector))
    return mcp


@pytest.mark.asyncio
async def test_signal_emitted_on_success(tmp_path):
    """A successful tool call should produce a success signal."""
    log = tmp_path / "signals.jsonl"
    collector = SensorySystem(cortex_path=log)
    mcp = _make_server(collector)

    result = await mcp.call_tool("echo", {"text": "hello world"})
    assert result is not None

    signals = collector.recall_all()
    assert len(signals) == 1

    sig = signals[0]
    assert sig.tool == "echo"
    assert sig.outcome == "success"
    assert sig.response_latency >= 0
    assert sig.substrate_consumed >= 1
    assert sig.product_released >= 1
    assert sig.error is None


@pytest.mark.asyncio
async def test_signal_emitted_on_error(tmp_path):
    """A failed tool call should produce an error signal with the message."""
    log = tmp_path / "signals.jsonl"
    collector = SensorySystem(cortex_path=log)
    mcp = _make_server(collector)

    with pytest.raises(ToolError):
        await mcp.call_tool("fail_tool", {})

    signals = collector.recall_all()
    assert len(signals) == 1

    sig = signals[0]
    assert sig.tool == "fail_tool"
    assert sig.outcome == "error"
    assert sig.error is not None
    assert "intentional failure" in sig.error


@pytest.mark.asyncio
async def test_multiple_calls_accumulate(tmp_path):
    """Consecutive tool calls should each append a signal."""
    log = tmp_path / "signals.jsonl"
    collector = SensorySystem(cortex_path=log)
    mcp = _make_server(collector)

    for i in range(5):
        await mcp.call_tool("echo", {"text": f"call {i}"})

    signals = collector.recall_all()
    assert len(signals) == 5
    assert all(s.tool == "echo" for s in signals)
    assert all(s.outcome == "success" for s in signals)


@pytest.mark.asyncio
async def test_signal_collector_failure_does_not_break_tool(tmp_path, monkeypatch):
    """If signal collection itself fails, the tool call must still succeed."""
    log = tmp_path / "signals.jsonl"
    collector = SensorySystem(cortex_path=log)
    mcp = _make_server(collector)

    # Sabotage the collector — make append always raise.
    def broken_append(signal):
        raise OSError("disk full")

    monkeypatch.setattr(collector, "append", broken_append)

    # The tool call should still succeed despite the broken collector.
    result = await mcp.call_tool("echo", {"text": "should work"})
    assert result is not None


@pytest.mark.asyncio
async def test_create_server_includes_middleware(tmp_path):
    """assemble_organism() with a custom collector should wire the middleware."""
    from metabolon.membrane import assemble_organism

    log = tmp_path / "signals.jsonl"
    collector = SensorySystem(cortex_path=log)
    mcp = assemble_organism(signal_collector=collector)

    # The middleware list should contain our SensoryMiddleware.
    has_signal_mw = any(isinstance(mw, SensoryMiddleware) for mw in mcp.middleware)
    assert has_signal_mw, "SensoryMiddleware not found in server middleware"
