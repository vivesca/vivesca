# Claude Code In-Session Usage & Quota Tracking — Research Findings
*Researched 2026-03-18. Focus: Max plan subscribers, from inside a running Claude Code session.*

---

## Finding

There is **no first-party, officially-supported way** to check Max plan quota (5-hour / weekly %) from inside a running Claude Code session. Anthropic has not responded to multiple open feature requests (#13585, #15366, #22428). However, a reliable workaround exists: read the live OAuth token from macOS Keychain and query `GET https://api.anthropic.com/api/oauth/usage` directly. This is what `usus` already does.

The core blocker is OAuth token expiry (~1hr into a session, sometimes less). No community tool has solved programmatic refresh — the refresh token flow is opaque and has multiple open bugs.

---

## Key Facts

### 1. The Undocumented API Endpoint (Working as of Mar 2026)

```
GET https://api.anthropic.com/api/oauth/usage
Authorization: Bearer <accessToken>
anthropic-beta: oauth-2025-04-20
```

Response:
```json
{
  "five_hour":      { "utilization": 8.0,  "resets_at": "2026-03-18T04:00:00+00:00" },
  "seven_day":      { "utilization": 13.0, "resets_at": "2026-03-20T03:00:00+00:00" },
  "seven_day_sonnet": { "utilization": 20.0, "resets_at": "2026-03-20T07:00:00+00:00" },
  "extra_usage":    { "amount_usd": 0.0, "limit_usd": 50.0 }
}
```

This is the same endpoint Claude Code itself calls when displaying the `/status` interactive UI. Discovered via mitmproxy intercept (community, Mar 2026). Undocumented — could change without notice.

Sources: [gist/jtbr](https://gist.github.com/jtbr/4f99671d1cee06b44106456958caba8b), [gist/omachala](https://gist.github.com/omachala/5ea5af4bfa0b194a1d48d6f2eedd6274), [GH issue #13585](https://github.com/anthropics/claude-code/issues/13585)

### 2. Token Storage (macOS)

```bash
security find-generic-password -s "Claude Code-credentials" -w
# Returns JSON: { "claudeAiOauth": { "accessToken": "sk-ant-oat01-...", "refreshToken": "...", "expiresAt": 1234567890, "scopes": [...] } }
```

The token written to Keychain at session start has `user:inference` **and** `user:profile` scopes — both required for the usage endpoint. Tokens from `claude setup-token` only get `user:inference` and **cannot** query the usage endpoint.

Source: [codelynx.dev](https://codelynx.dev/posts/claude-code-usage-limits-statusline), [GH issue #18444](https://github.com/anthropics/claude-code/issues/18444)

### 3. The Expiry Problem

- Access token expires roughly 1hr after Claude Code session start (sometimes faster under load)
- The `expiresAt` field in Keychain contains the expiry timestamp
- When expired, `GET /api/oauth/usage` returns 401
- **No community tool handles programmatic refresh.** All known scripts (codelynx, omachala gist, jtbr gist) assume the token is valid and fail silently or with an error on expiry

Source: [GH issue #12447](https://github.com/anthropics/claude-code/issues/12447), [GH issue #18444](https://github.com/anthropics/claude-code/issues/18444)

### 4. Why Programmatic Refresh Is Hard

Claude Code uses **OAuth with refresh token rotation** (RFC 9700 §2.2.2): each use of the refresh token invalidates it and issues a new pair. The Anthropic token refresh endpoint is not publicly documented. Two known failure modes:
- Multiple concurrent Claude Code sessions race on refresh → loser gets 404 and loses auth
- After refresh, the new token sometimes **loses `user:profile` scope** (GH issue #34785), making it useless for the usage endpoint

The `apiKeyHelper` setting (which supports TTL-based refresh) only works for API key flows, not for OAuth subscription auth. Setting `CLAUDE_CODE_OAUTH_TOKEN` as an env var overrides Keychain but is equally subject to expiry.

Sources: [GH #24317](https://github.com/anthropics/claude-code/issues/24317), [GH #21765](https://github.com/anthropics/claude-code/issues/21765), [GH #34785](https://github.com/anthropics/claude-code/issues/34785)

---

## Tools Survey

### ccusage ([github](https://github.com/ryoppippi/ccusage), [site](https://ccusage.com/))
- Reads local JSONL files from `~/.claude/` — token accounting only
- **Does not** query the OAuth usage endpoint
- **Does not** show quota %, 5-hour/weekly limits, or Extra Usage balance
- Has a statusline integration (beta) showing session cost and 5-hour billing-block burn rate — not Max plan quota
- Useful for: cost attribution, per-session token breakdown, identifying expensive prompts

### Claude-Code-Usage-Monitor ([github](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor))
- Real-time terminal monitor, ML-based predictions
- Uses historical JSONL data — no OAuth endpoint
- Detects plan tier (Max5/Max20) and auto-sets token ceiling
- Shows "how long until you hit session limit" via prediction
- **Does not** show actual quota % from Anthropic's servers

### jtbr statusline gist ([gist](https://gist.github.com/jtbr/4f99671d1cee06b44106456958caba8b))
- Most complete community implementation
- Reads Keychain → calls `/api/oauth/usage` → shows 5h/7d bars with pacing markers
- **Does not** handle token refresh — hangs/fails when token expires
- Caches result to `/tmp/claude-statusline-usage.json` with 60s TTL
- Requires both `user:inference` AND `user:profile` scopes

### omachala gist ([gist](https://gist.github.com/omachala/5ea5af4bfa0b194a1d48d6f2eedd6274))
- Standalone bash CLI, same Keychain + endpoint approach
- No token refresh, no expiry check, prompts user to manually refresh on 401
- Good as a simple one-off check; no integration with Claude Code session

### usage-monitor-for-claude ([github](https://github.com/jens-duttke/usage-monitor-for-claude))
- Windows tray app only — not relevant for macOS/SSH workflow

### Terry's `usus` (`~/code/usus/`)
- Already implements the canonical approach: Keychain read → `/api/oauth/usage` → human + JSON + statusline output + history JSONL
- Has the same unresolved expiry problem documented in the Gotchas section
- **This is the best available tool for this use case** — no third-party tool does more

---

## Hooks System — Can It Inject Quota?

The statusLine hook receives session JSON via stdin but **the payload does not include plan quota fields** (5-hour %, weekly %). This is an open feature request (GH #15366, #22428) with no Anthropic response as of Mar 2026.

The `UserPromptSubmit` hook can inject arbitrary text via `additionalContext` before each Claude message — this is the mechanism for in-session quota injection. A hook could:
1. Read Keychain token
2. Call `/api/oauth/usage`
3. Return `{ "hookSpecificOutput": { "hookEventName": "UserPromptSubmit", "additionalContext": "Weekly quota: 13%, resets Fri" } }`

This would make Claude aware of quota before each message. Feasible, but suffers from the same token expiry problem.

The statusLine hook approach (calling `usus --statusline` as the statusLine command) **does work** for continuous display as long as the token is valid. The statusline runs after each assistant message — so it calls `usus` (which hits the API) on each turn. Token expiry mid-session causes the statusline to go blank/error, but does not break Claude Code itself.

Source: [Official statusline docs](https://code.claude.com/docs/en/statusline), [hooks guide](https://code.claude.com/docs/en/hooks-guide), [GH #15366](https://github.com/anthropics/claude-code/issues/15366)

---

## OpenTelemetry (OTEL) — Does It Help?

Claude Code's OTEL telemetry (`CLAUDE_CODE_ENABLE_TELEMETRY=1`) exports:
- `claude_code.token.usage` (per-request tokens by type + model)
- `claude_code.cost.usage` (USD cost per request)
- API request/error events

It does **not** export quota utilization %, 5-hour window %, or weekly reset timestamps. These are plan-level data, not session-level metrics. OTEL is useful for cross-session accounting (Prometheus/ClickHouse) but not for real-time quota display.

Source: [Official monitoring docs](https://code.claude.com/docs/en/monitoring-usage)

---

## The Refresh Problem — Possible Approaches Not Yet Tried

No community implementation has solved programmatic token refresh. Three potential angles (unverified):

1. **Check `expiresAt` before each call.** If expired, surface a clear error rather than hanging. The token is usually still fresh for the first ~45-60 min — a startup-time check with an expiry warning would cover most sessions.

2. **Restart-to-refresh pattern.** Claude Code refreshes the Keychain token on every startup. A wrapper script that kills and restarts CC when the token is about to expire would be ugly but functional.

3. **Reverse-engineer the token refresh endpoint.** The token endpoint is not documented. Someone with mitmproxy could intercept the CC refresh flow to find the endpoint + body format. This is the path to a proper solution but carries the "undocumented, may break" risk.

---

## Caveats

- The `/api/oauth/usage` endpoint is **undocumented** — Anthropic has not committed to its stability. It has been stable since at least early 2026 but could change.
- The `user:profile` scope requirement means tokens acquired via `claude setup-token` or `ANTHROPIC_API_KEY` do not work for quota checks.
- All third-party tools (ccusage, Claude-Code-Usage-Monitor) track JSONL files locally. These reflect Claude Code token consumption only — they miss usage from Claude.ai web, mobile, and Claude Desktop, so they undercount true weekly quota used.
- No MCP server for quota tracking exists in any known MCP registry as of Mar 2026.
- The statusline quota display goes dark when the token expires — this is the main pain point and has no clean solution today.

---

## Sources

1. [ccusage GitHub](https://github.com/ryoppippi/ccusage)
2. [ccusage statusline guide](https://ccusage.com/guide/statusline)
3. [Claude-Code-Usage-Monitor GitHub](https://github.com/Maciek-roboblog/Claude-Code-Usage-Monitor)
4. [jtbr statusline gist — complete guide with gotchas](https://gist.github.com/jtbr/4f99671d1cee06b44106456958caba8b)
5. [omachala usage CLI gist](https://gist.github.com/omachala/5ea5af4bfa0b194a1d48d6f2eedd6274)
6. [codelynx.dev — usage limits in statusline](https://codelynx.dev/posts/claude-code-usage-limits-statusline)
7. [GH #13585 — Add Quota Information Access to CLI](https://github.com/anthropics/claude-code/issues/13585)
8. [GH #15366 — Add weekly/daily usage to statusLine hook JSON](https://github.com/anthropics/claude-code/issues/15366)
9. [GH #22428 — Expose Claude.ai plan usage in statusLine JSON](https://github.com/anthropics/claude-code/issues/22428)
10. [GH #18444 — OAuth token expires mid-session in Claude Desktop](https://github.com/anthropics/claude-code/issues/18444)
11. [GH #12447 — OAuth token expiration disrupts autonomous workflows](https://github.com/anthropics/claude-code/issues/12447)
12. [GH #21765 — Refresh token not used on headless machines](https://github.com/anthropics/claude-code/issues/21765)
13. [GH #24317 — Concurrent sessions OAuth refresh race condition](https://github.com/anthropics/claude-code/issues/24317)
14. [GH #34785 — Token refresh loses user:profile scope](https://github.com/anthropics/claude-code/issues/34785)
15. [Official statusline docs](https://code.claude.com/docs/en/statusline)
16. [Official monitoring/OTEL docs](https://code.claude.com/docs/en/monitoring-usage)
17. [Official authentication docs](https://code.claude.com/docs/en/authentication)
