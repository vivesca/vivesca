# Spending Metabolism Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Parse credit card statement PDFs from Mox, HSBC, and CCBA into structured markdown in the vault, with fraud/budget/subscription monitors.

**Architecture:** A `spending/` domain package under vivesca handles parsing (per-bank regex modules), categorisation (YAML map), vault writing (markdown), and monitoring (deterministic Python). A thin MCP tool (`spending_sense.py`) delegates to the package. A metabolism substrate provides periodic trend analysis.

**Tech Stack:** Python, pypdf, pyyaml, regex, pytest. Integrates with vivesca's fastmcp tool framework and metabolism substrate protocol.

**Spec:** `docs/superpowers/specs/2026-03-23-spending-metabolism-design.md`

**Note:** The spec references a single `parser.py` for dispatch + schema. This plan refines that into `schema.py`, `detect.py`, and `parsers/__init__.py` for better separation. Update the spec's Code Location section post-implementation.

---

## File Structure

```
~/code/vivesca/
├── src/vivesca/
│   ├── spending/                          # NEW — domain package
│   │   ├── __init__.py                    # public API: parse_statement, scan_and_process
│   │   ├── schema.py                     # Transaction, StatementMeta dataclasses
│   │   ├── detect.py                     # bank detection (filename + page-1 text)
│   │   ├── parsers/
│   │   │   ├── __init__.py               # parser registry
│   │   │   ├── mox.py                    # Mox Credit parser
│   │   │   ├── hsbc.py                   # HSBC Visa Signature parser
│   │   │   └── ccba.py                   # CCBA eye Credit Card parser
│   │   ├── categories.py                 # load YAML, prefix-match categorisation
│   │   ├── vault.py                      # write markdown, move PDF, dedup
│   │   └── monitors.py                   # fraud, budget, subscription checks
│   ├── tools/spending_sense.py            # NEW — MCP tool
│   └── metabolism/substrates/
│       ├── __init__.py                    # MODIFY — register spending substrate
│       └── spending.py                    # NEW — metabolism substrate
├── tests/
│   ├── test_spending_schema.py
│   ├── test_spending_detect.py
│   ├── test_spending_parser_mox.py
│   ├── test_spending_parser_hsbc.py
│   ├── test_spending_parser_ccba.py
│   ├── test_spending_categories.py
│   ├── test_spending_vault.py
│   ├── test_spending_monitors.py
│   └── test_spending_tool.py
└── pyproject.toml                         # MODIFY — add pypdf dependency
```

Vault files (created at runtime, not in code repo):
```
~/notes/Spending/
├── config.yaml
├── categories.yaml
├── .processed                             # SHA-256 dedup ledger
├── statements/                            # archived PDFs
```

---

### Task 1: Schema and project setup

**Files:**
- Create: `src/vivesca/spending/__init__.py`
- Create: `src/vivesca/spending/schema.py`
- Create: `tests/test_spending_schema.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add pypdf dependency**

In `pyproject.toml`, add `"pypdf>=4.0"` to the `dependencies` list.

- [ ] **Step 2: Write schema tests**

```python
# tests/test_spending_schema.py
"""Tests for spending transaction schema."""

from vivesca.spending.schema import Transaction, StatementMeta


def test_transaction_charge():
    t = Transaction(
        date="2025-01-02",
        merchant="SMOL AI COMPANY",
        category="Tech/AI",
        currency="USD",
        foreign_amount=-20.00,
        hkd=-158.40,
    )
    assert t.is_charge
    assert not t.is_credit


def test_transaction_credit():
    t = Transaction(
        date="2025-01-12",
        merchant="LI HO MING TERRY",
        category="Transfer",
        currency="HKD",
        foreign_amount=None,
        hkd=8450.20,
    )
    assert t.is_credit
    assert not t.is_charge


def test_transaction_hkd_only():
    t = Transaction(
        date="2025-01-08",
        merchant="SMARTONE",
        category="Telecom",
        currency="HKD",
        foreign_amount=None,
        hkd=-168.00,
    )
    assert t.foreign_amount is None
    assert t.currency == "HKD"


def test_statement_meta():
    m = StatementMeta(
        bank="mox",
        card="Mox Credit",
        period_start="31 Dec 2024",
        period_end="30 Jan 2025",
        statement_date="2025-01-30",
        balance=-6004.03,
        minimum_due=220.00,
        due_date="2025-02-24",
        credit_limit=108000.00,
    )
    assert m.bank == "mox"
    assert m.filename_stem == "2025-01-mox"


