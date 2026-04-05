---
name: nuntius
description: "Cora CLI — AI email assistant. Reading briefs, managing email todos, chatting with Cora. \"cora\", \"email brief\", \"email todos\". NOT for direct Gmail ops — use stilus."
triggers:
  - nuntius
  - cora
  - brief
  - email
  - todo
---

# Cora CLI — AI Email Assistant

Cora is an AI-powered email assistant that processes Gmail, generates daily briefs, manages todos, and drafts replies. You interact with Cora through the `cora` command-line tool.

## Quick Start

Before running any command, verify you're authenticated:

```
cora whoami
```

If not authenticated, log in with your API token:

```
cora login --token=REDACTED_ROTATED_2026_04_05
```

## Commands Reference

### Check Status
```
cora status    # Account status, brief settings, usage stats
cora whoami    # Current user and account info
```

### Email Briefs
```
cora brief              # List recent briefs
cora brief show         # Show latest brief details
cora brief show <id>    # Show specific brief
cora brief show --open  # Show and open in browser
cora brief --json       # JSON output (note: briefs use --json not --format json)
```

**Known crash:** `cora brief show` crashes mid-render on PPS payment items — drops remaining emails silently. Fallback: read via browser.
```bash
porta run --domain cora.computer --selector body "https://cora.computer/14910/briefs?date=YYYY-MM-DD&time=morning"
# or for afternoon brief:
porta run --domain cora.computer --selector body "https://cora.computer/14910/briefs?date=YYYY-MM-DD&time=afternoon"
```
Login to cora.computer in Chrome first. Account ID is `14910`.

### Todos
```
cora todo list                                           # List pending todos
cora todo list --all                                     # Include completed
cora todo show <id>                                      # View details
cora todo create "Title"                                 # Create new todo
cora todo create "Title" --priority high --due tomorrow  # With options
cora todo edit <id> --title "New" --priority low         # Update
cora todo complete <id>                                  # Mark done
cora todo delete <id> --force                            # Delete
cora todo list --format json                             # JSON output
```

### Email
```
cora email glimpse          # Quick inbox view (fast, cached)
cora email search "query"   # Search with Gmail query syntax
cora email show <id>        # Full email details
cora email archive <id>     # Archive email
cora email draft <id>       # Queue reply draft (async, returns immediately)
```

### Chat (slow — use only when no instant command fits)
```
cora chat send "message"              # New conversation (10-60s)
cora chat send "message" --chat <id>  # Continue conversation
```

## Daily Email Workflow (AI-native with review layer)

Cora is the primary triage layer. Inbox = action queue; archive = done. Work off Cora's output, not the raw inbox — but spot-check while trust is being established.

### Morning routine
```bash
cora brief show          # Step 1: digest — what came in, what's flagged
cora todo list           # Step 2: action queue — work from here, not the inbox
cora email glimpse       # Step 3: spot-check — scan inbox for anything brief missed
```

### Closing an email
Once actioned: archive it. Cora stops seeing it; inbox stays clean.
```bash
cora email archive <id>
```

### Trust-building review (run until confident — target ~2 weeks clean)
After the brief, ask: did Cora catch everything I would have caught manually?
- Silent miss → log it, check domain filters
- Missed action item → check if todo was created
- Two misses in the same category → fix the root cause (filter, label, or Cora config)

### Exit criteria for dropping the spot-check
- 2 weeks with no silent misses
- Todos consistently match actual action items
- Keep domain filters permanently regardless

## Best Practices

- **Prefer instant commands** over `cora chat send` — chat is 10-60s
- **briefs use `--json`** not `--format json` (unlike other commands)
- **Don't use `cora flow`** — requires interactive stdin, will hang
- **Don't retry failures** more than once — ask user for guidance

## Known Gotchas

### Unread count in "All Mail" is expected noise
Cora intentionally never marks emails as read. Its model: the daily brief is the reading interface, not Gmail. Cora labels emails (`Cora/Newsletter`, `Cora/Payments` etc.) but leaves read/unread state untouched. The `📥 Next Brief` label tracks "briefed yet", not Gmail's unread flag.

**Don't try to zero the All Mail unread count** — it will just accumulate again. Set Gmail's unread badge to inbox-only (Settings → General → Inbox count). Inbox zero is the goal; All Mail unread is noise.

### Cora/Action emails are invisible — not in inbox AND not in brief
Confirmed Mar 2026: emails labelled `Cora/Action` by Cora were excluded from both the inbox (INBOX label stripped) and the daily brief. The label exists but leads nowhere — there is no workflow that surfaces it automatically.

**Mitigation:** `epistula` Step 1 explicitly pulls `label:Cora/Action` as a third parallel search. Always triage these alongside the inbox.

### Interview/recruiter emails silently missing from inbox
Two confirmed cases of interview invitation emails arriving without an `INBOX` Gmail label — meaning they never appear in inbox and Cora never processes them (Cora only scans inbox). Root cause unclear: may be Gmail miscategorisation or Cora stripping INBOX during processing.

Affected emails had `CATEGORY_PERSONAL` but no `INBOX` label and no `Cora/` label — i.e. Cora never touched them at all.

**Permanent mitigation:** Gmail filters for active job application domains force `--important` and `--never-spam`. Currently set for:
- Company domains: `aia.com`, `mtr.com.hk`, `capco.com`
- ATS platforms (cover any company using these): `myworkday.com`, `greenhouse.io`, `lever.co`, `smartrecruiters.com`, `taleo.net`, `icims.com`

Add new company domains when applying. ATS platforms are already covered globally.
```bash
gog gmail filters create --from "<domain>" --never-spam --important
```

**When expecting a reply, also proactively search:**
```bash
cora email search "from:<domain>"
gog gmail search "from:<domain>"  # catches emails Cora missed entirely
```

**If email is missing INBOX label, restore it:**
```bash
gog gmail thread modify <threadId> --add INBOX
```

Real cases: MTR interview (Mar 4 2026) — `important_draft` category. AIA/Cherry Ma interview (Mar 6 2026) — `CATEGORY_PERSONAL`, no INBOX, no Cora label. AIA Workday interview (Mar 9 2026) — sent from `aia@myworkday.com`, no Cora label, caught via Gmail diff. Filter for `myworkday.com` added Mar 11 2026.

### gog thread show truncates body
`gog gmail thread show <id>` truncates the email body at ~1000 chars. For full content — headers (e.g. `List-Unsubscribe`) and base64 body parts — use:
```bash
gog gmail thread get <id> --json | python3 -c "
import sys, json
data = json.load(sys.stdin)
def walk(obj):
    if isinstance(obj, dict):
        if obj.get('name','').lower() == 'list-unsubscribe': print(obj.get('value',''))
        for v in obj.values(): walk(v)
    elif isinstance(obj, list): [walk(i) for i in obj]
walk(data)
"
```

## Error Codes

- `0` — Success  
- `1` — General error  
- `2` — Authentication required (`cora login`)  
- `3` — Resource not found  
- `4` — Validation error
