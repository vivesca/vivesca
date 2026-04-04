#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""
Oura weekly digest — fetches 7-day health data via chemoreceptor organelle
and saves a clean markdown note to ~/epigenome/chromatin/Daily/Oura Weekly - YYYY-MM-DD.md.
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure we can import metabolon
sys.path.append(str(Path.home() / "germline"))

try:
    from metabolon.organelles import chemoreceptor
except ImportError:
    print(
        "Error: metabolon.organelles.chemoreceptor not found. Ensure germline is in PATH.",
        file=sys.stderr,
    )
    sys.exit(1)


def compute_avg(values: list[int | None]) -> str:
    nums = [v for v in values if v is not None]
    if not nums:
        return "--"
    return str(round(sum(nums) / len(nums)))


def trend_arrow(values: list[int | None]) -> str:
    nums = [v for v in values if v is not None]
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


def format_section(label: str, data: dict) -> str:
    if not data or "error" in data:
        return "*No data available*"

    lines = []
    for k, v in data.items():
        if isinstance(v, dict):
            lines.append(f"- **{k.replace('_', ' ').title()}**: {len(v)} items")
        else:
            lines.append(f"- **{k.replace('_', ' ').title()}**: {v}")
    return "\n".join(lines)


def main():
    today_dt = date.today()
    yesterday_dt = today_dt - timedelta(days=1)

    try:
        # Fetch 7-day trend
        week_data = chemoreceptor.week(days=7)
        # Fetch yesterday's detail
        detail = chemoreceptor.sense()  # sense() defaults to today's data (last night)
    except Exception as e:
        print(f"Error fetching Oura data: {e}", file=sys.stderr)
        sys.exit(1)

    if not week_data:
        print("No Oura data found for the past 7 days.")
        sys.exit(0)

    # Build trend table
    table_lines = [
        "| Date | Sleep | Readiness | Activity |",
        "|------|------:|----------:|---------:|",
    ]

    sleeps = []
    readinesses = []
    # Note: chemoreceptor.week() doesn't currently include activity score,
    # but we can add it if needed. For now let's use what's available.

    for day in week_data:
        d = day["date"]
        s = day.get("sleep_score")
        r = day.get("readiness_score")
        # Activity score is not in week() yet, but let's assume it might be there or use placeholder
        a = "--"

        sleeps.append(s)
        readinesses.append(r)

        s_str = str(s) if s is not None else "--"
        r_str = str(r) if r is not None else "--"
        table_lines.append(f"| {d} | {s_str} | {r_str} | {a} |")

    avg_sleep = compute_avg(sleeps)
    avg_readiness = compute_avg(readinesses)

    sleep_trend = trend_arrow(sleeps)
    readiness_trend = trend_arrow(readinesses)

    table_lines.append(f"| **Average** | **{avg_sleep}** | **{avg_readiness}** | **--** |")
    table = "\n".join(table_lines)

    # Compose note
    note_date = today_dt.strftime("%Y-%m-%d")

    # Detail sections
    sleep_detail = detail.get("sleep_score", "--")
    readiness_detail = detail.get("readiness_score", "--")
    activity_detail = detail.get("activity", {}).get("score", "--")

    note = f"""---
date: {note_date}
tags: [oura, health, weekly]
---

# Oura Weekly Digest — {note_date}

## 7-Day Scores

{table}

**Trends (last 3 vs prior 4 days):** Sleep{sleep_trend} · Readiness{readiness_trend}

## Yesterday's Detail ({yesterday_dt})

### Sleep
- **Score**: {sleep_detail}
{format_section("Sleep Contributors", detail.get("sleep_contributors", {}))}

### Readiness
- **Score**: {readiness_detail}
{format_section("Readiness Contributors", detail.get("contributors", {}))}

### Activity
- **Score**: {activity_detail}
{format_section("Activity", detail.get("activity", {}))}
"""

    # Save note
    output_path = Path.home() / "notes" / "Daily" / f"Oura Weekly - {note_date}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(note)

    print(f"Oura 7d: sleep avg {avg_sleep} · readiness avg {avg_readiness} | saved {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__.strip(),
    )
    parser.parse_args()
    main()
