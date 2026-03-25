---
name: review-saved-jobs
description: Review saved LinkedIn jobs systematically for fit assessment. "review saved jobs"
requires: browser-automation
platform_note: Requires browser automation with LinkedIn login. Works on Claude Code (Chrome MCP) and OpenClaw (browser tool).
user_invocable: true
---

# Review Saved Jobs

Systematically review LinkedIn saved jobs, quick-filter obvious passes, and run `/evaluate-job` for promising roles.

## Prerequisites

- Chrome browser automation (Claude in Chrome MCP)
- User logged into LinkedIn in Chrome

## Workflow

### 1. Open LinkedIn Saved Jobs

```
tabs_create_mcp → create new tab
navigate to https://www.linkedin.com/my-items/saved-jobs/
wait 2 seconds for page load
screenshot to see current list
```

### 2. Get Job List

Take screenshot and identify visible jobs. Note:
- Job title
- Company name
- Posted date (freshness)
- "Easy Apply" badge if present
- "Actively reviewing applicants" if shown

### 3. Load Context (parallel)

- Read `[[Job Hunting]]` for:
  - Applied Jobs list (avoid duplicates)
  - Passed On list (already evaluated)
  - Anti-Signals patterns
  - Pipeline health (active count)
- Read user's CLAUDE.md for background/criteria

### 4. Quick-Filter by Title

Before clicking into each role, quick-filter visible titles:

| Auto-PASS | Reason |
|-----------|--------|
| Manager (non-Senior) | Step down from AGM |
| Analyst | Step down |
| Engineer (without Lead/Principal) | IC role |
| Consultant (non-Senior) | Step down |
| Associate | Too junior |
| Intern/Graduate/Trainee | Way too junior |

| Auto-FLAG for Review | Reason |
|---------------------|--------|
| Director/VP/Head of | Potential step up |
| Senior Manager/Principal | Lateral |
| Chief/GM | Step up |
| Lead/Architect | Could be senior IC |

### 5. Process Each Promising Role

For roles that pass quick-filter:

1. **Click on job title** to open details panel
2. **Wait for load** (2 seconds)
3. **Get the job URL** from the browser tab
4. **Chain to `/evaluate-job`:**
   - Invoke the skill with the LinkedIn job URL
   - `/evaluate-job` handles: full JD extraction, fit analysis, vault note creation, Job Hunting updates
   - Wait for evaluation to complete before moving to next role
5. **Record outcome** in session tracking (APPLY/CONSIDER/PASS)

### 6. Track Progress

Use todo list to track progress through saved jobs:
```
- [ ] Role A - Company X
- [x] Role B - Company Y → PASS (too junior)
- [x] Role C - Company Z → APPLY (drafted email)
- [ ] Role D - Company W
```

### 7. Summary Output

After processing batch, output summary:

| Role | Company | Verdict | Action Taken |
|------|---------|---------|--------------|
| Senior Data Scientist | Fano Labs | CONSIDER | Created note |
| AI Engineer | Pinpoint Asia | PASS | Already have CV with recruiter |
| Data Governance Manager | BEA | PASS | Governance not AI |
| ... | ... | ... | ... |

**Stats:**
- Reviewed: X roles
- APPLY: Y
- CONSIDER: Z
- PASS: W

### 8. Handle APPLY Decisions

For APPLY recommendations:
- **Easy Apply:** Ask "Proceed with application now?"
- **External ATS:** Add to "To Apply" list with note

## Scrolling Through Long Lists

If saved jobs list is long:
1. Process visible jobs first
2. Scroll down: `scroll` action with `scroll_direction: down`
3. Take new screenshot
4. Continue processing new visible jobs
5. Repeat until reaching previously evaluated roles or end of list

## Quick Commands

| User Says | Action |
|-----------|--------|
| "next" | Move to next saved job |
| "skip" | PASS current without full evaluation |
| "apply" | Proceed with Easy Apply |
| "done" | Stop processing, output summary |

## Chaining with /evaluate-job

This skill **invokes `/evaluate-job`** for each promising role after quick-filtering:

1. Quick-filter identifies roles worth evaluating (by title, company, freshness)
2. For each promising role, extract the LinkedIn job URL
3. Call `/evaluate-job <url>` — this handles:
   - Full JD extraction
   - Fit analysis across all dimensions
   - Anti-signal checking
   - Vault note creation (mandatory)
   - Job Hunting tracking updates
4. Record the outcome and move to next role

**Division of labor:**
- `/review-saved-jobs` — Batch processing, quick-filtering, session tracking
- `/evaluate-job` — Deep evaluation of individual roles

## Related Skills

- `/evaluate-job` — Deep evaluation of single job posting
- `chrome-automation` — Reference for Chrome browser best practices
