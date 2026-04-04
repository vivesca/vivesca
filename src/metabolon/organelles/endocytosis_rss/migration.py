
"""One-time migration: markdown news log -> JSONL cargo store."""

import re
from pathlib import Path
from typing import Any

from metabolon.organelles.endocytosis_rss.cargo import append_cargo


def migrate_markdown_to_jsonl(md_path: Path, cargo_path: Path) -> int:
    """Parse the markdown news log and write entries to JSONL.

    Returns the number of entries migrated.
    """
    if not md_path.exists():
        return 0

    entries: list[dict[str, Any]] = []
    current_date = ""
    current_source = ""

    for line in md_path.read_text(encoding="utf-8").splitlines():
        date_match = re.match(r"^## (\d{4}-\d{2}-\d{2})", line)
        if date_match:
            current_date = date_match.group(1)
            continue

        source_match = re.match(r"^### (.+)", line)
        if source_match:
            current_source = source_match.group(1).strip()
            continue

        article_match = re.match(
            r"^- (?:\[.\] )?\*\*(?:\[([^\]]+)\]\(([^)]+)\)|([^*]+))\*\*"
            r"(?:\s*\(banking_angle: ([^)]+)\))?"
            r"(?:\s*\(([^)]*)\))?"
            r"(?:\s*(?:--|---)\s*(.+))?",
            line,
        )
        if article_match:
            title = (article_match.group(1) or article_match.group(3) or "").strip()
            if not title:
                continue
            is_transcytose = line.lstrip().startswith("- [") and "]" in line[:10]
            score = 7 if is_transcytose else 5  # approximate; exact score lost in markdown
            entries.append(
                {
                    "timestamp": f"{current_date}T00:00:00+00:00",
                    "date": article_match.group(5) or current_date,
                    "title": title,
                    "source": current_source,
                    "link": article_match.group(2) or "",
                    "summary": article_match.group(6) or "",
                    "score": score,
                    "banking_angle": article_match.group(4) or "N/A",
                    "talking_point": "N/A",
                    "fate": "transcytose" if is_transcytose else "store",
                }
            )

    if entries:
        append_cargo(cargo_path, entries)
    return len(entries)
