"""electroreception — read iMessage/SMS from macOS chat.db.

Tools:
  electroreception_read   — fetch recent messages with optional filters
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timedelta

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion

_DB = os.path.expanduser("~/Library/Messages/chat.db")


def _extract_text(blob: bytes | None) -> str | None:
    """Extract text from NSAttributedString attributedBody blob."""
    if not blob:
        return None
    try:
        decoded = blob.decode("utf-8", errors="ignore")
        runs = re.split(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", decoded)
        meta = re.compile(
            r"streamtyped|NSString|NSMutable|NSObject|NSDictionary|NSArray|"
            r"NSAttributed|NSParagraph|NSColor|NSFont|NSNumber|NSValue|NSData|"
            r"__kIM|\$classname|\$classes|\$class|XDateTime|XAuthCode"
        )
        for r in runs:
            r = r.strip()
            if len(r) < 3 or meta.search(r):
                continue
            if r.startswith("+") and len(r) > 2:
                r = r[2:]
            r = r.strip()
            if len(r) >= 2:
                return r
        return None
    except Exception:
        return None


class ElectroreceptionResult(Secretion):
    """iMessage/SMS messages from macOS chat.db."""

    messages: list[dict]
    count: int


@tool(
    name="electroreception_read",
    description="Read iMessages/SMS from macOS chat.db. Filter by sender, days, or text.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def electroreception_read(
    limit: int = 20,
    sender: str = "",
    days: int = 0,
    query: str = "",
    incoming_only: bool = False,
) -> ElectroreceptionResult:
    """Read recent iMessages/SMS from local macOS database.

    Args:
        limit: Max messages to return (default 20).
        sender: Filter by sender substring (e.g. "MoxBank", "+852").
        days: Only messages from last N days (0 = no limit).
        query: Search message text content.
        incoming_only: If True, exclude sent messages.
    """
    if not os.path.exists(_DB):
        return ElectroreceptionResult(
            messages=[{"error": "chat.db not found — Messages must be enabled on this Mac"}],
            count=0,
        )

    where: list[str] = []
    if incoming_only:
        where.append("m.is_from_me = 0")
    if sender:
        safe = sender.replace("'", "''")
        where.append(f"h.id LIKE '%{safe}%'")
    if days:
        cutoff = datetime.now() - timedelta(days=days)
        apple_ns = int((cutoff.timestamp() - 978307200) * 1_000_000_000)
        where.append(f"m.date > {apple_ns}")

    where_clause = f"WHERE {' AND '.join(where)}" if where else ""

    sql = f"""
        SELECT m.rowid,
               datetime(m.date/1000000000 + 978307200, 'unixepoch', 'localtime') as dt,
               CASE WHEN m.is_from_me = 1 THEN 'Me'
                    ELSE coalesce(h.id, 'Unknown') END as sender,
               m.text,
               m.attributedBody,
               m.is_from_me
        FROM message m
        LEFT JOIN handle h ON m.handle_id = h.rowid
        {where_clause}
        ORDER BY m.date DESC
        LIMIT {limit}
    """

    conn = sqlite3.connect(_DB)
    cur = conn.cursor()
    cur.execute(sql)

    results = []
    for row in cur.fetchall():
        rowid, dt, sender_id, text, body, from_me = row
        content = text or _extract_text(body)
        if not content:
            continue
        if query and query.lower() not in content.lower():
            continue
        results.append(
            {
                "dt": dt,
                "sender": sender_id,
                "text": content,
                "from_me": bool(from_me),
            }
        )

    conn.close()
    return ElectroreceptionResult(messages=results, count=len(results))
