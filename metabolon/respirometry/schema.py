"""ConsumptionEvent and statement metadata schema."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConsumptionEvent:
    """A single credit card transaction."""

    date: str  # ISO format YYYY-MM-DD
    merchant: str
    category: str
    currency: str  # HKD, USD, GBP, etc.
    foreign_amount: float | None  # None if HKD
    hkd: float  # always present

    @property
    def is_charge(self) -> bool:
        return self.hkd < 0

    @property
    def is_credit(self) -> bool:
        return self.hkd > 0


@dataclass
class RespirogramMeta:
    """Statement-level metadata extracted from PDF."""

    bank: str  # mox, hsbc, ccba
    card: str  # human-readable card name
    period_start: str
    period_end: str
    statement_date: str  # ISO format YYYY-MM-DD
    balance: float
    minimum_due: float
    due_date: str
    credit_limit: float

    @property
    def filename_stem(self) -> str:
        """YYYY-MM-bank for vault filenames."""
        # statement_date is YYYY-MM-DD
        return f"{self.statement_date[:7]}-{self.bank}"
