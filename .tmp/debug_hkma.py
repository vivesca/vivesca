from playwright.sync_api import sync_playwright
import json

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating...")
        page.goto("https://www.hkma.gov.hk/eng/regulatory-resources/regulatory-guides/circulars/", timeout=60000)
        print("Waiting for networkidle...")
        page.wait_for_load_state("networkidle", timeout=30000)
        print("Waiting for content...")
        # The page uses rg-listing.js, let's wait for a table or list
        page.wait_for_selector("table, .view-content, .rg-list", timeout=30000)
        
        # Extract rows
        rows = page.query_selector_all("table tbody tr, .rg-list .rg-item, .view-content .views-row")
        print(f"Found {len(rows)} rows")
        
        for i, row in enumerate(rows[:5]):
            print(f"Row {i}: {row.inner_text().strip()[:100]}...")
            links = row.query_selector_all("a")
            for j, link in enumerate(links):
                print(f"  Link {j}: {link.get_attribute('href')} - {link.inner_text().strip()}")
        
        browser.close()

if __name__ == "__main__":
    run()
