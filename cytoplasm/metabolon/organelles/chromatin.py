"""chromatin — memory database (formerly oghma).

Endosymbiosis: external Python package → organelle import.
Oghma's Storage class is imported directly instead of subprocess.
Supports chromatin accessibility states (open/closed).
"""

from pathlib import Path

_DB_PATH = Path.home() / ".local" / "share" / "oghma" / "memories.db"
_storage = None


def _get_storage():
    """Lazy-init Storage to avoid import overhead."""
    global _storage
    if _storage is None:
        from oghma.storage import Storage

        _storage = Storage(str(_DB_PATH))
    return _storage


def search(
    query: str,
    category: str = "",
    source_enzyme: str = "",
    limit: int = 10,
    mode: str = "hybrid",
    chromatin: str = "open",
) -> list[dict]:
    """Search memories with chromatin accessibility control.

    chromatin: 'open' (active), 'closed' (archived), 'all'
    """
    s = _get_storage()
    status = None
    if chromatin == "open":
        status = "active"
    elif chromatin == "closed":
        status = "archived"

    if mode == "hybrid":
        results = s.search_memories_hybrid(
            query,
            limit=limit,
            category=category or None,
            source_tool=source_enzyme or None,
            status=status,
        )
    else:
        results = s.search_memories(
            query,
            limit=limit,
            category=category or None,
            source_tool=source_enzyme or None,
            status=status,
        )
    return results


def add(content: str, category: str = "gotcha", confidence: float = 0.8) -> dict:
    """Add a memory (histone mark)."""
    s = _get_storage()
    return s.add_memory(
        content=content,
        category=category,
        confidence=confidence,
        source_tool="metabolon",
        source_file="direct",
    )


def stats() -> dict:
    """Memory database statistics."""
    s = _get_storage()
    return s.get_stats() if hasattr(s, "get_stats") else {"status": "ok"}


def status() -> str:
    """Database status: path, exists, size."""
    exists = _DB_PATH.exists()
    size = _DB_PATH.stat().st_size if exists else 0
    return f"DB: {_DB_PATH} ({'exists' if exists else 'missing'}, {size / 1024:.0f}KB)"
