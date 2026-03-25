---
title: "Google Takeout Download Automation via AppleScript Chrome Control"
description: |
  Automating 98-part Google Takeout downloads (~50GB each) by controlling Chrome via AppleScript.
  Solves HTTP 500 errors (missing Referer), stale URLs (missing rapt tokens), slow auth detection,
  orphaned downloads, and rate limit tracking.
category: browser-automation
tags:
  - google-takeout
  - chrome-automation
  - applescript
  - referrer-header
  - session-tokens
  - photoferry
  - rust
date_resolved: 2026-02-24
project: photoferry
files:
  - src/downloader.rs
  - src/main.rs
related:
  - browser-automation/kindle-cloud-reader-automation.md
  - chrome-cookie-decryption-rusqlite-fix.md
  - runtime-errors/chrome-download-stall-recovery.md
  - photoferry-reference.md
---

## Problem

photoferry downloads Google Takeout ZIP archives (~50GB × 98 parts). Three layers of failure:

1. **HTTP 500**: Constructed URLs opened directly in Chrome lack Referer header → Google rejects
2. **Stale URLs**: Constructed URLs miss `rapt` session tokens that the Takeout UI injects
3. **Slow feedback**: 60-second blind wait before detecting auth is needed

## Root Cause

Google Takeout validates download requests against referrer context and session-specific `rapt` tokens. The Takeout SPA generates download links with these parameters at render time. Constructing URLs from `job_id + user_id + part_number` skips both protections.

Additionally, the job ID we were using was truncated (`65a591a2-167351b8dc4a` vs full `65a591a2-7f11-483f-9e04-d952f087a07f`).

## Solution: AppleScript Chrome Control

### 1. Referrer-based navigation

Navigate to `takeout.google.com` first, then JS-redirect. Chrome sends proper Referer automatically:

```rust
fn chrome_open_with_referrer(url: &str) -> Result<()> {
    Command::new("open")
        .args(["-a", "Google Chrome", "https://takeout.google.com/"])
        .spawn()?;
    chrome_wait_for_load();
    chrome_exec_js(&format!("window.location.href='{}'", url));
    Ok(())
}
```

### 2. Scrape fresh URLs with rapt tokens

Extract all download links from the Takeout manage page via JS injection:

```rust
pub fn scrape_takeout_urls() -> HashMap<usize, String> {
    chrome_navigate("https://takeout.google.com/settings/takeout/downloads");
    let js = r#"(function(){
        var links = Array.from(document.querySelectorAll('a'))
            .filter(l => l.href.indexOf('download') > -1);
        document.title = 'PFURLS:' + links.map(l => l.href).join('|||');
    })()"#;
    chrome_exec_js(js);
    // Read back from title via AppleScript
}
```

Or use `--urls-file` with pre-scraped URLs (one per line).

**Batch extraction trick**: AppleScript `execute javascript` returns synchronous results only. For large data, encode into `document.title` and read back, or use the `return` value from JS in 20-URL batches.

### 3. Instant auth detection

Poll Chrome's URL instead of waiting 60 seconds:

```rust
fn chrome_is_on_auth_page() -> bool {
    chrome_active_url()
        .map(|u| u.contains("accounts.google.com") || u.contains("signin"))
        .unwrap_or(false)
}
```

### 4. Page-load polling (replaces sleep(3))

```rust
fn chrome_wait_for_load() {
    let script = r#"tell application "Google Chrome"
        repeat 30 times
            if loading of active tab of first window is false then return "done"
            delay 0.5
        end repeat
    end tell"#;
    Command::new("osascript").args(["-e", script]).output();
}
```

## Additional Hardening

### Download attempt tracking

Google allows max 5 downloads per part per export. Track in persistent JSON:

```rust
pub fn record_attempt(&mut self, i: usize, dir: &Path) -> usize { ... }
pub fn attempts_remaining(&self, i: usize) -> usize {
    5usize.saturating_sub(*self.attempts.get(&i).unwrap_or(&0))
}
```

### Orphaned download recovery

On restart, check for existing `.crdownload` files and attach instead of opening new Chrome tabs.

### Cookie refresh

Re-extract cookies after every successful download (not just first Chrome fallback) to maximize the HTTP-first window.

## Prevention Rules

| Rule | Why |
|------|-----|
| Never construct Google download URLs | They lack rapt tokens and may have truncated IDs |
| Always navigate via referrer for Google services | Direct URLs get 500/403 without Referer |
| Never use fixed sleep for state detection | Poll browser properties via AppleScript instead |
| Track external service rate limits persistently | Google's 5-attempt limit survives process restarts |
| Snapshot .crdownload before opening Chrome | Prevents duplicate downloads on restart |
| Never retry on HTTP 500 from Google | It means the URL/job is invalid, not a transient error |

## AppleScript Chrome API Reference (macOS)

Requires: Chrome → View → Developer → Allow JavaScript from Apple Events

```applescript
-- Get URL (no JS permission needed)
tell application "Google Chrome" to return URL of active tab of first window

-- Get title
tell application "Google Chrome" to return title of active tab of first window

-- Check loading state
tell application "Google Chrome" to return loading of active tab of first window

-- Navigate
tell application "Google Chrome" to set URL of active tab of first window to "https://..."

-- Execute JS (needs permission toggle)
tell application "Google Chrome" to execute active tab of front window javascript "..."
```

## Key Commits

- `ed2bc11` — Fix 500 errors via referrer navigation
- `9ae2530` — Chrome automation: instant auth, URL scraping, load polling
- `07d1476` — `--urls-file` flag for pre-scraped URLs
- `f0f28ad` — Attempt tracking, crdownload attach, cookie refresh
- `e830f31` — Cookie refresh after every download

## Cross-References

- [photoferry-reference.md](../photoferry-reference.md) — Project reference
- [chrome-cookie-decryption-rusqlite-fix.md](../chrome-cookie-decryption-rusqlite-fix.md) — Cookie extraction gotchas
- [chrome-download-stall-recovery.md](../runtime-errors/chrome-download-stall-recovery.md) — Stall detection patterns
