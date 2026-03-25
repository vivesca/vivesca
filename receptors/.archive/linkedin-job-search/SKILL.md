---
name: linkedin-job-search
description: LinkedIn job search tips and strategies. Reference skill for optimizing job discovery.
user_invocable: false
---

# LinkedIn Job Search

Reference skill for effective LinkedIn job searching.

## Search Strategy

**Broad vs Specific:**
- **Broad keyword + location** (e.g., "AI" + Hong Kong) — Better for discovery. Catches non-standard titles like "Product Lead - AI", "Strategy Manager, AI", "Principal Engineer (ML)".
- **Specific title alerts** (e.g., "VP Data Science") — Better for passive monitoring. Notifies when exact-match roles post.

Use both: broad search for weekly manual scanning, specific alerts for notifications.

## Filtering for Sponsorship (Overseas)

When searching for roles that might sponsor visas:
- Add keywords: "relocation", "visa support", "visa sponsorship"
- Filter by company size (larger companies sponsor more often)
- Check job description for "must have right to work" (usually means no sponsorship) vs silence on visa (might sponsor)

## Applicant Stats Interpretation

LinkedIn shows applicant seniority breakdown. Notes:
- 50% entry-level doesn't mean the role IS junior — juniors spray-and-pray on everything
- Low VP/Director % suggests senior people don't see this as a fit
- Use as one signal among many, not definitive proof of seniority level

## Saved Jobs

Use LinkedIn's "Save" feature to batch jobs for later review. See `/review-saved-jobs` skill for systematic review workflow.

## Company Filter Caveat

**`f_C=` company filter works but is location-sensitive.**

Without explicit location, LinkedIn defaults to your profile/IP location. For overseas job searches from Hong Kong:

| Search | Location | Results |
|--------|----------|---------|
| `f_C=2775` + `AVP Financial Crime` | (default: HK) | **0** ❌ |
| `f_C=2775` + `AVP Financial Crime` | `Canada` | **1** ✅ |

**For overseas searches, ALWAYS specify location explicitly:**
```
f_C=2775&keywords=AI&location=Canada
```

**Keyword approach is still simpler:** `TD AI` + Canada works without needing the company ID.

| Approach | Pros | Cons |
|----------|------|------|
| Company filter (`f_C=`) | Guaranteed company match | Need company ID, location-sensitive |
| Keyword (`TD AI`) | Simple, no ID needed | May include other "TD"-named companies |

**Recommendation:** Use keyword approach (`Company AI` + location) for scanning. Use company filter for verification if needed.

## Seniority Filter Caveat

**`f_E=4` (Mid-Senior level) can miss relevant senior roles.**

Example: `RBC AI` + Toronto with Mid-Senior filter → **0 results**. Without filter → **454 results**, including:
- Senior Manager, AI Governance
- Sr. Director, Data Science
- Associate Director, Data Analytics & ML
- Lead Data Scientist, Fraud AI

**Why:** Companies classify levels differently. "Associate Director" or "Lead" may not map to LinkedIn's "Mid-Senior" category.

**Recommendation: Don't use seniority filter by default.**
1. Search **without** `f_E=4` to see full market
2. Scan titles manually for senior roles (Senior Manager, Director, VP, AVP)
3. Only add filter if results exceed 500+ and need narrowing

**URL parameter reference:**
- `f_E=4` = Mid-Senior level (unreliable)
- `f_TPR=r604800` = Posted in past week
- `sortBy=R` = Sort by relevance

## Best Search Pattern: Company + AI + City

| Target | Search | Location | Results (Feb 2026, no filter) |
|--------|--------|----------|------------------------------|
| Scotiabank AI roles | `Scotiabank AI` | Toronto | 486 |
| RBC AI roles | `RBC AI` | Toronto | 454 |
| TD Bank AI roles | `TD AI` | Toronto | 390 |
| BMO AI roles | `BMO AI` | Toronto | 272 |
| Barclays AI roles | `Barclays AI` | United Kingdom | 133 |
| CIBC AI roles | `CIBC AI` | Toronto | 111 |
| ASB AI roles | `ASB AI` | New Zealand | 63 |

This catches all AI-related roles at the company, then you scan the list for senior titles (AVP, VP, Director, Senior Manager, Head, Lead).

**Important:** Search WITHOUT seniority filter. RBC/BMO show 0 with filter, 400+ without.

## New Zealand Banks

| Bank | Search Keyword | Results | Notes |
|------|---------------|---------|-------|
| **ASB** | `ASB AI` | 63 | Best NZ bank — Head of Fraud, Chapter Lead roles |
| **Westpac NZ** | `Westpac New Zealand` | 41 | Full name required! `Westpac AI` returns 0 |
| ANZ | `ANZ` | 27 | Mostly BA/Data roles |
| BNZ | `BNZ Bank` | 0 | No results (LinkedIn redirects to ANZ) |

