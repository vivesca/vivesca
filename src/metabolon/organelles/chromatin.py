from __future__ import annotations

"""chromatin — file-based memory store.

Oghma retired (Mar 2026). This organelle now reads/writes markdown files
in ~/epigenome/marks/ — the canonical memory location.

Performance: an in-memory index caches frontmatter fields and file content
so that repeated queries hit RAM instead of disk. The index is lazy-loaded
on first access and auto-refreshed on writes.
"""


import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

MARKS_DIR = Path.home() / "epigenome" / "marks"

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML frontmatter key-value pairs from mark text."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta


class _MarkIndex:
    """In-memory index over mark files for fast filtering.

    Stores per-file: name, type, source, category, mtime, and full content.
    Supports lookup by frontmatter field and invalidation on writes.
    """

    def __init__(self, marks_dir: Path) -> None:
        self._dir = marks_dir
        self._entries: dict[str, dict[str, Any]] = {}  # filename -> metadata
        self._by_field: dict[str, dict[str, set[str]]] = {}  # field -> value -> {filenames}
        self._loaded = False

    def _load_one(self, filepath: Path) -> None:
        """Index a single mark file, skipping corrupt/unreadable ones."""
        name_key = filepath.name
        try:
            text = filepath.read_text(errors="replace")
            meta = _parse_frontmatter(text)
            mtime = filepath.stat().st_mtime
        except (OSError, ValueError) as exc:
            logger.warning("Skipping unreadable mark %s: %s", filepath.name, exc)
            return

        entry = {
            "name": meta.get("name", filepath.stem),
            "type": meta.get("type", ""),
            "source": meta.get("source", ""),
            "category": meta.get("category", ""),
            "mtime": mtime,
            "content": text,
            "path": str(filepath),
            "file": filepath.name,
        }
        self._entries[name_key] = entry

        # Update inverted index for filterable fields
        for field in ("type", "source", "category", "name"):
            value = entry.get(field, "")
            if not value:
                continue
            field_idx = self._by_field.setdefault(field, {})
            bucket = field_idx.setdefault(value, set())
            bucket.add(name_key)

    def ensure_loaded(self) -> None:
        """Load all marks from disk on first call (lazy init)."""
        if self._loaded:
            return
        self._loaded = True
        self._entries.clear()
        self._by_field.clear()
        if not self._dir.is_dir():
            logger.warning("Marks directory missing: %s", self._dir)
            self._dir.mkdir(parents=True, exist_ok=True)
            return
        for filepath in self._dir.glob("*.md"):
            self._load_one(filepath)
        logger.info("Mark index loaded: %d files", len(self._entries))

    def reload(self) -> None:
        """Force a full reload on next access."""
        self._loaded = False

    def invalidate(self, filename: str) -> None:
        """Remove a single file from the index (will be re-read on next query)."""
        old_entry = self._entries.pop(filename, None)
        if old_entry:
            # Remove from inverted index
            for field in ("type", "source", "category", "name"):
                value = old_entry.get(field, "")
                if value and field in self._by_field and value in self._by_field[field]:
                    self._by_field[field][value].discard(filename)
        self._load_one(self._dir / filename)

    def query(
        self,
        regex: str,
        category: str = "",
        source_enzyme: str = "",
        limit: int = 10,
    ) -> list[dict]:
        """Search indexed marks. Filters by category/source_enzyme first, then regex."""
        self.ensure_loaded()

        # Determine candidate set via index (or all if no field filter)
        candidates: set[str] | None = None
        if category:
            cat_set = self._by_field.get("category", {}).get(category)
            if cat_set is None:
                return []  # category value doesn't exist at all
            candidates = set(cat_set)
        if source_enzyme:
            src_set = self._by_field.get("source", {}).get(source_enzyme)
            if src_set is None:
                return []
            candidates = candidates & src_set if candidates is not None else set(src_set)

        # Build sorted list by mtime (newest first)
        if candidates is not None:
            pool = [self._entries[k] for k in candidates if k in self._entries]
        else:
            pool = list(self._entries.values())
        pool.sort(key=lambda e: e["mtime"], reverse=True)

        # Regex match on cached content
        pattern = re.compile(regex, re.IGNORECASE)
        results: list[dict] = []
        for entry in pool:
            if not pattern.search(entry["content"]):
                continue
            results.append(
                {
                    "file": entry["file"],
                    "name": entry["name"],
                    "content": entry["content"][:500],
                    "path": entry["path"],
                }
            )
            if len(results) >= limit:
                break
        return results

    @property
    def entry_count(self) -> int:
        self.ensure_loaded()
        return len(self._entries)

    @property
    def total_bytes(self) -> int:
        self.ensure_loaded()
        return sum(len(e["content"].encode()) for e in self._entries.values())

    def stale_marks(self, days: int = 180) -> list[dict[str, Any]]:
        """Return all marks that haven't been modified in more than `days` days.

        Entries are sorted from oldest to newest.
        """
        self.ensure_loaded()
        now = datetime.now(UTC).timestamp()
        cutoff = now - (days * 86400)
        stale = [
            {
                "file": entry["file"],
                "name": entry["name"],
                "type": entry["type"],
                "mtime_days": round((now - entry["mtime"]) / 86400, 1),
                "path": entry["path"],
            }
            for entry in self._entries.values()
            if entry["mtime"] < cutoff
        ]
        stale.sort(key=lambda x: x["mtime_days"], reverse=True)
        return stale

    def type_counts(self) -> dict[str, int]:
        """Return counts of marks by their type field.

        Only counts non-empty type values.
        """
        self.ensure_loaded()
        counts: dict[str, int] = {}
        for entry in self._entries.values():
            typ = entry.get("type", "").strip()
            if typ:
                counts[typ] = counts.get(typ, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))


