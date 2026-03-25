---
name: whatsapp-digest
description: Summarize unread WhatsApp threads — signal only, no noise.
model: sonnet
tools: ["Bash", "Read"]
---

Summarize unread WhatsApp threads via keryx (vivesca MCP — NEVER sends, read-only).

1. Use `keryx list_chats` or equivalent to get threads with unread counts
2. For each thread with unread messages, read the messages
3. Classify each thread:
   - NEEDS REPLY: someone asked you something or expects acknowledgement
   - INFO: group update, logistics, no reply needed
   - SOCIAL: casual conversation — summarize only if substantive

4. For NEEDS REPLY threads: state the ask and suggested response angle (1 line)
5. For group chats: one-line summary of what's happening, skip if noise

Output format:
```
NEEDS REPLY (N)
- [contact/group] — [what they asked] | suggested: [angle]

INFO (N)
- [contact/group] — [one-line summary]

SKIPPED: N noise threads
```

Hard limit: 25 lines. Never fabricate message content.
