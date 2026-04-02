"""Tests for metabolon.respirometry.parsers.boc."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from metabolon.respirometry.parsers.boc import (
    extract_boc,
    _extract_metadata,
    _parse_transactions,
    _parse_short_date,
    _extract_balance_bf,
    _extract_payments,
    _extract_odd_cents,
    _clean_merchant,
)
from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pdf_text(overrides: str | None = None) -> str:
    """Return a minimal but valid BOC statement text block."""
    base = (
        "Payment Slip\n"
        "HKD 80,000.00\n"
        "HKD 4,282.86\n"
        "HKD 500.00\n"
        "15-MAR-2025\n"
        "05-APR-2025\n"
        "Card Type:\n"
        "BOC Visa Platinum\n"
        "BALANCE B/F       5,000.00\n"
        "01-MAR 01-MAR STARBUCKS HONG KONG     HKG 48.00\n"
        "02-MAR 02-MAR SUPERMARKET HONG KONG     HKG 234.56\n"
        "03-MAR 03-MAR PPS PAYMENT           1,000.00CR\n"
        "CURRENT BALANCE\n"
        "ODD CENTS TO NEXT BILL 0.30\n"
    )
    if overrides:
        return overrides
    return base


def _mock_pdf_reader(text: str) -> MagicMock:
    """Return a mock PdfReader whose pages yield *text*."""
    page = MagicMock()
    page.extract_text.return_value = text
    reader = MagicMock()
    reader.pages = [page]
    return reader


# ---------------------------------------------------------------------------
# Tests: _clean_merchant
# ---------------------------------------------------------------------------

class TestCleanMerchant:
    def test_strips_trailing_location(self):
        assert _clean_merchant("STARBUCKS HONG KONG     HKG") == "STARBUCKS"

    def test_strips_truncated_location(self):
        assert _clean_merchant("COFFEE HONG KON HONG KONG") == "COFFEE"

    def test_strips_trailing_country_code(self):
        assert _clean_merchant("AMAZON  JP") == "AMAZON"

    def test_collapses_multiple_spaces(self):
        assert _clean_merchant("A   B   C") == "A B C"

    def test_strips_whitespace(self):
        assert _clean_merchant("  SHOP  ") == "SHOP"


# ---------------------------------------------------------------------------
# Tests: _parse_short_date
# ---------------------------------------------------------------------------

class TestParseShortDate:
    def test_same_year(self):
        result = _parse_short_date("15-MAR", 2025, "2025-03-15")
        assert result == "2025-03-15"

    def test_wraps_to_previous_year(self):
        """Dec transaction on a Jan statement → previous year."""
        result = _parse_short_date("20-DEC", 2025, "2025-01-15")
        assert result == "2024-12-20"

    def test_no_statement_date_uses_current_year(self):
        result = _parse_short_date("10-JUN", 2025, "")
        assert result == "2025-06-10"


# ---------------------------------------------------------------------------
# Tests: _extract_balance_bf / _extract_odd_cents / _extract_payments
# ---------------------------------------------------------------------------

class TestExtractionHelpers:
    def test_balance_bf_found(self):
        assert _extract_balance_bf("BALANCE B/F       5,000.00") == -5000.0

    def test_balance_bf_missing(self):
        assert _extract_balance_bf("no balance here") == 0.0

    def test_odd_cents_credit(self):
        assert _extract_odd_cents("ODD CENTS TO NEXT BILL 0.30CR") == 0.30

    def test_odd_cents_debit(self):
        assert _extract_odd_cents("ODD CENTS TO NEXT BILL 1.50") == -1.50

    def test_odd_cents_missing(self):
        assert _extract_odd_cents("nothing here") == 0.0

    def test_payments_sums_pps(self):
        text = "03-MAR 03-MAR PPS PAYMENT           1,000.00CR\n"
        assert _extract_payments(text, "2025-03-15") == 1000.0

    def test_payments_ignores_non_pps(self):
        text = "01-MAR 01-MAR STARBUCKS HONG KONG     HKG 48.00\n"
        assert _extract_payments(text, "2025-03-15") == 0.0


# ---------------------------------------------------------------------------
# Tests: _extract_metadata
# ---------------------------------------------------------------------------

class TestExtractMetadata:
    def test_parses_payment_slip_values(self):
        text = _make_pdf_text()
        meta = _extract_metadata(text)
        assert meta.bank == "boc"
        assert meta.credit_limit == 80000.0
        assert meta.balance == -4282.86
        assert meta.minimum_due == 500.0
        assert meta.statement_date == "2025-03-15"
        assert meta.due_date == "2025-04-05"
        assert meta.card == "BOC Visa Platinum"


# ---------------------------------------------------------------------------
# Tests: _parse_transactions
# ---------------------------------------------------------------------------

class TestParseTransactions:
    def test_excludes_pps_payment(self):
        text = _make_pdf_text()
        txns = _parse_transactions(text, "2025-03-15")
        merchants = [t.merchant for t in txns]
        assert "STARBUCKS" in merchants
        assert "SUPERMARKET" in merchants
        assert not any("PPS" in m for m in merchants)

    def test_amounts_negative_for_debits(self):
        text = _make_pdf_text()
        txns = _parse_transactions(text, "2025-03-15")
        starbucks = [t for t in txns if "STARBUCKS" in t.merchant][0]
        assert starbucks.hkd == -48.0
        assert starbucks.date == "2025-03-01"
        assert starbucks.currency == "HKD"


# ---------------------------------------------------------------------------
# Tests: extract_boc (integration with mocked PdfReader)
# ---------------------------------------------------------------------------

class TestExtractBoc:
    @patch("metabolon.respirometry.parsers.boc.PdfReader")
    def test_full_parse(self, mock_pdf_cls):
        text = _make_pdf_text()
        mock_pdf_cls.return_value = _mock_pdf_reader(text)

        meta, txns = extract_boc(Path("/fake/statement.pdf"))

        assert isinstance(meta, RespirogramMeta)
        assert all(isinstance(t, ConsumptionEvent) for t in txns)
        assert meta.bank == "boc"
        assert len(txns) == 2  # STARBUCKS + SUPERMARKET, PPS excluded
        total_spending = sum(t.hkd for t in txns)
        assert total_spending == -(48.0 + 234.56)

    @patch("metabolon.respirometry.parsers.boc.PdfReader")
    def test_balance_mismatch_raises(self, mock_pdf_cls):
        """If amounts don't add up, ValueError is raised."""
        bad_text = (
            "Payment Slip\n"
            "HKD 80,000.00\n"
            "HKD 99,999.00\n"   # wildly wrong balance
            "HKD 500.00\n"
            "15-MAR-2025\n"
            "05-APR-2025\n"
            "BALANCE B/F       5,000.00\n"
            "01-MAR 01-MAR STARBUCKS HONG KONG     HKG 48.00\n"
            "CURRENT BALANCE\n"
            "ODD CENTS TO NEXT BILL 0.00\n"
        )
        mock_pdf_cls.return_value = _mock_pdf_reader(bad_text)

        with pytest.raises(ValueError, match="Balance mismatch"):
            extract_boc(Path("/fake/bad.pdf"))
