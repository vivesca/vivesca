---
name: process-job-alerts
description: Process LinkedIn job alert emails from Gmail, filter against existing applications, and identify roles worth applying to. Triggers on "check job alerts", "process job emails", "any new jobs", or requests to review LinkedIn alert emails.
---

# Process Job Alerts

Batch process LinkedIn job alert emails from Gmail. Quick-filter against existing pipeline, fetch JD details for promising roles, and identify which ones deserve full evaluation.

## Workflow

1. **Fetch recent job alert emails:**
   ```
   mcp__gmail__search_emails
   - from_email: jobalerts-noreply@linkedin.com
   - max_results: 5
   - is_unread: true (optional, to focus on new alerts)
   ```

2. **Get email content:**
   ```
   mcp__gmail__get_emails with message_ids
   ```

3. **Extract job URLs from email:**
   - Parse LinkedIn job URLs (format: `linkedin.com/comm/jobs/view/[ID]`)
   - Clean tracking parameters, get base job IDs

4. **Load context** (parallel with above):
   - Read `[[Job Hunting]]` for Applied Jobs and Passed On lists
   - Note pipeline health (active count, scheduled interviews)

5. **Quick-filter by title:**
   - Match job titles against existing Applied/Passed lists
   - Skip roles already evaluated
   - Flag obvious mismatches (junior titles, wrong domain, relocation required)

6. **Fetch JD details for remaining roles:**
   - **Chrome available:** `tabs_create_mcp` → `navigate` → `get_page_text` for each
   - **Chrome unavailable:** `tavily-extract` with `extract_depth: advanced`
   - Extract: title, company, requirements, responsibilities, seniority level, applicant stats

7. **Rapid assessment for each role:**

   | Check | PASS if... |
   |-------|------------|
   | Title | Step down from AGM (Manager, Analyst, Associate, Engineer IC) |
   | Domain | Requires experience user lacks (crypto, CV, C++, quant trading) |
   | Location | Requires relocation (Bangkok, Singapore, etc.) |
   | Seniority | LinkedIn marks as "Entry level" |
   | Prior rejection | Already rejected by this company recently |
   | Language | Requires language user doesn't speak |

8. **Output summary table:**

   | Role | Company | Verdict | Reason |
   |------|---------|---------|--------|
   | Head of Analytics | Binance | PASS | Crypto exp required; prior rejection |
   | Senior Data Analyst | Reap | PASS | IC role, step down from AGM |
   | ... | ... | ... | ... |

9. **For APPLY/CONSIDER roles:**
   - Offer to run `/evaluate-job` for deeper analysis
   - Or proceed with Easy Apply if straightforward fit

10. **Update notes:**
    - Add PASS roles to Passed On list in `[[Job Hunting]]` with date and reason
    - Mark email as read (optional)

## Quick Reference: Title Hierarchy

For Terry's current level (AGM / Head of Data Science):

| Verdict | Titles |
|---------|--------|
| Step up | GM, Director, VP, Head of, Chief |
| Lateral | AGM, Senior Manager (large org), Principal |
| Step down | Manager, Senior Analyst, Analyst, Engineer, Consultant |

## Integration with /evaluate-job

For roles that pass initial filter and look promising:
- Invoke `/evaluate-job` skill with the LinkedIn URL
- That skill handles deep-dive analysis, vault note creation, and application tracking

## Example Usage

**User:** "Check my job alert emails"

**Claude:**
1. Fetches recent LinkedIn job alerts from Gmail
2. Extracts 6 job URLs
3. Quick-filters: 2 already in Passed list, 1 requires Bangkok relocation
4. Fetches JDs for remaining 3
5. Assesses: 2 are IC roles (PASS), 1 is Director level at fintech (CONSIDER)
6. Outputs summary table
7. Offers: "The Director role at [Company] looks interesting. Want me to run /evaluate-job for a deeper analysis?"
