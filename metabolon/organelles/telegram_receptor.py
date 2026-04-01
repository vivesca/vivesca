from __future__ import annotations

"""telegram_receptor — Telegram message reading via Telethon (user client API).

Bot API can only see incoming messages. Reading sent messages (e.g. overnight
heartbeat/golem notifications) requires the user client API.

Auth: one-time interactive phone + OTP via Telethon. Session file persists at
~/.config/telethon/vivesca.session.

Credentials: TELEGRAM_API_ID, TELEGRAM_API_HASH from env (set in .zshenv.local).
"""

import asyncio
import os
from pathlib import Path

SESSION_DIR = Path.home() / ".config" / "telethon"
SESSION_NAME = "vivesca"


def _get_client():
    """Create a Telethon client (lazy import)."""
    from telethon import TelegramClient

    api_id = int(os.environ.get("TELEGRAM_API_ID", "0"))
    api_hash = os.environ.get("TELEGRAM_API_HASH", "")
    if not api_id or not api_hash:
        raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set")

    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    session_path = str(SESSION_DIR / SESSION_NAME)
    return TelegramClient(session_path, api_id, api_hash)


def _format_message(msg) -> str:
    """Format a single Telethon message for display."""
    ts = msg.date.strftime("%Y-%m-%d %H:%M") if msg.date else "?"
    sender = "me" if msg.out else "them"
    text = msg.text or "[media/non-text]"
    return f"{ts}  {sender}: {text}"


async def _read_chat_async(chat: str, limit: int = 30) -> str:
    """Read recent messages from a chat."""
    client = _get_client()
    async with client:
        entity = await client.get_entity(chat)
        messages = await client.get_messages(entity, limit=limit)
        if not messages:
            return "No messages found"
        msgs = messages if isinstance(messages, list) else [messages]
        lines = [_format_message(m) for m in reversed(msgs)]
        return "\n".join(lines)


async def _search_async(query: str, chat: str = "", limit: int = 20) -> str:
    """Search messages by text, optionally scoped to a chat."""
    client = _get_client()
    async with client:
        entity = None
        if chat:
            entity = await client.get_entity(chat)
        messages = await client.get_messages(
            entity, search=query, limit=limit
        )
        if not messages:
            return f"No messages matching '{query}'"
        msgs = messages if isinstance(messages, list) else [messages]
        lines = [_format_message(m) for m in reversed(msgs)]
        return "\n".join(lines)


async def _list_chats_async(limit: int = 20) -> str:
    """List recent dialogs/chats."""
    client = _get_client()
    async with client:
        dialogs = await client.get_dialogs(limit=limit)
        lines = []
        for d in dialogs:
            unread = f" [{d.unread_count} unread]" if d.unread_count else ""
            lines.append(f"{d.name or d.id}{unread}")
        return "\n".join(lines) if lines else "No chats"


async def _auth_check_async() -> str:
    """Check if Telethon session is authenticated."""
    client = _get_client()
    async with client:
        me = await client.get_me()
        if me:
            name = getattr(me, "first_name", None) or str(getattr(me, "id", "unknown"))
            phone = getattr(me, "phone", None) or "no phone"
            return f"Authenticated as: {name} ({phone})"
        return "Not authenticated — run interactive login"


def _run(coro):
    """Run an async coroutine, handling existing event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result(timeout=30)
    return asyncio.run(coro)


# --- Public sync API (matches gap_junction pattern) ---


def read_chat(chat: str = "me", limit: int = 30) -> str:
    """Read recent messages. chat='me' for Saved Messages (bot notifications land here)."""
    return _run(_read_chat_async(chat, limit))


def search_messages(query: str, chat: str = "", limit: int = 20) -> str:
    """Search messages by text."""
    return _run(_search_async(query, chat, limit))


def list_chats(limit: int = 20) -> str:
    """List recent chats/dialogs."""
    return _run(_list_chats_async(limit))


def auth_status() -> str:
    """Check authentication status."""
    return _run(_auth_check_async())
