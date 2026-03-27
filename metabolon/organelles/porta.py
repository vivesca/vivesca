"""porta — cookie bridge from Chrome to agent-browser Playwright context.

Reads Chrome cookies for a domain via pycookiecheat (macOS Keychain
decryption), then injects them into agent-browser's active page.

Constraints:
  - Requires GUI session (Keychain access). Will not work from Blink/SSH.
  - Cookie injection only. Does not handle localStorage or JWT auth.
  - agent-browser must be running and reachable.
"""

from __future__ import annotations

import subprocess


def _ab(args: list[str], timeout: int = 15) -> tuple[bool, str]:
    """Run agent-browser command. Returns (success, output)."""
    # Late import to avoid circular dependency; pseudopod owns the _ab helpers
    # but porta is an organelle (not a tool), so we re-implement the slim variant.
    import os

    path = os.popen("which agent-browser").read().strip() or "agent-browser"
    try:
        result = subprocess.run(
            [path, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        ok = result.returncode == 0
        return ok, result.stdout.strip() if ok else result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except FileNotFoundError:
        return False, "agent-browser not found"
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()


def inject(domain: str) -> dict:
    """Extract Chrome cookies for domain and inject into agent-browser.

    Args:
        domain: Bare domain name, e.g. "bigmodel.cn". Protocol stripped
                automatically.

    Returns:
        dict with keys: success (bool), message (str), count (int).
    """
    # Normalise: strip protocol if user passed a full URL
    domain = domain.removeprefix("https://").removeprefix("http://").rstrip("/")
    url = f"https://{domain}"

    try:
        from pycookiecheat import chrome_cookies
    except ImportError:
        return {
            "success": False,
            "message": "pycookiecheat not installed — run: pip install pycookiecheat",
            "count": 0,
        }

    try:
        cookies: dict[str, str] = chrome_cookies(url)
    except Exception as exc:
        return {
            "success": False,
            "message": f"Chrome cookie extraction failed: {exc}",
            "count": 0,
        }

    if not cookies:
        return {
            "success": False,
            "message": f"No cookies found for {domain} — site may use localStorage/JWT",
            "count": 0,
        }

    # Navigate to the domain so cookies land on the correct origin
    ok, err = _ab(["open", url], timeout=15)
    if not ok:
        # Fall back to eval-based navigation
        escaped = url.replace("'", "\\'")
        ok, err = _ab(["eval", f"window.location.href = '{escaped}'"], timeout=10)
        if not ok:
            return {
                "success": False,
                "message": f"Failed to navigate agent-browser to {url}: {err}",
                "count": 0,
            }

    # Set each cookie via document.cookie
    injected = 0
    failures: list[str] = []
    for name, value in cookies.items():
        # Sanitise: remove newlines that would break cookie syntax
        safe_value = str(value).replace("\n", "").replace("\r", "")
        safe_name = str(name).replace("\n", "").replace("\r", "")
        js = f"document.cookie = '{safe_name}={safe_value}; path=/; domain=.{domain}';"
        ok, _ = _ab(["eval", js], timeout=5)
        if ok:
            injected += 1
        else:
            failures.append(safe_name)

    if injected == 0:
        return {
            "success": False,
            "message": f"Cookie injection failed for all {len(cookies)} cookies on {domain}",
            "count": 0,
        }

    msg = f"Injected {injected}/{len(cookies)} cookies for {domain}"
    if failures:
        msg += f" (failed: {', '.join(failures[:5])}{'...' if len(failures) > 5 else ''})"

    return {"success": True, "message": msg, "count": injected}
