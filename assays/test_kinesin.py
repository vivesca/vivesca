from __future__ import annotations

"""Tests for kinesin — session-independent agent dispatcher."""

from unittest.mock import patch

import pytest

from metabolon.enzymes.kinesin import translocation, TranslocationResult, EffectorResult


def test_translocation_list_action():
    """list action calls list_tasks and returns TranslocationResult."""
    with patch("metabolon.organelles.gemmation.list_tasks") as mock_list:
        mock_list.return_value = "task1\n task2"

        result = translocation(action="list")

        assert isinstance(result, TranslocationResult)
        assert result.output == "task1\n task2"
        mock_list.assert_called_once()


def test_translocation_run_action():
    """run action calls run_task with name and returns EffectorResult."""
    with patch("metabolon.organelles.gemmation.run_task") as mock_run:
        mock_run.return_value = "Started task my-task"

        result = translocation(action="run", name="my-task")

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.message == "Started task my-task"
        mock_run.assert_called_once_with("my-task")


def test_translocation_cancel_action():
    """cancel action calls cancel_task with name and returns EffectorResult."""
    with patch("metabolon.organelles.gemmation.cancel_task") as mock_cancel:
        mock_cancel.return_value = "Cancelled task my-task"

        result = translocation(action="cancel", name="my-task")

        assert isinstance(result, EffectorResult)
        assert result.success is True
        assert result.message == "Cancelled task my-task"
        mock_cancel.assert_called_once_with("my-task")


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


def test_translocation_unknown_action():
    """Unknown action returns error message in TranslocationResult."""
    result = translocation(action="invalid")

    assert isinstance(result, TranslocationResult)
    assert "Unknown action: invalid" in result.output
    assert "list|run|cancel|results" in result.output


def test_translocation_empty_name_not_required_for_list():
    """list action works even without name (ignored)."""
    with patch("metabolon.organelles.gemmation.list_tasks") as mock_list:
        mock_list.return_value = ""

        result = translocation(action="list", name="")

        assert isinstance(result, TranslocationResult)
        mock_list.assert_called_once()
