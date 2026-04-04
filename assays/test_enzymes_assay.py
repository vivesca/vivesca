from __future__ import annotations

"""Tests for metabolon.enzymes.assay — life experiment tracker."""

from unittest.mock import call, patch

import pytest


class TestAssayTool:
    """Tests for the assay() MCP tool function."""

    @patch("metabolon.enzymes.assay.run_cli")
    def test_list_action(self, mock_run):
        from metabolon.enzymes.assay import BINARY, assay

        mock_run.return_value = "ExpA (active)\nExpB (closed)"
        result = assay(action="list")
        mock_run.assert_called_once_with(BINARY, ["list"], timeout=60)
        assert "ExpA" in result
        assert "ExpB" in result

    @patch("metabolon.enzymes.assay.run_cli")
    def test_check_action_with_name(self, mock_run):
        from metabolon.enzymes.assay import BINARY, assay

        mock_run.return_value = "Sleep: 7.2h, HRV: 45ms"
        result = assay(action="check", name="melatonin")
        mock_run.assert_called_once_with(BINARY, ["check", "melatonin"], timeout=120)
        assert "Sleep" in result

    @patch("metabolon.enzymes.assay.run_cli")
    def test_check_action_without_name(self, mock_run):
        from metabolon.enzymes.assay import BINARY, assay

        mock_run.return_value = "All experiments checked."
        assay(action="check")
        mock_run.assert_called_once_with(BINARY, ["check"], timeout=120)

    @patch("metabolon.enzymes.assay.run_cli")
    def test_close_action_with_name(self, mock_run):
        from metabolon.enzymes.assay import BINARY, assay

        mock_run.return_value = "Closed: melatonin (14 days)"
        result = assay(action="close", name="melatonin")
        mock_run.assert_called_once_with(BINARY, ["close", "melatonin"], timeout=120)
        assert "Closed" in result

    @patch("metabolon.enzymes.assay.run_cli")
    def test_close_action_without_name(self, mock_run):
        from metabolon.enzymes.assay import BINARY, assay

        mock_run.return_value = "Done."
        assay(action="close")
        mock_run.assert_called_once_with(BINARY, ["close"], timeout=120)

    def test_unknown_action_returns_error(self):
        from metabolon.enzymes.assay import assay

        result = assay(action="delete")
        assert "Error" in result
        assert "delete" in result
        assert "'delete'" in result

    def test_unknown_action_suggests_valid(self):
        from metabolon.enzymes.assay import assay

        result = assay(action="foobar")
        assert "list" in result
        assert "check" in result
        assert "close" in result

    @patch("metabolon.enzymes.assay.run_cli")
    def test_list_propagates_error(self, mock_run):
        from metabolon.enzymes.assay import assay

        mock_run.side_effect = ValueError("assay error: no experiments found")
        with pytest.raises(ValueError, match="no experiments"):
            assay(action="list")

    @patch("metabolon.enzymes.assay.run_cli")
    def test_check_propagates_timeout(self, mock_run):
        from metabolon.enzymes.assay import assay

        mock_run.side_effect = ValueError("assay timed out (120s)")
        with pytest.raises(ValueError, match="timed out"):
            assay(action="check", name="slow-exp")

    @patch("metabolon.enzymes.assay.run_cli")
    def test_close_propagates_binary_missing(self, mock_run):
        from metabolon.enzymes.assay import assay

        mock_run.side_effect = ValueError("Binary not found")
        with pytest.raises(ValueError, match="Binary not found"):
            assay(action="close", name="anything")

    def test_binary_path(self):
        from metabolon.enzymes.assay import BINARY

        assert "effectors" in BINARY
        assert BINARY.endswith("assay")

    @patch("metabolon.enzymes.assay.run_cli")
    def test_name_empty_string_not_appended(self, mock_run):
        """Empty string name should not be appended to args."""
        from metabolon.enzymes.assay import BINARY, assay

        mock_run.return_value = "ok"
        assay(action="check", name="")
        # name="" is falsy, so args should be ["check"] not ["check", ""]
        assert mock_run.call_args == call(BINARY, ["check"], timeout=120)

    @patch("metabolon.enzymes.assay.run_cli")
    def test_name_with_spaces(self, mock_run):
        """Names with spaces are passed as a single argument."""
        from metabolon.enzymes.assay import BINARY, assay

        mock_run.return_value = "ok"
        assay(action="close", name="cold exposure winter")
        mock_run.assert_called_once_with(BINARY, ["close", "cold exposure winter"], timeout=120)

    def test_action_case_sensitive(self):
        """Uppercase action is treated as unknown."""
        from metabolon.enzymes.assay import assay

        result = assay(action="LIST")
        assert "Error" in result
