#!/usr/bin/env python3
from __future__ import annotations

# /// script
# requires-python = ">=3.11"
# ///
"""Mitosis checkpoint — watchdog for DR sync health.

In cell biology, the spindle assembly checkpoint ensures mitosis completes
correctly before the cell proceeds. This effector monitors soma sync
freshness and self-heals before alerting.

Logic:
  1. Call mitosis.status() to check each target
  2. If any target is stale/unreachable, attempt mitosis.sync() for those targets
  3. Re-check status
  4. Alert via deltos ONLY if repair fails

Silent when healthy. Runs via pacemaker every 30 min.
Throttling handled by secretory_vesicle transport layer (cooldown_key).
"""

import argparse
import sys
from pathlib import Path

# Ensure metabolon is importable (effector may run outside venv)
_venv = Path.home() / "germline" / ".venv" / "lib"
if _venv.exists():
    for p in sorted(_venv.glob("python*/site-packages")):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))

ALERT_COOLDOWN_SECONDS = 24 * 3600


def check_and_heal() -> None:
    from metabolon.organelles.mitosis import status, sync

    info = status()

    # Unreachable = machine down, can't self-heal.
    # But transient API blips happen — wait and re-check once before alerting.
    if not info["reachable"]:
        import time
        time.sleep(15)
        info = status()
        if not info["reachable"]:
            _alert("Soma UNREACHABLE — fly machine may be stopped.",
                   cooldown_key="mitosis-unreachable")
            return

    # Find stale or missing targets
    sick = [
        name
        for name, state in info["targets"].items()
        if state.get("state") in ("stale", "missing", "unknown")
    ]

    if not sick:
        return  # All healthy, stay silent

    # Attempt self-heal: sync only the sick targets
    report = sync(targets=sick)

    if report.ok and all(r.success for r in report.results if r.target in sick):
        # Verify with a fresh status check
        info2 = status()
        still_sick = [
            name
            for name in sick
            if info2["targets"].get(name, {}).get("state") not in ("ok",)
        ]
        if not still_sick:
            return  # Healed silently

        _alert(
            f"Mitosis checkpoint: self-heal ran but targets still degraded: "
            f"{', '.join(still_sick)}",
            cooldown_key="mitosis-degraded",
        )
    else:
        failed = [r for r in report.results if not r.success]
        details = "; ".join(f"{r.target}: {r.message}" for r in failed[:3])
        _alert(f"Mitosis checkpoint: sync repair failed — {details}",
               cooldown_key="mitosis-sync-failed")


def _alert(message: str, cooldown_key: str = "") -> None:
    """Alert via Telegram. Throttling delegated to secretory_vesicle."""
    print(f"ALERT: {message}", file=sys.stderr)
    try:
        from metabolon.organelles.secretory_vesicle import secrete_text

        result = secrete_text(
            f"[mitosis-checkpoint] {message}",
            html=False,
            label="DR alert",
            cooldown_key=cooldown_key,
            cooldown_seconds=ALERT_COOLDOWN_SECONDS,
        )
        if result == "throttled":
            print(f"THROTTLED by transport: {message}", file=sys.stderr)
    except Exception as exc:
        print(f"Telegram send failed: {exc}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mitosis checkpoint — watchdog for DR sync health."
    )
    parser.parse_args()

    try:
        check_and_heal()
    except Exception as exc:
        _alert(f"Checkpoint crashed: {exc}", cooldown_key="mitosis-crashed")
        sys.exit(1)


if __name__ == "__main__":
    main()
