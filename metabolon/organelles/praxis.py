from __future__ import annotations

"""praxis — Praxis.md TODO list management (formerly todo-cli).

Endosymbiosis: uv/Python script (vivesca/effectors/todo-cli) → Python organelle.
The original script delegated parsing to a shared gather module and added
CLI argument dispatch on top. This organelle exposes the same operations as
direct Python functions that the /todo skill and emit_praxis tool can import
without shelling out.

Core functions: today, upcoming, overdue, someday, all_items, spare, clean, stats.
"""


import re
from datetime import datetime, timedelta
from pathlib import Path

HOME = Path.home()
NOTES = HOME / "notes"
PRAXIS = NOTES / "Praxis.md"
PRAXIS_ARCHIVE = NOTES / "Praxis Archive.md"


def _parse_date(date_str: str | None):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _is_overdue(item: dict, today_date) -> bool:
    d = _parse_date(item.get("due"))
    return bool(d and d < today_date)


def _today_date():
    from metabolon.pinocytosis import current_date

    return _parse_date(current_date()["iso"])


def _read_all() -> dict:
    from metabolon.pinocytosis import recall_todo

    return recall_todo()


def _read_today() -> dict:
    from metabolon.pinocytosis import recall_todo_today

    return recall_todo_today()


def today() -> dict:
    """Return tasks due today (overdue + today), JSON-serialisable.

    Returns:
        {"date": "YYYY-MM-DD", "items": [...], "today_count": N, "overdue_count": N}
    """
    today_date = _today_date()
    data = _read_today()
    if not data["available"]:
        return {"error": data["error"]}

    items = data["items"]
    overdue_count = sum(1 for i in items if _is_overdue(i, today_date))
    return {
        "date": today_date.isoformat() if today_date else "",
        "items": items,
        "today_count": len(items),
        "overdue_count": overdue_count,
    }


def upcoming(days: int = 14) -> dict:
    """Return non-someday tasks due or scheduled within `days` days.

    Returns:
        {"date": "YYYY-MM-DD", "items": [...], "total_count": N, "overdue_count": N}
    """
    today_date = _today_date()
    end_date = today_date + timedelta(days=days)
    data = _read_all()
    if not data["available"]:
        return {"error": data["error"]}

    items = []
    for item in data["items"]:
        if item.get("done"):
            continue
        if "`someday`" in item.get("raw", ""):
            continue
        d = _parse_date(item.get("due"))
        w = _parse_date(item.get("when"))
        earliest = None
        for cand in (d, w):
            if cand and today_date <= cand <= end_date and (earliest is None or cand < earliest):
                earliest = cand
        if earliest is not None:
            item = dict(item)
            item["_sort_date"] = earliest
            items.append(item)

    items.sort(key=lambda x: x["_sort_date"])
    for i in items:
        i.pop("_sort_date", None)

    overdue_count = sum(1 for i in items if _is_overdue(i, today_date))
    return {
        "date": today_date.isoformat() if today_date else "",
        "items": items,
        "total_count": len(items),
        "overdue_count": overdue_count,
    }


def overdue() -> dict:
    """Return all overdue (not done, due < today) items.

    Returns:
        {"date": "YYYY-MM-DD", "items": [...], "total_count": N, "overdue_count": N}
    """
    today_date = _today_date()
    data = _read_all()
    if not data["available"]:
        return {"error": data["error"]}

    items = []
    for item in data["items"]:
        if item.get("done"):
            continue
        d = _parse_date(item.get("due"))
        if d and d < today_date:
            item = dict(item)
            item["_sort_date"] = d
            items.append(item)

    items.sort(key=lambda x: x["_sort_date"])
    for i in items:
        i.pop("_sort_date", None)

    return {
        "date": today_date.isoformat() if today_date else "",
        "items": items,
        "total_count": len(items),
        "overdue_count": len(items),
    }


def someday() -> dict:
    """Return items tagged `someday` (not done).

    Returns:
        {"date": "YYYY-MM-DD", "items": [...], "total_count": N, "overdue_count": N}
    """
    today_date = _today_date()
    data = _read_all()
    if not data["available"]:
        return {"error": data["error"]}

    items = [i for i in data["items"] if not i.get("done") and "`someday`" in i.get("raw", "")]
    overdue_count = sum(1 for i in items if _is_overdue(i, today_date))
    return {
        "date": today_date.isoformat() if today_date else "",
        "items": items,
        "total_count": len(items),
        "overdue_count": overdue_count,
    }


