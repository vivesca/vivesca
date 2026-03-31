"""Tests for metabolon/enzymes/catabolism.py -- _spending and _confirm internals."""

from unittest.mock import patch

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
def test_spending_no_results(mock_meta, mock_flag, mock_missing):
    result = _spending()
    assert isinstance(result, CatabolismResult)
    assert "No new statements" in result.summary
    assert "All cards accounted" in result.summary
    assert result.statements_processed == 0
    assert result.total_alerts == 0
    assert result.details == []


@patch("metabolon.respirometry.payments.assess_missing_statements", return_value=[])
@patch("metabolon.respirometry.payments.flag_overdue_payments", return_value=[])
@patch("metabolon.respirometry.metabolize_statements")
def test_spending_single_digested(mock_meta, mock_flag, mock_missing):
    mock_meta.return_value = [
        {
            "card": "CCBA",
            "statement_date": "2026-03-07",
            "transaction_count": 12,
            "total_hkd": 6107.99,
            "alerts": [],
        },
    ]
    result = _spending()
    assert result.statements_processed == 1
    assert "CCBA" in result.summary
    assert "6,107.99" in result.summary
    assert "12 transactions" in result.summary
    assert "2026-03-07" in result.summary


@patch("metabolon.respirometry.payments.assess_missing_statements", return_value=[])
@patch("metabolon.respirometry.payments.flag_overdue_payments", return_value=[])
@patch("metabolon.respirometry.metabolize_statements")
def test_spending_multiple_digested(mock_meta, mock_flag, mock_missing):
    mock_meta.return_value = [
        {
            "card": "CCBA",
            "statement_date": "2026-03-07",
            "transaction_count": 12,
            "total_hkd": 6107.99,
            "alerts": [],
        },
        {
            "card": "MOX",
            "statement_date": "2026-03-15",
            "transaction_count": 5,
            "total_hkd": 2500.00,
            "alerts": [],
        },
    ]
    result = _spending()
    assert result.statements_processed == 2
    assert "CCBA" in result.summary
    assert "MOX" in result.summary


@patch("metabolon.respirometry.payments.assess_missing_statements", return_value=[])
@patch("metabolon.respirometry.payments.flag_overdue_payments", return_value=[])
@patch("metabolon.respirometry.metabolize_statements")
def test_spending_error_only(mock_meta, mock_flag, mock_missing):
    mock_meta.return_value = [{"error": "Failed to parse CCBA statement"}]
    result = _spending()
    assert "Error:" in result.summary
    assert "Failed to parse CCBA statement" in result.summary
    assert result.statements_processed == 0


@patch("metabolon.respirometry.payments.assess_missing_statements", return_value=[])
@patch("metabolon.respirometry.payments.flag_overdue_payments", return_value=[])
@patch("metabolon.respirometry.metabolize_statements")
def test_spending_mixed_ok_and_error(mock_meta, mock_flag, mock_missing):
    mock_meta.return_value = [
        {
            "card": "CCBA",
            "statement_date": "2026-03-07",
            "transaction_count": 12,
            "total_hkd": 6107.99,
            "alerts": [],
        },
        {"error": "Failed SCB parse"},
    ]
    result = _spending()
    assert result.statements_processed == 1
    assert "CCBA" in result.summary
    assert "Error:" in result.summary
    assert "Failed SCB parse" in result.summary


@patch("metabolon.respirometry.payments.assess_missing_statements", return_value=[])
@patch("metabolon.respirometry.payments.flag_overdue_payments", return_value=[])
@patch("metabolon.respirometry.metabolize_statements")
def test_spending_payment_action(mock_meta, mock_flag, mock_missing):
    mock_meta.return_value = [
        {
            "card": "CCBA",
            "statement_date": "2026-03-07",
            "transaction_count": 12,
            "total_hkd": 6107.99,
            "alerts": [],
            "payment_action": "Queued payment: CCBA HKD 6,107.99 due 2026-04-01",
        },
    ]
    result = _spending()
    assert "Queued payment" in result.summary


@patch("metabolon.respirometry.payments.assess_missing_statements", return_value=[])
@patch("metabolon.respirometry.payments.flag_overdue_payments")
@patch("metabolon.respirometry.metabolize_statements", return_value=[])
def test_spending_payment_alerts_only(mock_meta, mock_flag, mock_missing):
    mock_flag.return_value = ["CCBA payment due in 2 days"]
    result = _spending()
    assert "Payment alerts:" in result.summary
    assert "CCBA payment due" in result.summary
    assert result.total_alerts == 1


@patch("metabolon.respirometry.payments.assess_missing_statements")
@patch("metabolon.respirometry.payments.flag_overdue_payments", return_value=[])
@patch("metabolon.respirometry.metabolize_statements", return_value=[])
def test_spending_missing_statements_only(mock_meta, mock_flag, mock_missing):
    mock_missing.return_value = ["SCB statement missing for March"]
    result = _spending()
    assert "Missing statements:" in result.summary
    assert "SCB statement missing" in result.summary
    assert result.total_alerts == 1


