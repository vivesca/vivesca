"""secretory_vesicle — Telegram export (formerly deltos).

Endosymbiosis: Rust binary → Python organelle.
Credentials: macOS keychain (telegram-bot-token, telegram-chat-id).
"""

import json
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

_API_BASE = "https://api.telegram.org"
_LOCK = Path("/tmp/deltos.lock")


def _keychain(service: str) -> str:
    """Read credential from macOS keychain."""
    r = subprocess.run(
        ["security", "find-generic-password", "-s", service, "-w"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0 or not r.stdout.strip():
        raise ValueError(f"Keychain credential missing: {service}")
    return r.stdout.strip()


def _rate_limit() -> None:
    """Enforce 1-second rate limit between sends."""
    if _LOCK.exists():
        elapsed = time.time() - _LOCK.stat().st_mtime
        if elapsed < 1:
            time.sleep(1 - elapsed)


def _html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def secrete_text(text: str, html: bool = True, label: str = "") -> str:
    """Send text to Telegram channel."""
    token = _keychain("telegram-bot-token")
    chat_id = _keychain("telegram-chat-id")
    _rate_limit()

    body = text if html else f"<pre>{_html_escape(text)}</pre>"

    if label:
        body = f"<b>{_html_escape(label)}</b>\n{body}"

    data = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
            "text": body,
        }
    ).encode()

    req = urllib.request.Request(f"{_API_BASE}/bot{token}/sendMessage", data=data)
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())

    _LOCK.touch()

    if not result.get("ok"):
        raise ValueError(f"Telegram error: {result.get('description', 'unknown')}")
    return "sent"


def secrete_image(path: str, caption: str = "") -> str:
    """Send photo to Telegram channel."""
    token = _keychain("telegram-bot-token")
    chat_id = _keychain("telegram-chat-id")
    _rate_limit()

    p = Path(path).expanduser()
    if not p.is_file():
        raise ValueError(f"File not found: {p}")

    args = ["curl", "-s", "-F", f"chat_id={chat_id}", "-F", f"photo=@{p}"]
    if caption:
        args.extend(["-F", f"caption={caption}"])
    args.append(f"{_API_BASE}/bot{token}/sendPhoto")

    r = subprocess.run(args, capture_output=True, text=True, timeout=30)
    result = json.loads(r.stdout)

    _LOCK.touch()

    if not result.get("ok"):
        raise ValueError(f"Telegram error: {result.get('description', 'unknown')}")
    return "photo sent"
