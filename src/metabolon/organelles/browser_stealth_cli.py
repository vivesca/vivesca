"""stealth-browser CLI — fetch pages with stealth fingerprint injection.

Supports three fingerprint modes:
  - cookies (default): Chrome cookies + playwright-extra stack (current behaviour).
  - generated: browserforge-generated fingerprint injected before navigation.
  - both: cookies + generated fingerprint stacked.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from patchright.async_api import async_playwright

from metabolon.organelles.browser_stealth import (
    apply_fingerprint,
    generate_fingerprint,
    stealth_context,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stealth-browser",
        description="Fetch a URL with stealth fingerprint injection.",
    )
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument(
        "--fingerprint-mode",
        choices=["generated", "cookies", "both"],
        default="cookies",
        help="Fingerprint strategy (default: cookies).",
    )
    parser.add_argument(
        "--headless",
        choices=["true", "false"],
        default="true",
        help="Run headless (default: true).",
    )
    parser.add_argument("--cookies", default=None, help="Path to JSON cookie file.")
    parser.add_argument("--screenshot", default=None, help="Path to save PNG screenshot.")
    parser.add_argument("--pdf", default=None, help="Path to save PDF.")
    parser.add_argument("--wait", type=int, default=0, help="Wait ms after load.")
    parser.add_argument("--json", dest="json_output", action="store_true", help="Output JSON.")
    parser.add_argument("--selector", default=None, help="CSS selector to extract.")
    return parser


def format_output(result: dict, *, as_json: bool = False) -> str:
    if as_json:
        return json.dumps(result, indent=2, ensure_ascii=False)
    return result.get("text", "")


async def _async_fetch(
    url: str,
    *,
    fingerprint_mode: str = "cookies",
    headless: bool = True,
    cookies: str | None = None,
    selector: str | None = None,
    screenshot: str | None = None,
    pdf: str | None = None,
    wait: int = 0,
) -> dict:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)

        use_generated = fingerprint_mode in ("generated", "both")
        use_cookies = fingerprint_mode in ("cookies", "both")

        context_kwargs: dict = {}
        if use_generated:
            fp = generate_fingerprint()
            scr = fp.get("screen", {})
            w = scr.get("width") or scr.get("innerWidth") or 1920
            h = scr.get("height") or scr.get("height") or 1080
            context_kwargs["viewport"] = {"width": int(w), "height": int(h)}
            context_kwargs["user_agent"] = fp.get("navigator", {}).get("userAgent", "")

        context = await browser.new_context(**context_kwargs)

        if use_generated:
            fp = generate_fingerprint()
            await apply_fingerprint(context, fp)

        if use_cookies:
            await stealth_context(context)

        cookies_loaded = 0
        if cookies and fingerprint_mode in ("cookies", "both"):
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

        if selector:
            element = await page.query_selector(selector)
            text = await element.inner_text() if element else ""
        else:
            text = await page.inner_text("body")

        title = await page.title()
        final_url = page.url

        screenshot_saved = False
        if screenshot:
            await page.screenshot(path=screenshot)
            screenshot_saved = True

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
        "fingerprint_mode": fingerprint_mode,
        "headless": headless,
        "cookies_loaded": cookies_loaded,
        "screenshot_saved": screenshot_saved,
        "pdf_saved": pdf_saved,
    }


def _do_fetch(args: argparse.Namespace) -> dict:
    return asyncio.run(
        _async_fetch(
            args.url,
            fingerprint_mode=args.fingerprint_mode,
            headless=args.headless == "true",
            cookies=args.cookies,
            selector=args.selector,
            screenshot=args.screenshot,
            pdf=args.pdf,
            wait=args.wait,
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if not argv:
        parser.print_help(sys.stderr)
        return 1
    args = parser.parse_args(argv)

    try:
        result = _do_fetch(args)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except TimeoutError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    output = format_output(result, as_json=args.json_output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
