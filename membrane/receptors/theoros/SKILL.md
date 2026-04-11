---
name: theoros
description: LinkedIn daily feed digest. Run manually or check today's digest. Use when asking about recent LinkedIn activity, job leads, or network updates.
triggers:
  - theoros
  - linkedin
  - feed digest
  - linkedin jobs
  - job leads
  - network updates
---

# theoros — LinkedIn Feed Digest

Scrapes LinkedIn feed via agent-browser, filters with Claude, writes daily vault note.

## Commands

```bash
theoros run          # full pipeline: scrape → dedup → filter → write vault note
theoros fetch        # scrape feed and print raw posts (debug)
theoros fetch -l 5   # limit to 5 posts
theoros view         # print today's digest to stdout
theoros status       # show today/yesterday note status + agent-browser liveness
theoros jobs         # scrape LinkedIn Jobs for DS/AI/AML/fintech HK roles (last 24h)
theoros --version
```

## Vault Output

Feed digest: `~/epigenome/chromatin/LinkedIn/YYYY-MM-DD LinkedIn Digest.md`
Jobs note: `~/epigenome/chromatin/LinkedIn/YYYY-MM-DD LinkedIn Jobs.md`

Today's digest:
```bash
theoros view
# or:
cat ~/epigenome/chromatin/LinkedIn/$(date +%Y-%m-%d)\ LinkedIn\ Digest.md
```

## Schedule

LaunchAgent: `com.terry.theoros` fires at 8am daily.
Log: `~/logs/cron-theoros.log`

## Filter Context

Claude filters for: job leads (DS/AI/AML in HK), industry news (fintech/AML/HKMA), Capco-related posts.

## Deduplication

- **Intra-day:** vault dedup — if today's note >100 bytes already exists, `run` skips writing.
- **Cross-day:** seen-hash store at `~/.local/share/theoros/seen.json` — posts fingerprinted by first 200 chars, 7-day rolling window. Fresh runs skip already-seen posts.
- **Freshness filter:** posts with age >24h (1d, 2d, 1w…) are silently skipped during scrape.

## Gotchas

- agent-browser must be running and LinkedIn session must be active. If session expired, scrape returns login page content (no "Feed post number" markers → 0 posts → empty digest).
- ANTHROPIC_API_KEY must be set in LaunchAgent plist EnvironmentVariables.
- Each agent-browser call is sequential — never parallel.
- Binary: `~/.cargo/bin/theoros`, symlinked to `~/bin/theoros`.
- After `cargo install --path .`, bin updates automatically on reinstall.
- `theoros jobs` makes live browser calls — do not run as a dry-test.
