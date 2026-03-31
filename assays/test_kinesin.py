from __future__ import annotations

"""Tests for kinesin — session-independent agent dispatcher."""

from unittest.mock import patch

import pytest

from metabolon.enzymes.kinesin import translocation, TranslocationResult, EffectorResult
from metabolon.morphology import Secretion


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------


def test_translocation_list_action():
    """list action calls list_tasks and returns TranslocationResult."""
    with patch("metabolon.organelles.gemmation.list_tasks") as mock_list:
        mock_list.return_value = "task1\n task2"

        result = translocation(action="list")

        assert isinstance(result, TranslocationResult)
        assert result.output == "task1\n task2"
        mock_list.assert_called_once()


def test_list_returns_secretion_subclass():
    """TranslocationResult is a Secretion for schema compatibility."""
    with patch("metabolon.organelles.gemmation.list_tasks") as mock_list:
        mock_list.return_value = "ok"

        result = translocation(action="list")

        assert isinstance(result, Secretion)
        assert isinstance(result, TranslocationResult)


def test_list_name_ignored():
    """list action ignores the name parameter entirely."""
    with patch("metabolon.organelles.gemmation.list_tasks") as mock_list:
        mock_list.return_value = ""

        translocation(action="list", name="should-be-ignored")

        mock_list.assert_called_once_with()


def test_list_empty_result():
    """list action returns empty string output when no tasks exist."""
    with patch("metabolon.organelles.gemmation.list_tasks") as mock_list:
        mock_list.return_value = ""

        result = translocation(action="list")

        assert isinstance(result, TranslocationResult)
        assert result.output == ""


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


def test_translocation_run_action():
    """run action calls run_task with name and returns EffectorResult."""
    with patch("metabolon.organelles.gemmation.run_task") as mock_run:
        mock_run.return_value = "Started task my-task"

        result = translocation(action="run", name="my-task")

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.message == "Started task my-task"
        mock_run.assert_called_once_with("my-task")


def test_run_returns_secretion_subclass():
    """EffectorResult is a Secretion subclass."""
    with patch("metabolon.organelles.gemmation.run_task") as mock_run:
        mock_run.return_value = "ok"

        result = translocation(action="run", name="t")

        assert isinstance(result, Secretion)
        assert isinstance(result, EffectorResult)


def test_run_passes_empty_name_through():
    """run action passes empty string to run_task (does not coerce to None)."""
    with patch("metabolon.organelles.gemmation.run_task") as mock_run:
        mock_run.return_value = "started"

        translocation(action="run", name="")

        mock_run.assert_called_once_with("")


def test_run_with_special_chars_in_name():
    """run action passes special characters in task name verbatim."""
    with patch("metabolon.organelles.gemmation.run_task") as mock_run:
        mock_run.return_value = "ok"

        translocation(action="run", name="my-task_v2.0@prod")

        mock_run.assert_called_once_with("my-task_v2.0@prod")


def test_run_result_has_default_data_dict():
    """EffectorResult includes the default empty data dict."""
    with patch("metabolon.organelles.gemmation.run_task") as mock_run:
        mock_run.return_value = "done"

        result = translocation(action="run", name="t")

        assert result.data == {}


# ---------------------------------------------------------------------------
# cancel
# ---------------------------------------------------------------------------


def test_translocation_cancel_action():
    """cancel action calls cancel_task with name and returns EffectorResult."""
    with patch("metabolon.organelles.gemmation.cancel_task") as mock_cancel:
        mock_cancel.return_value = "Cancelled task my-task"

        result = translocation(action="cancel", name="my-task")

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.message == "Cancelled task my-task"
        mock_cancel.assert_called_once_with("my-task")


def test_cancel_passes_empty_name_through():
    """cancel action passes empty string to cancel_task."""
    with patch("metabolon.organelles.gemmation.cancel_task") as mock_cancel:
        mock_cancel.return_value = "cancelled"

        translocation(action="cancel", name="")

        mock_cancel.assert_called_once_with("")


def test_cancel_returns_secretion_subclass():
    """cancel returns EffectorResult which is a Secretion."""
    with patch("metabolon.organelles.gemmation.cancel_task") as mock_cancel:
        mock_cancel.return_value = "ok"

        result = translocation(action="cancel", name="t")

        assert isinstance(result, Secretion)
        assert isinstance(result, EffectorResult)


# ---------------------------------------------------------------------------
# results
# ---------------------------------------------------------------------------


