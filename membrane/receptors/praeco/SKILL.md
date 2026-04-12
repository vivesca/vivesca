---
name: praeco
description: "Monitor HK financial regulatory circulars (HKMA + SFC + IA). Use when checking for new circulars, running praeco, or troubleshooting the regulatory monitor."
---

# praeco — HK Regulatory Circular Monitor

Rust CLI that polls HKMA, SFC, and IA for new circulars and press releases, and downloads PDFs automatically.

## Commands

```bash
praeco check          # Poll all sources now (also default with no subcommand)
praeco list           # Show items seen in last 7 days
praeco list --days 30 # Show last 30 days
praeco download <url> # Download a specific PDF by URL
```

## Sources
- **HKMA**: `https://api.hkma.gov.hk/public/press-releases?lang=en` (JSON API, no scraping)
- **SFC**: `https://www.sfc.hk/en/RSS-Feeds/Circulars` (RSS 2.0 feed)
- **IA**: `http://www.ia.org.hk/en/rss/rss_news_en.xml` (RSS "What's New" feed — covers circulars + press releases)
- **MPFA**: email-only (subscribed to Circulars category at terry.li.hm@gmail.com)

## State & Output
- Seen items: `~/.local/share/praeco/seen.json`
- Downloaded PDFs: `~/.local/share/praeco/pdfs/`

## LaunchAgent
Runs daily at 9am HKT via `com.terry.praeco` LaunchAgent.
Log: `~/logs/cron-praeco.log`

```bash
# Check log
tail -50 ~/logs/cron-praeco.log

# Reload after changes
launchctl unload ~/Library/LaunchAgents/com.terry.praeco.plist
launchctl load ~/Library/LaunchAgents/com.terry.praeco.plist
```

## Gotchas
- **BRDR SSL cert**: `brdr.hkma.gov.hk` has a self-signed cert — `danger_accept_invalid_certs(true)` is scoped to that host only
- **BRDR returns HTML for some docs**: non-PDF responses are silently skipped (Content-Type check). `-1-EN` docs often return HTML index page, not a PDF
- **BRDR probing is noisy**: scam alerts / bond tenders show "non-PDF" warnings because BRDR returns HTML for non-circular press releases — expected, not a bug
- **SFC refNo extraction**: parsed from URL query param `refNo=` (e.g. `26EC11`)
- **Workspace build**: binary lands at `~/code/target/release/praeco`, not `~/code/praeco/target/release/praeco`
- **IA has RSS**: `http://www.ia.org.hk/en/rss/rss_news_en.xml` — "What's New" feed, covered. MPFA is email-only (subscribed to Circulars).
- **Don't assume no feed**: checked IA in Mar 2026 — had RSS all along. Always verify before concluding "no feed available."

## Fallback: Playwright CSS Selectors (when RSS unavailable)

If a regulator page has no RSS and praeco can't reach it, fall back to Playwright scraping with these selectors:

```python
REGULATOR_CONFIGS = {
    "hkma": {
        "url": "https://www.hkma.gov.hk/eng/regulatory-resources/regulatory-guides/circulars/",
        "list_selector": "table tbody tr",
        "title_selector": "td:nth-child(1) a",
        "date_selector": "td:nth-child(2)",
    },
    "sfc": {
        "url": "https://apps.sfc.hk/edistributionWeb/gateway/EN/circular/",
        "list_selector": ".circulars-table tbody:nth-of-type(n+2) tr",
        "title_selector": "td:nth-child(2) a div",
        "date_selector": "td:nth-child(1)",
    },
}
```

Date formats seen: `%d %b %Y`, `%d/%m/%Y`, `%Y-%m-%d`. SFC is React SPA — needs `wait_for_load_state("networkidle")` + 10s buffer.

## Rebuild & Install
```bash
cd ~/code/praeco && cargo build --release
cp ~/code/target/release/praeco ~/bin/praeco
```

## Repo
`https://github.com/terry-li-hm/praeco` (private)
