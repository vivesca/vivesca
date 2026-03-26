"""pacemaker — reminder signaling (pacemaker = generates signals at scheduled intervals)."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Endosymbiosis: import the full moneo-py implementation directly.
# moneo-py lives at ~/code/moneo-py/moneo.py and is the canonical Python
# implementation of the Due app reminder manager. We inject its parent dir
# into sys.path so we can import it as a module — no subprocess required.
# ---------------------------------------------------------------------------

import argparse
import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

_MONEO_PY_DIR = Path.home() / "code" / "moneo-py"
if str(_MONEO_PY_DIR) not in sys.path:
    sys.path.insert(0, str(_MONEO_PY_DIR))

import moneo as _m  # noqa: E402 — path injection must precede this


# ---------------------------------------------------------------------------
# Public API — called directly from MCP tools (no subprocess)
# ---------------------------------------------------------------------------


def add(
    title: str,
    *,
    date: str | None = None,
    at: str | None = None,
    rel: str | None = None,
    due: str | None = None,
    recur: str | None = None,
    autosnooze: int | None = None,
    timezone: str = "Asia/Hong_Kong",
) -> str:
    """Add a Due reminder. Returns a confirmation string.

    Args:
        title: Reminder text.
        date: YYYY-MM-DD or 'today'/'tomorrow'.
        at: HH:MM time (combined with date or defaults to today).
        rel: Relative offset — '30m', '2h', '90s'.
        due: Combined date+time string — 'today 16:15', 'tomorrow 09:00'.
        recur: One of daily/weekly/monthly/quarterly/yearly.
        autosnooze: Snooze interval in minutes (1/5/10/15/30/60).
        timezone: IANA timezone, defaults to Asia/Hong_Kong.

    Returns:
        Human-readable confirmation string.

    Raises:
        _m.MoneoError: On validation failure or DB write error.
    """
    # Resolve --due shorthand into at + date
    if due is not None:
        if at is not None or date is not None:
            raise _m.MoneoError("--due cannot be combined with --at or --date.")
        at_parsed, date_parsed = _m.parse_due_string(due)
    else:
        at_parsed, date_parsed = at, date

    due_ts = _m.parse_time(rel, at_parsed, date_parsed, timezone=timezone)
    if due_ts is None:
        raise _m.MoneoError("Specify a time with --in, --at, --date, or --due.")

    if recur and recur not in _m.RECUR_CHOICES:
        raise _m.MoneoError(f"Invalid --recur '{recur}'.")
    if autosnooze is not None and autosnooze not in _m.VALID_AUTOSNOOZE:
        raise _m.MoneoError("--autosnooze must be one of 1, 5, 10, 15, 30, 60.")

    data = _m.read_db()
    duplicate = _m.find_duplicate(title, due_ts, data)
    if duplicate:
        existing_ts = _m.reminder_due_ts(duplicate) or due_ts
        raise _m.MoneoError(
            f"Duplicate: '{title}' already exists on that day at {_m.fmt_ts(existing_ts)}."
        )

    _m.add_direct(title, due_ts, recur, autosnooze, data)
    _m.write_db(data)

    recur_str = f" (repeats {recur})" if recur else ""
    return f"Added: '{title}' due {_m.fmt_ts(due_ts)}{recur_str} — synced to iPhone via CloudKit"


def ls() -> list[dict[str, Any]]:
    """Return all active reminders as a list of dicts (sorted by due date).

    Each dict has keys: index (1-based), uuid, title, due (human), due_ts, recur.
    """
    data = _m.read_db()
    reminders = _m.sorted_reminders(data)
    now = _m.now_ts()
    result = []
    for i, reminder in enumerate(reminders, start=1):
        uid = _m.reminder_uuid(reminder)
        due_ts = _m.reminder_due_ts(reminder)
        result.append(
            {
                "index": i,
                "uuid": uid,
                "short_uuid": _m.short_uuid(uid),
                "title": _m.reminder_title(reminder),
                "due": _m.fmt_ts(due_ts) if due_ts else None,
                "due_ts": due_ts,
                "overdue": bool(due_ts and due_ts < now),
                "recur": _m.recur_label(
                    reminder.get("rf") if isinstance(reminder.get("rf"), str) else None
                ),
            }
        )
    return result


def rm(target: str) -> str:
    """Delete a reminder by UUID prefix, pattern, or numeric index.

    Args:
        target: UUID prefix (6+ chars), substring pattern, or 1-based numeric index.

    Returns:
        Confirmation string listing deleted reminders.

    Raises:
        _m.MoneoError: If target not found or is ambiguous.
    """
    data = _m.read_db()
    matches, _ = _m.resolve_target(data, target, allow_pattern=True)
    current_ts = _m.now_ts()
    deleted = []
    for _, reminder in matches:
        target_uuid = _m.reminder_uuid(reminder)
        title = _m.reminder_title(reminder)
        if not target_uuid:
            raise _m.MoneoError("Reminder is missing UUID")
        raw = _m.reminders_mut(data)
        for index, raw_reminder in enumerate(raw):
            if _m.reminder_uuid(raw_reminder) == target_uuid:
                raw.pop(index)
                break
        _m.set_tombstone(data, target_uuid, current_ts)
        deleted.append(f"'{title}' [{_m.short_uuid(target_uuid)}]")
    _m.write_db(data)
    return "Deleted: " + ", ".join(deleted)


def edit(
    target: str,
    *,
    title: str | None = None,
    date: str | None = None,
    at: str | None = None,
    rel: str | None = None,
    autosnooze: int | None = None,
    timezone: str = "Asia/Hong_Kong",
) -> str:
    """Edit a reminder's title and/or time.

    Args:
        target: UUID prefix (6+ chars), substring pattern, or 1-based numeric index.
        title: New title (optional).
        date: New date YYYY-MM-DD or 'today'/'tomorrow' (optional).
        at: New time HH:MM (optional).
        rel: New relative offset '30m', '2h' (optional).
        autosnooze: New snooze interval in minutes (optional).
        timezone: IANA timezone.

    Returns:
        Confirmation string.

    Raises:
        _m.MoneoError: If target not found, ambiguous, or nothing to change.
    """
    data = _m.read_db()
    matches, _ = _m.resolve_target(data, target, allow_pattern=True)
    if len(matches) > 1:
        titles = [f"[{_m.short_uuid(_m.reminder_uuid(r))}] '{_m.reminder_title(r)}'" for _, r in matches]
        raise _m.MoneoError(f"Multiple matches: {'; '.join(titles)}. Use a UUID prefix.")

    raw_idx, reminder = matches[0]
    old_uuid = _m.reminder_uuid(reminder)
    if not old_uuid:
        raise _m.MoneoError("Reminder is missing UUID")

    # Build namespace to reuse build_change_set
    ns = argparse.Namespace(
        title=title,
        rel=rel,
        at=at,
        date=date,
        autosnooze=autosnooze,
        timezone=timezone,
    )
    changes = _m.build_change_set(ns, reminder)
    _m.ensure_no_duplicates(changes.title, [changes.due_ts], data)

    _m.reminders_mut(data).pop(raw_idx)
    _m.set_tombstone(data, old_uuid, _m.now_ts())
    _m.add_direct(changes.title, changes.due_ts, changes.recur, autosnooze, data)
    _m.write_db(data)
    return f"Updated [{_m.short_uuid(old_uuid)}]: {', '.join(changes.changed)} — synced to iPhone via CloudKit"


def log(n: int = 20, filter_str: str | None = None) -> list[dict[str, Any]]:
    """Return completion history from the Due DB logbook.

    Args:
        n: Number of recent entries to return.
        filter_str: Case-insensitive substring filter on title.

    Returns:
        List of dicts with keys: completed_hkt (str), title (str), completed_ts (int).
    """
    data = _m.read_db()
    entries: list[dict] = data.get("lb", [])
    entries = sorted(entries, key=lambda e: e.get("m", 0), reverse=True)
    if filter_str:
        fl = filter_str.lower()
        entries = [e for e in entries if fl in str(e.get("n", "")).lower()]
    entries = entries[:n]
    result = []
    for entry in entries:
        ts = int(entry.get("m", 0))
        result.append(
            {
                "completed_hkt": _m.hkt_from_ts(ts).strftime("%Y-%m-%d %H:%M") if ts else None,
                "completed_ts": ts,
                "title": str(entry.get("n", "")),
            }
        )
    return result


def snapshot() -> str:
    """Commit a git snapshot of current reminders. Returns a status string.

    Raises:
        _m.MoneoError: If Due DB is unavailable.
    """
    data = _m.read_db()
    if not isinstance(data, dict) or not data:
        raise _m.MoneoError("Could not read Due DB (permission error or DB unavailable).")
    _m.git_snapshot(data)
    count = len(_m.reminders_slice(data))
    return f"Snapshot committed ({count} reminders)."


# ---------------------------------------------------------------------------
# CLI entry point — matches Rust moneo interface
# ---------------------------------------------------------------------------


def _capture_stdout(fn, *args, **kwargs) -> str:
    """Run fn, capture its stdout output, return as string."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        fn(*args, **kwargs)
    return buf.getvalue().strip()


def _cli(argv: list[str] | None = None) -> int:
    """CLI entry point matching the Rust moneo interface.

    Dispatches subcommands: ls, add, rm, edit, log, snapshot, search.
    Delegates to the underlying moneo-py implementation via _m.main().
    """
    return _m.main(argv)


if __name__ == "__main__":
    raise SystemExit(_cli())
