from __future__ import annotations

"""browser_stealth — make Playwright browser contexts undetectable.

Provides four public functions:
  - patch_navigator:  override navigator.webdriver on a page
  - set_realistic_headers: rotate User-Agent from a curated Chrome list
  - human_delay: random pause between actions (simulates human cadence)
  - stealth_context: create a Playwright context with all patches applied
"""


import asyncio
import random
from typing import Any

from playwright.async_api import BrowserContext, Page

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


def set_realistic_headers(context: BrowserContext) -> str:
    """Set a randomly chosen Chrome User-Agent on *context*.

    Returns the selected UA string so callers can log or verify it.
    """
    ua = random.choice(CHROME_USER_AGENTS)
    context.set_extra_http_headers({"User-Agent": ua})
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
    set_realistic_headers(context)

    # Apply init scripts so every new page in the context gets patched.
    await context.add_init_script(_WEBDRIVER_PATCH_JS)
    await context.add_init_script(_CHROME_RUNTIME_PATCH_JS)
    await context.add_init_script(_PLUGINS_PATCH_JS)
    await context.add_init_script(_PERMISSIONS_PATCH_JS)

    return context
