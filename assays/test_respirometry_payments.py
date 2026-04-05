from __future__ import annotations

"""Tests for metabolon.respirometry.payments — payment tracking module."""

import subprocess
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
import yaml

from metabolon.respirometry.payments import (
    HKT,
    assess_missing_statements,
    dequeue_payment,
    flag_overdue_payments,
    is_autopay,
    persist_payments,
    queue_payment,
    restore_card_config,
    restore_payments,
    schedule_payment_reminder,
)

if TYPE_CHECKING:
    from pathlib import Path

# ── fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def tmp_payments(tmp_path: Path) -> Path:
    return tmp_path / "payments.yaml"


@pytest.fixture
def tmp_config(tmp_path: Path) -> Path:
    return tmp_path / "cards.yaml"


@pytest.fixture
def sample_pending() -> list[dict]:
    return [
        {
            "bank": "hsbc",
            "amount": 5000.0,
            "due_date": "2026-04-15",
            "statement_date": "2026-03-15",
            "created": "2026-03-20",
        },
        {
            "bank": "citi",
            "amount": 3200.0,
            "due_date": "2026-04-20",
            "statement_date": "2026-03-18",
            "created": "2026-03-22",
        },
    ]


@pytest.fixture
def sample_cards_config() -> dict:
    return {
        "cards": {
            "hsbc": {"autopay": True, "active": True, "statement_day": 15},
            "citi": {"autopay": False, "active": True, "statement_day": 18},
            "sc": {"autopay": False, "active": False, "statement_day": 10},
        }
    }


# ── restore_payments ─────────────────────────────────────────────────


def test_restore_payments_empty_file(tmp_payments: Path):
    """Returns empty list when file does not exist."""
    assert restore_payments(tmp_payments) == []


def test_restore_payments_valid_yaml(tmp_payments: Path, sample_pending: list[dict]):
    """Loads pending entries from YAML file."""
    tmp_payments.write_text(yaml.dump({"pending": sample_pending}))
    result = restore_payments(tmp_payments)
    assert len(result) == 2
    assert result[0]["bank"] == "hsbc"


def test_restore_payments_empty_yaml(tmp_payments: Path):
    """Returns empty list for empty YAML file."""
    tmp_payments.write_text("")
    assert restore_payments(tmp_payments) == []


def test_restore_payments_no_pending_key(tmp_payments: Path):
    """Returns empty list when YAML has no 'pending' key."""
    tmp_payments.write_text(yaml.dump({"other": "data"}))
    assert restore_payments(tmp_payments) == []


# ── persist_payments ─────────────────────────────────────────────────


def test_persist_payments_creates_file(tmp_payments: Path, sample_pending: list[dict]):
    """Writes payments and creates parent directories."""
    assert not tmp_payments.exists()
    persist_payments(tmp_payments, sample_pending)
    assert tmp_payments.exists()
    data = yaml.safe_load(tmp_payments.read_text())
    assert len(data["pending"]) == 2


def test_persist_payments_header(tmp_payments: Path):
    """File starts with the expected header comment."""
    persist_payments(tmp_payments, [])
    content = tmp_payments.read_text()
    assert content.startswith("# Auto-managed by vivesca spending pipeline\n")


def test_persist_payments_roundtrip(tmp_payments: Path, sample_pending: list[dict]):
    """Data survives a write-then-read cycle."""
    persist_payments(tmp_payments, sample_pending)
    restored = restore_payments(tmp_payments)
    assert restored == sample_pending


# ── restore_card_config ──────────────────────────────────────────────


def test_restore_card_config_missing_file(tmp_config: Path):
    """Returns empty dict when config file does not exist."""
    assert restore_card_config(tmp_config) == {}


def test_restore_card_config_valid(tmp_config: Path, sample_cards_config: dict):
    """Loads the 'cards' sub-dict from YAML."""
    tmp_config.write_text(yaml.dump(sample_cards_config))
    result = restore_card_config(tmp_config)
    assert "hsbc" in result
    assert result["hsbc"]["autopay"] is True


