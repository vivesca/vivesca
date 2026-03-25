---
module: LinkedIn Integration
date: 2026-02-06
problem_type: integration_issue
component: api
symptoms:
  - "LinkedIn Voyager API returns 302 redirect loop"
  - "Response includes set-cookie: li_at=delete me with 1970 expiry"
  - "Response includes clear-site-data header"
  - "Valid browser cookies rejected when sent via requests library"
  - "Testing with real cookies invalidates the Chrome session too"
root_cause: tool_limitation
resolution_type: tool_switch
severity: medium
tags: [linkedin, api, browser-automation, anti-bot, cookie-auth, openclaw-skills]
related_files:
  - ~/code/vivesca-terry/chromatin/Awesome OpenClaw Skills - Evaluation.md
  - ~/skills/linkedin-cli/ (removed)
---

# LinkedIn Cookie-Based API Access Is Dead

## Problem

Attempted to use the `linkedin-api` Python library (powering OpenClaw's popular `linkedin-cli` skill) to access LinkedIn data via CLI instead of fragile browser automation.

The library authenticates by injecting `li_at` and `JSESSIONID` cookies from a real browser session into Python `requests`. This approach worked historically but is now actively blocked by LinkedIn.

## Investigation

### What was tried

1. Extracted valid `li_at` and `JSESSIONID` cookies from Chrome DevTools
2. Verified cookies were valid (Chrome session was active, feed loaded)
3. Tested with multiple cookie domain configurations:
   - `.www.linkedin.com` (original skill code)
   - `.linkedin.com`
   - `www.linkedin.com`
4. Tested with raw `curl` (not just Python) — same result
5. Added proper User-Agent header — still rejected

### What happened

Every request to `https://www.linkedin.com/voyager/api/me` returned:

```
HTTP/2 302
location: https://www.linkedin.com/voyager/api/me  (redirect to self = loop)
set-cookie: li_at=delete me; Expires=Thu, 01-Jan-1970 00:00:00 GMT
clear-site-data: "storage"
```

LinkedIn:
1. Detected the request came from a non-browser client
2. Actively invalidated the session cookie (`li_at=delete me`)
3. Issued `clear-site-data` to wipe stored credentials
4. Returned a redirect loop (302 → same URL)

### Collateral damage

Testing with the real Chrome session cookie **invalidated it** — had to re-login to LinkedIn in the browser.

## Root Cause

LinkedIn's Voyager API now fingerprints TLS ClientHello patterns, header ordering, and other signals that distinguish real browsers from HTTP libraries like Python `requests` or `curl`. When a non-browser client is detected, LinkedIn doesn't just reject the request — it actively destroys the session.

This is a deliberate anti-bot measure that makes all `linkedin-api`-based tools non-functional, regardless of cookie validity.

## Resolution

**Browser automation remains the only reliable path for LinkedIn.**

Priority chain (from CLAUDE.md):
1. `agent-browser` (text-based, lightweight)
2. Claude in Chrome (extension-based)
3. Playwright MCP (full browser engine)

These work because they use actual browser engines with real TLS stacks and browser fingerprints.

## Prevention

1. **Never test LinkedIn API tools with real session cookies** — they'll get invalidated
2. **Don't adopt OpenClaw skills that use `linkedin-api`** — the library is fundamentally broken for cookie auth
3. **For any service with anti-bot detection** (LinkedIn, Twitter/X, etc.), only browser automation survives

## Broader Pattern

This applies to any platform with sophisticated bot detection:
- **LinkedIn** — Voyager API cookie injection dead
- **X/Twitter** — Web scraping returns login walls (already known)
- **Instagram** — Similar anti-bot measures

The pattern: if a platform has invested in bot detection, cookie injection from HTTP libraries won't work. Browser automation (with real browser engines) is the floor, not the ceiling.

## Context

Discovered while evaluating [awesome-openclaw-skills](https://github.com/VoltAgent/awesome-openclaw-skills) (9.8k stars, 1,715+ skills). The `linkedin-cli` skill was the #1 recommended candidate but failed on first test.