def test_translocation_results_with_name():
    """results action calls get_results with specified name."""
    with patch("metabolon.organelles.gemmation.get_results") as mock_results:
        mock_results.return_value = "Results for my-task"

        result = translocation(action="results", name="my-task")

        assert isinstance(result, TranslocationResult)
        assert result.output == "Results for my-task"
        mock_results.assert_called_once_with("my-task")


def test_translocation_results_without_name():
    """results action calls get_results with None when no name given."""
    with patch("metabolon.organelles.gemmation.get_results") as mock_results:
        mock_results.return_value = "All results"

        result = translocation(action="results")

        assert isinstance(result, TranslocationResult)
        assert result.output == "All results"
        mock_results.assert_called_once_with(None)


def test_results_empty_string_name_coerces_to_none():
    """results with name='' passes None (falsy coercion via `name or None`)."""
    with patch("metabolon.organelles.gemmation.get_results") as mock_results:
        mock_results.return_value = "all"

        translocation(action="results", name="")

        mock_results.assert_called_once_with(None)


def test_results_returns_secretion_subclass():
    """results returns TranslocationResult which is a Secretion."""
    with patch("metabolon.organelles.gemmation.get_results") as mock_results:
        mock_results.return_value = "ok"

        result = translocation(action="results")

        assert isinstance(result, Secretion)
        assert isinstance(result, TranslocationResult)


# ---------------------------------------------------------------------------
# unknown / edge-case actions
# ---------------------------------------------------------------------------


def test_translocation_unknown_action():
    """Unknown action returns error message in TranslocationResult."""
    result = translocation(action="invalid")

    assert isinstance(result, TranslocationResult)
    assert "Unknown action: invalid" in result.output
    assert "list|run|cancel|results" in result.output


def test_unknown_action_case_sensitive():
    """Actions are case-sensitive: 'LIST' is unknown."""
    result = translocation(action="LIST")

    assert isinstance(result, TranslocationResult)
    assert "Unknown action: LIST" in result.output


def test_unknown_action_empty_string():
    """Empty string action is treated as unknown."""
    result = translocation(action="")

    assert isinstance(result, TranslocationResult)
    assert "Unknown action: " in result.output


# ---------------------------------------------------------------------------
# return-type model validation
# ---------------------------------------------------------------------------


def test_translocation_result_has_output_field():
    """TranslocationResult model has an 'output' string field."""
    r = TranslocationResult(output="hello")
    assert r.output == "hello"


def test_effector_result_serialization():
    """EffectorResult from run/cancel serializes cleanly to dict."""
    with patch("metabolon.organelles.gemmation.run_task") as mock_run:
        mock_run.return_value = "dispatched"

        result = translocation(action="run", name="t")

        d = result.model_dump()
        assert d["success"] is True
        assert d["message"] == "dispatched"
        assert isinstance(d.get("data"), dict)


def test_translocation_result_serialization():
    """TranslocationResult serializes cleanly to dict."""
    with patch("metabolon.organelles.gemmation.list_tasks") as mock_list:
        mock_list.return_value = "items"

        result = translocation(action="list")

        d = result.model_dump()
        assert d["output"] == "items"


# ---------------------------------------------------------------------------
# lazy import verification
# ---------------------------------------------------------------------------


def test_list_imports_from_gemmation():
    """list action lazily imports list_tasks from gemmation."""
    with patch("metabolon.organelles.gemmation.list_tasks") as mock_list:
        mock_list.return_value = "ok"

        translocation(action="list")

        mock_list.assert_called_once()


def test_run_imports_from_gemmation():
    """run action lazily imports run_task from gemmation."""
    with patch("metabolon.organelles.gemmation.run_task") as mock_run:
        mock_run.return_value = "ok"

        translocation(action="run", name="t")

        mock_run.assert_called_once_with("t")


def test_cancel_imports_from_gemmation():
    """cancel action lazily imports cancel_task from gemmation."""
    with patch("metabolon.organelles.gemmation.cancel_task") as mock_cancel:
        mock_cancel.return_value = "ok"

        translocation(action="cancel", name="t")

        mock_cancel.assert_called_once_with("t")


def test_results_imports_from_gemmation():
    """results action lazily imports get_results from gemmation."""
    with patch("metabolon.organelles.gemmation.get_results") as mock_results:
        mock_results.return_value = "ok"

        translocation(action="results", name="t")

        mock_results.assert_called_once_with("t")
