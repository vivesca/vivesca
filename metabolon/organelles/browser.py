"""browser — headless page fetcher using Playwright.

Single public async function:

  fetch(url, *, cookies, selector, screenshot, pdf, wait) -> dict

Returns dict with: text, title, url, status, cookies_loaded,
                    screenshot_saved, pdf_saved.
"""
from __future__ import annotations

import json
from pathlib import Path

from playwright.async_api import async_playwright


async def fetch(
    url: str,
    *,
    cookies: str | None = None,
    selector: str | None = None,
    screenshot: str | None = None,
    pdf: str | None = None,
    wait: int = 0,
) -> dict:
    """Fetch *url* with headless Chromium and extract page content.

    Args:
        url: URL to navigate to.
        cookies: Path to a JSON cookie file (array of cookie objects).
        selector: CSS selector — when given, return inner_text of first match.
        screenshot: File path to save a PNG screenshot.
        pdf: File path to save a PDF rendering.
        wait: Milliseconds to pause after domcontentloaded.

    Returns:
        dict with keys: title, url, text, status,
        cookies_loaded, screenshot_saved, pdf_saved.
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()

        # Load cookies if provided
        cookies_loaded = 0
        if cookies:
            cookie_path = Path(cookies)
            if cookie_path.exists():
                raw = json.loads(cookie_path.read_text())
                if isinstance(raw, list):
                    await context.add_cookies(raw)
                    cookies_loaded = len(raw)

        page = await context.new_page()
        response = await page.goto(url, wait_until="domcontentloaded")
        status = response.status if response else 0

        if wait > 0:
            await page.wait_for_timeout(wait)

        # Extract text
        if selector:
            element = await page.query_selector(selector)
            text = await element.inner_text() if element else ""
        else:
            text = await page.inner_text("body")

        title = await page.title()
        final_url = page.url

        # Screenshot
        screenshot_saved = False
        if screenshot:
            await page.screenshot(path=screenshot)
            screenshot_saved = True

        # PDF
        pdf_saved = False
        if pdf:
            await page.pdf(path=pdf)
            pdf_saved = True

        await browser.close()

    return {
        "title": title,
        "url": final_url,
        "text": text,
        "status": status,
        "cookies_loaded": cookies_loaded,
        "screenshot_saved": screenshot_saved,
        "pdf_saved": pdf_saved,
    }