def test_statement_meta_filename_from_date():
    m = StatementMeta(
        bank="hsbc",
        card="HSBC Visa Signature",
        period_start="07 Jan 2025",
        period_end="06 Feb 2025",
        statement_date="2025-02-06",
        balance=-46417.99,
        minimum_due=469.00,
        due_date="2025-03-04",
        credit_limit=60000.00,
    )
    assert m.filename_stem == "2025-02-hsbc"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_schema.py -v`
Expected: FAIL — module not found

- [ ] **Step 4: Create the spending package and schema**

```python
# src/vivesca/spending/__init__.py
"""Spending metabolism — credit card statement parsing and monitoring."""
```

```python
# src/vivesca/spending/schema.py
"""Transaction and statement metadata schema."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Transaction:
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
class StatementMeta:
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
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_schema.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
cd ~/code/vivesca
git add src/vivesca/spending/__init__.py src/vivesca/spending/schema.py tests/test_spending_schema.py pyproject.toml
git commit -m "feat(spending): add transaction schema and project setup"
```

---

### Task 2: Bank detection

**Files:**
- Create: `src/vivesca/spending/detect.py`
- Create: `tests/test_spending_detect.py`

- [ ] **Step 1: Write detection tests**

```python
# tests/test_spending_detect.py
"""Tests for bank detection from PDF filename and page-1 text."""

from vivesca.spending.detect import detect_bank, filename_matches


def test_filename_mox():
    assert filename_matches("HO-MING-TERRY-LI_Jan2025_Mox_Credit_Statement.pdf")


def test_filename_hsbc():
    assert filename_matches("eStatementFile_20250315064205.pdf")


def test_filename_ccba():
    assert filename_matches("ECardPersonalStatement_HK_123_20250908_read.pdf")


def test_filename_random_pdf():
    assert not filename_matches("Terry Li - CV.pdf")


def test_detect_mox_from_text():
    text = "Page 1 of 5\nMox Credit statement\nMox Credit 月結單"
    assert detect_bank(text) == "mox"


def test_detect_hsbc_from_text():
    text = "HSBC\nSTATEMENT OF HSBC VISA SIGNATURE CARD ACCOUNT"
    assert detect_bank(text) == "hsbc"


def test_detect_ccba_from_text():
    text = "中国建设银行(亚洲)\nChina Construction Bank"
    assert detect_bank(text) == "ccba"


def test_detect_unknown():
    text = "Some random PDF text"
    assert detect_bank(text) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_detect.py -v`
Expected: FAIL

- [ ] **Step 3: Implement detection**

```python
# src/vivesca/spending/detect.py
"""Detect which bank issued a credit card statement."""

from __future__ import annotations

import re

# Filename patterns for pre-filtering iCloud scan
_FILENAME_PATTERNS = [
    re.compile(r"HO-MING-TERRY-LI_.*_Mox_Credit_Statement\.pdf$"),
    re.compile(r"eStatementFile[_.].*\.pdf$"),
    re.compile(r"ECardPersonalStatement.*\.pdf$"),
]

# Page-1 text signatures for bank identification
_BANK_SIGNATURES: list[tuple[str, list[str]]] = [
    ("mox", ["Mox Credit statement"]),
    ("hsbc", ["HSBC", "VISA SIGNATURE"]),
    ("ccba", ["中国建设银行"]),
]


def filename_matches(filename: str) -> bool:
    """Check if a filename looks like a credit card statement."""
    return any(p.search(filename) for p in _FILENAME_PATTERNS)


def detect_bank(page1_text: str) -> str | None:
    """Identify the issuing bank from page 1 text.

    Returns bank key ('mox', 'hsbc', 'ccba') or None if unrecognised.
    """
    for bank, signatures in _BANK_SIGNATURES:
        if all(sig in page1_text for sig in signatures):
            return bank
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_detect.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
cd ~/code/vivesca
git add src/vivesca/spending/detect.py tests/test_spending_detect.py
git commit -m "feat(spending): bank detection from filename and page-1 text"
```

---

### Task 3: Categories (YAML map + prefix matching)

**Files:**
- Create: `src/vivesca/spending/categories.py`
- Create: `tests/test_spending_categories.py`

- [ ] **Step 1: Write category tests**

```python
# tests/test_spending_categories.py
"""Tests for merchant categorisation."""

from vivesca.spending.categories import categorise, load_categories


def test_exact_prefix_match():
    cats = {"GOOGLE": "Tech/Subscriptions", "GITHUB": "Tech/Dev Tools"}
    assert categorise("GOOGLE", cats) == "Tech/Subscriptions"


def test_case_insensitive():
    cats = {"SMARTONE": "Telecom"}
    assert categorise("SmarTone", cats) == "Telecom"
    assert categorise("smartone", cats) == "Telecom"


def test_prefix_match():
    cats = {"PAYPAL *GIVEWELL": "Charity/Donation"}
    assert categorise("PAYPAL *GIVEWELL 4029357733", cats) == "Charity/Donation"


def test_uncategorised():
    cats = {"GOOGLE": "Tech/Subscriptions"}
    assert categorise("UNKNOWN MERCHANT", cats) == "Uncategorised"


def test_first_match_wins():
    cats = {"GOOGLE": "Tech/Subscriptions", "GOOGLE CLOUD": "Tech/Infrastructure"}
    assert categorise("GOOGLE CLOUD PLATFORM", cats) == "Tech/Subscriptions"


def test_load_categories(tmp_path):
    yaml_file = tmp_path / "categories.yaml"
    yaml_file.write_text("GOOGLE: Tech/Subscriptions\nSMARTONE: Telecom\n")
    cats = load_categories(yaml_file)
    assert cats["GOOGLE"] == "Tech/Subscriptions"
    assert cats["SMARTONE"] == "Telecom"


def test_load_categories_missing_file(tmp_path):
    cats = load_categories(tmp_path / "nonexistent.yaml")
    assert cats == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_categories.py -v`
Expected: FAIL

- [ ] **Step 3: Implement categories**

```python
# src/vivesca/spending/categories.py
"""Merchant categorisation via YAML prefix map."""

from __future__ import annotations

from pathlib import Path

import yaml


def load_categories(path: Path) -> dict[str, str]:
    """Load merchant → category map from YAML file."""
    if not path.exists():
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def categorise(merchant: str, categories: dict[str, str]) -> str:
    """Match merchant name against category map (case-insensitive prefix).

    First match wins. Returns 'Uncategorised' if no match.
    """
    upper = merchant.upper()
    for prefix, category in categories.items():
        if upper.startswith(prefix.upper()):
            return category
    return "Uncategorised"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_categories.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
cd ~/code/vivesca
git add src/vivesca/spending/categories.py tests/test_spending_categories.py
git commit -m "feat(spending): YAML-based merchant categorisation"
```

---

### Task 4: Mox parser

**Files:**
- Create: `src/vivesca/spending/parsers/__init__.py`
- Create: `src/vivesca/spending/parsers/mox.py`
- Create: `tests/test_spending_parser_mox.py`
- Create: `tests/fixtures/` (copy test PDFs)

- [ ] **Step 1: Set up test fixtures**

Copy the Mox test PDF to the test fixtures directory:

```bash
cd ~/code/vivesca
mkdir -p tests/fixtures
cp "/Users/terry/Library/Mobile Documents/com~apple~CloudDocs/HO-MING-TERRY-LI_Jan2025_Mox_Credit_Statement.pdf" tests/fixtures/mox_jan2025.pdf
```

- [ ] **Step 2: Write Mox parser tests**

```python
# tests/test_spending_parser_mox.py
"""Tests for Mox Credit statement parser."""

from pathlib import Path

import pytest

from vivesca.spending.parsers.mox import parse_mox
from vivesca.spending.schema import StatementMeta, Transaction

FIXTURE = Path(__file__).parent / "fixtures" / "mox_jan2025.pdf"


@pytest.mark.skipif(not FIXTURE.exists(), reason="test fixture not available")
class TestMoxParser:
    def setup_method(self):
        self.meta, self.txns = parse_mox(FIXTURE)

    def test_returns_metadata(self):
        assert isinstance(self.meta, StatementMeta)
        assert self.meta.bank == "mox"
        assert self.meta.card == "Mox Credit"

    def test_statement_date(self):
        assert self.meta.statement_date == "2025-01-30"

    def test_period(self):
        assert self.meta.period_start == "31 Dec 2024"
        assert self.meta.period_end == "30 Jan 2025"

    def test_balance(self):
        assert self.meta.balance == -6004.03

    def test_credit_limit(self):
        assert self.meta.credit_limit == 108000.00

    def test_due_date(self):
        assert self.meta.due_date == "2025-02-24"

    def test_transaction_count(self):
        # 20 spending transactions (excluding internal transfer)
        charges = [t for t in self.txns if t.is_charge]
        assert len(charges) == 20

    def test_total_matches_balance(self):
        """Critical integrity check: parsed total must match statement balance."""
        total = sum(t.hkd for t in self.txns if t.category != "Transfer")
        assert abs(total - self.meta.balance) < 0.02  # float tolerance

    def test_foreign_currency_parsed(self):
        usd_txns = [t for t in self.txns if t.currency == "USD"]
        assert len(usd_txns) > 0
        for t in usd_txns:
            assert t.foreign_amount is not None

    def test_merchant_names_clean(self):
        merchants = [t.merchant for t in self.txns]
        # No trailing amounts in merchant names
        for m in merchants:
            assert not m.endswith(".00"), f"Merchant has trailing amount: {m}"
            assert not m.endswith(".40"), f"Merchant has trailing amount: {m}"

    def test_internal_transfer_excluded(self):
        """Internal Mox transfers should not appear as spending."""
        merchants = [t.merchant for t in self.txns]
        assert not any("Move between" in m for m in merchants)

    def test_known_merchants(self):
        merchants = {t.merchant for t in self.txns}
        assert "SMARTONE" in merchants
        assert "Bowtie Life Insurance" in merchants
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_parser_mox.py -v`
Expected: FAIL — module not found

- [ ] **Step 4: Implement Mox parser**

```python
# src/vivesca/spending/parsers/__init__.py
"""Bank-specific statement parsers."""
```

```python
# src/vivesca/spending/parsers/mox.py
"""Mox Credit statement PDF parser."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from pypdf import PdfReader

from vivesca.spending.schema import StatementMeta, Transaction


