#!/usr/bin/env python3
"""InstructionsLoaded hook — log which context files load and when."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

LOG = Path.home() / ".claude" / "context-audit.log"


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    file_path = data.get("file_path", "unknown")
    memory_type = data.get("memory_type", "unknown")
    load_reason = data.get("load_reason", "unknown")

    ts = datetime.now().strftime("%H:%M:%S")
    with LOG.open("a") as f:
        f.write(f"{ts}\t{memory_type}\t{load_reason}\t{file_path}\n")


if __name__ == "__main__":
    main()
