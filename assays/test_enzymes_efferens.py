from __future__ import annotations

"""Tests for metabolon.enzymes.efferens — the MCP tool wrapper.

All CLI calls are mocked; no external binaries invoked.
"""

from unittest.mock import patch

import pytest

from metabolon.enzymes.efferens import BINARY, efferens

_CLI = "metabolon.enzymes.efferens.run_cli"


class TestList:
    """action='list' delegates to run_cli with list args."""

    @patch(_CLI, return_value="msg1\nmsg2")
    def test_basic_list(self, mock_cli):
        result = efferens("list")
        mock_cli.assert_called_once_with(BINARY, ["list", "--to", "terry"])
        assert result == "msg1\nmsg2"

    @patch(_CLI, return_value="no messages")
    def test_custom_recipient(self, mock_cli):
        result = efferens("list", to="alice")
        mock_cli.assert_called_once_with(BINARY, ["list", "--to", "alice"])
        assert result == "no messages"

    @patch(_CLI, return_value="empty")
    def test_empty_to_omits_flag(self, mock_cli):
        # When to="" the if-guard skips the --to flag
        result = efferens("list", to="")
        mock_cli.assert_called_once_with(BINARY, ["list"])
        assert result == "empty"

    @patch(_CLI, return_value="inbox")
    def test_returns_run_cli_output(self, mock_cli):
        assert efferens("list") == "inbox"


class TestPost:
    """action='post' delegates to run_cli with post args."""

    @patch(_CLI, return_value="Posted.")
    def test_basic_post(self, mock_cli):
        result = efferens("post", message="hello", sender="bot")
        mock_cli.assert_called_once_with(
            BINARY,
            ["post", "hello", "--from", "bot", "--to", "terry", "--severity", "info"],
        )
        assert result == "Posted."

    @patch(_CLI, return_value="ok")
    def test_custom_params(self, mock_cli):
        result = efferens(
            "post",
            message="urgent",
            sender="admin",
            to="bob",
            severity="warning",
        )
        mock_cli.assert_called_once_with(
            BINARY,
            ["post", "urgent", "--from", "admin", "--to", "bob", "--severity", "warning"],
        )

    @patch(_CLI, return_value="ok")
    def test_with_subject(self, mock_cli):
        result = efferens(
            "post",
            message="body",
            sender="sys",
            subject="Test Subject",
        )
        args = mock_cli.call_args[0][1]
        assert "--subject" in args
        assert "Test Subject" in args

    @patch(_CLI, return_value="ok")
    def test_without_subject_no_flag(self, mock_cli):
        result = efferens("post", message="body", sender="sys")
        args = mock_cli.call_args[0][1]
        assert "--subject" not in args

    @patch(_CLI, return_value="ok")
    def test_severity_action(self, mock_cli):
        efferens("post", message="x", sender="y", severity="action")
        args = mock_cli.call_args[0][1]
        assert args[-1] == "action"


class TestCount:
    """action='count' delegates to run_cli with ['count']."""

    @patch(_CLI, return_value="42")
    def test_basic_count(self, mock_cli):
        result = efferens("count")
        mock_cli.assert_called_once_with(BINARY, ["count"])
        assert result == "42"

    @patch(_CLI, return_value="0")
    def test_empty_count(self, mock_cli):
        assert efferens("count") == "0"


class TestUnknownAction:
    """Unrecognised actions return an error string without calling run_cli."""

    @patch(_CLI)
    def test_unknown_action(self, mock_cli):
        result = efferens("delete")
        mock_cli.assert_not_called()
        assert "Unknown action" in result
        assert "delete" in result

    @patch(_CLI)
    def test_empty_action(self, mock_cli):
        result = efferens("")
        mock_cli.assert_not_called()
        assert "Unknown action" in result

    @patch(_CLI)
    def test_case_sensitive(self, mock_cli):
        # "LIST" should not match "list"
        result = efferens("LIST")
        mock_cli.assert_not_called()
        assert "Unknown action" in result


class TestDefaults:
    """Verify that the default parameter values flow correctly."""

    @patch(_CLI, return_value="ok")
    def test_default_to_is_terry(self, mock_cli):
        efferens("list")
        args = mock_cli.call_args[0][1]
        assert "--to" in args and "terry" in args

    @patch(_CLI, return_value="ok")
    def test_default_severity_is_info(self, mock_cli):
        efferens("post", message="m", sender="s")
        args = mock_cli.call_args[0][1]
        idx = args.index("--severity")
        assert args[idx + 1] == "info"
