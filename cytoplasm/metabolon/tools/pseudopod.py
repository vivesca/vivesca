"""navigator — endocytosis of web content with structured output and fallbacks.

Wraps agent-browser CLI with the reliability fallback chain baked in.

Tools:
  endocytosis_extract    — ingest page content (text + title + url)
  endocytosis_screenshot — capture a membrane snapshot
  endocytosis_check_auth — verify surface markers for a domain
"""

import os
import subprocess
import time

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import EffectorResult, Secretion


class EndocytosisResult(Secretion):
    """Ingested page content — endocytosed from the web."""

    url: str
    title: str = ""
    text: str = ""
    success: bool = False
    method: str = ""
    error: str = ""


class EndocytosisCapture(EffectorResult):
    """Membrane snapshot — captured page image."""

    url: str
    path: str


class SurfaceMarkerResult(Secretion):
    """Surface marker check — browser authentication state."""

    domain: str
    authenticated: bool = False
    url: str = ""
    message: str = ""
    fix: str = ""


def _ab(args: list[str], timeout: int = 15) -> str:
    """Run an agent-browser command. Returns stdout or empty on failure."""
    path = os.popen("which agent-browser").read().strip() or "agent-browser"
    try:
        result = subprocess.run(
            [path, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except (
        subprocess.TimeoutExpired,
        FileNotFoundError,
        subprocess.CalledProcessError,
    ):
        return ""


def _ab_check(args: list[str], timeout: int = 15) -> tuple[bool, str]:
    """Run agent-browser command, return (success, output)."""
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


def _navigate(url: str, timeout: int = 15) -> bool:
    """Navigate to URL with fallback chain."""
    ok, _ = _ab_check(["open", url], timeout=timeout)
    if ok:
        return True
    escaped = url.replace("'", "\\'")
    ok, _ = _ab_check(["eval", f"window.location.href = '{escaped}'"], timeout=10)
    if ok:
        time.sleep(3)
        return True
    return False


def _get_text() -> str:
    """Extract page text with fallback chain."""
    ok, text = _ab_check(["get", "text"], timeout=10)
    if ok and text:
        return text
    ok, text = _ab_check(["eval", "document.body.innerText"], timeout=10)
    if ok and text:
        return text
    return ""


@tool(
    name="endocytosis_extract",
    description="Extract page content from URL. Structured output with automated fallbacks.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def endocytosis_extract(url: str, wait_ms: int = 3000) -> EndocytosisResult:
    """Endocytose page content from a URL."""
    result = EndocytosisResult(url=url)

    if not _navigate(url, timeout=15):
        result.error = "Failed to navigate — both open and eval fallback failed"
        return result

    _ab(["wait", str(wait_ms)], timeout=max(wait_ms // 1000 + 5, 10))

    ok, title = _ab_check(["get", "title"], timeout=5)
    if ok:
        result.title = title

    ok, actual_url = _ab_check(["get", "url"], timeout=5)
    if ok:
        result.url = actual_url

    text = _get_text()
    if text:
        result.text = text
        result.success = True
        result.method = "get_text" if _ab_check(["get", "text"], timeout=5)[0] else "eval"
    else:
        result.error = "Failed to extract text — both get text and eval fallback failed"

    return result


@tool(
    name="endocytosis_screenshot",
    description="Screenshot a URL. Wakes display, handles nav fallbacks.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def endocytosis_screenshot(
    url: str, output_path: str = "", wait_ms: int = 3000
) -> EndocytosisCapture:
    """Capture a membrane snapshot of a page."""
    if not output_path:
        output_path = os.path.expanduser("~/tmp/screenshot.png")

    subprocess.run(
        ["caffeinate", "-u", "-t", "2"],
        capture_output=True,
        timeout=5,
    )

    if not _navigate(url, timeout=15):
        return EndocytosisCapture(
            success=False, message="Failed to navigate", url=url, path=output_path
        )

    _ab(["wait", str(wait_ms)], timeout=max(wait_ms // 1000 + 5, 10))

    ok, out = _ab_check(["screenshot", output_path], timeout=10)
    if ok:
        return EndocytosisCapture(
            success=True, message="Screenshot captured", url=url, path=output_path
        )
    return EndocytosisCapture(
        success=False, message=f"Screenshot failed: {out}", url=url, path=output_path
    )


@tool(
    name="endocytosis_check_auth",
    description="Check browser auth for a domain. Detects login redirects.",
    annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False),
)
def endocytosis_check_auth(domain: str) -> SurfaceMarkerResult:
    """Check surface markers — browser authentication for a domain."""
    url = f"https://{domain}" if not domain.startswith("http") else domain
    result = SurfaceMarkerResult(domain=domain)

    if not _navigate(url, timeout=15):
        result.message = "Failed to navigate — browser may not be running"
        result.fix = "Run: agent-browser open about:blank"
        return result

    _ab(["wait", "3000"], timeout=10)

    ok, actual_url = _ab_check(["get", "url"], timeout=5)
    result.url = actual_url if ok else url

    ok, title = _ab_check(["get", "title"], timeout=5)
    title_lower = title.lower() if ok else ""

    login_signals = ["login", "sign in", "log in", "authenticate", "sso", "oauth"]
    is_login_page = any(s in title_lower for s in login_signals)

    url_lower = (actual_url or "").lower()
    login_url_signals = ["/login", "/signin", "/auth", "/sso", "/oauth", "/checkpoint"]
    is_login_url = any(s in url_lower for s in login_url_signals)

    if is_login_page or is_login_url:
        result.authenticated = False
        result.message = f"Not authenticated — redirected to login ({title})"
        result.fix = (
            f"Option 1: agent-browser --headed open {url}  (log in manually)\n"
            f"Option 2: porta inject --browser chrome --domain {domain}"
        )
    else:
        result.authenticated = True
        result.message = f"Authenticated — landed on: {title}"

    return result
