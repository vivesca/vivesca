#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Oura weekly digest — fetches 7-day health data via oura CLI and saves a
clean markdown note to ~/code/epigenome/chromatin/Daily/Oura Weekly - YYYY-MM-DD.md.
"""

import re
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path


def strip_ansi(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


OURA_BIN = Path.home() / "code" / "oura-cli" / "target" / "release" / "oura"


def run(cmd: list[str]) -> str:
    # Replace 'oura' with full path if not on PATH
    if cmd[0] == "oura":
        cmd = [str(OURA_BIN)] + cmd[1:]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return strip_ansi(result.stdout).strip()


def parse_trend_table(raw: str) -> list[dict]:
    """Parse `oura trend` output into list of row dicts."""
    rows = []
    for line in raw.splitlines():
        line = line.strip()
        # Skip header and average lines
        if not line or line.startswith("Date") or line.startswith("Average"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        # Date is first two tokens (e.g. "Sat Feb 28") or three tokens
        # Format: "Sat Feb 28  88  88  92" or "Sat Feb 28  88  88  --"
        # Find where numbers/dashes start
        try:
            # Day-of-week + Month + Day = 3 tokens
            date_str = " ".join(parts[:3])
            scores = parts[3:]
            sleep = scores[0] if len(scores) > 0 else "--"
            readiness = scores[1] if len(scores) > 1 else "--"
            activity = scores[2] if len(scores) > 2 else "--"
            rows.append({
                "date": date_str,
                "sleep": sleep,
                "readiness": readiness,
                "activity": activity,
            })
        except (IndexError, ValueError):
            continue
    return rows


def compute_avg(values: list[str]) -> str:
    nums = [int(v) for v in values if v not in ("--", "")]
    if not nums:
        return "--"
    return str(round(sum(nums) / len(nums)))


def trend_arrow(values: list[str]) -> str:
    nums = [int(v) for v in values if v not in ("--", "")]
    if len(nums) < 3:
        return ""
    recent = nums[-3:]
    older = nums[:-3]
    if not older:
        return ""
    recent_avg = sum(recent) / len(recent)
    older_avg = sum(older) / len(older)
    diff = recent_avg - older_avg
    if diff >= 3:
        return " (trending up)"
    elif diff <= -3:
        return " (trending down)"
    return " (stable)"


def format_section(label: str, raw: str) -> str:
    if not raw:
        return f"*No data*"
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    return "\n".join(f"- {l}" for l in lines)


def main():
    today = date.today()
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")

    # Fetch data
    trend_raw = run(["oura", "trend", "--days", "7"])
    sleep_raw = run(["oura", "sleep", yesterday_str])
    readiness_raw = run(["oura", "readiness", yesterday_str])
    activity_raw = run(["oura", "activity", yesterday_str])
    hrv_raw = run(["oura", "hrv", yesterday_str])

    rows = parse_trend_table(trend_raw)

    sleeps = [r["sleep"] for r in rows]
    readinesses = [r["readiness"] for r in rows]
    activities = [r["activity"] for r in rows]

    avg_sleep = compute_avg(sleeps)
    avg_readiness = compute_avg(readinesses)
    avg_activity = compute_avg(activities)

    sleep_trend = trend_arrow(sleeps)
    readiness_trend = trend_arrow(readinesses)
    activity_trend = trend_arrow(activities)

    # Build markdown table
    table_lines = [
        "| Date | Sleep | Readiness | Activity |",
        "|------|------:|----------:|---------:|",
    ]
    for r in rows:
        table_lines.append(
            f"| {r['date']} | {r['sleep']} | {r['readiness']} | {r['activity']} |"
        )
    table_lines.append(
        f"| **Average** | **{avg_sleep}** | **{avg_readiness}** | **{avg_activity}** |"
    )
    table = "\n".join(table_lines)

    # Compose note
    note_date = today.strftime("%Y-%m-%d")
    note = f"""---
date: {note_date}
tags: [oura, health, weekly]
---

# Oura Weekly Digest — {note_date}

## 7-Day Scores

{table}

**Trends (last 3 vs prior 4 days):** Sleep{sleep_trend} · Readiness{readiness_trend} · Activity{activity_trend}

## Yesterday's Detail ({yesterday_str})

### Sleep
{format_section("Sleep", sleep_raw)}

### Readiness
{format_section("Readiness", readiness_raw)}

### HRV & Recovery
{format_section("HRV", hrv_raw)}

### Activity
{format_section("Activity", activity_raw)}
"""

    # Save note
    output_path = Path.home() / "notes" / "Daily" / f"Oura Weekly - {note_date}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(note)

    # One-line summary to stdout
    # Pull yesterday's scores directly from rows if available
    yesterday_label = yesterday.strftime("%a %b %-d")
    yesterday_row = next(
        (r for r in rows if r["date"].strip() == yesterday_label), None
    )
    if yesterday_row:
        s, r2, a = yesterday_row["sleep"], yesterday_row["readiness"], yesterday_row["activity"]
    else:
        s, r2, a = avg_sleep, avg_readiness, avg_activity

    print(
        f"Oura 7d: sleep avg {avg_sleep} · readiness avg {avg_readiness} · "
        f"activity avg {avg_activity} | yesterday: sleep {s}, readiness {r2}, activity {a} "
        f"| saved {output_path}"
    )


if __name__ == "__main__":
    main()
