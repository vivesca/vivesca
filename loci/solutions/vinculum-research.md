---
title: "vinculum: Inactive Contact Surfacing Tool Research"
date: 2026-03-04
tags:
  - vinculum
  - wacli
  - imessage
  - sqlite
  - contact-management
  - uv-run-script
category: research
module: contact_management
component: cli_tool
severity: medium
---

# vinculum Research Summary

Research for building `vinculum` — a Python uv run --script tool at `~/bin/` that queries wacli (WhatsApp CLI) and iMessage SQLite to surface contacts who haven't been messaged recently.

---

## 1. Python uv run --script Pattern

**Reference File:** `/Users/terry/scripts/takeout-migrate.py`

### Exact Shebang & Dependencies Format
```python
#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pyyaml"]  # or empty list [] for stdlib-only
# ///
"""Docstring with usage examples."""

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
```

**Critical Points:**
- Shebang: `#!/usr/bin/env -S uv run --script` (must be exact)
- `# /// script` block defines inline dependencies (PEP 723)
- No external venv needed — uv handles it
- Python 3.13+ (uv default, per MEMORY.md)
- Inline arg parsing with `sys.argv`
- Direct execution: `vinculum [args]` works from any directory

---

## 2. SQLite Query Patterns

### Photos.sqlite Reference (Read-Only SQLite)
**Reference File:** `/Users/terry/scripts/photos.py` (lines 49-170)

```python
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta

DB_PATH = Path.home() / "Pictures" / "Photos Library.photoslibrary" / "database" / "Photos.sqlite"

# Read-only URI connection
uri = f"file:{DB_PATH}?mode=ro"
conn = sqlite3.connect(uri, uri=True)
conn.row_factory = sqlite3.Row  # Enable dict-like access

# Parameterized query
sql = """
    SELECT column1, column2, ZDATECREATED
    FROM TABLE_NAME
    WHERE condition = ?
    ORDER BY ZDATECREATED DESC
    LIMIT ?
"""
rows = conn.execute(sql, (value, limit)).fetchall()
results = [dict(r) for r in rows]
conn.close()
```

**Key Practices:**
- Always use `mode=ro` (read-only, safe for system DBs)
- `row_factory = sqlite3.Row` enables column access by name
- Parameterized queries (`?` placeholders) prevent SQL injection
- Explicit `conn.close()` or use context manager
- Test locally first on real DB

### iMessage Database
**Location:** `~/Library/Messages/chat.db`
**Format:** SQLite 3.x (confirmed accessible)
**Schema:** Standard macOS/iOS Core Data format
- `message` table: `ROWID`, `handle_id`, `text`, `date`, `date_read`, etc.
- `handle` table: `ROWID`, `id` (phone/email), `country`, etc.
- `chat` table: `ROWID`, `guid`, `display_name`, etc.

---

## 3. Subprocess & JSON Patterns

### Safe Command Execution
**Reference File:** `/Users/terry/scripts/job-heartbeat.py` (lines 1-50)

```python
import subprocess
import json
import sys

# Run command with JSON output
result = subprocess.run(
    ["wacli", "chats", "list", "--json"],
    capture_output=True,
    text=True,
    timeout=30
)

if result.returncode != 0:
    print(f"Error: {result.stderr}", file=sys.stderr)
    sys.exit(1)

try:
    data = json.loads(result.stdout)
except json.JSONDecodeError as e:
    print(f"JSON parse error: {e}", file=sys.stderr)
    sys.exit(1)
```

**Key Practices:**
- `capture_output=True` + `text=True` for string parsing
- Set `timeout` (10-30s for CLI tools)
- Always check `returncode` before parsing
- Handle JSON decode errors gracefully
- Use `sys.stderr` for error logging

---

## 4. wacli Integration Patterns

### From keryx Skill
**File:** `/Users/terry/skills/keryx/SKILL.md`

#### Contact Resolution Commands
```bash
wacli contacts search --json           # All contacts with JID mappings
wacli chats list --query --json        # Recent chats (may include duplicates for dual JIDs)
wacli messages list --chat <JID> --json  # Messages for specific chat
```

#### Dual-JID Architecture
- Each WhatsApp contact has TWO JIDs:
  - **Phone JID:** `<number>@s.whatsapp.net` (original pairing)
  - **LID JID:** `<uuid>@lid` (linked device)
