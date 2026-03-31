from __future__ import annotations

"""Tests for metabolon/enzymes/catabolism.py"""


from unittest.mock import patch

import pytest

from metabolon.enzymes.catabolism import (
    CatabolismConfirmResult,
    CatabolismResult,
    _confirm,
    _spending,
    catabolism,
)

# Imports are lazy (inside function bodies), so we patch at the source module.
_RESPIR = "metabolon.respirometry.metabolize_statements"
_PAYMENTS = "metabolon.respirometry.payments"


# ---------------------------------------------------------------------------
# _spending
# ---------------------------------------------------------------------------

class TestSpending:
    """Tests for _spending helper."""

    @patch(f"{_PAYMENTS}.assess_missing_statements", return_value=[])
    @patch(f"{_PAYMENTS}.flag_overdue_payments", return_value=[])
    @patch(_RESPIR, return_value=[])
    def test_no_statements_no_alerts(
        self, mock_metabolize, mock_flag, mock_missing
    ):
        result = _spending()

        assert isinstance(result, CatabolismResult)
        assert "No new statements found" in result.summary
        assert result.statements_processed == 0
        assert result.total_alerts == 0
        assert result.details == []

    @patch(f"{_PAYMENTS}.assess_missing_statements", return_value=[])
    @patch(f"{_PAYMENTS}.flag_overdue_payments", return_value=[])
    @patch(_RESPIR)
    def test_digested_statements(
        self, mock_metabolize, mock_flag, mock_missing
    ):
        mock_metabolize.return_value = [
            {
                "card": "SCB",
                "statement_date": "2026-03-15",
                "transaction_count": 12,
                "total_hkd": 5432.10,
                "alerts": ["High spend alert"],
            }
        ]

        result = _spending()

        assert result.statements_processed == 1
        assert "SCB" in result.summary
        assert "5,432.10" in result.summary
        assert "12 transactions" in result.summary
        assert result.total_alerts == 1
        assert result.details == mock_metabolize.return_value

    @patch(f"{_PAYMENTS}.assess_missing_statements", return_value=[])
    @patch(f"{_PAYMENTS}.flag_overdue_payments", return_value=[])
    @patch(_RESPIR)
    def test_degraded_statements_show_errors(
        self, mock_metabolize, mock_flag, mock_missing
    ):
        mock_metabolize.return_value = [
            {"error": "Failed to parse PDF"},
        ]

        result = _spending()

        assert result.statements_processed == 0
        assert "Error: Failed to parse PDF" in result.summary

    @patch(f"{_PAYMENTS}.assess_missing_statements", return_value=[])
    @patch(f"{_PAYMENTS}.flag_overdue_payments", return_value=[])
    @patch(_RESPIR)
    def test_mixed_digested_and_degraded(
        self, mock_metabolize, mock_flag, mock_missing
    ):
        mock_metabolize.return_value = [
            {
                "card": "MOX",
                "statement_date": "2026-03-01",
                "transaction_count": 5,
                "total_hkd": 1200.00,
                "alerts": [],
            },
            {"error": " corrupt file"},
        ]

        result = _spending()

        assert result.statements_processed == 1
        assert "MOX" in result.summary
        assert "Error:  corrupt file" in result.summary

    @patch(f"{_PAYMENTS}.assess_missing_statements", return_value=[])
    @patch(f"{_PAYMENTS}.flag_overdue_payments")
    @patch(_RESPIR, return_value=[])
    def test_payment_alerts_included(
        self, mock_metabolize, mock_flag, mock_missing
    ):
        mock_flag.return_value = ["SCB payment overdue!"]

        result = _spending()

        assert "Payment alerts:" in result.summary
        assert "SCB payment overdue!" in result.summary
        assert result.total_alerts == 1

    @patch(f"{_PAYMENTS}.assess_missing_statements")
    @patch(f"{_PAYMENTS}.flag_overdue_payments", return_value=[])
    @patch(_RESPIR, return_value=[])
    def test_missing_statements_included(
        self, mock_metabolize, mock_flag, mock_missing
    ):
        mock_missing.return_value = ["HSBC March statement missing"]

        result = _spending()

        assert "Missing statements:" in result.summary
        assert "HSBC March statement missing" in result.summary

    @patch(f"{_PAYMENTS}.assess_missing_statements", return_value=[])
    @patch(f"{_PAYMENTS}.flag_overdue_payments", return_value=[])
    @patch(_RESPIR)
    def test_payment_action_included(
        self, mock_metabolize, mock_flag, mock_missing
    ):
        mock_metabolize.return_value = [
            {
                "card": "CCBA",
                "statement_date": "2026-02-28",
                "transaction_count": 3,
                "total_hkd": 900.00,
                "alerts": [],
                "payment_action": "Pay CCBA HKD 900.00 by 2026-04-15",
            }
        ]

        result = _spending()

        assert "Pay CCBA HKD 900.00 by 2026-04-15" in result.summary

    @patch(f"{_PAYMENTS}.assess_missing_statements", return_value=[])
    @patch(f"{_PAYMENTS}.flag_overdue_payments", return_value=[])
    @patch(_RESPIR)
    def test_multiple_statements_counted(
        self, mock_metabolize, mock_flag, mock_missing
    ):
        mock_metabolize.return_value = [
            {
                "card": "SCB",
                "statement_date": "2026-03-15",
                "transaction_count": 5,
                "total_hkd": 1000.00,
                "alerts": [],
            },
            {
                "card": "MOX",
                "statement_date": "2026-03-10",
                "transaction_count": 2,
                "total_hkd": 300.00,
                "alerts": ["Low balance"],
            },
        ]

        result = _spending()

        assert result.statements_processed == 2
        assert result.total_alerts == 1
        assert "SCB" in result.summary
        assert "MOX" in result.summary


