#!/usr/bin/env python3
"""Stop hook — trigger memory consolidation after session activity.

Real hippocampal consolidation happens during sleep (between activity),
not on a calendar. This fires consolidation at session end — the
organism's rest phase.

Debounced: skips if last run was <6 hours ago.
Runs in background — never blocks session exit.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

STATE_FILE = Path.home() / ".local/share/respirometry/consolidation-last.json"
MIN_INTERVAL = 6 * 3600  # 6 hours


def main():
    # Debounce — don't run on every stop
    try:
        state = json.loads(STATE_FILE.read_text())
        last_run = state.get("ts", 0)
        if time.time() - last_run < MIN_INTERVAL:
            sys.exit(0)
    except Exception:
        pass

    # Fire consolidation in background
    try:
        subprocess.Popen(
            ["vivesca", "metabolism", "dissolve", "--days", "30"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({"ts": time.time()}))
    except Exception:
        pass  # Never block session exit

    sys.exit(0)


if __name__ == "__main__":
    main()
