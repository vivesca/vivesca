---
name: hm-tracker
description: Track HMs, predict hiring windows (90-180d). Use to identify when hiring managers are likely to hire based on role tenure. Triggers on "hm-tracker", "hiring managers", "who's hiring soon".
---

# HM Tracker

Track hiring managers by role tenure to predict when they'll hire.

## Purpose

Hiring managers typically hire:
- **90-120 days**: Initial team building after joining
- **120-180 days**: Second wave after assessment period
- **180+ days**: Replacement/expansion hires

This skill tracks HM movements and predicts hiring windows.

## Trigger

Use when:
- User says "hm-tracker", "hiring managers", "who's hiring"
- Weekly reset (auto-check for HMs entering window)
- When a new HM is identified (add to tracker)

## Inputs

- **mode**: "scan" (check windows) | "add" (new HM) | "update" (status change)
- **name** (for add/update): HM name
- **company** (for add/update): Company
- **start_date** (for add): When they started role

## Workflow

### Mode: Scan

1. **Read [[HM Tracker]]**

2. **Calculate windows**:
   For each HM:
   - Days since start = Today - Start Date
   - Window status:
     - <90 days: "Pre-window"
     - 90-180 days: "Active window ⭐"
     - >180 days: "Post-initial window"

3. **Flag actionable HMs**:
   - Entering window this week
   - In active window, no recent outreach
   - Approaching end of window

4. **Output summary**

### Mode: Add

1. **Capture HM details**:
   - Name
   - Company
   - Title
   - Start date (or estimate)
   - Source (how you know)

2. **Calculate predicted window**:
   - Begin: Start Date + 90 days
   - Peak: Start Date + 120 days
   - End: Start Date + 180 days

3. **Update [[HM Tracker]]**

### Mode: Update

1. **Update status**:
   - Outreach made
   - Response received
   - Role filled
   - No longer relevant

## Output

**Scan Mode:**
```markdown
# HM Tracker Scan — [Date]

## Entering Window This Week
| Name | Company | Start Date | Days In | Action |
|------|---------|------------|---------|--------|
| [Name] | [Company] | [Date] | [X] | Reach out |

## Active Window (90-180 days)
| Name | Company | Start Date | Days In | Last Contact | Next Step |
|------|---------|------------|---------|--------------|-----------|
| [Name] | [Company] | [Date] | [X] | [Date/Never] | [Action] |

## Approaching Window (60-90 days)
| Name | Company | Start Date | Days Until Window |
|------|---------|------------|-------------------|
| [Name] | [Company] | [Date] | [X] days |

## Suggested Actions
1. [Specific outreach to make]
2. [Follow-up on prior contact]
```

**Add Mode:**
```markdown
# Added HM: [Name] at [Company]

- **Start Date:** [Date]
- **Predicted Window:** [Start] to [End]
- **Days Until Window:** [X]

Next: Set reminder for [Window Start Date]
```

## HM Sources

Where to find HM movements:
1. **LinkedIn notifications**: Set alerts for target companies
2. **Recruiter intel**: They mention HMs during calls
3. **Job postings**: "Reports to [Name]" often named
4. **Company announcements**: Leadership hires
5. **Interview process**: You meet HMs

## Integration

- **`/weekly-reset`**: Auto-scans for HMs in window
- **`/interview-prep`**: Adds interviewed HMs to tracker
- **`/debrief`**: Updates HM status after interactions

## Examples

**User**: "hm-tracker"
**Action**: Scan all tracked HMs, identify actionable ones
**Output**: Summary of HMs by window status

**User**: "Add Hannah from Intact as an HM, she just started in December"
**Action**: Add to tracker, calculate window
**Output**: Confirmation with predicted hiring window

**User**: "Who's likely to be hiring soon?"
**Action**: Filter HMs entering 90-180 day window
**Output**: List of actionable HMs with outreach suggestions