def parse_mox(pdf_path: Path) -> tuple[StatementMeta, list[Transaction]]:
    """Parse a Mox Credit statement PDF.

    Returns (metadata, transactions). Raises ValueError if balance validation
    fails.
    """
    reader = PdfReader(pdf_path)

    # Extract text from transaction pages only
    full_text = ""
    for page in reader.pages:
        text = page.extract_text() or ""
        if "Repayment calculator" in text or "Rate summary" in text:
            break
        full_text += text + "\n"

    meta = _extract_metadata(full_text)
    txns = _parse_transactions(full_text, meta.statement_date[:4])

    # Balance validation: spending transactions must sum to statement balance
    spending_total = sum(t.hkd for t in txns if t.category != "Transfer")
    if abs(spending_total - meta.balance) > 0.02:
        msg = (
            f"Balance mismatch: parsed {spending_total:.2f}, "
            f"statement says {meta.balance:.2f}"
        )
        raise ValueError(msg)

    return meta, txns


def _extract_metadata(text: str) -> StatementMeta:
    """Extract statement-level metadata from page 1."""
    period_match = re.search(
        r"(\d{1,2} \w+ \d{4})\s*-\s*(\d{1,2} \w+ \d{4})", text
    )
    period_start = period_match.group(1) if period_match else ""
    period_end = period_match.group(2) if period_match else ""

    # Parse period_end to ISO date
    statement_date = ""
    if period_end:
        dt = datetime.strptime(period_end, "%d %b %Y")
        statement_date = dt.strftime("%Y-%m-%d")

    credit_limit = _extract_float(
        r"Total credit limit[^:]*:\s*([\d,]+\.\d{2})", text
    )
    balance = _extract_float(
        r"(-?[\d,]+\.\d{2})\s*HKD\s*\nStatement balance", text
    )
    minimum_due = _extract_float(
        r"([\d,]+\.\d{2})\s*HKD\s*\nMinimum amount due", text
    )
    due_date_match = re.search(
        r"(\d{1,2} \w+ \d{4})\s*\nPayment due date", text
    )
    due_date = ""
    if due_date_match:
        dt = datetime.strptime(due_date_match.group(1), "%d %b %Y")
        due_date = dt.strftime("%Y-%m-%d")

    return StatementMeta(
        bank="mox",
        card="Mox Credit",
        period_start=period_start,
        period_end=period_end,
        statement_date=statement_date,
        balance=balance,
        minimum_due=minimum_due,
        due_date=due_date,
        credit_limit=credit_limit,
    )


def _extract_float(pattern: str, text: str) -> float:
    m = re.search(pattern, text)
    return float(m.group(1).replace(",", "")) if m else 0.0


def _parse_transactions(full_text: str, year: str) -> list[Transaction]:
    """Parse transaction blocks from extracted PDF text."""
    # Remove page headers
    text = re.sub(r"Page \d+ of \d+", "", full_text)
    text = re.sub(
        r"Activity date\n交易⽇期Settlement date\n結算⽇期Description\n詳情"
        r"Foreign currency amount\n外幣⾦額Amount \(HKD\)\n⾦額\s+\(港幣\s*\)",
        "",
        text,
    )

    date_pat = r"(\d{2} \w{3}) (\d{2} \w{3})"
    parts = re.split(f"(?={date_pat})", text)

    transactions: list[Transaction] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        m = re.match(date_pat, part)
        if not m:
            continue

        activity_date_raw = m.group(1)
        rest = part[m.end() :].strip()

        # Internal transfers — skip
        if "Move between own Mox" in rest:
            continue

        # Extract amounts
        amounts = re.findall(r"(-?[\d,]+\.\d{2})", rest)
        if not amounts:
            continue

        hkd = float(amounts[-1].replace(",", ""))

        # Foreign currency
        foreign_amount = None
        foreign_currency = "HKD"
        fx_match = re.search(
            r"(-?[\d,]+\.\d{2})\s+(USD|GBP|EUR|JPY|AUD|CAD|SGD|CNY)\b",
            rest,
        )
        if fx_match and len(amounts) >= 2:
            foreign_amount = float(fx_match.group(1).replace(",", ""))
            foreign_currency = fx_match.group(2)

        # Merchant name — first line, cleaned
        desc_lines = rest.split("\n")
        merchant_raw = desc_lines[0].strip()
        merchant_raw = re.sub(r"\s+-?[\d,]+\.\d{2}\s*$", "", merchant_raw)
        merchant = re.sub(
            r"\s*\+\d[\d\s]*\w{2,3}\s*$", "", merchant_raw
        ).strip()
        merchant = re.sub(
            r"\s+(USA|GBR|IRL|CAN|HKG|AUS|SGP|JPN|NEW)\s*$",
            "",
            merchant,
        ).strip()
        merchant = re.sub(r"\s+(GOO|II)\s*$", "", merchant).strip()

        # Parse date to ISO
        dt = datetime.strptime(f"{activity_date_raw} {year}", "%d %b %Y")
        iso_date = dt.strftime("%Y-%m-%d")

        transactions.append(
            Transaction(
                date=iso_date,
                merchant=merchant,
                category="",  # categorised later by pipeline
                currency=foreign_currency,
                foreign_amount=foreign_amount,
                hkd=hkd,
            )
        )

    return transactions
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_parser_mox.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
cd ~/code/vivesca
git add src/vivesca/spending/parsers/ tests/test_spending_parser_mox.py tests/fixtures/
git commit -m "feat(spending): Mox Credit PDF parser with balance validation"
```

---

### Task 5: HSBC parser

**Files:**
- Create: `src/vivesca/spending/parsers/hsbc.py`
- Create: `tests/test_spending_parser_hsbc.py`

- [ ] **Step 1: Copy HSBC test fixtures**

```bash
cd ~/code/vivesca
cp "/Users/terry/Library/Mobile Documents/com~apple~CloudDocs/eStatementFile_20250315064205.pdf" tests/fixtures/hsbc_mar2025.pdf
cp "/Users/terry/Library/Mobile Documents/com~apple~CloudDocs/eStatementFile_20250209154654.pdf" tests/fixtures/hsbc_feb2025.pdf
```

- [ ] **Step 2: Examine the raw PDF text structure**

```bash
cd ~/code/vivesca && python3 -c "
from pypdf import PdfReader
r = PdfReader('tests/fixtures/hsbc_mar2025.pdf')
for i, p in enumerate(r.pages[:3]):
    print(f'=== PAGE {i+1} ===')
    print(repr(p.extract_text()[:2000]))
    print()
"
```

Study the output to understand the exact text layout before writing the parser. HSBC uses fixed-width columns; the regex patterns will differ from Mox.

- [ ] **Step 3: Write HSBC parser tests**

Write tests following the same pattern as `test_spending_parser_mox.py`:
- Test metadata extraction (bank="hsbc", card, dates, balance)
- Test transaction count
- Test balance validation (new transactions total, excluding PREVIOUS BALANCE and payments)
- Test merchant name cleaning (strip GOOGLE PAY-DEVICE, APPLE PAY-MOBILE suffixes)
- Test DCC fee merging
- Test that PREVIOUS BALANCE and PPS PAYMENT are excluded

Use the real fixture PDF. Adapt assertions to match the actual data visible in the PDF (statement date 07 Mar 2025, balance HKD26,119.50).

- [ ] **Step 4: Implement HSBC parser**

Follow the same structure as `mox.py`:
- `parse_hsbc(pdf_path) -> tuple[StatementMeta, list[Transaction]]`
- `_extract_metadata(text) -> StatementMeta`
- `_parse_transactions(text, year) -> list[Transaction]`
- Balance validation against new transactions total

Key differences from Mox:
- HSBC has "PREVIOUS BALANCE" as first line — this is carried forward, not a transaction
- Payments show as "PPS PAYMENT - THANK YOU" with CR suffix — filter out
- "DCC FEE-NON-HK MERCHANT" lines are surcharges — merge with preceding transaction
- Dates are `DDMON` format (e.g. `07FEB`, `10JAN`) not `DD Mon`
- Amount column is right-aligned, `CR` suffix means credit
- Multi-line descriptions include merchant location and payment device

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_parser_hsbc.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
cd ~/code/vivesca
git add src/vivesca/spending/parsers/hsbc.py tests/test_spending_parser_hsbc.py tests/fixtures/hsbc_*.pdf
git commit -m "feat(spending): HSBC Visa Signature PDF parser"
```

