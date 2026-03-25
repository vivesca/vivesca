# Critical Patterns

**ALWAYS check this file before starting work.** These patterns prevent catastrophic or high-severity issues.

---

## HARD RULES (Always Apply)

### Search Safety

**Grep/Glob on /Users/terry is BLOCKED.**

Never run Grep or Glob without a specific `path` parameter on `/Users/terry`. The safe_search.py script will block it. Always scope to a subdirectory.

```
# BAD - will error
Grep: pattern="foo" path="/Users/terry"

# GOOD
Grep: pattern="foo" path="/Users/terry/code/vivesca-terry/chromatin"
```

### Destructive Operations

**rm -rf requires verification.**

Before `rm -rf`, ALWAYS run:
```bash
python3 ~/scripts/safe_rm.py <path>
```

Protected paths (not backed up): `~/.ssh`, `~/.gnupg`, `~`, `/`

### WhatsApp Safety

**NEVER send WhatsApp messages directly.**

Draft the command and let Terry run it:
```bash
wacli send text --to "852XXXXXXXX" --message "text here"
```

OpenClaw WhatsApp plugin must stay DISABLED (`plugins.entries.whatsapp.enabled: false`).

**Incident context:** Bot pairing codes were sent to real contacts (Gavin, Simon) when plugin was enabled.

### Permission Resets

**NEVER run `tccutil reset`.**

This breaks Screen Recording permissions for Jump, Peekaboo, and other tools. The fix requires restarting tmux from Ghostty locally.

---

## Browser Automation Patterns

### Always Resize First

Before `read_page` or screenshots in Claude in Chrome:
```javascript
resize_window({ width: 800, height: 600 })  // chat apps
resize_window({ width: 1024, height: 768 }) // general
```

Large viewports waste tokens on empty space.

### React Inputs Need `fill`, Not `type`

Use `fill` for React inputs—it triggers proper input events. `type` leaves send buttons disabled because React doesn't detect the change.

### Refs Shift After Actions

After any agent-browser action (click, fill), refs change. Always re-snapshot before the next action.

---

## Search & Context Patterns

### Check Vault Before Asking

When Terry asks about someone or something, search the vault first. The answer is usually there.

### Fast Subagent Pattern

1. Scout with `ls -R <path>` first
2. Pass exact file list to subagent
3. Explicitly instruct: "search only within <directory>"

---

## Tool-Specific Quirks

### Gmail MCP Cannot Reply in Thread

`send_email` creates NEW email, not reply. No thread ID support. For thread continuity, Terry must reply manually or use browser.

### OpenCode Config Location

Permissions at `~/.config/opencode/opencode.json`, NOT `~/.opencode/config.json`.

### Python hash() is Unstable

Salted per-process. Use `hashlib.sha256` for persistent caches.

---

## Date/Time

### Day-of-Week: USE PYTHON

Any reference to day-of-week → run Python calculation FIRST.

```python
from datetime import date
date(2026, 2, 4).strftime("%A")  # Tuesday
```

Never trust mental math. Anchor: Jan 1, 2026 = Thursday.

### HKT Day Boundaries

Convert timestamps to HKT (UTC+8) before grouping by day.
