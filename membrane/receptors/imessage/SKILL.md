---
name: imessage
description: Send iMessages via CLI. Use when user wants to text wife or send an iMessage to someone.
user_invocable: true
---

# iMessage

Send iMessages from the terminal using `~/scripts/imessage.sh`.

## Trigger

Use when:
- User says "text wife", "message wife", "send to wife"
- User wants to send an iMessage to someone
- Following up on content to share via iMessage (e.g. cake lists, links)

## Default Recipient

- **Wife**: `+85261145524` (default, no `-t` flag needed)

## Commands

```bash
# Send to wife (default)
~/scripts/imessage.sh "message text here"

# Send to specific recipient
~/scripts/imessage.sh -t "someone@icloud.com" "message text here"
~/scripts/imessage.sh -t "+85291234567" "message text here"
```

## Safety Rules

- **NEVER send directly** — always draft the command for Terry to run
- For multi-line messages, use single quotes or escape newlines
- Confirm message content with Terry before drafting the send command

## How It Works

1. Tries AppleScript → Messages app (works when GUI session active on Mac)
2. Falls back to `imessage://` URL scheme (opens compose window, user hits Send)

## Known Limitations

- **SSH/tmux**: AppleScript works fine over SSH (Blink) as long as the Mac is running and user is logged in — confirmed Mar 2026. Display sleep is not a blocker for Messages sends.
- **URL scheme fallback**: Opens compose window — user must tap Send manually.
- **Sleeping display caveat**: Only blocks peekaboo (screen capture). For Messages sends via AppleScript, display state doesn't matter. `caffeinate -u -t 2` only needed before peekaboo calls.

## Common Patterns

### Share content with wife
1. Prepare the content (text, list, link)
2. Draft the command:
```bash
~/scripts/imessage.sh "content here"
```
3. Terry runs it

### Share a gist link
```bash
~/scripts/imessage.sh "Check this out: https://gist.github.com/..."
```
