"""gap_junction — WhatsApp via wacli (formerly keryx).

Endosymbiosis: Rust binary → Python organelle.
Still wraps wacli (Go binary) for WhatsApp protocol.
The Rust layer was just JSON parsing — Python handles that directly.
"""

import json
import subprocess

WACLI = "/opt/homebrew/bin/wacli"

# Gap junction contacts: direct, bidirectional, low-friction
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


def _wacli_json(args: list[str], timeout: int = 15) -> list[dict]:
    """Call wacli and parse JSON output."""
    raw = _wacli(args, timeout)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def contact_type(name: str) -> str:
    """Classify: gap_junction (close) or receptor (formal)."""
    return "gap_junction" if name.lower() in GAP_JUNCTION_CONTACTS else "receptor"


def read_messages(name: str, limit: int = 20) -> str:
    """Read messages from a conversation."""
    return _wacli(["read", name, "--limit", str(limit)])


def draft_message(name: str, message: str) -> str:
    """Draft a message (NEVER sends — returns shell command)."""
    return _wacli(["send", name, message, "--copy"])


def list_chats(limit: int = 20) -> str:
    """List recent conversations."""
    return _wacli(["chats", "--limit", str(limit)])


def sync_status() -> str:
    """Check wacli sync daemon status."""
    return _wacli(["sync", "status"])
