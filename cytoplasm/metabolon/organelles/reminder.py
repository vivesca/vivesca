"""reminder — Due app management (formerly moneo). Endosymbiosis: Rust binary → Python organelle."""

import gzip
import json
import subprocess
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

HKT = timezone(timedelta(hours=8))

# Due app DB: gzip-compressed JSON at this path (Mac app sandbox container)
_DUE_DB = (
    Path.home()
    / "Library/Containers/com.phocusllp.duemac/Data/Library/Application Support/Due App/Due.duedb"
)

_APPLE_SCRIPT = """
    tell application "System Events"
        tell process "Due"
            repeat 20 times
                try
                    click button "Save" of window "Reminder Editor"
                    return "ok"
                end try
                delay 0.5
            end repeat
        end tell
    end tell
    return "timeout"
"""

_RECUR_UNIT = {"daily": 16, "weekly": 256, "monthly": 8, "quarterly": 8, "yearly": 4}
_RECUR_FREQ = {"daily": 1, "weekly": 1, "monthly": 1, "quarterly": 3, "yearly": 1}
_RECUR_LABEL = {"d": "daily", "w": "weekly", "m": "monthly", "q": "quarterly", "y": "yearly"}


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


def read_db() -> dict:
    """Read and return the Due app JSON database (gzip-compressed)."""
    path = _DUE_DB
    if not path.exists():
        return {}
    try:
        with gzip.open(path, "rb") as fh:
            return json.loads(fh.read())
    except PermissionError:
        return {}
    except Exception as exc:
        raise RuntimeError(f"Failed to read Due DB at {path}: {exc}") from exc


def _reminders(data: dict) -> list[dict]:
    """Return raw reminders list from DB data."""
    return data.get("re", [])


def _sorted_reminders(data: dict) -> list[dict]:
    """Return reminders sorted by due timestamp ascending."""
    return sorted(_reminders(data), key=lambda r: r.get("d", 0))


def _reminder_due_ts(r: dict) -> int:
    return r.get("d", 0)


def _reminder_title(r: dict) -> str:
    return r.get("n", "")


def _recur_label(code: str | None) -> str:
    return _RECUR_LABEL.get(code or "", "")


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def _fmt_ts(ts: int) -> str:
    """Format a Unix timestamp as a human-readable HKT string."""
    if not ts:
        return "\u2014"
    dt = datetime.fromtimestamp(ts, tz=HKT)
    now = datetime.now(tz=HKT)
    if dt.date() == now.date():
        return dt.strftime("today %H:%M")
    if dt.date() == (now + timedelta(days=1)).date():
        return dt.strftime("tomorrow %H:%M")
    return dt.strftime("%b %d %H:%M")


# ---------------------------------------------------------------------------
# Time parsing
# ---------------------------------------------------------------------------


def _hkt_now() -> datetime:
    return datetime.now(tz=HKT)


def resolve_date_keyword(s: str) -> str:
    """Resolve 'today'/'tomorrow' to YYYY-MM-DD; pass through other strings."""
    now = _hkt_now()
    lower = s.lower()
    if lower == "today":
        return now.strftime("%Y-%m-%d")
    if lower == "tomorrow":
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")
    return s


def parse_due_string(due: str) -> tuple[str | None, str | None]:
    """
    Parse a --due string such as 'today 16:15', 'tomorrow', '2026-03-16 10:00', '16:15'.
    Returns (at, date) where at is HH:MM or None, date is YYYY-MM-DD or None.
    """
    parts = due.split()
    if len(parts) == 1:
        p = parts[0]
        if ":" in p:
            return (p, None)  # time only
        return (None, resolve_date_keyword(p))  # date keyword or ISO date
    if len(parts) == 2:
        date_str = resolve_date_keyword(parts[0])
        time_str = parts[1]
        return (time_str, date_str)
    raise ValueError(
        f"Invalid --due '{due}'. Use e.g. 'today 16:15', 'tomorrow', '2026-03-16 10:00'."
    )


