from __future__ import annotations

"""Comprehensive tests for Mox Credit statement PDF parser.

All external calls and file I/O are mocked for isolation.
"""


from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.respirometry.parsers.mox import (
    _extract_float,
    _extract_metadata,
    _parse_transactions,
    extract_mox,
)
from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


class TestExtractFloat:
    """Tests for the _extract_float helper function."""

    def test_basic_float(self):
        """Extract a basic float value."""
        text = "Amount: 123.45 HKD"
        result = _extract_float(r"Amount: ([\d,]+\.\d{2})", text)
        assert result == 123.45

    def test_float_with_commas(self):
        """Extract float with comma separators."""
        text = "Amount: 1,234,567.89 HKD"
        result = _extract_float(r"Amount: ([\d,]+\.\d{2})", text)
        assert result == 1234567.89

    def test_negative_float(self):
        """Extract negative float value."""
        text = "Balance: -1,234.56 HKD"
        result = _extract_float(r"Balance: (-?[\d,]+\.\d{2})", text)
        assert result == -1234.56

    def test_no_match_returns_zero(self):
        """Return 0.0 when pattern doesn't match."""
        text = "No amount here"
        result = _extract_float(r"Amount: ([\d,]+\.\d{2})", text)
        assert result == 0.0

    def test_empty_text(self):
        """Handle empty text gracefully."""
        result = _extract_float(r"([\d,]+\.\d{2})", "")
        assert result == 0.0


class TestExtractMetadata:
    """Tests for statement metadata extraction."""

    def test_extracts_all_fields(self):
        """Extract period, balance, limits, and dates."""
        text = """1 Aug 2025 - 31 Aug 2025
Total credit limit: 100,000.00
-1,234.56 HKD
Statement balance
500.00 HKD
Minimum amount due
15 Sep 2025
Payment due date"""
        meta = _extract_metadata(text)

        assert meta.bank == "mox"
        assert meta.card == "Mox Credit"
        assert meta.period_start == "1 Aug 2025"
        assert meta.period_end == "31 Aug 2025"
        assert meta.statement_date == "2025-08-31"
        assert meta.balance == -1234.56
        assert meta.credit_limit == 100000.00
        assert meta.minimum_due == 500.00
        assert meta.due_date == "2025-09-15"

    def test_period_with_single_digit_day(self):
        """Parse period dates with single-digit days."""
        text = "1 Aug 2025 - 7 Sep 2025"
        meta = _extract_metadata(text)
        assert meta.period_start == "1 Aug 2025"
        assert meta.period_end == "7 Sep 2025"
        assert meta.statement_date == "2025-09-07"

    def test_missing_period(self):
        """Missing period results in empty strings."""
        text = "Some text without period"
        meta = _extract_metadata(text)
        assert meta.period_start == ""
        assert meta.period_end == ""
        assert meta.statement_date == ""

    def test_missing_credit_limit(self):
        """Missing credit limit defaults to 0.0."""
        text = "1 Aug 2025 - 31 Aug 2025"
        meta = _extract_metadata(text)
        assert meta.credit_limit == 0.0

    def test_missing_balance(self):
        """Missing balance defaults to 0.0."""
        text = "1 Aug 2025 - 31 Aug 2025"
        meta = _extract_metadata(text)
        assert meta.balance == 0.0

    def test_missing_minimum_due(self):
        """Missing minimum due defaults to 0.0."""
        text = "1 Aug 2025 - 31 Aug 2025"
        meta = _extract_metadata(text)
        assert meta.minimum_due == 0.0

    def test_missing_due_date(self):
        """Missing due date results in empty string."""
        text = "1 Aug 2025 - 31 Aug 2025"
        meta = _extract_metadata(text)
        assert meta.due_date == ""

    def test_positive_balance(self):
        """Handle positive balance (credit balance)."""
        text = """1 Aug 2025 - 31 Aug 2025
500.00 HKD
Statement balance"""
        meta = _extract_metadata(text)
        assert meta.balance == 500.00

    def test_empty_text(self):
        """Empty text results in default metadata."""
        meta = _extract_metadata("")
        assert meta.bank == "mox"
        assert meta.card == "Mox Credit"
        assert meta.period_start == ""
        assert meta.balance == 0.0


