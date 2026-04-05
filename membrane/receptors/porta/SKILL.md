---
name: porta
description: Bridge browser cookies into agent-browser profile (solves Google OAuth block). Use when agent-browser needs authenticated session. "porta inject", "chrome cookies", "browser login"
triggers:
  - porta inject
  - porta watch
  - agent-browser google oauth
  - chrome cookies playwright
  - firefox cookies playwright
---

# porta

Bridges browser cookies into the agent-browser Playwright persistent profile.
Solves the Google OAuth block (agent-browser can't authenticate via Google SSO).
Supports Chrome (multi-profile), Firefox, and Arc. Has a watch mode for long-running sessions.

## Workflow

```
# 1. Log in to the target site in your browser (Chrome/Firefox — normal, not headless)
open -a "Google Chrome" "https://site.com/login"
# → user logs in manually

# 2. Bridge cookies to agent-browser profile
porta inject --domain site.com

# 3. Verify headless access works
agent-browser open "https://site.com/dashboard"
agent-browser get url  # should NOT redirect to login

# 4. For long-running tasks: keep cookies fresh automatically
porta watch --domain site.com --interval 300
```

## Commands

```bash
# --- Inject ---
porta inject --domain vercel.com                    # Chrome Default profile
porta inject --domain vercel.com --dry-run          # see what would be injected
porta inject --browser firefox --domain google.com  # Firefox
porta inject --browser arc --domain linear.app      # Arc
porta inject --chrome-profile "Profile 1" --domain site.com  # Chrome non-default profile

# --- List ---
porta list --domain vercel.com                      # Chrome Default
porta list --browser firefox --domain google.com    # Firefox
porta list --browser arc --domain site.com          # Arc
porta list --chrome-profile "Profile 1" --domain site.com

# --- Watch mode ---
# Re-injects automatically when auth cookies near expiry (default: every 5 min)
porta watch --domain vercel.com
porta watch --browser firefox --domain site.com --interval 120
# Ctrl+C to stop

# --- All cookies (no domain filter) ---
porta inject
```

## Browser paths (auto-detected)

| Browser | Cookies DB | Keychain service |
|---------|-----------|-----------------|
| Chrome Default | `~/Library/Application Support/Google/Chrome/Default/Cookies` | `Chrome Safe Storage` |
| Chrome Profile N | `~/Library/Application Support/Google/Chrome/<profile>/Cookies` | `Chrome Safe Storage` |
| Arc | `~/Library/Application Support/Arc/User Data/Default/Cookies` | `Arc Safe Storage` |
| Firefox | `~/Library/Application Support/Firefox/Profiles/*.default-release/cookies.sqlite` | plaintext, no decrypt |

## Watch mode — when to use

Watch re-injects when:
- No auth cookies are found (count = 0), OR
- Any auth cookie expires within `2 × interval` seconds

Auth cookies detected by name containing: `session`, `auth`, `token`, `login`, `sid`, `credential`, `psid`, `sapisid` (covers Google `1PSID`/`SAPISID`).

Typical use: leave running during a long agentic task that hits authenticated endpoints.

## How it works

1. Copies browser's Cookies SQLite DB to `/tmp` (avoids lock contention)
2. Chrome/Arc: decrypts values via `AES-128-CBC` + PBKDF2 key from macOS Keychain; strips 32-byte SHA256 prefix for DB schema v24+
3. Firefox: plaintext values, reads `moz_cookies` table directly
4. Removes agent-browser `SingletonLock` if present
5. Writes cookies JSON to `/tmp/porta_inject_cookies.json`, runs Playwright Python via `uv`
6. `ctx.add_cookies()` — the only way to set HttpOnly cookies (JS `document.cookie` can't)

## Prerequisites

- `uv` installed
- `playwright` Python package (auto-fetched by `uv run --with playwright`)
- agent-browser profile exists at `~/.agent-browser-profile/`

## Requirements for injection to work

- Browser must have written cookies to disk (usually fine while open; close first if in doubt)
- macOS Keychain must be unlocked (`security unlock-keychain` in another tab if locked)

## Install / Update

```bash
cd ~/code/porta && cargo install --path .
```

## Caveats

- Google OAuth cookies are session-bound; they expire after hours/days
- If Vercel re-prompts for login: `porta inject --domain vercel.com`
- Session cookies (`expires=None`) aren't persisted across browser restarts by Playwright — test access immediately after injecting
- Arc: only useful if Arc is installed and has a Default profile

## Cloudflare-Protected Sites — Direct Playwright Pattern

`porta inject → agent-browser` fails on Cloudflare-protected sites — headless Chromium fingerprint gets detected even with valid cookies. Workaround: skip agent-browser entirely and use a direct Playwright + browser_cookie3 script. Injecting `cf_clearance` + session cookies together bypasses Cloudflare.

```python
# /// script
# dependencies = ["playwright", "browser-cookie3"]
# ///
import asyncio, browser_cookie3
from playwright.async_api import async_playwright

async def main():
    # Extract from both subdomain AND parent domain to capture all CF + session cookies
    cookies = list(browser_cookie3.chrome(domain_name='community.linkingyourthinking.com'))
    cf = list(browser_cookie3.chrome(domain_name='.community.linkingyourthinking.com'))
    cookie_list = [{"name": c.name, "value": c.value, "domain": c.domain, "path": c.path or "/"} for c in cookies + cf]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        await ctx.add_cookies(cookie_list)
        page = await ctx.new_page()
        await page.goto("https://community.linkingyourthinking.com/courses", timeout=30000)
        await page.wait_for_load_state("domcontentloaded", timeout=20000)  # NOT networkidle — SPAs hang
        content = await page.evaluate("document.body.innerText")
        print(content)
        await browser.close()

asyncio.run(main())
```

Run with: `uv run --script --python 3.13 script.py`

**Gotchas:**
- Use `wait_for_load_state("domcontentloaded")` not `"networkidle"` — Circle.so and React SPAs hang on networkidle
- Extract cookies from both `.domain.com` AND `subdomain.domain.com` — CF stores `cf_clearance` on the parent, session cookies on the subdomain

## When porta FAILS — use `tessera` instead

| Site | Why porta fails | Fix |
|------|----------------|-----|
| **linkedin.com** | `li_at` session is IP + device-fingerprint bound. Injected cookie is silently rejected. | `tessera` for linkedin.com |
| **cora.computer** | Uses Devise auth (own login form, not Google SSO). | `tessera` for cora.computer |
| Any Google SSO third-party | Google cookies ≠ third-party site session. Log in via Google SSO in Chrome first, *then* `porta inject --domain site.com` for that site's cookies. | |

**Decision rule:** If `agent-browser` redirects to a login page after `porta inject`, the site uses fingerprint-binding or own auth. Switch to `tessera`.

## Authenticated Sites (via porta)

| Site | Last injected | Status | Notes |
|------|--------------|--------|-------|
| vercel.com | Mar 2026 | ✅ works | Google OAuth, ~20 cookies |
| linkedin.com | Mar 2026 | ❌ fails | IP-bound session |
| cora.computer | Mar 2026 | ⚠️ partial | Cookies inject OK in-context but don't survive profile restart. No fix script available — investigate manually. |
| community.linkingyourthinking.com | Mar 2026 | ✅ works (direct Playwright only) | Cloudflare-protected — porta inject → agent-browser blocked. Use direct Playwright pattern above instead. |
