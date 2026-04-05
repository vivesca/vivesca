from __future__ import annotations

"""Tests for metabolon.enzymes.kinesin — tool metadata, statelessness,
sequential dispatch, and boundary conditions."""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from metabolon.enzymes.kinesin import TranslocationResult, translocation
from metabolon.morphology import EffectorResult, Secretion

# ---------------------------------------------------------------------------
# tool decorator metadata
# ---------------------------------------------------------------------------


def test_translocation_is_callable_directly():
    """The @tool-decorated function can still be invoked directly."""
    result = translocation(action="list")
    assert isinstance(result, TranslocationResult)


def test_translocation_preserves_function_name():
    """The @tool decorator preserves __name__."""
    assert translocation.__name__ == "translocation"


def test_translocation_has_docstring():
    """The @tool decorator preserves the original docstring."""
    assert translocation.__doc__ is not None
    assert "action" in translocation.__doc__.lower()


# ---------------------------------------------------------------------------
# TranslocationResult model
# ---------------------------------------------------------------------------


def test_translocation_result_inherits_secretion():
    """TranslocationResult is a Secretion subclass."""
    assert issubclass(TranslocationResult, Secretion)


def test_translocation_result_model_dump_keys():
    """TranslocationResult.model_dump() contains 'output' key."""
    r = TranslocationResult(output="hello")
    d = r.model_dump()
    assert "output" in d
    assert d["output"] == "hello"


def test_translocation_result_extra_fields_allowed():
    """TranslocationResult accepts extra fields (inherited from Secretion)."""
    r = TranslocationResult(output="x", extra_info="y")
    assert r.output == "x"
    assert r.extra_info == "y"  # type: ignore[attr-defined]


def test_translocation_result_output_required():
    """TranslocationResult requires the output field."""
    with pytest.raises(ValidationError):
        TranslocationResult()  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# sequential calls — statelessness
# ---------------------------------------------------------------------------


def test_sequential_list_then_list():
    """Two list calls return independent results."""
    with patch("metabolon.organelles.gemmation.list_tasks") as mock_list:
        mock_list.side_effect = ["first", "second"]

        r1 = translocation(action="list")
        r2 = translocation(action="list")

        assert r1.output == "first"
        assert r2.output == "second"
        assert mock_list.call_count == 2


def test_sequential_run_then_cancel():
    """run followed by cancel dispatches correctly to different backends."""
    with (
        patch("metabolon.organelles.gemmation.run_task") as mock_run,
        patch("metabolon.organelles.gemmation.cancel_task") as mock_cancel,
    ):
        mock_run.return_value = "started"
        mock_cancel.return_value = "stopped"

        r1 = translocation(action="run", name="alpha")
        r2 = translocation(action="cancel", name="alpha")

        assert isinstance(r1, EffectorResult)
        assert isinstance(r2, EffectorResult)
        assert r1.message == "started"
        assert r2.message == "stopped"
        mock_run.assert_called_once_with("alpha")
        mock_cancel.assert_called_once_with("alpha")


def test_sequential_results_then_list():
    """results then list dispatches to different backends."""
    with (
        patch("metabolon.organelles.gemmation.get_results") as mock_results,
        patch("metabolon.organelles.gemmation.list_tasks") as mock_list,
    ):
        mock_results.return_value = "output data"
        mock_list.return_value = "task listing"

        r1 = translocation(action="results", name="job")
        r2 = translocation(action="list")

        assert r1.output == "output data"
        assert r2.output == "task listing"


# ---------------------------------------------------------------------------
# boundary conditions
# ---------------------------------------------------------------------------


def test_unicode_task_name():
    """run action passes Unicode task names verbatim."""
    with patch("metabolon.organelles.gemmation.run_task") as mock_run:
        mock_run.return_value = "ok"

        result = translocation(action="run", name="タスク-τ1")

        mock_run.assert_called_once_with("タスク-τ1")
        assert isinstance(result, EffectorResult)


def test_very_long_task_name():
    """run action handles a 1000-char task name."""
    long_name = "x" * 1000
    with patch("metabolon.organelles.gemmation.run_task") as mock_run:
        mock_run.return_value = "dispatched"

        translocation(action="run", name=long_name)

        mock_run.assert_called_once_with(long_name)


def test_whitespace_only_name():
    """run action passes whitespace-only names through (no strip)."""
    with patch("metabolon.organelles.gemmation.run_task") as mock_run:
        mock_run.return_value = "ok"

        translocation(action="run", name="  ")

        mock_run.assert_called_once_with("  ")


def test_results_name_whitespace_not_coerced():
    """results with whitespace-only name passes it through (not falsy)."""
    with patch("metabolon.organelles.gemmation.get_results") as mock_results:
        mock_results.return_value = "data"

        translocation(action="results", name="  ")

        # "  " is truthy, so `name or None` keeps the whitespace string
        mock_results.assert_called_once_with("  ")