class TestParseTransactions:
    """Tests for transaction parsing."""

    def test_basic_charge(self):
        """Parse a basic HKD charge transaction."""
        text = "01 Aug 01 AugAMAZON HONG KONG\n-123.45\n2025"
        txns = _parse_transactions(text, "2025")

        assert len(txns) == 1
        assert txns[0].date == "2025-08-01"
        assert "AMAZON" in txns[0].merchant
        assert txns[0].hkd == -123.45
        assert txns[0].currency == "HKD"
        assert txns[0].foreign_amount is None
        assert txns[0].category == ""

    def test_credit_transaction(self):
        """Parse a credit (positive amount)."""
        text = "15 Aug 15 AugREFUND STORE\n50.00\n2025"
        txns = _parse_transactions(text, "2025")

        assert len(txns) == 1
        assert txns[0].hkd == 50.00
        assert txns[0].is_credit

    def test_internal_transfer_excluded(self):
        """Internal transfers are excluded."""
        text = "01 Aug 01 AugMove between own Mox accounts\n-500.00\n2025"
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 0

    def test_cardholder_payment_excluded(self):
        """Payments from cardholder are excluded."""
        text = "01 Aug 01 AugLI HO MING TERRY 2,711.86\n2025"
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 0

    def test_foreign_currency_usd(self):
        """Parse transaction with USD foreign currency."""
        text = "15 Aug 15 AugAMAZON COM\n-123.45\n15.99 USD\n2025"
        txns = _parse_transactions(text, "2025")

        assert len(txns) == 1
        assert txns[0].currency == "USD"
        assert txns[0].foreign_amount == 15.99

    def test_foreign_currency_gbp(self):
        """Parse transaction with GBP foreign currency."""
        text = "15 Aug 15 AugUK STORE\n-200.00\n20.00 GBP\n2025"
        txns = _parse_transactions(text, "2025")

        assert len(txns) == 1
        assert txns[0].currency == "GBP"
        assert txns[0].foreign_amount == 20.00

    def test_foreign_currency_various(self):
        """Various foreign currencies are recognized."""
        currencies = ["USD", "GBP", "EUR", "JPY", "AUD", "CAD", "SGD", "CNY", "TWD", "THB", "KRW"]

        for currency in currencies:
            text = f"15 Aug 15 AugSTORE\n-100.00\n10.00 {currency}\n2025"
            txns = _parse_transactions(text, "2025")
            assert txns[0].currency == currency
            assert txns[0].foreign_amount == 10.00

    def test_merchant_cleaned_removes_trailing_amount(self):
        """Trailing amount is removed from merchant name."""
        text = "15 Aug 15 AugSTORE NAME -123.45\n2025"
        txns = _parse_transactions(text, "2025")
        # The -123.45 at end of first line should be removed
        assert txns[0].merchant == "STORE NAME"

    def test_merchant_cleaned_removes_phone_prefix(self):
        """Phone prefixes like +852 XXXX are removed."""
        text = "15 Aug 15 AugSTORE +852 1234 5678 HK\n-100.00\n2025"
        txns = _parse_transactions(text, "2025")
        assert "+852" not in txns[0].merchant

    def test_merchant_cleaned_removes_country_codes(self):
        """Country codes like USA, GBR, etc. are removed."""
        country_codes = ["USA", "GBR", "IRL", "CAN", "HKG", "AUS", "SGP", "JPN", "NEW", "TWN", "KOR"]

        for code in country_codes:
            text = f"15 Aug 15 AugSTORE {code}\n-100.00\n2025"
            txns = _parse_transactions(text, "2025")
            assert code not in txns[0].merchant

    def test_merchant_cleaned_removes_special_codes(self):
        """Special codes like GOO and II are removed."""
        for code in ["GOO", "II"]:
            text = f"15 Aug 15 AugSTORE {code}\n-100.00\n2025"
            txns = _parse_transactions(text, "2025")
            assert code not in txns[0].merchant

    def test_amount_with_commas(self):
        """Parse amounts with comma separators."""
        text = "15 Aug 15 AugBIG PURCHASE\n-1,234.56\n2025"
        txns = _parse_transactions(text, "2025")
        assert txns[0].hkd == -1234.56

    def test_multiple_transactions(self):
        """Parse multiple transactions in sequence."""
        text = """01 Aug 01 AugSTORE A
-100.00
15 Aug 15 AugSTORE B
-200.00
2025"""
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 2
        assert txns[0].date == "2025-08-01"
        assert txns[1].date == "2025-08-15"

    def test_page_headers_removed(self):
        """Page headers like 'Page X of Y' are removed."""
        text = """Page 1 of 3
01 Aug 01 AugSTORE
-100.00
Page 2 of 3
15 Aug 15 AugOTHER
-200.00
2025"""
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 2

    def test_transaction_header_removed(self):
        """Transaction table header is removed."""
        text = """Activity date
交易⽇期Settlement date
結算⽇期Description
詳情Foreign currency amount
外幣⾦額Amount (HKD)
⾦額  (港幣 )
01 Aug 01 AugSTORE
-100.00
2025"""
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 1

    def test_returns_consumption_events(self):
        """Returns list of ConsumptionEvent objects."""
        text = "01 Aug 01 AugSTORE\n-100.00\n2025"
        txns = _parse_transactions(text, "2025")

        assert len(txns) == 1
        assert isinstance(txns[0], ConsumptionEvent)

    def test_empty_text(self):
        """Empty text results in empty list."""
        txns = _parse_transactions("", "2025")
        assert len(txns) == 0

    def test_whitespace_only(self):
        """Whitespace-only text is handled gracefully."""
        txns = _parse_transactions("   \n\n   ", "2025")
        assert len(txns) == 0

    def test_no_amounts_in_transaction(self):
        """Transaction without amounts is skipped."""
        text = "01 Aug 01 AugSTORE WITHOUT AMOUNT\n2025"
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 0

    def test_is_charge_property(self):
        """is_charge property returns True for negative amounts."""
        text = "01 Aug 01 AugSTORE\n-100.00\n2025"
        txns = _parse_transactions(text, "2025")
        assert txns[0].is_charge is True
        assert txns[0].is_credit is False

    def test_is_credit_property(self):
        """is_credit property returns True for positive amounts."""
        text = "01 Aug 01 AugREFUND\n100.00\n2025"
        txns = _parse_transactions(text, "2025")
        assert txns[0].is_credit is True
        assert txns[0].is_charge is False


