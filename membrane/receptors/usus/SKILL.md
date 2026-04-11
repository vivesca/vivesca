---
name: usus
description: Check exact Claude Code Max plan usage limits (session %, weekly %, Sonnet %). Use when asked about usage, weekly limits, or /status data. Reads from Anthropic's OAuth API via macOS Keychain — same source as /status interactive dialog.
effort: low
user_invocable: false
---

# usus — Claude Code Usage CLI

Reads the live OAuth token from macOS Keychain and calls `GET https://api.anthropic.com/api/oauth/usage`. Gives the same numbers as `/status` without the interactive UI.

## Commands

```bash
usus                              # Human-readable display with status colour
usus --json                       # Raw JSON from the API
usus --statusline                 # Compact one-liner for statusLine config
usus log                          # Fetch + append snapshot to history.jsonl
usus log --note "morning session" # Snapshot with freetext annotation
usus history                      # Show all logged snapshots as table
usus history --last 7             # Show last N snapshots
```

## History

Snapshots are stored in `~/.local/share/usus/history.jsonl` (JSONL, one row per `usus log`).
Use `usus history` to review usage trends — replaces manual markdown tracking for quota validation.

## Output

```
Claude Code Usage — Sun Mar  8 07:19 HKT

  Session (5h)     8%   resets 11:00am
  Weekly           13%  resets Fri Mar 13 11:00am
  Weekly (Sonnet)  20%  resets Fri Mar 13  3:00pm
  Extra usage      $0.00 / $50.00

Status: SAFE
```

Statusline: `📊 W:13% S:20% 5h:8% ↻Fri`

## How it works

1. Reads `Claude Code-credentials` from macOS Keychain (JSON with `claudeAiOauth.accessToken`)
2. Calls `GET https://api.anthropic.com/api/oauth/usage` with `Authorization: Bearer <token>`
3. Parses response: `five_hour`, `seven_day`, `seven_day_sonnet`, `extra_usage`

## Gotchas

- **Token expires ~1hr after Claude Code session starts.** If you get an auth error, start a new Claude Code session — it refreshes the token on startup.
- **Requires active Claude Code session.** The token lives in Keychain only while Claude Code has authenticated. Fresh login writes a new token.
- **Token refresh not yet implemented.** v0.1.0 errors on expiry with a clear message.
- **macOS only.** Uses `security-framework` (Keychain). Won't work on Linux/Windows.
- The `seven_day_sonnet` counter resets ~4h after `seven_day` (3pm vs 11am HKT Friday).
- Discovered via mitmproxy intercept of Claude Code traffic (2026-03-08). Endpoint undocumented — could change on Claude Code updates.

## Integration with statusLine

Add to `~/.claude/settings.json` `statusLine.command` to show `📊 W:13% S:20%` in the Claude Code status bar:

```json
"statusLine": {
  "type": "command",
  "command": "... && usus --statusline 2>/dev/null || echo ''"
}
```

## Source

`~/code/usus/` — private repo at `terry-li-hm/usus`
