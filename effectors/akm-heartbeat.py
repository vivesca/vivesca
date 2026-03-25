#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""AKM Heartbeat — nightly vault health digest via Telegram.

Scans ~/code/vivesca-terry/chromatin/ for stale notes, orphan links, overdue TODOs, and
prospective memory items due. Sends a consolidated morning digest
via deltos (Telegram). Designed to feed into /zeitgeber.

Runs as a LaunchAgent: com.terry.akm-heartbeat
"""

import re
import shutil
import subprocess
import sys
import time
from datetime import date, datetime
from pathlib import Path

VAULT = Path.home() / "code" / "vivesca-terry" / "chromatin"
MEMORY_DIR = Path.home() / ".claude" / "projects" / "-Users-terry" / "memory"
PRAXIS_FILE = VAULT / "Praxis.md"
PROSPECTIVE_FILE = MEMORY_DIR / "prospective.md"
STALE_DAYS = 30
MAX_STALE_REPORT = 10
MAX_ORPHAN_REPORT = 10

# Directories to exclude from stale scan
EXCLUDE_DIRS = {
    ".obsidian",
    ".git",
    ".claude",
    ".trash",
    "Archive",
    "Templates",
    "Attachments",
    "assets",
}


def scan_stale_notes() -> list[tuple[str, int]]:
    """Find notes not modified in STALE_DAYS+ days. Returns (name, days_stale)."""
    cutoff = time.time() - (STALE_DAYS * 86400)
    stale: list[tuple[str, int]] = []

    for md in VAULT.rglob("*.md"):
        # Skip excluded directories
        if any(part in EXCLUDE_DIRS for part in md.relative_to(VAULT).parts):
            continue
        # Skip hidden files
        if md.name.startswith("."):
            continue
        try:
            mtime = md.stat().st_mtime
        except OSError:
            continue
        if mtime < cutoff:
            days = int((time.time() - mtime) / 86400)
            stale.append((md.stem, days))

    stale.sort(key=lambda x: -x[1])
    return stale[:MAX_STALE_REPORT]


def scan_orphan_links() -> list[str]:
    """Find notes with no incoming links using obsidian CLI."""
    try:
        result = subprocess.run(
            ["obsidian", "vault=notes", "orphans"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        orphans = [
            line.strip()
            for line in result.stdout.strip().splitlines()
            if line.strip() and not line.strip().startswith("(")
        ]
        return orphans[:MAX_ORPHAN_REPORT]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def scan_overdue_todos() -> list[str]:
    """Scan Praxis.md for overdue items (lines with past dates)."""
    if not PRAXIS_FILE.exists():
        return []

    today = date.today()
    overdue: list[str] = []
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")

    for line in PRAXIS_FILE.read_text().splitlines():
        stripped = line.strip()
        if not stripped.startswith("- [ ]"):
            continue
        match = date_pattern.search(stripped)
        if not match:
            continue
        try:
            due = datetime.strptime(match.group(), "%Y-%m-%d").date()
        except ValueError:
            continue
        if due < today:
            # Extract the task text (remove checkbox prefix)
            task = stripped.removeprefix("- [ ]").strip()
            days_late = (today - due).days
            overdue.append(f"{task} ({days_late}d overdue)")

    return overdue


def scan_prospective_memory() -> list[str]:
    """Check prospective memory for items triggered by date proximity."""
    if not PROSPECTIVE_FILE.exists():
        return []

    today = date.today()
    triggered: list[str] = []
    content = PROSPECTIVE_FILE.read_text()

    # Find the ## Active section
    in_active = False
    for line in content.splitlines():
        if line.strip() == "## Active":
            in_active = True
            continue
        if line.startswith("## ") and in_active:
            break
        if not in_active or not line.strip().startswith("- WHEN:"):
            continue

        # Check for date-based triggers
        date_pattern = re.compile(
            r"(?:~?\s*)?((?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+)?(\w{3}\s+\d{1,2})"
        )
        # Also check for "any session" or "next session" triggers
        if "any session" in line or "next session" in line:
            # Extract the THEN action
            then_match = re.search(r"→ THEN:\s*(.+?)(?:\(added:|\Z)", line)
            if then_match:
                action = then_match.group(1).strip()
                if len(action) > 100:
                    action = action[:97] + "..."
                triggered.append(action)
        # Check for specific month+day triggers near today
        month_day = re.search(r"(\w{3})\s+(\d{1,2})", line)
        if month_day:
            try:
                month_str = month_day.group(1)
                day = int(month_day.group(2))
                month_map = {
                    "Jan": 1,
                    "Feb": 2,
                    "Mar": 3,
                    "Apr": 4,
                    "May": 5,
                    "Jun": 6,
                    "Jul": 7,
                    "Aug": 8,
                    "Sep": 9,
                    "Oct": 10,
                    "Nov": 11,
                    "Dec": 12,
                }
                month = month_map.get(month_str)
                if month:
                    trigger_date = date(today.year, month, day)
                    if abs((trigger_date - today).days) <= 3:
                        then_match = re.search(r"→ THEN:\s*(.+?)(?:\(added:|\Z)", line)
                        if then_match:
                            action = then_match.group(1).strip()
                            if len(action) > 100:
                                action = action[:97] + "..."
                            triggered.append(action)
            except (ValueError, KeyError):
                pass

    # Deduplicate
    return list(dict.fromkeys(triggered))


def build_digest() -> str:
    """Build the consolidated digest message."""
    sections: list[str] = []
    today_str = date.today().isoformat()

    # Header
    sections.append(f"🫀 AKM Heartbeat — {today_str}")

    # Stale notes
    stale = scan_stale_notes()
    if stale:
        lines = [f"📦 Stale Notes ({len(stale)}+ not touched in {STALE_DAYS}d):"]
        for name, days in stale[:5]:
            lines.append(f"  · {name} ({days}d)")
        if len(stale) > 5:
            lines.append(f"  ... +{len(stale) - 5} more")
        sections.append("\n".join(lines))

    # Orphan links
    orphans = scan_orphan_links()
    if orphans:
        lines = [f"🔗 Orphan Notes ({len(orphans)} with no backlinks):"]
        for name in orphans[:5]:
            lines.append(f"  · {name}")
        if len(orphans) > 5:
            lines.append(f"  ... +{len(orphans) - 5} more")
        sections.append("\n".join(lines))

    # Overdue TODOs
    overdue = scan_overdue_todos()
    if overdue:
        lines = [f"⏰ Overdue TODOs ({len(overdue)}):"]
        for item in overdue[:5]:
            lines.append(f"  · {item}")
        if len(overdue) > 5:
            lines.append(f"  ... +{len(overdue) - 5} more")
        sections.append("\n".join(lines))

    # Prospective memory
    prospective = scan_prospective_memory()
    if prospective:
        lines = [f"🧠 Prospective Reminders ({len(prospective)}):"]
        for item in prospective[:5]:
            lines.append(f"  · {item}")
        if len(prospective) > 5:
            lines.append(f"  ... +{len(prospective) - 5} more")
        sections.append("\n".join(lines))

    if len(sections) == 1:
        sections.append("✅ Vault looks healthy — nothing flagged.")

    return "\n\n".join(sections)


def send_via_deltos(message: str) -> bool:
    """Send message via deltos binary.

    deltos takes [LABEL] [CONTENT] — pass a label as the first arg
    and pipe the digest body via stdin so it doesn't block on empty input
    in LaunchAgent context.
    """
    try:
        result = subprocess.run(
            [shutil.which("deltos") or "deltos", "AKM Heartbeat"],
            input=message.encode(),
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace").strip()
            print(f"deltos exited {result.returncode}: {stderr}", file=sys.stderr)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"deltos send failed: {exc}", file=sys.stderr)
        return False


def main() -> None:
    digest = build_digest()
    print(digest)  # Log to stdout (captured by LaunchAgent)

    if not send_via_deltos(digest):
        print("WARNING: Failed to send via deltos", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
