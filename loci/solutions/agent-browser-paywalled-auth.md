# agent-browser: One-Time Auth for Paywalled Sites

## Pattern

Use `--headed --profile` to show a visible Chrome window for interactive login. Cookies persist in the profile for future headless fetches.

```bash
# 1. Close any existing headless session
agent-browser close

# 2. Open login page in visible browser
agent-browser open "https://example.com/sign-in" --headed --profile

# 3. User logs in manually in the visible Chrome window

# 4. Close and return to headless
agent-browser close

# 5. Future fetches are authenticated (headless, cookies persist)
agent-browser --profile open "https://example.com/paywalled-article"
agent-browser eval "document.querySelector('article').innerText"
```

## Gotchas

- **`AGENT_BROWSER_PROFILE` must be the actual path, not a boolean.** Fixed Feb 2026: env var now set in `~/.claude/settings.json` `env` field — no manual prefix needed. Never use `AGENT_BROWSER_PROFILE=1` — that creates a profile at literal path "1" and cookies go to the wrong place.
- `--profile` flag position: must come **after** the URL for `open` command, or use `agent-browser --profile open <url>` (flag before command also works)
- `--headed` and `--profile` can't be mixed with an already-running daemon — `close` first
- Substack RSS feeds truncate paywalled content regardless of subscription — browser auth is the only way to get full text programmatically
- When daemon is already running, `--profile` flag is ignored with warning: "daemon already running. Use 'agent-browser close' first"

## Cloudflare-Blocked Sites

Some sites use Cloudflare Turnstile which detects headless Chrome and blocks login entirely — even with a valid profile and correct credentials. No workaround via `eval` or clicking the checkbox; the Turnstile widget doesn't render in the accessibility tree.

| Site | Status | Notes |
|------|--------|-------|
| Manulife HK (`individuallogin.manulife.com.hk`) | Blocked (Feb 2026) | Cloudflare Turnstile after login POST. Username: `terrylihm` (not email). Check claims on phone instead. |

## `porta run` — Best Path for Cookie-Auth Sites (LRN-20260311-001)

For sites where `porta inject` + `agent-browser open` silently fails, use `porta run` directly. It injects Chrome cookies into a fresh Playwright context and fetches the page in one step.

```bash
porta run --domain <site.com> --selector body "<url>"
```

- `--selector main` (default) works if site has `<main>` tag; use `--selector body` as fallback
- Login in Chrome first, then run — cookies are read fresh each time
- No need to call `agent-browser close` or `porta inject` separately

**Do NOT use `porta inject` → `agent-browser open` for HttpOnly/SameSite session cookies** — the injection silently fails; browser redirects to login page with no error.

| Site | Command | Notes |
|------|---------|-------|
| cora.computer | `porta run --domain cora.computer --selector body "<url>"` | Mar 2026. `porta inject` → `agent-browser open` silently fails. `porta run` works. |

## Authenticated Sites (agent-browser profile)

| Site | Profile Auth | Notes |
|------|-------------|-------|
| Substack (Latent Space) | Yes (Feb 2026) | Full AINews digest + editorial |
| Taobao/Tmall | Yes | See taobao reference skill |

## Discovery

Feb 2026. Initially tried headless-only flow — user couldn't see the browser to log in. `--headed` flag wasn't obvious from the basic help output.
