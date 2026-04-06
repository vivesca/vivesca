---
name: deltos
description: Send text/code snippets or image files to Telegram for mobile copy-paste. Use when relaying content to phone. "send to telegram", "deltos", "copy-paste relay"
effort: low
---

# deltos

Rust CLI that sends text/code to Telegram as HTML code blocks. Primary copy-paste relay — open your Telegram on mobile and tap to copy.

## Usage

```bash
# Pipe content (most common)
echo "text" | deltos
echo "text" | deltos "label"

# Inline arg (TTY only — won't work in scripts)
deltos "text"
deltos "label" "content"

# Plain mode (URLs, no <pre> wrapper)
echo "https://example.com" | deltos --plain "link"

# Send an image file (--photo)
deltos --photo ~/tmp/qrcode.png "optional caption"
deltos --photo ~/screenshots/chart.png
```

## Config

Credentials live in macOS Keychain. Already set from tg-clip era.

```bash
# Verify
security find-generic-password -s telegram-bot-token -w
security find-generic-password -s telegram-chat-id -w

# Set (if needed)
security add-generic-password -s telegram-bot-token -a "$USER" -w "YOUR_TOKEN" -U
security add-generic-password -s telegram-chat-id  -a "$USER" -w "YOUR_CHAT_ID" -U
```

## Telegram notification triage

`deltos` is a **copy-paste relay** — you trigger it manually to move content to mobile.

Telegram **bot push notifications** (via Bot API in CLIs/LaunchAgents) are a different channel and should be used sparingly:

| Use Telegram push | Use log/vault instead |
|-------------------|-----------------------|
| Health alert (HRV, sleep threshold breach) | Scheduled digest (regulatory monitor, job alerts) |
| Urgent time gate (interview confirmed, offer deadline) | Daily cron output |
| One-off human action needed now | Background research results |
| System failure requiring immediate attention | Routine status updates |

**Rule:** If it runs on a schedule and the world won't end if you see it an hour later → write to log, surface via `kairos`/`cardo`. Reserve Telegram push for interrupts.

## Gotchas

- **Inline arg only works in a real TTY.** Scripts and agent shells are non-TTY — `deltos "text"` will wait for stdin. Use `echo "text" | deltos` in scripts.
- **Single arg = label, not content.** `subprocess.run(["deltos", msg])` treats `msg` as the LABEL (bold header) with no content — message sends empty. In Python scripts: `subprocess.run(["deltos", "--plain"], input=msg, text=True)` to pipe correctly.
- **Rate limit:** 1s gap enforced via `/tmp/deltos.lock`. Parallel sends will queue.
- **HTML in content:** `&`, `<`, `>` are escaped automatically. No double-escaping needed.

## Source

`~/code/deltos/` — standalone crate (excluded from `~/code/` workspace).

```bash
cd ~/code/deltos && cargo build --release && cp target/release/deltos ~/bin/deltos
```
