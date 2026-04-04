
"""gap_junction — WhatsApp messaging via wacli.

Actions: read|search|draft|list_chats|sync_status
Absorbs: gap_junction (ligand_*), keryx (keryx_*), receptor (receptor_*).
"""


from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion

GAP_JUNCTION_CONTACTS = {"tara", "mum", "dad", "brother", "sister", "yujie"}


class GapJunctionResult(Secretion):
    output: str


_ACTIONS = (
    "read — read a conversation with a contact. Requires: name. Optional: limit. "
    "search — search messages by text. Requires: query. Optional: name, limit. "
    "draft — draft a message (NEVER sends). Requires: name, message. "
    "list_chats — list recent chats. Optional: limit. "
    "sync_status — check wacli sync daemon status."
)


@tool(
    name="gap_junction",
    description=f"WhatsApp messaging. Actions: {_ACTIONS}",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def gap_junction(
    action: str,
    name: str = "",
    message: str = "",
    query: str = "",
    limit: int = 20,
) -> GapJunctionResult:
    """Unified WhatsApp tool."""
    action = action.lower().strip()

    if action == "read":
        if not name:
            return GapJunctionResult(output="read requires: name")
        from metabolon.organelles.gap_junction import receive_signals

        result = receive_signals(name, limit)
        prefix = "[gap_junction] " if name.lower() in GAP_JUNCTION_CONTACTS else ""
        return GapJunctionResult(output=f"{prefix}{result}")

    elif action == "search":
        if not query:
            return GapJunctionResult(output="search requires: query")
        from metabolon.organelles.gap_junction import search_signals

        result = search_signals(query, name, limit)
        return GapJunctionResult(output=result)

    elif action == "draft":
        if not name or not message:
            return GapJunctionResult(output="draft requires: name, message")
        from metabolon.organelles.gap_junction import compose_signal

        return GapJunctionResult(output=compose_signal(name, message))

    elif action == "list_chats":
        from metabolon.organelles.gap_junction import active_junctions

        return GapJunctionResult(output=active_junctions(limit))

    elif action == "sync_status":
        from metabolon.organelles.gap_junction import junction_status

        return GapJunctionResult(output=junction_status())

    else:
        return GapJunctionResult(
            output=f"Unknown action '{action}'. Valid: read, search, draft, list_chats, sync_status"
        )
