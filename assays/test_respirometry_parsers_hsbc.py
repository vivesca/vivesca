"""Tests for metabolon/respirometry/parsers/hsbc.py."""

from __future__ import annotations

import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from metabolon.respirometry.parsers.hsbc import (
    _clean_merchant,
    _extract_hsbc_date,
    _extract_metadata,
    _parse_transactions,
    extract_hsbc,
)
from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


class TestExtractHsbcDate(unittest.TestCase):
    """Tests for _extract_hsbc_date helper."""

    def test_parses_valid_date(self) -> None:
        result = _extract_hsbc_date("07FEB", 2025)
        expected = datetime(2025, 2, 7)
        self.assertEqual(result, expected)

    def test_parses_march_date(self) -> None:
        result = _extract_hsbc_date("15MAR", 2024)
        expected = datetime(2024, 3, 15)
        self.assertEqual(result, expected)

    def test_invalid_date_raises(self) -> None:
        with self.assertRaises(ValueError):
            _extract_hsbc_date("99XXX", 2025)


class TestCleanMerchant(unittest.TestCase):
    """Tests for _clean_merchant helper."""

    def test_removes_hong_kong_suffix(self) -> None:
        self.assertEqual(_clean_merchant("SHOPNAMEHongKongHK"), "SHOPNAME")
        self.assertEqual(_clean_merchant("SHOPNAMEHONGKONGHK"), "SHOPNAME")

    def test_removes_location_suffixes(self) -> None:
        self.assertEqual(_clean_merchant("STOREKOWLOONBAYHK"), "STORE")
        self.assertEqual(_clean_merchant("CAFETAIKOOSHINGHK"), "CAFE")

    def test_removes_us_suffix(self) -> None:
        self.assertEqual(_clean_merchant("AMAZONUS"), "AMAZON")

    def test_removes_nl_suffix(self) -> None:
        self.assertEqual(_clean_merchant("BOOKINGAMSTERDAMNL"), "BOOKING")

    def test_removes_itunes_ie_suffix(self) -> None:
        result = _clean_merchant("ITUNES.COMIE")
        self.assertEqual(result, "ITUNES.COM")

    def test_removes_amzn_bill_suffix(self) -> None:
        self.assertEqual(_clean_merchant("SHOPAmzn.com/bill"), "SHOP")

    def test_strips_whitespace(self) -> None:
        self.assertEqual(_clean_merchant("  MERCHANT  "), "MERCHANT")

    def test_empty_string_stays_empty(self) -> None:
        self.assertEqual(_clean_merchant(""), "")


class TestExtractMetadata(unittest.TestCase):
    """Tests for _extract_metadata function."""

    def test_extracts_basic_metadata(self) -> None:
        text = """Statementdate  Statementbalance
07MAR2025HKD26,119.50
HSBCVisaSignatureHKD150,000.00
Total minimum payment due  HKD
1,500.00
15APR2025
"""
        meta = _extract_metadata(text)

        self.assertEqual(meta.bank, "hsbc")
        self.assertEqual(meta.card, "HSBC Visa Signature")
        self.assertEqual(meta.statement_date, "2025-03-07")
        self.assertEqual(meta.balance, -26119.50)
        self.assertEqual(meta.credit_limit, 150000.00)
        self.assertEqual(meta.minimum_due, 1500.00)
        self.assertEqual(meta.due_date, "2025-04-15")

    def test_handles_missing_metadata_gracefully(self) -> None:
        """When no matches, returns defaults/zeros."""
        text = "Some random text without patterns"
        meta = _extract_metadata(text)

        self.assertEqual(meta.bank, "hsbc")
        self.assertEqual(meta.card, "HSBC Visa Signature")
        self.assertEqual(meta.statement_date, "")
        self.assertEqual(meta.balance, 0.0)
        self.assertEqual(meta.credit_limit, 0.0)