# Module-level singleton index — shared across all calls in a process
_index = _MarkIndex(MARKS_DIR)


def recall(
    query: str,
    category: str = "",
    source_enzyme: str = "",
    limit: int = 10,
    mode: str = "hybrid",
    chromatin: str = "open",
) -> list[dict]:
    """Search marks by regex match on content, using in-memory index."""
    return _index.query(query, category=category, source_enzyme=source_enzyme, limit=limit)


def inscribe(content: str, category: str = "gotcha", confidence: float = 0.8) -> dict:
    """Add a memory as a markdown file in marks/."""
    if not MARKS_DIR.is_dir():
        MARKS_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9-]", "", content[:50].lower().replace(" ", "-"))[:40]
    ts = datetime.now(UTC).strftime("%Y%m%d-%H%M")
    filename = f"auto_{slug}_{ts}.md"
    path = MARKS_DIR / filename
    path.write_text(
        f"---\n"
        f"name: {slug}\n"
        f"description: {content[:80]}\n"
        f"type: finding\n"
        f"source: mcp\n"
        f"category: {category}\n"
        f"confidence: {confidence}\n"
        f"---\n\n"
        f"{content}\n"
    )
    # Invalidate just the new file in the index
    _index.invalidate(filename)
    return {"status": "saved", "path": str(path), "file": filename}


def search(
    query: str,
    category: str = "",
    source_enzyme: str = "",
    limit: int = 10,
    mode: str = "hybrid",
    chromatin: str = "open",
) -> list[dict]:
    """Alias for recall() — histone tool calls this name."""
    return recall(
        query,
        category=category,
        source_enzyme=source_enzyme,
        limit=limit,
        mode=mode,
        chromatin=chromatin,
    )


def add(content: str, category: str = "gotcha", confidence: float = 0.8) -> dict:
    """Alias for inscribe() — histone_mark tool calls this name."""
    return inscribe(content, category=category, confidence=confidence)


def stats() -> dict:
    """Memory file statistics."""
    return {
        "count": _index.entry_count,
        "size_kb": round(_index.total_bytes / 1024),
        "path": str(MARKS_DIR),
    }


def status() -> str:
    """Marks directory status."""
    count = _index.entry_count
    size_kb = _index.total_bytes / 1024
    return f"Marks: {MARKS_DIR} ({count} files, {size_kb:.0f}KB)"


def stale_marks(days: int = 180) -> list[dict[str, Any]]:
    """Return all stale marks (not modified in > N days)."""
    return _index.stale_marks(days=days)


def type_counts() -> dict[str, int]:
    """Return counts of marks by type."""
    return _index.type_counts()
