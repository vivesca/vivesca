from __future__ import annotations

"""Tests for metabolon/enzymes/noesis — Perplexity-powered AI search tool."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest


# ── import the module under test ──────────────────────────────────────
# Import at module level so every test shares the same object.
from metabolon.enzymes.noesis import (
    noesis,
    noesis_search_log,
    BINARY,
    _RESEARCH_TIMEOUT,
)


# ── constants ─────────────────────────────────────────────────────────

class TestConstants:
    def test_binary_path(self):
        assert BINARY == "~/.cargo/bin/noesis"

    def test_research_timeout(self):
        assert _RESEARCH_TIMEOUT == 300


# ── noesis tool ───────────────────────────────────────────────────────

class TestNoesisTool:
    """Unit tests for the noesis() MCP tool function."""

    @patch("metabolon.enzymes.noesis.run_cli")
    def test_search_action(self, mock_run_cli):
        mock_run_cli.return_value = "sonar result"
        result = noesis(action="search", query="what is MCP?")
        mock_run_cli.assert_called_once_with(BINARY, ["search", "what is MCP?"])
        assert result == "sonar result"

    @patch("metabolon.enzymes.noesis.run_cli")
    def test_ask_action(self, mock_run_cli):
        mock_run_cli.return_value = "sonar-pro result"
        result = noesis(action="ask", query="explain fastmcp")
        mock_run_cli.assert_called_once_with(BINARY, ["ask", "explain fastmcp"])
        assert result == "sonar-pro result"

    @patch("metabolon.enzymes.noesis.run_cli")
    def test_research_action(self, mock_run_cli):
        mock_run_cli.return_value = "deep research result"
        result = noesis(action="research", query="survey of LLM agents")
        mock_run_cli.assert_called_once_with(
            BINARY, ["research", "--save", "survey of LLM agents"],
            timeout=_RESEARCH_TIMEOUT,
        )
        assert result == "deep research result"

    def test_unknown_action(self):
        result = noesis(action="summarize", query="ignored")
        assert "Unknown action 'summarize'" in result
        assert "search" in result
        assert "ask" in result
        assert "research" in result

    @patch("metabolon.enzymes.noesis.run_cli")
    def test_default_query_is_empty(self, mock_run_cli):
        mock_run_cli.return_value = "ok"
        noesis(action="search")
        mock_run_cli.assert_called_once_with(BINARY, ["search", ""])

    @patch("metabolon.enzymes.noesis.run_cli")
    def test_run_cli_error_propagates(self, mock_run_cli):
        mock_run_cli.side_effect = ValueError("Binary not found")
        with pytest.raises(ValueError, match="Binary not found"):
            noesis(action="search", query="test")


# ── noesis_search_log resource ────────────────────────────────────────

class TestNoesisSearchLog:
    """Unit tests for the noesis_search_log() resource function."""

    @patch("metabolon.enzymes.noesis.subprocess.run")
    def test_returns_full_output_when_fewer_than_10_lines(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="line1\nline2\nline3",
            stderr="",
        )
        result = noesis_search_log()
        assert result == "line1\nline2\nline3"
        mock_run.assert_called_once()
        cmd_args = mock_run.call_args
        assert cmd_args[0][0][-1] == "log"

    @patch("metabolon.enzymes.noesis.subprocess.run")
    def test_returns_last_10_lines_when_more(self, mock_run):
        lines = [f"entry{i}" for i in range(15)]
        mock_run.return_value = MagicMock(
            stdout="\n".join(lines),
            stderr="",
        )
        result = noesis_search_log()
        result_lines = result.split("\n")
        assert len(result_lines) == 10
        assert result_lines[0] == "entry5"
        assert result_lines[-1] == "entry14"

    @patch("metabolon.enzymes.noesis.subprocess.run")
    def test_empty_stdout_returns_empty_string(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", stderr="")
        result = noesis_search_log()
        assert result == ""

    @patch("metabolon.enzymes.noesis.subprocess.run")
    def test_called_process_error_raises_value_error(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["noesis", "log"], stderr="something broke"
        )
        with pytest.raises(ValueError, match="noesis log error"):
            noesis_search_log()

    @patch("metabolon.enzymes.noesis.subprocess.run")
    def test_called_process_error_no_stderr(self, mock_run):
        err = subprocess.CalledProcessError(
            returncode=1, cmd=["noesis", "log"], stderr=""
        )
        mock_run.side_effect = err
        with pytest.raises(ValueError, match="noesis log error"):
            noesis_search_log()

    @patch("metabolon.enzymes.noesis.subprocess.run")
    def test_subprocess_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["noesis", "log"], timeout=10)
        # noesis_search_log doesn't catch TimeoutExpired, so it propagates
        with pytest.raises(subprocess.TimeoutExpired):
            noesis_search_log()

    @patch("metabolon.enzymes.noesis.subprocess.run")
    def test_exactly_10_lines_returns_all(self, mock_run):
        """Boundary: exactly 10 lines should not slice."""
        lines = [f"entry{i}" for i in range(10)]
        mock_run.return_value = MagicMock(
            stdout="\n".join(lines),
            stderr="",
        )
        result = noesis_search_log()
        assert result == "\n".join(lines)

    @patch("metabolon.enzymes.noesis.subprocess.run")
    def test_subprocess_called_with_check_and_timeout(self, mock_run):
        """Verify subprocess.run is invoked with check=True and timeout=10."""
        mock_run.return_value = MagicMock(stdout="line1", stderr="")
        noesis_search_log()
        _, kwargs = mock_run.call_args
        assert kwargs["check"] is True
        assert kwargs["timeout"] == 10
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True

    @patch("metabolon.enzymes.noesis.subprocess.run")
    def test_binary_path_expanded(self, mock_run):
        """Verify the binary path goes through expanduser."""
        import os

        mock_run.return_value = MagicMock(stdout="ok", stderr="")
        noesis_search_log()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == os.path.expanduser(BINARY)

    @patch("metabolon.enzymes.noesis.subprocess.run")
    def test_called_process_error_uses_str_when_no_stderr(self, mock_run):
        """CalledProcessError with empty stderr falls back to str(e)."""
        err = subprocess.CalledProcessError(
            returncode=1, cmd=["noesis", "log"], stderr=None
        )
        mock_run.side_effect = err
        with pytest.raises(ValueError, match="noesis log error"):
            noesis_search_log()
