#!/usr/bin/env python3
from __future__ import annotations

"""Set up tmux workspace with research-backed tab layout.

One deep-work tab (CC) + stateless utility tabs.
See ~/docs/solutions/cognitive-switching-costs.md for rationale.

Usage:
    tmux-workspace              # set up windows in current session (if in tmux)
                                # or create 'main' session (if outside tmux)
    tmux-workspace dev          # use 'dev' layout (cc|shell|test|logs)
    tmux-workspace --help
"""

from __future__ import annotations

import os
import subprocess
import sys


LAYOUTS = {
    "default": [
        ("main", None),         # Tab 1: deep work — holds context, long sessions
        ("light", None),        # Tab 2: quick CC — todos, lookups, weather, short tasks
    ],
    "dev": [
        ("main", None),         # Tab 1: deep work
        ("light", None),        # Tab 2: quick CC
        ("shell", None),        # Tab 3: git, builds, raw shell when needed
    ],
}


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check, timeout=30)


def get_current_session() -> str | None:
    """Get the current tmux session name, if inside tmux."""
    if "TMUX" not in os.environ:
        return None
    result = run("tmux display-message -p '#S'", check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def get_existing_windows(session: str) -> list[str]:
    """Get list of window names in a session."""
    result = run(f"tmux list-windows -t {session} -F '#{{window_name}}'", check=False)
    if result.returncode != 0:
        return []
    return result.stdout.strip().split("\n")


def setup_windows(session: str, layout_name: str) -> None:
    """Create the layout windows in an existing session."""
    windows = LAYOUTS[layout_name]
    existing = get_existing_windows(session)

    # Rename first window if it exists
    if existing:
        run(f"tmux rename-window -t {session}:1 {windows[0][0]}", check=False)

    # Create missing windows
    for i, (name, cmd) in enumerate(windows[1:], start=2):
        if i <= len(existing):
            # Window exists at this index — rename it
            run(f"tmux rename-window -t {session}:{i} {name}", check=False)
        else:
            # Create new window
            run(f"tmux new-window -t {session} -n {name}")
            if cmd:
                run(f"tmux send-keys -t {session}:{name} '{cmd}' Enter")

    # Select first window (deep work)
    run(f"tmux select-window -t {session}:1")
    print(f"Workspace ready: {' | '.join(w[0] for w in windows)}")


def create_and_attach(session_name: str, layout_name: str) -> None:
    """Create a new session with the layout and attach."""
    windows = LAYOUTS[layout_name]
    first_name = windows[0][0]
    run(f"tmux new-session -d -s {session_name} -n {first_name}")

    for name, cmd in windows[1:]:
        run(f"tmux new-window -t {session_name} -n {name}")
        if cmd:
            run(f"tmux send-keys -t {session_name}:{name} '{cmd}' Enter")

    run(f"tmux select-window -t {session_name}:1")
    print(f"Workspace '{session_name}' created: {' | '.join(w[0] for w in windows)}")
    subprocess.run(f"tmux attach-session -t {session_name}", shell=True, timeout=300)


def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        print("Available layouts:", ", ".join(LAYOUTS.keys()))
        return

    arg = sys.argv[1] if len(sys.argv) > 1 else None
    layout = arg if arg in LAYOUTS else "default"

    current = get_current_session()

    if current:
        # Inside tmux — set up windows in current session
        setup_windows(current, layout)
    else:
        # Outside tmux — create new session
        session_name = arg if arg and arg not in LAYOUTS else "main"
        result = run(f"tmux has-session -t {session_name} 2>/dev/null", check=False)
        if result.returncode == 0:
            # Session exists — set up windows and attach
            setup_windows(session_name, layout)
            subprocess.run(f"tmux attach-session -t {session_name}", shell=True, timeout=300)
        else:
            create_and_attach(session_name, layout)


if __name__ == "__main__":
    main()
