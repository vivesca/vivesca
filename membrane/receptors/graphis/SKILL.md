---
name: graphis
description: Manage Telegram bots — create, delete, list, start-bot via BotFather. Use when creating a new bot, retiring an old one, or rotating a token. Companion to deltos (sends snippets).
user_invocable: false
---

# graphis

Rust CLI that manages Telegram bots via BotFather using MTProto (grammers crate). No browser needed — talks directly to Telegram as your user account.

Companion to `deltos` (Greek "tablet" → sends snippets). graphis (Greek "stylus" → shapes the bots).

## Commands

```bash
# Auth — two-step, agent-friendly (I run both; user provides the code)
graphis auth +85261872354          # step 1: request code from Telegram
graphis auth-complete 76314        # step 2: complete with code from phone

# Send /start to a bot (required before it can message you)
graphis start-bot @TekmarBot

# Create a new bot — tries usernames in order until one is accepted
graphis create "DisplayName" UsernameBot AltUsernameBot FallbackBot

# Delete a bot
graphis delete @TekmarBot

# List your bots
graphis list
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

1. `graphis create "Name" NameBot AltNameBot` — tries candidates, saves token to keychain
2. `graphis start-bot @NewBot` — I run this; required before bot can message you
3. `echo "test" | deltos` — verify delivery
4. `graphis delete @OldBot` — retire the old bot

## Auth workflow (agent-friendly two-step)

```bash
# I run step 1:
graphis auth +85261872354
# → "Code sent to +85261872354. Give me the code..."

# User checks Telegram app, tells me the code. I run step 2:
graphis auth-complete 21620
# → "Signed in successfully!" (or "Signed in successfully with 2FA!")

# Session saved — no re-auth needed unless session.bin is deleted.
```

State persisted between steps: `pending-auth.json` holds `{phone, phone_code_hash, dc}`.

## Gotchas

- **DC migration** — Terry's phone is on Telegram DC5. `auth` handles this automatically (reconnects to `91.108.56.130:443`). DC is saved to `dc.txt` so all subsequent commands use the right DC. If you delete `dc.txt` and get transport errors, recreate it: `echo "5" > ~/.local/share/graphis/dc.txt`.
- **Session file encodes auth key but NOT the DC address** — grammers does not honour the session's DC on reconnect; `dc.txt` is the source of truth for which server to connect to.
- **Transport error `-404`** — means wrong DC. Check `dc.txt` exists and contains `5`.
- **Stale session after failed auth** — if auth-complete fails with a transport error, delete `session.bin` and `pending-auth.json` and restart from `graphis auth`.
- **Send `/start` to new bots** — Telegram requires users to initiate contact. `deltos` returns "chat not found" until done. Use `graphis start-bot @BotName` — don't rely on doing it manually.
- **CamelCase usernames preferred** — e.g. `TekmarBot` not `tekmar_bot`.
- **Popular names are taken** — try 3-4 candidates. StrixBot, SemaBot, PraecoBot, VoxBot, RemaBot, OssaBot, FamaBot all taken (Mar 2026). TekmarBot was available.
- **BotFather parsing** — relies on BotFather's response text. If BotFather changes phrasing, the create/delete flow may break.
- **macOS only** — keychain integration uses `security` CLI.
- **grammers 0.7 does not handle PHONE_MIGRATE** — neither `invoke()` nor `request_login_code()` auto-migrate. Must handle manually via `InitParams::server_addr`. See `~/docs/solutions/agent-cli-patterns.md`.
- **LoginToken fields are `pub(crate)`** — cannot extract `phone_code_hash` from the high-level type; use raw TL `auth.SendCode` instead which returns the hash directly.

## Current bot

`@TekmarBot` — Greek *tekmar* "a fixed sign, token". Created Mar 2026.
Token in keychain: `telegram-bot-token`.
