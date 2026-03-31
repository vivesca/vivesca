"""Tests for metabolon.respirometry.schema."""

from metabolon.respirometry.schema import ConsumptionEvent, RespirogramMeta


class TestConsumptionEvent:
    """Tests for the ConsumptionEvent dataclass."""

from __future__ import annotations

    def test_create_basic_event(self) -> None:
        """Test creating a basic ConsumptionEvent."""
        event = ConsumptionEvent(
            date="2024-03-15",
            merchant="STARBUCKS",
            category="Food",
            currency="HKD",
            foreign_amount=None,
            hkd=-45.0,
        )
        assert event.date == "2024-03-15"
        assert event.merchant == "STARBUCKS"
        assert event.category == "Food"
        assert event.currency == "HKD"
        assert event.foreign_amount is None
        assert event.hkd == -45.0

    def test_create_foreign_currency_event(self) -> None:
        """Test creating a ConsumptionEvent with foreign currency."""
        event = ConsumptionEvent(
            date="2024-03-15",
            merchant="AMAZON",
            category="Shopping",
            currency="USD",
            foreign_amount=29.99,
            hkd=-235.0,
        )
        assert event.foreign_amount == 29.99
        assert event.hkd == -235.0

    def test_is_charge_property(self) -> None:
        """Test the is_charge property works correctly."""
        # Negative hkd is a charge
        charge = ConsumptionEvent(
            date="2024-03-15",
            merchant="TEST",
            category="Test",
            currency="HKD",
            foreign_amount=None,
            hkd=-100.0,
        )
        assert charge.is_charge is True
        assert charge.is_credit is False

        # Positive hkd is a credit
        credit = ConsumptionEvent(
            date="2024-03-15",
            merchant="TEST",
            category="Test",
            currency="HKD",
            foreign_amount=None,
            hkd=50.0,
        )
        assert credit.is_charge is False
        assert credit.is_credit is True

        # Zero is neither?
        zero = ConsumptionEvent(
            date="2024-03-15",
            merchant="TEST",
            category="Test",
            currency="HKD",
            foreign_amount=None,
            hkd=0.0,
        )
        assert zero.is_charge is False
        assert zero.is_credit is False


class TestRespirogramMeta:
    """Tests for the RespirogramMeta dataclass."""

    def test_create_meta(self) -> None:
        """Test creating a RespirogramMeta instance."""
        meta = RespirogramMeta(
            bank="mox",
            card="Mox Credit",
            period_start="2024-02-01",
            period_end="2024-02-29",
            statement_date="2024-03-01",
            balance=12345.67,
            minimum_due=500.0,
            due_date="2024-03-20",
            credit_limit=100000.0,
        )
        assert meta.bank == "mox"
        assert meta.card == "Mox Credit"
        assert meta.statement_date == "2024-03-01"
        assert meta.balance == 12345.67

    def test_filename_stem(self) -> None:
        """Test the filename_stem property."""
        meta = RespirogramMeta(
            bank="hsbc",
            card="HSBC Visa",
            period_start="2024-02-01",
            period_end="2024-02-29",
            statement_date="2024-03-01",
            balance=0.0,
            minimum_due=0.0,
            due_date="2024-03-20",
            credit_limit=0.0,
        )
        assert meta.filename_stem == "2024-03-hsbc"

        meta2 = RespirogramMeta(
            bank="ccba",
            card="China Construction Bank",
            period_start="2024-02-01",
            period_end="2024-02-29",
            statement_date="2024-02-29",
            balance=0.0,
            minimum_due=0.0,
            due_date="2024-03-20",
            credit_limit=0.0,
        )
        assert meta2.filename_stem == "2024-02-ccba"
