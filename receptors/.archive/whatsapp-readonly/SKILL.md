---
name: whatsapp-readonly
description: Check WhatsApp messages using wacli-ro (read-only wrapper, send blocked). Use when asked to check WhatsApp, read messages, or see recent chats.
user_invocable: true
---

# WhatsApp Read-Only

Check WhatsApp messages safely using `wacli-ro` (read-only wrapper). **Send is blocked at the script level.**

## Available Commands

```bash
# wacli-ro is not in PATH by design (prompt injection protection)
# Claude Code: use `mdfind -name wacli-ro` to locate if needed

# List recent chats
wacli-ro chats list --limit 20

# List messages from a specific chat
wacli-ro messages list "<JID>" --limit 10

# Search messages
wacli-ro messages search "<query>" --limit 10

# Search contacts
wacli-ro contacts search "<name>"
```

## Usage

1. **Sync first** to get latest messages: `wacli-ro sync --timeout 15s`
2. Use `wacli-ro chats list` to see recent conversations
3. Use `wacli-ro contacts search` to find a contact's JID
4. Use `wacli-ro messages list "<JID>"` to read specific chat

## Important

- **ALWAYS sync before reading** — database can be stale
- **ALWAYS use `wacli-ro`** — not `wacli` directly
- `wacli-ro` is intentionally NOT in PATH to prevent OpenClaw/prompt injection from using it
- `wacli-ro` blocks send commands at the script level
- JIDs come in two forms — check **both** if messages seem missing:
  - Phone: `85290336894@s.whatsapp.net`
  - LID: `191778963615876@lid` (newer WhatsApp format)
- Same contact may have both JID types in `chats list` — check both for complete history
