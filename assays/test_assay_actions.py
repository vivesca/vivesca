"""Tests for assay enzyme — life experiment tracker."""
from unittest.mock import patch
import pytest


class TestAssayList:
    """Tests for the list action."""

    @patch("metabolon.enzymes.assay.run_cli")
    def test_list_calls_run_cli_with_correct_args(self, mock_run):
        from metabolon.enzymes.assay import assay

        mock_run.return_value = "experiment1\nexperiment2"
        result = assay(action="list")

        mock_run.assert_called_once()
        args = mock_run.call_args
        assert args[0][1] == ["list"]  # second positional arg is the args list
        assert args[1]["timeout"] == 60
        assert result == "experiment1\nexperiment2"

    @patch("metabolon.enzymes.assay.run_cli")
    def test_list_ignores_name_parameter(self, mock_run):
        """List action should ignore any name parameter."""
        from metabolon.enzymes.assay import assay

        mock_run.return_value = "results"
        result = assay(action="list", name="ignored")

        args = mock_run.call_args
        assert args[0][1] == ["list"]
        assert result == "results"


class TestAssayCheck:
    """Tests for the check action."""

    @patch("metabolon.enzymes.assay.run_cli")
    def test_check_with_name(self, mock_run):
        from metabolon.enzymes.assay import assay

        mock_run.return_value = "check result"
        result = assay(action="check", name="my-experiment")

        args = mock_run.call_args
        assert args[0][1] == ["check", "my-experiment"]
        assert args[1]["timeout"] == 120
        assert result == "check result"

    @patch("metabolon.enzymes.assay.run_cli")
    def test_check_without_name(self, mock_run):
        """Check without name should only pass 'check' arg."""
        from metabolon.enzymes.assay import assay

        mock_run.return_value = "check result"
        result = assay(action="check")

        args = mock_run.call_args
        assert args[0][1] == ["check"]
        assert args[1]["timeout"] == 120

    @patch("metabolon.enzymes.assay.run_cli")
    def test_check_empty_name(self, mock_run):
        """Empty string name should not be appended."""
        from metabolon.enzymes.assay import assay

        mock_run.return_value = "done"
        result = assay(action="check", name="")

        args = mock_run.call_args
        assert args[0][1] == ["check"]


class TestAssayClose:
    """Tests for the close action."""

    @patch("metabolon.enzymes.assay.run_cli")
    def test_close_with_name(self, mock_run):
        from metabolon.enzymes.assay import assay

        mock_run.return_value = "closed"
        result = assay(action="close", name="my-experiment")

        args = mock_run.call_args
        assert args[0][1] == ["close", "my-experiment"]
        assert args[1]["timeout"] == 120
        assert result == "closed"

    @patch("metabolon.enzymes.assay.run_cli")
    def test_close_without_name(self, mock_run):
        """Close without name should only pass 'close' arg."""
        from metabolon.enzymes.assay import assay

        mock_run.return_value = "closed"
        result = assay(action="close")

        args = mock_run.call_args
        assert args[0][1] == ["close"]
        assert args[1]["timeout"] == 120


class TestAssayUnknownAction:
    """Tests for error handling with unknown actions."""

    def test_unknown_action_returns_error_message(self):
        from metabolon.enzymes.assay import assay

        result = assay(action="nonexistent")
        assert "unknown action" in result.lower()
        assert "nonexistent" in result
        assert "list" in result or "check" in result or "close" in result

    def test_unknown_action_empty_string(self):
        from metabolon.enzymes.assay import assay

        result = assay(action="")
        assert "unknown action" in result.lower()

    def test_unknown_action_does_not_call_run_cli(self):
        """Unknown actions should not invoke run_cli at all."""
        from metabolon.enzymes.assay import assay, run_cli

        with patch("metabolon.enzymes.assay.run_cli") as mock_run:
            result = assay(action="invalid")
            mock_run.assert_not_called()
            assert "unknown action" in result.lower()


class TestAssayBinaryPath:
    """Tests for the BINARY constant."""

    def test_binary_path_is_absolute(self):
        from metabolon.enzymes.assay import BINARY
        from pathlib import Path

        # BINARY is a string, should be absolute path
        assert BINARY.startswith(str(Path.home()))
        assert "effectors" in BINARY
        assert "assay" in BINARY
