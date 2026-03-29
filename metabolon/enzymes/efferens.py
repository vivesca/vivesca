"""efferens — shared notice board for inter-process messages.

Tools:
  efferens_list  — list messages, optional recipient filter
  efferens_post  — post a message to the notice board
  efferens_count — count unread messages
"""



from metabolon.organelles.effector import run_cli  # noqa: E402

from fastmcp.tools import tool  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

BINARY = "/Users/terry/.local/bin/efferens"


@tool(
    name="efferens_list",
    description="List messages on the notice board, optionally filtered by recipient.",
    annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
)
def efferens_list(to: str = "") -> str:
    """List messages on the efferens notice board.

    Args:
        to: Optional recipient filter. Returns all messages if omitted.
    """
    args = ["list"]
    if to:
        args += ["--to", to]
    return run_cli(BINARY, args)


@tool(
    name="efferens_post",
    description="Post a message to the notice board.",
    annotations=ToolAnnotations(destructiveHint=False, idempotentHint=False),
)
def efferens_post(
    message: str,
    sender: str,
    to: str = "terry",
    severity: str = "info",
    subject: str = "",
) -> str:
    """Post a message to the efferens notice board.

    Args:
        message: The message body.
        sender: Who is sending the message (--from).
        to: Recipient (default "terry").
        severity: One of "action", "info", "warning" (default "info").
        subject: Optional subject line.
    """
    args = ["post", message, "--from", sender, "--to", to, "--severity", severity]
    if subject:
        args += ["--subject", subject]
    return run_cli(BINARY, args)


@tool(
    name="efferens_count",
    description="Count unread messages on the notice board.",
    annotations=ToolAnnotations(destructiveHint=False, idempotentHint=True),
)
def efferens_count() -> str:
    """Count unread messages on the efferens notice board."""
    return run_cli(BINARY, ["count"])
