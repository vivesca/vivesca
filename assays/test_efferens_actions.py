from __future__ import annotations

"""Tests for metabolon/enzymes/efferens.py — MCP tool wrapper.

Mocks run_cli (the subprocess call) and verifies argument forwarding,
defaults, return values, and error propagation.
"""

from pathlib import Path
from unittest.mock import call, patch

import pytest

from metabolon.enzymes.efferens import BINARY, efferens


# ── BINARY constant ──────────────────────────────────────────────────────────


class TestBinaryPath:
    def test_binary_is_under_home_local_bin(self):
        assert BINARY.endswith("/.local/bin/efferens")

    def test_binary_uses_home(self):
        assert Path.home().as_posix() in BINARY


# ── action="list" ────────────────────────────────────────────────────────────


class TestListAction:
    @patch("metabolon.enzymes.efferens.run_cli")
    def test_basic_list(self, mock_run):
        mock_run.return_value = "No messages"
        result = efferens(action="list")
        assert result == "No messages"
        mock_run.assert_called_once_with(BINARY, ["list", "--to", "terry"])

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_list_with_custom_to(self, mock_run):
        mock_run.return_value = "1 message(s)"
        result = efferens(action="list", to="bot")
        assert result == "1 message(s)"
        mock_run.assert_called_once_with(BINARY, ["list", "--to", "bot"])

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_list_returns_run_cli_output_verbatim(self, mock_run):
        mock_run.return_value = "Board empty"
        assert efferens(action="list") == "Board empty"

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_list_empty_to_still_passes_flag(self, mock_run):
        mock_run.return_value = ""
        efferens(action="list", to="")
        # Empty string is falsy, so --to should NOT be appended
        mock_run.assert_called_once_with(BINARY, ["list"])


# ── action="post" ────────────────────────────────────────────────────────────


class TestPostAction:
    @patch("metabolon.enzymes.efferens.run_cli")
    def test_post_minimal(self, mock_run):
        mock_run.return_value = "Posted: 2026-01-01-msg.md"
        result = efferens(
            action="post",
            message="hello",
            sender="bot",
        )
        assert "Posted" in result
        mock_run.assert_called_once_with(
            BINARY,
            ["post", "hello", "--from", "bot", "--to", "terry", "--severity", "info"],
        )

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_post_all_params(self, mock_run):
        mock_run.return_value = "Posted: x.md"
        result = efferens(
            action="post",
            message="urgent task",
            sender="system",
            to="admin",
            severity="warning",
            subject="alert",
        )
        assert result == "Posted: x.md"
        mock_run.assert_called_once_with(
            BINARY,
            [
                "post", "urgent task",
                "--from", "system",
                "--to", "admin",
                "--severity", "warning",
                "--subject", "alert",
            ],
        )

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_post_action_severity(self, mock_run):
        mock_run.return_value = "ok"
        efferens(action="post", message="do it", sender="a", severity="action")
        args_passed = mock_run.call_args[0][1]
        assert "--severity" in args_passed
        idx = args_passed.index("--severity")
        assert args_passed[idx + 1] == "action"

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_post_no_subject_omits_flag(self, mock_run):
        mock_run.return_value = "ok"
        efferens(action="post", message="m", sender="s")
        args_passed = mock_run.call_args[0][1]
        assert "--subject" not in args_passed

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_post_empty_subject_omits_flag(self, mock_run):
        mock_run.return_value = "ok"
        efferens(action="post", message="m", sender="s", subject="")
        args_passed = mock_run.call_args[0][1]
        assert "--subject" not in args_passed


# ── action="count" ───────────────────────────────────────────────────────────


class TestCountAction:
    @patch("metabolon.enzymes.efferens.run_cli")
    def test_count(self, mock_run):
        mock_run.return_value = "42"
        result = efferens(action="count")
        assert result == "42"
        mock_run.assert_called_once_with(BINARY, ["count"])

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_count_zero(self, mock_run):
        mock_run.return_value = "0"
        assert efferens(action="count") == "0"

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_count_ignores_extra_params(self, mock_run):
        mock_run.return_value = "5"
        efferens(action="count", message="ignored", sender="ignored", to="ignored")
        mock_run.assert_called_once_with(BINARY, ["count"])


# ── unknown action ───────────────────────────────────────────────────────────


class TestUnknownAction:
    def test_unknown_returns_error_string(self):
        result = efferens(action="delete")
        assert isinstance(result, str)
        assert "Unknown action" in result
        assert "delete" in result

    def test_unknown_mentions_valid_actions(self):
        result = efferens(action="bogus")
        assert "list" in result
        assert "post" in result
        assert "count" in result

    def test_case_sensitive(self):
        result = efferens(action="LIST")
        assert "Unknown action" in result

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_does_not_call_run_cli(self, mock_run):
        efferens(action="whatever")
        mock_run.assert_not_called()


# ── error propagation ────────────────────────────────────────────────────────


class TestErrorPropagation:
    @patch("metabolon.enzymes.efferens.run_cli")
    def test_run_cli_value_error_propagates(self, mock_run):
        mock_run.side_effect = ValueError("Binary not found")
        with pytest.raises(ValueError, match="Binary not found"):
            efferens(action="list")

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_run_cli_timeout_propagates(self, mock_run):
        mock_run.side_effect = ValueError("efferens timed out")
        with pytest.raises(ValueError, match="timed out"):
            efferens(action="count")
