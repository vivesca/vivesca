"""glucosensor — OpenRouter energy currency sensor (glucosensor = glucose level sensor)."""

import configparser
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError

KEYCHAIN_SERVICE = "openrouter-api-key"
KEYCHAIN_ACCOUNT = "openrouter"

_CONF_PATH = Path(__file__).with_suffix(".conf")
_DEFAULTS = {"thresholds": {"low_credits_threshold": "5.0"}}


def _load_conf() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read_dict(_DEFAULTS)
    if _CONF_PATH.exists():
        cfg.read(_CONF_PATH)
    return cfg


LOW_CREDITS_THRESHOLD = _load_conf().getfloat("thresholds", "low_credits_threshold")


def _base_url() -> str:
    return os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai")


def _read_api_key() -> str:
    """Read API key from env var or macOS Keychain."""
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    result = subprocess.run(
        ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("API key not found. Run: stips key save <key>")
    return result.stdout.strip()


def _request_json(url: str, api_key: str, timeout: int = 15) -> dict:
    """Authenticated GET, returns parsed JSON."""
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "glucosensor/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc


def fetch_credits(api_key: str | None = None) -> dict:
    """Fetch credit balance. Returns {remaining, used, total}."""
    if api_key is None:
        api_key = _read_api_key()
    data = _request_json(f"{_base_url()}/api/v1/credits", api_key)["data"]
    total = float(data["total_credits"])
    used = float(data["total_usage"])
    return {"remaining": total - used, "used": used, "total": total}


def sense() -> dict:
    """Primary entry point. Never raises; returns {"error": ...} on failure."""
    try:
        credits = fetch_credits()
        credits["low"] = credits["remaining"] < LOW_CREDITS_THRESHOLD
        return credits
    except Exception as exc:
        return {"error": str(exc)}


def _cli() -> None:
    """CLI: `stips` (credits), `stips --json`, `stips key save <key>`."""
    args = sys.argv[1:]

    if not args:
        credits = sense()
        if "error" in credits:
            print(credits["error"], file=sys.stderr)
            sys.exit(1)
        print(f"${credits['remaining']:.2f} remaining  (${credits['used']:.2f} used of ${credits['total']:.2f})")
        if credits.get("low"):
            print("Warning: low credits", file=sys.stderr)
        return

    if args[0] == "--json":
        print(json.dumps(sense(), indent=2))
    elif args == ["key", "save"] or (len(args) == 3 and args[:2] == ["key", "save"]):
        if len(args) < 3:
            print("Usage: stips key save <key>", file=sys.stderr)
            sys.exit(1)
        subprocess.run([
            "security", "add-generic-password",
            "-s", KEYCHAIN_SERVICE, "-a", KEYCHAIN_ACCOUNT, "-w", args[2], "-U",
        ], capture_output=True, timeout=10, check=True)
        print("API key saved to keychain")
    else:
        print("Usage: stips [--json] | stips key save <key>", file=sys.stderr)
        sys.exit(1)
