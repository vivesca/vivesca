# Spending Metabolism — Design Spec

> vivesca metabolises credit card statements: parse PDFs, write structured markdown to the vault, monitor for fraud and budget drift, surface alerts.

## Contract

**Terry's job:** drop statement PDFs into iCloud (download from bank app).

**Vivesca's job:** everything else — parse, categorise, store, monitor, alert.

## Data Flow

```
iCloud (new PDF detected by filename pattern)
    ↓
detect bank (Mox / HSBC / CCBA) → route to parser
    ↓
extract transactions → normalise to common schema
    ↓
validate: parsed transaction total == statement-printed total
    ↓  (mismatch → quarantine PDF, alert, stop)
categorise merchants (YAML map, prefix match)
    ↓
write per-statement markdown:  ~/code/epigenome/chromatin/Spending/YYYY-MM-bank.md
    ↓
write/update monthly summary:  ~/code/epigenome/chromatin/Spending/YYYY-MM-summary.md
    ↓
move PDF to vault:             ~/code/epigenome/chromatin/Spending/statements/YYYY-MM-bank.pdf
    ↓
run monitors (fraud, budget, subscription drift)
    ↓
return summary + alerts (conversation or Telegram)
```

## Parsers

One regex-based Python module per bank. Deterministic — same PDF always produces same output.

### Balance Validation

Every parser must extract the statement's printed total/balance and assert it matches the sum of parsed transactions. If validation fails, the statement is quarantined (not written to vault, PDF not moved) and an alert is raised. This is the critical integrity check — without it, a bank format change produces silently wrong data instead of a loud failure.

For statements where balance includes previous balance (e.g. HSBC), the parser validates against the "new transactions total" or "total new activity" figure rather than the cumulative balance.

### Mox (`mox.py`)

- **Source:** `HO-MING-TERRY-LI_*_Mox_Credit_Statement.pdf`
- **Format:** Clean tabular. Activity date, settlement date, description, foreign currency amount, HKD amount.
- **Quirks:** Multi-line descriptions with FX rates and cross-border fees. Internal transfers ("Account / Move between own Mox accounts") should be excluded from spending totals but preserved in the transaction table with a `Transfer` category.
- **Status:** Proof of concept built and validated against Jan 2025 and Aug 2025 statements. Totals balance.

### HSBC Visa Signature (`hsbc.py`)

- **Source:** `eStatementFile_*.pdf` (generic names from HSBC e-banking)
- **Format:** Fixed-width text. Post date, trans date, description, amount. Multi-line descriptions include merchant location, payment device, exchange rates.
- **Quirks:** "PREVIOUS BALANCE" and "PPS PAYMENT" lines are not spending transactions — filter out. "DCC FEE-NON-HK MERCHANT" is a fee line tied to the preceding transaction — merge as a surcharge. "OCTOPUS CARDS LTD / AUTO ADD-VALUE" is a transit top-up, not a purchase. Apple Pay transactions show "GOOGLE PAY-DEVICE:0376" or "APPLE PAY-MOBILE:5893" as suffix — strip for clean merchant name.
- **Detection:** Page 1 contains "HSBC" logo text and "STATEMENT OF HSBC VISA SIGNATURE CARD ACCOUNT".

### CCBA eye Credit Card (`ccba.py`)

- **Source:** `ECardPersonalStatement_*.pdf` or `eStatementFile_*.pdf`
- **Format:** Table with Trans Date, Post Date, New Activity, Reference No., Amount(HKD). Cross-border fees appear as separate "FEE - CROSS-BORDER TXN IN HKD" lines.
- **Quirks:** "PPS PAYMENT - THANK YOU" is a payment, not a charge (positive/CR amount). Foreign currency info appears as separate lines ("FOREIGN CURRENCY AMOUNT" + "EXCHANGE RATE"). Merge these with the parent transaction.
- **Detection:** Page 1 contains "中国建设银行(亚洲)" / "China Construction Bank".

### Bank Detection

Two-stage detection. First, filename pattern pre-filter narrows candidates:
- `HO-MING-TERRY-LI_*_Mox_Credit_Statement.pdf` → likely Mox
- `eStatementFile_*.pdf` → likely HSBC (ambiguous — could be CCBA)
- `ECardPersonalStatement_*.pdf` → likely CCBA

Then page 1 text confirms:
- `Mox Credit statement` → Mox parser
- `HSBC` + `VISA SIGNATURE` → HSBC parser
- `中国建设银行` or `China Construction Bank` → CCBA parser
- No match → skip with warning, log the unrecognised file path

### Adding New Banks

If SCB Smart or BOC statements appear later: write a new parser module, add detection string, register in dispatcher. The common schema and downstream pipeline are bank-agnostic.

## Common Transaction Schema

Each parser outputs a list of transactions in this shape:

```python
{
    "date": "2025-01-02",       # activity date, ISO format
    "merchant": "SMOL AI COMPANY",
    "category": "Tech/AI",
    "currency": "USD",          # original currency (HKD if local)
    "foreign_amount": -20.00,   # None if HKD
    "hkd": -158.40,             # always present
}
```