---

### Task 6: CCBA parser

**Files:**
- Create: `src/vivesca/spending/parsers/ccba.py`
- Create: `tests/test_spending_parser_ccba.py`

- [ ] **Step 1: Copy CCBA test fixture**

```bash
cd ~/code/vivesca
cp "/Users/terry/Library/Mobile Documents/com~apple~CloudDocs/ECardPersonalStatement_HK_2451800001579614051_20250908_read.pdf" tests/fixtures/ccba_sep2025.pdf
```

- [ ] **Step 2: Examine the raw PDF text structure**

```bash
cd ~/code/vivesca && python3 -c "
from pypdf import PdfReader
r = PdfReader('tests/fixtures/ccba_sep2025.pdf')
for i, p in enumerate(r.pages[:2]):
    print(f'=== PAGE {i+1} ===')
    print(repr(p.extract_text()[:2000]))
    print()
"
```

- [ ] **Step 3: Write CCBA parser tests**

Test metadata extraction, transaction count, balance validation, payment exclusion ("PPS PAYMENT - THANK YOU"), cross-border fee merging ("FEE - CROSS-BORDER TXN IN HKD"), and foreign currency line merging.

Use the real fixture. Adapt assertions to actual data (statement date Sep 07 2025, balance HKD 2,021.59).

- [ ] **Step 4: Implement CCBA parser**

`parse_ccba(pdf_path) -> tuple[StatementMeta, list[Transaction]]`

Key differences:
- Date format: `Mon DD,YYYY` (e.g. `Aug 18,2025`)
- "PPS PAYMENT - THANK YOU" with "CR" suffix = payment, exclude
- "FEE - CROSS-BORDER TXN IN HKD" = separate fee line, merge with preceding cross-border transaction
- "FOREIGN CURRENCY AMOUNT" + "EXCHANGE RATE" appear as separate description lines
- Reference numbers in a separate column — ignore

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_parser_ccba.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
cd ~/code/vivesca
git add src/vivesca/spending/parsers/ccba.py tests/test_spending_parser_ccba.py tests/fixtures/ccba_*.pdf
git commit -m "feat(spending): CCBA eye Credit Card PDF parser"
```

---

### Task 7: Parser registry and dispatcher

**Files:**
- Modify: `src/vivesca/spending/parsers/__init__.py`
- Create: `tests/test_spending_dispatch.py`

- [ ] **Step 1: Write dispatcher tests**

```python
# tests/test_spending_dispatch.py
"""Tests for parser dispatch."""

from pathlib import Path

import pytest

from vivesca.spending.parsers import get_parser


def test_get_mox_parser():
    parser = get_parser("mox")
    assert parser is not None
    assert callable(parser)


def test_get_hsbc_parser():
    parser = get_parser("hsbc")
    assert parser is not None


def test_get_ccba_parser():
    parser = get_parser("ccba")
    assert parser is not None


