"""Shared context-gathering module. Deterministic data collection for skills.

No LLM calls. Shell out to CLIs, parse vault files, return structured dicts.
Skills (kairos, commute, photoreception, copia, weekly, etc.) call gather_context()
and hand the result to the model for reasoning only.

Usage:
    from gather import gather_context, read_todo, read_now, get_calendar, check_budget, get_date

    ctx = gather_context()                          # all sources
    ctx = gather_context(include=["todo", "date"])  # selective
"""

import concurrent.futures
import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from typing import Any

# HKT = UTC+8
_HKT = timezone(timedelta(hours=8))

_PRAXIS_PATH = os.path.expanduser("~/notes/Praxis.md")
_NOW_PATH = os.path.expanduser("~/notes/Tonus.md")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run(cmd: list[str], timeout: int = 15) -> tuple[str, str]:
    """Run a subprocess. Returns (stdout, stderr). Never raises."""
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return "", f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return "", f"timed out after {timeout}s"
    except Exception as e:
        return "", str(e)


def _read_file(path: str) -> str | None:
    """Read a file. Returns None on any error."""
    expanded = os.path.expanduser(path)
    try:
        with open(expanded, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# get_date
# ---------------------------------------------------------------------------


def get_date() -> dict[str, str]:
    """Return current HKT datetime as structured dict.

    Returns:
        {
            "iso": "2026-03-20",
            "time": "14:35",
            "datetime": "2026-03-20 14:35 HKT",
            "day_of_week": "Friday",
            "day_abbr": "Fri",
            "timestamp": "2026-03-20T14:35:00+08:00",
        }
    """
    now = datetime.now(_HKT)
    return {
        "iso": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "datetime": now.strftime("%Y-%m-%d %H:%M HKT"),
        "day_of_week": now.strftime("%A"),
        "day_abbr": now.strftime("%a"),
        "timestamp": now.isoformat(),
    }


# ---------------------------------------------------------------------------
# read_todo
# ---------------------------------------------------------------------------

# Matches: - [ ] item text `tag:value` `tag2:value2`
_PRAXIS_ITEM_RE = re.compile(r"^(?P<indent>\s*)-\s+\[(?P<done>[ xX])\]\s+(?P<text>.+)$")
_TAG_RE = re.compile(r"`(?P<key>[a-zA-Z_-]+):(?P<value>[^`]*)`")
_SECTION_RE = re.compile(r"^#{1,6}\s+(?P<title>.+)$")


def _parse_todo_item(line: str, section: str) -> dict[str, Any] | None:
    """Parse a single TODO line. Returns None if not a TODO item."""
    m = _PRAXIS_ITEM_RE.match(line)
    if not m:
        return None

    done_marker = m.group("done").strip().lower()
    done = done_marker in ("x",)
    raw_text = m.group("text")

    # Extract inline tags
    tags: dict[str, str] = {}
    for tm in _TAG_RE.finditer(raw_text):
        tags[tm.group("key")] = tm.group("value")

    # Strip tags from display text
    display_text = _TAG_RE.sub("", raw_text).strip()

    return {
        "text": display_text,
        "raw": raw_text,
        "done": done,
        "section": section,
        "due": tags.get("due"),
        "when": tags.get("when"),
        "agent": tags.get("agent"),
        "recurring": tags.get("recurring"),
        "tags": tags,
    }


def read_todo(
    path: str = _PRAXIS_PATH,
    sections: list[str] | None = None,
    tags: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Parse Praxis.md, return structured list of items with metadata.

    Args:
        path: Path to Praxis.md (default: ~/notes/Praxis.md).
        sections: If given, only include items from sections whose headings
                  contain any of these strings (case-insensitive).
        tags:     If given, only include items whose inline tags match ALL
                  key-value pairs (e.g. {"agent": "terry"}).

    Returns:
        {
            "available": True/False,
            "path": "/path/to/Praxis.md",
            "items": [
                {
                    "text": "Send conference emails",
                    "raw": "Send conference emails `due:2026-03-20` `agent:terry`",
                    "done": False,
                    "section": "Copia Wave 5",
                    "due": "2026-03-20",
                    "when": None,
                    "agent": "terry",
                    "recurring": None,
                    "tags": {"due": "2026-03-20", "agent": "terry"},
                },
                ...
            ],
            "error": None or "message",
        }
    """
    expanded = os.path.expanduser(path)
    raw = _read_file(expanded)

    if raw is None:
        return {"available": False, "path": expanded, "items": [], "error": "file not found"}

    items: list[dict[str, Any]] = []
    current_section = ""

    for line in raw.splitlines():
        section_match = _SECTION_RE.match(line)
        if section_match:
            current_section = section_match.group("title").strip()
            continue

        item = _parse_todo_item(line, current_section)
        if item is None:
            continue

        # Section filter
        if sections:
            section_lower = current_section.lower()
            if not any(s.lower() in section_lower for s in sections):
                continue

        # Tag filter
        if tags:
            if not all(item["tags"].get(k) == v for k, v in tags.items()):
                continue

        items.append(item)

    return {
        "available": True,
        "path": expanded,
        "items": items,
        "error": None,
    }


def read_todo_today(date_iso: str | None = None) -> dict[str, Any]:
    """Convenience: return only overdue and today's TODO items, max 10.

    Filters for items where:
    - due <= today, OR
    - when <= today (and not done), OR
    - recurring:daily, OR
    - recurring tag matches today's day-of-week pattern

    Args:
        date_iso: Date string "YYYY-MM-DD" to use as 'today'. Defaults to HKT now.

    Returns same shape as read_todo() but with filtered items.
    """
    if date_iso is None:
        date_iso = get_date()["iso"]

    result = read_todo()
    if not result["available"]:
        return result

    today = _parse_date(date_iso)
    if today is None:
        return result  # can't filter without a valid date

    # Day-of-week for recurring checks
    day_of_week = today.weekday()  # 0=Mon ... 6=Sun
    day_abbr = today.strftime("%a").lower()  # "mon", "tue", ...

    qualifying: list[dict[str, Any]] = []
    for item in result["items"]:
        if item["done"]:
            continue

        due_str = item.get("due")
        when_str = item.get("when")
        recurring = item.get("recurring", "")

        # Due date filter
        if due_str:
            d = _parse_date(due_str)
            if d and d <= today:
                qualifying.append(item)
                continue

        # When filter
        if when_str:
            w = _parse_date(when_str)
            if w and w <= today:
                qualifying.append(item)
                continue

        # Recurring patterns
        if recurring:
            r = recurring.lower()
            if r == "daily":
                qualifying.append(item)
            elif r == "weekly":
                # Match same day of week as the item's 'due' baseline
                if due_str:
                    base = _parse_date(due_str)
                    if base and base.weekday() == day_of_week:
                        qualifying.append(item)
            elif r in ("mon", "tue", "wed", "thu", "fri", "sat", "sun"):
                if r == day_abbr:
                    qualifying.append(item)
            elif r == "weekdays":
                if day_of_week < 5:
                    qualifying.append(item)
            elif r == "3x-week":
                # Mon/Wed/Fri
                if day_of_week in (0, 2, 4):
                    qualifying.append(item)
            elif r == "biweekly":
                # Biweekly: fall through — needs a base date for ISO week parity
                # Include if due date is <= today as a conservative approximation
                if due_str:
                    d = _parse_date(due_str)
                    if d and d <= today:
                        qualifying.append(item)

    # Sort: overdue first (has due date <= today), then others
    def _sort_key(item: dict[str, Any]) -> tuple:
        d = _parse_date(item.get("due") or "9999-12-31")
        return (d or datetime.max.date(),)

    qualifying.sort(key=_sort_key)

    return {
        "available": True,
        "path": result["path"],
        "items": qualifying[:10],
        "error": None,
    }


def _parse_date(date_str: str | None) -> "datetime.date | None":
    """Parse YYYY-MM-DD string into a date. Returns None on failure."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# read_now
# ---------------------------------------------------------------------------

_H2_RE = re.compile(r"^##\s+(?P<title>.+)$")
_PROGRESS_ITEM_RE = re.compile(
    r"^-\s+\[(?P<state>[^\]]+)\]\s+\*\*(?P<title>[^*]+)\*\*(?P<rest>.*)"
)


def read_now(path: str = _NOW_PATH) -> dict[str, Any]:
    """Parse Tonus.md and return structured facts and progress items.

    Returns:
        {
            "available": True/False,
            "path": "/path/...",
            "facts": ["Career compound machine live. ...", ...],
            "progress": [
                {"state": "in-progress", "title": "HSBC delivery readiness", "detail": "..."},
                {"state": "queued", "title": "IBKR migration", "detail": "..."},
            ],
            "raw": "full file content",
            "last_wrap": "19/03/2026 ~18:30 HKT" or None,
            "error": None or "message",
        }
    """
    expanded = os.path.expanduser(path)
    raw = _read_file(expanded)

    if raw is None:
        return {
            "available": False,
            "path": expanded,
            "facts": [],
            "progress": [],
            "raw": None,
            "last_wrap": None,
            "error": "file not found",
        }

    facts: list[str] = []
    progress: list[dict[str, str]] = []
    current_section = ""
    last_wrap: str | None = None

    for line in raw.splitlines():
        # Track section headings
        h2 = _H2_RE.match(line)
        if h2:
            current_section = h2.group("title").strip().lower()
            continue

        # Extract last_wrap from HTML comment
        wrap_match = re.search(r"last wrap:\s*(.+?)-->", line)
        if wrap_match:
            last_wrap = wrap_match.group(1).strip()
            continue

        # Facts section: bullet lines
        if "facts" in current_section:
            # Remove markdown bold/italic and leading "- "
            stripped = line.strip()
            if stripped.startswith("- "):
                fact = re.sub(r"\*\*([^*]+)\*\*", r"\1", stripped[2:]).strip()
                if fact:
                    facts.append(fact)
            continue

        # Progress section: [state] **title** detail
        if "progress" in current_section:
            pm = _PROGRESS_ITEM_RE.match(line.strip())
            if pm:
                detail = pm.group("rest").strip()
                # Strip leading punctuation from detail
                detail = re.sub(r"^[.\s]+", "", detail)
                progress.append(
                    {
                        "state": pm.group("state").strip(),
                        "title": pm.group("title").strip(),
                        "detail": detail,
                    }
                )

    return {
        "available": True,
        "path": expanded,
        "facts": facts,
        "progress": progress,
        "raw": raw,
        "last_wrap": last_wrap,
        "error": None,
    }


# ---------------------------------------------------------------------------
# get_calendar
# ---------------------------------------------------------------------------


def get_calendar(date: str = "today", days: int = 1) -> dict[str, Any]:
    """Shell out to `fasti list {date}` and return parsed calendar events.

    Args:
        date: Date string accepted by fasti (e.g. "today", "tomorrow",
              "2026-03-21"). Defaults to "today".
        days: Number of days to fetch. If > 1, calls fasti for each day
              and merges results.

    Returns:
        {
            "available": True/False,
            "date": "today",
            "days": 1,
            "raw": "raw fasti output",
            "events": [
                {
                    "raw_line": "10:00 Standup",
                    "time": "10:00",
                    "title": "Standup",
                },
                ...
            ],
            "error": None or "message",
        }
    """
    if days == 1:
        stdout, stderr = _run(["fasti", "list", date])
        if not stdout and stderr:
            return {
                "available": False,
                "date": date,
                "days": days,
                "raw": None,
                "events": [],
                "error": stderr,
            }
        return {
            "available": True,
            "date": date,
            "days": days,
            "raw": stdout,
            "events": _parse_fasti_output(stdout),
            "error": None,
        }

    # Multi-day: resolve date and iterate
    # For simplicity, only support ISO date strings or "today"/"tomorrow" for multi-day
    if date in ("today", "tomorrow"):
        now = datetime.now(_HKT)
        base = now.date() if date == "today" else (now.date() + timedelta(days=1))
    else:
        d = _parse_date(date)
        base = d if d else datetime.now(_HKT).date()

    all_events: list[dict[str, str]] = []
    all_raw: list[str] = []
    errors: list[str] = []

    for offset in range(days):
        target = base + timedelta(days=offset)
        target_str = target.isoformat()
        stdout, stderr = _run(["fasti", "list", target_str])
        if stderr and not stdout:
            errors.append(f"{target_str}: {stderr}")
        else:
            all_raw.append(stdout)
            for event in _parse_fasti_output(stdout):
                event["date"] = target_str
                all_events.append(event)

    return {
        "available": bool(all_events or not errors),
        "date": date,
        "days": days,
        "raw": "\n".join(all_raw),
        "events": all_events,
        "error": "; ".join(errors) if errors else None,
    }


def _parse_fasti_output(text: str) -> list[dict[str, str]]:
    """Parse fasti list output into event dicts.

    fasti outputs lines like:
        10:00 - 10:30  Standup
        14:00          Deep work block
        All day        Public holiday

    Returns list of {"raw_line", "time", "end_time", "title"}.
    """
    events: list[dict[str, str]] = []
    if not text:
        return events

    # Pattern: optional time range then title
    time_range_re = re.compile(
        r"^(?P<time>\d{1,2}:\d{2})"
        r"(?:\s*[-–]\s*(?P<end_time>\d{1,2}:\d{2}))?"
        r"\s+(?P<title>.+)$"
    )
    allday_re = re.compile(r"^(?:All day|all-day|allday)\s+(?P<title>.+)$", re.IGNORECASE)

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        m = time_range_re.match(line)
        if m:
            events.append(
                {
                    "raw_line": line,
                    "time": m.group("time"),
                    "end_time": m.group("end_time") or "",
                    "title": m.group("title").strip(),
                    "all_day": False,
                }
            )
            continue

        m = allday_re.match(line)
        if m:
            events.append(
                {
                    "raw_line": line,
                    "time": "",
                    "end_time": "",
                    "title": m.group("title").strip(),
                    "all_day": True,
                }
            )
            continue

        # Fallback: treat the whole line as a title (fasti format may vary)
        if not line.startswith("#") and len(line) > 2:
            events.append(
                {
                    "raw_line": line,
                    "time": "",
                    "end_time": "",
                    "title": line,
                    "all_day": False,
                }
            )

    return events


# ---------------------------------------------------------------------------
# check_budget
# ---------------------------------------------------------------------------


def check_budget() -> dict[str, Any]:
    """Shell out to `respirometry` CLI and parse budget status.

    Returns:
        {
            "available": True/False,
            "raw": "raw respirometry output",
            "summary": "first non-empty line from respirometry (status line)",
            "lines": ["line1", "line2", ...],
            "error": None or "message",
        }
    """
    stdout, stderr = _run(["respirometry"], timeout=20)

    if not stdout and stderr:
        return {
            "available": False,
            "raw": None,
            "summary": None,
            "lines": [],
            "error": stderr,
        }

    lines = [l for l in stdout.splitlines() if l.strip()]
    summary = lines[0] if lines else None

    return {
        "available": True,
        "raw": stdout,
        "summary": summary,
        "lines": lines,
        "error": None,
    }


# ---------------------------------------------------------------------------
# gather_context
# ---------------------------------------------------------------------------

_ALL_SOURCES = ["date", "todo", "now", "calendar", "budget"]


def gather_context(
    include: list[str] = _ALL_SOURCES,
    calendar_date: str = "today",
    calendar_days: int = 1,
    todo_path: str = _PRAXIS_PATH,
    now_path: str = _NOW_PATH,
    todo_filter: str = "today",
) -> dict[str, Any]:
    """Gather context from all requested sources in parallel.

    Args:
        include:       List of source keys to gather. Any subset of:
                       ["date", "todo", "now", "calendar", "budget"].
        calendar_date: Date argument forwarded to get_calendar().
        calendar_days: Days argument forwarded to get_calendar().
        todo_path:     Path to Praxis.md.
        now_path:      Path to Tonus.md.
        todo_filter:   "today" (default, filters for overdue+today only),
                       "all" (all items), or "none" (skip items parsing).

    Returns:
        Dict with a key per requested source. E.g.:
        {
            "date": { ... },         # get_date() output
            "todo": { ... },         # read_todo_today() or read_todo() output
            "now": { ... },          # read_now() output
            "calendar": { ... },     # get_calendar() output
            "budget": { ... },       # check_budget() output
        }

    Each value is None if the source was not included.
    """
    # Validate requested sources
    unknown = set(include) - set(_ALL_SOURCES)
    if unknown:
        raise ValueError(f"Unknown sources: {unknown}. Valid: {_ALL_SOURCES}")

    # Map source names to callables (date is synchronous and cheap)
    def _gather_date() -> dict:
        return get_date()

    def _gather_todo() -> dict:
        if todo_filter == "today":
            return read_todo_today()
        elif todo_filter == "all":
            return read_todo(path=todo_path)
        else:
            return {"available": False, "path": todo_path, "items": [], "error": "skipped"}

    def _gather_now() -> dict:
        return read_now(path=now_path)

    def _gather_calendar() -> dict:
        return get_calendar(date=calendar_date, days=calendar_days)

    def _gather_budget() -> dict:
        return check_budget()

    dispatch: dict[str, Any] = {
        "date": _gather_date,
        "todo": _gather_todo,
        "now": _gather_now,
        "calendar": _gather_calendar,
        "budget": _gather_budget,
    }

    result: dict[str, Any] = {k: None for k in _ALL_SOURCES}

    # date is synchronous and free — always resolve immediately
    if "date" in include:
        result["date"] = _gather_date()

    # remaining sources in parallel
    parallel_keys = [k for k in include if k != "date"]
    if parallel_keys:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(parallel_keys)) as pool:
            futures = {pool.submit(dispatch[k]): k for k in parallel_keys}
            for future in concurrent.futures.as_completed(futures):
                key = futures[future]
                try:
                    result[key] = future.result()
                except Exception as e:
                    result[key] = {"available": False, "error": str(e)}

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    # Optional: pass source names as args, e.g. python gather.py date todo now
    requested = sys.argv[1:] if len(sys.argv) > 1 else _ALL_SOURCES
    unknown = set(requested) - set(_ALL_SOURCES)
    if unknown:
        print(f"Unknown sources: {unknown}", file=sys.stderr)
        print(f"Valid: {_ALL_SOURCES}", file=sys.stderr)
        sys.exit(1)

    ctx = gather_context(include=requested)
    print(json.dumps(ctx, indent=2, default=str))
