"""chemotaxis — browser automation via agent-browser.

Actions: navigate|extract|screenshot|click|fill|eval|resize|snapshot|check_auth
"""

import atexit
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from fastmcp.tools.function_tool import tool
from mcp.types import ToolAnnotations
from trogocytosis.browser import _resolve_domain_skills

from metabolon.morphology import Secretion

# Track auto-generated temp screenshots for cleanup on exit.
_pending_screenshots: list[str] = []


@atexit.register
def _cleanup_temp_screenshots() -> None:
    for p in _pending_screenshots:
        Path(p).unlink(missing_ok=True)


class ChemotaxisResult(Secretion):
    success: bool
    data: dict[str, Any]
    error: str | None = None


_ACTIONS = (
    "navigate — navigate to URL and extract page content. Requires: url. Optional: wait_ms. "
    "(extract is an alias for navigate.) "
    "screenshot — capture screenshot. Requires: url. Optional: output_path, wait_ms, "
    "width, height, scale, device. "
    "click — click an element. Requires: css_selector. "
    "fill — fill a form field. Requires: css_selector, value. "
    "eval — evaluate JavaScript in browser context. Requires: js. "
    "resize — set viewport dimensions. Requires: width, height. Optional: scale. "
    "snapshot — capture accessibility tree of the current page. "
    "check_auth — check if authenticated. Requires: domain."
)


def _run_ab(args: list[str]) -> tuple[bool, str]:
    path = (
        subprocess.run(["which", "agent-browser"], capture_output=True, text=True).stdout.strip()
        or "agent-browser"
    )
    try:
        res = subprocess.run(
            [path, *args], capture_output=True, text=True, check=True, timeout=300
        )
        return True, res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, (e.stderr.strip() or e.stdout.strip())


def _set_viewport(width: int, height: int, scale: float = 0) -> tuple[bool, str]:
    """Set the browser viewport via `agent-browser set viewport`."""
    args = ["set", "viewport", str(width), str(height)]
    if scale > 0:
        args.extend(["--scale", str(scale)])
    return _run_ab(args)


def _set_device(name: str) -> tuple[bool, str]:
    """Set the browser device preset via `agent-browser set device`."""
    return _run_ab(["set", "device", name])


def _handle_navigate(
    url: str,
    wait_ms: int,
) -> ChemotaxisResult:
    """Shared logic for navigate / extract actions."""
    if not url:
        return ChemotaxisResult(success=False, data={}, error="navigate requires: url")

    ok, out = _run_ab(["open", url])
    if not ok:
        return ChemotaxisResult(
            success=False, data={"url": url}, error=f"Navigation failed: {out}"
        )

    if wait_ms > 0:
        time.sleep(wait_ms / 1000.0)

    ok_title, title = _run_ab(["get", "title"])
    ok_text, text = _run_ab(["get", "text"])
    ok_url, current_url = _run_ab(["get", "url"])

    data: dict[str, Any] = {
        "url": current_url if ok_url else url,
        "title": title if ok_title else "",
        "text": text if ok_text else "",
    }

    # Side-channel: inject domain-specific skill/note paths
    domain_skills = _resolve_domain_skills(current_url if ok_url else url)
    if domain_skills:
        data["domain_skills"] = domain_skills

    return ChemotaxisResult(success=True, data=data)


