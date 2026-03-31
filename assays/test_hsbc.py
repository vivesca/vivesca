"""Tests for HSBC statement parser."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from pathlib import Path

from metabolon.respirometry.parsers.hsbc import (
    extract_hsbc,
    _extract_metadata,
    _extract_hsbc_date,
    _parse_transactions,
    _clean_merchant,
)
from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


class TestExtractHsbcDate:
    """Test _extract_hsbc_date function."""

    def test_valid_date(self):
        """Test parsing valid HSBC date format."""
        dt = _extract_hsbc_date("07MAR", 2025)
        assert dt == datetime(2025, 3, 7)

    def test_single_digit_day(self):
        """Test parsing single digit day with leading zero."""
        dt = _extract_hsbc_date("05FEB", 2025)
        assert dt == datetime(2025, 2, 5)

    def test_december_date(self):
        """Test parsing December date."""
        dt = _extract_hsbc_date("25DEC", 2024)
        assert dt == datetime(2024, 12, 25)


class TestCleanMerchant:
    """Test _clean_merchant function."""

    def test_no_cleaning_needed(self):
        """Test merchant name that doesn't need cleaning."""
        assert _clean_merchant("ParknShop") == "ParknShop"

    def test_remove_hongkong_hk(self):
        """Test removing trailing HONGKONGHK."""
        assert _clean_merchant("Starbucks HONGKONGHK") == "Starbucks"

    def test_remove_hongkong_space_hk(self):
        """Test removing trailing HongKong HK."""
        assert _clean_merchant("Citysuper HongKongHK") == "Citysuper"

    def test_remove_uber_hk(self):
        """Test removing UBER.COM/HK/E trailing HK."""
        assert _clean_merchant("UBER.COM/HK/EHK") == ""

    def test_remove_us_trailing(self):
        """Test removing trailing US."""
        assert _clean_merchant("AMAZON.COMUS") == "AMAZON.COM"

    def test_remove_nl_trailing(self):
        """Test removing trailing NL."""
        assert _clean_merchant("SomeStoreNL") == "SomeStore"

    def test_remove_amsterdam_nl(self):
        """Test removing trailing AmsterdamNL."""
        assert _clean_merchant("Booking.comAmsterdamNL") == "Booking.com"

    def test_itunes_com_ie(self):
        """Test preserving ITUNES.COM when removing IE."""
        assert _clean_merchant("ITUNES.COMIE") == "ITUNES.COM"

    def test_cork_ie(self):
        """Test removing IE from CORK."""
        assert _clean_merchant("SomeStore CORKIE") == "SomeStore"

    def test_remove_amazon_bill(self):
        """Test removing trailing Amzn.com/bill."""
        assert _clean_merchant("Amzn.com/bill") == ""


class TestExtractMetadata:
    """Test _extract_metadata function."""

    def test_full_metadata_extraction(self):
        """Test extracting complete metadata from valid text."""
        text = """Statementdate  Statementbalance
07MAR2025HKD26,119.50
HSBCVisaSignatureHKD100,000.00
Total minimum payment due  HKD
300.00
28MAR2025
01FEB28FEB TRANSACTION 123.45
"""
        meta = _extract_metadata(text)

        assert meta.bank == "hsbc"
        assert meta.card == "HSBC Visa Signature"
        assert meta.statement_date == "2025-03-07"
        assert meta.balance == -26119.50
        assert meta.credit_limit == 100000.00
        assert meta.minimum_due == 300.00
        assert meta.due_date == "2025-03-28"
        assert meta.period_start == "01 Feb 2025"
        assert meta.period_end == "07 Mar 2025"

    def test_minimal_metadata_no_transactions(self):
        """Test metadata extraction when no transactions found."""
        text = """Statementdate  Statementbalance
07MAR2025HKD26,119.50
"""
        meta = _extract_metadata(text)

        assert meta.period_start == ""
        assert meta.period_end == ""

    def test_no_match_uses_defaults(self):
        """Test default values when regex doesn't match."""
        text = "some random text"
        meta = _extract_metadata(text)

        assert meta.bank == "hsbc"
        assert meta.statement_date == ""
        assert meta.balance == 0.0
        assert meta.credit_limit == 0.0
        assert meta.minimum_due == 0.0
        assert meta.due_date == ""


