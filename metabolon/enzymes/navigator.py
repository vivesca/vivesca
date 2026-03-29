"""navigator — browser automation via agent-browser.

Actions: extract|screenshot|check_auth
"""

from __future__ import annotations

import os
import subprocess
import time
from typing import Any

from fastmcp.tools import tool
from mcp.types import ToolAnnotations

from metabolon.morphology import Secretion


class NavigatorResult(Secretion):
    success: bool
    data: dict[str, Any]
    error: str | None = None


_ACTIONS = (
    "extract — extract page content. Requires: url. Optional: wait_ms. "
    "screenshot — capture screenshot. Requires: url. Optional: output_path, wait_ms. "
    "check_auth — check if authenticated. Requires: domain."
)


def _run_ab(args: list[str]) -> tuple[bool, str]:
    path = os.popen("which agent-browser").read().strip() or "agent-browser"
    try:
        res = subprocess.run([path] + args, capture_output=True, text=True, check=True)
        return True, res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, (e.stderr.strip() or e.stdout.strip())


@tool(
    name="navigator",
    description=f"Browser automation. Actions: {_ACTIONS}",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def navigator(
    action: str,
    url: str = "",
    domain: str = "",
    output_path: str = "",
    wait_ms: int = 3000,
) -> NavigatorResult:
    """Browser automation tool."""
    action = action.lower().strip()

    if action == "extract":
        if not url:
            return NavigatorResult(success=False, data={}, error="extract requires: url")
        
        ok, out = _run_ab(["open", url])
        if not ok:
            return NavigatorResult(success=False, data={"url": url}, error=f"Navigation failed: {out}")
        
        if wait_ms > 0:
            time.sleep(wait_ms / 1000.0)

        ok_title, title = _run_ab(["get", "title"])
        ok_text, text = _run_ab(["get", "text"])
        ok_url, current_url = _run_ab(["get", "url"])
        
        return NavigatorResult(
            success=True,
            data={
                "url": current_url if ok_url else url,
                "title": title if ok_title else "",
                "text": text if ok_text else "",
            }
        )

    elif action == "screenshot":
        if not url:
            return NavigatorResult(success=False, data={}, error="screenshot requires: url")
        
        # caffeinate to wake display if sleeping
        subprocess.run(["caffeinate", "-u", "-t", "2"], capture_output=True)

        ok, out = _run_ab(["open", url])
        if not ok:
            return NavigatorResult(success=False, data={"url": url}, error=f"Navigation failed: {out}")
        
        if wait_ms > 0:
            time.sleep(wait_ms / 1000.0)

        if not output_path:
            import tempfile
            output_path = os.path.join(tempfile.gettempdir(), f"screenshot_{int(time.time())}.png")

        ok, out = _run_ab(["screenshot", output_path])
        if not ok:
            return NavigatorResult(success=False, data={"url": url}, error=f"Screenshot failed: {out}")
        
        return NavigatorResult(
            success=True,
            data={"url": url, "output_path": output_path}
        )

    elif action == "check_auth":
        if not domain:
            return NavigatorResult(success=False, data={}, error="check_auth requires: domain")
        
        target_url = f"https://{domain}" if not domain.startswith("http") else domain
        ok, out = _run_ab(["open", target_url])
        if not ok:
            return NavigatorResult(success=False, data={"domain": domain}, error=f"Navigation failed: {out}")
        
        time.sleep(3) # Wait for potential redirects
        
        ok_url, current_url = _run_ab(["get", "url"])
        if not ok_url:
            current_url = ""

        # Basic heuristic for login redirect
        is_authenticated = True
        curr_lower = current_url.lower()
        if "login" in curr_lower or "signin" in curr_lower or "auth" in curr_lower:
            is_authenticated = False
            
        data = {
            "domain": domain,
            "current_url": current_url,
            "is_authenticated": is_authenticated
        }
        if not is_authenticated:
            data["guidance"] = f"Not authenticated. Use 'porta inject {domain}' to inject cookies."
            
        return NavigatorResult(
            success=True,
            data=data
        )

    else:
        return NavigatorResult(
            success=False,
            data={},
            error=f"Unknown action '{action}'. Valid: extract, screenshot, check_auth"
        )
