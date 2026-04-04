"""telegram_receptor — Read Telegram messages via user client API.

Actions: read|search|list_chats|auth_status
Mirrors gap_junction pattern (WhatsApp reading).
"""

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion


class TelegramResult(Secretion):
    output: str


_ACTIONS = (
    "read — read recent messages from a chat. Optional: chat (default 'me' = Saved Messages / bot chat), limit. "
    "search — search messages by text. Requires: query. Optional: chat, limit. "
    "list_chats — list recent Telegram chats. Optional: limit. "
    "auth_status — check Telethon authentication status."
)


@tool(
    name="telegram_receptor",
    description=f"Read Telegram messages. Actions: {_ACTIONS}",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def telegram_receptor(
    action: str,
    chat: str = "me",
    query: str = "",
    limit: int = 30,
) -> TelegramResult:
    """Unified Telegram reading tool."""
    action = action.lower().strip()

    if action == "read":
        from metabolon.organelles.telegram_receptor import read_chat

        result = read_chat(chat, limit)
        return TelegramResult(output=result)

    elif action == "search":
        if not query:
            return TelegramResult(output="search requires: query")
        from metabolon.organelles.telegram_receptor import search_messages

        result = search_messages(query, chat, limit)
        return TelegramResult(output=result)

    elif action == "list_chats":
        from metabolon.organelles.telegram_receptor import list_chats

        result = list_chats(limit)
        return TelegramResult(output=result)

    elif action == "auth_status":
        from metabolon.organelles.telegram_receptor import auth_status

        result = auth_status()
        return TelegramResult(output=result)

    else:
        return TelegramResult(
            output=f"Unknown action: {action}. Use: read, search, list_chats, auth_status"
        )
