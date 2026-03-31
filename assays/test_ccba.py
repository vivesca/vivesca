from __future__ import annotations
"""Comprehensive tests for CCBA eye Credit Card statement PDF parser.

All external calls and file I/O are mocked for isolation.
"""


from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.respirometry.parsers.ccba import (
    _TXN_PAT,
    _clean_merchant,
    _extract_metadata,
    _parse_transactions,
    extract_ccba,
)
from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


class TestTxnPattern:
    """Tests for the transaction regex pattern."""

    def test_basic_transaction(self):
        """Match a basic HKD charge."""
        line = "AMAZON HK HKD 123.45 Sep 15,2025 Sep 15,2025"
        m = _TXN_PAT.match(line)
        assert m is not None
        assert m.group(1) == "AMAZON HK"
        assert m.group(2) == "123.45"
        assert m.group(3) is None  # not CR

    def test_credit_transaction(self):
        """Match a credit (CR) transaction."""
        # CR must be adjacent to the first date (no space between)
        line = "REFUND STORE HKD 50.00 CRSep 10,2025 Sep 10,2025"
        m = _TXN_PAT.match(line)
        assert m is not None
        assert m.group(3) == "CR"

    def test_amount_with_commas(self):
        """Match amounts with comma separators."""
        line = "BIG PURCHASE HK HKD 1,234.56 Sep 01,2025 Sep 01,2025"
        m = _TXN_PAT.match(line)
        assert m is not None
        assert m.group(2) == "1,234.56"

    def test_dates_adjacent_to_amount(self):
        """Dates may be adjacent to amount with no space."""
        line = "STORE HKD 99.99Sep 05,2025 Sep 05,2025"
        m = _TXN_PAT.match(line)
        assert m is not None
        assert m.group(4) == "Sep 05,2025"

    def test_dates_adjacent_to_cr(self):
        """Dates may be adjacent to CR flag."""
        line = "REFUND HKD 25.00 CRSep 05,2025 Sep 05,2025"
        m = _TXN_PAT.match(line)
        assert m is not None
        assert m.group(3) == "CR"
        assert m.group(4) == "Sep 05,2025"

    def test_merchant_with_spaces(self):
        """Merchant names with spaces are captured."""
        line = "THE COFFEE SHOP HK HKD 45.00 Sep 20,2025 Sep 20,2025"
        m = _TXN_PAT.match(line)
        assert m is not None
        assert m.group(1) == "THE COFFEE SHOP HK"

    def test_no_match_without_hkd(self):
        """Pattern requires HKD currency marker."""
        line = "STORE USD 100.00 Sep 01,2025 Sep 01,2025"
        m = _TXN_PAT.match(line)
        assert m is None

    def test_no_match_without_dates(self):
        """Pattern requires two dates."""
        line = "STORE HKD 100.00"
        m = _TXN_PAT.match(line)
        assert m is None


class TestCleanMerchant:
    """Tests for merchant name cleaning."""

    def test_basic_name(self):
        """Basic name passes through unchanged."""
        assert _clean_merchant("AMAZON") == "AMAZON"

    def test_removes_trailing_reference_numbers(self):
        """Long digit strings (10+ digits) are removed."""
        assert _clean_merchant("STORE 12345678901234") == "STORE"
        assert _clean_merchant("MERCHANT 98765432109876") == "MERCHANT"

    def test_keeps_short_numbers(self):
        """Short digit strings (under 10 digits) are kept."""
        assert _clean_merchant("STORE 12345") == "STORE 12345"

    def test_removes_trailing_country_codes(self):
        """Trailing 2-letter country codes are removed."""
        assert _clean_merchant("STORE US") == "STORE"
        assert _clean_merchant("SHOP SG") == "SHOP"
        assert _clean_merchant("MERCHANT HK") == "MERCHANT"

    def test_keeps_country_codes_in_middle(self):
        """Country codes not at the end are kept."""
        assert _clean_merchant("US STORE") == "US STORE"
        assert _clean_merchant("HK SHOP NAME") == "HK SHOP NAME"

    def test_collapses_multiple_spaces(self):
        """Multiple consecutive spaces become single space."""
        assert _clean_merchant("STORE   NAME") == "STORE NAME"
        assert _clean_merchant("A    B    C") == "A B C"

    def test_combined_cleaning(self):
        """Multiple cleaning rules apply together."""
        # Trailing country code + reference number
        assert _clean_merchant("STORE US 123456789012") == "STORE"
        # Multiple spaces + trailing country code
        assert _clean_merchant("BIG   SHOP   HK") == "BIG SHOP"

    def test_strips_whitespace(self):
        """Leading and trailing whitespace is stripped."""
        assert _clean_merchant("  STORE  ") == "STORE"


