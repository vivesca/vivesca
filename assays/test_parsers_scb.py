"""Tests for metabolon.respirometry.parsers.scb."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from metabolon.respirometry.parsers.scb import (
    _clean_merchant,
    _extract_metadata,
    _extract_purchases_total,
    _parse_transactions,
    extract_scb,
)
from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


# ---------------------------------------------------------------------------
# Sample statement text fragments (mimic real SCB PDF output)
# ---------------------------------------------------------------------------
SAMPLE_STATEMENT = (
    "Statement Date 15/03/2025\n"
    "Payment Due Date 05/04/2025\n"
    "SMART CREDIT CARD 106,000 26,345.39\n"
    "STATEMENT BALANCE 12,345.67\n"
    "MINIMUM PAYMENT DUE 1,234.56\n"
    "Previous Payments Credits Purchases Cash Charges Balance\n"
    "15,000.00 5,000.00 0.00 3,456.78 100.00 50.00 3,606.78\n"
    "Transaction Ref 1 AMAZON HONG KONG HK\n"
    "\xa0\xa0\n"
    "Transaction Ref 2 STARBUCKS CENTRAL HK\n"
    "\xa0\xa0\n"
    "03/10  120.50\n"
    "03/12  200.28\n"
)

SAMPLE_STATEMENT_ALT_DATE = (
    "Statement Date:15 Mar 2025\n"
    "Payment Due Date:5 Apr 2025\n"
    "SMART CREDIT CARD 50,000 500.00\n"
    "STATEMENT BALANCE 1,234.00\n"
    "MINIMUM PAYMENT DUE 200.00\n"
    "Previous Payments Credits Purchases Cash Charges Balance\n"
    "5,000.00 2,000.00 0.00 1,234.00 0.00 0.00 1,234.00\n"
)


class TestCleanMerchant:
    """Tests for _clean_merchant helper."""

    def test_strips_hong_kong_location(self):
        assert _clean_merchant("AMAZON HONG KONG HK") == "AMAZON"

    def test_strips_central_location(self):
        assert _clean_merchant("STARBUCKS CENTRAL HK") == "STARBUCKS"

    def test_strips_country_code_alone(self):
        assert _clean_merchant("FOOBAR  SG") == "FOOBAR"

    def test_collapses_multiple_spaces(self):
        assert _clean_merchant("HELLO   WORLD") == "HELLO WORLD"

    def test_strips_known_website_domains(self):
        assert _clean_merchant("ITUNES.COM/BILL IE") == "ITUNES.COM/BILL"

    def test_preserves_simple_name(self):
        assert _clean_merchant("SIMPLE MERCHANT") == "SIMPLE MERCHANT"


class TestExtractMetadata:
    """Tests for _extract_metadata helper."""

    def test_extracts_statement_date_dd_mm_yyyy(self):
        meta = _extract_metadata(SAMPLE_STATEMENT)
        assert meta.statement_date == "2025-03-15"

    def test_extracts_due_date_dd_mm_yyyy(self):
        meta = _extract_metadata(SAMPLE_STATEMENT)
        assert meta.due_date == "2025-04-05"

    def test_extracts_credit_limit(self):
        meta = _extract_metadata(SAMPLE_STATEMENT)
        assert meta.credit_limit == 106000.0

    def test_extracts_balance_negative(self):
        meta = _extract_metadata(SAMPLE_STATEMENT)
        assert meta.balance == -12345.67

    def test_extracts_minimum_due(self):
        meta = _extract_metadata(SAMPLE_STATEMENT)
        assert meta.minimum_due == 1234.56

    def test_extracts_alt_date_format(self):
        meta = _extract_metadata(SAMPLE_STATEMENT_ALT_DATE)
        assert meta.statement_date == "2025-03-15"
        assert meta.due_date == "2025-04-05"

    def test_bank_and_card_fields(self):
        meta = _extract_metadata(SAMPLE_STATEMENT)
        assert meta.bank == "scb"
        assert meta.card == "SCB Smart Credit Card"


class TestExtractPurchasesTotal:
    """Tests for _extract_purchases_total helper."""

    def test_extracts_purchases_from_summary(self):
        total = _extract_purchases_total(SAMPLE_STATEMENT)
        assert total == 3456.78

    def test_extracts_purchases_alt_statement(self):
        total = _extract_purchases_total(SAMPLE_STATEMENT_ALT_DATE)
        assert total == 1234.00

    def test_returns_zero_when_no_match(self):
        assert _extract_purchases_total("no summary here") == 0.0


class TestParseTransactions:
    """Tests for _parse_transactions helper."""

    def test_parses_charge_amounts(self):
        txns = _parse_transactions(SAMPLE_STATEMENT, "2025")
        amounts = [t.hkd for t in txns]
        # charges are negative
        assert all(a < 0 for a in amounts)

    def test_correct_number_of_charges(self):
        txns = _parse_transactions(SAMPLE_STATEMENT, "2025")
        # 2 Transaction Ref entries, neither is PAYMENT → 2 charge descs
        # 2 date/amount lines → 2 charge amounts → 2 transactions
        assert len(txns) == 2

    def test_transaction_dates(self):
        txns = _parse_transactions(SAMPLE_STATEMENT, "2025")
        dates = [t.date for t in txns]
        assert "2025-10-03" in dates or "2025-03-10" in dates

    def test_transaction_is_charge_property(self):
        txns = _parse_transactions(SAMPLE_STATEMENT, "2025")
        assert all(t.is_charge for t in txns)

    def test_merchant_cleaned(self):
        txns = _parse_transactions(SAMPLE_STATEMENT, "2025")
        merchants = [t.merchant for t in txns]
        assert all(m != "" for m in merchants)

    def test_filters_payment_descriptions(self):
        text_with_payment = (
            "Transaction Ref 1 PAYMENT THANK YOU HK\n"
            "\xa0\n"
            "Transaction Ref 2 SHOP HK\n"
            "\xa0\n"
            "01/15  500.00\n"
            "01/20  100.00\n"
        )
        txns = _parse_transactions(text_with_payment, "2025")
        # PAYMENT desc filtered out → only 1 charge desc paired with 1st amount
        assert len(txns) == 1
        assert txns[0].merchant == "SHOP"

    def test_fx_info_attached(self):
        text_fx = (
            "Foreign Currency USD 50.00, Rate 7.8\n"
            "Transaction Ref 1 AWS AMAZON HK\n"
            "\xa0\n"
            "02/01  390.00\n"
        )
        txns = _parse_transactions(text_fx, "2025")
        assert len(txns) == 1
        assert txns[0].currency == "USD"
        assert txns[0].foreign_amount == -50.0


class TestExtractScb:
    """Integration test for extract_scb (mocked PDF reader)."""

    def _make_mock_reader(self, text: str):
        reader = MagicMock()
        page = MagicMock()
        page.extract_text.return_value = text
        reader.pages = [page]
        return reader

    @patch("metabolon.respirometry.parsers.scb.PdfReader")
    def test_full_parse_returns_meta_and_txns(self, mock_pdf_cls):
        # Build text where purchases total (3456.78) matches charge amounts
        text = (
            "Statement Date 15/03/2025\n"
            "Payment Due Date 05/04/2025\n"
            "SMART CREDIT CARD 106,000 26,345.39\n"
            "STATEMENT BALANCE 12,345.67\n"
            "MINIMUM PAYMENT DUE 1,234.56\n"
            "Previous Payments Credits Purchases Cash Charges Balance\n"
            "15,000.00 5,000.00 0.00 3,456.78 100.00 50.00 3,606.78\n"
            "Transaction Ref 1 SHOP A HONG KONG HK\n"
            "\xa0\n"
            "Transaction Ref 2 SHOP B KOWLOON BAY HK\n"
            "\xa0\n"
            "03/10  1,000.00\n"
            "03/12  2,456.78\n"
        )
        mock_pdf_cls.return_value = self._make_mock_reader(text)

        meta, txns = extract_scb(Path("/fake/statement.pdf"))
        assert isinstance(meta, RespirogramMeta)
        assert len(txns) == 2
        assert meta.statement_date == "2025-03-15"

    @patch("metabolon.respirometry.parsers.scb.PdfReader")
    def test_balance_mismatch_raises_value_error(self, mock_pdf_cls):
        # Purchases total = 999.99 but charges sum won't match
        text = (
            "Statement Date 15/03/2025\n"
            "Payment Due Date 05/04/2025\n"
            "SMART CREDIT CARD 50,000 500.00\n"
            "STATEMENT BALANCE 999.99\n"
            "MINIMUM PAYMENT DUE 100.00\n"
            "Previous Payments Credits Purchases Cash Charges Balance\n"
            "1,000.00 0.00 0.00 999.99 0.00 0.00 999.99\n"
            "Transaction Ref 1 SHOP HK\n"
            "\xa0\n"
            "03/10  100.00\n"
        )
        mock_pdf_cls.return_value = self._make_mock_reader(text)

        with pytest.raises(ValueError, match="Balance mismatch"):
            extract_scb(Path("/fake/statement.pdf"))
