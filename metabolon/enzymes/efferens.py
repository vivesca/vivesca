from __future__ import annotations

"""efferens — shared notice board for inter-process messages."""


from pathlib import Path

from metabolon.organelles.effector import run_cli

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

BINARY = str(Path.home() / ".local/bin/efferens")


@tool(
    name="efferens",
    description="Internal messaging. Actions: list|post|count",
    annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
)
def efferens(
    action: str,
    message: str = "",
    sender: str = "",
    to: str = "terry",
    severity: str = "info",
    subject: str = "",
) -> str:
    """Dispatch efferens notice-board actions.

    Args:
        action: One of "list", "post", "count".
        message: Message body (used by "post").
        sender: Who is sending the message, --from (used by "post").
        to: Recipient filter (used by "list" and "post", default "terry").
        severity: One of "action", "info", "warning" (used by "post", default "info").
        subject: Optional subject line (used by "post").
    """
    if action == "list":
        args = ["list"]
        if to:
            args += ["--to", to]
        return run_cli(BINARY, args)

    if action == "post":
        args = ["post", message, "--from", sender, "--to", to, "--severity", severity]
        if subject:
            args += ["--subject", subject]
        return run_cli(BINARY, args)

    if action == "count":
        return run_cli(BINARY, ["count"])

    return f"Unknown action: {action}. Use list, post, or count."
