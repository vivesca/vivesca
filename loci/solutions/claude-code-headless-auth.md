# Claude Code Headless Server Auth

## Problem
`claude auth login` and `claude setup-token` on headless servers can't be automated via:
- Piped SSH commands (no TTY)
- tmux send-keys (Ink TUI doesn't read from terminal line buffer)
- agent-browser (Cloudflare bot check blocks claude.ai)
- expect (TUI escape codes make pattern matching unreliable)

## Solution
SSH in interactively and run `claude setup-token`. It provides a proper "Paste code here" prompt that works with a real TTY.

```bash
ssh ubuntu@<server>
export PATH="$HOME/.local/share/fnm:$PATH" && eval "$(fnm env)"
claude setup-token
```

1. Opens URL → authorize in browser
2. Callback page shows code → paste into terminal
3. Done

## Notes
- `setup-token` creates a long-lived token (better for servers than `auth login`)
- `auth login` polls for callback but times out quickly on headless
- The `#state=...` suffix in the callback URL is NOT part of the code — only paste what's before `#`
- Hetzner's "Heray" and Cloudflare both block agent-browser completely

## AWS Server Reference
See `~/code/vivesca-terry/chromatin/AWS Cloud Dev Server.md` for full server details.
