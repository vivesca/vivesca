# Programmatic .shortcut File Creation (macOS 26 / Tahoe)

## Problem
Building a `.shortcut` file programmatically that uses a third-party AppIntent action without crashing Shortcuts.app.

## Key Findings

### 1. Correct Action Identifier Format
Third-party AppIntents use **bundle-prefixed identifiers** in `.shortcut` binary plists:
- ❌ Wrong: `CreateRepeatingReminderIntent`
- ✅ Correct: `com.phocusllp.duemac.CreateRepeatingReminderIntent`

**Source of truth:** `~/Library/Shortcuts/ToolKit/Tools-prod.v63-*.sqlite`
```sql
SELECT id, toolType FROM Tools WHERE id LIKE '%duemac%';
```
Returns: `com.phocusllp.duemac.CreateRepeatingReminderIntent|appIntent`

### 2. macOS 26 (Tahoe) Action ID Changes
Some built-in action identifiers changed between macOS 15 and 26:

| Old (macOS 15) | New (macOS 26) | Input key change |
|---|---|---|
| `is.workflow.actions.splittext` | `is.workflow.actions.text.split` | `WFInput` → `text` |

Check current valid IDs:
```sql
SELECT t.id, tl.name FROM Tools t
JOIN ToolLocalizations tl ON t.rowid = tl.toolId AND tl.locale = 'en'
WHERE tl.name LIKE '%Split%';
```

### 3. Import Name = Signed File's Filename
Shortcuts.app uses the **signed file's filename** (without `.shortcut`) as the shortcut's display name on import — NOT the `WFWorkflowName` field in the plist.

- `shortcuts sign ... --output /tmp/DueAddRecurring.shortcut` → imports as "DueAddRecurring"
- `shortcuts sign ... --output "/tmp/Due Add Recurring.shortcut"` → imports as "Due Add Recurring"

### 4. Permission Dialog on First Run
When `shortcuts run "ShortcutName"` uses a third-party AppIntent for the first time, macOS shows:
> "Allow 'ShortcutName' to run actions from 'Due'?"

Requires user click (screen must be on). After allowing, runs silently.

### 5. Due AppIntent Parameters
`com.phocusllp.duemac.CreateRepeatingReminderIntent` parameters:
- `title`: string
- `date`: dateComponents — connect via `is.workflow.actions.detect.date` output
- `repeatFrequency`: enum — values: `day`, `week`, `month`, `year`
- `repeatIntervalWeekly`: int (1 = every week)
- `syncWhenRun`: bool — set True for CloudKit sync

Enum format in plist: `{'identifier': 'week', 'value': 1}`

### 6. getitemfromlist with text.split
Connect via `WFInput` (unchanged). The output name from `text.split` is "Split Text".

## Working Shortcut Structure (macOS 26)
```
gettext          → receives "title|ISO_date" input
text.split       → splits by "|" (input key: 'text', not 'WFInput')
getitemfromlist  → item 1 = title
getitemfromlist  → item 2 = ISO date string
detect.date      → converts ISO string to Date
CreateRepeatingReminderIntent → creates recurring reminder in Due
```

## File Location
- Unsigned plist builder: `/tmp/DueAddRecurringFinal.shortcut` (ephemeral)
- Signed: `~/bin/DueAddRecurring.shortcut`
- moneo shortcut name: `"DueAddRecurring"`

## Signing
```bash
shortcuts sign --mode anyone --input /tmp/input.shortcut --output /tmp/output.shortcut
# Ignore "ERROR: Unrecognized attribute string flag" — these are warnings, not failures
```
