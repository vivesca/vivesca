"""Tests for HSBC Visa Signature statement parser."""

from pathlib import Path

import pytest

from metabolon.respirometry.parsers.hsbc import extract_hsbc
from metabolon.respirometry.schema import RespirogramMeta

FIXTURE = Path(__file__).parent / "fixtures" / "hsbc_mar2025.pdf"
FIXTURE_FEB = Path(__file__).parent / "fixtures" / "hsbc_feb2025.pdf"


@pytest.mark.skipif(not FIXTURE.exists(), reason="test fixture not available")
class TestHsbcParser:
    def setup_method(self):
        self.meta, self.txns = extract_hsbc(FIXTURE)

    def test_returns_metadata(self):
        assert isinstance(self.meta, RespirogramMeta)
        assert self.meta.bank == "hsbc"
        assert self.meta.card == "HSBC Visa Signature"

    def test_statement_date(self):
        assert self.meta.statement_date == "2025-03-07"

    def test_balance(self):
        assert self.meta.balance == -26119.50

    def test_credit_limit(self):
        assert self.meta.credit_limit == 72000.00

    def test_due_date(self):
        assert self.meta.due_date == "2025-04-02"

    def test_minimum_due(self):
        assert self.meta.minimum_due == 300.00

    def test_total_matches_balance(self):
        """Critical integrity check: parsed total must match statement balance."""
        total = sum(t.hkd for t in self.txns)
        assert abs(total - self.meta.balance) < 0.02

    def test_previous_balance_excluded(self):
        merchants = [t.merchant for t in self.txns]
        assert not any("PREVIOUS" in m.upper() for m in merchants)

    def test_payment_excluded(self):
        merchants = [t.merchant for t in self.txns]
        assert not any("PAYMENT-THANKYOU" in m.upper() for m in merchants)
        assert not any("PAYMENT - THANK YOU" in m.upper() for m in merchants)

    def test_dcc_fee_merged(self):
        """DCC fees should be merged into preceding transaction, not standalone."""
        merchants = [t.merchant for t in self.txns]
        assert not any("DCC" in m.upper() for m in merchants)

    def test_foreign_currency_parsed(self):
        usd_txns = [t for t in self.txns if t.currency == "USD"]
        assert len(usd_txns) > 0
        for t in usd_txns:
            assert t.foreign_amount is not None

    def test_merchant_names_cleaned(self):
        """Payment device suffixes should be stripped."""
        for t in self.txns:
            assert "APPLE PAY-MOBILE" not in t.merchant
            assert "GOOGLE PAY-DEVICE" not in t.merchant
            assert "APPLEPAY-MOBILE" not in t.merchant


@pytest.mark.skipif(not FIXTURE_FEB.exists(), reason="test fixture not available")
class TestHsbcParserFeb:
    def setup_method(self):
        self.meta, self.txns = extract_hsbc(FIXTURE_FEB)

    def test_statement_date(self):
        assert self.meta.statement_date == "2025-02-06"

    def test_total_matches_balance(self):
        """Balance validation on second fixture."""
        total = sum(t.hkd for t in self.txns)
        assert abs(total - self.meta.balance) < 0.02
