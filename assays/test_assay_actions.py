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


class TestAssayErrorPropagation:
    """Tests for error propagation from run_cli."""

    @patch("metabolon.enzymes.assay.run_cli")
    def test_list_propagates_value_error(self, mock_run):
        """List action should propagate ValueError from run_cli."""
        from metabolon.enzymes.assay import assay

        mock_run.side_effect = ValueError("Binary not found")
        with pytest.raises(ValueError, match="Binary not found"):
            assay(action="list")

    @patch("metabolon.enzymes.assay.run_cli")
    def test_check_propagates_timeout_error(self, mock_run):
        """Check action should propagate timeout ValueError."""
        from metabolon.enzymes.assay import assay

        mock_run.side_effect = ValueError("assay timed out")
        with pytest.raises(ValueError, match="timed out"):
            assay(action="check", name="exp")

    @patch("metabolon.enzymes.assay.run_cli")
    def test_close_propagates_process_error(self, mock_run):
        """Close action should propagate process error ValueError."""
        from metabolon.enzymes.assay import assay

        mock_run.side_effect = ValueError("assay error: something went wrong")
        with pytest.raises(ValueError, match="assay error"):
            assay(action="close", name="exp")


class TestAssayNameHandling:
    """Tests for name parameter handling."""

    @patch("metabolon.enzymes.assay.run_cli")
    def test_check_whitespace_name_is_appended(self, mock_run):
        """Whitespace name should still be appended (non-empty string)."""
        from metabolon.enzymes.assay import assay

        mock_run.return_value = "done"
        result = assay(action="check", name="   ")

        args = mock_run.call_args
        assert args[0][1] == ["check", "   "]
        assert result == "done"

    @patch("metabolon.enzymes.assay.run_cli")
    def test_check_special_characters_in_name(self, mock_run):
        """Special characters in name should be passed through."""
        from metabolon.enzymes.assay import assay

        mock_run.return_value = "done"
        result = assay(action="check", name="my-experiment_v2.0")

        args = mock_run.call_args
        assert args[0][1] == ["check", "my-experiment_v2.0"]
        assert result == "done"

    @patch("metabolon.enzymes.assay.run_cli")
    def test_close_unicode_name(self, mock_run):
        """Unicode characters in name should be handled."""
        from metabolon.enzymes.assay import assay

        mock_run.return_value = "closed"
        result = assay(action="close", name="实验-1")

        args = mock_run.call_args
        assert args[0][1] == ["close", "实验-1"]
        assert result == "closed"


class TestAssayReturnValues:
    """Tests for return value handling."""

    @patch("metabolon.enzymes.assay.run_cli")
    def test_list_returns_empty_string_as_is(self, mock_run):
        """Empty stdout from run_cli is returned as-is (run_cli returns 'Done.')."""
        from metabolon.enzymes.assay import assay

        mock_run.return_value = "Done."
        result = assay(action="list")
        assert result == "Done."

    @patch("metabolon.enzymes.assay.run_cli")
    def test_check_returns_multiline_output(self, mock_run):
        """Multiline output from run_cli should be preserved."""
        from metabolon.enzymes.assay import assay

        mock_run.return_value = "line1\nline2\nline3"
        result = assay(action="check", name="exp")
        assert result == "line1\nline2\nline3"
