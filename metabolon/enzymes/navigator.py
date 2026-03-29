"""navigator — browser automation with structured output and fallbacks.

Wraps agent-browser CLI with the reliability fallback chain baked in.
Agents get structured JSON instead of raw text. Auth checks via porta.

Tools:
  navigator_extract   — extract page content (text + title + url)
  navigator_screenshot — capture a page screenshot
  navigator_check_auth — verify browser auth for a domain
"""

import json
import os
import subprocess
import time


from metabolon.organelles.effector import run_cli  # noqa: E402

from fastmcp.tools import tool  # noqa: E402
from mcp.types import ToolAnnotations  # noqa: E402

AB = "agent-browser"


def _ab(args: list[str], timeout: int = 15) -> str:
    """Run an agent-browser command. Returns stdout or empty on failure."""
    path = os.popen("which agent-browser").read().strip() or "agent-browser"
    try:
        result = subprocess.run(
            [path] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        return ""


def _ab_check(args: list[str], timeout: int = 15) -> tuple[bool, str]:
    """Run agent-browser command, return (success, output)."""
    path = os.popen("which agent-browser").read().strip() or "agent-browser"
    try:
        result = subprocess.run(
            [path] + args,
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


def _navigate(url: str, timeout: int = 15) -> bool:
    """Navigate to URL with fallback chain.

    Primary: agent-browser open <url>
    Fallback: eval window.location.href = '<url>'
    """
    ok, _ = _ab_check(["open", url], timeout=timeout)
    if ok:
        return True

    # Fallback: JS navigation
    escaped = url.replace("'", "\\'")
    ok, _ = _ab_check(["eval", f"window.location.href = '{escaped}'"], timeout=10)
    if ok:
        time.sleep(3)  # Wait for navigation
        return True

    return False


def _get_text() -> str:
    """Extract page text with fallback chain.

    Primary: agent-browser get text
    Fallback: eval document.body.innerText
    """
    ok, text = _ab_check(["get", "text"], timeout=10)
    if ok and text:
        return text

    # Fallback: JS extraction
    ok, text = _ab_check(["eval", "document.body.innerText"], timeout=10)
    if ok and text:
        return text

    return ""


@tool(
    name="navigator_extract",
    description=(
        "Extract page content from a URL with automated fallbacks. "
        "Returns structured output: url, title, text, success. "
        "Handles navigation timeouts and text extraction failures automatically."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def navigator_extract(url: str, wait_ms: int = 3000) -> str:
    """Extract page content from a URL.

    Args:
        url: The URL to extract content from.
        wait_ms: Milliseconds to wait after page load (default 3000).
    """
    result = {"url": url, "title": "", "text": "", "success": False, "method": ""}

    # Navigate
    if not _navigate(url, timeout=15):
        result["error"] = "Failed to navigate — both open and eval fallback failed"
        return json.dumps(result)

    # Wait for page load
    _ab(["wait", str(wait_ms)], timeout=max(wait_ms // 1000 + 5, 10))

    # Get title
    ok, title = _ab_check(["get", "title"], timeout=5)
    if ok:
        result["title"] = title

    # Get URL (may have redirected)
    ok, actual_url = _ab_check(["get", "url"], timeout=5)
    if ok:
        result["url"] = actual_url

    # Extract text with fallback
    text = _get_text()
    if text:
        result["text"] = text
        result["success"] = True
        result["method"] = "get_text" if _ab_check(["get", "text"], timeout=5)[0] else "eval"
    else:
        result["error"] = "Failed to extract text — both get text and eval fallback failed"

    return json.dumps(result)


@tool(
    name="navigator_screenshot",
    description=(
        "Capture a screenshot of a URL. Returns the file path on success. "
        "Wakes display if sleeping (caffeinate). Handles navigation fallbacks."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def navigator_screenshot(url: str, output_path: str = "", wait_ms: int = 3000) -> str:
    """Capture a page screenshot.

    Args:
        url: The URL to screenshot.
        output_path: File path for the screenshot (default: ~/tmp/screenshot.png).
        wait_ms: Milliseconds to wait before capture (default 3000).
    """
    if not output_path:
        output_path = os.path.expanduser("~/tmp/screenshot.png")

    result = {"url": url, "path": output_path, "success": False}

    # Wake display if sleeping
    subprocess.run(
        ["caffeinate", "-u", "-t", "2"],
        capture_output=True, timeout=5,
    )

    # Navigate
    if not _navigate(url, timeout=15):
        result["error"] = "Failed to navigate"
        return json.dumps(result)

    _ab(["wait", str(wait_ms)], timeout=max(wait_ms // 1000 + 5, 10))

    # Capture
    ok, out = _ab_check(["screenshot", output_path], timeout=10)
    if ok:
        result["success"] = True
    else:
        result["error"] = f"Screenshot failed: {out}"

    return json.dumps(result)


@tool(
    name="navigator_check_auth",
    description=(
        "Check if the browser is authenticated for a domain. "
        "Opens the domain, checks if redirected to a login page. "
        "Returns auth status and guidance for porta inject if needed."
    ),
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def navigator_check_auth(domain: str) -> str:
    """Check browser authentication for a domain.

    Args:
        domain: Domain to check (e.g., 'linkedin.com', 'gmail.com').
    """
    url = f"https://{domain}" if not domain.startswith("http") else domain
    result = {"domain": domain, "authenticated": False, "url": "", "message": ""}

    if not _navigate(url, timeout=15):
        result["message"] = "Failed to navigate — browser may not be running"
        result["fix"] = "Run: agent-browser open about:blank"
        return json.dumps(result)

    _ab(["wait", "3000"], timeout=10)

    # Check current URL — login redirects are the signal
    ok, actual_url = _ab_check(["get", "url"], timeout=5)
    result["url"] = actual_url if ok else url

    # Check title for login indicators
    ok, title = _ab_check(["get", "title"], timeout=5)
    title_lower = title.lower() if ok else ""

    login_signals = ["login", "sign in", "log in", "authenticate", "sso", "oauth"]
    is_login_page = any(s in title_lower for s in login_signals)

    # Check URL for login path patterns
    url_lower = (actual_url or "").lower()
    login_url_signals = ["/login", "/signin", "/auth", "/sso", "/oauth", "/checkpoint"]
    is_login_url = any(s in url_lower for s in login_url_signals)

    if is_login_page or is_login_url:
        result["authenticated"] = False
        result["message"] = f"Not authenticated — redirected to login ({title})"
        result["fix"] = (
            f"Option 1: agent-browser --headed open {url}  (log in manually)\n"
            f"Option 2: porta inject --browser chrome --domain {domain}"
        )
    else:
        result["authenticated"] = True
        result["message"] = f"Authenticated — landed on: {title}"

    return json.dumps(result)
