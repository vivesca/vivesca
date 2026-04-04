from __future__ import annotations

"""Detect which bank issued a credit card statement."""


import re

# Filename patterns for pre-filtering iCloud scan
_FILENAME_PATTERNS = [
    re.compile(r"HO-MING-TERRY-LI_.*_Mox_Credit_Statement\.pdf$"),
    re.compile(r"eStatementFile[_.].*\.pdf$"),
    re.compile(r"ECardPersonalStatement.*\.pdf$"),
    re.compile(r"\d{1,2}\s*月\.pdf$"),
]

# Page-1 text signatures for bank identification
_BANK_SIGNATURES: list[tuple[str, list[str]]] = [
    ("mox", ["Mox Credit statement"]),
    ("hsbc", ["HSBC", "VISA SIGNATURE"]),
    ("ccba", ["eye Credit Card"]),
    ("scb", ["SMART CREDIT CARD"]),
    ("boc", ["BOC Credit Card", "MONTHLY STATEMENT"]),
]


def filename_matches(filename: str) -> bool:
    """Check if a filename looks like a credit card statement."""
    return any(p.search(filename) for p in _FILENAME_PATTERNS)


def identify_bank(page1_text: str) -> str | None:
    """Identify the issuing bank from page 1 text.

    Returns bank key ('mox', 'hsbc', 'ccba') or None if unrecognised.
    """
    for bank, signatures in _BANK_SIGNATURES:
        if all(sig in page1_text for sig in signatures):
            return bank
    return None