class TestParseTransactions:
    """Test _parse_transactions function."""

    def test_single_hkd_transaction(self):
        """Test parsing a simple HKD transaction."""
        text = "01MAR05MAR  PARKnSHOP  123.45"
        txns = _parse_transactions(text, "2025")

        assert len(txns) == 1
        txn = txns[0]
        assert txn.date == "2025-03-05"
        assert txn.merchant == "PARKnSHOP"
        assert txn.currency == "HKD"
        assert txn.foreign_amount is None
        assert txn.hkd == -123.45

    def test_credit_transaction(self):
        """Test parsing a credit transaction (refund)."""
        text = "01MAR05MAR  REFUND FROM STORE  100.00CR"
        txns = _parse_transactions(text, "2025")

        assert len(txns) == 1
        assert txns[0].hkd == 100.00

    def test_fx_transaction(self):
        """Test parsing a foreign currency transaction."""
        text = "01MAR05MAR  AMAZON  USD  100.00  785.50"
        txns = _parse_transactions(text, "2025")

        assert len(txns) == 1
        txn = txns[0]
        assert txn.merchant == "AMAZON"
        assert txn.currency == "USD"
        assert txn.foreign_amount == -100.00
        assert txn.hkd == -785.50

    def test_fx_transaction_credit(self):
        """Test parsing a foreign currency credit transaction."""
        text = "01MAR05MAR  REFUND  GBP  50.00  490.00CR"
        txns = _parse_transactions(text, "2025")

        assert len(txns) == 1
        txn = txns[0]
        assert txn.currency == "GBP"
        assert txn.foreign_amount == 50.00
        assert txn.hkd == 490.00

    def test_skip_prev_balance(self):
        """Test that previous balance line is skipped."""
        text = "01MAR01MAR PREVIOUSBALANCE 10000.00"
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 0

    def test_skip_payment(self):
        """Test that payment line is skipped."""
        text = "01MAR05MAR  PAYMENT-THANKYOU  5000.00"
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 0

    def test_skip_payment_with_space(self):
        """Test that spaced payment line is skipped."""
        text = "01MAR05MAR  PAYMENT - THANK YOU  5000.00"
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 0

    def test_merge_dcc_fee(self):
        """Test that DCC fee is merged with previous transaction."""
        text = """01MAR05MAR  STORE  EUR  100.00  850.00
01MAR05MAR  DCC FEE  10.00
"""
        txns = _parse_transactions(text, "2025")

        assert len(txns) == 1
        # Original -850 + (-10) fee = -860
        assert txns[0].hkd == -860.00

    def test_dcc_fee_without_previous_txn(self):
        """Test DCC fee when no previous transaction (should be skipped)."""
        text = "01MAR05MAR  DCC FEE  10.00"
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 0

    def test_multiple_transactions(self):
        """Test parsing multiple transactions."""
        text = """01FEB03FEB  7-ELEVEN  32.00
02FEB04FEB  MANNINGS  156.50
05FEB06FEB  AIRBNB  EUR  80.00  680.00
"""
        txns = _parse_transactions(text, "2025")

        assert len(txns) == 3
        assert txns[0].hkd == -32.00
        assert txns[1].hkd == -156.50
        assert txns[2].hkd == -680.00
        assert txns[2].currency == "EUR"
        assert txns[2].foreign_amount == -80.00

    def test_skipped_lines_regex(self):
        """Test that continuation lines are skipped (handled in regex)."""
        # These lines should not match _TXN_PAT and get skipped
        lines = [
            "APPLEPAY-",
            "GOOGLEPAY-",
            "OCTOPUSCARD:",
            "CRI:",
            "*EXCHANGERATE:",
        ]
        for line in lines:
            txns = _parse_transactions(line, "2025")
            assert len(txns) == 0

    def test_comma_in_amount(self):
        """Test parsing amounts with thousands separators."""
        text = "01MAR05MAR  AIR TICKET  5,299.00"
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 1
        assert txns[0].hkd == -5299.00

    def test_fx_with_comma(self):
        """Test FX amounts with thousands separators."""
        text = "01MAR05MAR  HOTEL  GBP  1,250.50  12,350.25"
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 1
        assert txns[0].foreign_amount == -1250.50
        assert txns[0].hkd == -12350.25


class TestExtractHsbc:
    """Test extract_hsbc function with mocked PDF."""

    @patch("metabolon.respirometry.parsers.hsbc.PdfReader")
    def test_successful_parsing_balance_ok(self, mock_pdf_reader):
        """Test successful extraction when balance matches."""
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = """Statementdate  Statementbalance
07MAR2025HKD178.45
HSBCVisaSignatureHKD100000.00
Total minimum payment due  HKD
300.00
28MAR2025
01MAR05MAR  PARKnSHOP  123.45
02MAR06MAR  7-ELEVEN  55.00
"""
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_hsbc(Path("test.pdf"))

        assert meta.bank == "hsbc"
        assert len(txns) == 2
        # Total: -178.45 matches balance of -178.45
        sum_spending = sum(t.hkd for t in txns)
        assert abs(sum_spending - meta.balance) < 0.02

    @patch("metabolon.respirometry.parsers.hsbc.PdfReader")
    def test_balance_mismatch_raises(self, mock_pdf_reader):
        """Test that ValueError is raised when balance doesn't match."""
        mock_page = Mock()
        mock_page.extract_text.return_value = """Statementdate  Statementbalance
07MAR2025HKD200.00
01MAR05MAR  PARKnSHOP  100.00
"""
        mock_reader = Mock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        with pytest.raises(ValueError, match="Balance mismatch"):
            extract_hsbc(Path("test.pdf"))

    @patch("metabolon.respirometry.parsers.hsbc.PdfReader")
    def test_multiple_pages(self, mock_pdf_reader):
        """Test extraction from multiple PDF pages."""
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = """Statementdate  Statementbalance
07MAR2025HKD178.45
"""
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = """01MAR05MAR  PARKnSHOP  123.45
02MAR06MAR  7-ELEVEN  55.00
"""
        mock_reader = Mock()
        mock_reader.pages = [mock_page1, mock_page2]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_hsbc(Path("test.pdf"))
        assert len(txns) == 2
        assert sum(t.hkd for t in txns) == pytest.approx(-178.45)


class TestConsumptionEventProperties:
    """Test ConsumptionEvent property methods."""

    def test_is_charge(self):
        """Test is_charge property."""
        txn = ConsumptionEvent(
            date="2025-03-05",
            merchant="Test",
            category="",
            currency="HKD",
            foreign_amount=None,
            hkd=-100.00,
        )
        assert txn.is_charge
        assert not txn.is_credit

    def test_is_credit(self):
        """Test is_credit property."""
        txn = ConsumptionEvent(
            date="2025-03-05",
            merchant="Test",
            category="",
            currency="HKD",
            foreign_amount=None,
            hkd=100.00,
        )
        assert txn.is_credit
        assert not txn.is_charge
