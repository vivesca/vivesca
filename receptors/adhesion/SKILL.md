---
name: adhesion
description: Evaluate LinkedIn job postings for fit. Triggers on job URLs or "evaluate this role".
requires: browser-automation
user_invocable: true
---

# Evaluate Job

Analyze LinkedIn job postings against user's background, current pipeline health, and career criteria. Output a recommendation (APPLY/CONSIDER/PASS) with structured reasoning.

## Workflow

1. **Navigate to job posting — HARD GATE: actual JD required before proceeding:**
   - **Primary:** `WebFetch` — fast, works for most JD content
   - **Fallback:** `agent-browser` for logged-in view (applicant stats, seniority breakdown, salary source attribution)
   - Extract: company name, role title, requirements, responsibilities, preferred qualifications, salary if disclosed, applicant stats

   **CRITICAL: Never use search engine result summaries as JD source.** Google/Bing summaries can describe a *different role at the same company* — same employer, similar title, completely different function and requirements. This has happened (Hang Seng "Head of AI and Data Applications" summary was used for what turned out to be "Head of AI Adoption" — IT PM role, not data science). If the source URL is 404/403, try agent-browser before writing any note. If genuinely unreachable, say so explicitly and do not infer JD from search summaries.

   **WebFetch limitations on LinkedIn:**
   - Misses **applicant stats** (count, seniority breakdown) — requires being logged in
   - Cannot distinguish LinkedIn's estimated salary range from employer-disclosed salary. Mark any salary as `(LinkedIn estimate — not employer-disclosed)` unless the JD text explicitly states the range
   - If applicant stats or salary attribution matter, use agent-browser.

   **LinkedIn agent-browser pattern (Mar 2026):**
   - `wait --load networkidle` times out — use `wait 4000` (fixed ms)
   - Notification onboarding loop: `agent-browser close` → `porta inject --browser chrome --domain linkedin.com` → `agent-browser open <url>` → `agent-browser wait 4000` → `agent-browser snapshot`

2. **Check for duplicates and same-employer saturation** (before full analysis):
   - Search vault for existing note matching company + role (e.g., `[[*Role* - *Company*]]`)
   - Check [[Job Hunting]] "Applied Jobs" and "Passed On" sections for the company name
   - If match found:
     - Show user what was found (existing note, application status, date)
     - Ask: "Already evaluated/applied to [match]. Proceed with analysis anyway?"
     - If user says no, stop early — no further analysis needed
   - **Same-employer batch detection:** If 3+ roles at the same company have been evaluated (in vault or current session), flag it: "Multiple roles at [Company] — consider picking your strongest match rather than scatter-applying across the same division." This prevents diluted applications and signals desperation to recruiters who may see multiple apps.

3. **Load context files** (can run in parallel with step 1) — Check user's CLAUDE.md for background, credentials, differentiators, current situation, and job hunting status

4. **Analyze fit** across dimensions (see Fit Dimensions below). see [[mental-models]] — check for barbell strategy, specific knowledge, compounding, opportunity cost before weighting dimensions. **North star filter:** Does this role move toward "real AI problems + sharp people who build"? Surface `memory/user_career_north_star.md` and weigh against the 70/30 technical/people split.

5. **Factor pipeline health:**
   - **Healthy** (5+ active, interviews scheduled): Maintain standards — PASS on poor fits
   - **Thin** (<5 active, no interviews): Lower bar — CONSIDER "good enough" roles
   - Consider urgency of user's situation when weighing trade-offs
   - **Offer-signed hard filter:** When an offer is already signed, apply stricter competition thresholds — especially for roles requiring relocation. ~90+ applicants on a relocation role = auto-PASS regardless of credential match. The ROI of competing against 100 people when starting a new job in weeks is near zero.

6. **Check for red flags** (feedback loop from `/debrief`):
   - Review [[Job Hunting]] → Market Signals for relevant patterns:
     - **Objections:** What got pushback in similar roles?
     - **Wins:** What hooks landed that this role could use?
     - **Persona Mismatches:** Did similar roles expect different positioning?
   - Review [[Job Hunting]] → Anti-Signals for known rejection patterns
   - If role matches a pattern, flag it in analysis and factor into recommendation

