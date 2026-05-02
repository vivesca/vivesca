"""browser_stealth — make Playwright browser contexts undetectable.

Provides six public functions:
  - patch_navigator:  override navigator.webdriver on a page
  - set_realistic_headers: rotate User-Agent from a curated Chrome list
  - human_delay: random pause between actions (simulates human cadence)
  - stealth_context: create a Playwright context with all patches applied
  - generate_fingerprint: create a browserforge fingerprint (cacheable per session)
  - apply_fingerprint: inject a generated fingerprint into a Playwright context
"""

from __future__ import annotations

import asyncio
import json
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from patchright.async_api import BrowserContext, Page

from browserforge.fingerprints import FingerprintGenerator as _FingerprintGenerator

# 20 real Chrome User-Agent strings (Chrome 120-131 across Win/Mac/Linux).
CHROME_USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

# JavaScript to override navigator.webdriver so it returns undefined.
_WEBDRIVER_PATCH_JS = """
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
});
"""

# Additional stealth: mask automation indicators in Chrome runtime.
_CHROME_RUNTIME_PATCH_JS = """
window.chrome = {
    runtime: {},
    loadTimes: function() {},
    csi: function() {},
    app: {},
};
"""

# Mask plugins and mimeTypes to look like a real Chrome install.
_PLUGINS_PATCH_JS = """
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});
Object.defineProperty(navigator, 'mimeTypes', {
    get: () => [1, 2],
});
"""

# Permissions query override so navigator.permissions.query returns prompt.
_PERMISSIONS_PATCH_JS = """
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : originalQuery(parameters)
);
"""


async def patch_navigator(page: Page) -> None:
    """Override navigator.webdriver on *page* so it returns undefined.

    Must be called after page.goto() or via add_init_script for new pages.
    Applies webdriver, chrome.runtime, plugins, and permissions patches.
    """
    await page.add_init_script(_WEBDRIVER_PATCH_JS)
    await page.add_init_script(_CHROME_RUNTIME_PATCH_JS)
    await page.add_init_script(_PLUGINS_PATCH_JS)
    await page.add_init_script(_PERMISSIONS_PATCH_JS)


async def set_realistic_headers(context: BrowserContext) -> str:
    """Set a randomly chosen Chrome User-Agent on *context*.

    Returns the selected UA string so callers can log or verify it.

    Note: This is async because `BrowserContext.set_extra_http_headers`
    is a coroutine in the async Playwright API (and `stealth_context`
    expects an async context). Calling the sync version raised a silent
    RuntimeWarning ("coroutine was never awaited") and the UA was never
    applied — defeating one of the four stealth patches.
    """
    ua = random.choice(CHROME_USER_AGENTS)
    await context.set_extra_http_headers({"User-Agent": ua})
    return ua


async def human_delay(
    min_seconds: float = 0.5,
    max_seconds: float = 2.0,
) -> float:
    """Sleep for a random duration to simulate human interaction cadence.

    Returns the actual delay chosen (in seconds).
    """
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)
    return delay


async def stealth_context(context: BrowserContext) -> BrowserContext:
    """Apply all stealth patches to a Playwright *context*.

    Patches applied:
      1. Random realistic User-Agent header rotation
      2. init-script patches applied to every new page in this context
         (webdriver override, chrome runtime, plugins, permissions)
      3. Hides Playwright-specific indicators (e.g. webdriver flag)

    Returns the same context for chaining.
    """
    # Rotate User-Agent.
    await set_realistic_headers(context)

    # Apply init scripts so every new page in the context gets patched.
    await context.add_init_script(_WEBDRIVER_PATCH_JS)
    await context.add_init_script(_CHROME_RUNTIME_PATCH_JS)
    await context.add_init_script(_PLUGINS_PATCH_JS)
    await context.add_init_script(_PERMISSIONS_PATCH_JS)

    return context


# ── browserforge fingerprint support ──────────────────────────────────────
# Source: Scrapling (https://github.com/D4Vinci/Scrapling) assay 2026-05-02.
# Stolen primitive only — framework rejected. browserforge is the upstream lib
# Scrapling's StealthyFetcher uses underneath. See
# marks/finding_scrapling_no_uplift_2026_05_02.md for re-evaluation triggers.

_generator = _FingerprintGenerator()