@patch("metabolon.respirometry.payments.assess_missing_statements")
@patch("metabolon.respirometry.payments.flag_overdue_payments")
@patch("metabolon.respirometry.metabolize_statements", return_value=[])
def test_spending_payment_and_missing_alerts(mock_meta, mock_flag, mock_missing):
    mock_flag.return_value = ["CCBA due soon"]
    mock_missing.return_value = ["SCB missing"]
    result = _spending()
    assert "Payment alerts:" in result.summary
    assert "Missing statements:" in result.summary
    assert result.total_alerts == 2


@patch("metabolon.respirometry.payments.assess_missing_statements", return_value=[])
@patch("metabolon.respirometry.payments.flag_overdue_payments", return_value=[])
@patch("metabolon.respirometry.metabolize_statements")
def test_spending_alerts_in_digested(mock_meta, mock_flag, mock_missing):
    mock_meta.return_value = [
        {
            "card": "MOX",
            "statement_date": "2026-03-15",
            "transaction_count": 5,
            "total_hkd": 2500.00,
            "alerts": ["Large transaction: HKD 1,500"],
        },
    ]
    result = _spending()
    assert result.total_alerts >= 1


@patch("metabolon.respirometry.payments.assess_missing_statements", return_value=[])
@patch("metabolon.respirometry.payments.flag_overdue_payments", return_value=[])
@patch("metabolon.respirometry.metabolize_statements", return_value=[])
def test_spending_no_results_but_payment_alerts(mock_meta, mock_flag, mock_missing):
    """When no statements but there are payment alerts, should NOT say 'No new statements'."""
    mock_flag.return_value = ["MOX overdue"]
    result = _spending()
    assert "Payment alerts:" in result.summary
    # The "No new statements" branch should be skipped since payment_alerts is truthy
    lines = result.summary.split("\n")
    assert "No new statements found." not in lines


# ---------------------------------------------------------------------------
# _confirm
# ---------------------------------------------------------------------------


@patch("metabolon.respirometry.payments.dequeue_payment")
def test_confirm_success(mock_dequeue):
    mock_dequeue.return_value = {
        "bank": "ccba",
        "amount": 6107.99,
        "due_date": "2026-04-01",
    }
    result = _confirm("CCBA")
    assert isinstance(result, CatabolismConfirmResult)
    assert result.success is True
    assert "CCBA" in result.message
    assert "6,107.99" in result.message
    assert "2026-04-01" in result.message
    assert "Removed from pending" in result.message


@patch("metabolon.respirometry.payments.dequeue_payment")
def test_confirm_not_found(mock_dequeue):
    mock_dequeue.return_value = None
    result = _confirm("nonexistent")
    assert isinstance(result, CatabolismConfirmResult)
    assert result.success is False
    assert "No pending payment" in result.message
    assert "NONEXISTENT" in result.message


@patch("metabolon.respirometry.payments.dequeue_payment")
def test_confirm_bank_normalised(mock_dequeue):
    mock_dequeue.return_value = {"bank": "mox", "amount": 1000.00, "due_date": "2026-04-15"}
    _confirm("  MOX  ")
    # dequeue_payment receives lowercased, stripped bank name
    args, _kwargs = mock_dequeue.call_args
    assert args[1] == "mox"


@patch("metabolon.respirometry.payments.dequeue_payment")
def test_confirm_missing_fields_uses_defaults(mock_dequeue):
    mock_dequeue.return_value = {"bank": "hsbc"}
    result = _confirm("hsbc")
    assert result.success is True
    assert "0.00" in result.message
    assert "unknown" in result.message


# ---------------------------------------------------------------------------
# catabolism dispatch
# ---------------------------------------------------------------------------


def test_catabolism_unknown_action():
    result = catabolism(action="bogus")
    assert isinstance(result, CatabolismConfirmResult)
    assert result.success is False
    assert "Unknown action" in result.message
    assert "bogus" in result.message


@patch("metabolon.enzymes.catabolism._spending")
def test_catabolism_spending_passes_days(mock_spending):
    expected = CatabolismResult(summary="test", statements_processed=1)
    mock_spending.return_value = expected
    result = catabolism(action="spending", days=90)
    mock_spending.assert_called_once_with(days=90)
    assert result is expected


@patch("metabolon.enzymes.catabolism._spending")
def test_catabolism_spending_default_days(mock_spending):
    mock_spending.return_value = CatabolismResult(summary="ok")
    catabolism(action="spending")
    mock_spending.assert_called_once_with(days=30)


@patch("metabolon.enzymes.catabolism._confirm")
def test_catabolism_confirm_passes_bank(mock_confirm):
    expected = CatabolismConfirmResult(success=True, message="done")
    mock_confirm.return_value = expected
    result = catabolism(action="confirm", bank="scb")
    mock_confirm.assert_called_once_with(bank="scb")
    assert result is expected


# ---------------------------------------------------------------------------
# Model construction
# ---------------------------------------------------------------------------


def test_catabolism_result_defaults():
    r = CatabolismResult(summary="hello")
    assert r.summary == "hello"
    assert r.statements_processed == 0
    assert r.total_alerts == 0
    assert r.details == []


def test_catabolism_result_with_values():
    r = CatabolismResult(
        summary="test",
        statements_processed=3,
        total_alerts=2,
        details=[{"card": "CCBA"}, {"card": "MOX"}],
    )
    assert r.statements_processed == 3
    assert r.total_alerts == 2
    assert len(r.details) == 2
