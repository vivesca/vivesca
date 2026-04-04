"""secretory_vesicle — Telegram export (formerly deltos).

Endosymbiosis: Rust binary → Python organelle.
Credentials: macOS keychain (telegram-bot-token, telegram-chat-id).
"""

import hashlib
import json
import os
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

_API_BASE = "https://api.telegram.org"
_LOCK = Path(tempfile.gettempdir()) / "deltos.lock"
_COOLDOWN_FILE = Path.home() / "tmp" / "secrete-cooldowns.json"


def _keychain(service: str) -> str:
    """Read credential from macOS keychain or 1Password on Linux."""
    import platform
    import shutil

    # macOS: use native keychain
    if platform.system() == "Darwin" and shutil.which("security"):
        r = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-w"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()

    # Linux/fallback: check env vars first (set by importin/op-inject)
    env_map = {
        "telegram-bot-token": "TELEGRAM_BOT_TOKEN",
        "telegram-chat-id": "TELEGRAM_CHAT_ID",
    }
    env_var = env_map.get(service, "")
    if env_var and os.environ.get(env_var):
        return os.environ[env_var].strip()

    # Last resort: 1Password CLI
    op_map = {
        "telegram-bot-token": "op://Agents/Agent Environment/telegram_bot_token",
        "telegram-chat-id": "op://Agents/Agent Environment/telegram_chat_id",
    }
    op_ref = op_map.get(service)
    if op_ref:
        op_bin = shutil.which("op") or os.path.expanduser("~/bin/op")
        r = subprocess.run(
            [op_bin, "read", op_ref],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()

    raise ValueError(f"Credential not found: {service} (tried keychain, env, op)")


def _rate_limit() -> None:
    """Enforce 1-second rate limit between sends."""
    if _LOCK.exists():
        elapsed = time.time() - _LOCK.stat().st_mtime
        if elapsed < 1:
            time.sleep(1 - elapsed)


def _html_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _is_cooled_down(key: str, cooldown_seconds: int) -> bool:
    """Return True if this key was sent within the cooldown window."""
    now = time.time()
    stamps: dict = {}
    if _COOLDOWN_FILE.exists():
        try:
            stamps = json.loads(_COOLDOWN_FILE.read_text())
        except json.JSONDecodeError, OSError:
            stamps = {}
    last_sent = stamps.get(key, 0)
    if now - last_sent < cooldown_seconds:
        return True
    stamps[key] = now
    # Prune entries older than 48h
    stamps = {digest: ts for digest, ts in stamps.items() if now - ts < 48 * 3600}
    _COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
    _COOLDOWN_FILE.write_text(json.dumps(stamps))
    return False


def secrete_text(
    text: str,
    html: bool = True,
    label: str = "",
    cooldown_key: str = "",
    cooldown_seconds: int = 0,
) -> str:
    """Send text to Telegram channel.

    Args:
        cooldown_key: If set, suppress duplicate sends with the same key
            within cooldown_seconds. Use for alerts that repeat on a schedule.
        cooldown_seconds: Cooldown window in seconds. Ignored without cooldown_key.
    """
    if cooldown_key and cooldown_seconds > 0:
        fingerprint = hashlib.md5(cooldown_key.encode()).hexdigest()
        if _is_cooled_down(fingerprint, cooldown_seconds):
            return "throttled"

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
        try:
            result = json.loads(resp.read())
        except json.JSONDecodeError as e:
            raise ValueError(f"Telegram API returned invalid JSON: {e}") from e

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
    try:
        result = json.loads(r.stdout)
    except json.JSONDecodeError as e:
        raise ValueError(f"Telegram API returned invalid JSON: {e}") from e

    _LOCK.touch()

    if not result.get("ok"):
        raise ValueError(f"Telegram error: {result.get('description', 'unknown')}")
    return "photo sent"
