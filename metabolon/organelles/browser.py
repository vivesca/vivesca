"""browser — headless page fetcher built on Playwright.

Public API:
  fetch(url, **options) -> dict   — fetch a URL and return structured result
  fetch_text(url, **options) -> str — fetch a URL and return clean text only

Options:
  cookies:   Path to JSON cookie file (Playwright storageState format)
  selector:  CSS selector to extract a subtree instead of full page
  screenshot: Path to write a PNG screenshot
  pdf:       Path to write a PDF (requires headed chromium)
  wait:      Milliseconds to wait after load before extracting (default 0)
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Optional

from playwright.sync_api import sync_playwright


def fetch(
    url: str,
    *,
    cookies: Optional[str] = None,
    selector: Optional[str] = None,
    screenshot: Optional[str] = None,
    pdf: Optional[str] = None,
    wait: int = 0,
) -> dict[str, Any]:
    """Fetch *url* with a headless Chromium browser.

    Returns a dict with keys: url, title, text, status, cookies, screenshot, pdf.
    """
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context_opts: dict[str, Any] = {}
        if cookies:
            cookie_path = Path(cookies)
            if not cookie_path.exists():
                raise FileNotFoundError(f"Cookie file not found: {cookie_path}")
            context_opts["storage_state"] = str(cookie_path)

        context = browser.new_context(**context_opts)
        page = context.new_page()

        response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        status = response.status if response else None

        if wait > 0:
            page.wait_for_timeout(wait)

        title = page.title()

        # Extract text
        if selector:
            element = page.query_selector(selector)
            if element:
                text = element.inner_text()
            else:
                text = ""
        else:
            text = page.inner_text("body")

        # Screenshot
        screenshot_path = None
        if screenshot:
            page.screenshot(path=screenshot, full_page=True)
            screenshot_path = screenshot

        # PDF
        pdf_path = None
        if pdf:
            page.pdf(path=pdf)
            pdf_path = pdf

        context.close()
        browser.close()

    return {
        "url": url,
        "title": title,
        "text": text,
        "status": status,
        "screenshot": screenshot_path,
        "pdf": pdf_path,
    }


def fetch_text(url: str, **kwargs: Any) -> str:
    """Fetch *url* and return only the clean text content."""
    return fetch(url, **kwargs)["text"]
