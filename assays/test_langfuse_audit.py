"""Tests for Langfuse audit tracing on MCP tool calls.

Verifies that every MCP tool call creates a Langfuse trace with correct
tool name, arguments, result, latency, and outcome metadata.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_langfuse():
    """Mock Langfuse client that captures traces."""
    client = MagicMock()
    trace = MagicMock()
    span = MagicMock()
    client.trace.return_value = trace
    trace.span.return_value = span
    return client, trace, span


class TestLangfuseAuditTracing:
    """Langfuse integration in SensoryMiddleware."""

    def test_langfuse_client_initializes_from_env(self):
        """Client reads LANGFUSE_SECRET_KEY + LANGFUSE_PUBLIC_KEY from env."""
        with patch.dict(
            "os.environ",
            {
                "LANGFUSE_SECRET_KEY": "sk-test-secret",
                "LANGFUSE_PUBLIC_KEY": "pk-test-public",
                "LANGFUSE_HOST": "https://cloud.langfuse.com",
            },
        ):
            from metabolon.audit import get_langfuse_client

            client = get_langfuse_client()
            assert client is not None

    def test_langfuse_client_returns_none_without_keys(self):
        """Gracefully returns None when Langfuse is not configured."""
        with patch.dict("os.environ", {}, clear=True):
            # Force reimport to pick up cleared env
            import importlib

            import metabolon.audit

            importlib.reload(metabolon.audit)
            client = metabolon.audit.get_langfuse_client()
            assert client is None

    def test_trace_created_on_tool_call(self, mock_langfuse):
        """A Langfuse trace is created for each tool call."""
        client, _trace, _span = mock_langfuse

        from metabolon.audit import record_tool_trace

        record_tool_trace(
            client=client,
            tool_name="rheotaxis",
            args={"query": "AI banking regulations"},
            result="Found 5 results...",
            latency_ms=342,
            outcome="success",
            error=None,
        )

        client.trace.assert_called_once()
        call_kwargs = client.trace.call_args[1]
        assert call_kwargs["name"] == "mcp-tool-call"
        assert call_kwargs["metadata"]["tool"] == "rheotaxis"

    def test_trace_includes_tool_args(self, mock_langfuse):
        """Tool arguments are recorded in the trace span."""
        client, trace, _span = mock_langfuse

        from metabolon.audit import record_tool_trace

        args = {"query": "HKMA circular", "mode": "research"}
        record_tool_trace(
            client=client,
            tool_name="rheotaxis",
            args=args,
            result="results...",
            latency_ms=200,
            outcome="success",
            error=None,
        )

        trace.span.assert_called_once()
        span_kwargs = trace.span.call_args[1]
        assert span_kwargs["input"] == args

    def test_trace_records_latency(self, mock_langfuse):
        """Latency is recorded as metadata on the span."""
        client, trace, _span = mock_langfuse

        from metabolon.audit import record_tool_trace

        record_tool_trace(
            client=client,
            tool_name="fetch",
            args={"url": "https://example.com"},
            result="page content",
            latency_ms=1500,
            outcome="success",
            error=None,
        )

        span_kwargs = trace.span.call_args[1]
        assert span_kwargs["metadata"]["latency_ms"] == 1500

    def test_trace_records_error_outcome(self, mock_langfuse):
        """Error outcomes are recorded with error details."""
        client, trace, _span = mock_langfuse

        from metabolon.audit import record_tool_trace

        record_tool_trace(
            client=client,
            tool_name="endosomal",
            args={"action": "search", "query": "test"},
            result=None,
            latency_ms=50,
            outcome="error",
            error="Gmail API quota exceeded",
        )

        span_kwargs = trace.span.call_args[1]
        assert span_kwargs["metadata"]["outcome"] == "error"
        assert "quota exceeded" in span_kwargs["metadata"]["error"]

    def test_trace_skipped_when_client_none(self):
        """No crash when Langfuse is not configured."""
        from metabolon.audit import record_tool_trace

        # Should not raise
        record_tool_trace(
            client=None,
            tool_name="rheotaxis",
            args={"query": "test"},
            result="ok",
            latency_ms=100,
            outcome="success",
            error=None,
        )

    def test_flush_called_after_trace(self, mock_langfuse):
        """Langfuse flush is called to ensure trace is sent."""
        client, _trace, _span = mock_langfuse

        from metabolon.audit import record_tool_trace

        record_tool_trace(
            client=client,
            tool_name="rheotaxis",
            args={},
            result="ok",
            latency_ms=100,
            outcome="success",
            error=None,
        )

        # flush() should be called (non-blocking background send)
        client.flush.assert_called_once()

    def test_pii_args_not_logged(self, mock_langfuse):
        """Arguments containing PII patterns are redacted."""
        client, trace, _span = mock_langfuse

        from metabolon.audit import record_tool_trace

        args = {"action": "send", "to": "alice@example.com", "body": "secret content"}
        record_tool_trace(
            client=client,
            tool_name="endosomal",
            args=args,
            result="sent",
            latency_ms=300,
            outcome="success",
            error=None,
        )

        span_kwargs = trace.span.call_args[1]
        logged_input = span_kwargs["input"]
        # Email body should be redacted, action preserved
        assert logged_input["action"] == "send"
        assert "secret content" not in json.dumps(logged_input)
