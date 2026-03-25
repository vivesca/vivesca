"""Pinocytosis — deterministic context gathering for skills.

Non-specific fluid-phase uptake: the cell drinks from its environment without
selecting what comes in. No LLM calls. Shell out to CLIs, parse vault files,
return structured dicts. Skills reason over the output.

Shared helpers live here. Per-routine modules (interphase, ultradian, etc.)
compose these into routine-specific gathers.
"""

import concurrent.futures
import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# HKT = UTC+8
HKT = timezone(timedelta(hours=8))

PRAXIS_PATH = os.path.expanduser("~/code/vivesca-terry/chromatin/Praxis.md")
TONUS_PATH = os.path.expanduser("~/code/vivesca-terry/chromatin/Tonus.md")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def run_cmd(cmd: list[str], timeout: int = 15) -> tuple[str, str]:
    """Run a subprocess. Returns (stdout, stderr). Never raises."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip()
    except FileNotFoundError:
        return "", f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return "", f"timed out after {timeout}s"
    except Exception as e:
        return "", str(e)


def read_file(path: str | Path, max_lines: int | None = None) -> tuple[bool, str]:
    """Read a file. Returns (ok, content). Never raises."""
    expanded = Path(str(path)).expanduser()
    try:
        if not expanded.exists():
            return False, f"[file not found: {expanded}]"
        text = expanded.read_text(encoding="utf-8", errors="replace")
        if max_lines is not None:
            lines = text.splitlines()
            text = "\n".join(lines[:max_lines])
            if len(lines) > max_lines:
                text += f"\n... ({len(lines) - max_lines} more lines)"
        return True, text.strip()
    except Exception as exc:
        return False, f"[read error: {exc}]"


def _read_file_raw(path: str) -> str | None:
    """Read a file, return content or None on error."""
    expanded = os.path.expanduser(path)
    try:
        with open(expanded, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# current_date
# ---------------------------------------------------------------------------


def current_date() -> dict[str, str]:
    """Return current HKT datetime as structured dict."""
    now = datetime.now(HKT)
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

    tags: dict[str, str] = {}
    for tm in _TAG_RE.finditer(raw_text):
        tags[tm.group("key")] = tm.group("value")

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


def _parse_date(date_str: str | None) -> Any:
    """Parse YYYY-MM-DD string into a date. Returns None on failure."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def recall_todo(
    path: str = PRAXIS_PATH,
    sections: list[str] | None = None,
    tags: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Parse Praxis.md, return structured list of items with metadata."""
    expanded = os.path.expanduser(path)
    raw = _read_file_raw(expanded)

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

        if sections:
            section_lower = current_section.lower()
            if not any(s.lower() in section_lower for s in sections):
                continue

        if tags:
            if not all(item["tags"].get(k) == v for k, v in tags.items()):
                continue

        items.append(item)

    return {"available": True, "path": expanded, "items": items, "error": None}


def recall_todo_today(date_iso: str | None = None) -> dict[str, Any]:
    """Return only overdue and today's TODO items, max 10."""
    if date_iso is None:
        date_iso = current_date()["iso"]

    result = recall_todo()
    if not result["available"]:
        return result

    today = _parse_date(date_iso)
    if today is None:
        return result

    day_of_week = today.weekday()
    day_abbr = today.strftime("%a").lower()

    qualifying: list[dict[str, Any]] = []
    for item in result["items"]:
        if item["done"]:
            continue

        due_str = item.get("due")
        when_str = item.get("when")
        recurring = item.get("recurring", "")

        if due_str:
            d = _parse_date(due_str)
            if d and d <= today:
                qualifying.append(item)
                continue

        if when_str:
            w = _parse_date(when_str)
            if w and w <= today:
                qualifying.append(item)
                continue

        if recurring:
            r = recurring.lower()
            if r == "daily":
                qualifying.append(item)
            elif r == "weekly":
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
                if day_of_week in (0, 2, 4):
                    qualifying.append(item)
            elif r == "biweekly":
                if due_str:
                    d = _parse_date(due_str)
                    if d and d <= today:
                        qualifying.append(item)

    def _sort_key(item: dict[str, Any]) -> tuple:
        d = _parse_date(item.get("due") or "9999-12-31")
        return (d or datetime.max.date(),)

    qualifying.sort(key=_sort_key)

    return {"available": True, "path": result["path"], "items": qualifying[:10], "error": None}


# ---------------------------------------------------------------------------
# read_now (Tonus)
# ---------------------------------------------------------------------------

_H2_RE = re.compile(r"^##\s+(?P<title>.+)$")
_PROGRESS_ITEM_RE = re.compile(
    r"^-\s+\[(?P<state>[^\]]+)\]\s+\*\*(?P<title>[^*]+)\*\*(?P<rest>.*)"
)


