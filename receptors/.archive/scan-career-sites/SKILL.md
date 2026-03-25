---
name: scan-career-sites
description: This skill scans company career sites for AI/Data Science roles that don't appear on LinkedIn. Focus on statutory bodies and government-adjacent orgs that bypass LinkedIn.
---

# Scan Career Sites

Scan career sites that **don't post on LinkedIn** (or post inconsistently). These are the gaps LinkedIn alerts miss.

## Core List (Scan Weekly)

These organisations use their own portals and often don't appear on LinkedIn:

| Company | Career URL | Keywords |
|---------|-----------|----------|
| Cyberport | https://www.cyberport.hk/en/news/career_opportunities/ | AI, Data Science, Manager |
| HKSTP | https://careers.hkstp.org/go/LATEST-JOB/7846910/ | AI, Data Science, Innovation |
| HKMA | https://www.hkma.gov.hk/eng/about-us/join-us/current-vacancies/ | AI, Data, Fintech |
| WKCDA | https://wd3.myworkdaysite.com/recruiting/wkcda/External | Data, AI, Architecture |
| SFC | https://www.sfc.hk/en/Career/Why-the-SFC/Join-us-as-an-experienced-professional/Current-Openings | Technology, Data, Fintech |
| HKJC | https://careers.hkjc.com/ | Data, AI, Technology |
| Hospital Authority | https://www.ha.org.hk/visitor/ha_visitor_index.asp?Content_ID=2010 | AI, Health Informatics |
| MTR | https://www.mtr.com.hk/en/corporate/careers/career_opportunities.html | AI, Data Science, Digitalisation |
| Airport Authority HK | https://www.hongkongairport.com/en/airport-authority/careers/ | AI, Innovation, Data |

## How to Scan

1. **Use browser automation** to visit each career site
2. **Search/filter** for AI, Data Science, Machine Learning keywords
3. **Check posting dates** — prioritize recent postings
4. **Compare against Job Hunting.md** — skip already-applied roles
5. **Report new findings** with quick fit assessment

## Quick Fit Criteria

**Strong Fit:**
- Senior Manager / Director / Head / VP level
- AI/ML/GenAI focus (not just BI/analytics)
- Hong Kong based
- Leadership role (not IC)

**Pass:**
- Manager or below (step down from AGM)
- Pure data engineering / architecture (not ML)
- Master's/PhD required
- Heavy quant/trading focus

## Output Format

```
### [Company] - [Role Title]
- **URL:** [direct link]
- **Posted:** [date if visible]
- **Fit:** HIGH / MEDIUM / LOW / PASS
- **Notes:** [1-2 sentence assessment]
- **Action:** Apply / Skip / Research more
```

## When to Run

- Weekly during active job search
- After hearing about company hiring news
- Before networking calls (check if target company is hiring)

## Check When Relevant (Not Regular Scanning)

These post on LinkedIn but worth checking their site before a networking call or when you hear hiring news:

- Banks: DBS, StanChart, HSBC, Hang Seng, BOC HK, HKEX
- Insurance: Manulife, AIA, AXA, Prudential
- Virtual Banks: ZA Bank, Mox, WeLab
- Property: Swire, Link REIT, Cathay Pacific