class TestExtractMetadata:
    """Tests for statement metadata extraction."""

    def test_extracts_all_fields(self):
        """Extract statement date, credit limit, balance, etc."""
        text = """Statement Date 月結單截數日：Sep 07,2025
HKD 49,000.00
HKD 46,978.41
HKD 2,021.59
RMB
4317-8420-0303-6220 HKD 2,021.59 2,021.59 220.00 0.00 Oct 02,2025"""
        meta = _extract_metadata(text)

        assert meta.bank == "ccba"
        assert meta.card == "CCBA eye Credit Card"
        assert meta.statement_date == "2025-09-07"
        assert meta.credit_limit == 49000.00
        assert meta.balance == -2021.59
        assert meta.minimum_due == 220.00
        assert meta.due_date == "2025-10-02"

    def test_fullwidth_colon_in_statement_date(self):
        """Statement date label may use fullwidth colon (U+FF1A)."""
        text = "Statement Date 月結單截數日\uff1aSep 07,2025"
        meta = _extract_metadata(text)
        assert meta.statement_date == "2025-09-07"

    def test_regular_colon_in_statement_date(self):
        """Statement date label may use regular colon."""
        text = "Statement Date 月結單截數日:Sep 07,2025"
        meta = _extract_metadata(text)
        assert meta.statement_date == "2025-09-07"

    def test_missing_statement_date(self):
        """Missing statement date results in empty string."""
        text = "Some text without statement date"
        meta = _extract_metadata(text)
        assert meta.statement_date == ""

    def test_missing_limits_defaults_to_zero(self):
        """Missing credit limits default to 0.0."""
        text = "Some text without limit info"
        meta = _extract_metadata(text)
        assert meta.credit_limit == 0.0
        assert meta.balance == 0.0

    def test_missing_card_summary(self):
        """Missing card summary results in zero min/due."""
        text = "Statement Date 月結單截數日：Sep 07,2025\nHKD 100.00\nHKD 50.00\nHKD 25.00\nRMB"
        meta = _extract_metadata(text)
        assert meta.minimum_due == 0.0
        assert meta.due_date == ""

    def test_period_derived_from_statement_date(self):
        """Period end is derived from statement date."""
        text = "Statement Date 月結單截數日：Sep 07,2025"
        meta = _extract_metadata(text)
        assert meta.period_end == "07 Sep 2025"

    def test_period_start_from_transaction_dates(self):
        """Period start is the earliest transaction date found."""
        text = """
        Statement Date 月結單截數日：Sep 07,2025
        STORE HKD 100.00 Aug 15,2025 Aug 15,2025
        OTHER HKD 50.00 Aug 20,2025 Aug 20,2025
        """
        meta = _extract_metadata(text)
        assert meta.period_start == "15 Aug 2025"


