"""Tests for metabolon.respirometry.parsers.hsbc — edge cases and skip-line handling."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from metabolon.respirometry.parsers.hsbc import (
    _clean_merchant,
    _extract_metadata,
    _parse_transactions,
    extract_hsbc,
)
from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta

# ---------------------------------------------------------------------------
# _clean_merchant — location suffixes not covered by the sibling test file
# ---------------------------------------------------------------------------


class TestCleanMerchantExtraLocations:
    def test_removes_quarry_bay(self) -> None:
        assert _clean_merchant("STOREQUARRYBAYHK") == "STORE"

    def test_removes_sheung_wan(self) -> None:
        assert _clean_merchant("COFFEESHEUNGWANHK") == "COFFEE"

    def test_removes_north_point(self) -> None:
        assert _clean_merchant("MARTNORTHPOINTHK") == "MART"

    def test_removes_central_and_western(self) -> None:
        assert _clean_merchant("SHOPCENTRALANDWHK") == "SHOP"

    def test_removes_tsim_sha_tsui(self) -> None:
        assert _clean_merchant("CAFETSIMSHATSUHK") == "CAFE"

    def test_removes_uber_hk(self) -> None:
        assert _clean_merchant("UBER TRIPUBER.COM/HK/EHK") == "UBER TRIP"


# ---------------------------------------------------------------------------
# _parse_transactions — comma-formatted amounts and skip-line filtering
# ---------------------------------------------------------------------------


class TestParseTransactionsCommasAndSkips:
    def test_comma_formatted_amount(self) -> None:
        text = "01FEB03FEBBIG PURCHASE  1,234.56"
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 1
        assert txns[0].hkd == -1234.56

    def test_skip_previous_balance(self) -> None:
        text = "01JAN01JANPREVIOUSBALANCE  5,000.00"
        assert _parse_transactions(text, "2025") == []

    def test_skip_payment_thankyou_variant(self) -> None:
        text = "15FEB15FEBPAYMENT - THANK YOU  3,000.00"
        assert _parse_transactions(text, "2025") == []

    def test_skip_card_number_line(self) -> None:
        text = "01JAN01JAN1234567890123456  100.00"
        assert _parse_transactions(text, "2025") == []

    def test_line_without_amount_is_skipped(self) -> None:
        text = "01FEB03FEBNO AMOUNT HERE"
        txns = _parse_transactions(text, "2025")
        assert txns == []


# ---------------------------------------------------------------------------
# _parse_transactions — foreign-currency edge cases
# ---------------------------------------------------------------------------


class TestParseTransactionsFx:
    def test_gbp_transaction(self) -> None:
        text = "01MAR05MARHOTEL GBP 200.00 1,980.00"
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 1
        assert txns[0].currency == "GBP"
        assert txns[0].foreign_amount == -200.00
        assert txns[0].hkd == -1980.00

    def test_jpy_transaction(self) -> None:
        text = "10MAR12MARRESTAURANT JPY 5,000.00 280.50"
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 1
        assert txns[0].currency == "JPY"
        assert txns[0].foreign_amount == -5000.00
        assert txns[0].hkd == -280.50


# ---------------------------------------------------------------------------
# Schema property coverage
# ---------------------------------------------------------------------------


class TestSchemaProperties:
    def test_consumption_event_is_charge(self) -> None:
        ev = ConsumptionEvent("2025-01-01", "M", "", "HKD", None, -100.0)
        assert ev.is_charge is True
        assert ev.is_credit is False

    def test_consumption_event_is_credit(self) -> None:
        ev = ConsumptionEvent("2025-01-01", "M", "", "HKD", None, 50.0)
        assert ev.is_charge is False
        assert ev.is_credit is True

    def test_respirogram_meta_filename_stem(self) -> None:
        meta = RespirogramMeta(
            bank="hsbc",
            card="HSBC Visa Signature",
            period_start="",
            period_end="",
            statement_date="2025-03-07",
            balance=-1000.0,
            minimum_due=100.0,
            due_date="2025-04-15",
            credit_limit=150000.0,
        )
        assert meta.filename_stem == "2025-03-hsbc"


# ---------------------------------------------------------------------------
# extract_hsbc — multi-page PDF
# ---------------------------------------------------------------------------


class TestExtractHsbcMultiPage:
    def test_multi_page_statement(self) -> None:
        page1 = """Statementdate  Statementbalance
07MAR2025HKD600.00
HSBCVisaSignatureHKD150,000.00
Total minimum payment due  HKD
60.00
15APR2025
05FEB07FEBSTORE A  300.00
"""
        page2 = "10FEB12FEBSTORE B  300.00\n"
        mock_reader = MagicMock()
        p1, p2 = MagicMock(), MagicMock()
        p1.extract_text.return_value = page1
        p2.extract_text.return_value = page2
        mock_reader.pages = [p1, p2]

        with patch("metabolon.respirometry.parsers.hsbc.PdfReader", return_value=mock_reader):
            meta, txns = extract_hsbc(Path("/fake/statement.pdf"))

        assert meta.statement_date == "2025-03-07"
        assert len(txns) == 2
        assert sum(t.hkd for t in txns) == -600.00


# ---------------------------------------------------------------------------
# _extract_metadata — period derivation from transaction dates
# ---------------------------------------------------------------------------


class TestExtractMetadataPeriod:
    def test_derives_period_from_transactions(self) -> None:
        text = """Statementdate  Statementbalance
07MAR2025HKD500.00
HSBCVisaSignatureHKD150,000.00
05FEB07FEBSTORE A  500.00
"""
        meta = _extract_metadata(text)
        assert meta.period_start == "05 Feb 2025"
        assert meta.period_end == "07 Mar 2025"

    def test_no_period_without_transactions(self) -> None:
        text = """Statementdate  Statementbalance
07MAR2025HKD500.00
HSBCVisaSignatureHKD150,000.00
"""
        meta = _extract_metadata(text)
        assert meta.period_start == ""
