"""Tests for metabolon/respirometry/parsers/scb.py — SCB PDF parser.

Unit tests for internal helpers: _clean_merchant, _extract_metadata,
_extract_purchases_total, _parse_transactions.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from metabolon.respirometry.parsers.scb import (
    _clean_merchant,
    _extract_metadata,
    _extract_purchases_total,
    _parse_transactions,
)


# ---------------------------------------------------------------------------
# _clean_merchant
# ---------------------------------------------------------------------------

class TestCleanMerchant:
    def test_basic(self):
        assert _clean_merchant("STARBUCKS") == "STARBUCKS"

    def test_strips_hong_kong(self):
        result = _clean_merchant("AMAZON HONG KONG HK")
        assert "HONG KONG" not in result
        assert "HK" not in result

    def test_strips_country_code(self):
        result = _clean_merchant("STORE SG")
        assert result == "STORE"

    def test_collapses_spaces(self):
        result = _clean_merchant("A  B   C")
        assert result == "A B C"

    def test_strips_website_domains(self):
        result = _clean_merchant("ITUNES.COM HK")
        assert "ITUNES" not in result or result == ""

    def test_strips_multiple_locations(self):
        result = _clean_merchant("SHOP CENTRAL HK")
        assert "CENTRAL" not in result


# ---------------------------------------------------------------------------
# _extract_metadata
# ---------------------------------------------------------------------------

class TestExtractMetadata:
    def _make_text(self, **overrides: str) -> str:
        defaults = {
            "stmt": "Statement Date 15/01/2025",
            "due": "Payment Due Date 05/02/2025",
            "cl": "SMART CREDIT CARD 106,000",
            "bal": "STATEMENT BALANCE 12,345.67",
            "min": "MINIMUM PAYMENT DUE 1,234.56",
        }
        defaults.update(overrides)
        return textwrap.dedent(f"""\
            {defaults['stmt']}
            {defaults['due']}
            {defaults['cl']}
            {defaults['bal']}
            {defaults['min']}
        """)

    def test_basic_metadata(self):
        text = self._make_text()
        meta = _extract_metadata(text)
        assert meta.bank == "scb"
        assert meta.card == "SCB Smart Credit Card"
        assert meta.statement_date == "2025-01-15"
        assert meta.due_date == "2025-02-05"
        assert meta.credit_limit == 106000.0
        assert meta.balance == -12345.67
        assert meta.minimum_due == 1234.56

    def test_missing_fields(self):
        text = "some random text without any markers"
        meta = _extract_metadata(text)
        assert meta.statement_date == ""
        assert meta.balance == 0.0

    def test_statement_date_alt_format(self):
        text = "Statement Date :15 Jan 2025\nPayment Due Date :5 Feb 2025"
        meta = _extract_metadata(text)
        assert meta.statement_date == "2025-01-15"
        assert meta.due_date == "2025-02-05"


# ---------------------------------------------------------------------------
# _extract_purchases_total
# ---------------------------------------------------------------------------

class TestExtractPurchasesTotal:
    def test_finds_purchases_column(self):
        text = "1,000.00 200.00 50.00 500.00 0.00 10.00 1,260.00"
        result = _extract_purchases_total(text)
        assert result == 500.00

    def test_no_match(self):
        assert _extract_purchases_total("nothing here") == 0.0

    def test_with_commas(self):
        text = "10,000.00 2,000.00 500.00 5,000.00 0.00 100.00 12,600.00"
        result = _extract_purchases_total(text)
        assert result == 5000.00


# ---------------------------------------------------------------------------
# _parse_transactions
# ---------------------------------------------------------------------------

class TestParseTransactions:
    def test_parses_transaction_dates_and_amounts(self):
        text = textwrap.dedent("""\
            Transaction Ref 1 APPLE STORE\xa0\xa0\xa0
            01/15 500.00
            Transaction Ref 2 PAYMENT TO SCB\xa0\xa0\xa0
            01/20 200.00
            Transaction Ref 3 AMAZON\xa0\xa0\xa0
            01/25 100.00
        """)
        txns = _parse_transactions(text, "2025")
        # PAYMENT desc filtered out; charge_descs = [APPLE, AMAZON]
        # Amounts paired in order: APPLE→01/15 500.00, AMAZON→01/20 200.00
        assert len(txns) == 2
        assert txns[0].merchant == "APPLE STORE"
        assert txns[0].hkd == -500.00
        assert txns[0].date == "2025-01-15"
        assert txns[1].hkd == -200.00

    def test_empty_text(self):
        txns = _parse_transactions("no transactions here", "2025")
        assert txns == []

    def test_fx_transaction(self):
        text = textwrap.dedent("""\
            Foreign Currency USD 50.00, Rate 7.8
            Transaction Ref 1 OVERSEAS SHOP\xa0\xa0\xa0
            01/10 390.00
        """)
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 1
        assert txns[0].currency == "USD"
        assert txns[0].foreign_amount == -50.00
        assert txns[0].hkd == -390.00