def sense_tonus(path: str = TONUS_PATH) -> dict[str, Any]:
    """Parse Tonus.md and return structured facts and progress items."""
    expanded = os.path.expanduser(path)
    raw = _read_file_raw(expanded)

    if raw is None:
        return {
            "available": False, "path": expanded, "facts": [], "progress": [],
            "raw": None, "last_wrap": None, "error": "file not found",
        }

    facts: list[str] = []
    progress: list[dict[str, str]] = []
    current_section = ""
    last_wrap: str | None = None

    for line in raw.splitlines():
        h2 = _H2_RE.match(line)
        if h2:
            current_section = h2.group("title").strip().lower()
            continue

        wrap_match = re.search(r"last (?:wrap|checkpoint):\s*(.+?)-->", line)
        if wrap_match:
            last_wrap = wrap_match.group(1).strip()
            continue

        if "facts" in current_section:
            stripped = line.strip()
            if stripped.startswith("- "):
                fact = re.sub(r"\*\*([^*]+)\*\*", r"\1", stripped[2:]).strip()
                if fact:
                    facts.append(fact)
            continue

        if "progress" in current_section:
            pm = _PROGRESS_ITEM_RE.match(line.strip())
            if pm:
                detail = pm.group("rest").strip()
                detail = re.sub(r"^[.\s]+", "", detail)
                progress.append({
                    "state": pm.group("state").strip(),
                    "title": pm.group("title").strip(),
                    "detail": detail,
                })

    return {
        "available": True, "path": expanded, "facts": facts, "progress": progress,
        "raw": raw, "last_wrap": last_wrap, "error": None,
    }


# ---------------------------------------------------------------------------
# get_calendar
# ---------------------------------------------------------------------------


def sense_calendar(date: str = "today", days: int = 1) -> dict[str, Any]:
    """Shell out to fasti and return parsed calendar events."""
    if days == 1:
        stdout, stderr = run_cmd(["fasti", "list", date])
        if not stdout and stderr:
            return {"available": False, "date": date, "days": days, "raw": None, "events": [], "error": stderr}
        return {"available": True, "date": date, "days": days, "raw": stdout, "events": _parse_fasti_output(stdout), "error": None}

    if date in ("today", "tomorrow"):
        now = datetime.now(HKT)
        base = now.date() if date == "today" else (now.date() + timedelta(days=1))
    else:
        d = _parse_date(date)
        base = d if d else datetime.now(HKT).date()

    all_events: list[dict[str, str]] = []
    all_raw: list[str] = []
    errors: list[str] = []

    for offset in range(days):
        target = base + timedelta(days=offset)
        target_str = target.isoformat()
        stdout, stderr = run_cmd(["fasti", "list", target_str])
        if stderr and not stdout:
            errors.append(f"{target_str}: {stderr}")
        else:
            all_raw.append(stdout)
            for event in _parse_fasti_output(stdout):
                event["date"] = target_str
                all_events.append(event)

    return {
        "available": bool(all_events or not errors),
        "date": date, "days": days, "raw": "\n".join(all_raw),
        "events": all_events, "error": "; ".join(errors) if errors else None,
    }


def _parse_fasti_output(text: str) -> list[dict[str, str]]:
    """Parse fasti list output into event dicts."""
    events: list[dict[str, str]] = []
    if not text:
        return events

    time_range_re = re.compile(
        r"^(?P<time>\d{1,2}:\d{2})"
        r"(?:\s*[-\u2013]\s*(?P<end_time>\d{1,2}:\d{2}))?"
        r"\s+(?P<title>.+)$"
    )
    allday_re = re.compile(r"^(?:All day|all-day|allday)\s+(?P<title>.+)$", re.IGNORECASE)

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        m = time_range_re.match(line)
        if m:
            events.append({"raw_line": line, "time": m.group("time"), "end_time": m.group("end_time") or "", "title": m.group("title").strip(), "all_day": False})
            continue

        m = allday_re.match(line)
        if m:
            events.append({"raw_line": line, "time": "", "end_time": "", "title": m.group("title").strip(), "all_day": True})
            continue

        if not line.startswith("#") and len(line) > 2:
            events.append({"raw_line": line, "time": "", "end_time": "", "title": line, "all_day": False})

    return events


# ---------------------------------------------------------------------------
# assess_budget
# ---------------------------------------------------------------------------


def sense_budget() -> dict[str, Any]:
    """Shell out to respirometry and parse budget status."""
    stdout, stderr = run_cmd(["respirometry"], timeout=20)
    if not stdout and stderr:
        return {"available": False, "raw": None, "summary": None, "lines": [], "error": stderr}
    lines = [l for l in stdout.splitlines() if l.strip()]
    return {"available": True, "raw": stdout, "summary": lines[0] if lines else None, "lines": lines, "error": None}