class TestParseTransactions(unittest.TestCase):
    """Tests for _parse_transactions function."""

    def test_parses_single_charge(self) -> None:
        text = "05FEB07FEBMERCHANTHK  100.00"
        txns = _parse_transactions(text, "2025")

        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0].date, "2025-02-07")
        self.assertEqual(txns[0].merchant, "MERCHANTHK")
        self.assertEqual(txns[0].hkd, -100.00)
        self.assertEqual(txns[0].currency, "HKD")
        self.assertIsNone(txns[0].foreign_amount)

    def test_parses_credit_transaction(self) -> None:
        text = "01FEB05FEBREFUND CR  50.00CR"
        txns = _parse_transactions(text, "2025")

        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0].hkd, 50.00)  # Positive for credit

    def test_parses_foreign_currency_transaction(self) -> None:
        text = "10FEB12FEBSTORE USD 99.00 780.00"
        txns = _parse_transactions(text, "2025")

        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0].currency, "USD")
        self.assertEqual(txns[0].foreign_amount, -99.00)
        self.assertEqual(txns[0].hkd, -780.00)

    def test_skips_previous_balance(self) -> None:
        text = "01JAN01JANPREVIOUSBALANCE  5,000.00"
        txns = _parse_transactions(text, "2025")

        self.assertEqual(len(txns), 0)

    def test_skips_payment_thankyou(self) -> None:
        text = "15FEB15FEBPAYMENT-THANKYOU  3,000.00"
        txns = _parse_transactions(text, "2025")

        self.assertEqual(len(txns), 0)

    def test_handles_dcc_fee(self) -> None:
        """DCC fee should be merged into previous transaction."""
        text = """05FEB07FEBSTORE USD 50.00 400.00
05FEB07FEBCONVDCC FEE  8.00"""
        txns = _parse_transactions(text, "2025")

        self.assertEqual(len(txns), 1)
        # Original -400 minus 8 fee = -408
        self.assertEqual(txns[0].hkd, -408.00)

    def test_skips_card_number_lines(self) -> None:
        text = "01JAN01JAN1234567890123456  100.00"
        txns = _parse_transactions(text, "2025")

        self.assertEqual(len(txns), 0)

    def test_multiple_transactions(self) -> None:
        text = """05FEB07FEBSTORE A  100.00
10FEB12FEBSTORE B  200.00
15FEB17FEBSTORE C  50.00CR"""
        txns = _parse_transactions(text, "2025")

        self.assertEqual(len(txns), 3)
        self.assertEqual(txns[0].hkd, -100.00)
        self.assertEqual(txns[1].hkd, -200.00)
        self.assertEqual(txns[2].hkd, 50.00)


class TestExtractHsbc(unittest.TestCase):
    """Tests for the main extract_hsbc function."""

    def test_extracts_full_statement(self) -> None:
        """Integration test with mocked PdfReader."""
        mock_pdf_text = """Statementdate  Statementbalance
07MAR2025HKD1,000.00
HSBCVisaSignatureHKD150,000.00
Total minimum payment due  HKD
100.00
15APR2025
05FEB07FEBMERCHANT A  500.00
10FEB12FEBMERCHANT B  500.00
"""
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = mock_pdf_text
        mock_reader.pages = [mock_page]

        with patch(
            "metabolon.respirometry.parsers.hsbc.PdfReader", return_value=mock_reader
        ):
            meta, txns = extract_hsbc(Path("/fake/statement.pdf"))

        self.assertEqual(meta.statement_date, "2025-03-07")
        self.assertEqual(meta.balance, -1000.00)
        self.assertEqual(len(txns), 2)
        self.assertEqual(sum(t.hkd for t in txns), -1000.00)

    def test_raises_on_balance_mismatch(self) -> None:
        """Should raise ValueError if parsed total doesn't match statement balance."""
        # Balance shows 2000, but transactions sum to 1000
        mock_pdf_text = """Statementdate  Statementbalance
07MAR2025HKD2,000.00
HSBCVisaSignatureHKD150,000.00
Total minimum payment due  HKD
100.00
15APR2025
05FEB07FEBMERCHANT A  500.00
10FEB12FEBMERCHANT B  500.00
"""
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = mock_pdf_text
        mock_reader.pages = [mock_page]

        with patch(
            "metabolon.respirometry.parsers.hsbc.PdfReader", return_value=mock_reader
        ):
            with self.assertRaises(ValueError) as ctx:
                extract_hsbc(Path("/fake/statement.pdf"))

        self.assertIn("Balance mismatch", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
