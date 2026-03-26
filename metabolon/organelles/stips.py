"""stips — OpenRouter budget sensor (stips = stipend/allowance)."""

import json
import os
import subprocess
import sys
import urllib.request
from urllib.error import HTTPError, URLError

OPENROUTER_KEYS_PAGE = "https://openrouter.ai/keys"
OPENROUTER_TOPUP_PAGE = "https://openrouter.ai/credits"
KEYCHAIN_SERVICE = "openrouter-api-key"
KEYCHAIN_ACCOUNT = "openrouter"
LOW_CREDITS_THRESHOLD = 5.0


def _base_url() -> str:
    return os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai")


def _read_api_key() -> str:
    """Read API key from env var or macOS Keychain.

    Returns:
        API key string.

    Raises:
        RuntimeError: If key is not found.
    """
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key

    result = subprocess.run(
        ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(
            "Error: API key not found. Run: stips key save <your-key>"
        )
    return result.stdout.strip()


def _request_json(url: str, api_key: str, timeout: int = 15) -> dict:
    """Make authenticated GET request and return parsed JSON.

    Args:
        url: Full URL to fetch.
        api_key: OpenRouter API key.
        timeout: HTTP timeout in seconds.

    Returns:
        Parsed JSON response dict.

    Raises:
        RuntimeError: On HTTP or network error.
    """
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "stips/1.0.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        raise RuntimeError(f"Error: HTTP {exc.code} {exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"Error: {exc.reason}") from exc


def fetch_credits(api_key: str) -> dict:
    """Fetch credit balance from OpenRouter.

    Args:
        api_key: OpenRouter API key.

    Returns:
        dict with keys: remaining, used, total (all floats in USD).
    """
    url = f"{_base_url()}/api/v1/credits"
    data = _request_json(url, api_key)["data"]
    total = float(data["total_credits"])
    used = float(data["total_usage"])
    return {"remaining": total - used, "used": used, "total": total}


def fetch_usage(api_key: str) -> dict:
    """Fetch usage breakdown from OpenRouter.

    Args:
        api_key: OpenRouter API key.

    Returns:
        dict with keys: daily, weekly, monthly (all floats in USD).
    """
    url = f"{_base_url()}/api/v1/auth/key"
    data = _request_json(url, api_key)["data"]
    return {
        "daily": float(data["usage_daily"]),
        "weekly": float(data["usage_weekly"]),
        "monthly": float(data["usage_monthly"]),
    }


def key_save(key: str) -> None:
    """Save API key to macOS Keychain.

    Args:
        key: OpenRouter API key string.

    Raises:
        RuntimeError: If security command fails.
    """
    result = subprocess.run(
        [
            "security",
            "add-generic-password",
            "-s", KEYCHAIN_SERVICE,
            "-a", KEYCHAIN_ACCOUNT,
            "-w", key,
            "-U",
        ],
        capture_output=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError("Error: failed to save API key to keychain")
    print("API key saved to keychain")


def key_open() -> None:
    """Open OpenRouter keys page in the browser (macOS only).

    Raises:
        RuntimeError: If open command fails.
    """
    print(f"Opening {OPENROUTER_KEYS_PAGE}")
    result = subprocess.run(["open", OPENROUTER_KEYS_PAGE], timeout=10)
    if result.returncode != 0:
        raise RuntimeError("Error: failed to open URL")


def sense() -> dict:
    """Top-level sense call: fetch credits and return structured status.

    Primary entry point for invoke_organelle-style callers.
    Never raises; returns {"error": "..."} on failure.

    Returns:
        dict with keys: remaining, used, total, low (bool), or {"error": "..."}.
    """
    try:
        api_key = _read_api_key()
        credits = fetch_credits(api_key)
        credits["low"] = credits["remaining"] < LOW_CREDITS_THRESHOLD
        return credits
    except Exception as exc:
        return {"error": str(exc)}


def _cli() -> None:
    """CLI entry point matching the Rust stips interface."""
    args = sys.argv[1:]

    def _print_err(msg: str) -> None:
        print(msg, file=sys.stderr)

    def _die(msg: str) -> None:
        _print_err(msg)
        sys.exit(1)

    # No subcommand → show credits (default)
    if not args or args[0] in ("-h", "--help"):
        if not args:
            _run_credits(is_tty=sys.stdout.isatty(), as_json=False)
            return
        print(
            "Usage: stips [credits|usage|key] [--json]\n"
            "       stips key open\n"
            "       stips key save <key>\n"
            "\nSubcommands:\n"
            "  credits   Show credit balance (default)\n"
            "  usage     Show daily/weekly/monthly usage\n"
            "  key open  Open OpenRouter keys page\n"
            "  key save  Save API key to macOS Keychain"
        )
        return

    if args[0] in ("-V", "--version"):
        print("stips 1.0.0")
        return

    sub = args[0]

    if sub == "credits":
        as_json = "--json" in args
        _run_credits(is_tty=sys.stdout.isatty(), as_json=as_json)

    elif sub == "usage":
        as_json = "--json" in args
        _run_usage(as_json=as_json)

    elif sub == "key":
        if len(args) < 2:
            _die("Usage: stips key open | stips key save <key>")
        key_sub = args[1]
        if key_sub == "open":
            try:
                key_open()
            except RuntimeError as exc:
                _die(str(exc))
        elif key_sub == "save":
            if len(args) < 3:
                _die("Usage: stips key save <key>")
            try:
                key_save(args[2])
            except RuntimeError as exc:
                _die(str(exc))
        else:
            _die(f"Unknown key subcommand: {key_sub}")

    else:
        _die(f"Unknown subcommand: {sub}. Try: stips --help")


def _run_credits(is_tty: bool, as_json: bool) -> None:
    try:
        api_key = _read_api_key()
        credits = fetch_credits(api_key)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    remaining = credits["remaining"]
    used = credits["used"]
    total = credits["total"]

    if as_json:
        print(json.dumps(credits, indent=2))
    else:
        print(f"${remaining:.2f} remaining  (${used:.2f} used of ${total:.2f})")
        if remaining < LOW_CREDITS_THRESHOLD:
            warn = (
                f"Warning: Low - top up at {OPENROUTER_TOPUP_PAGE}"
            )
            print(warn, file=sys.stderr)


def _run_usage(as_json: bool) -> None:
    try:
        api_key = _read_api_key()
        usage = fetch_usage(api_key)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    if as_json:
        print(json.dumps(usage, indent=2))
    else:
        print(f"Daily:   ${usage['daily']:.2f}")
        print(f"Weekly:  ${usage['weekly']:.2f}")
        print(f"Monthly: ${usage['monthly']:.2f}")


if __name__ == "__main__":
    _cli()
