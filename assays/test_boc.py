from __future__ import annotations

"""Comprehensive tests for BOC Credit Card statement PDF parser.

Tests mock external calls and file I/O to avoid dependency on real PDF fixtures.
"""


from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.respirometry.parsers import boc
from metabolon.respirometry.parsers.boc import (
    _clean_merchant,
    _extract_balance_bf,
    _extract_metadata,
    _extract_odd_cents,
    _extract_payments,
    _parse_short_date,
    _parse_transactions,
    extract_boc,
)
from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta

# =============================================================================
# Sample PDF text fixtures (mocked content)
# =============================================================================

# Balanced sample: transactions sum = balance - balance_bf - payments - odd_cents
# balance=-1500, bf=-100, payments=200, odd=0, expected=-1600
# txns: -1200 + -800 + 400 = -1600 (PPS PAYMENT excluded)
SAMPLE_PDF_TEXT_FULL = """
Card Type:
BOC Taobao World Mastercard

Payment Slip
HKD 200,000.00
HKD 1,500.00
HKD 230.00
27-FEB-2026
24-MAR-2026

BALANCE B/F                     100.00
03-FEB 03-FEB TAobao.COM DEFAULT    HONG KONG     HKG  1,200.00
05-FEB 05-FEB ALIPAY SERVICES  HONG KONG     HKG  800.00
10-FEB 10-FEB PPS PAYMENT                  HONG KONG     HKG  200.00 CR
15-FEB 15-FEB REFUND STORE     HONG KONG     HKG  400.00 CR
ODD CENTS TO NEXT BILL         0.00
CURRENT BALANCE           1,500.00
"""

# Balanced: balance=-100, bf=0, payments=0, odd=0, expected=-100
SAMPLE_PDF_TEXT_MINIMAL = """
Payment Slip
HKD 50,000.00
HKD 100.00
HKD 50.00
15-JAN-2026
05-FEB-2026

BALANCE B/F                     0.00
01-JAN 01-JAN STORE A          HONG KONG     HKG  100.00
"""

SAMPLE_PDF_TEXT_NO_TRANSACTIONS = """
Payment Slip
HKD 100,000.00
HKD 0.00
HKD 0.00
01-MAR-2026
15-MAR-2026

BALANCE B/F                   0.00
CURRENT BALANCE           0.00
"""

SAMPLE_PDF_TEXT_CROSS_YEAR = """
Payment Slip
HKD 100,000.00
HKD 5,000.00
HKD 250.00
15-JAN-2026
05-FEB-2026

BALANCE B/F                   1,000.00
25-DEC 25-DEC LATE DEC STORE   HONG KONG     HKG  500.00
05-JAN 05-JAN EARLY JAN SHOP   HONG KONG     HKG  300.00
"""


# =============================================================================
# Tests for _extract_metadata
# =============================================================================