class TestParseTransactions:
    """Tests for transaction parsing."""

    def test_basic_charge(self):
        """Parse a basic charge transaction."""
        text = "AMAZON HK HKD 123.45 Sep 15,2025 Sep 15,2025"
        txns = _parse_transactions(text)

        assert len(txns) == 1
        # Note: "HK" suffix is removed as country code by _clean_merchant
        assert txns[0].merchant == "AMAZON"
        assert txns[0].hkd == -123.45
        assert txns[0].date == "2025-09-15"
        assert txns[0].currency == "HKD"
        assert txns[0].foreign_amount is None

    def test_credit_transaction(self):
        """Parse a credit (positive amount)."""
        # CR must be adjacent to the first date (no space between)
        text = "REFUND STORE HKD 50.00 CRSep 10,2025 Sep 10,2025"
        txns = _parse_transactions(text)

        assert len(txns) == 1
        assert txns[0].hkd == 50.00
        assert txns[0].is_credit

    def test_payment_excluded(self):
        """PPS PAYMENT credits are excluded."""
        # CR must be adjacent to the first date
        text = "PPS PAYMENT - THANK YOU HKD 2,021.59 CRSep 01,2025 Sep 01,2025"
        txns = _parse_transactions(text)
        assert len(txns) == 0

    def test_payment_not_cr_included(self):
        """PPS PAYMENT without CR is included (edge case)."""
        text = "PPS PAYMENT - THANK YOU HKD 100.00 Sep 01,2025 Sep 01,2025"
        txns = _parse_transactions(text)
        assert len(txns) == 1
        assert txns[0].hkd == -100.00

    def test_cross_border_fee_merged(self):
        """Cross-border fees are merged with preceding transaction."""
        text = """
AMAZON HK HKD 100.00 Sep 15,2025 Sep 15,2025
FEE - CROSS-BORDER TXN HKD 1.50 Sep 15,2025 Sep 15,2025
"""
        txns = _parse_transactions(text)

        assert len(txns) == 1
        # Fee is subtracted (more negative = more spent)
        assert txns[0].hkd == -101.50

    def test_cross_border_fee_alternate_name(self):
        """CROSS-BORDER TXN variant is also merged."""
        text = """
STORE HK HKD 200.00 Sep 15,2025 Sep 15,2025
CROSS-BORDER TXN FEE HKD 3.00 Sep 15,2025 Sep 15,2025
"""
        txns = _parse_transactions(text)
        assert len(txns) == 1
        assert txns[0].hkd == -203.00

    def test_cross_border_fee_without_preceding(self):
        """Cross-border fee without preceding txn is skipped."""
        text = "FEE - CROSS-BORDER TXN HKD 1.50 Sep 15,2025 Sep 15,2025"
        txns = _parse_transactions(text)
        assert len(txns) == 0

    def test_foreign_currency_parsed(self):
        """Foreign currency amount is parsed from following line."""
        text = """
AMAZON COM US HKD 123.45 Sep 15,2025 Sep 15,2025
FOREIGN CURRENCY AMOUNT USD 15.00
EXCHANGE RATE 7.80
"""
        txns = _parse_transactions(text)

        assert len(txns) == 1
        assert txns[0].currency == "USD"
        assert txns[0].foreign_amount == -15.00

    def test_foreign_currency_various_currencies(self):
        """Various foreign currencies are recognized."""
        currencies = ["USD", "GBP", "EUR", "JPY", "AUD", "CAD", "SGD", "CNY"]

        for currency in currencies:
            text = f"""
STORE HK HKD 100.00 Sep 15,2025 Sep 15,2025
FOREIGN CURRENCY AMOUNT {currency} 10.00
"""
            txns = _parse_transactions(text)
            assert txns[0].currency == currency
            assert txns[0].foreign_amount == -10.00

    def test_merchant_cleaned(self):
        """Merchant names are cleaned before storage."""
        text = "STORE US 123456789012 HKD 100.00 Sep 15,2025 Sep 15,2025"
        txns = _parse_transactions(text)
        assert txns[0].merchant == "STORE"

    def test_multiple_transactions(self):
        """Parse multiple transactions in sequence."""
        text = """
AMAZON HK HKD 100.00 Sep 15,2025 Sep 15,2025
BOOKSTORE HK HKD 50.00 Sep 16,2025 Sep 16,2025
COFFEE SHOP HK HKD 25.00 Sep 17,2025 Sep 17,2025
"""
        txns = _parse_transactions(text)
        assert len(txns) == 3

    def test_bonus_point_summary_removed(self):
        """Trailing 'Bonus Point Summary...' is stripped from lines."""
        text = "STORE HK HKD 100.00 Sep 15,2025 Sep 15,2025Bonus Point Summary Page 1"
        txns = _parse_transactions(text)
        assert len(txns) == 1
        assert txns[0].merchant == "STORE"

    def test_non_transaction_lines_ignored(self):
        """Lines that don't match transaction pattern are ignored."""
        text = """
Some random text
Another line without transaction data
Page 1 of 3
"""
        txns = _parse_transactions(text)
        assert len(txns) == 0

    def test_returns_consumption_events(self):
        """Returns list of ConsumptionEvent objects."""
        text = "STORE HK HKD 100.00 Sep 15,2025 Sep 15,2025"
        txns = _parse_transactions(text)

        assert len(txns) == 1
        assert isinstance(txns[0], ConsumptionEvent)
        assert txns[0].category == ""  # Categorized later by pipeline


