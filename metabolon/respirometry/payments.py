"""Payment tracking -- pending payments for non-autopay cards."""

from __future__ import annotations

import shutil
import subprocess
from datetime import datetime, timedelta, timezone, date
from pathlib import Path

import yaml

HKT = timezone(timedelta(hours=8))
FASTI_BINARY = shutil.which("fasti") or "fasti"


def restore_payments(payments_file: Path) -> list[dict]:
    """Load pending payments from YAML file."""
    if not payments_file.exists():
        return []
    data = yaml.safe_load(payments_file.read_text()) or {}
    return data.get("pending", []) or []


def persist_payments(payments_file: Path, pending: list[dict]) -> None:
    """Write pending payments back to YAML file."""
    payments_file.parent.mkdir(parents=True, exist_ok=True)
    content = "# Auto-managed by vivesca spending pipeline\n"
    data = {"pending": pending}
    content += yaml.dump(data, default_flow_style=False, sort_keys=False)
    payments_file.write_text(content)


def restore_card_config(config_file: Path) -> dict:
    """Load card autopay configuration."""
    if not config_file.exists():
        return {}
    data = yaml.safe_load(config_file.read_text()) or {}
    return data.get("cards", {})


def is_autopay(bank: str, config_file: Path) -> bool:
    """Check whether a card is on autopay."""
    cards = restore_card_config(config_file)
    card_cfg = cards.get(bank, {})
    return card_cfg.get("autopay", False)


def queue_payment(
    payments_file: Path,
    bank: str,
    amount: float,
    due_date: str,
    statement_date: str,
) -> dict:
    """Add a pending payment entry and return it."""
    pending = restore_payments(payments_file)

    # Avoid duplicate entries for same bank + statement_date
    for entry in pending:
        if entry.get("bank") == bank and entry.get("statement_date") == statement_date:
            return entry

    now = datetime.now(HKT)
    entry = {
        "bank": bank,
        "amount": amount,
        "due_date": due_date,
        "statement_date": statement_date,
        "created": now.strftime("%Y-%m-%d"),
    }
    pending.append(entry)
    persist_payments(payments_file, pending)
    return entry


def dequeue_payment(payments_file: Path, bank: str) -> dict | None:
    """Remove the oldest pending payment for a bank. Returns the removed entry or None."""
    pending = restore_payments(payments_file)
    for i, entry in enumerate(pending):
        if entry.get("bank") == bank:
            removed = pending.pop(i)
            persist_payments(payments_file, pending)
            return removed
    return None


def schedule_payment_reminder(
    bank: str,
    amount: float,
    due_date: str,
) -> str | None:
    """Create a fasti calendar event 3 days before due_date.

    Returns the fasti output or None on failure.
    """
    try:
        due = datetime.strptime(due_date, "%Y-%m-%d")
    except ValueError:
        return None

    reminder_date = due - timedelta(days=3)
    summary = f"Pay {bank.upper()} HKD {amount:,.2f}"
    date_str = reminder_date.strftime("%Y-%m-%d")

    try:
        result = subprocess.run(
            [
                str(FASTI_BINARY),
                "create",
                summary,
                "--date",
                date_str,
                "--from",
                "09:00",
                "--to",
                "09:30",
                "--description",
                f"Credit card payment due {due_date}. Amount: HKD {amount:,.2f}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def assess_missing_statements(
    config_file: Path,
    spending_dir: Path,
) -> list[str]:
    """Check for expected statements that haven't been processed yet.

    For each active card with a statement_day, if today is past that day
    and no statement file exists for the current month, flag it.
    """
    cards = restore_card_config(config_file)
    now = datetime.now(HKT).date()
    current_month = now.strftime("%Y-%m")
    alerts: list[str] = []

    for bank, cfg in cards.items():
        if not cfg.get("active", True):
            continue
        statement_day = cfg.get("statement_day")
        if not statement_day:
            continue

        # Grace period: 5 days after statement day for download/processing
        expected_by = statement_day + 5
        if now.day < expected_by:
            continue

        statement_file = spending_dir / f"{current_month}-{bank}.md"
        if not statement_file.exists():
            alerts.append(
                f"Missing statement: {bank.upper()} "
                f"(expected by day {statement_day}, not yet processed)"
            )

    return alerts


def flag_overdue_payments(payments_file: Path) -> list[str]:
    """Check for payments due within 2 days. Returns alert strings."""
    pending = restore_payments(payments_file)
    if not pending:
        return []

    now = datetime.now(HKT).date()
    alerts: list[str] = []

    for entry in pending:
        try:
            due_date_val = entry["due_date"]
            if isinstance(due_date_val, date):
                due = due_date_val
            elif isinstance(due_date_val, datetime):
                due = due_date_val.date()
            elif isinstance(due_date_val, str):
                due = datetime.strptime(due_date_val, "%Y-%m-%d").date()
            else:
                raise ValueError(f"Unexpected type {type(due_date_val)} for due_date")
        except (KeyError, ValueError):
            continue

        days_until = (due - now).days
        bank = entry.get("bank", "unknown").upper()
        amount = entry.get("amount", 0)

        if days_until < 0:
            alerts.append(f"OVERDUE: {bank} HKD {amount:,.2f} was due {entry['due_date']}")
        elif days_until <= 2:
            alerts.append(
                f"Payment due soon: {bank} HKD {amount:,.2f} due {entry['due_date']} "
                f"({days_until} day{'s' if days_until != 1 else ''} left)"
            )

    return alerts
