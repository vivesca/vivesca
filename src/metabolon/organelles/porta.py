"""porta — cookie bridge from Chrome to agent-browser Playwright context.

Extracts Chrome cookies via cookie-bridge HTTP server on Mac (LaunchAgent
with Keychain access), then injects into agent-browser (local or via SSH).

Architecture:
  soma → HTTP GET mac:7743/cookies?domain=X → cookie-bridge (Mac LaunchAgent)
       → pycookiecheat (macOS Keychain) → cookies JSON
  soma → SSH mac agent-browser cookies set → Playwright context

Constraints:
  - Cookie injection only. Does not handle localStorage or JWT auth.
  - cookie-bridge must be running on Mac (LaunchAgent: com.terryli.cookie-bridge).
  - Falls back to local pycookiecheat if cookie-bridge unreachable.
"""

import subprocess


def _ab(args: list[str], timeout: int = 15) -> tuple[bool, str]:
    """Run agent-browser command, locally or via SSH to Mac."""
    import platform

    if platform.system() == "Darwin":
        cmd = ["agent-browser", *args]
    else:
        # agent-browser with Chrome lives on Mac — relay via SSH
        cmd = ["ssh", "mac", "agent-browser", *args]

    try:
        result = subprocess.run(
            cmd,
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
    except subprocess.CalledProcessError as exc:
        return False, exc.stderr.strip()


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

    # Cookie bridge: HTTP server on Mac with Keychain access (LaunchAgent)
    # Falls back to local pycookiecheat if running on macOS directly
    import json
    import urllib.request

    cookie_bridge_url = f"http://mac:7743/cookies?domain={domain}"
    try:
        with urllib.request.urlopen(cookie_bridge_url, timeout=10) as resp:
            cookies: dict[str, str] = json.loads(resp.read().decode("utf-8"))
        if "error" in cookies:
            return {
                "success": False,
                "message": f"Cookie bridge error: {cookies['error']}",
                "count": 0,
            }
    except Exception:
        # Fallback: direct pycookiecheat (if running on macOS)
        try:
            from pycookiecheat import chrome_cookies  # type: ignore

            cookies = chrome_cookies(url)
        except Exception as exc:
            return {
                "success": False,
                "message": f"Cookie extraction failed (bridge unreachable, local fallback failed): {exc}",
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

    # Set each cookie via agent-browser cookies set (supports HttpOnly)
    injected = 0
    failures: list[str] = []
    for name, value in cookies.items():
        safe_value = str(value).replace("\n", "").replace("\r", "")
        safe_name = str(name).replace("\n", "").replace("\r", "")
        # Use agent-browser cookies set with --httpOnly --secure --url
        # This uses Playwright's context.add_cookies() under the hood,
        # which can set HttpOnly cookies (document.cookie cannot).
        cmd = [
            "cookies",
            "set",
            safe_name,
            safe_value,
            "--url",
            url,
            "--domain",
            f".{domain}",
            "--path",
            "/",
            "--httpOnly",
            "--secure",
        ]
        ok, _ = _ab(cmd, timeout=5)
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