# ---------------------------------------------------------------------------
# intake_context — composable shared gather
# ---------------------------------------------------------------------------

ALL_SOURCES = ["date", "todo", "now", "calendar", "budget"]


def intake_context(
    include: list[str] | None = None,
    calendar_date: str = "today",
    calendar_days: int = 1,
    todo_path: str = PRAXIS_PATH,
    now_path: str = TONUS_PATH,
    todo_filter: str = "today",
) -> dict[str, Any]:
    """Gather context from all requested sources in parallel."""
    if include is None:
        include = ALL_SOURCES

    unknown = set(include) - set(ALL_SOURCES)
    if unknown:
        raise ValueError(f"Unknown sources: {unknown}. Valid: {ALL_SOURCES}")

    def _gather_todo() -> dict:
        if todo_filter == "today":
            return recall_todo_today()
        elif todo_filter == "all":
            return recall_todo(path=todo_path)
        return {"available": False, "path": todo_path, "items": [], "error": "skipped"}

    dispatch = {
        "date": current_date,
        "todo": _gather_todo,
        "now": lambda: sense_tonus(path=now_path),
        "calendar": lambda: sense_calendar(date=calendar_date, days=calendar_days),
        "budget": sense_budget,
    }

    result: dict[str, Any] = {k: None for k in ALL_SOURCES}

    if "date" in include:
        result["date"] = current_date()

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
# Section formatting helpers (shared across routines)
# ---------------------------------------------------------------------------


def transduce(ctx: dict[str, Any], calendar_keys: dict[str, str] | None = None) -> dict[str, dict]:
    """Convert intake_context() results into {key: {label, ok, content}} section dicts.

    Args:
        ctx: Output of intake_context(), potentially with extra calendar keys.
        calendar_keys: Mapping of ctx keys to labels for calendar sections.
            Default: {"calendar": "Calendar"}.
    """
    if calendar_keys is None:
        calendar_keys = {"calendar": "Calendar"}

    sections: dict[str, dict] = {}

    d = ctx.get("date")
    sections["datetime"] = {
        "label": "Current Date / Time",
        "ok": bool(d),
        "content": d.get("datetime", "(unavailable)") if d else "(unavailable)",
    }

    for key, label in calendar_keys.items():
        cal = ctx.get(key)
        if cal and cal.get("available"):
            content = cal.get("raw", "").strip() or "(no events)"
            sections[key] = {"label": label, "ok": True, "content": content}
        else:
            sections[key] = {"label": label, "ok": False, "content": "(no events)"}

    todo = ctx.get("todo")
    if todo and todo.get("available"):
        items = todo.get("items", [])
        if items:
            lines = []
            for item in items[:80]:
                done_mark = "x" if item.get("done") else " "
                lines.append(f"- [{done_mark}] {item.get('raw', item.get('text', ''))}")
            content = "\n".join(lines)
        else:
            content = "(no TODO items)"
        sections["todo"] = {"label": "Praxis.md", "ok": True, "content": content}
    else:
        err = todo.get("error", "unavailable") if todo else "unavailable"
        sections["todo"] = {"label": "Praxis.md", "ok": False, "content": f"[{err}]"}

    now = ctx.get("now")
    if now and now.get("available"):
        content = now.get("raw", "").strip() or "(empty)"
        sections["now"] = {"label": "Tonus (current state)", "ok": True, "content": content}
    else:
        err = now.get("error", "unavailable") if now else "unavailable"
        sections["now"] = {"label": "Tonus (current state)", "ok": False, "content": f"[{err}]"}

    budget = ctx.get("budget")
    if budget and budget.get("available"):
        content = budget.get("raw", "").strip() or "(unavailable)"
        sections["budget"] = {"label": "Budget (respirometry)", "ok": True, "content": content}
    else:
        err = budget.get("error", "unavailable") if budget else "unavailable"
        sections["budget"] = {"label": "Budget (respirometry)", "ok": False, "content": f"[{err}]"}

    return sections


def secrete_text(title: str, results: dict[str, dict], section_order: list[str]) -> str:
    """Render sections as human-readable text."""
    lines = ["=" * 70, f"  {title}", "=" * 70, ""]
    for key in section_order:
        r = results.get(key)
        if r is None:
            continue
        status = "" if r["ok"] else "  [PARTIAL / FAILED]"
        lines += ["-" * 70, f"## {r['label']}{status}", "", r["content"] or "(empty)", ""]
    lines += ["=" * 70, f"  END OF {title}", "=" * 70]
    return "\n".join(lines)


def secrete_json(results: dict) -> str:
    """Render sections as JSON."""
    return json.dumps(results, indent=2, ensure_ascii=False)