- Same conversation appears in wacli as **two separate chats**
- Must merge by timestamp + content to avoid duplicates

#### Critical Gotchas
1. **Daemon must be running** — check with `keryx sync status`
   - If down: `keryx sync restart` or `keryx sync start`
2. **Cache location:** `~/Library/Application Support/keryx/contacts.json` (1h TTL)
3. **LID name mismatch:** If a contact's LID chat has different display name than phone JID, reads may look stale
   - Workaround: query both JIDs separately, or check `keryx chats --limit 20` to spot LID
4. **Business messages:** wacli PR #79 fixed rendering (patched binary at `/opt/homebrew/Cellar/wacli/0.2.0/bin/wacli`)
   - See: `/Users/terry/docs/solutions/wacli-business-message-fix.md`

---

## 5. Contact Deduplication & Merging

### WhatsApp Dual-JID Pattern
```python
def merge_whatsapp_contacts(phone_jid, lid_jid):
    """Merge messages from both JIDs, deduplicate by timestamp + content."""
    messages_phone = query_wacli(phone_jid)
    messages_lid = query_wacli(lid_jid)
    
    all_messages = messages_phone + messages_lid
    all_messages.sort(key=lambda m: m['timestamp'])
    
    # Deduplicate by (sender, timestamp, text)
    seen = set()
    unique = []
    for msg in all_messages:
        key = (msg['sender'], msg['timestamp'], msg['text'])
        if key not in seen:
            seen.add(key)
            unique.append(msg)
    
    return unique[-1] if unique else None  # Last message
```

### iMessage by Handle Pattern
```python
def get_imessage_last_message(handle_id):
    """Get last message from a specific phone/email."""
    sql = """
        SELECT text, date, date_read
        FROM message
        WHERE handle_id = (SELECT ROWID FROM handle WHERE id = ?)
        ORDER BY date DESC
        LIMIT 1
    """
    row = conn.execute(sql, (handle_id,)).fetchone()
    return dict(row) if row else None
```

---

## 6. State & Caching

### State File Pattern
**Reference Files:** `takeout-migrate.py` (lines 223-239), `job-heartbeat.py` (lines 10-20)

```python
import json
from pathlib import Path

STATE_FILE = Path.home() / ".cache" / "vinculum-state.json"

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {
        "last_check": None,
        "last_contacts": {},  # contact_id -> last_msg_timestamp
        "inactive_count": 0,
    }

def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
```

**Location:** `~/.cache/` (standard macOS ephemeral state location)

---

## 7. Date/Time Handling (HKT)

### From takeout-migrate.py & photos.py

```python
from datetime import datetime, timezone, timedelta

HKT = timezone(timedelta(hours=8))

def now_hkt() -> str:
    return datetime.now(HKT).strftime("%Y-%m-%d %H:%M:%S")

def days_ago(timestamp: float) -> int:
    """Calculate days between Unix timestamp and now (HKT)."""
    now = datetime.now(HKT)
    then = datetime.fromtimestamp(timestamp, tz=HKT)
    return (now - then).days

# Note: iMessage uses Unix epoch (seconds since 1970-01-01)
# Photos.sqlite uses Core Data epoch (seconds since 2001-01-01)
```

---

## 8. Error Handling & Logging

### Standard Pattern
**Reference File:** `/Users/terry/scripts/takeout-migrate.py` (lines 62-72)

```python
import sys
from pathlib import Path

LOG_FILE = Path.home() / ".cache" / "vinculum.log"

def log(msg: str) -> None:
    """Log to stdout and file with timestamp."""
    timestamped = f"[{now_hkt()}] {msg}"
    print(timestamped)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(timestamped + "\n")

# Usage
try:
    result = some_operation()
except Exception as e:
    log(f"ERROR: {e}")
    sys.exit(1)
```

---

## 9. Output Format Examples

### Structured Listing (Reference: keryx, photos.py)
```
Found 24 inactive contacts (last message >7 days ago)

Contact Name              Platform    Last Message         Days Ago
Herman                    WhatsApp    2026-02-15 14:32     17
Dorothy                   iMessage    2026-02-20 09:15     12
...

SUMMARY: 24 contacts queried, 8 inactive (>7 days), 16 active
```