**Key insights:**
- **ASB Bank** (owned by Commonwealth Bank Australia) has the most senior AI roles in NZ
- **Westpac NZ** has 41 roles but requires full company name — `Westpac AI` returns 0
- **BNZ** genuinely has no roles posted

## Company Naming Caveats

**Short company names + "AI" can fail for some banks.**

### NZ Banks
`Westpac AI` + New Zealand → **0 results**. `Westpac New Zealand` → **41 results**.

### UK Banks
`Lloyds AI` + UK → **0 results**. `Lloyds Banking Group` → **304 results**.

**Pattern:** Use full company name for banks where short name + "AI" fails. Test both approaches.

| Bank | Fails | Works |
|------|-------|-------|
| Westpac NZ | `Westpac AI` | `Westpac New Zealand` |
| Lloyds UK | `Lloyds AI` | `Lloyds Banking Group` |
| HSBC UK | — | `HSBC AI` ✓ |
| Barclays UK | — | `Barclays AI` ✓ |

## Terry-Specific Search Patterns (Overseas)

Tested and working searches for roles matching Terry's background:

| Background | Search Keywords | Location | Example Result |
|------------|-----------------|----------|----------------|
| AML/Financial Crime | `AVP Financial Crime` | Toronto | TD Bank AVP role |
| AML/Financial Crime | `Financial Crime AI` | Toronto, London | - |
| AML/Financial Crime | `AML AI automation` | Toronto, London | - |
| Audit + AI | `Senior Audit Manager AI` | Toronto | CIBC Audit role |
| Audit + AI | `Audit Manager Data AI` | Toronto, London | - |
| Audit + AI | `AI Risk Audit` | Toronto, London | - |
| AI Governance | `AI Governance` | Toronto, Dublin, London | Gartner, Intact |
| AI Governance | `Responsible AI` | Toronto, London | - |
| AI Governance | `AI Risk` | Toronto, London | - |

## Target Companies (Canadian Big Five)

For banking AI roles in Canada, prioritize these employers:

| Bank | Alumni (CNCBI/HKUST) | AI Roles (no filter) | Best Finds |
|------|---------------------|----------------------|------------|
| Scotiabank | ? / 27 | 486 | Senior Manager AI & Ethics Governance |
| RBC | ? / 46 | 454 | Senior Manager AI Governance, Sr. Director Data Science |
| TD Bank | 12 / 31 | 390 | AVP Financial Crime AI, Senior Manager AI Vulnerability |
| BMO | ? / 26 | 272 | Senior Manager GenAI, VP AI Engineer |
| CIBC | 7 / 18 | 111 | Senior Audit Manager Data & AI Risk, Sr. AI Scientist |

**Note:** All counts are WITHOUT seniority filter. With `f_E=4` filter, RBC and BMO show 0.

**Priority for Terry:** TD (AVP Financial Crime) > Scotiabank (AI Governance) > RBC (AI Governance) > BMO (GenAI) > CIBC (Audit)

## Browser Automation: Scrolling & Pagination

**When scanning results via Claude in Chrome or agent-browser:**

1. **Scroll the job list panel, not the whole page** — LinkedIn uses a left sidebar for job listings. Scroll within that panel to load more results.

2. **Pagination is unreliable in automation** — Clicking page numbers (1, 2, 3...) often fails silently. Instead:
   - Scroll down repeatedly (5-10 scroll ticks) to load more results
   - Each scroll loads ~7-10 more jobs
   - Scroll 3-5 times to see 25-50 jobs

3. **Senior AI roles are sparse** — In a search like "TD AI" (1,544 results), most are:
   - IC ML Scientist positions (not leadership)
   - Analytics roles (not AI)
   - Wrong domain (Quant, Digitization, etc.)
   - AVP/VP + AI + specific domain = rare (maybe 1-3 per company)

4. **Scan strategy for senior AI roles:**
   - Scroll through first 25-50 results
   - Look for keywords: AVP, VP, Director, Senior Manager + AI/ML/GenAI
   - Skip: Analyst, Scientist, Engineer (IC roles)
   - Skip: Analytics, Quant, Data (not AI-specific)

## Weekly Monitoring Routine (Overseas)

1. Run each domain keyword search once/week
2. Filter by "Past week" (Date posted → Past week, or `f_TPR=r604800` in URL)
3. Save promising roles to LinkedIn "Saved Jobs"
4. Cross-check alumni count (CNCBI/HKUST) for referral potential
5. For strong matches, create vault note with fit analysis
