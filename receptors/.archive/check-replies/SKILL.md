---
name: check-replies
description: Scan LinkedIn, WhatsApp, and Gmail for replies from network contacts and recruiters. Use when user says "check replies", "any messages", "who replied", or after being AFK.
---

# Check Replies

Scan multiple communication channels for replies from job search contacts. Consolidates LinkedIn DMs, WhatsApp messages, and Gmail into one view. Designed to run when catching up after being AFK.

## Trigger

Use when:
- Terry says "check replies", "any messages", "who replied"
- After being AFK (sleep, exercise, interviews)
- Part of morning review

## Inputs

- **channels** (optional): Which to check — "all" | "linkedin" | "gmail" | "whatsapp" — default: all
- **since** (optional): Time window — "today" | "yesterday" | "24h" | "week" — default: today

## Workflow

1. **Read context**:
   - `/Users/terry/notes/Job Hunting.md` — know who to watch for
   - Extract key contact names (recruiters, hiring managers, network)

2. **Check Gmail** (via Gmail MCP):
   - Search for replies from known contacts
   - Search for new recruiter outreach
   - Flag urgent or time-sensitive messages

3. **Check LinkedIn** (via browser automation):
   - Open LinkedIn messaging
   - Scan for unread messages
   - Note sender and preview

4. **Check WhatsApp** (via browser if available):
   - Note: May require manual check if not accessible
   - Flag if WhatsApp check needed

5. **Consolidate and prioritize**:
   - Group by urgency (interview scheduling > recruiter reply > networking)
   - Flag action-required items
   - Note any missed messages from VIP contacts

6. **Output summary**

## Error Handling

- **If LinkedIn requires login**: Note it, continue with other channels
- **If WhatsApp not accessible**: Flag for manual check
- **If no new messages**: Report "all clear" with last check time

## Output

```
Replies since [time]:

LinkedIn (X new):
- [Name] - [Preview] - [Urgency]

Gmail (X new):
- [Sender] - [Subject] - [Urgency]

WhatsApp:
- [Status or manual check needed]

Action required:
1. [Reply to X about Y]
2. [Schedule with Z]

VIP contacts (no reply yet):
- [Name] - Last contact: [date]
```

## Examples

**User**: "check replies" (after waking up)
**Action**: Scan all channels for overnight messages
**Output**: Consolidated list of new messages, prioritized by urgency

**User**: "any LinkedIn messages?"
**Action**: Check LinkedIn DMs only
**Output**: List of unread LinkedIn messages
