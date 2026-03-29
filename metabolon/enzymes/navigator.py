"""navigator — browser automation with structured output and fallbacks.

Single action-dispatch tool wrapping agent-browser CLI.
Actions: extract, screenshot, check_auth.
"""

from __future__ import annotations

import json
import os
import subprocess
import time

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Secretion


class NavigatorResult(Secretion):
    output: str


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Action dispatch
# ---------------------------------------------------------------------------

@tool(
    name="navigator",
    description="Browser automation. Actions: extract|screenshot|check_auth",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def navigator(
    action: str,
    url: str = "",
    wait_ms: int = 3000,
    output_path: str = "",
    domain: str = "",
) -> NavigatorResult | EffectorResult:
    """Browser automation with fallbacks.

    Args:
        action: One of extract, screenshot, check_auth.
        url: Target URL (for extract / screenshot).
        wait_ms: Milliseconds to wait after page load (default 3000).
        output_path: File path for screenshots (default ~/tmp/screenshot.png).
        domain: Domain to check for auth (e.g. 'linkedin.com').
    """
    # -- extract ----------------------------------------------------------
    if action == "extract":
        result = {"url": url, "title": "", "text": "", "success": False, "method": ""}

        # Navigate
        if not _navigate(url, timeout=15):
            result["error"] = "Failed to navigate — both open and eval fallback failed"
            return NavigatorResult(output=json.dumps(result))

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

        return NavigatorResult(output=json.dumps(result))

    # -- screenshot -------------------------------------------------------
    if action == "screenshot":
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
            return NavigatorResult(output=json.dumps(result))

        _ab(["wait", str(wait_ms)], timeout=max(wait_ms // 1000 + 5, 10))

        # Capture
        ok, out = _ab_check(["screenshot", output_path], timeout=10)
        if ok:
            result["success"] = True
        else:
            result["error"] = f"Screenshot failed: {out}"

        return NavigatorResult(output=json.dumps(result))

    # -- check_auth -------------------------------------------------------
    if action == "check_auth":
        target_url = f"https://{domain}" if not domain.startswith("http") else domain
        result = {"domain": domain, "authenticated": False, "url": "", "message": ""}

        if not _navigate(target_url, timeout=15):
            result["message"] = "Failed to navigate — browser may not be running"
            result["fix"] = "Run: agent-browser open about:blank"
            return NavigatorResult(output=json.dumps(result))

        _ab(["wait", "3000"], timeout=10)

        # Check current URL — login redirects are the signal
        ok, actual_url = _ab_check(["get", "url"], timeout=5)
        result["url"] = actual_url if ok else target_url

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
                f"Option 1: agent-browser --headed open {target_url}  (log in manually)\n"
                f"Option 2: porta inject --browser chrome --domain {domain}"
            )
        else:
            result["authenticated"] = True
            result["message"] = f"Authenticated — landed on: {title}"

        return NavigatorResult(output=json.dumps(result))

    # -- unknown action ---------------------------------------------------
    return EffectorResult(success=False, error=f"Unknown action: {action!r}. Use extract|screenshot|check_auth.")
