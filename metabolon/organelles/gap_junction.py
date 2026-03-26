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


def receive_signals(name: str, limit: int = 20) -> str:
    """Read messages from a conversation."""
    return _wacli(["read", name, "--limit", str(limit)])


def compose_signal(name: str, message: str) -> str:
    """Draft a message (NEVER sends — returns shell command)."""
    return _wacli(["send", name, message, "--copy"])


def active_junctions(limit: int = 20) -> str:
    """List recent conversations."""
    return _wacli(["chats", "--limit", str(limit)])


def junction_status() -> str:
    """Check wacli sync daemon status."""
    return _wacli(["sync", "status"])


def sync_catchup() -> str:
    """Run a one-shot sync (replaces `keryx sync catchup`). Exits when idle."""
    return _wacli(["sync", "--once"], timeout=120)


def _cli() -> None:
    """CLI entry point: gap_junction sync catchup → wacli sync --once.

    Interface mirrors the old `keryx sync catchup` command so LaunchAgents
    and scripts can call this without knowing about wacli internals.

    Usage:
        python -m metabolon.organelles.gap_junction sync catchup
    """
    import sys

    args = sys.argv[1:]

    if args == ["sync", "catchup"]:
        try:
            out = sync_catchup()
            print(out)
            sys.exit(0)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        print(
            "usage: gap_junction sync catchup",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    _cli()
