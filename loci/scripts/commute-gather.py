#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
commute-gather -- assemble all context needed by the /commute evening routine.

Deterministic data gathering in one pass; LLM only reasons over the output.

Usage:
  commute-gather           # plain text to stdout
  commute-gather --json    # structured JSON to stdout
"""

import argparse
import concurrent.futures
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

# Shared gather-lib on the path regardless of invocation context
sys.path.insert(0, str(Path.home() / "reticulum" / "lib"))
from gather import gather_context


def _path():
    extra = [
        "/opt/homebrew/bin",
        str(Path.home() / "bin"),
        str(Path.home() / "reticulum" / "bin"),
        str(Path.home() / ".cargo" / "bin"),
        str(Path.home() / ".local" / "bin"),
        str(Path.home() / ".bun" / "bin"),
    ]
    return ":".join(extra) + ":" + os.environ.get("PATH", "")


def run(cmd, timeout=20):
    """Run a command; return (success, output). Never raises."""
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PATH": _path()},
        )
        out = (r.stdout or "").strip()
        err = (r.stderr or "").strip()
        combined = out if out else err
        if r.returncode == 0:
            return (True, combined)
        return (False, combined if combined else "exit %d" % r.returncode)
    except subprocess.TimeoutExpired:
        return (False, "[timed out after %ds]" % timeout)
    except FileNotFoundError:
        return (False, "[command not found: %s]" % cmd[0])
    except Exception as exc:
        return (False, "[error: %s]" % exc)


def read_file(path, max_lines=None):
    try:
        p = Path(str(path)).expanduser()
        if not p.exists():
            return (False, "[file not found: %s]" % p)
        text = p.read_text(encoding="utf-8", errors="replace")
        if max_lines is not None:
            lines = text.splitlines()
            text = "\n".join(lines[:max_lines])
            if len(lines) > max_lines:
                text += "\n... (%d more lines)" % (len(lines) - max_lines)
        return (True, text.strip())
    except Exception as exc:
        return (False, "[read error: %s]" % exc)


# ---------------------------------------------------------------------------
# Convert gather-lib structured results to commute label/ok/content format
# ---------------------------------------------------------------------------


def _ctx_to_section(label, available, content, error=""):
    return {"label": label, "ok": available, "content": content or "(empty)"}


def sections_from_ctx(ctx):
    """Convert gather_context() results into commute-style section dicts."""
    sections = {}

    # datetime
    d = ctx.get("date")
    if d:
        sections["datetime"] = {
            "label": "Current Date / Time",
            "ok": True,
            "content": d.get("datetime", "(unavailable)"),
        }
    else:
        sections["datetime"] = {
            "label": "Current Date / Time",
            "ok": False,
            "content": "(unavailable)",
        }

    # calendar_today
    cal = ctx.get("calendar_today")
    if cal and cal.get("available"):
        content = (
            cal.get("raw", "").strip() or "(no events - calendar may be empty or auth needed)"
        )
        sections["calendar_today"] = {"label": "Today's Calendar", "ok": True, "content": content}
    else:
        err = cal.get("error", "unavailable") if cal else "unavailable"
        sections["calendar_today"] = {
            "label": "Today's Calendar",
            "ok": False,
            "content": "(no events - calendar may be empty or auth needed)",
        }

    # calendar_tomorrow
    cal2 = ctx.get("calendar_tomorrow")
    if cal2 and cal2.get("available"):
        content = cal2.get("raw", "").strip() or "(no events)"
        sections["calendar_tomorrow"] = {
            "label": "Tomorrow's Calendar",
            "ok": True,
            "content": content,
        }
    else:
        sections["calendar_tomorrow"] = {
            "label": "Tomorrow's Calendar",
            "ok": False,
            "content": "(no events)",
        }

    # todo
    todo = ctx.get("todo")
    if todo and todo.get("available"):
        items = todo.get("items", [])
        if items:
            lines = []
            for item in items[:80]:
                done_mark = "x" if item.get("done") else " "
                lines.append("- [{}] {}".format(done_mark, item.get("raw", item.get("text", ""))))
            content = "\n".join(lines)
        else:
            content = "(no TODO items)"
        sections["todo"] = {"label": "Praxis.md (first 80 lines)", "ok": True, "content": content}
    else:
        err = todo.get("error", "unavailable") if todo else "unavailable"
        sections["todo"] = {
            "label": "Praxis.md (first 80 lines)",
            "ok": False,
            "content": "[%s]" % err,
        }

    # now
    now = ctx.get("now")
    if now and now.get("available"):
        content = now.get("raw", "").strip() or "(empty)"
        sections["now"] = {"label": "Tonus (current state)", "ok": True, "content": content}
    else:
        err = now.get("error", "unavailable") if now else "unavailable"
        sections["now"] = {"label": "Tonus (current state)", "ok": False, "content": "[%s]" % err}

    # budget
    budget = ctx.get("budget")
    if budget and budget.get("available"):
        content = budget.get("raw", "").strip() or "(unavailable)"
        sections["budget"] = {
            "label": "Budget / Usage (respirometry)",
            "ok": True,
            "content": content,
        }
    else:
        err = budget.get("error", "unavailable") if budget else "unavailable"
        sections["budget"] = {
            "label": "Budget / Usage (respirometry)",
            "ok": False,
            "content": "[%s]" % err,
        }

    return sections


# ---------------------------------------------------------------------------
# Script-specific gatherers
# ---------------------------------------------------------------------------


def gather_emails():
    ok, out = run(["gog", "gmail", "read", "--unread"], timeout=30)
    if not ok and "[timed out" not in out:
        ok, out = run(["gog", "gmail", "search", "in:inbox", "--limit", "20"], timeout=30)
    return {"label": "Unread Emails (inbox)", "ok": ok, "content": out or "(none)"}


def gather_emails_archived():
    """Safety net: catch emails Cora archived today that skipped the inbox."""
    ok, out = run(
        [
            "gog",
            "gmail",
            "search",
            "newer_than:1d -in:inbox -from:briefs@cora.computer",
            "--plain",
        ],
        timeout=30,
    )
    return {"label": "Today's Archived (Cora safety net)", "ok": ok, "content": out or "(none)"}


def gather_whatsapp():
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    ok, out = run(["wacli", "messages", "list", "--after", yesterday, "--limit", "40"], timeout=15)
    if not ok:
        ok2, out2 = run(["wacli", "chats", "list", "--limit", "20"], timeout=10)
        if ok2:
            return {
                "label": "WhatsApp (recent chats - messages unavailable)",
                "ok": True,
                "content": out2,
            }
        return {"label": "WhatsApp Messages", "ok": False, "content": out}
    return {"label": "WhatsApp Messages (last 24h)", "ok": True, "content": out}


def gather_reminders():
    moneo = str(Path.home() / "bin" / "moneo")
    ok, out = run([moneo, "ls"], timeout=10)
    if not ok:
        ok, out = run(["due", "list"], timeout=10)
        label = "Due Reminders"
    else:
        label = "Reminders (moneo)"
    return {"label": label, "ok": ok, "content": out or "(none)"}


def gather_email_threads():
    ok, out = read_file("~/notes/Email Threads Tracker.md", max_lines=60)
    return {"label": "Email Threads Tracker (first 60 lines)", "ok": ok, "content": out}


def gather_prospective():
    ok, out = read_file(Path.home() / ".claude/projects/-Users-terry/memory/prospective.md")
    return {"label": "Prospective Memory", "ok": ok, "content": out}


# ---------------------------------------------------------------------------
# GATHERERS ordering (preserves original display order)
# ---------------------------------------------------------------------------

SECTION_KEYS = [
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

SCRIPT_GATHERERS = {
    "emails": gather_emails,
    "emails_archived": gather_emails_archived,
    "whatsapp": gather_whatsapp,
    "reminders": gather_reminders,
    "email_threads": gather_email_threads,
    "prospective": gather_prospective,
}


def run_all():
    # Shared sources via gather-lib (parallel I/O within the lib)
    ctx = gather_context(
        include=["date", "now", "budget", "todo"],
        calendar_date="today",
        calendar_days=2,  # today + tomorrow in one call
        todo_filter="all",
    )

    # Calendar: gather-lib returns merged multi-day; split by date for display
    # Fetch today and tomorrow separately for cleaner labels
    import concurrent.futures as _cf

    from gather import get_calendar

    with _cf.ThreadPoolExecutor(max_workers=2) as pool:
        f_today = pool.submit(get_calendar, "today", 1)
        f_tomorrow = pool.submit(get_calendar, "tomorrow", 1)
        ctx["calendar_today"] = f_today.result()
        ctx["calendar_tomorrow"] = f_tomorrow.result()

    results = sections_from_ctx(ctx)

    # Script-specific gatherers in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(SCRIPT_GATHERERS)) as pool:
        futures = {pool.submit(fn): key for key, fn in SCRIPT_GATHERERS.items()}
        for future in concurrent.futures.as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as exc:
                results[key] = {"label": key, "ok": False, "content": "[gatherer error: %s]" % exc}

    # Return in canonical display order
    return {key: results[key] for key in SECTION_KEYS if key in results}


def render_text(results):
    lines = [
        "=" * 70,
        "  COMMUTE CONTEXT BRIEF",
        "=" * 70,
        "",
    ]
    for key, r in results.items():
        status = "" if r["ok"] else "  [PARTIAL / FAILED]"
        lines += [
            "-" * 70,
            "## %s%s" % (r["label"], status),
            "",
            r["content"] if r["content"] else "(empty)",
            "",
        ]
    lines += [
        "=" * 70,
        "  END OF CONTEXT BRIEF",
        "=" * 70,
    ]
    return "\n".join(lines)


def render_json(results):
    return json.dumps(results, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Gather all context for the /commute evening routine."
    )
    parser.add_argument("--json", action="store_true", help="Output structured JSON.")
    args = parser.parse_args()
    results = run_all()
    print(render_json(results) if args.json else render_text(results))


if __name__ == "__main__":
    main()
