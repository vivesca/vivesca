#!/usr/bin/env python3
"""terminus.py — consolidated Stop hook.

Replaces: proofreading.js, checkpoint.js, anabolism-checkpoint.py, consolidation-stop.py
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()

# Repo root: hooks → claude → vivesca
_VIVESCA_ROOT = Path(__file__).resolve().parent.parent.parent


# ── dirty repo check (from proofreading.js) ────────────────

REPOS = [
    ("vivesca", _VIVESCA_ROOT),
    ("skills", HOME / "skills"),
    ("notes", HOME / "notes"),
]


def mod_dirty_repos():
    dirty = []
    for name, path in REPOS:
        try:
            r = subprocess.run(
                ["git", "-C", str(path), "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = [l for l in r.stdout.strip().split("\n") if l.strip()]
            if lines:
                dirty.append(f"{name} ({len(lines)} file{'s' if len(lines) > 1 else ''})")
        except Exception:
            pass
    if dirty:
        print(f"Uncommitted changes: {', '.join(dirty)}. Commit before closing.")


# ── contract enforcer (from checkpoint.js) ──────────────────

CONTRACTS_DIR = HOME / ".claude" / "contracts"


def mod_contracts():
    if not CONTRACTS_DIR.exists():
        return
    blockers = []
    for f in CONTRACTS_DIR.glob("*.md"):
        content = f.read_text(encoding="utf-8")
        unchecked = len(re.findall(r"^- \[ \]", content, re.MULTILINE))
        if unchecked:
            blockers.append(f"{f.name}: {unchecked} unchecked item{'s' if unchecked > 1 else ''}")
    if blockers:
        items = "\n".join(f"  - {b}" for b in blockers)
        print(
            f"CONTRACT NOT FULFILLED:\n{items}\n\nComplete all items or run: /contract clear <name>"
        )
        sys.exit(2)


# ── anabolism guard (from anabolism-checkpoint.py) ──────────

ANAB_LOCK = HOME / "tmp" / ".anabolism-guard-active"


def mod_anabolism():
    # stdin already consumed by main, pass through
    if not ANAB_LOCK.exists():
        return
    try:
        r = subprocess.run(
            ["respirometry-cached", "--budget"], capture_output=True, text=True, timeout=2
        )
        budget = r.stdout.strip().lower() or "unknown"
    except Exception:
        budget = "unknown"

    if budget == "green":
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": "[ANABOLISM GUARD] Budget GREEN, interactive anabolism active. Keep dispatching.",
                }
            )
        )
    elif budget == "yellow":
        print(
            json.dumps(
                {
                    "reason": "[ANABOLISM GUARD] Budget YELLOW. Finish current systole, write report, then stop."
                }
            )
        )


# ── consolidation (from consolidation-stop.py) ─────────────

CONSOL_STATE = HOME / ".local/share/respirometry/consolidation-last.json"
CONSOL_INTERVAL = 6 * 3600


def mod_consolidation():
    try:
        state = json.loads(CONSOL_STATE.read_text())
        if time.time() - state.get("ts", 0) < CONSOL_INTERVAL:
            return
    except Exception:
        pass

    try:
        subprocess.Popen(
            ["vivesca", "metabolism", "dissolve", "--days", "30"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        CONSOL_STATE.parent.mkdir(parents=True, exist_ok=True)
        CONSOL_STATE.write_text(json.dumps({"ts": time.time()}))
    except Exception:
        pass


# ── main ───────────────────────────────────────────────────


def main():
    for mod in [mod_contracts, mod_dirty_repos, mod_anabolism, mod_consolidation]:
        try:
            mod()
        except SystemExit:
            raise
        except Exception:
            pass


if __name__ == "__main__":
    main()
