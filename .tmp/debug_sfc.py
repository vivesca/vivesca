import time

from playwright.sync_api import sync_playwright


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating to SFC...")
        page.goto("https://apps.sfc.hk/edistributionWeb/gateway/EN/circular/", timeout=60000)
        print("Waiting for load...")
        time.sleep(10)  # Wait for React

        # Take a look at the content
        rows = page.query_selector_all("a")
        print(f"Found {len(rows)} links")
        for i, row in enumerate(rows[:20]):
            print(f"Link {i}: {row.get_attribute('href')} - {row.inner_text().strip()[:100]}")

        browser.close()


if __name__ == "__main__":
    run()