class TestExtractMox:
    """Tests for the main extract_mox function."""

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_returns_meta_and_transactions(self, mock_pdf_reader):
        """Returns tuple of (RespirogramMeta, list[ConsumptionEvent])."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = """1 Aug 2025 - 31 Aug 2025
Total credit limit: 100,000.00
-1,000.00 HKD
Statement balance
500.00 HKD
Minimum amount due
15 Sep 2025
Payment due date
01 Aug 01 AugSTORE A
-500.00
15 Aug 15 AugSTORE B
-500.00
"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_mox(Path("/fake/path.pdf"))

        assert isinstance(meta, RespirogramMeta)
        assert isinstance(txns, list)
        assert all(isinstance(t, ConsumptionEvent) for t in txns)

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_balance_validation_success(self, mock_pdf_reader):
        """Passes when parsed total matches statement balance."""
        mock_page = MagicMock()
        # Total transactions = 1000.00, balance = -1000.00
        mock_page.extract_text.return_value = """1 Aug 2025 - 31 Aug 2025
Total credit limit: 100,000.00
-1,000.00 HKD
Statement balance
500.00 HKD
Minimum amount due
15 Sep 2025
Payment due date
01 Aug 01 AugSTORE
-1,000.00
"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        # Should not raise
        meta, txns = extract_mox(Path("/fake/path.pdf"))
        assert meta.balance == -1000.00
        assert sum(t.hkd for t in txns) == -1000.00

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_balance_validation_failure(self, mock_pdf_reader):
        """Raises ValueError when parsed total doesn't match balance."""
        mock_page = MagicMock()
        # Balance says -1000.00 but transactions sum to -100.00
        mock_page.extract_text.return_value = """1 Aug 2025 - 31 Aug 2025
Total credit limit: 100,000.00
-1,000.00 HKD
Statement balance
500.00 HKD
Minimum amount due
15 Sep 2025
Payment due date
01 Aug 01 AugSTORE
-100.00
"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        with pytest.raises(ValueError, match="Balance mismatch"):
            extract_mox(Path("/fake/path.pdf"))

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_multiple_pages_concatenated(self, mock_pdf_reader):
        """Text from multiple pages is concatenated."""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = """1 Aug 2025 - 31 Aug 2025