class TestExtractCcba:
    """Tests for the main extract_ccba function."""

    @patch("metabolon.respirometry.parsers.ccba.PdfReader")
    def test_returns_meta_and_transactions(self, mock_pdf_reader):
        """Returns tuple of (RespirogramMeta, list[ConsumptionEvent])."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = """Statement Date 月結單截數日：Sep 07,2025
HKD 49,000.00
HKD 46,978.41
HKD 2,021.59
RMB
4317-8420-0303-6220 HKD 2,021.59 2,021.59 220.00 0.00 Oct 02,2025
AMAZON HK HKD 1,021.59 Sep 15,2025 Sep 15,2025
BOOKSTORE HK HKD 500.00 Sep 16,2025 Sep 16,2025
COFFEE SHOP HKD 500.00 Sep 17,2025 Sep 17,2025"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_ccba(Path("/fake/path.pdf"))

        assert isinstance(meta, RespirogramMeta)
        assert isinstance(txns, list)
        assert all(isinstance(t, ConsumptionEvent) for t in txns)

    @patch("metabolon.respirometry.parsers.ccba.PdfReader")
    def test_balance_validation_success(self, mock_pdf_reader):
        """Passes when parsed total matches statement balance."""
        mock_page = MagicMock()
        # Total transactions = 2021.59, balance = -2021.59
        mock_page.extract_text.return_value = """
Statement Date 月結單截數日：Sep 07,2025

HKD 49,000.00
HKD 46,978.41
HKD 2,021.59
RMB

4317-8420-0303-6220 HKD 2,021.59 2,021.59 220.00 0.00 Oct 02,2025

STORE HK HKD 2,021.59 Sep 15,2025 Sep 15,2025
"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        # Should not raise
        meta, txns = extract_ccba(Path("/fake/path.pdf"))
        assert meta.balance == -2021.59
        assert sum(t.hkd for t in txns) == -2021.59

    @patch("metabolon.respirometry.parsers.ccba.PdfReader")
    def test_balance_validation_failure(self, mock_pdf_reader):
        """Raises ValueError when parsed total doesn't match balance."""
        mock_page = MagicMock()
        # Balance says 2,021.59 but transactions sum to 100.00
        mock_page.extract_text.return_value = """
Statement Date 月結單截數日：Sep 07,2025

HKD 49,000.00
HKD 46,978.41
HKD 2,021.59
RMB

4317-8420-0303-6220 HKD 2,021.59 2,021.59 220.00 0.00 Oct 02,2025

STORE HK HKD 100.00 Sep 15,2025 Sep 15,2025
"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        with pytest.raises(ValueError, match="Balance mismatch"):
            extract_ccba(Path("/fake/path.pdf"))

    @patch("metabolon.respirometry.parsers.ccba.PdfReader")
    def test_multiple_pages_concatenated(self, mock_pdf_reader):
        """Text from multiple pages is concatenated."""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = """Statement Date 月結單截數日：Sep 07,2025
