---
name: mora
description: Surface productive low-energy tasks when you have downtime. Use when energy is low, between meetings, or during idle moments.
user_invocable: true
triggers:
  - mora
  - rest
  - leisure
  - downtime
  - low energy
---

# Mora — Productive Downtime

Pull-based skill for low-energy windows. Surfaces quick wins that don't need deep focus.

## Steps

### 1. Quick Status Checks

Run in parallel:

- **Gmail:** `gog gmail search "is:unread" --max 5 --plain` — show unread count + sender/subject for top 5. Don't triage — just surface.
- **WhatsApp:** `wacli chat list 2>/dev/null | head -20` — show chats with unread messages.

Present as a quick dashboard: "3 unread emails, 1 WhatsApp message" style. If nothing unread, say so and move on.

### 2. Surface Low-Energy Tasks from TODO.md

If `~/notes/TODO.md` exists, read it and collect unchecked items (`- [ ]`) that fit a low-energy window. If missing, skip this step and note "No TODO.md found — nothing to surface":

**Explicit tag:** Items tagged `low-energy` — always show these.

**Inherently low-energy sections** (show items that aren't future-gated):
- 🏠 Home Tidying
- 📸 Personal
- 🛒 To Buy

**Recurring dailies not yet done:** Items with `recurring:daily` that are simple/habitual (e.g., meditation, razor, bedding). Skip study-heavy recurring items (GARP quiz, consulting-prep).

**Filter OUT:**
- Items gated by `when:` in the future (after today)
- Items gated by `someday` (unless also tagged `low-energy`)
- Items that clearly need deep focus (writing, research, prep, study)
- Items with `agent:` tag (these are for Claude, not leisure)
- Completed items (`- [x]`)

### 3. LinkedIn job alerts (post-noon only)

If current time is after 12:00 HKT, check `~/notes/Job Hunting/Job Alerts YYYY-MM-DD.md`:
- Count unchecked flagged roles (`- [ ]` lines)
- If any exist, include in the menu as: "💼 Job alerts: X roles flagged — `/evaluate-job`"
- Skip silently if file missing or all items checked

### 4. Inbox triage prompt (post-3pm only)

If current time is after 15:00 HKT, check inbox count from Step 1. If Gmail shows any unread/inbox items, include in the menu:

```
📧 Inbox triage: X in inbox — `/epistula` (10 min, wind-down)
```

This is the daily acta slot. Email is a low-energy end-of-day task, not a morning one.

### 5. Present Menu

Show results as a short, scannable list grouped by type:

```
📬 Inbox: 3 Gmail, 1 WhatsApp
📧 Inbox triage: 3 in inbox — /epistula (10 min, wind-down)
💼 Job alerts: 4 roles flagged
🏠 Quick wins: [2-5 items from TODO.md]
```

Keep it to **max 7 items total** (excluding inbox counts). If more qualify, pick the most actionable.

End with: "Want to tackle any of these, or just check messages?"

## Notes

- This skill does NOT do Gmail triage itself. It surfaces the count so Terry can decide to run `/epistula`.
- Don't add low-energy items to TODO.md from this skill — it's read-only on TODO.md.
- If Terry picks "check Gmail" or "acta", hand off to `/epistula` skill.
- If Terry picks a TODO item, help with it directly.
- The `low-energy` tag is compatible with the existing `/todo` system — items tagged this way still show in `/todo` normally.
