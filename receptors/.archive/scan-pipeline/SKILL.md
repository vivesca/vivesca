---
name: scan-pipeline
description: Review job hunting pipeline status, identify stale applications, suggest follow-ups. Use when user says "scan pipeline", "check pipeline", "what's stale", or for weekly reset prep.
user_invocable: true
---

# Scan Pipeline

Quick review of job hunting pipeline. Identifies stale items, pending actions, and suggests follow-ups. Designed to run async while Terry is AFK.

## Trigger

Use when:
- Terry says "scan pipeline", "check pipeline", "what's stale"
- Part of weekly reset or morning review
- Before/after being AFK to catch up on status

## Inputs

- **mode** (optional): "quick" (summary only) | "full" (detailed analysis) — default: quick
- **days_stale** (optional): Days without activity to consider stale — default: 7

## Workflow

1. **Read current state**:
   - `/Users/terry/notes/Active Pipeline.md` — live pipeline (source of truth)
   - `/Users/terry/notes/Job Hunting.md` — archive (comp, market signals, passed roles)
   - `/Users/terry/notes/CLAUDE.md` — context

2. **Analyze pipeline**:
   - Count by status: Applied, Interviewing, Offered, Rejected
   - Identify stale items (no update > days_stale)
   - Identify items with pending actions (follow-up due, prep needed)
   - Check for upcoming interviews

3. **Generate recommendations**:
   - Which applications to follow up on (prioritized)
   - Which contacts to nudge
   - Which roles to deprioritize/archive
   - Prep needed for upcoming interviews

4. **Output summary** (chat or vault depending on mode)

## Error Handling

- **If Job Hunting.md missing**: Prompt to create it or check path
- **If no stale items**: Report healthy pipeline, suggest proactive actions

## Output

**Quick mode** (chat only):
```
Pipeline: X applied, Y interviewing, Z stale

Stale (>7 days):
- [Company] - [Role] - Last: [date] - Action: [suggestion]

Upcoming:
- [Interview details]

Suggested actions:
1. [Action]
```

**Full mode**: Also saves to `/Users/terry/notes/Pipeline Scan - [date].md`

## Examples

**User**: "scan pipeline"
**Action**: Read Job Hunting.md, analyze status, output summary
**Output**: Quick summary of pipeline health and suggested actions

**User**: "what's stale in my pipeline?"
**Action**: Focus on stale items, suggest follow-ups
**Output**: List of stale applications with recommended actions
