---
name: weekly-reset
description: Sunday ritual to review job search status and plan the week ahead. Use when user says "weekly reset", "sunday reset", or on Sundays.
---

# Weekly Reset

Sunday ritual to review job search status, identify follow-ups, and plan the week ahead.

## Trigger

Use when:
- Every Sunday
- User says "weekly reset", "sunday reset"
- At natural week boundaries

## Inputs

- **week** (optional): Date range to review, defaults to current week

## Workflow

1. **Read current state**:
   - `/Users/terry/notes/Job Hunting.md` — pipeline, networking, applications
   - `/Users/terry/notes/CLAUDE.md` — context

2. **Identify week date range** (e.g., "Jan 19-25")

3. **Review & present summary**:

   **Pipeline Status:**
   - Interviews scheduled (with dates)
   - Awaiting responses
   - Recently applied (too early for signal)
   - Likely dead (>3 weeks, no response)

   **Networking Status:**
   - Calls/meetings this week
   - Who's in motion
   - Who needs follow-up

   **Follow-ups Due:**
   - Applications to nudge (1-2 weeks old)
   - Contacts to check in with
   - Deadlines approaching

   **Applications to Send:**
   - "Noted but not applied" roles worth pursuing
   - Prioritize by fit and deadline

   **Priorities for the Week:**
   - Top 2-3 actions
   - Key calendar items

4. **Run integrated scans** (in parallel where possible):
   - `/anti-signals` — Review rejection patterns, update rules
   - `/hm-tracker` scan — Check for HMs entering hiring window
   - `/market-radar` scan — Check for new hiring signals

5. **Offer AI news scan** for interview talking points (`/ai-news`)

6. **Update weekly note**

7. **Update Job Hunting.md** if changes recorded

## Integration

This skill integrates with:
- `/anti-signals` — Monthly pattern review
- `/hm-tracker` — Scan for HMs in hiring window
- `/market-radar` — Scan for new hiring signals

## Error Handling

- **If Job Hunting.md not found**: Create skeleton structure
- **If no applications in pipeline**: Focus on sourcing new roles
- **If user skipped last week**: Review 2-week period

## Output

**Template:**
```markdown
# Week of [Date Range]

## Priorities
1. [Top priority]
2. [Second priority]
3. [Third priority]

## Calendar
- **[Day]:** [Event]

## Pipeline
| Role | Status |
|------|--------|

## Follow-ups
- [ ] [Task]

## Applications to Send
- [ ] [[Role Name]] — [Brief note]

## Networking Waiting
- [Contact] — [status]

## HM Tracker
| Name | Company | Days In Role | Status |
|------|---------|--------------|--------|

## Market Signals
[Any new signals from /market-radar]

## Notes
[Any market context or observations]
```

**Location:** `/Users/terry/notes/Week of [date range].md`