def test_get_unknown_parser():
    assert get_parser("unknown") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_dispatch.py -v`

- [ ] **Step 3: Implement parser registry**

```python
# src/vivesca/spending/parsers/__init__.py
"""Bank-specific statement parsers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from vivesca.spending.schema import StatementMeta, Transaction

Parser: TypeAlias = Callable[[Path], "tuple[StatementMeta, list[Transaction]]"]

_REGISTRY: dict[str, Parser] = {}


def _build_registry() -> dict[str, Parser]:
    from vivesca.spending.parsers.ccba import parse_ccba
    from vivesca.spending.parsers.hsbc import parse_hsbc
    from vivesca.spending.parsers.mox import parse_mox

    return {
        "mox": parse_mox,
        "hsbc": parse_hsbc,
        "ccba": parse_ccba,
    }


def get_parser(bank: str) -> Parser | None:
    """Get the parser function for a given bank."""
    global _REGISTRY
    if not _REGISTRY:
        _REGISTRY = _build_registry()
    return _REGISTRY.get(bank)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_dispatch.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
cd ~/code/vivesca
git add src/vivesca/spending/parsers/__init__.py tests/test_spending_dispatch.py
git commit -m "feat(spending): parser registry and dispatch"
```

---

### Task 8: Vault writer (markdown output, PDF archival, dedup)

**Files:**
- Create: `src/vivesca/spending/vault.py`
- Create: `tests/test_spending_vault.py`

- [ ] **Step 1: Write vault tests**

```python
# tests/test_spending_vault.py
"""Tests for vault writing, PDF archival, and deduplication."""

from pathlib import Path

from vivesca.spending.schema import StatementMeta, Transaction
from vivesca.spending.vault import (
    format_markdown,
    is_processed,
    mark_processed,
)


def _sample_meta() -> StatementMeta:
    return StatementMeta(
        bank="mox",
        card="Mox Credit",
        period_start="31 Dec 2024",
        period_end="30 Jan 2025",
        statement_date="2025-01-30",
        balance=-600.00,
        minimum_due=220.00,
        due_date="2025-02-24",
        credit_limit=108000.00,
    )


def _sample_txns() -> list[Transaction]:
    return [
        Transaction(
            date="2025-01-02",
            merchant="GOOGLE",
            category="Tech/Subscriptions",
            currency="HKD",
            foreign_amount=None,
            hkd=-16.00,
        ),
        Transaction(
            date="2025-01-02",
            merchant="SMOL AI",
            category="Tech/AI",
            currency="USD",
            foreign_amount=-20.00,
            hkd=-158.40,
        ),
        Transaction(
            date="2025-01-07",
            merchant="SMARTONE",
            category="Telecom",
            currency="HKD",
            foreign_amount=None,
            hkd=-168.00,
        ),
    ]


def test_format_markdown_has_frontmatter():
    md = format_markdown(_sample_meta(), _sample_txns())
    assert md.startswith("---\n")
    assert "bank: mox" in md
    assert "balance: -600.0" in md


def test_format_markdown_has_transactions():
    md = format_markdown(_sample_meta(), _sample_txns())
    assert "| 02 Jan | GOOGLE |" in md
    assert "| 02 Jan | SMOL AI |" in md


def test_format_markdown_has_summary():
    md = format_markdown(_sample_meta(), _sample_txns())
    assert "## Summary" in md
    assert "Tech/AI" in md
    assert "Telecom" in md


def test_dedup_new_file(tmp_path):
    ledger = tmp_path / ".processed"
    assert not is_processed("abc123", ledger)


def test_dedup_after_mark(tmp_path):
    ledger = tmp_path / ".processed"
    mark_processed("abc123", ledger)
    assert is_processed("abc123", ledger)
    assert not is_processed("def456", ledger)


def test_dedup_multiple(tmp_path):
    ledger = tmp_path / ".processed"
    mark_processed("abc123", ledger)
    mark_processed("def456", ledger)
    assert is_processed("abc123", ledger)
    assert is_processed("def456", ledger)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_vault.py -v`

- [ ] **Step 3: Implement vault writer**

```python
# src/vivesca/spending/vault.py
"""Write parsed statements to the vault as markdown."""

from __future__ import annotations

import hashlib
import shutil
from datetime import datetime
from pathlib import Path

from vivesca.spending.schema import StatementMeta, Transaction


def format_markdown(
    meta: StatementMeta, transactions: list[Transaction]
) -> str:
    """Generate vault markdown from parsed statement data."""
    lines: list[str] = []

    # Frontmatter
    lines.append("---")
    lines.append(f"bank: {meta.bank}")
    lines.append(f"card: {meta.card}")
    lines.append(f"period: {meta.period_start} - {meta.period_end}")
    lines.append(f"statement_date: {meta.statement_date}")
    lines.append(f"balance: {meta.balance}")
    lines.append(f"minimum_due: {meta.minimum_due}")
    lines.append(f"due_date: {meta.due_date}")
    lines.append(f"credit_limit: {meta.credit_limit}")
    lines.append("---")
    lines.append("")

    # Transactions
    lines.append("## Transactions")
    lines.append("")
    lines.append("| Date | Merchant | Category | Currency | Foreign | HKD |")
    lines.append("|------|----------|----------|----------|---------|-----|")

    for t in transactions:
        date_short = _format_date_short(t.date)
        foreign = f"{t.foreign_amount:.2f}" if t.foreign_amount else ""
        hkd = f"{t.hkd:,.2f}"
        lines.append(
            f"| {date_short} | {t.merchant} | {t.category} "
            f"| {t.currency} | {foreign} | {hkd} |"
        )

    lines.append("")

    # Summary by category
    cats: dict[str, dict[str, float | int]] = {}
    for t in transactions:
        if t.category not in cats:
            cats[t.category] = {"count": 0, "total": 0.0}
        cats[t.category]["count"] += 1
        cats[t.category]["total"] += t.hkd

    sorted_cats = sorted(cats.items(), key=lambda x: x[1]["total"])

    lines.append("## Summary")
    lines.append("")
    lines.append("| Category | Count | Total (HKD) |")
    lines.append("|----------|-------|-------------|")
    for cat, data in sorted_cats:
        lines.append(
            f"| {cat} | {int(data['count'])} | {data['total']:,.2f} |"
        )
    total = sum(t.hkd for t in transactions)
    lines.append(
        f"| **Total** | **{len(transactions)}** | **{total:,.2f}** |"
    )
    lines.append("")

    return "\n".join(lines)


def _format_date_short(iso_date: str) -> str:
    """'2025-01-02' → '02 Jan'"""
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return dt.strftime("%d %b")


def file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def is_processed(sha: str, ledger: Path) -> bool:
    """Check if a file hash has already been processed."""
    if not ledger.exists():
        return False
    return sha in ledger.read_text().splitlines()


def mark_processed(sha: str, ledger: Path) -> None:
    """Record a file hash as processed."""
    with open(ledger, "a") as f:
        f.write(sha + "\n")


def write_statement(
    meta: StatementMeta,
    transactions: list[Transaction],
    spending_dir: Path,
) -> Path:
    """Write parsed statement to vault and return the file path."""
    spending_dir.mkdir(parents=True, exist_ok=True)
    md_path = spending_dir / f"{meta.filename_stem}.md"
    md_path.write_text(format_markdown(meta, transactions))
    return md_path


def archive_pdf(
    pdf_path: Path, meta: StatementMeta, spending_dir: Path
) -> Path:
    """Move original PDF to vault archive."""
    archive_dir = spending_dir / "statements"
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / f"{meta.filename_stem}.pdf"
    shutil.move(str(pdf_path), str(dest))  # shutil handles cross-filesystem
    return dest
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_vault.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
cd ~/code/vivesca
git add src/vivesca/spending/vault.py tests/test_spending_vault.py
git commit -m "feat(spending): vault writer with markdown output and dedup"
```

---

### Task 9: Monitors (fraud, budget, subscription)

**Files:**
- Create: `src/vivesca/spending/monitors.py`
- Create: `tests/test_spending_monitors.py`

- [ ] **Step 1: Write monitor tests**

```python
# tests/test_spending_monitors.py
"""Tests for spending monitors."""

from vivesca.spending.monitors import (
    check_budget,
    check_duplicates,
    check_subscriptions,
    check_unknown_high,
)
from vivesca.spending.schema import Transaction


def _txn(merchant: str, hkd: float, category: str = "Dining") -> Transaction:
    return Transaction(
        date="2025-01-15",
        merchant=merchant,
        category=category,
        currency="HKD",
        foreign_amount=None,
        hkd=hkd,
    )


class TestUnknownHigh:
    def test_flags_unknown_over_500(self):
        txns = [_txn("WEIRD MERCHANT", -800.00, "Uncategorised")]
        alerts = check_unknown_high(txns)
        assert len(alerts) == 1
        assert "WEIRD MERCHANT" in alerts[0]

    def test_ignores_known_merchant(self):
        txns = [_txn("SMARTONE", -800.00, "Telecom")]
        alerts = check_unknown_high(txns)
        assert len(alerts) == 0

    def test_ignores_unknown_under_500(self):
        txns = [_txn("WEIRD MERCHANT", -100.00, "Uncategorised")]
        alerts = check_unknown_high(txns)
        assert len(alerts) == 0


class TestDuplicates:
    def test_flags_same_merchant_amount_date(self):
        txns = [
            _txn("GOOGLE", -78.00),
            _txn("GOOGLE", -78.00),
        ]
        alerts = check_duplicates(txns)
        assert len(alerts) == 1

    def test_ignores_different_amounts(self):
        txns = [
            _txn("GOOGLE", -78.00),
            _txn("GOOGLE", -16.00),
        ]
        alerts = check_duplicates(txns)
        assert len(alerts) == 0


class TestBudget:
    def test_under_budget(self):
        txns = [_txn("FOOD", -5000.00)]
        alerts = check_budget(txns, monthly_budget=15000.00)
        assert len(alerts) == 0

    def test_at_80_percent(self):
        txns = [_txn("FOOD", -12500.00)]
        alerts = check_budget(txns, monthly_budget=15000.00)
        assert len(alerts) == 1
        assert "83%" in alerts[0] or "80%" in alerts[0]

    def test_over_budget(self):
        txns = [_txn("FOOD", -16000.00)]
        alerts = check_budget(txns, monthly_budget=15000.00)
        assert any("100%" in a or "exceed" in a.lower() for a in alerts)


class TestSubscriptions:
    def test_missing_subscription(self):
        expected = [{"merchant": "SMARTONE", "amount": -168.00}]
        txns = []  # no transactions at all
        alerts = check_subscriptions(txns, expected)
        assert len(alerts) == 1
        assert "SMARTONE" in alerts[0]

    def test_subscription_present(self):
        expected = [{"merchant": "SMARTONE", "amount": -168.00}]
        txns = [_txn("SMARTONE", -168.00, "Telecom")]
        alerts = check_subscriptions(txns, expected)
        assert len(alerts) == 0

    def test_price_change(self):
        expected = [{"merchant": "SMARTONE", "amount": -168.00}]
        txns = [_txn("SMARTONE", -200.00, "Telecom")]
        alerts = check_subscriptions(txns, expected)
        assert len(alerts) == 1
        assert "price" in alerts[0].lower() or "change" in alerts[0].lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_monitors.py -v`

- [ ] **Step 3: Implement monitors**

```python
# src/vivesca/spending/monitors.py
"""Deterministic spending monitors — fraud, budget, subscriptions."""

from __future__ import annotations

from collections import Counter

from vivesca.spending.schema import Transaction


def check_unknown_high(
    transactions: list[Transaction], threshold: float = 500.0
) -> list[str]:
    """Flag uncategorised transactions above threshold."""
    alerts = []
    for t in transactions:
        if t.category == "Uncategorised" and abs(t.hkd) > threshold:
            alerts.append(
                f"Unknown merchant: {t.merchant} ({t.hkd:,.2f} HKD) "
                f"on {t.date}"
            )
    return alerts


def check_duplicates(transactions: list[Transaction]) -> list[str]:
    """Flag potential duplicate charges (same merchant, amount, date)."""
    keys = Counter(
        (t.date, t.merchant, t.hkd)
        for t in transactions
        if t.is_charge
    )
    alerts = []
    for (date, merchant, hkd), count in keys.items():
        if count > 1:
            alerts.append(
                f"Possible duplicate: {merchant} {hkd:,.2f} HKD "
                f"on {date} ({count}x)"
            )
    return alerts


def check_budget(
    transactions: list[Transaction],
    monthly_budget: float,
    category_budgets: dict[str, float] | None = None,
) -> list[str]:
    """Check total spend against budget thresholds."""
    total_spend = sum(abs(t.hkd) for t in transactions if t.is_charge)
    pct = (total_spend / monthly_budget * 100) if monthly_budget else 0
    alerts = []

    if pct >= 100:
        alerts.append(
            f"Budget exceeded: {total_spend:,.0f}/{monthly_budget:,.0f} HKD "
            f"({pct:.0f}%)"
        )
    elif pct >= 80:
        alerts.append(
            f"Budget warning: {total_spend:,.0f}/{monthly_budget:,.0f} HKD "
            f"({pct:.0f}%)"
        )

    # Per-category checks
    if category_budgets:
        cat_totals: dict[str, float] = {}
        for t in transactions:
            if t.is_charge:
                cat_totals[t.category] = (
                    cat_totals.get(t.category, 0) + abs(t.hkd)
                )
        for cat, budget in category_budgets.items():
            spent = cat_totals.get(cat, 0)
            if spent > budget:
                alerts.append(
                    f"{cat} over budget: {spent:,.0f}/{budget:,.0f} HKD"
                )

    return alerts


def check_subscriptions(
    transactions: list[Transaction],
    expected: list[dict],
) -> list[str]:
    """Check for missing or price-changed subscriptions.

    Each expected entry: {"merchant": "SMARTONE", "amount": -168.00}
    """
    alerts = []
    for sub in expected:
        merchant = sub["merchant"]
        expected_amount = sub["amount"]
        matches = [
            t for t in transactions
            if t.merchant.upper().startswith(merchant.upper())
            and t.is_charge
        ]
        if not matches:
            alerts.append(f"Missing subscription: {merchant} (expected {expected_amount:.2f} HKD)")
        else:
            actual = matches[0].hkd
            if abs(actual - expected_amount) / abs(expected_amount) > 0.05:
                alerts.append(
                    f"Subscription price change: {merchant} "
                    f"({expected_amount:.2f} → {actual:.2f} HKD)"
                )
    return alerts


def run_all_monitors(
    transactions: list[Transaction],
    monthly_budget: float = 15000.0,
    category_budgets: dict[str, float] | None = None,
    expected_subscriptions: list[dict] | None = None,
) -> list[str]:
    """Run all monitors and return combined alerts."""
    alerts: list[str] = []
    alerts.extend(check_unknown_high(transactions))
    alerts.extend(check_duplicates(transactions))
    alerts.extend(
        check_budget(transactions, monthly_budget, category_budgets)
    )
    if expected_subscriptions:
        alerts.extend(check_subscriptions(transactions, expected_subscriptions))
    return alerts
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_monitors.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
cd ~/code/vivesca
git add src/vivesca/spending/monitors.py tests/test_spending_monitors.py
git commit -m "feat(spending): fraud, budget, and duplicate monitors"
```

---

### Task 10: Pipeline (scan → parse → categorise → write → monitor)

**Files:**
- Modify: `src/vivesca/spending/__init__.py`

- [ ] **Step 1: Implement the pipeline**

```python
# src/vivesca/spending/__init__.py
"""Spending metabolism — credit card statement parsing and monitoring."""

from __future__ import annotations

from pathlib import Path

from vivesca.spending.categories import categorise, load_categories
from vivesca.spending.detect import detect_bank, filename_matches
from vivesca.spending.monitors import run_all_monitors
from vivesca.spending.parsers import get_parser
from vivesca.spending.vault import (
    archive_pdf,
    file_hash,
    format_markdown,
    is_processed,
    mark_processed,
    write_statement,
)

SPENDING_DIR = Path.home() / "notes" / "Spending"
CATEGORIES_FILE = SPENDING_DIR / "categories.yaml"
DEDUP_LEDGER = SPENDING_DIR / ".processed"


def process_statement(
    pdf_path: Path,
    spending_dir: Path = SPENDING_DIR,
    categories_file: Path = CATEGORIES_FILE,
    move_pdf: bool = True,
) -> dict:
    """Parse a single statement PDF end-to-end.

    Returns dict with: bank, md_path, transactions, alerts.
    Raises ValueError on balance validation failure.
    """
    from pypdf import PdfReader

    # Detect bank
    reader = PdfReader(pdf_path)
    page1 = reader.pages[0].extract_text() or ""
    bank = detect_bank(page1)
    if bank is None:
        return {"error": f"Unrecognised bank: {pdf_path.name}"}

    # Parse
    parser = get_parser(bank)
    if parser is None:
        return {"error": f"No parser for bank: {bank}"}

    meta, txns = parser(pdf_path)

    # Categorise
    cats = load_categories(categories_file)
    for t in txns:
        if not t.category:
            t.category = categorise(t.merchant, cats)

    # Write to vault
    md_path = write_statement(meta, txns, spending_dir)

    # Archive PDF
    pdf_dest = None
    if move_pdf:
        pdf_dest = archive_pdf(pdf_path, meta, spending_dir)

    # Run monitors
    alerts = run_all_monitors(txns)

    return {
        "bank": bank,
        "card": meta.card,
        "statement_date": meta.statement_date,
        "md_path": str(md_path),
        "pdf_archived": str(pdf_dest) if pdf_dest else None,
        "transaction_count": len(txns),
        "total_hkd": sum(t.hkd for t in txns),
        "alerts": alerts,
    }


def scan_and_process(
    scan_path: Path | None = None,
    spending_dir: Path = SPENDING_DIR,
    move_pdf: bool = True,
) -> list[dict]:
    """Scan iCloud for new statement PDFs and process each.

    Returns list of results (one per processed statement).
    """
    if scan_path is None:
        scan_path = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"

    if not scan_path.exists():
        return [{"error": f"Scan path not found: {scan_path}"}]

    ledger = spending_dir / ".processed"
    results = []

    for pdf in scan_path.iterdir():
        if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
            continue
        if not filename_matches(pdf.name):
            continue

        sha = file_hash(pdf)
        if is_processed(sha, ledger):
            continue

        try:
            result = process_statement(
                pdf, spending_dir=spending_dir, move_pdf=move_pdf
            )
            if "error" not in result:
                mark_processed(sha, ledger)
            results.append(result)
        except ValueError as e:
            results.append({
                "error": str(e),
                "file": pdf.name,
                "quarantined": True,
            })

    return results
```

- [ ] **Step 2: Run all tests to verify nothing is broken**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_*.py -v`
Expected: all PASS

- [ ] **Step 3: Commit**

```bash
cd ~/code/vivesca
git add src/vivesca/spending/__init__.py
git commit -m "feat(spending): end-to-end pipeline — scan, parse, categorise, write, monitor"
```

---

### Task 11: Monthly summary generator

**Files:**
- Modify: `src/vivesca/spending/vault.py`
- Modify: `tests/test_spending_vault.py`

- [ ] **Step 1: Write monthly summary tests**

Add to `tests/test_spending_vault.py`:

```python
from vivesca.spending.vault import write_monthly_summary


def test_monthly_summary_single_card(tmp_path):
    """Generate summary from one statement file."""
    # Write a statement file first
    md = tmp_path / "2025-01-mox.md"
    md.write_text(
        "---\nbank: mox\ncard: Mox Credit\nstatement_date: 2025-01-30\n"
        "balance: -600.0\n---\n\n## Transactions\n\n"
        "| Date | Merchant | Category | Currency | Foreign | HKD |\n"
        "|------|----------|----------|----------|---------|-----|\n"
        "| 02 Jan | GOOGLE | Tech/Subscriptions | HKD | | -16.00 |\n"
        "| 07 Jan | SMARTONE | Telecom | HKD | | -168.00 |\n\n"
        "## Summary\n\n"
        "| Category | Count | Total (HKD) |\n"
        "|----------|-------|-------------|\n"
        "| Tech/Subscriptions | 1 | -16.00 |\n"
        "| Telecom | 1 | -168.00 |\n"
        "| **Total** | **2** | **-184.00** |\n"
    )
    summary_path = write_monthly_summary("2025-01", tmp_path)
    assert summary_path.exists()
    content = summary_path.read_text()
    assert "month: 2025-01" in content
    assert "mox" in content.lower()


def test_monthly_summary_multi_card(tmp_path):
    """Aggregates across multiple cards."""
    for bank in ("mox", "hsbc"):
        md = tmp_path / f"2025-02-{bank}.md"
        md.write_text(
            f"---\nbank: {bank}\ncard: {bank.upper()} Card\n"
            f"statement_date: 2025-02-28\nbalance: -500.0\n---\n\n"
            "## Summary\n\n"
            "| Category | Count | Total (HKD) |\n"
            "|----------|-------|-------------|\n"
            "| Dining | 2 | -300.00 |\n"
            "| **Total** | **2** | **-300.00** |\n"
        )
    summary_path = write_monthly_summary("2025-02", tmp_path)
    content = summary_path.read_text()
    assert "cards:" in content
    assert "mox" in content
    assert "hsbc" in content
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_vault.py::test_monthly_summary_single_card -v`

- [ ] **Step 3: Implement monthly summary generator**

Add to `src/vivesca/spending/vault.py`:

```python
def write_monthly_summary(month: str, spending_dir: Path) -> Path:
    """Generate/update YYYY-MM-summary.md aggregating all cards for the month.

    Args:
        month: YYYY-MM string
        spending_dir: vault spending directory
    """
    # Find all per-statement files for this month
    statements = sorted(spending_dir.glob(f"{month}-*.md"))
    statements = [s for s in statements if not s.name.endswith("-summary.md")]

    cards = []
    all_categories: dict[str, dict[str, float]] = {}  # cat -> {card: total}
    card_totals: dict[str, dict] = {}

    for stmt_path in statements:
        text = stmt_path.read_text()
        # Extract bank from frontmatter
        bank = ""
        card_name = ""
        for line in text.splitlines():
            if line.startswith("bank: "):
                bank = line.split(": ", 1)[1]
            elif line.startswith("card: "):
                card_name = line.split(": ", 1)[1]
        if not bank:
            continue
        cards.append(bank)

        # Parse category totals from summary table
        txn_count = 0
        total = 0.0
        import re
        for m in re.finditer(
            r"\| (.+?) \| (\d+) \| (-?[\d,]+\.\d{2}) \|", text
        ):
            cat = m.group(1).strip()
            if cat.startswith("**"):
                txn_count = int(m.group(2).strip("*"))
                total = float(m.group(3).strip("*").replace(",", ""))
                continue
            cat_total = float(m.group(3).replace(",", ""))
            if cat not in all_categories:
                all_categories[cat] = {}
            all_categories[cat][bank] = cat_total

        card_totals[bank] = {
            "card": card_name,
            "count": txn_count,
            "total": total,
        }

    # Build summary markdown
    grand_total = sum(ct["total"] for ct in card_totals.values())
    lines = [
        "---",
        f"month: {month}",
        f"cards: [{', '.join(cards)}]",
        f"total_spend: {grand_total:.2f}",
        "---",
        "",
        "## By Category",
        "",
    ]

    # Header with card columns
    header = "| Category |"
    sep = "|----------|"
    for bank in cards:
        header += f" {bank.upper()} |"
        sep += "------|"
    header += " Total |"
    sep += "-------|"
    lines.extend([header, sep])

    for cat in sorted(all_categories.keys()):
        row = f"| {cat} |"
        cat_total = 0.0
        for bank in cards:
            val = all_categories[cat].get(bank, 0)
            cat_total += val
            row += f" {val:,.2f} |" if val else " 0 |"
        row += f" {cat_total:,.2f} |"
        lines.append(row)

    lines.extend([
        "",
        "## By Card",
        "",
        "| Card | Transactions | Total (HKD) |",
        "|------|-------------|-------------|",
    ])
    for bank in cards:
        ct = card_totals[bank]
        lines.append(
            f"| {ct['card']} | {ct['count']} | {ct['total']:,.2f} |"
        )
    lines.append("")

    summary_path = spending_dir / f"{month}-summary.md"
    summary_path.write_text("\n".join(lines))
    return summary_path
```

- [ ] **Step 4: Update `process_statement` in `__init__.py` to call `write_monthly_summary`**

After the `write_statement` call, add:

```python
from vivesca.spending.vault import write_monthly_summary
month = meta.statement_date[:7]  # YYYY-MM
write_monthly_summary(month, spending_dir)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_vault.py -v`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
cd ~/code/vivesca
git add src/vivesca/spending/vault.py src/vivesca/spending/__init__.py tests/test_spending_vault.py
git commit -m "feat(spending): monthly summary generator with cross-card aggregation"
```

---

### Task 12: MCP tool

**Files:**
- Create: `src/vivesca/tools/spending_sense.py`
- Create: `tests/test_spending_tool.py`

- [ ] **Step 1: Write tool tests**

```python
# tests/test_spending_tool.py
"""Tests for the spending MCP tool."""

from vivesca.tools.spending_sense import SpendingResult


def test_spending_result_is_tool_output():
    from vivesca.schemas import ToolOutput
    assert issubclass(SpendingResult, ToolOutput)


def test_spending_result_fields():
    r = SpendingResult(
        summary="Processed 1 statement",
        statements_processed=1,
        total_alerts=0,
        details=[],
    )
    assert r.summary == "Processed 1 statement"
    assert r.statements_processed == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_tool.py -v`

- [ ] **Step 3: Implement MCP tool**

```python
# src/vivesca/tools/spending_sense.py
"""spending — credit card statement metabolism.

