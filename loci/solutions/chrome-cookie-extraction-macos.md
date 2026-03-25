# Chrome Cookie Extraction on macOS

## Problem
Extracting encrypted cookies from Chrome's SQLite DB on macOS for browser automation.

## Key Facts
- Chrome stores cookies in `~/Library/Application Support/Google/Chrome/Default/Cookies` (SQLite)
- All cookie values are encrypted with `v10` prefix (AES-128-CBC)
- Encryption key: `security find-generic-password -s "Chrome Safe Storage" -w` → PBKDF2(password, "saltysalt", 1003, 16, sha1)
- IV: 16 space characters (0x20)

## Gotcha: First Block Corruption
On newer Chrome versions, the first 2 AES blocks (32 bytes) of decrypted values are garbage. The real cookie value follows after. Fix: find the longest trailing ASCII substring.

## Gotcha: pycookiecheat Hangs
`pycookiecheat` hangs indefinitely waiting for macOS Keychain permission dialog. The dialog may be hidden behind other windows. Workarounds:
1. Run `security unlock-keychain` in another terminal first
2. Click "Always Allow" on the macOS dialog when it appears
3. Use custom Python script with `cryptography` lib instead (avoids pycookiecheat dependency)

## Gotcha: `__Host-` Cookie Injection in Playwright
`__Host-` prefixed cookies CANNOT have `domain` set in Playwright's `addCookies()`. Use `url` parameter instead, and omit `path`:
```js
if (c.name.startsWith('__Host')) {
  return { ...base, url: `https://${host}/` }; // no domain, no path
}
return { ...base, domain: c.domain }; // normal cookies use domain
```

## Gotcha: better-sqlite3 on Node v25
`better-sqlite3` native bindings fail to build on Node v25 (node-v141). Use Python's built-in `sqlite3` module instead via a helper script.

## Working Solution (limen)
Python script (`scripts/extract-cookies.py`) using `cryptography` lib for decryption + `sqlite3` for DB access. Called from Node.js via `execSync`. Results cached to `~/.limen/cookies.json` with JWT expiry checking.

## Related
- Project: `~/code/limen/`
- Playwright stealth: `playwright-extra` + `puppeteer-extra-plugin-stealth` bypasses Cloudflare Turnstile

## Agent-Browser Cookie Injection via Playwright

**Pattern:** Extract with `browser_cookie3` (handles decryption), inject via `playwright.async_api` `context.add_cookies()`.
```python
import browser_cookie3
from playwright.async_api import async_playwright

cj = browser_cookie3.chrome(domain_name=".example.com")
cookies = [{"name": c.name, "value": c.value, "domain": c.domain, "path": c.path or "/", "secure": bool(c.secure)} for c in cj]
# Then: await context.add_cookies(cookies)
```

**Works for:** Sites that don't fingerprint sessions (Vercel, etc.)

**Does NOT work for:**
- **LinkedIn** — `li_at` is IP/device-fingerprint-bound. Cookie injection fails silently; session is rejected.
- **Cora** — uses Devise auth (no Chrome session to copy). Need `tessera` skill to log in fresh.
- **Sites using Google SSO** — extracting Google cookies doesn't grant access to third-party sites; SSO tokens are separate.

**Alternative:** Use `tessera` skill to interactively log in once, saving the session to `~/.agent-browser-profile`.
