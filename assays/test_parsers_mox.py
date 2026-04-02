from __future__ import annotations

"""Scenario-focused tests for metabolon.respirometry.parsers.mox.

These tests exercise the full extraction pipeline with realistic PDF text,
complementing the unit-level tests in test_mox.py.
"""


from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from metabolon.respirometry.parsers.mox import (
    _extract_metadata,
    _parse_transactions,
    extract_mox,
)
from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_statement_page(
    period: str = "1 Nov 2025 - 30 Nov 2025",
    credit_limit: str = "100,000.00",
    balance: str = "-2,345.67",
    minimum_due: str = "300.00",
    due_date: str = "25 Dec 2025",
    transactions: str = "",
) -> str:
    """Build realistic Mox statement page-1 text."""
    return f"""{period}
Total credit limit: {credit_limit}
{balance} HKD
Statement balance
{minimum_due} HKD
Minimum amount due
{due_date}
Payment due date
{transactions}"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFullPipelineSinglePage:
    """End-to-end extraction from a single mocked PDF page."""

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_single_charge_balanced(self, mock_pdf_reader):
        """One charge matches statement balance exactly."""
        page_text = _make_statement_page(
            balance="-88.50",
            transactions="05 Nov 05 NovCOFFEE SHOP\n-88.50\n",
        )
        mock_page = MagicMock()
        mock_page.extract_text.return_value = page_text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_mox(Path("/fake/mox.pdf"))
        assert meta.bank == "mox"
        assert meta.statement_date == "2025-11-30"
        assert len(txns) == 1
        assert txns[0].merchant == "COFFEE SHOP"
        assert txns[0].hkd == -88.50
        assert txns[0].is_charge

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_charge_and_refund_balanced(self, mock_pdf_reader):
        """Mix of charge and credit; net must match balance."""
        page_text = _make_statement_page(
            balance="-1,000.00",
            transactions=(
                "03 Nov 03 NovELECTRONICS STORE\n-1,500.00\n"
                "10 Nov 10 NovPARTIAL REFUND\n500.00\n"
            ),
        )
        mock_page = MagicMock()
        mock_page.extract_text.return_value = page_text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_mox(Path("/fake/mox.pdf"))
        assert len(txns) == 2
        assert txns[0].hkd == -1500.00
        assert txns[0].is_charge
        assert txns[1].hkd == 500.00
        assert txns[1].is_credit


class TestFullPipelineMultiPage:
    """Extraction from multi-page PDFs with page breaks."""

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_transactions_span_two_pages(self, mock_pdf_reader):
        """Transactions split across two pages are all captured."""
        page1 = _make_statement_page(
            balance="-300.00",
            transactions="05 Nov 05 NovSTORE ALPHA\n-150.00\n",
        )
        page2 = "20 Nov 20 NovSTORE BETA\n-150.00\n"
        p1, p2 = MagicMock(), MagicMock()
        p1.extract_text.return_value = page1
        p2.extract_text.return_value = page2
        mock_reader = MagicMock()
        mock_reader.pages = [p1, p2]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_mox(Path("/fake/mox.pdf"))
        assert len(txns) == 2
        assert txns[0].merchant == "STORE ALPHA"
        assert txns[1].merchant == "STORE BETA"

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_rate_summary_page_stops_extraction(self, mock_pdf_reader):
        """Pages after Rate summary are ignored."""
        page1 = _make_statement_page(
            balance="-200.00",
            transactions="05 Nov 05 NovGROCERY\n-200.00\n",
        )
        page2 = "Rate summary\nInterest rate info\n"
        page3 = "25 Nov 25 NovLATE CHARGE\n-50.00\n"
        p1, p2, p3 = (MagicMock() for _ in range(3))
        p1.extract_text.return_value = page1
        p2.extract_text.return_value = page2
        p3.extract_text.return_value = page3
        mock_reader = MagicMock()
        mock_reader.pages = [p1, p2, p3]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_mox(Path("/fake/mox.pdf"))
        assert len(txns) == 1  # page3 should be ignored


class TestForeignCurrencyIntegration:
    """Foreign currency transactions through the full pipeline."""

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_usd_transaction_with_fx(self, mock_pdf_reader):
        """USD transaction preserves both foreign and HKD amounts."""
        page_text = _make_statement_page(
            balance="-779.22",
            transactions=(
                "12 Nov 12 NovAMAZON.COM\n-779.22\n99.99 USD\n"
            ),
        )
        mock_page = MagicMock()
        mock_page.extract_text.return_value = page_text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        _, txns = extract_mox(Path("/fake/mox.pdf"))
        assert len(txns) == 1
        t = txns[0]
        assert t.currency == "USD"
        assert t.foreign_amount == 99.99
        assert t.hkd == -779.22

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_mixed_hkd_and_jpy(self, mock_pdf_reader):
        """Statement with HKD and JPY transactions."""
        page_text = _make_statement_page(
            balance="-1,600.00",
            transactions=(
                "01 Nov 01 NovLOCAL SHOP\n-100.00\n"
                "15 Nov 15 NovJAPAN RAIL\n-1,500.00\n15,000 JPY\n"
            ),
        )
        mock_page = MagicMock()
        mock_page.extract_text.return_value = page_text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        _, txns = extract_mox(Path("/fake/mox.pdf"))
        assert txns[0].currency == "HKD"
        assert txns[0].foreign_amount is None
        assert txns[1].currency == "JPY"
        assert txns[1].foreign_amount == 15000.00


class TestBalanceValidation:
    """Balance validation behaviour in realistic scenarios."""

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_mismatch_raises_value_error(self, mock_pdf_reader):
        """Mismatched totals raise ValueError with helpful message."""
        page_text = _make_statement_page(
            balance="-5,000.00",
            transactions="05 Nov 05 NovSMALL CHARGE\n-50.00\n",
        )
        mock_page = MagicMock()
        mock_page.extract_text.return_value = page_text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        with pytest.raises(ValueError, match=r"Balance mismatch.*-50\.00.*-5,000\.00"):
            extract_mox(Path("/fake/mox.pdf"))

    @patch("metabolon.respirometry.parsers.mox.PdfReader")
    def test_transfers_excluded_from_balance(self, mock_pdf_reader):
        """Internal Mox transfers don't count toward balance validation."""
        page_text = _make_statement_page(
            balance="-500.00",
            transactions=(
                "01 Nov 01 NovSTORE\n-500.00\n"
                "02 Nov 02 NovMove between own Mox accounts\n-200.00\n"
            ),
        )
        mock_page = MagicMock()
        mock_page.extract_text.return_value = page_text
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        # Should NOT raise — transfer excluded from balance check
        meta, txns = extract_mox(Path("/fake/mox.pdf"))
        assert len(txns) == 1
        assert txns[0].hkd == -500.00


class TestMerchantCleaning:
    """Merchant name cleaning in realistic transaction text."""

    def test_country_code_removed(self):
        """Trailing country codes (USA, GBR, etc.) are stripped."""
        text = "15 Nov 15 NovHOTEL NIKKO JPN\n-25,000.00\n2025"
        txns = _parse_transactions(text, "2025")
        assert len(txns) == 1
        assert txns[0].merchant == "HOTEL NIKKO"
        assert "JPN" not in txns[0].merchant

    def test_amount_stripped_from_merchant(self):
        """Trailing HKD amount is removed from merchant name."""
        text = "15 Nov 15 NovSTARBUCKS -48.00\n2025"
        txns = _parse_transactions(text, "2025")
        assert txns[0].merchant == "STARBUCKS"

    def test_combined_country_and_amount_cleaning(self):
        """Multiple cleaning rules apply in sequence."""
        text = "15 Nov 15 NovAPPLE.COM/BILL USA -99.00\n-99.00\n2025"
        txns = _parse_transactions(text, "2025")
        assert txns[0].merchant == "APPLE.COM/BILL"
        assert "USA" not in txns[0].merchant