Total credit limit: 100,000.00
-1,000.00 HKD
Statement balance
500.00 HKD
Minimum amount due
15 Sep 2025
Payment due date
01 Aug 01 AugSTORE A
-500.00
"""
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = """15 Aug 15 AugSTORE B
-500.00
"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_mox(Path("/fake/path.pdf"))

        assert len(txns) == 2

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_stops_at_repayment_calculator(self, mock_pdf_reader):
        """Stops extracting text when 'Repayment calculator' is found."""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = """1 Aug 2025 - 31 Aug 2025
Total credit limit: 100,000.00
-500.00 HKD
Statement balance
500.00 HKD
Minimum amount due
15 Sep 2025
Payment due date
01 Aug 01 AugSTORE
-500.00
"""
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = """Repayment calculator
Some other text that should be ignored
"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_mox(Path("/fake/path.pdf"))

        assert len(txns) == 1

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_stops_at_rate_summary(self, mock_pdf_reader):
        """Stops extracting text when 'Rate summary' is found on a page."""
        # Page 1 has transactions, page 2 has Rate summary and is skipped entirely
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = """1 Aug 2025 - 31 Aug 2025
Total credit limit: 100,000.00
-500.00 HKD
Statement balance
500.00 HKD
Minimum amount due
15 Sep 2025
Payment due date
01 Aug 01 AugSTORE
-500.00
"""
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = """Rate summary
Some other text that should be ignored
"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_mox(Path("/fake/path.pdf"))

        assert len(txns) == 1

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_empty_page_text_handled(self, mock_pdf_reader):
        """Pages returning None for extract_text are handled."""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = """1 Aug 2025 - 31 Aug 2025
Total credit limit: 100,000.00
-500.00 HKD
Statement balance
500.00 HKD
Minimum amount due
15 Sep 2025
Payment due date
01 Aug 01 AugSTORE
-500.00
"""
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = None  # Empty page

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        # Should not raise
        meta, txns = extract_mox(Path("/fake/path.pdf"))
        assert len(txns) == 1

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_balance_tolerance(self, mock_pdf_reader):
        """Balance validation allows 0.02 tolerance for floating point."""
        mock_page = MagicMock()
        # 500.00 + 500.01 = 1000.01, balance = 1000.00, within tolerance
        mock_page.extract_text.return_value = """1 Aug 2025 - 31 Aug 2025
Total credit limit: 100,000.00
-1,000.00 HKD
Statement balance
500.00 HKD
Minimum amount due
15 Sep 2025
Payment due date
01 Aug 01 AugSTORE A
-500.00
15 Aug 15 AugSTORE B
-500.01
"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        # Should not raise - within 0.02 tolerance
        meta, txns = extract_mox(Path("/fake/path.pdf"))

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_transfers_excluded_from_balance_check(self, mock_pdf_reader):
        """Transfer transactions are excluded from balance validation."""
        mock_page = MagicMock()
        # Total spending = 1000.00, balance = -1000.00
        # Transfer should be excluded from balance check
        mock_page.extract_text.return_value = """1 Aug 2025 - 31 Aug 2025