Negative = charge. Positive = payment/refund/credit.

## Vault Structure

```
~/code/epigenome/chromatin/Spending/
├── config.yaml                  # budget targets, known subscriptions
├── categories.yaml              # merchant → category map
├── 2025-01-mox.md              # per-statement parsed output
├── 2025-02-hsbc.md
├── 2025-02-ccba.md
├── 2025-02-summary.md          # monthly cross-card aggregate
├── statements/                  # archived original PDFs
│   ├── 2025-01-mox.pdf
│   ├── 2025-02-hsbc.pdf
│   └── 2025-02-ccba.pdf
```

### Per-Statement File (`YYYY-MM-bank.md`)

```markdown
---
bank: mox
card: Mox Credit
period: 31 Dec 2024 - 30 Jan 2025
statement_date: 2025-01-30
balance: -6004.03
minimum_due: 220.00
due_date: 2025-02-24
credit_limit: 108000.00
---

## Transactions

| Date | Merchant | Category | Currency | Foreign | HKD |
|------|----------|----------|----------|---------|-----|
| 02 Jan | GOOGLE | Tech/Subscriptions | HKD | | -16.00 |
| 02 Jan | SMOL AI COMPANY | Tech/AI | USD | -20.00 | -158.40 |

## Summary

| Category | Count | Total (HKD) |
|----------|-------|-------------|
| Tech/AI | 5 | -2,581.23 |
| **Total** | **20** | **-6,004.03** |
```

### Monthly Summary (`YYYY-MM-summary.md`)

Aggregates all cards for the month. Generated/updated whenever a new statement is parsed for that month.

```markdown
---
month: 2025-02
cards: [mox, hsbc, ccba]
total_spend: -12450.30
budget: -15000.00
budget_remaining: -2549.70
---

## By Category

| Category | Mox | HSBC | CCBA | Total |
|----------|-----|------|------|-------|
| Dining | -200 | -1,500 | -300 | -2,000 |
| Tech/AI | -600 | 0 | 0 | -600 |

## By Card

| Card | Transactions | Total (HKD) |
|------|-------------|-------------|
| Mox Credit | 20 | -4,200.00 |
| HSBC Visa Signature | 15 | -5,800.00 |
| CCBA eye Credit | 8 | -2,450.30 |

## Alerts

- New merchant: LATENT.SPACE/SWYX (-640.27 HKD) — categorise?
- Budget: 83% spent with 10 days remaining
```

### Config (`config.yaml`)

```yaml
budget:
  monthly: 15000          # HKD, total across all cards
  categories:
    Dining: 3000
    Tech/AI: 2000

subscriptions:
  expected:
    - merchant: SMARTONE
      amount: -168.00
      frequency: monthly
    - merchant: Bowtie Life Insurance
      amount: -374.41
      frequency: monthly
    - merchant: GOOGLE
      amount: -78.00
      frequency: monthly

icloud_scan_path: ~/Library/Mobile Documents/com~apple~CloudDocs/
scan_patterns:            # filename pre-filter before page-1 detection
  - "HO-MING-TERRY-LI_*_Mox_Credit_Statement.pdf"
  - "eStatementFile_*.pdf"
  - "ECardPersonalStatement_*.pdf"
```

### Categories (`categories.yaml`)

```yaml
# Prefix match, case-insensitive. First match wins.
GOOGLE: Tech/Subscriptions
SMOL AI COMPANY: Tech/AI
PAYPAL *GOOGLEHKPL: Tech/Subscriptions
THE NEW YORK TIMES: Media/News
BOWTIE LIFE INSURANCE: Insurance
SMARTONE: Telecom
RAILWAY: Tech/Dev Tools
DROPBOX: Tech/Cloud Storage
PAYPAL *GIVEWELL: Charity/Donation
SP HEIGHTS: Education
WWW.PERPLEXITY.AI: Tech/AI
FOUNDMYFITNESS: Health/Wellness
GITHUB: Tech/Dev Tools
OBSIDIAN.MD: Tech/Productivity
INTERCONNECTS.AI: Tech/AI
BREVILABS LLC: Tech/AI
OPENROUTER: Tech/AI
RUNWAY: Tech/AI
PROTON AG: Tech/Privacy
UBER: Transport
MCDONALD: Dining
CAFE DE CORAL: Dining
PICI QUARRY BAY: Dining
OCTOPUS CARDS: Transport/Octopus
APPLE STORE: Tech/Hardware
APPLE.COM: Tech/Subscriptions
ITUNES.COM: Tech/Subscriptions
```

When the parser encounters an unknown merchant, it categorises as `Uncategorised` and includes it in the alert output. Terry can then add the mapping to `categories.yaml` — or vivesca can propose a category and update the file.

## Monitors

All deterministic Python. No LLM. Run after every parse.

### Fraud Flags

- **Unknown merchant + high amount:** merchant not in `categories.yaml` AND |amount| > HK$500.
- **Duplicate charge:** same merchant, same amount, same date, different transaction (not a known recurring like Obsidian which legitimately charges twice).