# ---------------------------------------------------------------------------
# _confirm
# ---------------------------------------------------------------------------

class TestConfirm:
    """Tests for _confirm helper."""

    @patch(f"{_PAYMENTS}.dequeue_payment")
    def test_confirm_removes_payment(self, mock_dequeue):
        mock_dequeue.return_value = {
            "amount": 5432.10,
            "due_date": "2026-04-15",
        }

        result = _confirm("SCB")

        assert isinstance(result, CatabolismConfirmResult)
        assert result.success is True
        assert "SCB" in result.message
        assert "5,432.10" in result.message
        assert "2026-04-15" in result.message

    @patch(f"{_PAYMENTS}.dequeue_payment")
    def test_confirm_no_pending_payment(self, mock_dequeue):
        mock_dequeue.return_value = None

        result = _confirm("mox")

        assert isinstance(result, CatabolismConfirmResult)
        assert result.success is False
        assert "No pending payment" in result.message
        assert "MOX" in result.message

    @patch(f"{_PAYMENTS}.dequeue_payment")
    def test_confirm_bank_case_insensitive(self, mock_dequeue):
        mock_dequeue.return_value = {"amount": 100, "due_date": "2026-05-01"}

        _confirm("  HSBC  ")
        mock_dequeue.assert_called_once()
        # bank is lowercased and stripped before passing to dequeue
        call_args = mock_dequeue.call_args
        # second positional arg is bank string
        assert call_args[0][1] == "hsbc"


# ---------------------------------------------------------------------------
# catabolism dispatch
# ---------------------------------------------------------------------------

class TestCatabolismDispatch:
    """Tests for the top-level catabolism tool dispatch."""

    @patch("metabolon.enzymes.catabolism._spending")
    def test_spending_action(self, mock_spend):
        mock_spend.return_value = CatabolismResult(
            summary="ok", statements_processed=1
        )

        result = catabolism(action="spending", days=60)

        mock_spend.assert_called_once_with(days=60)
        assert isinstance(result, CatabolismResult)

    @patch("metabolon.enzymes.catabolism._confirm")
    def test_confirm_action(self, mock_conf):
        mock_conf.return_value = CatabolismConfirmResult(
            success=True, message="done"
        )

        result = catabolism(action="confirm", bank="mox")

        mock_conf.assert_called_once_with(bank="mox")
        assert result.success is True

    def test_unknown_action(self):
        result = catabolism(action="bogus")

        assert isinstance(result, CatabolismConfirmResult)
        assert result.success is False
        assert "Unknown action" in result.message
        assert "bogus" in result.message
