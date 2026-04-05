"""pacemaker -- reminder signaling (pacemaker = generates signals at scheduled intervals)."""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import os
import re as re_mod
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from datetime import time as dt_time
from pathlib import Path
from typing import Any, NoReturn
from zoneinfo import ZoneInfo

HKT = ZoneInfo("Asia/Hong_Kong")
VALID_AUTOSNOOZE = {1, 5, 10, 15, 30, 60}
RECUR_CHOICES = {"daily", "weekly", "monthly", "quarterly", "yearly"}


class MoneoError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChangeSet:
    title: str
    due_ts: int
    changed: list[str]
    recur: str | None


def fatal(message: str) -> NoReturn:
    raise MoneoError(message)


def home_dir() -> Path:
    home = os.environ.get("HOME")
    if not home:
        fatal("HOME is not set")
    return Path(home)


def due_db_path() -> Path:
    return (
        home_dir()
        / "Library/Containers/com.phocusllp.duemac/Data/Library/Application Support/Due App/Due.duedb"
    )


def snapshot_path() -> Path:
    return home_dir() / "officina/backups/due-reminders.json"


def log_path() -> Path:
    return home_dir() / "tmp/due-snapshot.log"


def hkt_now() -> datetime:
    return datetime.now(HKT)


def now_ts() -> int:
    return int(datetime.now(UTC).timestamp())


def hkt_from_ts(ts: int, timezone: str = "Asia/Hong_Kong") -> datetime:
    try:
        tz = ZoneInfo(timezone)
    except Exception as exc:
        fatal(f"Invalid timezone '{timezone}': {exc}")
    return datetime.fromtimestamp(ts, tz=UTC).astimezone(tz)


def parse_due_string(due: str) -> tuple[str | None, str | None]:
    parts = due.split()
    if len(parts) == 1:
        part = parts[0]
        if ":" in part:
            return part, None
        return None, resolve_date_keyword(part)
    if len(parts) == 2:
        return parts[1], resolve_date_keyword(parts[0])
    fatal(f"Error: invalid --due '{due}'. Use e.g. 'today 16:15', 'tomorrow', '2026-03-16 10:00'.")


def resolve_date_keyword(value: str, now: datetime | None = None) -> str:
    now = now or hkt_now()
    lowered = value.lower()
    if lowered == "today":
        return now.strftime("%Y-%m-%d")
    if lowered == "tomorrow":
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")
    return value


def parse_relative(value: str) -> timedelta:
    if len(value) < 2:
        fatal(f"Error: invalid --in '{value}'. Use e.g. 30m, 2h, 90s.")
    amount, unit = value[:-1], value[-1]
    try:
        n = int(amount)
    except ValueError:
        fatal(f"Error: invalid --in '{value}'. Use e.g. 30m, 2h, 90s.")
    if unit == "s":
        return timedelta(seconds=n)
    if unit == "m":
        return timedelta(minutes=n)
    if unit == "h":
        return timedelta(hours=n)
    fatal(f"Error: invalid --in '{value}'. Use e.g. 30m, 2h, 90s.")


def parse_interval(value: str) -> timedelta:
    if len(value) < 2:
        fatal(f"Error: invalid --every '{value}'. Use Nh, Nm, or And.")
    amount, unit = value[:-1], value[-1]
    try:
        n = int(amount)
    except ValueError:
        fatal(f"Error: invalid --every '{value}'. Use Nh, Nm, or And.")
    if n <= 0:
        fatal(f"Error: invalid --every '{value}'. Use a positive interval.")
    if unit == "m":
        return timedelta(minutes=n)
    if unit == "h":
        return timedelta(hours=n)
    if unit == "d":
        return timedelta(days=n)
    fatal(f"Error: invalid --every '{value}'. Use Nh, Nm, or And.")


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        fatal(f"Error: invalid --date '{value}'. Use YYYY-MM-DD.")


def parse_at(value: str) -> dt_time:
    for fmt in ("%H:%M", "%-H:%M"):
        try:
            parsed = datetime.strptime(value, fmt)
            return dt_time(parsed.hour, parsed.minute)
        except ValueError:
            continue
    fatal(f"Error: invalid --at '{value}'. Use HH:MM.")


def resolve_local_timestamp(day: date, at_value: str | None, timezone: str) -> int:
    zone = ZoneInfo(timezone)
    if at_value is None:
        local = datetime.combine(day, dt_time(9, 0), tzinfo=zone)
        return int(local.timestamp())
    parsed_time = parse_at(at_value)
    local = datetime.combine(day, parsed_time, tzinfo=zone)
    return int(local.timestamp())


