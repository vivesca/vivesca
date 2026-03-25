"""HSBC Visa Signature statement PDF parser."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

from metabolon.spending.schema import StatementMeta, Transaction

# Lines that are continuation descriptors, not transactions
_SKIP_LINES = re.compile(
    r"^(APPLEPAY-|GOOGLEPAY-|OCTOPUSCARD:|CRI:|"
    r"\*EXCHANGERATE:|APPLE PAY|GOOGLE PAY)",
    re.IGNORECASE,
)

# Transaction line: DDMONDDMONdescription amount[CR]
_TXN_PAT = re.compile(r"^(\d{2}[A-Z]{3})(\d{2}[A-Z]{3})(.+)")

# Foreign currency amount pattern at end of description
_FX_PAT = re.compile(r"(USD|GBP|EUR|JPY|AUD|CAD|SGD|CNY)\s*([\d,]+\.\d{2})\s*([\d,]+\.\d{2})$")


def parse_hsbc(pdf_path: Path) -> tuple[StatementMeta, list[Transaction]]:
    """Parse an HSBC Visa Signature statement PDF.

    Returns (metadata, transactions). Raises ValueError if balance validation
    fails.
    """
    reader = PdfReader(pdf_path)

    full_text = ""
    for page in reader.pages:
        text = page.extract_text() or ""
        full_text += text + "\n"

    meta = _extract_metadata(full_text)
    txns = _parse_transactions(full_text, meta.statement_date[:4])

    # Balance validation against new transactions total (excluding prev balance and payments)
    spending_total = sum(t.hkd for t in txns)
    if abs(spending_total - meta.balance) > 0.02:
        msg = f"Balance mismatch: parsed {spending_total:.2f}, statement says {meta.balance:.2f}"
        raise ValueError(msg)

    return meta, txns


def _extract_metadata(text: str) -> StatementMeta:
    """Extract statement-level metadata from PDF text."""
    # Statement date + balance: "07MAR2025HKD26,119.50"
    m = re.search(
        r"Statementdate\s+Statementbalance\n(\d{2}[A-Z]{3}\d{4})HKD([\d,]+\.\d{2})",
        text,
    )
    stmt_date_raw = m.group(1) if m else ""
    balance_raw = m.group(2) if m else "0"

    statement_date = ""
    if stmt_date_raw:
        dt = datetime.strptime(stmt_date_raw, "%d%b%Y")
        statement_date = dt.strftime("%Y-%m-%d")

    balance = -float(balance_raw.replace(",", ""))

    # Credit limit
    cl_match = re.search(r"HSBCVisaSignatureHKD([\d,]+\.\d{2})", text)
    credit_limit = float(cl_match.group(1).replace(",", "")) if cl_match else 0.0

    # Minimum payment + due date
    mp_match = re.search(
        r"Total minimum payment due\s+HKD\n([\d,]+\.\d{2})\n(\d{2}[A-Z]{3}\d{4})",
        text,
    )
    minimum_due = 0.0
    due_date = ""
    if mp_match:
        minimum_due = float(mp_match.group(1).replace(",", ""))
        dt = datetime.strptime(mp_match.group(2), "%d%b%Y")
        due_date = dt.strftime("%Y-%m-%d")

    # Period: derive from first and last transaction dates
    # HSBC doesn't state the period explicitly
    all_trans_dates = re.findall(r"^(\d{2}[A-Z]{3})\d{2}[A-Z]{3}", text, re.MULTILINE)
    period_start = ""
    period_end = ""
    if all_trans_dates and statement_date:
        year = int(statement_date[:4])
        try:
            first_dt = _parse_hsbc_date(all_trans_dates[0], year)
            period_start = first_dt.strftime("%d %b %Y")
        except ValueError:
            pass
        period_end = datetime.strptime(statement_date, "%Y-%m-%d").strftime("%d %b %Y")

    return StatementMeta(
        bank="hsbc",
        card="HSBC Visa Signature",
        period_start=period_start,
        period_end=period_end,
        statement_date=statement_date,
        balance=balance,
        minimum_due=minimum_due,
        due_date=due_date,
        credit_limit=credit_limit,
    )


def _parse_hsbc_date(ddmon: str, year: int) -> datetime:
    """Parse HSBC 'DDMON' date format (e.g., '07FEB') with year context."""
    return datetime.strptime(f"{ddmon}{year}", "%d%b%Y")


def _parse_transactions(full_text: str, year_str: str) -> list[Transaction]:
    """Parse transaction lines from HSBC statement text."""
    year = int(year_str)
    lines = full_text.split("\n")

    raw_txns: list[dict] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        m = _TXN_PAT.match(line)
        if not m:
            continue

        post_date_raw = m.group(1)  # noqa: F841 — reserved for future use
        trans_date_raw = m.group(2)
        desc_amount = m.group(3)

        # Skip non-transaction lines
        if "PREVIOUSBALANCE" in desc_amount:
            continue
        if "PAYMENT-THANKYOU" in desc_amount or "PAYMENT - THANK YOU" in desc_amount:
            continue
        # Skip card number / account lines
        if re.match(r"^\d{16}", desc_amount):
            continue

        # DCC fee — merge with preceding transaction
        if "DCCFEE" in desc_amount or "DCC FEE" in desc_amount:
            amt_match = re.search(r"([\d,]+\.\d{2})$", desc_amount)
            if amt_match and raw_txns:
                fee = float(amt_match.group(1).replace(",", ""))
                raw_txns[-1]["hkd"] -= fee  # more negative = more spent
            continue

        # Determine if CR (credit)
        is_cr = desc_amount.rstrip().endswith("CR")
        if is_cr:
            desc_amount = desc_amount.rstrip()[:-2].rstrip()

        # Parse amount(s) — check for FX first
        foreign_amount = None
        foreign_currency = "HKD"
        hkd = 0.0

        fx_match = _FX_PAT.search(desc_amount)
        if fx_match:
            foreign_currency = fx_match.group(1)
            foreign_amount = float(fx_match.group(2).replace(",", ""))
            hkd = float(fx_match.group(3).replace(",", ""))
            desc_part = desc_amount[: fx_match.start()].rstrip()
        else:
            # HKD only — amount at end
            amt_match = re.search(r"([\d,]+\.\d{2})$", desc_amount)
            if not amt_match:
                continue
            hkd = float(amt_match.group(1).replace(",", ""))
            desc_part = desc_amount[: amt_match.start()].rstrip()

        # Apply sign: charges are negative, credits positive
        if is_cr:
            hkd = hkd  # credit = positive
            if foreign_amount is not None:
                foreign_amount = foreign_amount
        else:
            hkd = -hkd  # charge = negative
            if foreign_amount is not None:
                foreign_amount = -foreign_amount

        # Clean merchant name
        merchant = _clean_merchant(desc_part)

        # Parse transaction date
        trans_dt = _parse_hsbc_date(trans_date_raw, year)
        iso_date = trans_dt.strftime("%Y-%m-%d")

        raw_txns.append(
            {
                "date": iso_date,
                "merchant": merchant,
                "currency": foreign_currency,
                "foreign_amount": foreign_amount,
                "hkd": hkd,
            }
        )

    return [
        Transaction(
            date=t["date"],
            merchant=t["merchant"],
            category="",  # categorised later by pipeline
            currency=t["currency"],
            foreign_amount=t["foreign_amount"],
            hkd=t["hkd"],
        )
        for t in raw_txns
    ]


def _clean_merchant(raw: str) -> str:
    """Clean HSBC merchant description into a readable name."""
    name = raw.strip()

    # Remove trailing location info (HongKongHK, HONGKONGHK, etc.)
    # Common patterns: city+country code squished together
    name = re.sub(
        r"(?:Hong\s*Kong|HONGKONG|KOWLOONBAY|QUARRYBAY|TAIKOOSHING|"
        r"SHEUNGWAN|NORTHPOINT|CENTRALANDW|TSIMSHATSU|UBER\.COM/HK/E)"
        r"HK\s*$",
        "",
        name,
    ).rstrip()

    # Remove other trailing country indicators
    name = re.sub(
        r"(?:CORK|ITUNES\.COM)IE\s*$",
        lambda m: "ITUNES.COM" if "ITUNES" in m.group() else "",
        name,
    ).rstrip()

    name = re.sub(r"Amzn\.com/bill\s*$", "", name).rstrip()

    # Remove trailing US for US merchants
    name = re.sub(r"US\s*$", "", name).rstrip()

    # Remove trailing NL, etc.
    name = re.sub(r"(?:Amsterdam)?NL\s*$", "", name).rstrip()

    return name.strip()