def generate_fingerprint() -> dict:
    """Generate a realistic browser fingerprint via browserforge.

    Returns a dict with keys: navigator, screen, videoCard, pluginsData,
    fonts, headers, and the raw JS injection string under ``js``.
    Thread-safe — each call produces a fresh fingerprint from the generator.
    """
    fp = _generator.generate()
    raw: dict = json.loads(fp.dumps())
    raw["js"] = fp.dumps()
    return raw


def _fingerprint_injection_js(fingerprint: dict) -> str:
    """Build a JS init-script that overrides browser APIs with fingerprint data.

    Overrides: navigator properties, screen dimensions, plugin/mimeType lists,
    WebGL vendor/renderer, codec support strings.
    """
    nav = fingerprint.get("navigator", {})
    scr = fingerprint.get("screen", {})
    vc = fingerprint.get("videoCard", {})
    plugins_data = fingerprint.get("pluginsData", {})
    fonts = fingerprint.get("fonts", [])

    plugins_js = "[]"
    mime_types_js = "[]"
    if plugins_data:
        plugin_list = plugins_data.get("plugins", [])
        if plugin_list:
            plugins_js = json.dumps(plugin_list)
        mt_list = plugins_data.get("mimeTypes", [])
        if mt_list:
            mime_types_js = json.dumps(mt_list)

    fonts_js = json.dumps(fonts)

    nav_props = {}
    for key in (
        "userAgent",
        "appVersion",
        "platform",
        "language",
        "languages",
        "hardwareConcurrency",
        "deviceMemory",
        "maxTouchPoints",
        "vendor",
        "product",
        "productSub",
        "appCodeName",
        "appName",
        "doNotTrack",
    ):
        if key in nav:
            nav_props[key] = nav[key]

    nav_js = json.dumps(nav_props)
    scr_js = json.dumps(scr)

    vc_overrides = ""
    if vc:
        vc_overrides = f"""
    Object.defineProperty(HTMLCanvasElement.prototype, 'getContext', {{
        value: function(type, attributes) {{
            const ctx = origGetContext.apply(this, arguments);
            if (ctx && type === 'webgl2' || type === 'webgl' || type === 'experimental-webgl') {{
                const getParam = ctx.getParameter;
                const ext = ctx.getExtension('WEBGL_debug_renderer_info');
                ctx.getParameter = function(param) {{
                    if (ext && param === ext.UNMASKED_VENDOR_WEBGL) return {json.dumps(vc.get("vendor", ""))};
                    if (ext && param === ext.UNMASKED_RENDERER_WEBGL) return {json.dumps(vc.get("renderer", ""))};
                    return getParam.call(ctx, param);
                }};
            }}
            return ctx;
        }},
        writable: true,
        configurable: true,
    }});
    """

    return f"""
(function() {{
    const origGetContext = HTMLCanvasElement.prototype.getContext;
    const navProps = {nav_js};
    const scrProps = {scr_js};
    const plugins = {plugins_js};
    const mimeTypes = {mime_types_js};
    const fonts = {fonts_js};

    for (const [key, value] of Object.entries(navProps)) {{
        try {{
            Object.defineProperty(navigator, key, {{
                get: () => typeof value === 'object' ? JSON.parse(JSON.stringify(value)) : value,
            }});
        }} catch (e) {{}}
    }}

    if (scrProps) {{
        for (const [key, value] of Object.entries(scrProps)) {{
            try {{
                if (key in screen) {{
                    Object.defineProperty(screen, key, {{ get: () => value }});
                }}
            }} catch (e) {{}}
        }}
    }}

    Object.defineProperty(navigator, 'plugins', {{
        get: () => plugins,
    }});
    Object.defineProperty(navigator, 'mimeTypes', {{
        get: () => mimeTypes,
    }});

    Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined,
    }});

    {vc_overrides}

    if (fonts.length > 0) {{
        Object.defineProperty(document, 'fonts', {{
            get: () => ({{ check: () => true }}),
        }});
    }}
}})();
"""


async def apply_fingerprint(
    context: BrowserContext,
    fingerprint: dict,
) -> BrowserContext:
    """Apply a generated browserforge fingerprint to a Playwright context.

    Sets User-Agent and extra headers, then installs an init-script that
    overrides navigator, screen, plugins, WebGL, and fonts for every page
    created in this context.

    Returns the same context for chaining.
    """
    headers = fingerprint.get("headers", {})
    if headers:
        filtered = {k: v for k, v in headers.items() if not k.lower().startswith("sec-fetch")}
        await context.set_extra_http_headers(filtered)

    js = _fingerprint_injection_js(fingerprint)
    await context.add_init_script(js)

    return context