def parse_time(
    rel: str | None,
    at: str | None,
    date_value: str | None,
    *,
    timezone: str = "Asia/Hong_Kong",
    now: datetime | None = None,
) -> int | None:
    now = now or datetime.now(ZoneInfo(timezone))
    if rel:
        return int((now + parse_relative(rel)).timestamp())
    if date_value:
        return resolve_local_timestamp(parse_date(date_value), at, timezone)
    if at:
        return resolve_local_timestamp(now.date(), at, timezone)
    return None


def fmt_ts(ts: int) -> str:
    dt = hkt_from_ts(ts)
    now = hkt_now()
    if dt.date() == now.date():
        return dt.strftime("today %H:%M")
    if dt.date() == (now + timedelta(days=1)).date():
        return dt.strftime("tomorrow %H:%M")
    return dt.strftime("%b %d %H:%M")


def read_db() -> dict[str, Any]:
    path = due_db_path()
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    except PermissionError:
        return {}
    except FileNotFoundError as exc:
        fatal(f"Failed to read {path}: {exc}")
    except OSError as exc:
        fatal(f"Failed to parse {path}: {exc}")
    except json.JSONDecodeError as exc:
        fatal(f"Failed to parse {path}: {exc}")


def due_pid() -> str | None:
    result = subprocess.run(
        ["pgrep", "-x", "Due"], capture_output=True, text=True, check=False, timeout=300
    )
    if result.returncode != 0:
        return None
    pid = result.stdout.strip()
    return pid or None


