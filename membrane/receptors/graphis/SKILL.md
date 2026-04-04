---
name: graphics
description: Manage Telegram bots — create, delete, list, start-bot via BotFather. Use when creating a new bot, retiring an old one, or rotating a token. Companion to deltos (sends snippets).
user_invocable: false
---

# graphics

Rust CLI that manages Telegram bots via BotFather using MTProto (grammars crate). No browser needed — talks directly to Telegram as your user account.

Companion to `deltos` (Greek "tablet" → sends snippets). graphics (Greek "stylus" → shapes the bots).

## Commands

```bash
# Auth — two-step, agent-friendly (I run both; user provides the code)
graphics auth +85261872354          # step 1: request code from Telegram
graphics auth-complete 76314        # step 2: complete with code from phone

# Send /start to a bot (required before it can message you)
graphics start-bot @TekmarBot

# Create a new bot — tries usernames in order until one is accepted
graphics create "DisplayName" UsernameBot AltUsernameBot FallbackBot

# Delete a bot
graphics delete @TekmarBot

# List your bots
graphics list
```

On successful `create`: token saved to keychain (`telegram-bot-token`), username saved (`telegram-bot-username`). deltos picks these up automatically.

## Prerequisites

```bash
# API credentials — already in ~/.zshenv via 1Password:
export TELEGRAM_API_ID=2040
export TELEGRAM_API_HASH=b18441a1ff607e10a989891a5462e627
# These are Telegram Desktop's public credentials (standard workaround for personal MTProto clients).
# Do NOT use bot tokens here — these are *user* app credentials.
```

## Files

- Binary: `~/.local/bin/graphis` → symlink to `~/code/target/release/graphis`
- Source: `~/code/graphis/`
- Session: `~/.local/share/graphis/session.bin`
- DC config: `~/.local/share/graphis/dc.txt` — persists which Telegram DC to connect to
- Pending auth: `~/.local/share/graphis/pending-auth.json` — temp file during two-step auth

## Rebuild

```bash
cd ~/code/graphis && cargo build --release
```

## Bot token rotation workflow

1. `graphics create "Name" NameBot AltNameBot` — tries candidates, saves token to keychain
2. `graphics start-bot @NewBot` — I run this; required before bot can message you
3. `echo "test" | deltos` — verify delivery
4. `graphics delete @OldBot` — retire the old bot

## Auth workflow (agent-friendly two-step)

```bash
# I run step 1:
graphics auth +85261872354
# → "Code sent to +85261872354. Give me the code..."

# User checks Telegram app, tells me the code. I run step 2:
graphics auth-complete 21620
# → "Signed in successfully!" (or "Signed in successfully with 2FA!")

# Session saved — no re-auth needed unless session.bin is deleted.
```

State persisted between steps: `pending-auth.json` holds `{phone, phone_code_hash, dc}`.

## Gotchas

- **DC migration** — Terry's phone is on Telegram DC5. `auth` handles this automatically (reconnects to `91.108.56.130:443`). DC is saved to `dc.txt` so all subsequent commands use the right DC. If you delete `dc.txt` and get transport errors, recreate it: `echo "5" > ~/.local/share/graphis/dc.txt`.
- **Session file encodes auth key but NOT the DC address** — grammars does not honour the session's DC on reconnect; `dc.txt` is the source of truth for which server to connect to.
- **Transport error `-404`** — means wrong DC. Check `dc.txt` exists and contains `5`.
- **Stale session after failed auth** — if auth-complete fails with a transport error, delete `session.bin` and `pending-auth.json` and restart from `graphics auth`.
- **Send `/start` to new bots** — Telegram requires users to initiate contact. `deltos` returns "chat not found" until done. Use `graphics start-bot @BotName` — don't rely on doing it manually.
- **CamelCase usernames preferred** — e.g. `TekmarBot` not `tekmar_bot`.
- **Popular names are taken** — try 3-4 candidates. StrixBot, SemaBot, PraecoBot, VoxBot, RemaBot, OssaBot, FamaBot all taken (Mar 2026). TekmarBot was available.
- **BotFather parsing** — relies on BotFather's response text. If BotFather changes phrasing, the create/delete flow may break.
- **macOS only** — keychain integration uses `security` CLI.
- **grammars 0.7 does not handle PHONE_MIGRATE** — neither `invoke()` nor `request_login_code()` auto-migrate. Must handle manually via `InitParams::server_addr`. See `~/docs/solutions/agent-cli-patterns.md`.
- **LoginToken fields are `pub(crate)`** — cannot extract `phone_code_hash` from the high-level type; use raw TL `auth.SendCode` instead which returns the hash directly.

## Current bot

`@TekmarBot` — Greek *tekmar* "a fixed sign, token". Created Mar 2026.
Token in keychain: `telegram-bot-token`.
