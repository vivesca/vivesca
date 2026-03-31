"""browser — high-level Playwright browsing with stealth baked in.

Wraps common browsing operations (navigate, extract, screenshot) in a
context that is already patched for undetectability via
:mod:`metabolon.organelles.browser_stealth`.

Biology: the cell's exploratory pseudopod — reaching out into the
environment while wearing camouflage to avoid triggering defensive
responses from the substrate.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from playwright.sync_api import sync_playwright

from metabolon.organelles.browser_stealth import (
    human_delay,
    patch_navigator,
    set_realistic_headers,
    stealth_context,
)

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright


class StealthBrowser:
    """Manages a Playwright browser lifecycle with stealth patches.

    Usage::

        with StealthBrowser() as sb:
            page = sb.goto("https://example.com")
            html = page.content()
    """

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    # -- context manager ---------------------------------------------------

    def __enter__(self) -> StealthBrowser:
        self.launch()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # -- lifecycle ---------------------------------------------------------

    def launch(self) -> None:
        """Start Playwright, launch browser, create stealth context."""
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self._headless)
        self._context = stealth_context(
            self._browser,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
        )

    def close(self) -> None:
        """Shut down browser and Playwright."""
        if self._context is not None:
            self._context.close()
        if self._browser is not None:
            self._browser.close()
        if self._pw is not None:
            self._pw.stop()
        self._context = self._browser = self._pw = None

    # -- browsing operations -----------------------------------------------

    def goto(self, url: str, *, wait_until: str = "domcontentloaded") -> Page:
        """Navigate to *url* with a human-like delay first.

        Returns the Page object for further interaction.
        """
        assert self._context is not None, "Browser not launched"
        human_delay()
        page = self._context.new_page()
        page.goto(url, wait_until=wait_until)
        return page

    @property
    def context(self) -> BrowserContext:
        """The active stealth context (read-only)."""
        assert self._context is not None, "Browser not launched"
        return self._context

    @property
    def browser(self) -> Browser:
        """The active Browser instance (read-only)."""
        assert self._browser is not None, "Browser not launched"
        return self._browser
