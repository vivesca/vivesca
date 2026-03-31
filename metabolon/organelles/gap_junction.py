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

import json
import subprocess

WACLI = "/opt/homebrew/bin/wacli"

GAP_JUNCTION_CONTACTS = {"tara", "mum", "dad", "brother", "sister", "yujie"}


def _wacli(args: list[str], timeout: int = 15) -> str:
    """Call wacli CLI."""
    r = subprocess.run(
        [WACLI, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if r.returncode != 0:
        raise ValueError(f"wacli failed: {r.stderr.strip()}")
    return r.stdout.strip()


def _wacli_json(args: list[str], timeout: int = 15) -> dict:
    """Call wacli with --json and parse. Returns raw parsed dict."""
    raw = _wacli(args, timeout)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _extract_messages(raw: dict) -> list[dict]:
    """Extract message list from wacli JSON envelope."""
    d = raw.get("data", {}) if isinstance(raw, dict) else {}
    return (d.get("messages") or []) if isinstance(d, dict) else []


def _extract_contacts(raw: dict) -> list[dict]:
    """Extract contact list from wacli JSON envelope."""
    d = raw.get("data", []) if isinstance(raw, dict) else []
    return d if isinstance(d, list) else []


def _dedup_sort(messages: list[dict], limit: int) -> list[dict]:
    """Deduplicate by MsgID, sort by Timestamp descending, cap at limit."""
    seen: set[str] = set()
    unique = []
    for m in messages:
        mid = m.get("MsgID", "")
        if mid and mid not in seen:
            seen.add(mid)
            unique.append(m)
    unique.sort(key=lambda m: m.get("Timestamp", ""), reverse=True)
    return unique[:limit]


def _format_messages(messages: list[dict], name: str) -> str:
    """Format messages for display."""
    lines = []
    for m in messages:
        ts = m.get("Timestamp", "")[:19]
        sender = "me" if m.get("FromMe") else name
        text = m.get("Text", "")
        lines.append(f"{ts}  {sender}: {text}")
    return "\n".join(lines) if lines else "No messages found"


# --- Contact resolution ---


def contact_type(name: str) -> str:
    """Classify: gap_junction (close) or receptor (formal)."""
    return "gap_junction" if name.lower() in GAP_JUNCTION_CONTACTS else "receptor"


def resolve_jids(name: str) -> list[str]:
    """Resolve a contact name to all matching JIDs (phone + LID)."""
    contacts = _extract_contacts(_wacli_json(["contacts", "search", name, "--json"]))
    return [c["JID"] for c in contacts if c.get("JID")]


# --- Message operations ---


def receive_signals(name: str, limit: int = 20) -> str:
    """Read messages from a conversation. Merges phone + LID JID threads."""
    jids = resolve_jids(name)
    if not jids:
        return f"No contact found for '{name}'"
    all_messages: list[dict] = []
    for jid in jids:
        raw = _wacli_json(["messages", "list", "--chat", jid, "--limit", str(limit), "--json"])
        all_messages.extend(_extract_messages(raw))
    return _format_messages(_dedup_sort(all_messages, limit), name)


def search_signals(query: str, name: str = "", limit: int = 20) -> str:
    """Search messages by text. Optionally scope to a contact."""
    args = ["messages", "search", query, "--limit", str(limit), "--json"]
    if name:
        jids = resolve_jids(name)
        if not jids:
            return f"No contact found for '{name}'"
        all_messages: list[dict] = []
        for jid in jids:
            raw = _wacli_json([*args, "--chat", jid])
            all_messages.extend(_extract_messages(raw))
        return _format_messages(_dedup_sort(all_messages, limit), name)
    raw = _wacli_json(args)
    msgs = _dedup_sort(_extract_messages(raw), limit)
    return _format_messages(msgs, "them")


# --- Draft (never sends) ---


def compose_signal(name: str, message: str) -> str:
    """Draft a message. NEVER sends — returns shell command for manual execution."""
    jids = resolve_jids(name)
    if not jids:
        return f"# No contact found for '{name}'"
    jid = jids[0]
    escaped = message.replace("'", "'\\''")
    return f"wacli send --to '{jid}' '{escaped}'"


# --- Chat list & sync ---


def active_junctions(limit: int = 20) -> str:
    """List recent conversations."""
    return _wacli(["chats", "list", "--limit", str(limit)])


def junction_status() -> str:
    """Check wacli sync daemon status."""
    return _wacli(["sync", "status"])


def sync_catchup() -> str:
    """Run a one-shot sync. Exits when idle."""
    return _wacli(["sync", "--once"], timeout=120)


# --- CLI entry point ---


def _cli() -> None:
    """CLI: gap_junction sync catchup → wacli sync --once."""
    import sys

    if sys.argv[1:] == ["sync", "catchup"]:
        try:
            print(sync_catchup())
        except ValueError as exc:
            msg = str(exc)
            if "store is locked" in msg:
                # Primary wacli-sync daemon is running and holding the lock.
                # Continuous sync is already covered — treat as success.
                print("catchup: daemon is running, sync covered — skipping", file=sys.stderr)
                sys.exit(0)
            print(f"error: {msg}", file=sys.stderr)
            sys.exit(1)
    else:
        print("usage: gap_junction sync catchup", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    _cli()
