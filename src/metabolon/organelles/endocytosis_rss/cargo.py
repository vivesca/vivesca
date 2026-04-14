"""JSONL canonical cargo store for endocytosis.

Biology: the early endosome collects all internalized cargo in one lumen.
This module is that lumen -- a single JSONL append log where every article
lands after endosomal sorting. All downstream readers (digest, weekly,
expression) query this store; markdown becomes a generated view.

Schema per line (one JSON object):
    timestamp, date, title, source, link, summary, score,
    banking_angle, talking_point, fate
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


def append_cargo(cargo_path: Path, articles: list[dict[str, Any]]) -> None:
    """Append scored articles to the JSONL cargo store."""
    cargo_path.parent.mkdir(parents=True, exist_ok=True)
    with cargo_path.open("a", encoding="utf-8") as fh:
        for article in articles:
            fh.write(json.dumps(article, ensure_ascii=False) + "\n")


def recall_cargo(
    cargo_path: Path,
    since: str | None = None,
    month: str | None = None,
) -> list[dict[str, Any]]:
    """Read cargo from the JSONL store, optionally filtered by date range.

    Args:
        cargo_path: Path to the JSONL file.
        since: ISO date string (inclusive). Only return entries with date >= since.
        month: YYYY-MM string. Only return entries whose date starts with this prefix.

    Returns:
        List of article dicts in file order.
    """
    if not cargo_path.exists():
        return []

    entries: list[dict[str, Any]] = []
    for line in cargo_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue

        entry_date = str(entry.get("date", ""))

        if since and entry_date < since:
            continue
        if month and not entry_date.startswith(month):
            continue

        entries.append(entry)
    return entries


def recall_title_prefixes(cargo_path: Path) -> set[str]:
    """Extract title prefixes from the cargo store for deduplication."""
    if not cargo_path.exists():
        return set()

    prefixes: set[str] = set()
    for line in cargo_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue
        title = str(entry.get("title", ""))
        prefix = _title_prefix(title)
        if prefix:
            prefixes.add(prefix)
    return prefixes


def _title_prefix(title: str) -> str:
    """Extract a normalized prefix for deduplication (matches log.py logic)."""
    words = re.sub(r"[^\w\s]", "", title.lower()).split()
    sig = [w for w in words if len(w) > 2][:6]
    return " ".join(sig)


def rotate_cargo(
    cargo_path: Path,
    archive_dir: Path,
    retain_days: int = 14,
    now: datetime | None = None,
) -> None:
    """Rotate old entries out of the active cargo store into monthly archives.

    Entries older than retain_days are moved to archive_dir/cargo-YYYY-MM.jsonl.
    """
    if now is None:
        now = datetime.now(UTC)

    if not cargo_path.exists():
        return

    cutoff = (now - timedelta(days=retain_days)).strftime("%Y-%m-%d")
    keep: list[str] = []
    archive_buckets: dict[str, list[str]] = {}

    for line in cargo_path.read_text(encoding="utf-8").splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue
        try:
            entry = json.loads(line_stripped)
        except json.JSONDecodeError:
            keep.append(line)
            continue
        if not isinstance(entry, dict):
            keep.append(line)
            continue

        entry_date = str(entry.get("date", ""))
        if entry_date < cutoff:
            month = entry_date[:7] if len(entry_date) >= 7 else "unknown"
            archive_buckets.setdefault(month, []).append(line_stripped)
        else:
            keep.append(line_stripped)

    if not archive_buckets:
        return

    archive_dir.mkdir(parents=True, exist_ok=True)
    for month, lines in archive_buckets.items():
        archive_path = archive_dir / f"cargo-{month}.jsonl"
        with archive_path.open("a", encoding="utf-8") as fh:
            for archived_line in lines:
                fh.write(archived_line + "\n")

    _atomic_write_lines(cargo_path, keep)


def _atomic_write_lines(path: Path, lines: list[str]) -> None:
    """Write lines atomically via tempfile + fsync + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            for line in lines:
                tmp_file.write(line + "\n")
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
