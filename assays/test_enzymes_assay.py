from __future__ import annotations

"""Tests for metabolon/enzymes/assay.py — life experiment tracker MCP tool."""

import pytest
from unittest.mock import patch, MagicMock

import metabolon.enzymes.assay as mod
from metabolon.enzymes.assay import assay, BINARY


# ---------------------------------------------------------------------------
# Helper: patch run_cli at the module where it is used
# ---------------------------------------------------------------------------

def _patch_run_cli():
    """Patch run_cli in the assay module's namespace."""
    return patch.object(mod, "run_cli")


# ---------------------------------------------------------------------------
# action="list"
# ---------------------------------------------------------------------------

class TestList:
    def test_list_calls_run_cli_with_list(self):
        with _patch_run_cli() as mock:
            mock.return_value = "exp1\nexp2"
            result = assay("list")
            mock.assert_called_once_with(BINARY, ["list"], timeout=60)
            assert result == "exp1\nexp2"

    def test_list_no_name_arg(self):
        """list action should ignore the name parameter."""
        with _patch_run_cli() as mock:
            mock.return_value = "empty"
            result = assay("list", name="should-be-ignored")
            mock.assert_called_once_with(BINARY, ["list"], timeout=60)
            assert result == "empty"


# ---------------------------------------------------------------------------
# action="check"
# ---------------------------------------------------------------------------

class TestCheck:
    def test_check_with_name(self):
        with _patch_run_cli() as mock:
            mock.return_value = "checked caffeine-cut"
            result = assay("check", name="caffeine-cut")
            mock.assert_called_once_with(BINARY, ["check", "caffeine-cut"], timeout=120)
            assert result == "checked caffeine-cut"

    def test_check_without_name(self):
        with _patch_run_cli() as mock:
            mock.return_value = "checked all"
            result = assay("check")
            mock.assert_called_once_with(BINARY, ["check"], timeout=120)
            assert result == "checked all"

    def test_check_empty_name_same_as_no_name(self):
        with _patch_run_cli() as mock:
            mock.return_value = "ok"
            result = assay("check", name="")
            mock.assert_called_once_with(BINARY, ["check"], timeout=120)
            assert result == "ok"


# ---------------------------------------------------------------------------
# action="close"
# ---------------------------------------------------------------------------

class TestClose:
    def test_close_with_name(self):
        with _patch_run_cli() as mock:
            mock.return_value = "closed caffeine-cut"
            result = assay("close", name="caffeine-cut")
            mock.assert_called_once_with(BINARY, ["close", "caffeine-cut"], timeout=120)
            assert result == "closed caffeine-cut"

    def test_close_without_name(self):
        with _patch_run_cli() as mock:
            mock.return_value = "closed all"
            result = assay("close")
            mock.assert_called_once_with(BINARY, ["close"], timeout=120)
            assert result == "closed all"

    def test_close_empty_name_omits_arg(self):
        with _patch_run_cli() as mock:
            mock.return_value = "done"
            result = assay("close", name="")
            mock.assert_called_once_with(BINARY, ["close"], timeout=120)
            assert result == "done"


# ---------------------------------------------------------------------------
# action=<unknown>
# ---------------------------------------------------------------------------

class TestUnknownAction:
    def test_unknown_action_returns_error(self):
        result = assay("bogus")
        assert "Error" in result
        assert "bogus" in result
        assert "list" in result  # help text mentions valid actions

    def test_unknown_action_does_not_call_run_cli(self):
        with _patch_run_cli() as mock:
            result = assay("explode")
            mock.assert_not_called()
            assert "Error" in result


# ---------------------------------------------------------------------------
# run_cli error propagation
# ---------------------------------------------------------------------------

class TestErrorPropagation:
    def test_binary_not_found_raises(self):
        with _patch_run_cli() as mock:
            mock.side_effect = ValueError("Binary not found: /no/such/binary")
            with pytest.raises(ValueError, match="Binary not found"):
                assay("list")

    def test_timeout_raises(self):
        with _patch_run_cli() as mock:
            mock.side_effect = ValueError("assay timed out")
            with pytest.raises(ValueError, match="timed out"):
                assay("check", name="slow-exp")

    def test_subprocess_error_raises(self):
        with _patch_run_cli() as mock:
            mock.side_effect = ValueError("assay error: something broke")
            with pytest.raises(ValueError, match="something broke"):
                assay("close", name="broken")


# ---------------------------------------------------------------------------
# BINARY path sanity
# ---------------------------------------------------------------------------

class TestBinaryPath:
    def test_binary_points_to_assay_effector(self):
        assert BINARY.endswith("effectors/assay")
        assert "assay" in BINARY

    def test_binary_is_string(self):
        assert isinstance(BINARY, str)


# ---------------------------------------------------------------------------
# Tool metadata (smoke test that decorator doesn't break callability)
# ---------------------------------------------------------------------------

class TestToolMetadata:
    def test_function_is_callable(self):
        assert callable(assay)

    def test_return_type_is_str(self):
        with _patch_run_cli() as mock:
            mock.return_value = "ok"
            assert isinstance(assay("list"), str)
