"""Tests for metabolon.respirometry.payments."""

from datetime import datetime
from pathlib import Path
import tempfile
from metabolon.respirometry.payments import (
    restore_payments,
    persist_payments,
    restore_card_config,
    is_autopay,
    queue_payment,
    dequeue_payment,
    assess_missing_statements,
    flag_overdue_payments,
)


class TestRestorePersistPayments:
    """Tests for restore_payments and persist_payments."""

from __future__ import annotations

    def test_restore_nonexistent_returns_empty(self) -> None:
        """Non-existent file returns empty list."""
        result = restore_payments(Path("/nonexistent"))
        assert result == []

    def test_restore_and_persist_roundtrip(self) -> None:
        """Persist writes data, restore reads it back."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            path = Path(f.name)

        try:
            pending = [
                {
                    "bank": "mox",
                    "amount": 1234.56,
                    "due_date": "2024-04-01",
                    "statement_date": "2024-03-01",
                    "created": "2024-03-01",
                }
            ]
            persist_payments(path, pending)
            loaded = restore_payments(path)
            assert loaded == pending
        finally:
            path.unlink()

    def test_restore_empty_file_returns_empty(self) -> None:
        """Empty file returns empty list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            path = Path(f.name)

        try:
            loaded = restore_payments(path)
            assert loaded == []
        finally:
            path.unlink()


class TestRestoreCardConfig:
    """Tests for restore_card_config and is_autopay."""

    def test_restore_nonexistent_returns_empty(self) -> None:
        """Non-existent file returns empty dict."""
        result = restore_card_config(Path("/nonexistent"))
        assert result == {}

    def test_is_autopay_returns_correctly(self) -> None:
        """is_autopay returns correct value based on config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
cards:
  mox:
    autopay: true
  hsbc:
    autopay: false
  ccba: {}
""")
            path = Path(f.name)

        try:
            assert is_autopay("mox", path) is True
            assert is_autopay("hsbc", path) is False
            assert is_autopay("ccba", path) is False
            assert is_autopay("unknown", path) is False
        finally:
            path.unlink()


class TestQueuePayment:
    """Tests for queue_payment."""

    def test_queue_new_payment_added(self) -> None:
        """New payment gets added to file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            path = Path(f.name)

        try:
            entry = queue_payment(path, "mox", 1234.56, "2024-04-01", "2024-03-01")
            assert entry["bank"] == "mox"
            assert entry["amount"] == 1234.56
            assert entry["due_date"] == "2024-04-01"
            assert entry["statement_date"] == "2024-03-01"
            assert "created" in entry

            # Check it's persisted
            loaded = restore_payments(path)
            assert len(loaded) == 1
        finally:
            path.unlink()

    def test_avoid_duplicates_same_statement(self) -> None:
        """Don't add duplicate for same bank + statement_date."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            path = Path(f.name)

        try:
            entry1 = queue_payment(path, "mox", 1234.56, "2024-04-01", "2024-03-01")
            entry2 = queue_payment(path, "mox", 1234.56, "2024-04-01", "2024-03-01")

            # Returns existing entry, doesn't add duplicate
            assert entry1 is not None
            assert entry2 is not None
            assert entry1["bank"] == entry2["bank"]
            assert entry1["statement_date"] == entry2["statement_date"]
            loaded = restore_payments(path)
            assert len(loaded) == 1
        finally:
            path.unlink()


class TestDequeuePayment:
    """Tests for dequeue_payment."""

    def test_dequeue_existing_removes_oldest(self) -> None:
        """Dequeue removes and returns oldest pending entry."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            path = Path(f.name)

        try:
            queue_payment(path, "mox", 1000, "2024-04-01", "2024-03-01")
            queue_payment(path, "hsbc", 2000, "2024-04-02", "2024-03-02")
            queue_payment(path, "mox", 3000, "2024-05-01", "2024-04-01")

            removed = dequeue_payment(path, "mox")
            assert removed is not None
            assert removed["amount"] == 1000

            # One mox entry remains
            loaded = restore_payments(path)
            assert len(loaded) == 2
            assert loaded[0]["bank"] == "hsbc"
            assert loaded[1]["bank"] == "mox"
            assert loaded[1]["amount"] == 3000
        finally:
            path.unlink()

    def test_dequeue_none_matching_returns_none(self) -> None:
        """No matching entry returns None."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            path = Path(f.name)

        try:
            queue_payment(path, "mox", 1000, "2024-04-01", "2024-03-01")
            removed = dequeue_payment(path, "hsbc")
            assert removed is None
            assert len(restore_payments(path)) == 1
        finally:
            path.unlink()


class TestAssessMissingStatements:
    """Tests for assess_missing_statements."""

    def test_no_alerts_when_all_exist(self) -> None:
        """No alerts when all expected statements exist."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
cards:
  mox:
    active: true
    statement_day: 1
  hsbc:
    active: true
    statement_day: 5
""")
            config_path = Path(f.name)

        with tempfile.TemporaryDirectory() as spending_dir:
            p_spending_dir = Path(spending_dir)
            # Create statement for current month
            current_month = datetime.now().strftime("%Y-%m")
            (p_spending_dir / f"{current_month}-mox.md").touch()
            (p_spending_dir / f"{current_month}-hsbc.md").touch()

            try:
                alerts = assess_missing_statements(config_path, p_spending_dir)
                assert len(alerts) == 0
            finally:
                config_path.unlink()

    def test_flag_missing(self) -> None:
        """Flag missing statements when grace period has passed."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
cards:
  mox:
    active: true
    statement_day: 1
  hsbc:
    active: false
    statement_day: 1
""")
            config_path = Path(f.name)

        with tempfile.TemporaryDirectory() as spending_dir:
            p_spending_dir = Path(spending_dir)
            # Don't create file

            try:
                alerts = assess_missing_statements(config_path, p_spending_dir)
                # Only active mox should be flagged
                assert len(alerts) == 1
                assert "MOX" in alerts[0]
                assert "Missing statement" in alerts[0]
            finally:
                config_path.unlink()


class TestFlagOverduePayments:
    """Tests for flag_overdue_payments."""

    def test_no_pending_no_alerts(self) -> None:
        """Empty pending list -> no alerts."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            path = Path(f.name)

        try:
            alerts = flag_overdue_payments(path)
            assert alerts == []
        finally:
            path.unlink()

    def test_flag_overdue(self) -> None:
        """Overdue payments (days_until < 0) flagged as OVERDUE."""
        # We need to manually create a file with a past due date
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
pending:
- bank: mox
  amount: 1234.56
  due_date: 2020-01-01
  statement_date: 2019-12-01
  created: 2019-12-01
""")
            path = Path(f.name)

        try:
            alerts = flag_overdue_payments(path)
            assert len(alerts) == 1
            assert "OVERDUE" in alerts[0]
            assert "MOX" in alerts[0]
            assert "1,234.56" in alerts[0]
        finally:
            path.unlink()

    def test_invalid_date_skipped(self) -> None:
        """Entries with invalid dates are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
pending:
- bank: mox
  amount: 1234
  due_date: not-a-date
  statement_date: 2024-03-01
- bank: hsbc
  amount: 500
  statement_date: 2024-03-01
""")
            path = Path(f.name)

        try:
            alerts = flag_overdue_payments(path)
            assert len(alerts) == 0
        finally:
            path.unlink()