class TestExtractMetadata:
    """Tests for _extract_metadata function."""

    def test_extracts_all_fields(self):
        """Extract all metadata fields from full sample text."""
        meta = _extract_metadata(SAMPLE_PDF_TEXT_FULL)

        assert meta.bank == "boc"
        assert meta.credit_limit == 200000.00
        assert meta.balance == -1500.00
        assert meta.minimum_due == 230.00
        assert meta.statement_date == "2026-02-27"
        assert meta.due_date == "2026-03-24"
        assert meta.card == "BOC Taobao World Mastercard"

    def test_extracts_credit_limit(self):
        """Extract credit limit as first HKD value."""
        meta = _extract_metadata(SAMPLE_PDF_TEXT_MINIMAL)
        assert meta.credit_limit == 50000.00

    def test_extracts_negative_balance(self):
        """Balance is negative (money owed)."""
        meta = _extract_metadata(SAMPLE_PDF_TEXT_FULL)
        assert meta.balance == -1500.00

    def test_extracts_zero_balance(self):
        """Zero balance when no amount owed."""
        meta = _extract_metadata(SAMPLE_PDF_TEXT_NO_TRANSACTIONS)
        assert meta.balance == 0.0

    def test_extracts_minimum_due(self):
        """Extract minimum payment due."""
        meta = _extract_metadata(SAMPLE_PDF_TEXT_MINIMAL)
        assert meta.minimum_due == 50.00

    def test_extracts_statement_date(self):
        """Statement date in ISO format."""
        meta = _extract_metadata(SAMPLE_PDF_TEXT_FULL)
        assert meta.statement_date == "2026-02-27"

    def test_extracts_due_date(self):
        """Due date in ISO format."""
        meta = _extract_metadata(SAMPLE_PDF_TEXT_MINIMAL)
        assert meta.due_date == "2026-02-05"

    def test_default_card_name(self):
        """Default card name when Card Type not found."""
        text = "Payment Slip\nHKD 1000.00\nHKD 500.00\nHKD 50.00\n"
        meta = _extract_metadata(text)
        assert meta.card == "BOC Credit Card"

    def test_empty_text_returns_defaults(self):
        """Handle empty text with default values."""
        meta = _extract_metadata("")
        assert meta.bank == "boc"
        assert meta.credit_limit == 0.0
        assert meta.balance == 0.0
        assert meta.minimum_due == 0.0
        assert meta.statement_date == ""
        assert meta.due_date == ""

    def test_stops_at_balance_bf(self):
        """Stop parsing at BALANCE B/F marker."""
        text = "Payment Slip\nHKD 10000.00\nHKD 5000.00\nHKD 100.00\nBALANCE B/F 1000.00\nHKD 999.00\n"
        meta = _extract_metadata(text)
        # Should not pick up the HKD 999.00 after BALANCE B/F
        assert meta.credit_limit == 10000.00
        assert meta.minimum_due == 100.00

    def test_stops_at_gift_points(self):
        """Stop parsing at Gift Points marker."""
        text = "Payment Slip\nHKD 10000.00\nHKD 5000.00\nHKD 100.00\nGift Points\nHKD 999.00\n"
        meta = _extract_metadata(text)
        assert meta.minimum_due == 100.00

    def test_period_end_from_statement_date(self):
        """Period end is derived from statement date."""
        meta = _extract_metadata(SAMPLE_PDF_TEXT_FULL)
        assert meta.period_end == "27 Feb 2026"

    def test_handles_comma_in_amounts(self):
        """Handle amounts with comma separators."""
        text = "Payment Slip\nHKD 200,000.00\nHKD 19,613.00\nHKD 1,230.00\n"
        meta = _extract_metadata(text)
        assert meta.credit_limit == 200000.00
        assert meta.balance == -19613.00
        assert meta.minimum_due == 1230.00


# =============================================================================
# Tests for _parse_transactions
# =============================================================================