# ── is_autopay ────────────────────────────────────────────────────────


def test_is_autopay_true(tmp_config: Path, sample_cards_config: dict):
    tmp_config.write_text(yaml.dump(sample_cards_config))
    assert is_autopay("hsbc", tmp_config) is True


def test_is_autopay_false(tmp_config: Path, sample_cards_config: dict):
    tmp_config.write_text(yaml.dump(sample_cards_config))
    assert is_autopay("citi", tmp_config) is False


def test_is_autopay_unknown_bank(tmp_config: Path, sample_cards_config: dict):
    tmp_config.write_text(yaml.dump(sample_cards_config))
    assert is_autopay("unknown_bank", tmp_config) is False


# ── queue_payment ────────────────────────────────────────────────────


def test_queue_payment_adds_entry(tmp_payments: Path):
    """Adds a new payment and persists it."""
    entry = queue_payment(tmp_payments, "hsbc", 5000.0, "2026-04-15", "2026-03-15")
    assert entry["bank"] == "hsbc"
    assert entry["amount"] == 5000.0
    assert entry["due_date"] == "2026-04-15"
    assert entry["statement_date"] == "2026-03-15"
    assert "created" in entry
    # File should have been written
    restored = restore_payments(tmp_payments)
    assert len(restored) == 1
    assert restored[0]["bank"] == "hsbc"


def test_queue_payment_no_duplicate(tmp_payments: Path):
    """Does not add a duplicate entry for same bank + statement_date."""
    queue_payment(tmp_payments, "hsbc", 5000.0, "2026-04-15", "2026-03-15")
    entry2 = queue_payment(tmp_payments, "hsbc", 6000.0, "2026-05-15", "2026-03-15")
    # Should return the original entry
    assert entry2["amount"] == 5000.0
    # Only one entry persisted
    restored = restore_payments(tmp_payments)
    assert len(restored) == 1


def test_queue_payment_different_statement_date(tmp_payments: Path):
    """Allows same bank with different statement_date."""
    queue_payment(tmp_payments, "hsbc", 5000.0, "2026-04-15", "2026-03-15")
    entry2 = queue_payment(tmp_payments, "hsbc", 6000.0, "2026-05-15", "2026-04-15")
    assert entry2["amount"] == 6000.0
    restored = restore_payments(tmp_payments)
    assert len(restored) == 2


# ── dequeue_payment ──────────────────────────────────────────────────


def test_dequeue_payment_removes_oldest(tmp_payments: Path, sample_pending: list[dict]):
    """Removes the first matching entry for the given bank."""
    persist_payments(tmp_payments, sample_pending)
    removed = dequeue_payment(tmp_payments, "hsbc")
    assert removed is not None
    assert removed["bank"] == "hsbc"
    assert removed["amount"] == 5000.0
    # Only citi should remain
    remaining = restore_payments(tmp_payments)
    assert len(remaining) == 1
    assert remaining[0]["bank"] == "citi"


def test_dequeue_payment_not_found(tmp_payments: Path, sample_pending: list[dict]):
    """Returns None when no entry exists for the given bank."""
    persist_payments(tmp_payments, sample_pending)
    removed = dequeue_payment(tmp_payments, "dbs")
    assert removed is None
    # Nothing should have been removed
    assert len(restore_payments(tmp_payments)) == 2


def test_dequeue_payment_empty_file(tmp_payments: Path):
    """Returns None when the payments file is empty."""
    removed = dequeue_payment(tmp_payments, "hsbc")
    assert removed is None


# ── schedule_payment_reminder ────────────────────────────────────────


