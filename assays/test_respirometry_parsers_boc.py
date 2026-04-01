"""Tests for metabolon/respirometry/parsers/boc.py."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

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


# ── Minimal BOC PDF text fixture ─────────────────────────────────────────────
# A realistic (but synthetic) single-page BOC statement.  All amounts are
# internally consistent so that the balance-validation arithmetic passes.

SAMPLE_PDF_TEXT = """\
Payment Slip
HKD 50,000.00
HKD 3,000.00
HKD 300.00
05-MAR-2025
25-MAR-2025
Card Type:
BOC Visa Gold
BALANCE B/F 2,000.00
01-FEB 03-FEB COFFEE SHOP HONG KONG     HKG  50.00
05-FEB 07-FEB SUPERMARKET HONG KONG     HKG  200.00
10-FEB 12-FEB PPS PAYMENT HONG KONG     HKG  1,000.00 CR
15-FEB 17-FEB BOOKSTORE HONG KONG     HKG  150.00
CURRENT BALANCE 3,400.00
ODD CENTS TO NEXT BILL 0.35 CR
"""

# Derived expected values:
#   balance_bf  = -2000.00
#   payments    =  1000.00  (PPS PAYMENT CR, excluded from txns)
#   odd_cents   =  0.35
#   balance     = -3000.00  (from HKD line)
#   expected new charges = balance - balance_bf - payments - odd_cents
#                        = -3000 - (-2000) - 1000 - 0.35 = -2000.35
#   txns: -50 - 200 - 150 = -450   ... wait recalculate:
#   Actually: spending_total = -50 - 200 - 150 = -450
#   expected = -3000 - (-2000) - 1000 - 0.35 = -3000 + 2000 - 1000 - 0.35 = -2000.35
#   That doesn't balance. Let me adjust.

# Let me construct a text that actually balances:
# balance = -3000 (HKD 3,000.00)
# balance_bf = -2000 (BALANCE B/F 2,000.00)
# payments = 1000 (PPS PAYMENT 1,000.00 CR)
# odd_cents = 0
# expected = -3000 - (-2000) - 1000 - 0 = -3000 + 2000 - 1000 = -2000
# So spending total must be -2000
# txns: -800 - 1200 = -2000

BALANCED_PDF_TEXT = """\
Payment Slip
HKD 50,000.00
HKD 3,000.00
HKD 300.00
05-MAR-2025
25-MAR-2025
Card Type:
BOC Visa Gold
BALANCE B/F 2,000.00
01-FEB 03-FEB COFFEE SHOP HONG KONG     HKG  800.00
10-FEB 12-FEB SUPERMARKET HONG KONG     HKG  1,200.00
15-FEB 17-FEB PPS PAYMENT HONG KONG     HKG  1,000.00 CR
CURRENT BALANCE 3,000.00
"""


class TestParseShortDate(unittest.TestCase):
    """Tests for _parse_short_date."""

    def test_parses_date_within_statement_year(self) -> None:
        result = _parse_short_date("15-FEB", 2025, "2025-03-05")
        self.assertEqual(result, "2025-02-15")

    def test_wraps_to_previous_year_when_month_after_statement(self) -> None:
        result = _parse_short_date("15-DEC", 2025, "2025-01-15")
        self.assertEqual(result, "2024-12-15")

    def test_no_wrap_when_statement_date_empty(self) -> None:
        result = _parse_short_date("10-MAR", 2025, "")
        self.assertEqual(result, "2025-03-10")

    def test_same_month_no_wrap(self) -> None:
        result = _parse_short_date("05-MAR", 2025, "2025-03-15")
        self.assertEqual(result, "2025-03-05")


class TestCleanMerchant(unittest.TestCase):
    """Tests for _clean_merchant."""

    def test_removes_hong_kong_hkg_suffix(self) -> None:
        self.assertEqual(
            _clean_merchant("COFFEE SHOP HONG KONG     HKG"), "COFFEE SHOP"
        )

    def test_removes_truncated_hong_kon(self) -> None:
        self.assertEqual(
            _clean_merchant("STORE HONG KON HONG KONG"), "STORE"
        )

    def test_removes_trailing_country_code(self) -> None:
        self.assertEqual(_clean_merchant("AMAZON USA"), "AMAZON")

    def test_collapses_multiple_spaces(self) -> None:
        # "BAZ" is 3 uppercase chars → stripped as trailing country code by design
        self.assertEqual(_clean_merchant("FOO  BAR    BAZ"), "FOO BAR")
        # Spaces collapsed, no trailing country code to strip
        self.assertEqual(_clean_merchant("FOO  BAR    SHOP"), "FOO BAR SHOP")

    def test_strips_whitespace(self) -> None:
        self.assertEqual(_clean_merchant("  MERCHANT  "), "MERCHANT")

    def test_empty_string(self) -> None:
        self.assertEqual(_clean_merchant(""), "")


class TestExtractBalanceBf(unittest.TestCase):
    """Tests for _extract_balance_bf."""

    def test_extracts_balance(self) -> None:
        text = "BALANCE B/F 2,500.00\n"
        self.assertEqual(_extract_balance_bf(text), -2500.00)

    def test_returns_zero_when_missing(self) -> None:
        self.assertEqual(_extract_balance_bf("no balance here"), 0.0)

    def test_handles_large_amount(self) -> None:
        text = "BALANCE B/F 123,456.78"
        self.assertEqual(_extract_balance_bf(text), -123456.78)


class TestExtractOddCents(unittest.TestCase):
    """Tests for _extract_odd_cents."""

    def test_extracts_cr_cents(self) -> None:
        text = "ODD CENTS TO NEXT BILL 0.35 CR"
        self.assertEqual(_extract_odd_cents(text), 0.35)

    def test_extracts_debit_cents(self) -> None:
        text = "ODD CENTS TO NEXT BILL 0.50"
        self.assertEqual(_extract_odd_cents(text), -0.50)

    def test_returns_zero_when_missing(self) -> None:
        self.assertEqual(_extract_odd_cents("no odd cents"), 0.0)


class TestExtractPayments(unittest.TestCase):
    """Tests for _extract_payments."""

    def test_sums_pps_payment_credits(self) -> None:
        text = (
            "15-FEB 17-FEB PPS PAYMENT HONG KONG     HKG  1,000.00 CR\n"
            "20-FEB 22-FEB PPS PAYMENT HONG KONG     HKG  500.00 CR\n"
        )
        self.assertEqual(_extract_payments(text, "2025-03-05"), 1500.00)

    def test_ignores_non_payment_credits(self) -> None:
        text = "01-FEB 03-FEB REFUND HONG KONG     HKG  100.00 CR\n"
        self.assertEqual(_extract_payments(text, "2025-03-05"), 0.0)

    def test_ignores_pps_without_cr(self) -> None:
        text = "01-FEB 03-FEB PPS PAYMENT HONG KONG     HKG  1,000.00\n"
        self.assertEqual(_extract_payments(text, "2025-03-05"), 0.0)

    def test_returns_zero_on_empty(self) -> None:
        self.assertEqual(_extract_payments("", "2025-03-05"), 0.0)


class TestExtractMetadata(unittest.TestCase):
    """Tests for _extract_metadata."""

    def test_extracts_full_metadata(self) -> None:
        text = (
            "Payment Slip\n"
            "HKD 50,000.00\n"
            "HKD 3,000.00\n"
            "HKD 300.00\n"
            "05-MAR-2025\n"
            "25-MAR-2025\n"
            "Card Type:\n"
            "BOC Visa Gold\n"
            "BALANCE B/F 0.00\n"
        )
        meta = _extract_metadata(text)
        self.assertEqual(meta.bank, "boc")
        self.assertEqual(meta.credit_limit, 50000.00)
        self.assertEqual(meta.balance, -3000.00)
        self.assertEqual(meta.minimum_due, 300.00)
        self.assertEqual(meta.statement_date, "2025-03-05")
        self.assertEqual(meta.due_date, "2025-03-25")
        self.assertEqual(meta.card, "BOC Visa Gold")
        self.assertEqual(meta.period_end, "05 Mar 2025")

    def test_defaults_when_no_payment_slip(self) -> None:
        meta = _extract_metadata("nothing useful here")
        self.assertEqual(meta.bank, "boc")
        self.assertEqual(meta.balance, 0.0)
        self.assertEqual(meta.credit_limit, 0.0)
        self.assertEqual(meta.statement_date, "")
        self.assertEqual(meta.card, "BOC Credit Card")

    def test_partial_hkd_values(self) -> None:
        text = "Payment Slip\nHKD 20,000.00\nBALANCE B/F 0.00\n"
        meta = _extract_metadata(text)
        self.assertEqual(meta.credit_limit, 20000.00)
        self.assertEqual(meta.balance, 0.0)


class TestParseTransactions(unittest.TestCase):
    """Tests for _parse_transactions."""

    def test_parses_single_charge(self) -> None:
        text = "01-FEB 03-FEB COFFEE SHOP HONG KONG     HKG  50.00\n"
        txns = _parse_transactions(text, "2025-03-05")
        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0].date, "2025-02-03")
        self.assertEqual(txns[0].merchant, "COFFEE SHOP")
        self.assertEqual(txns[0].hkd, -50.00)
        self.assertEqual(txns[0].currency, "HKD")
        self.assertIsNone(txns[0].foreign_amount)

    def test_parses_credit_transaction(self) -> None:
        text = "01-FEB 05-FEB REFUND SHOP HONG KONG     HKG  100.00 CR\n"
        txns = _parse_transactions(text, "2025-03-05")
        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0].hkd, 100.00)

    def test_skips_pps_payment(self) -> None:
        text = "15-FEB 17-FEB PPS PAYMENT HONG KONG     HKG  1,000.00 CR\n"
        txns = _parse_transactions(text, "2025-03-05")
        self.assertEqual(len(txns), 0)

    def test_skips_balance_bf_line(self) -> None:
        text = "BALANCE B/F 2,000.00\n"
        txns = _parse_transactions(text, "2025-03-05")
        self.assertEqual(len(txns), 0)

    def test_skips_current_balance_line(self) -> None:
        text = "CURRENT BALANCE 3,000.00\n"
        txns = _parse_transactions(text, "2025-03-05")
        self.assertEqual(len(txns), 0)

    def test_skips_odd_cents_line(self) -> None:
        text = "ODD CENTS TO NEXT BILL 0.35 CR\n"
        txns = _parse_transactions(text, "2025-03-05")
        self.assertEqual(len(txns), 0)

    def test_skips_last_item_line(self) -> None:
        text = "LAST ITEM ON 28-FEB\n"
        txns = _parse_transactions(text, "2025-03-05")
        self.assertEqual(len(txns), 0)

    def test_multiple_transactions(self) -> None:
        text = (
            "01-FEB 03-FEB STORE A HONG KONG     HKG  100.00\n"
            "10-FEB 12-FEB STORE B HONG KONG     HKG  200.00\n"
            "15-FEB 17-FEB STORE C HONG KONG     HKG  50.00 CR\n"
        )
        txns = _parse_transactions(text, "2025-03-05")
        self.assertEqual(len(txns), 3)
        self.assertEqual(txns[0].hkd, -100.00)
        self.assertEqual(txns[1].hkd, -200.00)
        self.assertEqual(txns[2].hkd, 50.00)

    def test_comma_separated_amount(self) -> None:
        text = "01-FEB 03-FEB BIG STORE HONG KONG     HKG  1,234.56\n"
        txns = _parse_transactions(text, "2025-03-05")
        self.assertEqual(txns[0].hkd, -1234.56)

    def test_date_wrap_to_previous_year(self) -> None:
        text = "15-DEC 17-DEC SHOP HONG KONG     HKG  100.00\n"
        txns = _parse_transactions(text, "2025-01-15")
        self.assertEqual(txns[0].date, "2024-12-17")


class TestExtractBoc(unittest.TestCase):
    """Integration tests for extract_boc (mocked PdfReader)."""

    def _make_reader(self, text: str) -> MagicMock:
        reader = MagicMock()
        page = MagicMock()
        page.extract_text.return_value = text
        reader.pages = [page]
        return reader

    def test_balanced_statement(self) -> None:
        mock_reader = self._make_reader(BALANCED_PDF_TEXT)
        with patch(
            "metabolon.respirometry.parsers.boc.PdfReader",
            return_value=mock_reader,
        ):
            meta, txns = extract_boc(Path("/fake/boc.pdf"))

        self.assertEqual(meta.bank, "boc")
        self.assertEqual(meta.card, "BOC Visa Gold")
        self.assertEqual(meta.statement_date, "2025-03-05")
        self.assertEqual(meta.balance, -3000.00)
        self.assertEqual(meta.credit_limit, 50000.00)
        self.assertEqual(meta.minimum_due, 300.00)
        self.assertEqual(meta.due_date, "2025-03-25")
        self.assertEqual(len(txns), 2)
        self.assertEqual(txns[0].merchant, "COFFEE SHOP")
        self.assertEqual(txns[0].hkd, -800.00)
        self.assertEqual(txns[1].merchant, "SUPERMARKET")
        self.assertEqual(txns[1].hkd, -1200.00)

        # period_start set from earliest txn posting date (group 2)
        self.assertEqual(meta.period_start, "03 Feb 2025")

    def test_raises_on_balance_mismatch(self) -> None:
        # Same as balanced but with wrong amount
        bad_text = BALANCED_PDF_TEXT.replace("800.00", "500.00")
        mock_reader = self._make_reader(bad_text)
        with patch(
            "metabolon.respirometry.parsers.boc.PdfReader",
            return_value=mock_reader,
        ):
            with self.assertRaises(ValueError) as ctx:
                extract_boc(Path("/fake/boc.pdf"))
        self.assertIn("Balance mismatch", str(ctx.exception))

    def test_multi_page_statement(self) -> None:
        page1 = (
            "Payment Slip\n"
            "HKD 50,000.00\n"
            "HKD 2,500.00\n"
            "HKD 250.00\n"
            "05-MAR-2025\n"
            "25-MAR-2025\n"
            "Card Type:\n"
            "BOC Visa Gold\n"
            "BALANCE B/F 1,500.00\n"
            "01-FEB 03-FEB SHOP A HONG KONG     HKG  500.00\n"
        )
        page2 = (
            "10-FEB 12-FEB SHOP B HONG KONG     HKG  500.00\n"
            "CURRENT BALANCE 2,500.00\n"
        )
        # balance=-2500, bf=-1500, payments=0, odd=0
        # expected = -2500 - (-1500) - 0 - 0 = -1000
        # txns = -500 + -500 = -1000 ✓
        reader = MagicMock()
        p1 = MagicMock()
        p1.extract_text.return_value = page1
        p2 = MagicMock()
        p2.extract_text.return_value = page2
        reader.pages = [p1, p2]

        with patch(
            "metabolon.respirometry.parsers.boc.PdfReader",
            return_value=reader,
        ):
            meta, txns = extract_boc(Path("/fake/boc.pdf"))

        self.assertEqual(len(txns), 2)
        self.assertEqual(txns[0].merchant, "SHOP A")
        self.assertEqual(txns[1].merchant, "SHOP B")

    def test_statement_with_refund_and_odd_cents(self) -> None:
        # balance=-2000, bf=-1500, payments=0, odd_cents=0.50
        # expected = -2000 - (-1500) - 0 - 0.50 = -500.50
        # txns: -600 + 99.50 = -500.50 ✓
        text = (
            "Payment Slip\n"
            "HKD 50,000.00\n"
            "HKD 2,000.00\n"
            "HKD 200.00\n"
            "05-MAR-2025\n"
            "25-MAR-2025\n"
            "Card Type:\n"
            "BOC Visa Gold\n"
            "BALANCE B/F 1,500.00\n"
            "01-FEB 03-FEB SHOP HONG KONG     HKG  600.00\n"
            "10-FEB 12-FEB REFUND HONG KONG     HKG  99.50 CR\n"
            "ODD CENTS TO NEXT BILL 0.50 CR\n"
            "CURRENT BALANCE 2,000.00\n"
        )
        mock_reader = self._make_reader(text)
        with patch(
            "metabolon.respirometry.parsers.boc.PdfReader",
            return_value=mock_reader,
        ):
            meta, txns = extract_boc(Path("/fake/boc.pdf"))

        self.assertEqual(len(txns), 2)
        self.assertEqual(txns[0].hkd, -600.00)
        self.assertEqual(txns[1].hkd, 99.50)


if __name__ == "__main__":
    unittest.main()
