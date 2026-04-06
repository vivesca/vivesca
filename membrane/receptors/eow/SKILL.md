---
name: eow
description: "End-of-work checkpoint. Synthesise the work day, capture mood, note unfinished threads. \"eow\", \"end of work\", \"done working\". NOT for session end (legatum) or bedtime (daily)."
effort: high
user_invocable: true
---

# End of Work

Work-day close — the gap between per-session `/legatum` and bedtime `/daily`.

## Triggers

- "eow", "end of work", "done working", "closing work"
- After the last work session of the day (before evening personal time)

## What This Is

A checkpoint that looks at the **whole work day** as a unit. `/legatum` handles individual sessions. `/daily` handles the full day before bed. This sits between them: "how was the work day?"

## What This Is NOT

- Not a session wrap (that's `/legatum`)
- Not the daily close (that's `/daily` — handles tomorrow preview, bedtime mood)
- Does not write the Tomorrow section

## Workflow

1. **Prep (silent)** — before the conversation:
   - Run `date` (HKT). If fails, use system-provided date.
   - Read today's daily note (`~/epigenome/chromatin/Daily/YYYY-MM-DD.md`) — session logs from `/legatum` should already be there.
   - Scan `~/epigenome/TODO.md` for items with today's date or imminent due dates.
   - Run `gog gmail search "in:inbox" --limit 5`.
   - If daily note is empty/missing, delegate history scan to a subagent.

2. **Conversation** — ask Terry one open question: **"How was the work day?"**
   - Let Terry talk. Follow up naturally — dig into what mattered, what felt off, what's unfinished.
   - Use the daily note and TODO scan as context to ask good follow-up questions (don't dump them as a report).
   - If inbox has items, mention it naturally in the conversation ("also, X unread — worth clearing before you switch off?").
   - This should feel like a 2-minute chat, not a form. 2-3 exchanges max.

3. **Summarise** — once the conversation feels done, write the EOW close:

```markdown
---

## End of Work

**Themes:** [comma-separated theme labels, drawn from conversation + daily note]

[2-3 sentence synthesis — what Terry said the day was about, what moved, what's stuck. Use Terry's framing, not yours.]

**Unfinished:**
- [ ] [Threads carrying over — from conversation + TODO scan]

**Work mood:** [one honest line — Terry's words, not a paraphrase]
```

   - Append to today's daily note.
   - TODO sweep: mark anything completed, add any new commitments mentioned in conversation.

4. Done. No tomorrow preview — `/daily` handles that before bed.

## Output

Confirm what was written to the daily note. One sentence, not a recap.

## Notes

- If `/legatum` wasn't run on the last session, do a quick session log first (step 2 of legatum), then proceed
- If Terry runs `/daily` without running `/eow` first, daily should still work fine — eow is additive, not required
- The work mood is separate from the daily mood — work might be frustrating but the evening great, or vice versa
- Keep it fast — a short conversation, not a retrospective
- **Conversation first, summary second.** Never present a pre-built report for Terry to approve. The daily note logs and TODO scan are *your* context for asking better questions — they're not the output.

## Example

> "How was the work day?"
> [Terry talks — 2-3 exchanges]
> "Got it. I've written the EOW close to the daily note — themes: X, Y, Z. Enjoy the evening."
