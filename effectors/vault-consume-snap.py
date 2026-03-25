#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Snapshot Obsidian's lastOpenFiles to a JSONL consumption log.

Reads ~/code/vivesca-terry/chromatin/.obsidian/workspace.json, extracts the lastOpenFiles array,
and appends a timestamped entry to ~/code/vivesca-terry/chromatin/.consumption-log.jsonl.
Skips if the file list is identical to the last snapshot (deduplication).
"""

import json
import time
from pathlib import Path

VAULT = Path.home() / "code" / "vivesca-terry" / "chromatin"
WORKSPACE = VAULT / ".obsidian" / "workspace.json"
LOG_FILE = VAULT / ".consumption-log.jsonl"


def read_last_open_files() -> list[str]:
    data = json.loads(WORKSPACE.read_text())
    return data.get("lastOpenFiles", [])


def read_last_snapshot() -> list[str] | None:
    if not LOG_FILE.exists():
        return None
    # Read last line
    with LOG_FILE.open("rb") as f:
        f.seek(0, 2)
        size = f.tell()
        if size == 0:
            return None
        # Scan backwards for last newline
        pos = size - 1
        while pos > 0:
            f.seek(pos)
            if f.read(1) == b"\n" and pos < size - 1:
                break
            pos -= 1
        if pos == 0:
            f.seek(0)
        line = f.readline().decode().strip()
        if not line:
            return None
        return json.loads(line).get("files")


def main() -> None:
    if not WORKSPACE.exists():
        return

    current_files = read_last_open_files()
    if not current_files:
        return

    last_files = read_last_snapshot()
    if last_files == current_files:
        return  # No change since last snapshot

    entry = {"ts": int(time.time()), "files": current_files}
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    main()