def parse_time(
    rel: str | None = None,
    at: str | None = None,
    date: str | None = None,
) -> int | None:
    """
    Resolve time arguments to a Unix timestamp (HKT).

    Priority: --in (relative) > --at / --date combination.
    If only --date is given, defaults to 09:00 on that date.
    Returns None if no time arguments are provided.
    """
    now = _hkt_now()

    if rel is not None:
        if len(rel) < 2:
            raise ValueError(f"Invalid --in '{rel}'. Use e.g. 30m, 2h, 90s.")
        num_str, unit = rel[:-1], rel[-1]
        try:
            n = int(num_str)
        except ValueError as err:
            raise ValueError(f"Invalid --in '{rel}'. Use e.g. 30m, 2h, 90s.") from err
        if unit == "s":
            delta = timedelta(seconds=n)
        elif unit == "m":
            delta = timedelta(minutes=n)
        elif unit == "h":
            delta = timedelta(hours=n)
        else:
            raise ValueError(f"Invalid --in '{rel}'. Use e.g. 30m, 2h, 90s.")
        return int((now + delta).timestamp())

    base_date = now.date()
    if date is not None:
        try:
            base_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError as err:
            raise ValueError(f"Invalid --date '{date}'. Use YYYY-MM-DD.") from err

    if at is not None:
        try:
            t = datetime.strptime(at, "%H:%M").time()
        except ValueError as err:
            raise ValueError(f"Invalid --at '{at}'. Use HH:MM.") from err
        dt_naive = datetime.combine(base_date, t)
        dt_hkt = dt_naive.replace(tzinfo=HKT)
        return int(dt_hkt.timestamp())

    if date is not None:
        dt_naive = datetime.combine(base_date, datetime.strptime("09:00", "%H:%M").time())
        dt_hkt = dt_naive.replace(tzinfo=HKT)
        return int(dt_hkt.timestamp())

    return None


# ---------------------------------------------------------------------------
# Public commands
# ---------------------------------------------------------------------------


def cmd_ls(data: dict | None = None) -> None:
    """List all reminders sorted by due date, printing a formatted table to stdout."""
    if data is None:
        data = read_db()
    reminders = _sorted_reminders(data)
    if not reminders:
        print("No reminders.")
        return

    now_ts = int(_hkt_now().timestamp())
    print(f"{'#':<4} {'Title':<36} {'Due':<16} Recur")
    print("\u2500" * 68)
    for i, r in enumerate(reminders):
        title = _reminder_title(r)[:35]
        due_ts = _reminder_due_ts(r)
        due_str = _fmt_ts(due_ts) if due_ts else "\u2014"
        flag = " \u26a0" if due_ts and due_ts < now_ts else ""
        recur = _recur_label(r.get("rf"))
        print(f"{i + 1:<4} {title:<36} {due_str + flag:<16} {recur}")


def cmd_add(
    title: str,
    rel: str | None = None,
    at: str | None = None,
    date: str | None = None,
    due: str | None = None,
    recur: str | None = None,
) -> None:
    """
    Add a reminder via the due:// URL scheme and sync via AppleScript.

    Time can be specified as:
      rel   -- relative offset e.g. '30m', '2h'
      at    -- HH:MM time (optionally combined with date)
      date  -- YYYY-MM-DD (or 'today'/'tomorrow')
      due   -- combined string e.g. 'today 16:15', 'tomorrow 09:00'
      recur -- one of: daily, weekly, monthly, quarterly, yearly
    """
    if due is not None:
        if at is not None or date is not None:
            raise ValueError("--due cannot be combined with --at or --date.")
        at, date = parse_due_string(due)

    due_ts = parse_time(rel, at, date)
    if due_ts is None:
        raise ValueError("Specify a time with --in, --at, --date, or --due.")

    # Duplicate check
    data = read_db()
    _check_duplicate(data, title, due_ts)

    ok = _sync_via_applescript(title, due_ts, recur)
    recur_str = f" (repeats {recur})" if recur else ""
    if ok:
        print(
            f"Added: '{title}' due {_fmt_ts(due_ts)}{recur_str}"
            " \u2014 synced to iPhone via CloudKit (AppleScript)"
        )
    else:
        print("Due editor open \u2014 please click Save manually to sync to iPhone.")