7. **Output recommendation:** APPLY, CONSIDER, or PASS with clear reasoning
   - **Warm lead check:** If a warm lead exists at this company (check [[Job Hunting - Pipeline Archive]] → Warm Leads), do NOT suggest forwarding the job posting to the contact. That's transactional and undermines organic positioning. Instead, note the posting as **intel** (confirms the company is actively hiring for this type of role) — useful context for when the organic introduction happens, not a conversation starter.

8. **Review with Judge:**
   - Run evaluation through `/judge` with `job-eval` criteria
   - Check: fit_analysis, red_flags, specificity, recommendation, career_direction
   - If verdict is `needs_work`: revise analysis (max 2 iterations)
   - Ensures recommendation is specific and actionable, not vague

9. **Create vault note — MANDATORY for ALL outcomes:**
   - **Do this immediately after giving recommendation — don't wait for user to ask**
   - Filename: `[[Role Title - Company]]`
   - **MUST include full JD details:** Copy requirements, responsibilities, qualifications verbatim from the posting
   - Include: Fit analysis table, recommendation reasoning
   - This creates a record for future reference, pattern recognition, and duplicate detection

10. **Update job tracking:**
    - **APPLY:** Add to "Applied Jobs" or "To Apply" section in [[Job Hunting]]
    - **PASS:** Add to "Passed On" section with one-line reason
    - **CONSIDER:** Note in appropriate section with context

11. **If APPLY:**
    - **Easy Apply roles:** Ask whether to proceed with application now
    - **Company website roles:** Offer to help via `agent-browser --profile` (persistent login). For form filling, always check `~/code/epigenome/chromatin/Personal Details for Applications.md` for correct name (李浩銘), address, and personal details. Note: Workday portals block Playwright actions on later form steps — use automation for login/upload/early steps, expect manual completion for dropdowns and submission.

## Fit Dimensions

| Dimension | Considerations |
|-----------|----------------|
| **Seniority** | Step up, lateral, or step down from current level? |
| **Role Focus** | Matches core skills (AI/ML, DS, etc.) or pivot (BI, PM, DE)? |
| **Industry** | Strategic value? Transferable credibility? |
| **Tech Stack** | Alignment with user's technical strengths? |
| **Competition** | Applicant count, seniority distribution, education levels |
| **Salary** | Compare to current compensation if known. For foreign currencies, **always use Python** for FX conversion — never mental math. Flag LinkedIn estimates vs employer-disclosed. |
| **Anti-Signal** | Does this match a known rejection pattern? |
| **Evidence vs persuasion** | Does the role reward proving things work, or selling/performing confidence? Surgeon end or salesman end? |
| **Meta vs execution** | Designing frameworks and methodology, or building to someone else's spec? |
| **Shapeability** | Can Terry steer the role toward his strengths, or is scope rigid? |
| **Conviction alignment** | Will he believe in what he's asked to advocate? (See `memory/user_why_ai.md`) |

## Note Template

```markdown
# [Role Title], [Company]

**Source:** [LinkedIn URL]
**Discovered:** [Date]
**Status:** [Applied/Passed/Considering]

## Job Details

**Title:**
**Company:**
**Location:**
**Salary:** [if disclosed — mark "(LinkedIn estimate)" vs "(employer-disclosed)"]
**Applicants:** [count] ([seniority breakdown])

## Requirements

[COPY FULL REQUIREMENTS FROM JD - verbatim bullet points]

## Responsibilities

[COPY FULL RESPONSIBILITIES FROM JD - verbatim bullet points]

## Preferred/Nice-to-Have

[If listed separately in JD]

## Fit Analysis

| Dimension | Assessment | Notes |
|-----------|------------|-------|
| Seniority | ✅/⚠️/❌ | |
| Role Focus | ✅/⚠️/❌ | |
| Industry | ✅/⚠️/❌ | |
| Tech Stack | ✅/⚠️/❌ | |
| Competition | ✅/⚠️/❌ | |
| Salary | ✅/⚠️/❌ | |
| Anti-Signal | ✅/⚠️/❌ | |

## Recommendation

**[APPLY/CONSIDER/PASS]**

[Reasoning]
```

## Passed On Format

```
- [[Role Title - Company]] (Date) - [One-line reason]
```

## Batch Processing

For multiple jobs, run this skill sequentially on each URL. Start with quick duplicate check before full analysis.

## Related Skills

- `browser-automation` — agent-browser best practices (persistent profile, headed mode for captchas)
- `/phagocytosis` — Routes LinkedIn job URLs to this skill automatically
