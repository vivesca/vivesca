"""Tests for metabolon.enzymes.noesis — tool/resource registration and edge cases."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.noesis import (
    BINARY,
    _RESEARCH_TIMEOUT,
    noesis,
    noesis_search_log,
)


# ── decorator metadata ─────────────────────────────────────────────────

class TestToolMetadata:
    """Verify the @tool decorator applied correct metadata."""

    def test_tool_name(self):
        assert noesis.__fastmcp__.name == "noesis"

    def test_tool_description_contains_actions(self):
        desc = noesis.__fastmcp__.description
        assert "search" in desc
        assert "ask" in desc
        assert "research" in desc

    def test_tool_annotations_read_only_false(self):
        assert noesis.__fastmcp__.annotations.readOnlyHint is False


# ── function signature and defaults ────────────────────────────────────

class TestSignature:
    """Check parameter defaults and types."""

    def test_query_default_is_empty_string(self):
        import inspect

        sig = inspect.signature(noesis)
        assert sig.parameters["query"].default == ""

    def test_noesis_is_callable(self):
        assert callable(noesis)

    def test_noesis_return_type_annotation(self):
        import inspect

        ann = inspect.signature(noesis).return_annotation
        # from __future__ import annotations turns it into 'str'
        assert ann == "str" or ann is str


# ── edge-case inputs ───────────────────────────────────────────────────

class TestEdgeCases:

    @patch("metabolon.enzymes.noesis.run_cli")
    def test_query_with_special_characters(self, mock_run):
        mock_run.return_value = "ok"
        result = noesis(action="search", query='test "quotes" & <tags>')
        mock_run.assert_called_once_with(
            BINARY, ["search", 'test "quotes" & <tags>']
        )
        assert result == "ok"

    @patch("metabolon.enzymes.noesis.run_cli")
    def test_empty_query_search(self, mock_run):
        mock_run.return_value = "empty result"
        result = noesis(action="search", query="")
        assert result == "empty result"

    @patch("metabolon.enzymes.noesis.run_cli")
    def test_unicode_query(self, mock_run):
        mock_run.return_value = "unicode ok"
        result = noesis(action="ask", query="日本語テスト")
        mock_run.assert_called_once_with(BINARY, ["ask", "日本語テスト"])
        assert result == "unicode ok"

    def test_unknown_action_returns_str(self):
        result = noesis(action="invalid", query="x")
        assert isinstance(result, str)

    def test_unknown_action_mentions_all_valid_actions(self):
        result = noesis(action="bogus")
        for valid in ("search", "ask", "research"):
            assert valid in result

    @patch("metabolon.enzymes.noesis.run_cli")
    def test_research_passes_save_flag(self, mock_run):
        mock_run.return_value = "saved"
        noesis(action="research", query="deep topic")
        args, kwargs = mock_run.call_args
        assert "--save" in args[1]
        assert kwargs["timeout"] == _RESEARCH_TIMEOUT

    @patch("metabolon.enzymes.noesis.run_cli")
    def test_search_and_ask_use_default_timeout(self, mock_run):
        """search and ask should NOT pass a custom timeout."""
        mock_run.return_value = "ok"
        noesis(action="search", query="t")
        _, kwargs = mock_run.call_args
        assert "timeout" not in kwargs
        mock_run.reset_mock()
        noesis(action="ask", query="t")
        _, kwargs = mock_run.call_args
        assert "timeout" not in kwargs


# ── search-log resource edge cases ─────────────────────────────────────

class TestSearchLogEdgeCases:

    @patch("metabolon.enzymes.noesis.subprocess.run")
    def test_single_line_output(self, mock_run):
        mock_run.return_value = MagicMock(stdout="only line", stderr="")
        assert noesis_search_log() == "only line"

    @patch("metabolon.enzymes.noesis.subprocess.run")
    def test_log_command_ends_with_log(self, mock_run):
        mock_run.return_value = MagicMock(stdout="x", stderr="")
        noesis_search_log()
        cmd = mock_run.call_args[0][0]
        assert cmd[-1] == "log"
