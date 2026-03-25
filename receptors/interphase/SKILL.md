---
name: interphase
description: Use when heading home from work — single evening routine covering full inbox triage, messages, work summary, brain dump, and tomorrow prep. "leaving office", "on the bus", "going home", "end of day", "check emails", "review inbox", "interphase"
user_invocable: true
---

# Interphase — Evening Routine

The quiet phase between divisions. Everything between "leaving the office" and "walking through the door." Process inputs, consolidate, prep for the next cycle.

## Design

Phone-friendly (Blink/tmux). Target: one bus ride. No deep reflection — capture facts, clear queues, prep tomorrow.

## Context Load (parallel, before starting)

- `[[Email Threads Tracker]]` (`~/notes/Email Threads Tracker.md`)
- `~/code/vivesca/engrams/prospective.md` — check for `WHEN: email triage` or `WHEN: interphase` entries
- Today's daily note (`~/notes/Daily/YYYY-MM-DD.md`)

## Steps

### 0. Gather

Call MCP tool `gather_interphase`. All deterministic gathering runs here (inbox, WhatsApp, calendar, Praxis, budget, reminders, email threads, prospective memory). Review output, then proceed.

### 1. Inbox Triage

Use vivesca `sorting_*` MCP tools directly (search, thread, categorize, mark_read, archive). For each inbox email:

1. **Drill inbox** — `sorting_thread` on every unread inbox email (skip only obvious spam)
2. **Drill archived** — from the gather output, `sorting_thread` on EVERY Cora-archived email tagged `Cora/Important Info` or `Cora/Important Context`. Also drill any archived email where the subject suggests a payment, failure, approval, or deadline. Don't rely on Cora's "needs attention" count — it misses things.
3. **Cora briefs** — read today's morning + afternoon briefs via `sorting_thread`. Cross-check: every email mentioned in the briefs should already be drilled above. If any were missed, drill them now.
4. **Decide** — for each drilled email: action_required / monitor / archive
5. **Act** — mark read + archive noise; flag action items to Terry
6. **Email Threads Tracker** — update if threads resolved or new threads opened

Check prospective memory for email-triage triggers (Grammarly, M365, Surfshark, etc.) and apply.

### 2. Messages

- WhatsApp via `keryx read <name>` — draft responses, never send
- LinkedIn notifications — replies, messages from network
- If a person has history, `amicus lookup <name>` for context

### 3. Brain Dump

Ask Terry: **"Anything still rattling around?"**

Capture to today's daily note. One or two exchanges max. Get it out of his head, not processed.

### 4. What Shipped Today

- Read today's daily note (`~/notes/Daily/YYYY-MM-DD.md`) for cytokinesis session logs
- If empty/missing, delegate to subagent (haiku): `python3 ~/scripts/chat_history.py --full`
- Write a 2-3 line summary to the daily note
- If anything shipped has consulting relevance (methodology, governance, AI pattern), append one line to `~/notes/Consulting/_sparks.md` under today's date: `- #[tag] — **[Title]**: [one-line consulting implication]`

### 5. Tomorrow Prep

Run in parallel: `fasti` (calendar), `moneo ls` (due items), Praxis.md (items with tomorrow's date or overdue), Schedule.md (recurring commitments).

If meetings tomorrow: one-line prep note for each.

**Thursday only:** Weekly token reset ~11am HKT tomorrow. Run `usus --json` — flag significant headroom.

### 6. Nudge

Quick scan for **blocked items that need a nudge** — things waiting on others where a follow-up is overdue, or time-sensitive items that need action before they expire. Examples: awaiting replies (WhatsApp, email), pending verifications, membership renewals, appointments to book. One-line flag per item. Don't solve — just surface.

### 7. Daily Note Close

Header: `# YYYY-MM-DD — Day — themes, comma, separated`

Append:
```markdown
## Interphase

**Shipped:** [2-3 line summary]
**Tomorrow:** [key items — meetings, deadlines, prep needed]
**Open threads:** [anything waiting on others]
**Nudges:** [items that need a poke tomorrow]
**Day score:** [1-5, based on what actually shipped vs what mattered]
```

### 8. Flush Prospective

Check prospective memory for `WHEN: next session` triggers. Attempt each. Update prospective entry with result (success, failed + reason, deferred + why).

### 9. Praxis Sync

Update resolved items, add new open items, mark blocked/waiting.

Then: **"You're done. Evening is yours."**

## Fail States

- `cora brief show` crashes → `porta run --domain cora.computer` fallback
- `gog gmail` fails → note "inbox skipped", continue
- Daily note empty + history scan fails → continue with current session context, label "partial"
- Any step fails → skip it, never block the whole routine

## Boundaries

- Draft only — never send (WhatsApp, email, LinkedIn)
- No deep reflection or extended conversation
- Only update: daily note, Email Threads Tracker, Praxis
- Nothing cognitive after walking through the door