### Command-Line Arguments
```python
import sys

def main():
    args = sys.argv[1:]
    
    # vinculum 7 --verbose
    days = int(args[0]) if args and args[0].isdigit() else 7
    verbose = "--verbose" in args or "-v" in args
    
    # Process...

if __name__ == "__main__":
    main()
```

---

## 10. CRITICAL PATTERNS (From critical-patterns.md)

**File:** `/Users/terry/docs/solutions/patterns/critical-patterns.md`

1. **WhatsApp Safety:** NEVER send messages directly. Draft commands, let user run them.
2. **SQLite Read-Only:** Always use `mode=ro` for system DBs (iMessage, Photos).
3. **Permission Checks:** iMessage DB requires Full Disk Access grant. Test first with:
   ```bash
   sqlite3 ~/Library/Messages/chat.db "SELECT COUNT(*) FROM message;" 2>&1
   ```

---

## 11. File Locations Reference

| Resource | Path | Type | Access |
|----------|------|------|--------|
| Python scripts | `~/scripts/` | .py | Executable |
| CLI tools | `~/bin/` | Symlinks | Executable |
| iMessage DB | `~/Library/Messages/chat.db` | SQLite | Read-only (Full Disk Access required) |
| Photos DB | `~/Pictures/Photos Library.photoslibrary/database/Photos.sqlite` | SQLite | Read-only |
| keryx contacts cache | `~/Library/Application Support/keryx/contacts.json` | JSON | 1h TTL |
| State files | `~/.cache/` | JSON | User-owned |
| Logs | `~/.cache/vinculum.log` | Text | Append-only |

---

## 12. Gotchas & Prevention

### For vinculum Implementation

| Gotcha | Prevention |
|--------|-----------|
| iMessage DB locked (in use) | Catch `sqlite3.OperationalError`, gracefully degrade |
| wacli daemon down | Check `keryx sync status` first, warn if down |
| Dual JID duplicates | Always deduplicate by (sender, timestamp, text) |
| Stale keryx cache | Don't rely on `contacts.json` — call `wacli contacts search --json` directly |
| LID name mismatch | Query both JIDs, merge by timestamp not name |
| No messages in cutoff window | Return `None` for `last_msg_date`, show "Never messaged" |
| Timezone bugs | Use HKT for display, Unix timestamp for comparisons |
| JSON parse failures | Catch `JSONDecodeError`, log stderr, don't crash |

---

## 13. What to Build

**vinculum Implementation Checklist:**

- [ ] Query `wacli chats list --json` → extract all JIDs
- [ ] For each contact, query both `@s.whatsapp.net` and `@lid` JIDs separately
- [ ] Merge WhatsApp messages by timestamp + content deduplication
- [ ] Query iMessage DB: `SELECT MAX(date) FROM message WHERE handle_id = ...`
- [ ] Group by contact (phone/email), get last message timestamp
- [ ] Filter: show only contacts with last message > N days ago (default 7)
- [ ] Output: contact name, platform, last message date, days since last message
- [ ] Optional: `--verbose` flag for last message preview
- [ ] Graceful errors: iMessage locked, wacli down, no messages
- [ ] State file for optional caching / debug history

---

## 14. Related Documentation

| Document | Path | Coverage |
|----------|------|----------|
| wacli business message fix | `/Users/terry/docs/solutions/wacli-business-message-fix.md` | Proto handling, patched binary path |
| keryx skill | `/Users/terry/skills/keryx/SKILL.md` | Contact resolution, dual JID, daemon management |
| Critical patterns | `/Users/terry/docs/solutions/patterns/critical-patterns.md` | Safety rules, permission gotchas |
| photos.py reference | `/Users/terry/scripts/photos.py` | Full SQLite patterns, Core Data timestamp handling |
| takeout-migrate.py reference | `/Users/terry/scripts/takeout-migrate.py` | State files, logging, command execution |
| job-heartbeat.py reference | `/Users/terry/scripts/job-heartbeat.py` | Subprocess + JSON, error handling |

---

## Summary

**vinculum** should be a small, clean tool (~200-300 lines) that:
1. Queries two data sources (wacli, iMessage)
2. Merges + deduplicates intelligently (dual JID, timestamp-based)
3. Surfaces inactive contacts (no message in N days, default 7)
4. Handles errors gracefully (daemon down, DB locked, no permission)
5. Logs all actions for debugging
6. Uses standard patterns from existing scripts (state, logging, subprocess, SQLite)
