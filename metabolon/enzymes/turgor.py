"""tonus tool — session state. Actions: mark|status"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

TONUS = Path.home() / "epigenome" / "chromatin" / "Tonus.md"
HKT = timezone(timedelta(hours=8))

# Pattern: - [status] **Label.** description
ITEM_RE = re.compile(r"^- \[([^\]]+)\] \*\*(.+?)\*\*\s*(.*)", re.DOTALL)


def _read_tonus() -> str:
    return TONUS.read_text(encoding="utf-8")


def _write_tonus(content: str) -> None:
    tmp = TONUS.with_suffix(".md.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(TONUS)


@tool(
    name="tonus",
    description="Session state. Actions: mark|status",
    annotations=ToolAnnotations(readOnlyHint=False),
)
def tonus(
    action: str,
    label: str = "",
    item_status: str = "",
    description: str = "",
) -> dict:
    """Manage Tonus session state.

    Args:
        action: mark (update a progress item) or status (list items)
        label: Item label to match (fuzzy). Used by mark.
        item_status: New status (in-progress, done, queued). Empty = don't change. Used by mark.
        description: New description text. Empty = don't change. Used by mark.
    """
    if action == "mark":
        if not item_status and not description:
            return {"success": False, "message": "Nothing to update — provide item_status or description"}

        content = _read_tonus()
        lines = content.splitlines()
        matched = False
        label_lower = label.lower()

        for i, line in enumerate(lines):
            m = ITEM_RE.match(line)
            if not m:
                continue
            item_label = m.group(2).rstrip(".")
            if label_lower not in item_label.lower():
                continue

            old_status = m.group(1)
            old_desc = m.group(3)
            new_status = item_status or old_status
            new_desc = description or old_desc

            lines[i] = f"- [{new_status}] **{item_label}.** {new_desc}"
            matched = True
            break

        if not matched:
            if item_status and description:
                new_line = f"- [{item_status}] **{label}.** {description}"
                for i in range(len(lines) - 1, -1, -1):
                    if lines[i].startswith("<!--"):
                        lines.insert(i, new_line)
                        break
                else:
                    lines.append(new_line)
                matched = True
            else:
                return {
                    "success": False,
                    "message": f"No item matching '{label}' found. Provide both item_status and description to create new.",
                }

        now = datetime.now(HKT).strftime("%d/%m/%Y ~%H:%M HKT")
        for i, line in enumerate(lines):
            if line.startswith("<!-- last checkpoint:"):
                lines[i] = f"<!-- last checkpoint: {now} -->"
                break

        _write_tonus("\n".join(lines) + "\n")
        return {"success": True, "message": f"Updated '{label}'"}

    elif action == "status":
        content = _read_tonus()
        items = []
        for line in content.splitlines():
            m = ITEM_RE.match(line)
            if m:
                items.append(
                    {
                        "status": m.group(1),
                        "label": m.group(2).rstrip("."),
                        "description": m.group(3).strip(),
                    }
                )

        total = len(items)
        in_progress = sum(1 for i in items if i["status"] == "in-progress")
        done = sum(1 for i in items if i["status"] == "done")
        pressure = in_progress / max(total, 1)

        turgor = "normal"
        if pressure > 0.7:
            turgor = "HIGH — too many items in-progress, finish before starting"
        elif pressure < 0.2 and total > 0:
            turgor = "LOW — wilting, pick up pace or reduce scope"

        return {
            "items": items,
            "count": total,
            "turgor": turgor,
            "pressure": f"{in_progress} in-progress / {total} total ({pressure:.0%})",
            "done": done,
        }

    else:
        return {"success": False, "message": f"Unknown action '{action}'. Use mark or status."}
