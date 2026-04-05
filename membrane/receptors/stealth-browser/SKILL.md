---
name: stealth-browser
description: Last-resort Cloudflare bypass via Chrome cookies + playwright-extra stealth. Use when peruro fails or authenticated browser session needed. "stealth browser", "cloudflare bypass"
---

# Stealth Browser

**Last resort.** For tool selection and the full fetch ladder, see `indago` skill first.

Reference skill for bypassing Cloudflare Turnstile and accessing authenticated sites via Chrome cookie extraction + playwright-extra stealth. Only reach here after `peruro` has failed or the site requires an authenticated Chrome session.

## Escalation Order (Cloudflare-blocked sites)

**Try in this order — stop at first success:**

1. `peruro "<url>"` — Firecrawl residential proxies, 1 credit/page. Works on most Cloudflare Bot Management sites (confirmed: OpenRice). No setup needed.
2. `stealth-browser` (this skill) — full Chrome cookie injection + playwright-extra stealth. Use when `peruro` fails or site requires authentication.

## When to Use

- `peruro` has failed or returned a challenge page
- `agent-browser` gets blocked by Cloudflare Turnstile CAPTCHA
- Need to automate a site the user is logged into in Chrome
- Need to inject Chrome's authenticated session into Playwright

## When NOT to Use

- Site works fine with `agent-browser` (no Cloudflare)
- Public pages without authentication → try `peruro` first
- Sites that need interactive login (Google OAuth blocks Playwright — no workaround)

## Prerequisites

```bash
# Cookie extraction (Rust CLI — crates.io)
cargo install kleis

# Node.js (in project, for stealth browser)
pnpm add playwright playwright-extra puppeteer-extra-plugin-stealth
```

Keychain must be unlocked: `security unlock-keychain ~/Library/Keychains/login.keychain-db`

## Pattern 1: Chrome Cookie Extraction (macOS)