Tools:
  vigilis_check_spending — parse new statements, summarise spending, flag issues
"""

from __future__ import annotations

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from vivesca.schemas import ToolOutput


class SpendingResult(ToolOutput):
    """Output from spending check."""

    summary: str
    statements_processed: int = 0
    total_alerts: int = 0
    details: list[dict] = []


@tool(
    name="vigilis_check_spending",
    description="Parse new credit card statements, summarise spending, flag issues.",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def vigilis_check_spending(days: int = 30) -> SpendingResult:
    """Scan iCloud for unprocessed statement PDFs, parse, write to vault, monitor.

    Args:
        days: budget monitoring window (how many days of spending to evaluate).
    """
    from vivesca.spending import scan_and_process

    results = scan_and_process()

    if not results:
        return SpendingResult(summary="No new statements found.")

    errors = [r for r in results if "error" in r]
    successes = [r for r in results if "error" not in r]

    all_alerts: list[str] = []
    for r in successes:
        all_alerts.extend(r.get("alerts", []))

    parts: list[str] = []
    for r in successes:
        total = r.get("total_hkd", 0)
        parts.append(
            f"{r['card']} ({r['statement_date']}): "
            f"{r['transaction_count']} transactions, "
            f"HKD {total:,.2f}"
        )
    for r in errors:
        parts.append(f"Error: {r['error']}")

    if all_alerts:
        parts.append("")
        parts.append("Alerts:")
        parts.extend(f"  - {a}" for a in all_alerts)

    return SpendingResult(
        summary="\n".join(parts),
        statements_processed=len(successes),
        total_alerts=len(all_alerts),
        details=results,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/code/vivesca && python -m pytest tests/test_spending_tool.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
cd ~/code/vivesca
git add src/vivesca/tools/spending_sense.py tests/test_spending_tool.py
git commit -m "feat(spending): MCP tool vigilis_check_spending"
```

---

### Task 13: Metabolism substrate

**Files:**
- Create: `src/vivesca/metabolism/substrates/spending.py`
- Modify: `src/vivesca/metabolism/substrates/__init__.py`

- [ ] **Step 1: Implement spending substrate**

```python
# src/vivesca/metabolism/substrates/spending.py
"""Spending substrate — periodic trend analysis over parsed statement data.