@patch("metabolon.respirometry.payments.subprocess.run")
def test_schedule_payment_reminder_success(mock_run: MagicMock):
    """Returns stdout on successful fasti invocation."""
    mock_run.return_value = MagicMock(stdout="event-created-123\n", returncode=0)
    result = schedule_payment_reminder("hsbc", 5000.0, "2026-04-15")
    assert result == "event-created-123"
    # Reminder is 3 days before due: 2026-04-12
    call_args = mock_run.call_args[0][0]
    assert "--date" in call_args
    idx = call_args.index("--date")
    assert call_args[idx + 1] == "2026-04-12"


@patch("metabolon.respirometry.payments.subprocess.run")
def test_schedule_payment_reminder_summary_format(mock_run: MagicMock):
    """Summary includes bank name uppercased and formatted amount."""
    mock_run.return_value = MagicMock(stdout="ok\n", returncode=0)
    schedule_payment_reminder("citi", 1234.56, "2026-05-01")
    call_args = mock_run.call_args[0][0]
    summary = call_args[2]
    assert "CITI" in summary
    assert "1,234.56" in summary


@patch("metabolon.respirometry.payments.subprocess.run")
def test_schedule_payment_reminder_fasti_failure(mock_run: MagicMock):
    """Returns None when fasti returns non-zero exit code."""
    mock_run.return_value = MagicMock(stdout="", returncode=1)
    result = schedule_payment_reminder("hsbc", 100.0, "2026-04-15")
    assert result is None


def test_schedule_payment_reminder_invalid_date():
    """Returns None for unparsable due_date."""
    result = schedule_payment_reminder("hsbc", 100.0, "not-a-date")
    assert result is None


@patch("metabolon.respirometry.payments.subprocess.run")
def test_schedule_payment_reminder_timeout(mock_run: MagicMock):
    """Returns None when fasti times out."""
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="fasti", timeout=30)
    result = schedule_payment_reminder("hsbc", 100.0, "2026-04-15")
    assert result is None


@patch("metabolon.respirometry.payments.subprocess.run")
def test_schedule_payment_reminder_not_found(mock_run: MagicMock):
    """Returns None when fasti binary is not found."""
    mock_run.side_effect = FileNotFoundError
    result = schedule_payment_reminder("hsbc", 100.0, "2026-04-15")
    assert result is None


# ── helpers for date-relative tests ──────────────────────────────────


def _today() -> date:
    """Return today's date in HKT."""
    return datetime.now(HKT).date()


def _fmt(d: date) -> str:
    return d.strftime("%Y-%m-%d")


# ── assess_missing_statements ────────────────────────────────────────


def test_assess_missing_statements_flags_missing(tmp_config: Path, tmp_path: Path):
    """Flags cards past their grace period with no statement file."""
    today = _today()
    # statement_day well in the past → grace period definitely passed
    config = {
        "cards": {
            "hsbc": {"active": True, "statement_day": 1},
            "citi": {"active": True, "statement_day": 28},  # grace=28+5=33, always > today.day
        }
    }
    tmp_config.write_text(yaml.dump(config))
    spending_dir = tmp_path / "spending"
    spending_dir.mkdir()

    alerts = assess_missing_statements(tmp_config, spending_dir)
    # hsbc: day 1, grace=6. If today.day >= 6 (almost always), flagged.
    # citi: day 28, grace=33. Never flagged (max day is 31).
    hsbc_alerts = [a for a in alerts if "HSBC" in a]
    if today.day >= 6:
        assert len(hsbc_alerts) == 1
        assert "Missing statement" in hsbc_alerts[0]
    else:
        # Edge case: day 1-5 of month, grace period not elapsed
        assert len(hsbc_alerts) == 0


def test_assess_missing_statements_skips_inactive(tmp_config: Path, tmp_path: Path):
    """Does not flag inactive cards."""
    config = {
        "cards": {
            "sc": {"active": False, "statement_day": 1},
        }
    }
    tmp_config.write_text(yaml.dump(config))
    spending_dir = tmp_path / "spending"
    spending_dir.mkdir()

    alerts = assess_missing_statements(tmp_config, spending_dir)
    assert not any("SC" in a for a in alerts)


