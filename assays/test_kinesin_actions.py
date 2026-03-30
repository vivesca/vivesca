"""Tests for kinesin action-dispatch consolidation."""
from unittest.mock import patch
import pytest


def test_unknown_action():
    from metabolon.enzymes.kinesin import translocation, TranslocationResult
    result = translocation(action="nonexistent")
    assert isinstance(result, TranslocationResult)
    assert "unknown" in result.output.lower()


@patch("metabolon.organelles.gemmation.list_tasks")
def test_list_action(mock_list):
    from metabolon.enzymes.kinesin import translocation, TranslocationResult
    mock_list.return_value = "list result"
    result = translocation(action="list")
    assert isinstance(result, TranslocationResult)
    assert result.output == "list result"


@patch("metabolon.organelles.gemmation.run_task")
def test_run_action(mock_run):
    from metabolon.enzymes.kinesin import translocation, EffectorResult
    mock_run.return_value = "run result"
    result = translocation(action="run", name="test")
    assert isinstance(result, EffectorResult)
    assert result.success is True


@patch("metabolon.organelles.gemmation.cancel_task")
def test_cancel_action(mock_cancel):
    from metabolon.enzymes.kinesin import translocation, EffectorResult
    mock_cancel.return_value = "cancel result"
    result = translocation(action="cancel", name="test")
    assert isinstance(result, EffectorResult)
    assert result.success is True


@patch("metabolon.organelles.gemmation.get_results")
def test_results_action(mock_results):
    from metabolon.enzymes.kinesin import translocation, TranslocationResult
    mock_results.return_value = "results result"
    result = translocation(action="results", name="test")
    assert isinstance(result, TranslocationResult)
    assert result.output == "results result"
