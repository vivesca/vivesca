# Discovering Undocumented APIs from macOS Apps via mitmproxy

## When to Use

Any native macOS app (Electron, Swift, etc.) that calls HTTP APIs you want to tap — especially when the app has no public API docs and you want to replicate its functionality in a CLI or script.

Real use: discovered `GET https://api.anthropic.com/api/oauth/usage` — the undocumented endpoint behind Claude Code's `/status` interactive dialog. Used to build `usus`.

## Setup (one-time)

```bash
brew install mitmproxy
mitmproxy --version   # verify
```

Install CA cert so macOS trusts mitmproxy's HTTPS interception:

```bash
# Start proxy first to generate cert
mitmproxy &
# In a new terminal:
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/.mitmproxy/mitmproxy-ca-cert.pem
```

Requires `sudo` — runs a Touch ID / password prompt in terminal, not from Claude Code.

## Intercept a Session

```bash
# Start proxy (port 8080 by default)
mitmproxy

# In another terminal, run the target app with proxy env vars:
ALL_PROXY=http://localhost:8080 HTTPS_PROXY=http://localhost:8080 HTTP_PROXY=http://localhost:8080 \
  /Applications/Claude.app/Contents/MacOS/Claude
```

Or for Electron apps that ignore env vars, use system-level proxy:
System Settings → Network → Proxies → set HTTP + HTTPS proxy to `127.0.0.1:8080`.

## Reading the Traffic

In mitmproxy UI:
- Arrow keys to navigate requests
- `Enter` to inspect a request
- `q` to go back
- `/` to search by URL

Look for:
- Auth headers (`Authorization: Bearer ...`)
- Request/response bodies (JSON)
- Endpoints you didn't know existed

## Extracting Credentials / Tokens

Once you see the Bearer token, find where the app stores it:

```bash
# Dump macOS Keychain for the app
security dump-keychain | grep -A5 -i "claude\|anthropic"
# Or more targeted:
security find-generic-password -s "Claude Code-credentials" -w
```

Claude Code stores its OAuth token as JSON in Keychain under service `Claude Code-credentials`:
```json
{"claudeAiOauth": {"accessToken": "sk-ant-oat01-...", "refreshToken": "...", "expiresAt": <ms>}}
```

## Building a CLI from Intercepted Traffic

Once you have the endpoint + auth pattern:
1. Replicate the exact headers (check `anthropic-beta`, `user-agent`, etc.)
2. Read credentials from Keychain at runtime (not hardcoded)
3. Handle token expiry gracefully with a clear error message

Example: `usus` (`~/code/usus/`) — reads OAuth token from Keychain, calls `/api/oauth/usage`, displays session/weekly/Sonnet % with HKT reset times.

## Cleanup (optional)

Remove the CA cert when no longer needed:

```bash
sudo security remove-trusted-cert ~/.mitmproxy/mitmproxy-ca-cert.pem
```

## Gotchas

- **`sudo` required for system-wide CA trust** — can't run from Claude Code Bash tool. Run manually in terminal.
- **Electron apps often ignore `HTTP_PROXY` env vars** — use system proxy settings instead.
- **OAuth tokens expire (~1hr for Claude Code).** Build with expiry handling from the start.
- **Undocumented endpoints can change without notice** — add a version/date comment in your CLI.
- **`anthropic-beta: oauth-2025-04-20` header required** for the Claude Code usage endpoint — without it, 401.

## Secondary Access Path: Response Headers

For Anthropic's API specifically: every `/v1/messages` response includes `anthropic-ratelimit-unified-7d-utilization` with the weekly utilization %. No Keychain, no separate auth needed — any tool already calling the API can read it directly from response headers. Lighter-weight alternative to the OAuth endpoint when you already have an API key in scope.

## Discovered

2026-03-08 — reverse-engineering Claude Code's `/status` dialog to build `usus`.
