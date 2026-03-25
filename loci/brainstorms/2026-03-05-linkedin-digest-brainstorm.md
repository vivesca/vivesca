# theoros — LinkedIn Daily Digest Brainstorm

**Date:** 2026-03-05
**Status:** Ready for planning

## What We're Building

A daily automated LinkedIn feed digest. **`theoros`** — a Rust CLI — scrapes the top 10 posts from the LinkedIn feed via `agent-browser`, calls the Claude API to filter and summarise for relevance, and writes a structured vault note to `~/epigenome/chromatin/LinkedIn/`. A LaunchAgent runs this at 8am daily. A skill wraps the script for manual invocation.

## Why This Approach

LinkedIn has no feed API and no email digest for network activity. Without active scrolling, relevant posts (job leads, network updates, industry news) go unseen. The digest solves this passively — vault-first means it integrates with existing morning brief skills (`auspex`, `statio`, `kairos`) without adding a new delivery channel.

Approach chosen: **Rust CLI (`theoros`) + LaunchAgent + skill wrapper**, matching the existing Lustro pattern. Failure is silent (skips the day) and doesn't affect other routines.

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Delivery | Vault only | Morning routine skills already read vault; no extra noise |
| Vault path | `~/epigenome/chromatin/LinkedIn/YYYY-MM-DD LinkedIn Digest.md` | Grouped, searchable |
| Scroll depth | Top 10 posts | Fast, low token cost, sufficient for daily cadence |
| Run time | 8am daily | Before morning brief; fresh when statio/auspex run |
| Filter priorities | Job leads, industry news (AML/fintech/AI), Capco-related | Current phase: job hunt + Capco onboarding |
| Name | `theoros` | Greek: official envoy sent to observe and report back. Available on crates.io. |
| Script location | `~/bin/theoros` (symlink to release binary) | Consistent with other bin scripts |
| LaunchAgent | `com.terry.theoros` | Matches existing naming convention |

## Filtering Prompt Context

Claude should know Terry's current context:
- AGM & Head of Data Science at CNCBI → joining Capco as Principal Consultant, AI Solution Lead
- Domain focus: AML/financial crime, AI in financial services, HK fintech market
- Job hunt active until Capco start date
- Key signal types: job postings (especially DS/AI/AML roles in HK), regulatory news (HKMA, SFC), Capco mentions, posts from known contacts

## Vault Note Structure

```markdown
# LinkedIn Digest — 2026-03-05

*Scraped: 10 posts · Filtered: N relevant · Run: 08:03*

## Job Leads
- ...

## Industry News
- ...

## Capco / Network
- ...

## Skipped
N posts filtered out (promotional, low relevance)
```

## Open Questions

None — all resolved in brainstorm session.

## Resolved Questions

- **Delivery channel:** Vault-only (no email/Telegram push)
- **Scroll depth:** Top 10 posts
- **Vault location:** `~/epigenome/chromatin/LinkedIn/`
- **Filter priorities:** Job leads, industry news, Capco-related