@tool(
    name="chemotaxis",
    description=f"Browser automation. Actions: {_ACTIONS}",
    annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False),
)
def chemotaxis(
    action: str,
    url: str = "",
    domain: str = "",
    output_path: str = "",
    wait_ms: int = 3000,
    css_selector: str = "",
    value: str = "",
    js: str = "",
    width: int = 0,
    height: int = 0,
    scale: float = 0,
    device: str = "",
) -> ChemotaxisResult:
    """Browser automation tool.

    Parameters
    ----------
    action : str
        One of: navigate, extract, screenshot, click, fill, eval, resize,
        snapshot, check_auth.
    url : str
        Target URL (navigate, extract, screenshot).
    domain : str
        Domain to check for authentication (check_auth).
    output_path : str
        File path for screenshot output (screenshot).
    wait_ms : int
        Milliseconds to wait after page load (navigate, extract, screenshot).
    css_selector : str
        CSS selector for target element (click, fill).
    value : str
        Value to fill into the selected element (fill).
    js : str
        JavaScript code to evaluate in the browser (eval).
    width : int
        Viewport width in pixels (screenshot, resize).
    height : int
        Viewport height in pixels (screenshot, resize).
    scale : float
        Device pixel ratio / scale factor (screenshot, resize). 0 = use browser default.
    device : str
        Device preset name, e.g. "iPhone 14" (screenshot).
    """
    action = action.lower().strip()

    # ── navigate / extract (alias) ───────────────────────────────────────
    if action in ("navigate", "extract"):
        return _handle_navigate(url, wait_ms)

    # ── screenshot ───────────────────────────────────────────────────────
    elif action == "screenshot":
        if not url:
            return ChemotaxisResult(success=False, data={}, error="screenshot requires: url")

        # Apply optional viewport / device presets before capture.
        if device:
            ok_dev, err_dev = _set_device(device)
            if not ok_dev:
                return ChemotaxisResult(
                    success=False,
                    data={"url": url},
                    error=f"Set device failed: {err_dev}",
                )
        if width > 0 and height > 0:
            ok_vp, err_vp = _set_viewport(width, height, scale)
            if not ok_vp:
                return ChemotaxisResult(
                    success=False,
                    data={"url": url},
                    error=f"Set viewport failed: {err_vp}",
                )

        # caffeinate to wake display if sleeping (macOS only)
        if sys.platform == "darwin":
            subprocess.run(["caffeinate", "-u", "-t", "2"], capture_output=True, timeout=300)

        ok, out = _run_ab(["open", url])
        if not ok:
            return ChemotaxisResult(
                success=False, data={"url": url}, error=f"Navigation failed: {out}"
            )

        if wait_ms > 0:
            time.sleep(wait_ms / 1000.0)

        if not output_path:
            import tempfile

            output_path = os.path.join(tempfile.gettempdir(), f"screenshot_{int(time.time())}.png")
            _pending_screenshots.append(output_path)

        ok, out = _run_ab(["screenshot", output_path])
        if not ok:
            return ChemotaxisResult(
                success=False, data={"url": url}, error=f"Screenshot failed: {out}"
            )

        return ChemotaxisResult(
            success=True,
            data={"url": url, "output_path": output_path},
        )

    # ── click ────────────────────────────────────────────────────────────
    elif action == "click":
        if not css_selector:
            return ChemotaxisResult(success=False, data={}, error="click requires: css_selector")
        ok, out = _run_ab(["click", css_selector])
        if not ok:
            return ChemotaxisResult(
                success=False,
                data={"css_selector": css_selector},
                error=f"Click failed: {out}",
            )
        return ChemotaxisResult(
            success=True,
            data={"css_selector": css_selector, "result": out},
        )

    # ── fill ─────────────────────────────────────────────────────────────
    elif action == "fill":
        if not css_selector:
            return ChemotaxisResult(success=False, data={}, error="fill requires: css_selector")
        if not value:
            return ChemotaxisResult(success=False, data={}, error="fill requires: value")
        ok, out = _run_ab(["fill", css_selector, value])
        if not ok:
            return ChemotaxisResult(
                success=False,
                data={"css_selector": css_selector, "value": value},
                error=f"Fill failed: {out}",
            )
        return ChemotaxisResult(
            success=True,
            data={"css_selector": css_selector, "value": value, "result": out},
        )

    # ── eval ─────────────────────────────────────────────────────────────
    elif action == "eval":
        if not js:
            return ChemotaxisResult(success=False, data={}, error="eval requires: js")
        ok, out = _run_ab(["eval", js])
        if not ok:
            return ChemotaxisResult(
                success=False,
                data={"js": js},
                error=f"Eval failed: {out}",
            )
        return ChemotaxisResult(
            success=True,
            data={"js": js, "result": out},
        )

    # ── resize ───────────────────────────────────────────────────────────
    elif action == "resize":
        if width <= 0 or height <= 0:
            return ChemotaxisResult(
                success=False,
                data={},
                error="resize requires: width (>0) and height (>0)",
            )
        ok, out = _set_viewport(width, height, scale)
        if not ok:
            return ChemotaxisResult(
                success=False,
                data={"width": width, "height": height},
                error=f"Resize failed: {out}",
            )
        result_data: dict[str, Any] = {"width": width, "height": height}
        if scale > 0:
            result_data["scale"] = scale
        return ChemotaxisResult(success=True, data=result_data)

    # ── snapshot ─────────────────────────────────────────────────────────
    elif action == "snapshot":
        ok, out = _run_ab(["snapshot"])
        if not ok:
            return ChemotaxisResult(success=False, data={}, error=f"Snapshot failed: {out}")
        return ChemotaxisResult(success=True, data={"snapshot": out})

    # ── check_auth ───────────────────────────────────────────────────────
    elif action == "check_auth":
        if not domain:
            return ChemotaxisResult(success=False, data={}, error="check_auth requires: domain")

        target_url = f"https://{domain}" if not domain.startswith("http") else domain
        ok, out = _run_ab(["open", target_url])
        if not ok:
            return ChemotaxisResult(
                success=False, data={"domain": domain}, error=f"Navigation failed: {out}"
            )

        time.sleep(3)  # Wait for potential redirects

        ok_url, current_url = _run_ab(["get", "url"])
        if not ok_url:
            current_url = ""

        # Basic heuristic for login redirect
        is_authenticated = True
        curr_lower = current_url.lower()
        if "login" in curr_lower or "signin" in curr_lower or "auth" in curr_lower:
            is_authenticated = False

        data: dict[str, Any] = {
            "domain": domain,
            "current_url": current_url,
            "is_authenticated": is_authenticated,
        }
        if not is_authenticated:
            data["guidance"] = f"Not authenticated. Use 'porta inject {domain}' to inject cookies."

        return ChemotaxisResult(success=True, data=data)

    else:
        return ChemotaxisResult(
            success=False,
            data={},
            error=(
                f"Unknown action '{action}'. "
                "Valid: navigate, extract, screenshot, click, fill, eval, "
                "resize, snapshot, check_auth"
            ),
        )
