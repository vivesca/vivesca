#!/usr/bin/env python3
"""14-day rolling trend of late_correction=Y and filed=N from cytokinesis session logs."""

import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

DAILY_DIR = Path("~/epigenome/chromatin/Daily").expanduser()
SESSION_DIR = Path("~/.claude/projects/-home-vivesca/sessions").expanduser()
WINDOW = 14


def _parse_daily(directory: Path) -> dict[date, list[dict]]:
    by_date: dict[date, list[dict]] = defaultdict(list)
    if not directory.is_dir():
        return by_date
    for p in sorted(directory.glob("*.md")):
        try:
            d = date.fromisoformat(p.stem)
        except ValueError:
            continue
        for line in p.read_text(errors="replace").splitlines():
            m_filed = re.search(r"filed=(\d+)", line)
            if not m_filed:
                continue
            m_lc = re.search(r"late_correction=([YN])", line)
            by_date[d].append({
                "filed": int(m_filed.group(1)),
                "late_correction": m_lc.group(1) if m_lc else None,
            })
    return by_date


def _parse_sessions(directory: Path) -> dict[date, list[dict]]:
    by_date: dict[date, list[dict]] = defaultdict(list)
    if not directory.is_dir():
        return by_date
    for p in directory.glob("*.jsonl"):
        d = date.fromtimestamp(p.stat().st_mtime)
        text = p.read_text(errors="replace")
        for line in text.splitlines():
            m_filed = re.search(r"filed=(\d+)", line)
            if not m_filed:
                continue
            m_lc = re.search(r"late_correction=([YN])", line)
            by_date[d].append({
                "filed": int(m_filed.group(1)),
                "late_correction": m_lc.group(1) if m_lc else None,
            })
    return by_date


def gather() -> dict[date, list[dict]]:
    merged: dict[date, list[dict]] = defaultdict(list)
    for src in (_parse_daily(DAILY_DIR), _parse_sessions(SESSION_DIR)):
        for d, entries in src.items():
            merged[d].extend(entries)
    return merged


def rolling_trend(entries: dict[date, list[dict]], end: date | None = None) -> list[dict]:
    end = end or date.today()
    start = end - timedelta(days=WINDOW - 1)
    rows = []
    for offset in range(WINDOW):
        d = start + timedelta(days=offset)
        sessions = entries.get(d, [])
        total = len(sessions)
        late = sum(1 for s in sessions if s["late_correction"] == "Y")
        lc_denom = sum(1 for s in sessions if s["late_correction"] is not None)
        filed_sum = sum(s["filed"] for s in sessions)
        rows.append({
            "date": d,
            "sessions": total,
            "late_pct": round(100 * late / lc_denom, 1) if lc_denom else None,
            "filed": filed_sum,
        })
    return rows


def summary() -> str:
    rows = rolling_trend(gather())
    lines = [f"{'date':>12s}  {'sess':>4s}  {'late%':>6s}  {'filed':>5s}"]
    lines.append("-" * 34)
    for r in rows:
        late = f"{r['late_pct']:.1f}" if r["late_pct"] is not None else "—"
        lines.append(f"{r['date']!s:>12s}  {r['sessions']:>4d}  {late:>6s}  {r['filed']:>5d}")
    total_sessions = sum(r["sessions"] for r in rows)
    total_filed = sum(r["filed"] for r in rows)
    lc_rows = [r for r in rows if r["late_pct"] is not None]
    avg_late = sum(r["late_pct"] for r in lc_rows) / len(lc_rows) if lc_rows else 0
    lines.append("-" * 34)
    lines.append(f"{WINDOW}-day totals: {total_sessions} sessions, "
                 f"{total_filed} filed, {avg_late:.1f}% avg late_correction")
    return "\n".join(lines)


if __name__ == "__main__":
    print(summary())