def cmd_log(n: int = 20, filter_str: str | None = None) -> None:
    """Show completion history from the Due DB log bucket ('lb' field)."""
    data = read_db()
    entries: list[dict] = data.get("lb", [])

    entries = sorted(entries, key=lambda r: r.get("m", 0), reverse=True)

    if filter_str:
        fl = filter_str.lower()
        entries = [r for r in entries if fl in r.get("n", "").lower()]

    entries = entries[:n]

    if not entries:
        print("No completions found.")
        return

    print(f"{'Completed (HKT)':<20} Title")
    print("\u2500" * 68)
    for r in entries:
        ts = r.get("m", 0)
        dt_str = datetime.fromtimestamp(ts, tz=HKT).strftime("%Y-%m-%d %H:%M") if ts else "\u2014"
        title = r.get("n", "")[:46]
        print(f"{dt_str:<20} {title}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _check_duplicate(data: dict, title: str, due_ts: int) -> None:
    """Raise ValueError if an identical title+date+time reminder already exists."""
    due_dt = datetime.fromtimestamp(due_ts, tz=HKT)
    norm = title.strip().lower()
    for r in _reminders(data):
        if _reminder_title(r).strip().lower() == norm:
            existing_ts = _reminder_due_ts(r)
            if existing_ts:
                ex_dt = datetime.fromtimestamp(existing_ts, tz=HKT)
                if (
                    ex_dt.date() == due_dt.date()
                    and ex_dt.hour == due_dt.hour
                    and ex_dt.minute == due_dt.minute
                ):
                    raise ValueError(
                        f"Duplicate: '{title}' already exists on that day at"
                        f" {_fmt_ts(existing_ts)}. Use 'moneo edit' to change the time."
                    )


def _run_best_effort(program: str, *args: str) -> None:
    """Run a subprocess, silencing all output and ignoring errors."""
    subprocess.run(
        [program, *args],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _build_due_url(title: str, due_ts: int, recur: str | None) -> str:
    """Build the due:// x-callback URL for adding a reminder."""
    params = urllib.parse.urlencode({"title": title, "duedate": due_ts})
    url = f"due://x-callback-url/add?{params}"

    if recur and recur in _RECUR_UNIT:
        unit = _RECUR_UNIT[recur]
        freq = _RECUR_FREQ[recur]
        url += f"&recurunit={unit}&recurfreq={freq}&recurfromdate={due_ts}"
        if recur == "weekly":
            dt = datetime.fromtimestamp(due_ts, tz=HKT)
            # Rust: (weekday().num_days_from_monday() + 2) % 7, then 0 -> 7
            day = (dt.weekday() + 2) % 7
            if day == 0:
                day = 7
            url += f"&recurbyday={day}"
    return url


def _sync_via_applescript(title: str, due_ts: int, recur: str | None) -> bool:
    """
    Open the due:// URL to create a reminder, then use osascript to click Save.
    Returns True if AppleScript confirmed the Save click, False on timeout.
    """
    import time

    url = _build_due_url(title, due_ts, recur)
    _run_best_effort("caffeinate", "-u", "-t", "1")
    time.sleep(0.5)
    _run_best_effort("open", url)
    time.sleep(3)

    result = subprocess.run(
        ["osascript", "-e", _APPLE_SCRIPT],
        capture_output=True,
        text=True,
    )
    return "ok" in result.stdout


# ---------------------------------------------------------------------------
# CLI entry point (thin — primary interface is MCP tool)
# ---------------------------------------------------------------------------


def _main(argv: list[str] | None = None) -> None:
    import argparse

    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="reminder", description="Due app reminder manager")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("ls", help="List all reminders")

    add_p = sub.add_parser("add", help="Add a reminder")
    add_p.add_argument("title")
    add_p.add_argument("--in", dest="rel", metavar="TIME")
    add_p.add_argument("--at", metavar="HH:MM")
    add_p.add_argument("--date", metavar="YYYY-MM-DD")
    add_p.add_argument("--due", metavar="WHEN")
    add_p.add_argument("--recur", choices=list(_RECUR_UNIT))

    log_p = sub.add_parser("log", help="Show completion history")
    log_p.add_argument("-n", type=int, default=20)
    log_p.add_argument("--filter")

    args = parser.parse_args(argv)

    if args.cmd == "ls":
        cmd_ls()
    elif args.cmd == "add":
        try:
            cmd_add(
                args.title,
                rel=args.rel,
                at=args.at,
                date=args.date,
                due=args.due,
                recur=args.recur,
            )
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
    elif args.cmd == "log":
        cmd_log(n=args.n, filter_str=args.filter)
    else:
        parser.print_help()


if __name__ == "__main__":
    _main()
