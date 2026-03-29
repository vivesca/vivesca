"""chromatin — file-based memory store.

Oghma retired (Mar 2026). This organelle now reads/writes markdown files
in ~/epigenome/marks/ — the canonical memory location.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

MARKS_DIR = Path.home() / "epigenome" / "marks"


def recall(
    query: str,
    category: str = "",
    source_enzyme: str = "",
    limit: int = 10,
    mode: str = "hybrid",
    chromatin: str = "open",
) -> list[dict]:
    """Search marks by regex match on content."""
    results = []
    for f in sorted(MARKS_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        text = f.read_text(errors="replace")
        if not re.search(query, text, re.IGNORECASE):
            continue
        if category and f"category: {category}" not in text:
            continue
        # Extract name from frontmatter
        name_match = re.search(r"^name:\s*(.+)$", text, re.MULTILINE)
        name = name_match.group(1).strip() if name_match else f.stem
        results.append({"file": f.name, "name": name, "content": text[:500], "path": str(f)})
        if len(results) >= limit:
            break
    return results


def inscribe(content: str, category: str = "gotcha", confidence: float = 0.8) -> dict:
    """Add a memory as a markdown file in marks/."""
    slug = re.sub(r"[^a-z0-9-]", "", content[:50].lower().replace(" ", "-"))[:40]
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
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
    return {"status": "saved", "path": str(path), "file": filename}


def search(
    query: str,
    category: str = "",
    source_enzyme: str = "",
    limit: int = 10,
    mode: str = "hybrid",
    chromatin: str = "open",
) -> list[dict]:
    """Alias for recall() — histone_search tool calls this name."""
    return recall(query, category=category, source_enzyme=source_enzyme, limit=limit, mode=mode, chromatin=chromatin)


def add(content: str, category: str = "gotcha", confidence: float = 0.8) -> dict:
    """Alias for inscribe() — histone_mark tool calls this name."""
    return inscribe(content, category=category, confidence=confidence)


def stats() -> dict:
    """Memory file statistics."""
    files = list(MARKS_DIR.glob("*.md"))
    total_size = sum(f.stat().st_size for f in files)
    return {"count": len(files), "size_kb": round(total_size / 1024), "path": str(MARKS_DIR)}


def status() -> str:
    """Marks directory status."""
    files = list(MARKS_DIR.glob("*.md"))
    total_size = sum(f.stat().st_size for f in files)
    return f"Marks: {MARKS_DIR} ({len(files)} files, {total_size / 1024:.0f}KB)"
