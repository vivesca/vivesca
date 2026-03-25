#!/usr/bin/env python3
"""PreCompact hook — log compaction to daily note for continuity."""

import json
import sys
from datetime import datetime
from pathlib import Path


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    custom = data.get("custom_instructions", "")
    ts = datetime.now().strftime("%H:%M")

    daily = Path.home() / "notes" / "Daily" / f"{datetime.now().strftime('%Y-%m-%d')}.md"
    if daily.exists():
        with daily.open("a") as f:
            f.write(f"\n**Compact ({ts}):** {custom or 'auto'}\n")


if __name__ == "__main__":
    main()