Use **kleis** (`~/code/kleis/`, [crates.io](https://crates.io/crates/kleis)) — a standalone Rust CLI that decrypts Chrome's v10-encrypted cookies and outputs JSON to stdout.

```bash
kleis midjourney.com          # → JSON array of cookies
kleis .example.com www.example.com  # multiple domains
```

Handles all the gotchas internally (first-block corruption, PKCS7 unpadding, domain expansion).

### How it works (internals)

Chrome encrypts cookies with AES-128-CBC. Key derivation:
```
password = `security find-generic-password -s "Chrome Safe Storage" -w`
key = PBKDF2(password, "saltysalt", iterations=1003, dklen=16, hash=sha1)
```

Cookie DB: `~/Library/Application Support/Google/Chrome/Default/Cookies` (SQLite)

### Gotcha: First-Block Corruption

On newer Chrome, the first 2 AES blocks (32 bytes) decrypt to garbage. The real value is the trailing clean ASCII. kleis handles this automatically.

### Gotcha: pycookiecheat Hangs

`pycookiecheat` blocks waiting for macOS Keychain dialog (may be hidden behind windows). kleis avoids this by calling `security` directly.

### Legacy: Python reference script

```python
#!/usr/bin/env python3
"""Extract cookies from Chrome on macOS. Outputs JSON to stdout."""
import json, sqlite3, subprocess, shutil, tempfile, hashlib
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

CHROME_COOKIES = Path.home() / "Library/Application Support/Google/Chrome/Default/Cookies"
DOMAINS = (".example.com", "www.example.com")  # ← CHANGE THIS

def get_chrome_key() -> bytes:
    raw = subprocess.check_output(
        ["security", "find-generic-password", "-s", "Chrome Safe Storage", "-w"],
        text=True,
    ).strip()
    return hashlib.pbkdf2_hmac("sha1", raw.encode(), b"saltysalt", 1003, dklen=16)

def decrypt_v10(encrypted: bytes, key: bytes) -> str:
    if len(encrypted) <= 3:
        return ""
    if encrypted[:3] != b"v10":
        return encrypted.decode("utf-8", errors="replace")
    iv = b" " * 16
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(encrypted[3:]) + decryptor.finalize()
    try:
        unpadder = padding.PKCS7(128).unpadder()
        decrypted = unpadder.update(decrypted) + unpadder.finalize()
    except Exception:
        pass
    # Strip garbage first-block(s) — find longest trailing ASCII
    raw = decrypted.decode("latin-1")
    best_start = len(raw)
    for i in range(len(raw) - 1, -1, -1):
        if 0x20 <= ord(raw[i]) < 0x7F:
            best_start = i
        else:
            break
    return raw[best_start:] if best_start < len(raw) else raw

def main():
    key = get_chrome_key()
    tmp = tempfile.mktemp(suffix=".db")
    shutil.copy2(CHROME_COOKIES, tmp)
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    placeholders = ",".join("?" for _ in DOMAINS)
    rows = conn.execute(
        f"SELECT name, encrypted_value, host_key, path, is_secure, is_httponly "
        f"FROM cookies WHERE host_key IN ({placeholders})", DOMAINS
    ).fetchall()
    result = []
    for row in rows:
        value = decrypt_v10(row["encrypted_value"], key)
        if value:
            result.append({
                "name": row["name"], "value": value,
                "domain": row["host_key"], "path": row["path"] or "/",
                "secure": bool(row["is_secure"]),
                "httpOnly": bool(row["is_httponly"]),
            })
    conn.close()
    Path(tmp).unlink(missing_ok=True)
    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

## Pattern 2: Playwright Stealth Setup

Use **larvo** (`~/code/larvo/`, [npm](https://www.npmjs.com/package/larvo)) — wraps playwright-extra + stealth plugin into a single function:

```typescript
import { createStealthContext } from 'larvo';
import { execSync } from 'child_process';

const cookies = JSON.parse(execSync('kleis midjourney.com', { encoding: 'utf-8' }));
const { context, page, close } = await createStealthContext({
  profile: '~/.myapp/browser-profile',
  cookies,
});

// ... use page ...
await close();
```

`pnpm add larvo` — handles all critical settings internally:
- `headless: false` — Cloudflare detects headless mode even with stealth
- `channel: 'chromium'` — use system Chromium, not bundled
- `--disable-blink-features=AutomationControlled` — hides `navigator.webdriver`
- Persistent context — retains cookies/state between runs

## Pattern 3: Cookie Injection

```typescript
// __Host- cookies CANNOT have domain set — use url instead
const mapped = cookies.map((c) => {
  const base = {
    name: c.name, value: c.value, path: c.path || '/',
    secure: c.secure ?? true,
    httpOnly: c.httpOnly ?? (c.name.startsWith('__Host') || c.name.startsWith('__cf')),
    sameSite: 'Lax' as const,
  };
  if (c.name.startsWith('__Host')) {
    const host = c.domain.startsWith('.') ? c.domain.slice(1) : c.domain;
    const { path: _path, ...rest } = base;
    return { ...rest, url: `https://${host}/` };
  }
  return { ...base, domain: c.domain };
});
await context.addCookies(mapped);
```

## Gotchas Checklist

Before implementing, verify:

- [ ] **Keychain unlocked?** `security find-generic-password -s "Chrome Safe Storage" -w` should return a value instantly
- [ ] **Chrome running?** Cookie DB can be read while Chrome runs (script copies it first)
- [ ] **`__Host-` cookies?** Must use `url` not `domain` in Playwright — will silently fail otherwise
- [ ] **JWT expiry?** Decode the JWT and check `exp` field before using cached cookies
- [ ] **`headless: false`?** Cloudflare WILL block headless, even with stealth plugin
- [ ] **`better-sqlite3` needed?** No — kleis handles SQLite internally. better-sqlite3 has native build issues on Node v25+.

## Proven Implementations

- **kleis** (`~/code/kleis/`, [crates.io](https://crates.io/crates/kleis)) — Standalone Rust cookie extraction CLI. `cargo install kleis`.
- **larvo** (`~/code/larvo/`, [npm](https://www.npmjs.com/package/larvo)) — Stealth browser context library. `pnpm add larvo`.
- **limen** (`~/code/limen/`) — Midjourney CLI. Uses kleis + larvo. Full working example of the complete pipeline.

## Future: agent-browser Enhancement

When this pattern is needed for a third site, extract into `agent-browser --stealth` flag. Until then, copy-adapt from limen or this skill's reference scripts.
