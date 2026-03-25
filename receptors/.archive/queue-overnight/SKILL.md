---
name: queue-overnight
description: Queue background job hunting tasks before sleep. Runs async agents that write results to vault for morning review. Use when user says "queue overnight", "before I sleep", "going to bed", or at end of /daily.
---

# Queue Overnight

Queue background agents to run job hunting tasks while Terry sleeps. Results are written to the vault and ready for morning review.

## Triggers

- "queue overnight"
- "before I sleep"
- "going to bed"
- End of `/daily` reflection
- Terry mentions stepping away for the night

## Workflow

1. **Get today's date** in `YYYY-MM-DD` format (HKT timezone)

2. **Read context:**
   - `/Users/terry/notes/Job Hunting.md` — check for upcoming interviews
   - Note any interviews in next 2 days that need prep

3. **Confirm tasks to queue** (quick check with user):
   ```
   Queuing overnight tasks:
   - Process new job alerts
   - Scan pipeline for stale items
   [- Prep for [Company] interview on [date]] ← if applicable

   Anything else to add? (or just "go" to start)
   ```

4. **Launch background agents** using Task tool with `run_in_background: true`:

   **Always run:**
   - `/process-job-alerts` — fetch and filter new LinkedIn job alerts
   - `/scan-pipeline` — identify stale applications and suggest follow-ups

   **If interview upcoming:**
   - `/interview-prep [company]` — deep research for upcoming interview

5. **Create overnight summary file:**
   - Path: `/Users/terry/notes/Overnight Queue - YYYY-MM-DD.md`
   - Lists what's queued and expected outputs
   - Morning can check this + the output files

6. **Confirm to user:**
   ```
   Queued 3 tasks running in background.
   Results will be in your vault by morning.

   Good night!
   ```

## Background Agent Prompts

### Process Job Alerts Agent
```
Run /process-job-alerts skill:
1. Fetch recent LinkedIn job alert emails from Gmail
2. Extract job URLs and filter against existing pipeline
3. Quick-assess each role for fit
4. Write summary to /Users/terry/notes/Job Alert Review - YYYY-MM-DD.md

Include:
- Table of roles found with PASS/CONSIDER verdict
- Roles worth deeper evaluation flagged for morning
- Update Passed On list in Job Hunting.md
```

### Scan Pipeline Agent
```
Run /scan-pipeline skill in full mode:
1. Read Job Hunting.md
2. Identify stale applications (>7 days no activity)
3. Identify pending follow-ups
4. Check for upcoming interviews needing prep
5. Write to /Users/terry/notes/Pipeline Scan - YYYY-MM-DD.md

Include:
- Pipeline health summary
- Stale items with suggested actions
- Follow-up recommendations prioritized
```

### Interview Prep Agent (if applicable)
```
Run /interview-prep for [Company]:
1. Research company deeply
2. Pull relevant stories from Core Story Bank
3. Match experience to role requirements
4. Write to /Users/terry/notes/Interview Prep - [Company] - YYYY-MM-DD.md
```

## Output

**Overnight Queue file** at `/Users/terry/notes/Overnight Queue - YYYY-MM-DD.md`:

```markdown
# Overnight Queue - YYYY-MM-DD

Queued at: HH:MM HKT

## Tasks

- [ ] Process job alerts → Job Alert Review - YYYY-MM-DD.md
- [ ] Scan pipeline → Pipeline Scan - YYYY-MM-DD.md
- [ ] Interview prep for [Company] → Interview Prep - [Company] - YYYY-MM-DD.md

## Morning Checklist

1. Check results files above
2. Review any CONSIDER roles from job alerts
3. Action stale follow-ups from pipeline scan
4. Review interview prep if applicable
```

## Integration with /morning

The `/morning` skill should check for overnight results:
1. Look for `Overnight Queue - YYYY-MM-DD.md` from previous night
2. Surface key findings from result files
3. Incorporate into morning briefing

## Examples

**User**: "going to bed"
**Action**: Check for upcoming interviews, confirm queue, launch background agents
**Output**: Confirmation of queued tasks, overnight summary file created

**User**: "/daily" (at end)
**Action**: After daily reflection, prompt "Want to queue overnight tasks?"
**Output**: If yes, run queue-overnight workflow