def test_multiline_return_value_in_list():
    """list action preserves multiline output."""
    multi = "task1: active\ntask2: idle\ntask3: done"
    with patch("metabolon.organelles.gemmation.list_tasks") as mock_list:
        mock_list.return_value = multi

        result = translocation(action="list")

        assert result.output == multi


def test_multiline_return_value_in_results():
    """results action preserves multiline output."""
    multi = "run1: ok\nrun2: fail\n---\nsummary"
    with patch("metabolon.organelles.gemmation.get_results") as mock_results:
        mock_results.return_value = multi

        result = translocation(action="results", name="t")

        assert result.output == multi


# ---------------------------------------------------------------------------
# unknown action edge cases
# ---------------------------------------------------------------------------


def test_unknown_action_numeric_string():
    """Numeric string action is treated as unknown."""
    result = translocation(action="123")

    assert isinstance(result, TranslocationResult)
    assert "Unknown action: 123" in result.output


def test_unknown_action_with_whitespace():
    """Action string with leading/trailing whitespace is unknown."""
    result = translocation(action=" list ")

    assert isinstance(result, TranslocationResult)
    assert "Unknown action" in result.output


def test_unknown_action_returns_action_usage_hint():
    """Unknown action output includes the valid action list."""
    result = translocation(action="bogus")

    assert "list|run|cancel|results" in result.output


# ---------------------------------------------------------------------------
# cross-action isolation
# ---------------------------------------------------------------------------


def test_run_does_not_call_cancel():
    """run action never invokes cancel_task."""
    with (
        patch("metabolon.organelles.gemmation.run_task") as mock_run,
        patch("metabolon.organelles.gemmation.cancel_task") as mock_cancel,
    ):
        mock_run.return_value = "ok"

        translocation(action="run", name="t")

        mock_cancel.assert_not_called()


def test_cancel_does_not_call_run():
    """cancel action never invokes run_task."""
    with (
        patch("metabolon.organelles.gemmation.cancel_task") as mock_cancel,
        patch("metabolon.organelles.gemmation.run_task") as mock_run,
    ):
        mock_cancel.return_value = "ok"

        translocation(action="cancel", name="t")

        mock_run.assert_not_called()


def test_list_does_not_call_get_results():
    """list action never invokes get_results."""
    with (
        patch("metabolon.organelles.gemmation.list_tasks") as mock_list,
        patch("metabolon.organelles.gemmation.get_results") as mock_results,
    ):
        mock_list.return_value = "ok"

        translocation(action="list")

        mock_results.assert_not_called()


def test_results_does_not_call_list():
    """results action never invokes list_tasks."""
    with (
        patch("metabolon.organelles.gemmation.get_results") as mock_results,
        patch("metabolon.organelles.gemmation.list_tasks") as mock_list,
    ):
        mock_results.return_value = "ok"

        translocation(action="results", name="t")

        mock_list.assert_not_called()


# ---------------------------------------------------------------------------
# return type consistency
# ---------------------------------------------------------------------------


def test_run_and_cancel_both_effector_result():
    """run and cancel both return EffectorResult with success=True."""
    with (
        patch("metabolon.organelles.gemmation.run_task") as mock_run,
        patch("metabolon.organelles.gemmation.cancel_task") as mock_cancel,
    ):
        mock_run.return_value = "r"
        mock_cancel.return_value = "c"

        r_run = translocation(action="run", name="t")
        r_cancel = translocation(action="cancel", name="t")

        assert type(r_run) is EffectorResult
        assert type(r_cancel) is EffectorResult
        assert r_run.success is True
        assert r_cancel.success is True


def test_list_and_results_both_translocation_result():
    """list and results both return TranslocationResult."""
    with (
        patch("metabolon.organelles.gemmation.list_tasks") as mock_list,
        patch("metabolon.organelles.gemmation.get_results") as mock_results,
    ):
        mock_list.return_value = "a"
        mock_results.return_value = "b"

        r_list = translocation(action="list")
        r_results = translocation(action="results")

        assert type(r_list) is TranslocationResult
        assert type(r_results) is TranslocationResult


# ---------------------------------------------------------------------------
# EffectorResult data field
# ---------------------------------------------------------------------------


def test_run_result_data_is_empty_dict():
    """EffectorResult from run has empty data dict."""
    with patch("metabolon.organelles.gemmation.run_task") as mock_run:
        mock_run.return_value = "ok"

        result = translocation(action="run", name="t")

        assert result.data == {}


def test_cancel_result_data_is_empty_dict():
    """EffectorResult from cancel has empty data dict."""
    with patch("metabolon.organelles.gemmation.cancel_task") as mock_cancel:
        mock_cancel.return_value = "ok"

        result = translocation(action="cancel", name="t")

        assert result.data == {}