def run_best_effort(program: str, *args: str) -> None:
    subprocess.run(
        [program, *args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=300,
    )


def reminders_slice(data: dict[str, Any]) -> list[dict[str, Any]]:
    reminders = data.get("re")
    return reminders if isinstance(reminders, list) else []


def active_reminders(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return reminders excluding entries that appear in the logbook (completed).

    Cross-references against data["lb"] using (title, due_ts) tuples.  Logbook
    entries use "n" for title and "d" for the original due timestamp (same field
    names as reminder entries).  If a logbook entry lacks "d", it is matched by
    title alone to stay conservative.
    """
    logbook = data.get("lb")
    if not isinstance(logbook, list) or not logbook:
        return reminders_slice(data)

    # Build completed sets: prefer (title, due_ts) pairs; fall back to title-only
    # for logbook entries that lack a "d" field.
    completed_pairs: set[tuple[str, int]] = set()
    completed_titles_only: set[str] = set()
    for entry in logbook:
        title = str(entry.get("n", "")).strip().lower()
        if not title:
            continue
        due_ts = entry.get("d")
        if isinstance(due_ts, int):
            completed_pairs.add((title, due_ts))
        else:
            completed_titles_only.add(title)

    active: list[dict[str, Any]] = []
    for reminder in reminders_slice(data):
        title = reminder_title(reminder).strip().lower()
        due_ts = reminder_due_ts(reminder)
        if due_ts is not None and (title, due_ts) in completed_pairs:
            continue
        if due_ts is None and title in completed_titles_only:
            continue
        active.append(reminder)
    return active


def reminders_mut(data: dict[str, Any]) -> list[dict[str, Any]]:
    reminders = data.setdefault("re", [])
    if not isinstance(reminders, list):
        fatal("Due DB field 're' is not an array")
    return reminders


def reminder_due_ts(reminder: dict[str, Any]) -> int | None:
    due = reminder.get("d")
    return due if isinstance(due, int) else None


def reminder_title(reminder: dict[str, Any]) -> str:
    title = reminder.get("n")
    return title if isinstance(title, str) else ""


def reminder_uuid(reminder: dict[str, Any]) -> str | None:
    value = reminder.get("u")
    return value if isinstance(value, str) else None


def sorted_reminders(data: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(reminders_slice(data), key=lambda reminder: reminder_due_ts(reminder) or 0)


def recur_label(code: str | None) -> str | None:
    return {
        "d": "daily",
        "w": "weekly",
        "m": "monthly",
        "q": "quarterly",
        "y": "yearly",
    }.get(code or "")


def recur_unit(freq: str) -> int | None:
    return {
        "daily": 16,
        "weekly": 256,
        "monthly": 8,
        "quarterly": 8,
        "yearly": 4,
    }.get(freq)


def recur_freq(freq: str) -> int | None:
    return {
        "daily": 1,
        "weekly": 1,
        "monthly": 1,
        "quarterly": 3,
        "yearly": 1,
    }.get(freq)


def recur_code(freq: str) -> str | None:
    return {"daily": "d", "weekly": "w", "monthly": "m", "quarterly": "q", "yearly": "y"}.get(freq)


def generate_uuid() -> str:
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).rstrip(b"=").decode("ascii")


def make_reminder(
    title: str,
    due_ts: int,
    recur: str | None,
    autosnooze: int | None,
) -> dict[str, Any]:
    ts = now_ts()
    reminder: dict[str, Any] = {
        "u": generate_uuid(),
        "n": title,
        "d": due_ts,
        "b": ts,
        "m": ts,
        "si": (autosnooze or 5) * 60,
    }
    if recur:
        code = recur_code(recur)
        if code:
            reminder["rf"] = code
            reminder["rd"] = due_ts
            unit = recur_unit(recur)
            freq = recur_freq(recur)
            if unit:
                reminder["rn"] = unit
            if freq and freq > 1:
                reminder["ru"] = {"i": freq}
            if recur == "weekly":
                dt = hkt_from_ts(due_ts)
                weekday = ((dt.weekday() + 1) % 7) + 1
                reminder["rb"] = weekday
    return reminder


def find_duplicate(
    title: str, due_ts: int, data: dict[str, Any] | None = None
) -> dict[str, Any] | None:
    due_dt = hkt_from_ts(due_ts)
    normalized = title.strip().lower()
    haystack = active_reminders(data or read_db())
    for reminder in haystack:
        if reminder_title(reminder).strip().lower() != normalized:
            continue
        existing_due = reminder_due_ts(reminder)
        if existing_due is None:
            continue
        existing_dt = hkt_from_ts(existing_due)
        if (
            existing_dt.date() == due_dt.date()
            and existing_dt.hour == due_dt.hour
            and existing_dt.minute == due_dt.minute
        ):
            return reminder
    return None


def make_snapshot(data: dict[str, Any]) -> list[dict[str, Any]]:
    snapshot: list[dict[str, Any]] = []
    for reminder in sorted_reminders(data):
        due_ts = reminder_due_ts(reminder)
        snapshot.append(
            {
                "title": reminder_title(reminder),
                "due": fmt_ts(due_ts) if due_ts is not None else None,
                "due_ts": due_ts,
                "recur": recur_label(
                    reminder.get("rf") if isinstance(reminder.get("rf"), str) else None
                ),
                "uuid": reminder_uuid(reminder),
            }
        )
    return snapshot


def comparable_snapshot(data: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "title": reminder_title(reminder),
            "due": reminder_due_ts(reminder),
            "recur": recur_label(
                reminder.get("rf") if isinstance(reminder.get("rf"), str) else None
            ),
        }
        for reminder in sorted_reminders(data)
    ]


def git_snapshot(data: dict[str, Any]) -> None:
    snapshot = make_snapshot(data)
    path = snapshot_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(snapshot, indent=2)}\n", encoding="utf-8")

    repo = path.parent
    subprocess.run(
        ["git", "-C", str(repo), "add", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=300,
    )
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", f"due: snapshot ({len(snapshot)} reminders)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=300,
    )


def write_db(data: dict[str, Any]) -> None:
    due_db = due_db_path()
    backup = due_db.with_suffix(".duedb.bak")
    try:
        backup.write_bytes(due_db.read_bytes())
    except OSError as exc:
        fatal(f"Failed to back up {due_db} to {backup}: {exc}")

    # Update modification timestamp for CloudKit
    mt = data.get("mt")
    if isinstance(mt, dict):
        mt["ts"] = now_ts()

    pid = due_pid()
    if pid:
        run_best_effort("kill", "-15", pid)
        for _ in range(20):
            time.sleep(0.2)
            if not due_pid():
                break

    try:
        with gzip.open(due_db, "wt", encoding="utf-8") as handle:
            json.dump(data, handle, separators=(",", ":"))
    except Exception as exc:
        try:
            due_db.write_bytes(backup.read_bytes())
        except OSError as restore_exc:
            fatal(f"Write failed, and restore also failed for {due_db}: {restore_exc}")
        fatal(f"Write failed, restored backup: {exc}")

    if pid:
        run_best_effort("open", "-a", "Due")

    git_snapshot(data)


def set_tombstone(data: dict[str, Any], uuid: str, ts: int) -> None:
    dl = data.setdefault("dl", {})
    if not isinstance(dl, dict):
        fatal("Due DB field 'dl' is not an object")
    dl[uuid] = ts


def get_reminder(data: dict[str, Any], index: int) -> tuple[int, dict[str, Any]]:
    reminders = sorted_reminders(data)
    if index <= 0 or index > len(reminders):
        fatal(f"Error: no reminder at index {index}.")
    target = reminders[index - 1]
    target_uuid = reminder_uuid(target)
    if not target_uuid:
        fatal("Reminder is missing UUID")
    raw = reminders_slice(data)
    for raw_idx, reminder in enumerate(raw):
        if reminder_uuid(reminder) == target_uuid:
            return raw_idx, reminder
    fatal("Reminder UUID not found in raw reminder list")


def short_uuid(uid: str | None) -> str:
    """Return the first 8 characters of a UUID for display."""
    return uid[:8] if uid else "--------"


def is_uuid_prefix(value: str) -> bool:
    """Check if a string looks like a UUID prefix (base64url chars, 6-22 length)."""
    if len(value) < 6 or len(value) > 22:
        return False
    return bool(re_mod.fullmatch(r"[A-Za-z0-9_-]+", value))


def is_numeric(value: str) -> bool:
    """Check if a string is a positive integer (display index)."""
    try:
        return int(value) > 0
    except ValueError:
        return False


def find_by_uuid_prefix(data: dict[str, Any], prefix: str) -> list[dict[str, Any]]:
    """Find reminders whose UUID starts with the given prefix."""
    return [r for r in reminders_slice(data) if (reminder_uuid(r) or "").startswith(prefix)]


def confirm_action(reminder: dict[str, Any], action: str) -> bool:
    """Prompt for confirmation when using numeric index. Returns True if confirmed."""
    title = reminder_title(reminder)
    due_ts = reminder_due_ts(reminder)
    due_str = fmt_ts(due_ts) if due_ts else "no due date"
    uid = short_uuid(reminder_uuid(reminder))
    prompt = f"{action} #{uid} '{title}' (due {due_str})? [y/N] "
    try:
        answer = input(prompt).strip().lower()
    except EOFError, KeyboardInterrupt:
        print()
        return False
    return answer in ("y", "yes")


def resolve_target(
    data: dict[str, Any],
    identifier: str,
    *,
    allow_pattern: bool = False,
) -> tuple[list[tuple[int, dict[str, Any]]], bool]:
    """Resolve a target identifier to (raw_index, reminder) pairs.

    Returns (matches, needs_confirm) where needs_confirm is True when the
    identifier was a numeric index (fragile).

    Resolution order:
    1. Numeric index → single match, needs confirmation
    2. UUID prefix (6+ base64url chars) → exact match(es)
    3. Pattern substring match (only if allow_pattern=True)
    """
    # 1. Try numeric index
    if is_numeric(identifier):
        index = int(identifier)
        raw_idx, reminder = get_reminder(data, index)
        return [(raw_idx, reminder)], True

    # 2. Try UUID prefix
    if is_uuid_prefix(identifier):
        uuid_matches = find_by_uuid_prefix(data, identifier)
        if uuid_matches:
            results: list[tuple[int, dict[str, Any]]] = []
            raw = reminders_slice(data)
            for match in uuid_matches:
                match_uuid = reminder_uuid(match)
                for raw_idx, raw_reminder in enumerate(raw):
                    if reminder_uuid(raw_reminder) == match_uuid:
                        results.append((raw_idx, raw_reminder))
                        break
            return results, False

    # 3. Pattern matching (substring)
    if allow_pattern:
        pattern = identifier.strip().lower()
        matches = [r for r in reminders_slice(data) if pattern in reminder_title(r).lower()]
        if matches:
            results = []
            raw = reminders_slice(data)
            for match in matches:
                match_uuid = reminder_uuid(match)
                for raw_idx, raw_reminder in enumerate(raw):
                    if reminder_uuid(raw_reminder) == match_uuid:
                        results.append((raw_idx, raw_reminder))
                        break
            return results, False
        fatal(f"No reminders matching '{identifier}'.")

    # UUID prefix didn't match, and pattern not allowed
    if is_uuid_prefix(identifier):
        fatal(f"No reminders with UUID starting '{identifier}'.")
    fatal(f"No reminders matching '{identifier}'.")


def add_direct(
    title: str,
    due_ts: int,
    recur: str | None,
    autosnooze: int | None,
    data: dict[str, Any],
) -> str:
    reminder = make_reminder(title, due_ts, recur, autosnooze)
    reminders_mut(data).append(reminder)
    return reminder["u"]


def expand_schedule(
    base_ts: int,
    interval: timedelta,
    until_value: str,
    *,
    skip_night: bool = True,
    timezone: str = "Asia/Hong_Kong",
) -> list[int]:
    until_day = parse_date(until_value)
    zone = ZoneInfo(timezone)
    current = datetime.fromtimestamp(base_ts, tz=zone)
    end_of_day = datetime.combine(until_day, dt_time(23, 59, 59), tzinfo=zone)
    results: list[int] = []
    while current <= end_of_day:
        include = True
        if skip_night and (current.hour >= 23 or current.hour < 7):
            include = False
        if include:
            results.append(int(current.timestamp()))
        current += interval
    return results


def build_change_set(
    *,
    title: str | None,
    rel: str | None,
    at: str | None,
    date: str | None,
    timezone: str,
    reminder: dict[str, Any],
) -> ChangeSet:
    """Build a ChangeSet from keyword arguments for editing a reminder."""
    current_title = reminder_title(reminder)
    current_due_ts = reminder_due_ts(reminder)
    if current_due_ts is None:
        fatal("Reminder is missing due timestamp")
    new_title = title if title is not None else current_title
    new_due_ts = parse_time(rel, at, date, timezone=timezone) or current_due_ts
    changed: list[str] = []
    if new_title != current_title:
        changed.append(f"title -> '{new_title}'")
    if new_due_ts != current_due_ts:
        changed.append(f"due -> {fmt_ts(new_due_ts)}")
    if not changed:
        fatal("Nothing to change. Use --title, --in, --at, or --date.")
    return ChangeSet(
        title=new_title,
        due_ts=new_due_ts,
        changed=changed,
        recur=recur_label(reminder.get("rf") if isinstance(reminder.get("rf"), str) else None),
    )


def ensure_no_duplicates(title: str, due_times: list[int], data: dict[str, Any]) -> None:
    for due_ts in due_times:
        duplicate = find_duplicate(title, due_ts, data)
        if duplicate:
            existing_due = reminder_due_ts(duplicate) or due_ts
            fatal(
                f"Duplicate: '{title}' already exists on that day at {fmt_ts(existing_due)}. "
                "Use 'pacemaker edit' to change the time."
            )


# ---------------------------------------------------------------------------
# Public API (used by MCP + skills)
# ---------------------------------------------------------------------------


def api_add(
    title: str,
    *,
    date_value: str | None = None,
    at: str | None = None,
    rel: str | None = None,
    due: str | None = None,
    recur: str | None = None,
    autosnooze: int | None = None,
    timezone: str = "Asia/Hong_Kong",
) -> str:
    """Add a Due reminder. Returns confirmation string."""
    if due is not None:
        if at is not None or date_value is not None:
            raise MoneoError("--due cannot be combined with --at or --date.")
        at_parsed, date_parsed = parse_due_string(due)
    else:
        at_parsed, date_parsed = at, date_value

    due_ts = parse_time(rel, at_parsed, date_parsed, timezone=timezone)
    if due_ts is None:
        raise MoneoError("Specify a time with --in, --at, --date, or --due.")

    if recur and recur not in RECUR_CHOICES:
        raise MoneoError(f"Invalid --recur '{recur}'.")
    if autosnooze is not None and autosnooze not in VALID_AUTOSNOOZE:
        raise MoneoError("--autosnooze must be one of 1, 5, 10, 15, 30, 60.")

    data = read_db()
    duplicate = find_duplicate(title, due_ts, data)
    if duplicate:
        existing_ts = reminder_due_ts(duplicate) or due_ts
        raise MoneoError(f"Duplicate: '{title}' already exists at {fmt_ts(existing_ts)}.")

    add_direct(title, due_ts, recur, autosnooze, data)
    write_db(data)

    recur_str = f" (repeats {recur})" if recur else ""
    return f"Added: '{title}' due {fmt_ts(due_ts)}{recur_str}"


def api_ls() -> list[dict[str, Any]]:
    """Return all active reminders sorted by due date."""
    data = read_db()
    reminders = sorted_reminders(data)
    now = now_ts()
    result = []
    for i, reminder in enumerate(reminders, start=1):
        uid = reminder_uuid(reminder)
        due_ts = reminder_due_ts(reminder)
        result.append(
            {
                "index": i,
                "uuid": uid,
                "short_uuid": short_uuid(uid),
                "title": reminder_title(reminder),
                "due": fmt_ts(due_ts) if due_ts else None,
                "due_ts": due_ts,
                "overdue": bool(due_ts and due_ts < now),
                "recur": recur_label(
                    reminder.get("rf") if isinstance(reminder.get("rf"), str) else None
                ),
            }
        )
    return result


def api_rm(target: str) -> str:
    """Delete a reminder by UUID prefix, pattern, or numeric index."""
    data = read_db()
    matches, _ = resolve_target(data, target, allow_pattern=True)
    current_ts = now_ts()
    deleted = []
    for _, reminder in matches:
        target_uuid = reminder_uuid(reminder)
        title = reminder_title(reminder)
        if not target_uuid:
            raise MoneoError("Reminder is missing UUID")
        raw = reminders_mut(data)
        for index, raw_reminder in enumerate(raw):
            if reminder_uuid(raw_reminder) == target_uuid:
                raw.pop(index)
                break
        set_tombstone(data, target_uuid, current_ts)
        deleted.append(f"'{title}' [{short_uuid(target_uuid)}]")
    write_db(data)
    return "Deleted: " + ", ".join(deleted)


def api_edit(
    target: str,
    *,
    title: str | None = None,
    date_value: str | None = None,
    at: str | None = None,
    rel: str | None = None,
    autosnooze: int | None = None,
    timezone: str = "Asia/Hong_Kong",
) -> str:
    """Edit a reminder's title and/or time."""
    data = read_db()
    matches, _ = resolve_target(data, target, allow_pattern=True)
    if len(matches) > 1:
        titles = [f"[{short_uuid(reminder_uuid(r))}] '{reminder_title(r)}'" for _, r in matches]
        raise MoneoError(f"Multiple matches: {'; '.join(titles)}. Use a UUID prefix.")

    raw_idx, reminder = matches[0]
    old_uuid = reminder_uuid(reminder)
    if not old_uuid:
        raise MoneoError("Reminder is missing UUID")

    changes = build_change_set(
        title=title,
        rel=rel,
        at=at,
        date=date_value,
        timezone=timezone,
        reminder=reminder,
    )
    ensure_no_duplicates(changes.title, [changes.due_ts], data)

    reminders_mut(data).pop(raw_idx)
    set_tombstone(data, old_uuid, now_ts())
    add_direct(changes.title, changes.due_ts, changes.recur, autosnooze, data)
    write_db(data)
    return f"Updated [{short_uuid(old_uuid)}]: {', '.join(changes.changed)}"


def api_log(n: int = 20, filter_str: str | None = None) -> list[dict[str, Any]]:
    """Return completion history from the Due DB logbook."""
    data = read_db()
    entries: list[dict] = data.get("lb", [])
    entries = sorted(entries, key=lambda e: e.get("m", 0), reverse=True)
    if filter_str:
        fl = filter_str.lower()
        entries = [e for e in entries if fl in str(e.get("n", "")).lower()]
    entries = entries[:n]
    return [
        {
            "completed_hkt": hkt_from_ts(ts).strftime("%Y-%m-%d %H:%M")
            if (ts := int(e.get("m", 0)))
            else None,
            "completed_ts": ts,
            "title": str(e.get("n", "")),
        }
        for e in entries
    ]


def api_snapshot() -> str:
    """Commit a git snapshot of current reminders."""
    data = read_db()
    if not isinstance(data, dict) or not data:
        raise MoneoError("Could not read Due DB.")
    git_snapshot(data)
    count = len(reminders_slice(data))
    return f"Snapshot committed ({count} reminders)."


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cmd_ls(_args: argparse.Namespace) -> None:
    items = api_ls()
    if not items:
        print("No reminders.")
        return
    hdr = f"{'#':<5}{'ID':<11}{'Title':<37}{'Due':<17}{'Recur'}"
    print(hdr)
    print("\u2500" * 78)
    for item in items:
        flag = " \u26a0" if item["overdue"] else ""
        recur = item["recur"] or ""
        print(
            f"{item['index']:<5}{item['short_uuid']:<11}{item['title']:<37}{(item['due'] or '') + flag:<17}{recur}"
        )


def _cmd_add(args: argparse.Namespace) -> None:
    if args.every:
        due_ts = parse_time(args.rel, args.at, args.date, timezone=args.timezone)
        if due_ts is None:
            fatal("Specify a start time with --in, --at, or --date.")
        if not args.until:
            fatal("--every requires --until.")
        interval = parse_interval(args.every)
        skip_night = not args.no_skip_night
        due_times = expand_schedule(
            due_ts, interval, args.until, skip_night=skip_night, timezone=args.timezone
        )
        data = read_db()
        ensure_no_duplicates(args.title, due_times, data)
        for ts in due_times:
            add_direct(args.title, ts, None, args.autosnooze, data)
        write_db(data)
        print(f"Added {len(due_times)} reminders for '{args.title}'.")
        return
    result = api_add(
        args.title,
        date_value=args.date,
        at=args.at,
        rel=args.rel,
        due=args.due,
        recur=args.recur,
        autosnooze=args.autosnooze,
        timezone=args.timezone,
    )
    print(result)


def _cmd_rm(args: argparse.Namespace) -> None:
    print(api_rm(args.target))


def _cmd_edit(args: argparse.Namespace) -> None:
    print(
        api_edit(
            args.target,
            title=args.title,
            date_value=args.date,
            at=args.at,
            rel=args.rel,
            autosnooze=args.autosnooze,
            timezone=args.timezone,
        )
    )


def _cmd_log(args: argparse.Namespace) -> None:
    items = api_log(n=args.n, filter_str=args.filter)
    if not items:
        print("No completions found.")
        return
    hdr = f"{'Completed (HKT)':<21}{'Title'}"
    print(hdr)
    print("\u2500" * 68)
    for item in items:
        print(f"{item['completed_hkt'] or '?':<21}{item['title']}")


def _cmd_snapshot(_args: argparse.Namespace) -> None:
    print(api_snapshot())


def _cmd_search(args: argparse.Namespace) -> None:
    url = f"due:///search?query={args.query}"
    if args.section:
        url += f"&section={args.section}"
    subprocess.run(["open", url], check=False, timeout=300)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pacemaker", description="Due app reminder manager")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("ls", help="List all reminders").set_defaults(func=_cmd_ls)
    subparsers.add_parser("snapshot", help="Git-commit snapshot").set_defaults(func=_cmd_snapshot)

    add = subparsers.add_parser("add", help="Add a reminder")
    add.add_argument("title")
    add.add_argument("--in", dest="rel", metavar="TIME")
    add.add_argument("--at", metavar="HH:MM")
    add.add_argument("--date", metavar="YYYY-MM-DD")
    add.add_argument("--due", metavar="WHEN")
    add.add_argument("--recur", metavar="FREQ")
    add.add_argument("--every", metavar="INTERVAL")
    add.add_argument("--until", metavar="YYYY-MM-DD")
    add.add_argument("--no-skip-night", action="store_true")
    add.add_argument("--autosnooze", type=int)
    add.add_argument("--timezone", default="Asia/Hong_Kong")
    add.set_defaults(func=_cmd_add)

    rm = subparsers.add_parser("rm", aliases=["delete"], help="Delete a reminder")
    rm.add_argument("target", metavar="TARGET")
    rm.set_defaults(func=_cmd_rm)

    edit = subparsers.add_parser("edit", help="Edit a reminder")
    edit.add_argument("target", metavar="TARGET")
    edit.add_argument("--title")
    edit.add_argument("--in", dest="rel", metavar="TIME")
    edit.add_argument("--at", metavar="HH:MM")
    edit.add_argument("--date", metavar="YYYY-MM-DD")
    edit.add_argument("--autosnooze", type=int)
    edit.add_argument("--timezone", default="Asia/Hong_Kong")
    edit.set_defaults(func=_cmd_edit)

    log = subparsers.add_parser("log", help="Show completion history")
    log.add_argument("--n", "-n", type=int, default=20)
    log.add_argument("--filter")
    log.set_defaults(func=_cmd_log)

    search = subparsers.add_parser("search", help="Launch Due and search")
    search.add_argument("query")
    search.add_argument("--section", choices=["Reminders", "Timers", "Logbook"])
    search.set_defaults(func=_cmd_search)

    return parser


def _cli(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        print()
        return 0
    try:
        args.func(args)
    except MoneoError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
