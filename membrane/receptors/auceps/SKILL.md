---
name: auceps
description: Smart wrapper for the bird X/Twitter CLI. Use instead of bare bird — auto-routes URLs, handles, and search; adds --vault and --endocytosis output modes.
user_invocable: false
---

# auceps

Smart bird CLI wrapper. Auto-routes input, always injects auth, normalises errors. Use instead of calling bird directly.

## Commands

### Auto-routed (main interface)

```bash
auceps <url>           # x.com URL → bird read
auceps @handle         # handle → bird about + user-tweets combined
auceps handle          # bare handle (no @) → same as above
auceps "search query"  # multi-word → bird search
```

### Explicit subcommands

```bash
auceps thread <url> [--depth 2]   # follow quoted tweet chain
auceps bird <any bird args>        # direct passthrough to bird
auceps post "tweet text"           # post a tweet (see Posting section below)
```

### Output flags (global)

```bash
auceps @handle --vault      # Obsidian markdown: # @handle (Name), bio, tweets
auceps @handle --endocytosis     # JSON for endocytosis x_accounts ingestion
auceps @handle -n 5         # limit tweets (default: 20)
```

## Endocytosis JSON schema

```json
{
  "handle": "@handle",
  "name": "Display Name",
  "focus": "",
  "tier": 2
}
```

Note: `focus` is empty — bird doesn't expose profile bio text. Fill manually after generating.

## Posting

`bird tweet` returns error 226 ("looks automated") from the API. Working path:

1. URL-encode the tweet text
2. Open `https://x.com/intent/post?text=<encoded>` via osascript `open location`
3. Wait ~3s for Chrome to load the compose dialog
4. Send Cmd+Enter via System Events to submit

```python
import os, subprocess, urllib.parse, time

def post_tweet(text: str):
    encoded = urllib.parse.quote(text)
    url = f"https://x.com/intent/post?text={encoded}"
    # Open in Chrome
    subprocess.run(['osascript', '-e', f'open location "{url}"'])
    time.sleep(3)
    # Submit with Cmd+Enter
    subprocess.run(['osascript', '-e', '''
tell application "Google Chrome" to activate
delay 0.5
tell application "System Events"
  keystroke return using {command down}
end tell
'''])
```

**Character limit:** X counts URLs as 23 chars. Effective limit = raw_length - actual_url_length + 23 ≤ 280.

**`porta inject` does NOT get auth cookies for X.** Guest cookies only (guest_id etc.). `AUTH_TOKEN`/`CT0` are in env vars from 1Password — use those directly if needed for other API calls.

**agent-browser is unreliable for X.** X blocks headless Chromium. Skip it entirely for posting — osascript + intent URL is the only reliable path.

## Gotchas

- **Auth:** Prefers `AUTH_TOKEN`/`CT0` env vars (injected via `~/.zshenv.tpl` from 1Password). Falls back to `--cookie-source chrome` if env vars absent. Never add auth args manually.
- **SSH/tmux:** If env vars not injected, bird fails with keychain exit 36. Fix: ensure `AUTH_TOKEN`/`CT0` are in `~/.zshenv.tpl` and shell was started after `op inject`. The old `security unlock-keychain` workaround is obsolete.
- **`-n` not `-l`:** short flag for limit is `-n`, long is `--limit`
- **`about` not `profile`:** auceps uses the correct bird subcommand internally — callers never need to know
- **focus field:** `--endocytosis` leaves focus blank; bio isn't available from bird. Fill it manually or from context.
- **Thread depth:** `auceps thread` follows quoted tweet URLs via regex. Stops early if no quoted tweet found.

## Binary

`~/.cargo/bin/auceps` — install/update: `cd ~/code/auceps && cargo install --path .`

## Source

`~/code/auceps/` — Rust, edition 2024, no async. Reference: keryx (subprocess pattern), stips (ExitCode entry point).
