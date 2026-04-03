"""Tests for metabolon.enzymes.catabolism."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from metabolon.enzymes.catabolism import (
    CatabolismConfirmResult,
    CatabolismResult,
    _confirm,
    _spending,
    catabolism,
)


# ---------------------------------------------------------------------------
# _spending
# ---------------------------------------------------------------------------


@patch("metabolon.respirometry.payments.assess_missing_statements", return_value=[])
@patch("metabolon.respirometry.payments.flag_overdue_payments", return_value=[])
@patch("metabolon.respirometry.metabolize_statements", return_value=[])
def test_spending_no_statements_no_alerts(mock_meta, mock_overdue, mock_missing):
    """When there are no statements, payments, or missing alerts, return a calm summary."""
    result = _spending()
    assert isinstance(result, CatabolismResult)
    assert result.statements_processed == 0
    assert result.total_alerts == 0
    assert "No new statements" in result.summary
    assert "All cards accounted" in result.summary


@patch("metabolon.respirometry.payments.assess_missing_statements", return_value=[])
@patch("metabolon.respirometry.payments.flag_overdue_payments", return_value=[])
@patch("metabolon.respirometry.metabolize_statements")
def test_spending_digests_statements(mock_meta, mock_overdue, mock_missing):
    """Successful statements produce formatted summary lines with card, date, txn count, total."""
    mock_meta.return_value = [
        {
            "card": "SCB",
            "statement_date": "2026-03-15",
            "transaction_count": 12,
            "total_hkd": 4321.50,
            "alerts": [],
        },
    ]
    result = _spending()
    assert isinstance(result, CatabolismResult)
    assert result.statements_processed == 1
    assert "SCB" in result.summary
    assert "4,321.50" in result.summary
    assert "12 transactions" in result.summary
    assert result.total_alerts == 0


@patch("metabolon.respirometry.payments.assess_missing_statements", return_value=[])
@patch("metabolon.respirometry.payments.flag_overdue_payments", return_value=["MOX payment overdue!"])
@patch("metabolon.respirometry.metabolize_statements", return_value=[])
def test_spending_includes_payment_alerts(mock_meta, mock_overdue, mock_missing):
    """Payment alerts are surfaced in the summary and counted."""
    result = _spending()
    assert isinstance(result, CatabolismResult)
    assert "Payment alerts" in result.summary
    assert "MOX payment overdue" in result.summary
    assert result.total_alerts == 1


@patch("metabolon.respirometry.payments.assess_missing_statements", return_value=["HSBC Feb missing"])
@patch("metabolon.respirometry.payments.flag_overdue_payments", return_value=[])
@patch("metabolon.respirometry.metabolize_statements", return_value=[])
def test_spending_includes_missing_statements(mock_meta, mock_overdue, mock_missing):
    """Missing statement alerts appear in summary and count."""
    result = _spending()
    assert "Missing statements" in result.summary
    assert "HSBC Feb missing" in result.summary
    assert result.total_alerts == 1


@patch("metabolon.respirometry.payments.assess_missing_statements", return_value=[])
@patch("metabolon.respirometry.payments.flag_overdue_payments", return_value=[])
@patch("metabolon.respirometry.metabolize_statements")
def test_spending_degraded_statements_show_error(mock_meta, mock_overdue, mock_missing):
    """Statements with 'error' key are separated out and reported as errors."""
    mock_meta.return_value = [
        {"error": "could not parse PDF"},
    ]
    result = _spending()
    assert result.statements_processed == 0  # degraded not counted as digested
    assert "Error: could not parse PDF" in result.summary


# ---------------------------------------------------------------------------
# _confirm
# ---------------------------------------------------------------------------


@patch("metabolon.respirometry.payments.dequeue_payment")
def test_confirm_removes_pending_payment(mock_dequeue):
    """Successful dequeue returns success with amount and due date."""
    mock_dequeue.return_value = {"amount": 1234.56, "due_date": "2026-04-10"}
    result = _confirm(bank="mox")
    assert isinstance(result, CatabolismConfirmResult)
    assert result.success is True
    assert "MOX" in result.message
    assert "1,234.56" in result.message
    assert "2026-04-10" in result.message


@patch("metabolon.respirometry.payments.dequeue_payment", return_value=None)
def test_confirm_no_pending_payment(mock_dequeue):
    """When nothing to dequeue, return failure message."""
    result = _confirm(bank="ccba")
    assert isinstance(result, CatabolismConfirmResult)
    assert result.success is False
    assert "No pending payment" in result.message
    assert "CCBA" in result.message


@patch("metabolon.respirometry.payments.dequeue_payment")
def test_confirm_bank_case_insensitive(mock_dequeue):
    """Bank identifier is lowercased and stripped before lookup."""
    mock_dequeue.return_value = {"amount": 500.0, "due_date": "2026-05-01"}
    _confirm(bank="  SCB  ")
    mock_dequeue.assert_called_once()
    # Verify the bank arg passed to dequeue is normalized
    call_args = mock_dequeue.call_args
    # dequeue_payment takes (payments_file, bank) — bank is the second positional arg
    assert call_args[0][1] == "scb"


# ---------------------------------------------------------------------------
# catabolism dispatch
# ---------------------------------------------------------------------------


@patch("metabolon.enzymes.catabolism._spending")
def test_catabolism_dispatches_spending(mock_spending):
    """Action 'spending' delegates to _spending with days kwarg."""
    mock_spending.return_value = CatabolismResult(summary="ok")
    result = catabolism(action="spending", days=7)
    mock_spending.assert_called_once_with(days=7)
    assert isinstance(result, CatabolismResult)


@patch("metabolon.enzymes.catabolism._confirm")
def test_catabolism_dispatches_confirm(mock_confirm):
    """Action 'confirm' delegates to _confirm with bank kwarg."""
    mock_confirm.return_value = CatabolismConfirmResult(success=True, message="done")
    result = catabolism(action="confirm", bank="hsbc")
    mock_confirm.assert_called_once_with(bank="hsbc")
    assert isinstance(result, CatabolismConfirmResult)


def test_catabolism_unknown_action():
    """Unknown action returns a failure CatabolismConfirmResult."""
    result = catabolism(action="bogus")
    assert isinstance(result, CatabolismConfirmResult)
    assert result.success is False
    assert "Unknown action" in result.message
    assert "bogus" in result.message
