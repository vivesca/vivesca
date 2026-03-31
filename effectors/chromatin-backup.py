#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""Chromatin git backup — auto-commit and push if there are changes.

Replaces Obsidian Git plugin (which only runs when app is open).
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

CHROMATIN_DIR = Path.home() / "epigenome" / "chromatin"


def _git(*args: str, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a git command in the chromatin directory."""
    return subprocess.run(
        ["git", *args],
        cwd=CHROMATIN_DIR,
        capture_output=capture,
        text=True,
        check=check,
    )


def _has_changes() -> bool:
    """Return True if there are staged, unstaged, or untracked changes."""
    # Unstaged changes
    if _git("diff", "--quiet", check=False).returncode != 0:
        return True
    # Staged changes
    if _git("diff", "--cached", "--quiet", check=False).returncode != 0:
        return True
    # Untracked files
    result = _git("ls-files", "--others", "--exclude-standard")
    return bool(result.stdout.strip())


def sync_remote() -> None:
    """Fetch and rebase/merge remote changes onto local branch."""
    _git("fetch", "origin", "main", check=False)

    local = _git("rev-parse", "HEAD").stdout.strip()
    remote = _git("rev-parse", "origin/main", check=False).stdout.strip()

    if local == remote:
        return

    # Try rebase first
    rebase = _git("rebase", "origin/main", check=False,
                   env={**__import__("os").environ, "GIT_EDITOR": "true"})
    if rebase.returncode == 0:
        return

    # Rebase failed — abort and try merge
    _git("rebase", "--abort", check=False)
    merge = _git("merge", "origin/main", "--no-edit", check=False)
    if merge.returncode == 0:
        return

    # Merge failed — accept theirs as last resort
    _git("checkout", "--theirs", ".", check=False)
    _git("add", "-A")
    _git("commit", "--no-edit", check=False,
         env={**__import__("os").environ, "GIT_EDITOR": "true"})


def backup() -> bool:
    """Commit and push if there are changes. Returns True if pushed."""
    if not CHROMATIN_DIR.is_dir():
        print(f"Chromatin directory not found: {CHROMATIN_DIR}", file=sys.stderr)
        sys.exit(1)

    sync_remote()

    if not _has_changes():
        return False

    _git("add", "-A")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _git("commit", "-m", f"chromatin backup: {timestamp}")
    _git("push", "origin", "main")
    return True


def main() -> None:
    backup()


if __name__ == "__main__":
    main()
