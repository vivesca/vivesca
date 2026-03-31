from __future__ import annotations

"""Tests for metabolon/enzymes/efferens.py."""

from unittest.mock import patch

import pytest


# Import the module under test
from metabolon.enzymes.efferens import efferens, BINARY


class TestEfferensList:
    """Tests for efferens list action."""

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_list_basic(self, mock_run_cli):
        """Test list action with default to parameter."""
        mock_run_cli.return_value = "message1\nmessage2"
        
        result = efferens(action="list")
        
        mock_run_cli.assert_called_once_with(BINARY, ["list", "--to", "terry"])
        assert result == "message1\nmessage2"

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_list_with_custom_recipient(self, mock_run_cli):
        """Test list action with custom recipient."""
        mock_run_cli.return_value = "custom messages"
        
        result = efferens(action="list", to="alice")
        
        mock_run_cli.assert_called_once_with(BINARY, ["list", "--to", "alice"])
        assert result == "custom messages"

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_list_empty_recipient(self, mock_run_cli):
        """Test list action with empty recipient."""
        mock_run_cli.return_value = "all messages"
        
        result = efferens(action="list", to="")
        
        # Empty to should not add --to flag
        mock_run_cli.assert_called_once_with(BINARY, ["list"])
        assert result == "all messages"

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_list_returns_empty_string(self, mock_run_cli):
        """Test list action when no messages exist."""
        mock_run_cli.return_value = ""
        
        result = efferens(action="list")
        
        assert result == ""


class TestEfferensPost:
    """Tests for efferens post action."""

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_post_basic(self, mock_run_cli):
        """Test post action with required parameters."""
        mock_run_cli.return_value = "Posted"
        
        result = efferens(
            action="post",
            message="Hello world",
            sender="bot",
        )
        
        mock_run_cli.assert_called_once_with(
            BINARY,
            ["post", "Hello world", "--from", "bot", "--to", "terry", "--severity", "info"]
        )
        assert result == "Posted"

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_post_with_all_parameters(self, mock_run_cli):
        """Test post action with all parameters specified."""
        mock_run_cli.return_value = "Done."
        
        result = efferens(
            action="post",
            message="Urgent message",
            sender="alert-system",
            to="admin",
            severity="warning",
            subject="System Alert",
        )
        
        mock_run_cli.assert_called_once_with(
            BINARY,
            ["post", "Urgent message", "--from", "alert-system", "--to", "admin", "--severity", "warning", "--subject", "System Alert"]
        )
        assert result == "Done."

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_post_with_subject(self, mock_run_cli):
        """Test post action with subject."""
        mock_run_cli.return_value = "Posted with subject"
        
        result = efferens(
            action="post",
            message="Body text",
            sender="sender",
            subject="Important Subject",
        )
        
        call_args = mock_run_cli.call_args[0][1]
        assert "--subject" in call_args
        assert "Important Subject" in call_args

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_post_without_subject(self, mock_run_cli):
        """Test post action without subject omits --subject flag."""
        mock_run_cli.return_value = "Posted"
        
        result = efferens(
            action="post",
            message="No subject",
            sender="sender",
        )
        
        call_args = mock_run_cli.call_args[0][1]
        assert "--subject" not in call_args

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_post_severity_action(self, mock_run_cli):
        """Test post action with 'action' severity."""
        mock_run_cli.return_value = "Action posted"
        
        result = efferens(
            action="post",
            message="Action required",
            sender="system",
            severity="action",
        )
        
        call_args = mock_run_cli.call_args[0][1]
        assert "--severity" in call_args
        severity_idx = call_args.index("--severity")
        assert call_args[severity_idx + 1] == "action"

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_post_empty_message(self, mock_run_cli):
        """Test post action with empty message."""
        mock_run_cli.return_value = "Done."
        
        result = efferens(
            action="post",
            message="",
            sender="empty-sender",
        )
        
        # Empty message should still be passed
        call_args = mock_run_cli.call_args[0][1]
        assert "post" in call_args
        assert "" in call_args


class TestEfferensCount:
    """Tests for efferens count action."""

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_count_returns_number(self, mock_run_cli):
        """Test count action returns count."""
        mock_run_cli.return_value = "42"
        
        result = efferens(action="count")
        
        mock_run_cli.assert_called_once_with(BINARY, ["count"])
        assert result == "42"

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_count_zero(self, mock_run_cli):
        """Test count action when no messages."""
        mock_run_cli.return_value = "0"
        
        result = efferens(action="count")
        
        assert result == "0"


class TestEfferensUnknownAction:
    """Tests for unknown action handling."""

    def test_unknown_action_returns_error(self):
        """Test unknown action returns helpful error message."""
        result = efferens(action="invalid")
        
        assert "Unknown action" in result
        assert "invalid" in result
        assert "list" in result
        assert "post" in result
        assert "count" in result

    def test_unknown_action_delete(self):
        """Test delete action is not recognized."""
        result = efferens(action="delete")
        
        assert "Unknown action" in result

    def test_unknown_action_empty(self):
        """Test empty action returns error."""
        result = efferens(action="")
        
        assert "Unknown action" in result


class TestEfferensBinary:
    """Tests for BINARY constant."""

    def test_binary_path(self):
        """Test that BINARY points to correct location."""
        assert ".local/bin/efferens" in BINARY
        assert BINARY.endswith("efferens")


class TestEfferensErrorHandling:
    """Tests for error propagation from run_cli."""

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_run_cli_error_propagates(self, mock_run_cli):
        """Test that run_cli errors are propagated."""
        mock_run_cli.side_effect = ValueError("Binary not found")
        
        with pytest.raises(ValueError, match="Binary not found"):
            efferens(action="list")

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_run_cli_timeout_propagates(self, mock_run_cli):
        """Test that timeout errors are propagated."""
        mock_run_cli.side_effect = ValueError("efferens timed out (30s)")
        
        with pytest.raises(ValueError, match="timed out"):
            efferens(action="count")

    @patch("metabolon.enzymes.efferens.run_cli")
    def test_run_cli_process_error_propagates(self, mock_run_cli):
        """Test that process errors are propagated."""
        mock_run_cli.side_effect = ValueError("efferens error: permission denied")
        
        with pytest.raises(ValueError, match="permission denied"):
            efferens(action="post", message="test", sender="test")
