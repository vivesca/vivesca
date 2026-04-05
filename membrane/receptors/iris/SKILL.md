---
name: iris
description: "Email verification link relay — polls Gmail for verification emails, extracts the link, opens it in agent-browser. Use when handling 2FA email verification. \"verify email\", \"verification link\""
---

# iris — Email Verification Link Relay

Polls Gmail for a verification email, extracts the first `https://` link, and opens it in an agent-browser tab. Purpose-built for same-browser-session 2FA flows.

## Usage

```bash
iris verify --from <sender> [--subject <keyword>] [--tab <n>] [--timeout <secs>] [--interval <secs>]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--from` | required | Sender pattern, e.g. `stripe` or `notifications@stripe.com` |
| `--subject` | — | Extra keyword to match in subject |
| `--tab` | 1 | agent-browser tab index to open link in |
| `--timeout` | 60 | Seconds to poll before giving up |
| `--interval` | 3 | Polling interval in seconds |

## Example — Stripe key rotation

```bash
# Tab 0: rotation dialog is waiting at dashboard.stripe.com
# Trigger the email verification flow in Stripe dashboard, then:

iris verify --from stripe --subject "verification" --tab 1
# → polls Gmail every 3s
# → switches agent-browser to tab 1
# → opens the link
# → prints: ✓ Opened: https://dashboard.stripe.com/auth_challenge/...
```

## Full Stripe 2FA rotation pattern

```bash
# 1. Open Stripe in tab 0 (persistent profile)
agent-browser open https://dashboard.stripe.com/apikeys --profile

# 2. Navigate to rotate: More options → Rotate key → select expiry → click Rotate
# (Stripe will show email verification dialog)

# 3. In a second terminal or alongside agent-browser commands:
iris verify --from stripe --tab 1 --timeout 90

# 4. After iris succeeds, switch back to tab 0
agent-browser tab 0

# 5. TOTP dialog may appear — get code and enter it
CODE=$(op item get "Stripe" --vault Agents --otp)
agent-browser fill @eXX "$CODE"
agent-browser click @eXX  # Continue button
```

## Gotchas

- **Browser must already be open** — iris runs `agent-browser tab <n>` which fails if the browser daemon isn't running. Start with `agent-browser open <url> --profile` first.
- **Email arrives fast** — Stripe sends within ~2s. Default 3s interval is fine; reduce to `--interval 1` if needed.
- **Link must be opened in same browser session** — that's the whole point. Never use a fresh `agent-browser open` in a new daemon; reuse the existing session.
- **Multiple emails in thread** — `gog gmail search` returns threads; `iris` reads the most recent message. If the first link in the body is expired (from a prior attempt), the email may have multiple links but iris only extracts the first `https://` URL per line. Future: `--link-n` flag to select nth link.
- **gog plain output** — iris uses `--plain` flag for TSV parsing. If gog changes its TSV format, the ID extraction will break.

## Source

`~/code/iris/` — Rust, ~130 lines, no external HTTP crates (pure std + clap + process::Command).
