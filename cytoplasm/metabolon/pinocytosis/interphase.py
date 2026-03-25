"""Interphase gather — evening routine context.

Collects: inbox, archived emails, WhatsApp, calendar (today + tomorrow),
Praxis, Tonus, budget, reminders, email threads tracker, prospective memory.
"""

import concurrent.futures
import datetime
import json
from pathlib import Path

from metabolon.pinocytosis import (
    gather_context,
    get_calendar,
    read_file,
    render_json,
    render_text,
    run_cmd,
    sections_from_ctx,
)

# ---------------------------------------------------------------------------
# Interphase-specific gatherers
# ---------------------------------------------------------------------------


def gather_emails() -> dict:
    ok, out = run_cmd(["gog", "gmail", "read", "--unread"], timeout=30)
    if not ok and "[timed out" not in out:
        ok, out = run_cmd(["gog", "gmail", "search", "in:inbox", "--limit", "20"], timeout=30)
    return {"label": "Unread Emails (inbox)", "ok": ok, "content": out or "(none)"}


def gather_emails_archived() -> dict:
    """Catch emails Cora archived today that skipped the inbox."""
    ok, out = run_cmd(
        ["gog", "gmail", "search", "newer_than:1d -in:inbox -from:briefs@cora.computer", "--plain"],
        timeout=30,
    )
    return {"label": "Today's Archived (Cora safety net)", "ok": ok, "content": out or "(none)"}


def gather_whatsapp() -> dict:
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    ok, out = run_cmd(["wacli", "messages", "list", "--after", yesterday, "--limit", "40"], timeout=15)
    if not ok:
        ok2, out2 = run_cmd(["wacli", "chats", "list", "--limit", "20"], timeout=10)
        if ok2:
            return {"label": "WhatsApp (recent chats - messages unavailable)", "ok": True, "content": out2}
        return {"label": "WhatsApp Messages", "ok": False, "content": out}
    return {"label": "WhatsApp Messages (last 24h)", "ok": True, "content": out}


def gather_reminders() -> dict:
    ok, out = run_cmd(["moneo", "ls"], timeout=10)
    if not ok:
        ok, out = run_cmd(["due", "list"], timeout=10)
        label = "Due Reminders"
    else:
        label = "Reminders (moneo)"
    return {"label": label, "ok": ok, "content": out or "(none)"}


def gather_email_threads() -> dict:
    ok, out = read_file("~/notes/Email Threads Tracker.md", max_lines=60)
    return {"label": "Email Threads Tracker", "ok": ok, "content": out}


def gather_prospective() -> dict:
    ok, out = read_file(Path.home() / ".claude/projects/-Users-terry/memory/prospective.md")
    return {"label": "Prospective Memory", "ok": ok, "content": out}


# ---------------------------------------------------------------------------
# Section ordering and dispatch
# ---------------------------------------------------------------------------

SECTION_ORDER = [
    "datetime",
    "emails",
    "emails_archived",
    "whatsapp",
    "calendar_today",
    "calendar_tomorrow",
    "todo",
    "now",
    "budget",
    "reminders",
    "email_threads",
    "prospective",
]

_SCRIPT_GATHERERS = {
    "emails": gather_emails,
    "emails_archived": gather_emails_archived,
    "whatsapp": gather_whatsapp,
    "reminders": gather_reminders,
    "email_threads": gather_email_threads,
    "prospective": gather_prospective,
}


def intake(as_json: bool = True) -> str:
    """Run full interphase gather. Returns formatted string."""
    ctx = gather_context(
        include=["date", "now", "budget", "todo"],
        calendar_date="today",
        calendar_days=2,
        todo_filter="all",
    )

    # Calendar: fetch today and tomorrow separately for cleaner labels
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        f_today = pool.submit(get_calendar, "today", 1)
        f_tomorrow = pool.submit(get_calendar, "tomorrow", 1)
        ctx["calendar_today"] = f_today.result()
        ctx["calendar_tomorrow"] = f_tomorrow.result()

    results = sections_from_ctx(
        ctx,
        calendar_keys={"calendar_today": "Today's Calendar", "calendar_tomorrow": "Tomorrow's Calendar"},
    )

    # Interphase-specific gatherers in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(_SCRIPT_GATHERERS)) as pool:
        futures = {pool.submit(fn): key for key, fn in _SCRIPT_GATHERERS.items()}
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as exc:
                results[key] = {"label": key, "ok": False, "content": f"[gatherer error: {exc}]"}

    ordered = {key: results[key] for key in SECTION_ORDER if key in results}

    if as_json:
        return render_json(ordered)
    return render_text("INTERPHASE CONTEXT BRIEF", ordered, SECTION_ORDER)


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Gather context for /interphase evening routine.")
    parser.add_argument("--json", action="store_true", help="Output structured JSON.")
    args = parser.parse_args()
    print(gather(as_json=args.json))


if __name__ == "__main__":
    main()
