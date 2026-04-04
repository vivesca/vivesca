from __future__ import annotations

"""Tests for metabolon.respirometry.parsers.ccba — complementary coverage."""

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


class TestCleanMerchantEdgeCases:
    """Additional _clean_merchant scenarios beyond the main test file."""

    def test_chinese_merchant_name_preserved(self):
        assert _clean_merchant("沙田餐廳") == "沙田餐廳"

    def test_mixed_alphanumeric_name(self):
        assert _clean_merchant("7-ELEVEN #123") == "7-ELEVEN #123"

    def test_name_with_hyphen(self):
        assert _clean_merchant("STARBUCKS-COFFEE") == "STARBUCKS-COFFEE"

    def test_only_country_code_and_spaces(self):
        assert _clean_merchant("   US   ") == "US"

    def test_empty_string(self):
        assert _clean_merchant("") == ""


class TestExtractMetadataPeriodLogic:
    """Focus on period_start / period_end derivation edge cases."""

    def test_no_transaction_dates_uses_statement_date(self):
        """When no transaction lines exist, the statement date itself is the
        only date found, so period_start equals that date."""
        text = "Statement Date 月結單截數日：Sep 07,2025"
        meta = _extract_metadata(text)
        # The regex picks up the statement date as the sole "transaction date"
        assert meta.period_start == "07 Sep 2025"

    def test_single_transaction_date_used_as_period_start(self):
        text = (
            "Statement Date 月結單截數日：Sep 07,2025\n"
            "STORE HK HKD 100.00 Aug 20,2025 Aug 20,2025\n"
        )
        meta = _extract_metadata(text)
        assert meta.period_start == "20 Aug 2025"

    def test_period_start_is_earliest_of_multiple_dates(self):
        text = (
            "Statement Date 月結單截數日：Sep 07,2025\n"
            "A HK HKD 10.00 Aug 20,2025 Aug 20,2025\n"
            "B HK HKD 20.00 Aug 05,2025 Aug 05,2025\n"
            "C HK HKD 30.00 Aug 25,2025 Aug 25,2025\n"
        )
        meta = _extract_metadata(text)
        assert meta.period_start == "05 Aug 2025"


class TestParseTransactionsAmounts:
    """Verify sign conventions on parsed hkd amounts."""

    def test_charge_is_negative(self):
        text = "STORE HK HKD 300.00 Sep 15,2025 Sep 15,2025"
        txns = _parse_transactions(text)
        assert txns[0].hkd == -300.00
        assert txns[0].is_charge
        assert not txns[0].is_credit

    def test_credit_is_positive(self):
        # CR adjacent to date
        text = "REFUND HKD 99.00 CRSep 10,2025 Sep 10,2025"
        txns = _parse_transactions(text)
        assert txns[0].hkd == 99.00
        assert txns[0].is_credit
        assert not txns[0].is_charge

    def test_large_amount_with_commas(self):
        text = "BIG BUY HK HKD 12,345.67 Sep 15,2025 Sep 15,2025"
        txns = _parse_transactions(text)
        assert txns[0].hkd == -12345.67

    def test_cross_border_fee_subtracts_from_preceding(self):
        text = (
            "STORE HK HKD 500.00 Sep 15,2025 Sep 15,2025\n"
            "CROSS-BORDER TXN FEE HKD 8.00 Sep 15,2025 Sep 15,2025\n"
        )
        txns = _parse_transactions(text)
        assert len(txns) == 1
        # 500 + 8 = 508 spent (more negative)
        assert txns[0].hkd == -508.00

    def test_sequential_cross_border_fees_accumulate(self):
        """Multiple cross-border fees on the same transaction all merge."""
        text = (
            "STORE HK HKD 200.00 Sep 15,2025 Sep 15,2025\n"
            "CROSS-BORDER TXN FEE HKD 3.00 Sep 15,2025 Sep 15,2025\n"
            "FEE - CROSS-BORDER TXN HKD 2.50 Sep 15,2025 Sep 15,2025\n"
        )
        txns = _parse_transactions(text)
        assert len(txns) == 1
        assert txns[0].hkd == -205.50


class TestTxnPatternRejects:
    """Inputs that must NOT match the transaction regex."""

    def test_missing_second_date(self):
        assert _TXN_PAT.match("STORE HKD 100.00 Sep 01,2025") is None

    def test_wrong_currency(self):
        assert _TXN_PAT.match("STORE USD 100.00 Sep 01,2025 Sep 01,2025") is None

    def test_incomplete_amount(self):
        assert _TXN_PAT.match("STORE HKD 100 Sep 01,2025 Sep 01,2025") is None


class TestExtractCcbaIntegration:
    """Integration tests for extract_ccba with mocked PdfReader."""

    @patch("metabolon.respirometry.parsers.ccba.PdfReader")
    def test_metadata_fields_populated(self, mock_pdf_reader):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Statement Date 月結單截數日：Oct 05,2025\n"
            "HKD 100,000.00\n"
            "HKD 95,000.00\n"
            "HKD 3,500.00\n"
            "RMB\n"
            "1234-5678-9012-3456 HKD 3,500.00 3,500.00 350.00 0.00 Nov 01,2025\n"
            "STORE HK HKD 3,500.00 Sep 20,2025 Sep 20,2025\n"
        )
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        meta, txns = extract_ccba(Path("/fake/oct.pdf"))

        assert meta.bank == "ccba"
        assert meta.statement_date == "2025-10-05"
        assert meta.credit_limit == 100000.00
        assert meta.balance == -3500.00
        assert meta.minimum_due == 350.00
        assert meta.due_date == "2025-11-01"
        assert len(txns) == 1
        assert txns[0].hkd == -3500.00

    @patch("metabolon.respirometry.parsers.ccba.PdfReader")
    def test_balance_mismatch_raises(self, mock_pdf_reader):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = (
            "Statement Date 月結單截數日：Sep 07,2025\n"
            "HKD 49,000.00\n"
            "HKD 46,978.41\n"
            "HKD 2,021.59\n"
            "RMB\n"
            "4317-8420-0303-6220 HKD 2,021.59 2,021.59 220.00 0.00 Oct 02,2025\n"
            "STORE HK HKD 50.00 Sep 15,2025 Sep 15,2025\n"
        )
        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        with pytest.raises(ValueError, match="Balance mismatch"):
            extract_ccba(Path("/fake/bad.pdf"))
