from __future__ import annotations

"""Request logging for MCP tool calls — JSONL persistence of tool name, duration, and outcome."""


import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from metabolon.locus import requests_log

logger = logging.getLogger(__name__)

DEFAULT_REQUEST_LOG = requests_log


class RequestLogger:
    """Append-only JSONL logger for MCP tool-call requests.

    Each entry: {"ts": <ISO-8601>, "tool": <name>, "duration_ms": <int>, "success": <bool>}
    """

    def __init__(self, path: Path = DEFAULT_REQUEST_LOG) -> None:
        self._path = Path(path)

    def log(self, *, tool: str, duration_ms: int, success: bool) -> None:
        """Append a single request entry to the JSONL log."""
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "tool": tool,
            "duration_ms": duration_ms,
            "success": success,
        }
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            logger.debug("Request log write failed for %s", tool, exc_info=True)
