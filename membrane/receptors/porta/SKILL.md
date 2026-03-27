---
name: porta
description: Bridge Chrome session cookies into agent-browser when a login wall appears for a site you're authenticated in Chrome.
user_invocable: false
tags: [browser, auth, cookies]
context: inline
---

# porta — Chrome cookie bridge

> *Porta: Latin "gate" — the membrane crossing that lets session identity flow from Chrome into the headless agent-browser context.*

When `endocytosis_check_auth` detects a login wall, porta injects Chrome cookies into agent-browser's active page. One call; no headed browser needed.

## When to use

- `endocytosis_check_auth` returns `authenticated: false` and you are logged into the site in Chrome
- agent-browser lands on a login redirect for a domain you have a valid Chrome session for
- The site uses cookie-based session auth (most standard web apps)

## When NOT to use

- **localStorage / JWT auth** — cookies don't carry this state; porta will inject successfully but the page will still show a login wall
- **Blink or SSH sessions** — pycookiecheat requires Keychain GUI access; injection will fail with a Keychain prompt error
- **Sites that pin cookies to IP/User-Agent** — injected cookies may be rejected by the server
- **First-time logins** — porta bridges existing sessions, not creates them

## Flow

```
endocytosis_check_auth(domain)
  → authenticated: false
    → porta_inject(domain)          # MCP tool
      → success: true, count > 0
        → endocytosis_extract(url)  # retry
      → success: false
        → check message for localStorage hint
        → fallback: agent-browser --headed open <url>  (log in manually)
```

## MCP tool

**`porta_inject`** — `domain: str`

Returns `EffectorResult`:
- `success`: whether at least one cookie was injected
- `message`: summary with count and any failures
- `data.count`: cookies injected
- `data.domain`: domain targeted

## Implementation

- Organelle: `~/germline/metabolon/organelles/porta.py`
- Tool: `~/germline/metabolon/tools/porta.py`
- Uses `_ab()` pattern from pseudopod for all agent-browser calls

## Known limitations

- Cookie scope: `document.cookie` sets session-visible cookies. HttpOnly cookies set by the server survive navigation; this path cannot replicate server-set HttpOnly cookies — it only restores what Chrome has in its SQLite store.
- Partial injection: if some cookies fail, porta returns `success: true` with a partial count. Check `message` for failed names.