_Deferred:_ "Unexpected geography" monitor (cross-border transactions from unseen countries) requires a `country` field in the schema and currency-to-country mapping which is many-to-one. Add once there are 6+ months of data and the value is proven.

### Budget Check

- Compare month-to-date spend (all cards) against `config.yaml` monthly budget.
- Alert at 80% and 100% thresholds.
- Per-category alerts if a category limit is defined and exceeded.

### Subscription Drift

- Compare this month's charges against `config.yaml` expected subscriptions.
- Flag: missing expected subscription, price change > 5%.
- **Recurrence detection:** a merchant is "recurring" if it appears in 2+ consecutive months with amount variance <10%. The monitor reads prior months' parsed markdown files from `~/code/epigenome/chromatin/Spending/` to determine recurrence. New recurring charges not in the expected list are flagged for review.
- _Initial implementation:_ compare against `config.yaml` only. Automatic recurrence detection ships once 3+ months of data exist.

## Deduplication

Before processing a PDF, compute SHA-256 hash of the file. Check against `~/code/epigenome/chromatin/Spending/.processed` (one hash per line). If already processed, skip. After successful processing, append hash.

This handles:
- Re-downloading the same PDF
- LaunchAgent re-scanning iCloud
- Multiple copies of the same file

## Vivesca Integration

### Tool: `vigilis_check_spending`

Lives in its own tool file (`tools/spending_sense.py`), not inside `vigilis.py`. The `vigilis_` prefix on the tool name indicates domain; the file stays separate to avoid bloating `vigilis.py` (already 360+ lines). `FileSystemProvider` discovers it automatically.

```python
@tool(name="vigilis_check_spending", description="Parse new statements, summarise spending, flag issues.")
def vigilis_check_spending(days: int = 30) -> SpendingResult:
    """
    1. Scan iCloud for unprocessed statement PDFs (filename pre-filter + page-1 detection)
    2. Parse each, validate totals, write to vault, archive PDF
    3. Run monitors
    4. Return summary + alerts
    """
```

Called on-demand in conversation, or by LaunchAgent.

### Metabolism Substrate: `spending.py`

For deeper periodic analysis during `vivesca metabolise`. This substrate is primarily a **reporter** — it reads parsed data and surfaces insights rather than mutating state. The `act()` method proposes actions ("review category X, spending up 40%") but does not auto-execute them.

- Month-over-month spending trends
- Category drift over 3-6 months
- FX cost analysis (how much spent on cross-border fees)
- Subscription cost creep

### LaunchAgent

Weekly scan (Sunday morning). Invocation: a standalone Python script that imports directly from `vivesca.spending` — no MCP server dependency. The script parses new statements, runs monitors, and calls `deltos` for alerts via subprocess. This matches the existing pattern (overnight pipeline calls subprocess, not MCP).

Alerts via Telegram if:
- New statement processed (summary)
- Fraud flag triggered
- Budget threshold breached

## Code Location

```
~/code/vivesca/src/vivesca/
├── tools/spending_sense.py           # vigilis_check_spending tool
├── metabolism/substrates/spending.py # spending substrate
├── spending/                         # domain package (see ADR below)
│   ├── __init__.py
│   ├── parser.py                     # dispatcher + common schema
│   ├── parsers/
│   │   ├── mox.py
│   │   ├── hsbc.py
│   │   └── ccba.py
│   ├── monitors.py                   # fraud, budget, subscription checks
│   └── vault.py                      # write markdown, move PDF, dedup
```

**ADR: domain packages.** `spending/` is the first domain-specific package at the top level of vivesca's source tree. This is deliberate — the parsing, monitoring, and vault logic is too substantial for a single tool file. If a second domain package appears (e.g. fitness tracking), refactor into a `domains/` directory.

## Vault File Naming

The `YYYY-MM` in filenames is derived from `statement_date`, not the transaction date range. A statement dated 30 Jan 2025 covering "31 Dec 2024 - 30 Jan 2025" is filed as `2025-01-mox.md`. If two statements from the same bank share a calendar month (unlikely for monthly billing), append a suffix: `2025-01-mox-2.md`.

## Privacy

Parsed markdown contains merchant-level spending data (no card numbers, no addresses). Original PDFs contain full PII (name, address, partial card number). Both live in `~/code/epigenome/chromatin/Spending/`.

- If the vault is git-tracked: `statements/*.pdf` must be in `.gitignore`.
- If synced via iCloud: acceptable for a personal system — same security posture as the bank app itself.
- The parsed markdown is lower-risk but still sensitive. No additional measures needed for a single-user vault.

## Out of Scope

- Bank API integration (no HK bank offers useful API access for statements)
- Historical backfill of old statements from Dropbox archive (can be done later if wanted)
- Real-time transaction alerts (would require bank app notifications, not statement parsing)
- Investment/savings account tracking (different concern, different data source)
- Unexpected geography fraud monitor (deferred — requires country extraction, see Monitors section)