HKD 49,000.00
HKD 46,978.41
HKD 1,000.00
RMB
4317-8420-0303-6220 HKD 1,000.00 1,000.00 100.00 0.00 Oct 02,2025
STORE HK HKD 500.00 Sep 15,2025 Sep 15,2025"""
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "OTHER HK HKD 500.00 Sep 16,2025 Sep 16,2025"
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_ccba(Path("/fake/path.pdf"))

        assert len(txns) == 2
        # Note: "HK" suffix is removed as country code by _clean_merchant
        assert txns[0].merchant == "STORE"
        assert txns[1].merchant == "OTHER"

    @patch("metabolon.respirometry.parsers.ccba.PdfReader")
    def test_empty_page_text_handled(self, mock_pdf_reader):
        """Pages returning None for extract_text are handled."""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = """
Statement Date 月結單截數日：Sep 07,2025

HKD 49,000.00
HKD 46,978.41
HKD 500.00
RMB

4317-8420-0303-6220 HKD 500.00 500.00 50.00 0.00 Oct 02,2025

STORE HK HKD 500.00 Sep 15,2025 Sep 15,2025
"""
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = None  # Empty page

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        # Should not raise
        meta, txns = extract_ccba(Path("/fake/path.pdf"))
        assert len(txns) == 1

    @patch("metabolon.respirometry.parsers.ccba.PdfReader")
    def test_balance_tolerance(self, mock_pdf_reader):
        """Balance validation allows 0.02 tolerance for floating point."""
        mock_page = MagicMock()
        # 100.00 + 100.00 + 0.01 rounding = within tolerance
        mock_page.extract_text.return_value = """
Statement Date 月結單截數日：Sep 07,2025

HKD 49,000.00
HKD 46,900.00
HKD 200.00
RMB

4317-8420-0303-6220 HKD 200.00 200.00 20.00 0.00 Oct 02,2025

STORE1 HK HKD 100.00 Sep 15,2025 Sep 15,2025
STORE2 HK HKD 100.01 Sep 16,2025 Sep 16,2025
"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        # Should not raise - within 0.02 tolerance
        meta, txns = extract_ccba(Path("/fake/path.pdf"))


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_text(self):
        """Empty text results in empty/default metadata and no transactions."""
        meta = _extract_metadata("")
        assert meta.statement_date == ""
        assert meta.balance == 0.0

        txns = _parse_transactions("")
        assert len(txns) == 0

    def test_whitespace_only(self):
        """Whitespace-only text is handled gracefully."""
        meta = _extract_metadata("   \n\n   \t  ")
        assert meta.statement_date == ""

        txns = _parse_transactions("   \n\n   ")
        assert len(txns) == 0

    def test_malformed_dates_ignored(self):
        """Malformed dates in transaction lines don't crash parsing."""
        # The pattern requires valid date format, so this won't match
        text = "STORE HK HKD 100.00 InvalidDate InvalidDate"
        txns = _parse_transactions(text)
        assert len(txns) == 0

    def test_foreign_currency_line_without_match(self):
        """Foreign currency line without matching pattern is skipped."""
        text = """
STORE HK HKD 100.00 Sep 15,2025 Sep 15,2025
FOREIGN CURRENCY AMOUNT XXX 10.00
"""
        txns = _parse_transactions(text)
        # Transaction still parsed, but with default HKD
        assert len(txns) == 1
        assert txns[0].currency == "HKD"
        assert txns[0].foreign_amount is None

    def test_cross_border_fee_case_insensitive(self):
        """Cross-border fee detection is case-insensitive."""
        text = """
STORE HK HKD 100.00 Sep 15,2025 Sep 15,2025
cross-border txn HKD 5.00 Sep 15,2025 Sep 15,2025
"""
        txns = _parse_transactions(text)
        assert len(txns) == 1
        assert txns[0].hkd == -105.00

    def test_payment_case_insensitive(self):
        """PPS PAYMENT detection is case-insensitive."""
        # CR must be adjacent to the first date
        text = "pps payment - thank you HKD 100.00 CRSep 01,2025 Sep 01,2025"
        txns = _parse_transactions(text)
        assert len(txns) == 0
