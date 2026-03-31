from __future__ import annotations

"""gap_junction — WhatsApp via wacli.

wacli CLI knowhow (Go binary, /opt/homebrew/bin/wacli):
  contacts search <name> --json  → {"success":bool, "data":[{JID, Phone, Name}]}
  messages list --chat <JID> --limit N --json → {"success":bool, "data":{"messages":[{MsgID, Timestamp, FromMe, Text, ChatJID, SenderJID}]}}
  messages search <query> --json [--chat JID] [--after/--before YYYY-MM-DD] → same shape as list
  chats --limit N                → human-readable chat list
  send --to <JID> <message>      → INTERACTIVE ONLY, never call from subprocess
  sync --once                    → one-shot sync, exits when idle
  sync status                    → daemon status

Contacts have multiple JIDs: phone (xxx@s.whatsapp.net) + LID (xxx@lid).
Messages must be fetched from all JIDs and merged/deduped by MsgID.
"""