Total credit limit: 100,000.00
-1,000.00 HKD
Statement balance
500.00 HKD
Minimum amount due
15 Sep 2025
Payment due date
01 Aug 01 AugSTORE
-1,000.00
01 Aug 01 AugMove between own Mox accounts
-500.00
"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        # Should not raise - transfer excluded from balance check
        meta, txns = extract_mox(Path("/fake/path.pdf"))
        assert len(txns) == 1  # Transfer is filtered out


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_text_metadata(self):
        """Empty text results in default metadata."""
        meta = _extract_metadata("")
        assert meta.bank == "mox"
        assert meta.card == "Mox Credit"
        assert meta.statement_date == ""
        assert meta.balance == 0.0

    def test_whitespace_only_metadata(self):
        """Whitespace-only text is handled gracefully for metadata."""
        meta = _extract_metadata("   \n\n   \t  ")
        assert meta.statement_date == ""
        assert meta.balance == 0.0

    def test_whitespace_only_transactions(self):
        """Whitespace-only text is handled gracefully for transactions."""
        txns = _parse_transactions("   \n\n   ", "2025")
        assert len(txns) == 0

    def test_malformed_period_date(self):
        """Malformed period dates don't crash extraction."""
        # If period can't be parsed, statement_date will be empty
        text = "Invalid period format"
        meta = _extract_metadata(text)
        assert meta.statement_date == ""

    def test_negative_foreign_amount(self):
        """Negative foreign amounts are parsed correctly."""
        text = "15 Aug 15 AugSTORE\n-100.00\n-15.99 USD\n2025"
        txns = _parse_transactions(text, "2025")
        assert txns[0].foreign_amount == -15.99

    def test_foreign_amount_with_commas(self):
        """HKD amounts with commas are parsed correctly."""
        text = "15 Aug 15 AugSTORE\n-1,234.56\n2025"
        txns = _parse_transactions(text, "2025")
        assert txns[0].hkd == -1234.56

    def test_date_parsing_various_months(self):
        """Various month abbreviations are parsed correctly."""
        months = [
            ("Jan", "01"),
            ("Feb", "02"),
            ("Mar", "03"),
            ("Apr", "04"),
            ("May", "05"),
            ("Jun", "06"),
            ("Jul", "07"),
            ("Aug", "08"),
            ("Sep", "09"),
            ("Oct", "10"),
            ("Nov", "11"),
            ("Dec", "12"),
        ]

        for month_abbr, month_num in months:
            text = f"15 {month_abbr} 15 {month_abbr}STORE\n-100.00\n2025"
            txns = _parse_transactions(text, "2025")
            assert len(txns) == 1
            assert txns[0].date == f"2025-{month_num}-15"

    def test_merchant_with_multiple_cleaning_rules(self):
        """Multiple cleaning rules apply to merchant names."""
        # Merchant with country code and trailing amount
        text = "15 Aug 15 AugSTORE USA -100.00\n2025"
        txns = _parse_transactions(text, "2025")
        assert "USA" not in txns[0].merchant

    def test_filename_stem_property(self):
        """RespirogramMeta has filename_stem property."""
        meta = _extract_metadata("1 Aug 2025 - 31 Aug 2025")
        meta = RespirogramMeta(
            bank="mox",
            card="Mox Credit",
            period_start="1 Aug 2025",
            period_end="31 Aug 2025",
            statement_date="2025-08-31",
            balance=0.0,
            minimum_due=0.0,
            due_date="",
            credit_limit=0.0,
        )
        assert meta.filename_stem == "2025-08-mox"

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_single_transaction_positive_balance(self, mock_pdf_reader):
        """Handle statement with credit balance (positive)."""
        mock_page = MagicMock()
        # Credit balance means money owed to cardholder
        mock_page.extract_text.return_value = """1 Aug 2025 - 31 Aug 2025
Total credit limit: 100,000.00
500.00 HKD
Statement balance
0.00 HKD
Minimum amount due
15 Sep 2025
Payment due date
01 Aug 01 AugREFUND
500.00
"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_mox(Path("/fake/path.pdf"))
        assert meta.balance == 500.00

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_statement_with_no_transactions(self, mock_pdf_reader):
        """Handle statement with no transactions (zero balance)."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = """1 Aug 2025 - 31 Aug 2025
Total credit limit: 100,000.00
0.00 HKD
Statement balance
0.00 HKD
Minimum amount due
15 Sep 2025
Payment due date
"""
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_mox(Path("/fake/path.pdf"))
        assert meta.balance == 0.0
        assert len(txns) == 0