def all_items() -> dict:
    """Return all incomplete items.

    Returns:
        {"date": "YYYY-MM-DD", "items": [...], "total_count": N, "overdue_count": N}
    """
    today_date = _today_date()
    data = _read_all()
    if not data["available"]:
        return {"error": data["error"]}

    items = [i for i in data["items"] if not i.get("done")]
    overdue_count = sum(1 for i in items if _is_overdue(i, today_date))
    return {
        "date": today_date.isoformat() if today_date else "",
        "items": items,
        "total_count": len(items),
        "overdue_count": overdue_count,
    }


def spare() -> dict:
    """Return items in the Spare Capacity section.

    Returns:
        {"date": "YYYY-MM-DD", "items": [...], "total_count": N, "overdue_count": N}
    """
    from metabolon.pinocytosis import recall_todo

    today_date = _today_date()
    data = recall_todo(sections=["Spare Capacity"])
    if not data["available"]:
        return {"error": data["error"]}

    items = [i for i in data["items"] if not i.get("done")]
    overdue_count = sum(1 for i in items if _is_overdue(i, today_date))
    return {
        "date": today_date.isoformat() if today_date else "",
        "items": items,
        "total_count": len(items),
        "overdue_count": overdue_count,
    }


def clean() -> dict:
    """Archive completed items from Praxis.md to Praxis Archive.md.

    Stamps completed items with `done:YYYY-MM-DD` if not already present,
    groups them under the current month heading in the archive.

    Returns:
        {"archived": N, "items": ["- [x] text `done:...`", ...]}
    """
    if not PRAXIS.exists():
        return {"error": "No Praxis.md found"}

    lines = PRAXIS.read_text(encoding="utf-8").splitlines(keepends=True)
    today = datetime.now().strftime("%Y-%m-%d")
    month_header = datetime.now().strftime("%B %Y")

    completed = []
    remaining = []
    skip_children = False

    for line in lines:
        stripped = line.rstrip()
        if re.match(r"^- \[[xX]\]", stripped):
            entry = stripped
            if "done:" not in entry:
                entry += f" `done:{today}`"
            completed.append(entry)
            skip_children = True
            continue

        if skip_children:
            if re.match(r"^  +- ", stripped):
                continue
            else:
                skip_children = False

        remaining.append(line)

    if not completed:
        return {"archived": 0, "items": []}

    archive_text = PRAXIS_ARCHIVE.read_text(encoding="utf-8") if PRAXIS_ARCHIVE.exists() else ""
    month_pattern = f"## {month_header}"

    if month_pattern in archive_text:
        idx = archive_text.index(month_pattern) + len(month_pattern)
        nl = archive_text.find("\n", idx)
        if nl == -1:
            nl = len(archive_text)
        insert_text = "\n" + "\n".join(completed)
        archive_text = archive_text[:nl] + insert_text + archive_text[nl:]
    else:
        first_section = archive_text.find("\n## ")
        if first_section >= 0:
            insert_text = f"\n{month_pattern}\n\n" + "\n".join(completed) + "\n"
            archive_text = (
                archive_text[:first_section] + insert_text + archive_text[first_section:]
            )
        else:
            if archive_text and not archive_text.endswith("\n"):
                archive_text += "\n"
            archive_text += f"\n{month_pattern}\n\n" + "\n".join(completed) + "\n"

    PRAXIS.write_text("".join(remaining), encoding="utf-8")
    PRAXIS_ARCHIVE.write_text(archive_text, encoding="utf-8")

    return {"archived": len(completed), "items": completed}


def stats() -> dict:
    """Return summary statistics for Praxis.md.

    Returns:
        {
            "total": N, "overdue": N, "due_this_week": N,
            "someday": N, "symbiont_stimuli": N, "host_stimuli": N, "recurring": N
        }
    """
    today_date = _today_date()
    week_end = today_date + timedelta(days=7)
    data = _read_all()
    if not data["available"]:
        return {"error": data["error"]}

    items = [i for i in data["items"] if not i.get("done")]
    result = {
        "total": len(items),
        "overdue": 0,
        "due_this_week": 0,
        "someday": 0,
        "symbiont_stimuli": 0,
        "host_stimuli": 0,
        "recurring": 0,
    }

    for i in items:
        d = _parse_date(i.get("due"))
        if d:
            if d < today_date:
                result["overdue"] += 1
            if today_date <= d <= week_end:
                result["due_this_week"] += 1
        if "`someday`" in i.get("raw", ""):
            result["someday"] += 1
        if i.get("agent") == "claude":
            result["symbiont_stimuli"] += 1
        if i.get("agent") == "terry":
            result["host_stimuli"] += 1
        if i.get("recurring"):
            result["recurring"] += 1

    return result
