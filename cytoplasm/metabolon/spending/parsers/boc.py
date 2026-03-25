"""BOC Credit Card statement PDF parser."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

from metabolon.spending.schema import StatementMeta, Transaction

# Transaction line: DD-MON DD-MON description  location  HKG  amount [CR]
_TXN_PAT = re.compile(
    r"^(\d{2}-[A-Z]{3})\s+(\d{2}-[A-Z]{3})\s+(.+?)\s+([\d,]+\.\d{2})\s*(CR)?\s*$"
)

# Balance B/F line
_BALANCE_BF_PAT = re.compile(r"BALANCE B/F\s+([\d,]+\.\d{2})")

# ODD CENTS line
_ODD_CENTS_PAT = re.compile(r"ODD CENTS TO NEXT BILL\s+([\d,]+\.\d{2})\s*(CR)?")


def parse_boc(pdf_path: Path) -> tuple[StatementMeta, list[Transaction]]:
    """Parse a BOC Credit Card statement PDF.

    Returns (metadata, transactions). Raises ValueError if balance validation
    fails.
    """
    reader = PdfReader(pdf_path)

    full_text = ""
    for page in reader.pages:
        text = page.extract_text() or ""
        full_text += text + "\n"

    meta = _extract_metadata(full_text)
    txns = _parse_transactions(full_text, meta.statement_date)

    # Set period_start from earliest transaction
    if txns and not meta.period_start:
        dates = sorted(t.date for t in txns)
        meta.period_start = datetime.strptime(dates[0], "%Y-%m-%d").strftime("%d %b %Y")

    # Balance validation.
    # BOC balance = balance_bf + new_charges - refunds - payments - odd_cents
    # We parse new_charges and refunds as txns (skipping payments & odd_cents).
    # So: sum(txns) should equal -(balance - balance_bf + payments + odd_cents)
    balance_bf = _extract_balance_bf(full_text)
    payments = _extract_payments(full_text, meta.statement_date)
    odd_cents = _extract_odd_cents(full_text)

    expected = meta.balance - balance_bf - payments - odd_cents
    spending_total = sum(t.hkd for t in txns)
    if abs(spending_total - expected) > 0.02:
        msg = (
            f"Balance mismatch: parsed {spending_total:.2f}, "
            f"expected {expected:.2f} "
            f"(balance={meta.balance}, bf={balance_bf}, "
            f"payments={payments}, odd={odd_cents})"
        )
        raise ValueError(msg)

    return meta, txns


def _extract_metadata(text: str) -> StatementMeta:
    """Extract statement-level metadata from PDF text.

    BOC Payment Slip is a table where labels and values are on separate lines.
    Values appear as: HKD lines (limit, balance, min payment) then date lines.
    """
    lines = text.split("\n")

    # Find HKD value lines after Payment Slip — order: limit, balance, min payment
    hkd_values: list[float] = []
    date_values: list[str] = []
    in_slip = False
    for line in lines:
        if "Payment Slip" in line:
            in_slip = True
            continue
        if not in_slip:
            continue
        # Stop at first transaction-area marker
        if "Balance B/F" in line or "Gift Points" in line:
            break
        m_hkd = re.match(r"^HKD\s*([\d,]+\.\d{2})\s*$", line.strip())
        if m_hkd:
            hkd_values.append(float(m_hkd.group(1).replace(",", "")))
        m_date = re.match(r"^(\d{2}-[A-Z]{3}-\d{4})\s*$", line.strip())
        if m_date:
            date_values.append(m_date.group(1))

    credit_limit = hkd_values[0] if len(hkd_values) > 0 else 0.0
    balance = -hkd_values[1] if len(hkd_values) > 1 else 0.0
    minimum_due = hkd_values[2] if len(hkd_values) > 2 else 0.0

    statement_date = ""
    if len(date_values) > 0:
        dt = datetime.strptime(date_values[0], "%d-%b-%Y")
        statement_date = dt.strftime("%Y-%m-%d")

    due_date = ""
    if len(date_values) > 1:
        dt = datetime.strptime(date_values[1], "%d-%b-%Y")
        due_date = dt.strftime("%Y-%m-%d")

    # Card type — Chinese name on same line, English on next line
    card = "BOC Credit Card"
    card_match = re.search(r"Card Type:.*?\n(BOC .+?)(?:\n|$)", text)
    if card_match:
        card = card_match.group(1).strip()

    # Period: derive from transaction dates
    period_start = ""
    period_end = ""
    if statement_date:
        period_end = datetime.strptime(statement_date, "%Y-%m-%d").strftime("%d %b %Y")

    return StatementMeta(
        bank="boc",
        card=card,
        period_start=period_start,
        period_end=period_end,
        statement_date=statement_date,
        balance=balance,
        minimum_due=minimum_due,
        due_date=due_date,
        credit_limit=credit_limit,
    )


def _parse_transactions(full_text: str, statement_date: str) -> list[Transaction]:
    """Parse transaction lines from BOC statement text."""
    lines = full_text.split("\n")
    raw_txns: list[dict] = []

    # Determine the statement year from statement_date
    stmt_year = int(statement_date[:4]) if statement_date else datetime.now().year

    for line in lines:
        line = line.rstrip()

        # Skip non-transaction lines
        if "BALANCE B/F" in line:
            continue
        if "CURRENT BALANCE" in line:
            continue
        if "LAST ITEM" in line:
            continue
        if "ODD CENTS" in line:
            continue

        m = _TXN_PAT.match(line)
        if not m:
            continue

        trans_date_raw = m.group(2)  # DD-MON
        desc = m.group(3).strip()
        amount = float(m.group(4).replace(",", ""))
        is_cr = m.group(5) == "CR"

        # Skip payments (PPS PAYMENT, etc.)
        if "PPS PAYMENT" in desc.upper() and is_cr:
            continue

        # Parse transaction date — BOC uses DD-MON without year
        trans_date = _parse_short_date(trans_date_raw, stmt_year, statement_date)

        # Clean merchant
        merchant = _clean_merchant(desc)

        hkd = amount if is_cr else -amount

        raw_txns.append(
            {
                "date": trans_date,
                "merchant": merchant,
                "currency": "HKD",
                "foreign_amount": None,
                "hkd": hkd,
            }
        )

    return [
        Transaction(
            date=t["date"],
            merchant=t["merchant"],
            category="",
            currency=t["currency"],
            foreign_amount=t["foreign_amount"],
            hkd=t["hkd"],
        )
        for t in raw_txns
    ]


def _parse_short_date(raw: str, stmt_year: int, statement_date: str) -> str:
    """Parse DD-MON into ISO date, inferring year from statement context."""
    dt = datetime.strptime(f"{raw}-{stmt_year}", "%d-%b-%Y")
    # If the transaction month is after the statement month, it's previous year
    if statement_date:
        stmt_month = int(statement_date[5:7])
        if dt.month > stmt_month:
            dt = dt.replace(year=stmt_year - 1)
    return dt.strftime("%Y-%m-%d")


def _extract_balance_bf(text: str) -> float:
    """Extract previous balance brought forward (negative = owing)."""
    m = _BALANCE_BF_PAT.search(text)
    if m:
        return -float(m.group(1).replace(",", ""))
    return 0.0


def _extract_payments(text: str, statement_date: str) -> float:
    """Sum of payment credits (PPS, etc.) excluded from txn list."""
    total = 0.0
    for line in text.split("\n"):
        m = _TXN_PAT.match(line.rstrip())
        if m and "PPS PAYMENT" in m.group(3).upper() and m.group(5) == "CR":
            total += float(m.group(4).replace(",", ""))
    return total


def _extract_odd_cents(text: str) -> float:
    """Extract ODD CENTS TO NEXT BILL adjustment."""
    m = _ODD_CENTS_PAT.search(text)
    if m:
        val = float(m.group(1).replace(",", ""))
        return val if m.group(2) == "CR" else -val
    return 0.0


def _clean_merchant(desc: str) -> str:
    """Clean BOC merchant description into a readable name."""
    name = desc.strip()
    # Remove trailing location info: "HONG KONG     HKG" or "HONG KON HONG KONG     HKG"
    name = re.sub(r"\s+HONG KONG\s+HKG\s*$", "", name)
    name = re.sub(r"\s+HONG KON\s+HONG KONG\s*$", "", name)  # truncated variant
    # Remove trailing country codes
    name = re.sub(r"\s+[A-Z]{2,3}\s*$", "", name)
    # Collapse multiple spaces
    name = re.sub(r"\s{2,}", " ", name).strip()
    return name
