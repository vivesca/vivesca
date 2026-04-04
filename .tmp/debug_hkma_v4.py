import time

from playwright.sync_api import sync_playwright


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(
            "https://www.hkma.gov.hk/eng/regulatory-resources/regulatory-guides/circulars/",
            timeout=60000,
        )
        time.sleep(15)

        row = page.query_selector("table tbody tr:nth-child(2)")
        if row:
            print(f"Row HTML: {row.inner_html()}")

        browser.close()


if __name__ == "__main__":
    run()
