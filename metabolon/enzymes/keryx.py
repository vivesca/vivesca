"""keryx — WhatsApp messaging via wacli.

Tools:
  keryx_read_messages — read a conversation
  keryx_draft_send    — draft a message (NEVER sends directly)
  keryx_list_chats    — list recent chats
  keryx_sync_status   — check the wacli daemon
"""



from metabolon.organelles.effector import run_cli  # noqa: E402

from fastmcp.tools import tool  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

BINARY = "~/bin/keryx"


@tool(
    name="keryx_read_messages",
    description="Read a WhatsApp conversation with a contact. Merges phone + LID JID threads.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def keryx_read_messages(name: str, limit: int = 20) -> str:
    """Read WhatsApp conversation with a contact.

    Args:
        name: Contact name (case-insensitive substring match).
        limit: Max messages to return (default 20).
    """
    return run_cli(BINARY, ["read", name, "--limit", str(limit)])


@tool(
    name="keryx_draft_send",
    description=(
        "Draft a WhatsApp message. Returns a shell block for Terry to execute manually. "
        "NEVER sends directly — output is a launchctl stop/send/start sequence."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def keryx_draft_send(name: str, message: str) -> str:
    """Draft a WhatsApp message (does not send).

    Args:
        name: Contact name to send to.
        message: The message text.
    """
    return run_cli(BINARY, ["send", name, message, "--copy"])


@tool(
    name="keryx_list_chats",
    description="List recent WhatsApp chats.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def keryx_list_chats(limit: int = 20) -> str:
    """List recent WhatsApp chats.

    Args:
        limit: Max chats to return (default 20).
    """
    return run_cli(BINARY, ["chats", "--limit", str(limit)])


@tool(
    name="keryx_sync_status",
    description="Check the wacli sync daemon status.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def keryx_sync_status() -> str:
    """Check the wacli sync daemon status."""
    return run_cli(BINARY, ["sync", "status"])
