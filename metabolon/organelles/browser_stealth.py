"""browser_stealth — make Playwright browser contexts undetectable.

Provides patches and utilities so automated browsing sessions look like
real Chrome traffic: navigator.webdriver override, realistic header
rotation, and human-like inter-action delays.

Biology: stealth camouflage for the cell's exploratory pseudopods,
allowing them to pass through membrane checkpoints undetected.
"""

from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext

# ---------------------------------------------------------------------------
# Realistic Chrome User-Agent pool (Chrome 120–131 on Windows/macOS/Linux)
# ---------------------------------------------------------------------------

CHROME_USER_AGENTS: list[str] = [
    # Windows 10/11 — Chrome 131
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Windows 10 — Chrome 130
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # macOS Sonoma — Chrome 131
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # macOS Ventura — Chrome 129
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    # Linux (Ubuntu) — Chrome 131
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Linux — Chrome 128
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    # Windows 11 — Chrome 127
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    # macOS — Chrome 126
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    # Windows 10 — Chrome 125
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    # Linux — Chrome 124
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Windows 10 — Chrome 123
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # macOS — Chrome 122
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Windows 11 — Chrome 121
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Linux — Chrome 120
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # macOS — Chrome 131 (ARM/M1+)
    "Mozilla/5.0 (Macintosh; ARM Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Windows 10 — Chrome 130 (WOW64)
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Linux — Chrome 129
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    # Windows 11 — Chrome 128
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    # macOS — Chrome 125
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    # Windows 10 — Chrome 124
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

# JS snippet that sets navigator.webdriver to false and deletes the getter.
_WEBDRIVER_PATCH_JS = """
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
    configurable: true,
});
delete Object.getPrototypeOf(navigator).__proto__.webdriver;
"""

# Extra stealth scripts: hide automation indicators.
_STEALTH_INIT_JS = """
// Override permissions query to avoid detection
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : originalQuery(parameters)
);

// Override plugins length to look like a real browser
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
    configurable: true,
});

// Override languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en'],
    configurable: true,
});
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def patch_navigator(context: BrowserContext) -> None:
    """Override navigator.webdriver on every new page in *context*.

    Injects a JavaScript init script that sets navigator.webdriver to
    ``undefined`` and removes the property descriptor, making the usual
    ``navigator.webdriver === true`` detection fail.
    """
    context.add_init_script(_WEBDRIVER_PATCH_JS)


def set_realistic_headers(context: BrowserContext) -> str:
    """Pick a random Chrome UA and apply it to *context*.

    Returns the chosen user-agent string so callers can log it.
    """
    ua = random.choice(CHROME_USER_AGENTS)
    context.set_extra_http_headers(
        {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24", "Google Chrome";v="131"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
        }
    )
    return ua


def human_delay(min_seconds: float = 0.5, max_seconds: float = 2.0) -> float:
    """Sleep for a random duration to mimic human interaction timing.

    Returns the actual delay in seconds so callers can log it.
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
    return delay


def stealth_context(browser: Browser, **context_kwargs: object) -> BrowserContext:
    """Create a new Playwright context with all stealth patches applied.

    Parameters
    ----------
    browser:
        A Playwright ``Browser`` instance.
    **context_kwargs:
        Forwarded to ``browser.new_context()`` (e.g. ``viewport``,
        ``proxy``, ``locale``).  If ``user_agent`` is not supplied one
        is chosen randomly from :data:`CHROME_USER_AGENTS`.

    Returns
    -------
    BrowserContext
        A context with navigator patch, realistic headers, and extra
        stealth init scripts already applied.
    """
    if "user_agent" not in context_kwargs:
        context_kwargs["user_agent"] = random.choice(CHROME_USER_AGENTS)

    context = browser.new_context(**context_kwargs)  # type: ignore[arg-type]

    # Apply patches
    patch_navigator(context)
    set_realistic_headers(context)
    context.add_init_script(_STEALTH_INIT_JS)

    return context
