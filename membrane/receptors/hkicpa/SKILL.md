---
name: hkicpa
description: Reference for HKICPA portal access and CPD compliance. Use when working with CPD submissions or HKICPA portal tasks.
user_invocable: true
disable-model-invocation: true
---

# HKICPA

Reference for HKICPA portal access and CPD compliance. Not user-invocable — load as context when working with CPD or HKICPA tasks.

## Two Separate Portals

| Portal | URL | Purpose |
|--------|-----|---------|
| **LMS** | https://lms.hkicpa.org.hk | Enrol and watch CPD courses |
| **MyCPA** | https://mas.hkicpa.org.hk/mycpa | Self-declare CPD hours, view record, renewal |

These are **completely separate systems** with different credentials.

## Credentials

| Portal | Username | Keychain |
|--------|----------|---------|
| LMS | `terryli` | `security find-generic-password -s hkicpa -a terry -w` |
| MyCPA | `terryli` | `security find-generic-password -s hkicpa-mycpa -a terryli -w` |

## LMS Login (automated)

Use the `hkicpa` script:
```bash
hkicpa              # opens enrolled courses page
hkicpa <url>        # opens specific course URL
```
Script: `~/bin/hkicpa` — uses `--headed` agent-browser, reads keychain `hkicpa/terry`.

## MyCPA Login (browser)

MyCPA has a CAPTCHA that changes quickly. Fill + submit must happen in a single chained call:

```python
import subprocess, time

def ab(args):
    return subprocess.run(['agent-browser'] + args, capture_output=True, text=True).stdout.strip()

ab(['close'])
ab(['--headed', 'open', 'https://mas.hkicpa.org.hk/mycpa'])
time.sleep(2)
ab(['fill', '@e4', 'terryli'])      # Login ID field
pw = subprocess.run(['security','find-generic-password','-s','hkicpa-mycpa','-a','terryli','-w'],
                    capture_output=True, text=True).stdout.strip()
ab(['fill', '@e5', pw])             # Password field
# Screenshot to read captcha, then:
ab(['fill', '#captcha', 'XXXX'])    # CSS selector is reliable; fill + click in same call
ab(['click', '@login_button'])
```

**Key gotcha:** captcha expires between Bash calls. Chain fill+click in one Python call or use `&&` in bash.

## MyCPA CPD Self-Declaration

Navigate to: `https://mas.hkicpa.org.hk/mycpa/development/cpd-activity/index`

Click "Add CPD hours". Form fields (by `name` attribute — more stable than refs):

| Field | `name` | Notes |
|-------|--------|-------|
| Title | `epName` | Free text |
| Organiser | `epOrganiser` | Free text |
| Start date | `epDateFr` | Format: `DD-MM-YYYY` (dashes) |
| End date | `epDateTo` | Format: `DD-MM-YYYY` (dashes) |
| Type | `select[2]` | value `'3'`=Verifiable, `'4'`=Non-verifiable |
| Status | `select[3]` | value `'0'`=Enrolled, `'1'`=Attended |
| Remarks | `epRemarks` | Optional |
| Hours | `epHours` | Integer |
| Minutes | `epMinutes` | Integer |

**Use Python subprocess for JS** — heredoc eval fails with exit code 1 on complex strings.

**"Save & add more"** keeps the dialog open for batch entry.

**Bulk consolidation:** HKICPA allows "your own method" — batch by year+type rather than per-course. Set date range = first to last course, hours = total sum.

## CPD Requirements (Regular Member, Dec 2023–Nov 2026)

| Requirement | Target | Status (as of 2026-03-02) |
|---|---|---|
| Total CPD | 120h / 3 years | **110.54h logged** (9.46h to go) |
| Verifiable | 60h / 3 years | **91.67h** ✓ |
| Ethics (verifiable) | 2h / year (from Dec 2025) | Ethics Conference 2025 enrolled ✓ |
| Structured | 30h / 3 years | Active Dec 2026 |

Full tracker: `~/notes/HKICPA CPD Tracker.md`

## CPD Evidence (keep on file, not uploaded)

- CNCBI training: `CISA CPE Evidence/CITIC_Training_Records.pdf`
- FinTech Week 2024: General Pass confirmation email (search `from:finoverse.com`)
- LMS courses: attendance certificate auto-generated after completion