Primarily a reporter: reads vault markdown files and surfaces insights about
spending trends, category drift, and subscription cost creep.
"""

from __future__ import annotations

import re
from pathlib import Path

SPENDING_DIR = Path.home() / "notes" / "Spending"


class SpendingSubstrate:
    """Metabolism substrate for spending analysis."""

    name: str = "spending"

    def __init__(self, spending_dir: Path = SPENDING_DIR) -> None:
        self.spending_dir = spending_dir

    def sense(self, days: int = 90) -> list[dict]:
        """Read parsed statement files from vault."""
        results = []
        for md in sorted(self.spending_dir.glob("????-??-*.md")):
            if md.name.endswith("-summary.md"):
                continue
            text = md.read_text()
            # Extract frontmatter
            fm_match = re.search(r"^---\n(.+?)\n---", text, re.DOTALL)
            if not fm_match:
                continue
            meta = {}
            for line in fm_match.group(1).splitlines():
                if ": " in line:
                    k, v = line.split(": ", 1)
                    meta[k.strip()] = v.strip()
            # Extract category totals from summary table
            cats = {}
            for m in re.finditer(
                r"\| (.+?) \| (\d+) \| (-?[\d,]+\.\d{2}) \|", text
            ):
                cat, count, total = m.group(1).strip(), m.group(2), m.group(3)
                if cat.startswith("**"):
                    continue
                cats[cat] = float(total.replace(",", ""))
            results.append({"file": md.name, "meta": meta, "categories": cats})
        return results

    def candidates(self, sensed: list[dict]) -> list[dict]:
        """Identify months with notable spending patterns."""
        if len(sensed) < 2:
            return []
        # Compare most recent month against prior months
        # Flag categories that increased >30% month-over-month
        recent = sensed[-1]
        prior = sensed[-2]
        candidates = []
        for cat, amount in recent["categories"].items():
            prior_amount = prior["categories"].get(cat, 0)
            if prior_amount != 0 and amount < 0:
                change_pct = ((amount - prior_amount) / abs(prior_amount)) * 100
                if change_pct < -30:  # spending increased >30% (more negative)
                    candidates.append({
                        "category": cat,
                        "current": amount,
                        "prior": prior_amount,
                        "change_pct": change_pct,
                    })
        return candidates

    def act(self, candidate: dict) -> str:
        """Propose review action (no auto-mutation)."""
        return (
            f"Review {candidate['category']}: "
            f"spending changed {candidate['change_pct']:+.0f}% "
            f"({candidate['prior']:,.0f} → {candidate['current']:,.0f} HKD)"
        )

    def report(self, sensed: list[dict], acted: list[str]) -> str:
        """Format human-readable spending metabolism report."""
        lines = [f"Spending substrate: {len(sensed)} statement(s) in vault"]
        if acted:
            lines.append("")
            lines.append("Proposals:")
            for a in acted:
                lines.append(f"  - {a}")
        return "\n".join(lines)
```

- [ ] **Step 2: Register substrate**

In `src/vivesca/metabolism/substrates/__init__.py`, add to `_build_registry()`:

```python
from vivesca.metabolism.substrates.spending import SpendingSubstrate
```

And add to the return dict:

```python
"spending": SpendingSubstrate,
```

- [ ] **Step 3: Run all tests**

Run: `cd ~/code/vivesca && python -m pytest tests/ -v`
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
cd ~/code/vivesca
git add src/vivesca/metabolism/substrates/spending.py src/vivesca/metabolism/substrates/__init__.py
git commit -m "feat(spending): metabolism substrate for trend analysis"
```

---

### Task 14: Seed vault config files

**Files:**
- Create: `~/notes/Spending/config.yaml`
- Create: `~/notes/Spending/categories.yaml`

- [ ] **Step 1: Create spending directory and config**

```bash
mkdir -p ~/notes/Spending/statements
```

- [ ] **Step 2: Write categories.yaml**

Write `~/notes/Spending/categories.yaml` with the full category map from the spec (all merchants seen in the Mox, HSBC, and CCBA test statements).

- [ ] **Step 3: Write config.yaml**

Write `~/notes/Spending/config.yaml` with budget targets and expected subscriptions. Ask Terry for the monthly budget figure if not known — default to 15000 HKD.

- [ ] **Step 4: Add .gitignore for PDFs**

```bash
echo "statements/*.pdf" > ~/notes/Spending/.gitignore
```

- [ ] **Step 5: Commit vault files**

```bash
cd ~/notes && git add Spending/config.yaml Spending/categories.yaml Spending/.gitignore
git commit -m "feat: seed spending config and categories"
```

---

### Task 15: Integration test — full pipeline on real PDF

- [ ] **Step 1: Run the MCP tool manually**

```bash
cd ~/code/vivesca && python3 -c "
from vivesca.spending import process_statement
from pathlib import Path

result = process_statement(
    Path.home() / 'Library/Mobile Documents/com~apple~CloudDocs/HO-MING-TERRY-LI_Jan2025_Mox_Credit_Statement.pdf',
    move_pdf=False,  # don't move during test
)
print(result)
"
```

Verify: markdown file created in `~/notes/Spending/2025-01-mox.md`, transactions parsed correctly, alerts list present.

- [ ] **Step 2: Inspect the generated markdown**

Read `~/notes/Spending/2025-01-mox.md` and verify it matches the expected format from the spec.

- [ ] **Step 3: Run the full scan**

```bash
cd ~/code/vivesca && python3 -c "
from vivesca.spending import scan_and_process
results = scan_and_process(move_pdf=False)
for r in results:
    print(r)
"
```

Verify: both Mox PDFs detected, parsed, and written. HSBC and CCBA PDFs detected and parsed (if parsers are ready). Dedup ledger created.

- [ ] **Step 4: Commit any fixes**

If anything needed adjustment, commit the fixes:

```bash
cd ~/code/vivesca
git add -A
git commit -m "fix(spending): integration test fixes"
```
