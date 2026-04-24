"""Scan chromatin frontmatter for approaching deadlines."""

import re
from datetime import date, datetime
from pathlib import Path

SCAN_DIRS = [
    Path.home() / "epigenome" / "chromatin" / "immunity",
    Path.home() / "epigenome" / "chromatin" / "loci" / "plans",
]

WINDOW_DAYS = 7


def scan_deadlines(scan_dirs=SCAN_DIRS, window=WINDOW_DAYS, today=None):
    today = today or date.today()
    results = []
    date_re = re.compile(r"\d{4}-\d{2}-\d{2}")

    for dir_path in scan_dirs:
        if not dir_path.is_dir():
            continue
        for md in dir_path.rglob("*.md"):
            frontmatter = _read_frontmatter(md)
            if not frontmatter:
                continue
            raw = frontmatter.get("deadline", "").strip()
            if not raw:
                continue
            match = date_re.search(raw)
            if not match:
                continue
            deadline_date = date.fromisoformat(match.group())
            days_until = (deadline_date - today).days
            if days_until <= window:
                title = frontmatter.get("title", md.stem)
                results.append({
                    "file": str(md),
                    "title": title,
                    "deadline_raw": raw,
                    "days_until": days_until,
                })

    results.sort(key=lambda r: r["days_until"])
    return results


def _read_frontmatter(path):
    """Parse YAML frontmatter from a markdown file. Returns dict or None."""
    text = path.read_text(errors="replace")
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    yaml_text = text[3:end]
    fm = {}
    for line in yaml_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        colon = line.find(":")
        if colon == -1:
            continue
        key = line[:colon].strip()
        val = line[colon + 1:].strip()
        if val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        fm[key] = val
    return fm


def _format_report(results):
    if not results:
        return "No upcoming deadlines within 7 days."
    lines = []
    for r in results:
        d = r["days_until"]
        label = "today" if d == 0 else f"{d} day{'s' if d != 1 else ''}"
        overdue = "OVERDUE" if d < 0 else ""
        prefix = f"WARNING {overdue}" if d < 0 else "DEADLINE"
        lines.append(f"{prefix} {label}: {r['title']} - {r['deadline_raw']}")
        lines.append(f"  {r['file']}")
    return "\n".join(lines)


if __name__ == "__main__":
    results = scan_deadlines()
    print(_format_report(results))
