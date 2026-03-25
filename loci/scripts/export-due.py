#!/usr/bin/env -S uv run --script --python 3.13
"""Export Due.duedb reminders to readable markdown for git changelog."""

import gzip
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DUEDB = (
    Path.home()
    / "Library/Containers/com.phocusllp.duemac/Data/Library/Application Support/Due App/Due.duedb"
)
EXPORT = Path.home() / "code/epigenome/chromatin/Due Backup/reminders.md"
HKT = ZoneInfo("Asia/Hong_Kong")

RECUR = {"d": "daily", "w": "weekly", "m": "monthly", "y": "yearly", "": ""}


def ts(epoch):
    if not epoch:
        return "—"
    return datetime.fromtimestamp(epoch, tz=HKT).strftime("%Y-%m-%d %H:%M")


with gzip.open(DUEDB, "rt") as f:
    data = json.load(f)

reminders = sorted(data.get("re", []), key=lambda r: r.get("d", 0))

lines = [
    "# Due Reminders Export",
    f"<!-- generated {ts(None or __import__('time').time())} HKT -->",
    "",
]
for r in reminders:
    recur = RECUR.get(r.get("rf", ""), "")
    recur_str = f" ↻ {recur}" if recur else ""
    lines.append(f"- **{r['n']}**  due {ts(r.get('d', 0))}{recur_str}")

EXPORT.write_text("\n".join(lines) + "\n")
print(f"Exported {len(reminders)} reminders → {EXPORT}")