class TestParseTransactions:
    """Tests for _parse_transactions function."""

    def test_parses_basic_transaction(self):
        """Parse a single transaction line."""
        text = "01-JAN 01-JAN STORE A          HONG KONG     HKG  100.00\n"
        txns = _parse_transactions(text, "2026-01-15")

        assert len(txns) == 1
        assert txns[0].date == "2026-01-01"
        assert txns[0].hkd == -100.00
        assert txns[0].currency == "HKD"

    def test_parses_credit_transaction(self):
        """Parse transaction with CR suffix (credit/refund)."""
        text = "01-JAN 01-JAN REFUND STORE     HONG KONG     HKG  50.00 CR\n"
        txns = _parse_transactions(text, "2026-01-15")

        assert len(txns) == 1
        assert txns[0].hkd == 50.00  # positive = credit

    def test_excludes_pps_payment(self):
        """PPS PAYMENT credits are excluded."""
        text = "10-FEB 10-FEB PPS PAYMENT      HONG KONG     HKG  500.00 CR\n"
        txns = _parse_transactions(text, "2026-02-27")

        assert len(txns) == 0

    def test_includes_non_pps_credits(self):
        """Non-PPS credits (refunds) are included."""
        text = "15-FEB 15-FEB REFUND STORE     HONG KONG     HKG  100.00 CR\n"
        txns = _parse_transactions(text, "2026-02-27")

        assert len(txns) == 1
        assert txns[0].hkd == 100.00

    def test_skips_balance_bf_line(self):
        """BALANCE B/F lines are not parsed as transactions."""
        text = "BALANCE B/F                   1,234.56\n"
        txns = _parse_transactions(text, "2026-02-27")

        assert len(txns) == 0

    def test_skips_current_balance_line(self):
        """CURRENT BALANCE lines are not parsed as transactions."""
        text = "CURRENT BALANCE           19,613.00\n"
        txns = _parse_transactions(text, "2026-02-27")

        assert len(txns) == 0

    def test_skips_odd_cents_line(self):
        """ODD CENTS lines are not parsed as transactions."""
        text = "ODD CENTS TO NEXT BILL         0.04 CR\n"
        txns = _parse_transactions(text, "2026-02-27")

        assert len(txns) == 0

    def test_skips_last_item_line(self):
        """LAST ITEM lines are not parsed as transactions."""
        text = "LAST ITEM\n"
        txns = _parse_transactions(text, "2026-02-27")

        assert len(txns) == 0

    def test_parses_multiple_transactions(self):
        """Parse multiple transaction lines."""
        text = """
01-JAN 01-JAN STORE A          HONG KONG     HKG  100.00
05-JAN 05-JAN STORE B          HONG KONG     HKG  250.50
10-JAN 10-JAN REFUND STORE     HONG KONG     HKG  50.00 CR
"""
        txns = _parse_transactions(text, "2026-01-15")

        assert len(txns) == 3
        assert txns[0].hkd == -100.00
        assert txns[1].hkd == -250.50
        assert txns[2].hkd == 50.00

    def test_handles_comma_in_amounts(self):
        """Handle amounts with comma separators."""
        text = "01-JAN 01-JAN BIG PURCHASE     HONG KONG     HKG  1,234.56\n"
        txns = _parse_transactions(text, "2026-01-15")

        assert txns[0].hkd == -1234.56

    def test_merchant_is_cleaned(self):
        """Merchant name is cleaned (location removed)."""
        text = "01-JAN 01-JAN STORE NAME HONG KONG     HKG  100.00\n"
        txns = _parse_transactions(text, "2026-01-15")

        assert "HONG KONG" not in txns[0].merchant
        assert "HKG" not in txns[0].merchant

    def test_empty_text_returns_empty_list(self):
        """Empty text returns no transactions."""
        txns = _parse_transactions("", "2026-01-15")
        assert txns == []

    def test_no_statement_date_uses_current_year(self):
        """Without statement date, uses current year."""
        text = "01-JAN 01-JAN STORE A          HONG KONG     HKG  100.00\n"
        with patch.object(boc, "datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 1)
            mock_dt.strptime.side_effect = datetime.strptime
            txns = _parse_transactions(text, "")

        assert txns[0].date == "2026-01-01"


# =============================================================================
# Tests for _parse_short_date
# =============================================================================


class TestParseShortDate:
    """Tests for _parse_short_date function."""

    def test_parses_basic_date(self):
        """Parse DD-MON format into ISO date."""
        result = _parse_short_date("15-JAN", 2026, "2026-01-20")
        assert result == "2026-01-15"

    def test_handles_cross_year_transaction(self):
        """Transaction in December for January statement is previous year."""
        result = _parse_short_date("25-DEC", 2026, "2026-01-15")
        assert result == "2025-12-25"

    def test_same_month_transaction(self):
        """Transaction in same month as statement uses statement year."""
        result = _parse_short_date("05-JAN", 2026, "2026-01-15")
        assert result == "2026-01-05"

    def test_no_statement_date(self):
        """Without statement date, uses provided year."""
        result = _parse_short_date("15-JAN", 2026, "")
        assert result == "2026-01-15"

    def test_february_date(self):
        """Handle February dates."""
        result = _parse_short_date("28-FEB", 2026, "2026-02-28")
        assert result == "2026-02-28"

    def test_all_months(self):
        """Test all month abbreviations."""
        month_cases = [
            ("01-JAN", "2026-01-01"),
            ("01-FEB", "2026-02-01"),
            ("01-MAR", "2026-03-01"),
            ("01-APR", "2026-04-01"),
            ("01-MAY", "2026-05-01"),
            ("01-JUN", "2026-06-01"),
            ("01-JUL", "2026-07-01"),
            ("01-AUG", "2026-08-01"),
            ("01-SEP", "2026-09-01"),
            ("01-OCT", "2026-10-01"),
            ("01-NOV", "2026-11-01"),
            ("01-DEC", "2026-12-01"),
        ]
        for date_str, expected in month_cases:
            result = _parse_short_date(date_str, 2026, "2026-12-31")
            assert result == expected, f"Failed for {date_str}"


# =============================================================================
# Tests for _extract_balance_bf
# =============================================================================


class TestExtractBalanceBf:
    """Tests for _extract_balance_bf function."""

    def test_extracts_balance(self):
        """Extract balance brought forward."""
        text = "BALANCE B/F                   1,234.56\n"
        result = _extract_balance_bf(text)
        assert result == -1234.56

    def test_returns_negative(self):
        """Balance B/F is returned as negative (owing)."""
        text = "BALANCE B/F                   500.00\n"
        result = _extract_balance_bf(text)
        assert result == -500.00

    def test_handles_comma(self):
        """Handle amounts with comma separators."""
        text = "BALANCE B/F                  12,345.67\n"
        result = _extract_balance_bf(text)
        assert result == -12345.67

    def test_no_balance_returns_zero(self):
        """Return zero when no balance found."""
        text = "Some other text\n"
        result = _extract_balance_bf(text)
        assert result == 0.0

    def test_empty_text_returns_zero(self):
        """Empty text returns zero."""
        result = _extract_balance_bf("")
        assert result == 0.0


# =============================================================================
# Tests for _extract_payments
# =============================================================================


class TestExtractPayments:
    """Tests for _extract_payments function."""

    def test_extracts_single_payment(self):
        """Extract single PPS payment."""
        text = "10-FEB 10-FEB PPS PAYMENT      HONG KONG     HKG  500.00 CR\n"
        result = _extract_payments(text, "2026-02-27")
        assert result == 500.00

    def test_sums_multiple_payments(self):
        """Sum multiple PPS payments."""
        text = """
10-FEB 10-FEB PPS PAYMENT      HONG KONG     HKG  500.00 CR
15-FEB 15-FEB PPS PAYMENT      HONG KONG     HKG  250.00 CR
"""
        result = _extract_payments(text, "2026-02-27")
        assert result == 750.00

    def test_ignores_non_pps_credits(self):
        """Non-PPS credits are not counted as payments."""
        text = "15-FEB 15-FEB REFUND STORE     HONG KONG     HKG  100.00 CR\n"
        result = _extract_payments(text, "2026-02-27")
        assert result == 0.0

    def test_ignores_pps_without_cr(self):
        """PPS without CR suffix is not counted as payment."""
        text = "10-FEB 10-FEB PPS PAYMENT      HONG KONG     HKG  500.00\n"
        result = _extract_payments(text, "2026-02-27")
        assert result == 0.0

    def test_handles_comma_in_amounts(self):
        """Handle amounts with comma separators."""
        text = "10-FEB 10-FEB PPS PAYMENT      HONG KONG     HKG  1,500.00 CR\n"
        result = _extract_payments(text, "2026-02-27")
        assert result == 1500.00

    def test_no_payments_returns_zero(self):
        """Return zero when no payments found."""
        text = "01-JAN 01-JAN STORE A          HONG KONG     HKG  100.00\n"
        result = _extract_payments(text, "2026-01-15")
        assert result == 0.0

    def test_empty_text_returns_zero(self):
        """Empty text returns zero."""
        result = _extract_payments("", "2026-01-15")
        assert result == 0.0


# =============================================================================
# Tests for _extract_odd_cents
# =============================================================================


class TestExtractOddCents:
    """Tests for _extract_odd_cents function."""

    def test_extracts_odd_cents_credit(self):
        """Extract odd cents with CR suffix (credit)."""
        text = "ODD CENTS TO NEXT BILL         0.04 CR\n"
        result = _extract_odd_cents(text)
        assert result == 0.04

    def test_extracts_odd_cents_debit(self):
        """Extract odd cents without CR (debit)."""
        text = "ODD CENTS TO NEXT BILL         0.04\n"
        result = _extract_odd_cents(text)
        assert result == -0.04

    def test_handles_larger_amounts(self):
        """Handle larger odd cents amounts."""
        text = "ODD CENTS TO NEXT BILL         1.50 CR\n"
        result = _extract_odd_cents(text)
        assert result == 1.50

    def test_no_odd_cents_returns_zero(self):
        """Return zero when no odd cents found."""
        text = "Some other text\n"
        result = _extract_odd_cents(text)
        assert result == 0.0

    def test_empty_text_returns_zero(self):
        """Empty text returns zero."""
        result = _extract_odd_cents("")
        assert result == 0.0


# =============================================================================
# Tests for _clean_merchant
# =============================================================================


class TestCleanMerchant:
    """Tests for _clean_merchant function."""

    def test_removes_hong_kong_hkg(self):
        """Remove 'HONG KONG HKG' suffix."""
        result = _clean_merchant("STORE NAME HONG KONG     HKG")
        assert result == "STORE NAME"

    def test_removes_truncated_hong_kong(self):
        """Remove truncated 'HONG KON HONG KONG' suffix."""
        result = _clean_merchant("STORE NAME HONG KON HONG KONG")
        assert result == "STORE NAME"

    def test_removes_country_codes(self):
        """Remove trailing country codes."""
        result = _clean_merchant("STORE NAME USA")
        assert result == "STORE NAME"

    def test_collapses_multiple_spaces(self):
        """Collapse multiple spaces into single space."""
        result = _clean_merchant("STORE    NAME    HERE")
        assert result == "STORE NAME HERE"

    def test_strips_whitespace(self):
        """Strip leading and trailing whitespace."""
        result = _clean_merchant("  STORE NAME  ")
        assert result == "STORE NAME"

    def test_returns_simple_name_unchanged(self):
        """Simple names are returned unchanged."""
        result = _clean_merchant("SIMPLE STORE")
        assert result == "SIMPLE STORE"

    def test_empty_string_returns_empty(self):
        """Empty string returns empty."""
        result = _clean_merchant("")
        assert result == ""


# =============================================================================
# Tests for extract_boc (integration with mocks)
# =============================================================================


class TestExtractBoc:
    """Tests for extract_boc main function with mocked PdfReader."""

    @patch("metabolon.respirometry.parsers.boc.PdfReader")
    def test_returns_metadata_and_transactions(self, mock_pdf_reader):
        """Returns (metadata, transactions) tuple."""
        # Setup mock
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_PDF_TEXT_FULL
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_boc(Path("/fake/path.pdf"))

        assert isinstance(meta, RespirogramMeta)
        assert isinstance(txns, list)
        assert all(isinstance(t, ConsumptionEvent) for t in txns)

    @patch("metabolon.respirometry.parsers.boc.PdfReader")
    def test_excludes_payments_from_transactions(self, mock_pdf_reader):
        """PPS payments are excluded from transaction list."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_PDF_TEXT_FULL
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        _meta, txns = extract_boc(Path("/fake/path.pdf"))

        merchants = [t.merchant.upper() for t in txns]
        assert not any("PPS PAYMENT" in m for m in merchants)

    @patch("metabolon.respirometry.parsers.boc.PdfReader")
    def test_sets_period_start_from_earliest_transaction(self, mock_pdf_reader):
        """Period start is set from earliest transaction date."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_PDF_TEXT_FULL
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        meta, _txns = extract_boc(Path("/fake/path.pdf"))

        assert meta.period_start == "03 Feb 2026"

    @patch("metabolon.respirometry.parsers.boc.PdfReader")
    def test_balance_mismatch_raises_value_error(self, mock_pdf_reader):
        """Balance validation failure raises ValueError."""
        # Create text where numbers don't add up
        bad_text = """
Payment Slip
HKD 100,000.00
HKD 10,000.00
HKD 500.00
15-JAN-2026
05-FEB-2026

BALANCE B/F                   0.00
01-JAN 01-JAN STORE A          HONG KONG     HKG  100.00
"""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = bad_text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        with pytest.raises(ValueError, match="Balance mismatch"):
            extract_boc(Path("/fake/path.pdf"))

    @patch("metabolon.respirometry.parsers.boc.PdfReader")
    def test_handles_multiple_pages(self, mock_pdf_reader):
        """Concatenates text from multiple PDF pages."""
        # Balanced: balance=-1800, bf=-1000, payments=0, odd=0, expected=-800
        # txns: -500 + -300 = -800
        page1_text = """
Payment Slip
HKD 100,000.00
HKD 1,800.00
HKD 250.00
15-JAN-2026
05-FEB-2026

BALANCE B/F                   1,000.00
01-JAN 01-JAN STORE A          HONG KONG     HKG  500.00
"""
        page2_text = """
05-JAN 05-JAN STORE B          HONG KONG     HKG  300.00
CURRENT BALANCE           1,800.00
"""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = page1_text
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = page2_text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        _meta, txns = extract_boc(Path("/fake/path.pdf"))

        assert len(txns) == 2

    @patch("metabolon.respirometry.parsers.boc.PdfReader")
    def test_handles_none_extract_text(self, mock_pdf_reader):
        """Handle None return from extract_text()."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = None
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        # Should not raise
        meta, _txns = extract_boc(Path("/fake/path.pdf"))
        assert isinstance(meta, RespirogramMeta)

    @patch("metabolon.respirometry.parsers.boc.PdfReader")
    def test_validates_balance_calculation(self, mock_pdf_reader):
        """Balance validation: sum(txns) == balance - balance_bf - payments - odd_cents."""
        # Construct a balanced example
        balanced_text = """
Payment Slip
HKD 100,000.00
HKD 1,300.00
HKD 100.00
15-JAN-2026
05-FEB-2026

BALANCE B/F                   0.00
01-JAN 01-JAN STORE A          HONG KONG     HKG  800.00
05-JAN 05-JAN STORE B          HONG KONG     HKG  500.00
ODD CENTS TO NEXT BILL         0.00
CURRENT BALANCE           1,300.00
"""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = balanced_text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        # Should not raise
        meta, txns = extract_boc(Path("/fake/path.pdf"))
        assert sum(t.hkd for t in txns) == -1300.00
        assert meta.balance == -1300.00


# =============================================================================
# Edge case tests
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_clean_merchant_removes_two_letter_codes(self):
        """Remove 2-letter country codes."""
        result = _clean_merchant("STORE UK")
        assert result == "STORE"

    def test_clean_merchant_removes_three_letter_codes(self):
        """Remove 3-letter country codes."""
        result = _clean_merchant("STORE USA")
        assert result == "STORE"

    def test_parse_transactions_with_pps_lowercase(self):
        """PPS PAYMENT detection is case-insensitive."""
        text = "10-FEB 10-FEB pps payment      HONG KONG     HKG  500.00 CR\n"
        txns = _parse_transactions(text, "2026-02-27")
        # PPS payment should be excluded even with lowercase
        assert len(txns) == 0

    def test_extract_metadata_partial_hkd_values(self):
        """Handle partial HKD values (only credit limit)."""
        text = "Payment Slip\nHKD 10000.00\n"
        meta = _extract_metadata(text)
        assert meta.credit_limit == 10000.00
        assert meta.balance == 0.0
        assert meta.minimum_due == 0.0

    def test_cross_year_date_inference(self):
        """Transaction in Dec for Jan statement uses previous year."""
        text = """
Payment Slip
HKD 100,000.00
HKD 500.00
HKD 50.00
15-JAN-2026
05-FEB-2026

BALANCE B/F                   0.00
25-DEC 25-DEC STORE A          HONG KONG     HKG  500.00
"""
        txns = _parse_transactions(text, "2026-01-15")
        assert txns[0].date == "2025-12-25"

    @patch("metabolon.respirometry.parsers.boc.PdfReader")
    def test_empty_transactions_list(self, mock_pdf_reader):
        """Handle statement with no transactions."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = SAMPLE_PDF_TEXT_NO_TRANSACTIONS
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_boc(Path("/fake/path.pdf"))
        assert txns == []
        assert meta.period_start == ""


# =============================================================================
# Transaction pattern matching tests
# =============================================================================


class TestTransactionPattern:
    """Tests for transaction line regex pattern matching."""

    def test_valid_transaction_format(self):
        """Valid transaction format is matched."""
        text = "01-JAN 01-JAN MERCHANT NAME    HONG KONG     HKG  100.00\n"
        txns = _parse_transactions(text, "2026-01-15")
        assert len(txns) == 1

    def test_valid_transaction_with_cr(self):
        """Valid transaction with CR suffix is matched."""
        text = "01-JAN 01-JAN MERCHANT NAME    HONG KONG     HKG  100.00 CR\n"
        txns = _parse_transactions(text, "2026-01-15")
        assert len(txns) == 1
        assert txns[0].hkd == 100.00

    def test_invalid_date_format_not_matched(self):
        """Invalid date format is not matched."""
        text = "2026-01-01 2026-01-01 MERCHANT NAME    HKG  100.00\n"
        txns = _parse_transactions(text, "2026-01-15")
        assert len(txns) == 0

    def test_missing_amount_not_matched(self):
        """Missing amount is not matched."""
        text = "01-JAN 01-JAN MERCHANT NAME    HKG\n"
        txns = _parse_transactions(text, "2026-01-15")
        assert len(txns) == 0

    def test_amount_without_decimals_not_matched(self):
        """Amount without decimal places is not matched."""
        text = "01-JAN 01-JAN MERCHANT NAME    HKG  100\n"
        txns = _parse_transactions(text, "2026-01-15")
        assert len(txns) == 0
