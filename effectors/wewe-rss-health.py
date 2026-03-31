#!/usr/bin/env python3
from __future__ import annotations

"""Wechat2RSS health check — alerts via Telegram when service is unhealthy.

Run via LaunchAgent every 6h. Only alerts on state *changes* to avoid spam.
Re-auth: localhost:8001 → scan QR with WeChat.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

STATE_FILE = Path.home() / ".wewe-rss-health.json"
API_URL = "http://localhost:8001/list?k=werss2026"
TG_SCRIPT = Path.home() / "scripts" / "tg-notify.sh"


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"last_status": "ok"}


def save_state(state: dict) -> None:
    tmp = STATE_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state))
    tmp.replace(STATE_FILE)


def send_alert(msg: str) -> None:
    if TG_SCRIPT.exists():
        subprocess.run([str(TG_SCRIPT), msg], timeout=10)
    else:
        print(msg, file=sys.stderr)


def check_service() -> tuple[bool, str]:
    try:
        req = urllib.request.Request(API_URL)
        resp = json.load(urllib.request.urlopen(req, timeout=10))
    except Exception as e:
        return False, f"API unreachable: {e}"

    if resp.get("err"):
        return False, f"API error: {resp['err']}"

    feeds = resp.get("data", [])
    if not feeds:
        return False, "no feeds configured"

    paused = [f for f in feeds if f.get("paused")]
    if paused:
        return False, f"{len(paused)}/{len(feeds)} feeds paused"

    return True, f"{len(feeds)} feed(s) active"


def main():
    parser = argparse.ArgumentParser(description="Wechat2RSS health check — alerts via Telegram when service is unhealthy.")
    parser.parse_args()

    state = load_state()
    healthy, detail = check_service()

    current = "ok" if healthy else "failing"
    prev = state.get("last_status", "ok")

    if current == "failing" and prev == "ok":
        send_alert(
            f"🔴 Wechat2RSS unhealthy — {detail}\n"
            f"Re-auth: localhost:8001 → scan QR"
        )
    elif current == "ok" and prev == "failing":
        send_alert(f"✅ Wechat2RSS recovered — {detail}")

    save_state({"last_status": current, "checked": datetime.now().isoformat()})


if __name__ == "__main__":
    main()
