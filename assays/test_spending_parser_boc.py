"""Tests for BOC Credit Card statement parser."""

from pathlib import Path

import pytest

from metabolon.respirometry.parsers.boc import extract_boc
from metabolon.respirometry.schema import RespirogramMeta

FIXTURE = Path(__file__).parent / "fixtures" / "boc_feb2026.pdf"


@pytest.mark.skipif(not FIXTURE.exists(), reason="test fixture not available")
class TestBocParser:
    def setup_method(self):
        self.meta, self.txns = extract_boc(FIXTURE)

    def test_returns_metadata(self):
        assert isinstance(self.meta, RespirogramMeta)
        assert self.meta.bank == "boc"
        assert self.meta.card == "BOC Taobao World Mastercard"

    def test_statement_date(self):
        assert self.meta.statement_date == "2026-02-27"

    def test_balance(self):
        assert self.meta.balance == -19613.00

    def test_credit_limit(self):
        assert self.meta.credit_limit == 200000.00

    def test_due_date(self):
        assert self.meta.due_date == "2026-03-24"

    def test_minimum_due(self):
        assert self.meta.minimum_due == 230.00

    def test_period_start(self):
        assert self.meta.period_start == "03 Feb 2026"

    def test_transaction_count(self):
        assert len(self.txns) == 33

    def test_balance_validation(self):
        """Balance validation passes (would raise ValueError on mismatch)."""
        # Already validated in extract_boc; this confirms no exception.
        assert True

    def test_payment_excluded(self):
        merchants = [t.merchant for t in self.txns]
        assert not any("PPS PAYMENT" in m.upper() for m in merchants)

    def test_refunds_included(self):
        credits = [t for t in self.txns if t.hkd > 0]
        assert len(credits) == 2
        assert any("ALIPAY FINANCIAL" in t.merchant for t in credits)

    def test_merchant_cleaned(self):
        """Location suffix 'HONG KONG HKG' should be stripped."""
        for t in self.txns:
            assert "HONG KONG" not in t.merchant
            assert not t.merchant.endswith("HKG")