def test_assess_missing_statements_statement_exists(tmp_config: Path, tmp_path: Path):
    """Does not flag when statement file already exists."""
    today = _today()
    config = {
        "cards": {
            "hsbc": {"active": True, "statement_day": 1},
        }
    }
    tmp_config.write_text(yaml.dump(config))
    spending_dir = tmp_path / "spending"
    spending_dir.mkdir()
    # Create the expected statement file for current month
    (spending_dir / f"{today.strftime('%Y-%m')}-hsbc.md").write_text("statement data")

    alerts = assess_missing_statements(tmp_config, spending_dir)
    assert len(alerts) == 0


# ── flag_overdue_payments ────────────────────────────────────────────


def test_flag_overdue_overdue(tmp_payments: Path):
    """Flags payments that are past due."""
    today = _today()
    past_due = _fmt(today - timedelta(days=5))
    pending = [
        {"bank": "hsbc", "amount": 5000.0, "due_date": past_due},
    ]
    persist_payments(tmp_payments, pending)
    alerts = flag_overdue_payments(tmp_payments)
    assert len(alerts) == 1
    assert "OVERDUE" in alerts[0]
    assert "HSBC" in alerts[0]


def test_flag_overdue_due_soon(tmp_payments: Path):
    """Flags payments due within 2 days."""
    today = _today()
    soon_due = _fmt(today + timedelta(days=1))
    pending = [
        {"bank": "citi", "amount": 3200.0, "due_date": soon_due},
    ]
    persist_payments(tmp_payments, pending)
    alerts = flag_overdue_payments(tmp_payments)
    assert len(alerts) == 1
    assert "due soon" in alerts[0].lower()
    assert "CITI" in alerts[0]


def test_flag_overdue_no_alert_when_far(tmp_payments: Path):
    """No alert when payment is more than 2 days away."""
    today = _today()
    far_due = _fmt(today + timedelta(days=10))
    pending = [
        {"bank": "hsbc", "amount": 5000.0, "due_date": far_due},
    ]
    persist_payments(tmp_payments, pending)
    alerts = flag_overdue_payments(tmp_payments)
    assert len(alerts) == 0


def test_flag_overdue_empty_payments(tmp_payments: Path):
    """Returns empty list when there are no pending payments."""
    alerts = flag_overdue_payments(tmp_payments)
    assert alerts == []


def test_flag_overdue_date_object(tmp_payments: Path):
    """Handles due_date stored as a date object."""
    today = _today()
    pending = [
        {"bank": "hsbc", "amount": 5000.0, "due_date": today - timedelta(days=5)},
    ]
    persist_payments(tmp_payments, pending)
    alerts = flag_overdue_payments(tmp_payments)
    assert len(alerts) == 1
    assert "OVERDUE" in alerts[0]


def test_flag_overdue_datetime_object(tmp_payments: Path):
    """Handles due_date stored as a datetime object."""
    today = _today()
    pending = [
        {
            "bank": "hsbc",
            "amount": 5000.0,
            "due_date": datetime.combine(today - timedelta(days=5), datetime.min.time()),
        },
    ]
    persist_payments(tmp_payments, pending)
    alerts = flag_overdue_payments(tmp_payments)
    assert len(alerts) == 1
    assert "OVERDUE" in alerts[0]


def test_flag_overdue_exactly_1_day(tmp_payments: Path):
    """Uses singular 'day' when exactly 1 day left."""
    today = _today()
    one_day_ahead = _fmt(today + timedelta(days=1))
    pending = [
        {"bank": "citi", "amount": 1000.0, "due_date": one_day_ahead},
    ]
    persist_payments(tmp_payments, pending)
    alerts = flag_overdue_payments(tmp_payments)
    assert len(alerts) == 1
    assert "1 day left" in alerts[0]
    # "days left" should not appear (singular form used)
    assert "days left" not in alerts[0].replace("1 day left", "")
