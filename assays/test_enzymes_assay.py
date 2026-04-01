from __future__ import annotations

"""Tests for metabolon/enzymes/assay.py — mock run_cli, cover all branches."""

from unittest.mock import patch

from metabolon.enzymes.assay import assay, BINARY


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _run_cli_path():
    """Return the dotted import path used for patching."""
    return "metabolon.enzymes.assay.run_cli"


# ---------------------------------------------------------------------------
# list action
# ---------------------------------------------------------------------------

def test_list_action():
    with patch(_run_cli_path(), return_value="exp1\nexp2") as mock:
        result = assay(action="list")
    mock.assert_called_once_with(BINARY, ["list"], timeout=60)
    assert result == "exp1\nexp2"


def test_list_action_empty():
    with patch(_run_cli_path(), return_value="No experiments found.") as mock:
        result = assay(action="list")
    mock.assert_called_once_with(BINARY, ["list"], timeout=60)
    assert "No experiments" in result


def test_list_raises():
    with patch(_run_cli_path(), side_effect=ValueError("Binary not found")):
        try:
            assay(action="list")
            assert False, "Should have raised"
        except ValueError as e:
            assert "Binary not found" in str(e)


# ---------------------------------------------------------------------------
# check action
# ---------------------------------------------------------------------------

def test_check_with_name():
    with patch(_run_cli_path(), return_value="ok") as mock:
        result = assay(action="check", name="cold-plunge")
    mock.assert_called_once_with(BINARY, ["check", "cold-plunge"], timeout=120)
    assert result == "ok"


def test_check_without_name():
    with patch(_run_cli_path(), return_value="Done.") as mock:
        result = assay(action="check")
    mock.assert_called_once_with(BINARY, ["check"], timeout=120)
    assert result == "Done."


def test_check_timeout():
    with patch(_run_cli_path(), side_effect=ValueError("assay timed out (120s)")):
        try:
            assay(action="check", name="x")
            assert False, "Should have raised"
        except ValueError as e:
            assert "timed out" in str(e)


# ---------------------------------------------------------------------------
# close action
# ---------------------------------------------------------------------------

def test_close_with_name():
    with patch(_run_cli_path(), return_value="Closed exp.") as mock:
        result = assay(action="close", name="cold-plunge")
    mock.assert_called_once_with(BINARY, ["close", "cold-plunge"], timeout=120)
    assert result == "Closed exp."


def test_close_without_name():
    with patch(_run_cli_path(), return_value="Done.") as mock:
        result = assay(action="close")
    mock.assert_called_once_with(BINARY, ["close"], timeout=120)
    assert result == "Done."


def test_close_error_propagates():
    with patch(_run_cli_path(), side_effect=ValueError("assay error: boom")):
        try:
            assay(action="close", name="x")
            assert False, "Should have raised"
        except ValueError as e:
            assert "boom" in str(e)


# ---------------------------------------------------------------------------
# unknown action
# ---------------------------------------------------------------------------

def test_unknown_action():
    result = assay(action="explode")
    assert "Error" in result
    assert "explode" in result


def test_unknown_action_case_sensitive():
    result = assay(action="LIST")
    assert "Error" in result
    assert "LIST" in result


# ---------------------------------------------------------------------------
# return type is always str
# ---------------------------------------------------------------------------

def test_return_type_list():
    with patch(_run_cli_path(), return_value="ok"):
        assert isinstance(assay(action="list"), str)


def test_return_type_unknown():
    assert isinstance(assay(action="nope"), str)
