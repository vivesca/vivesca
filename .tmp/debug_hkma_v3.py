from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.hkma.gov.hk/eng/regulatory-resources/regulatory-guides/circulars/", timeout=60000)
        # Wait for the table to be populated
        time.sleep(15)
        
        # Check if there's a table
        rows = page.query_selector_all("table tbody tr")
        print(f"Found {len(rows)} table rows")
        for i, row in enumerate(rows[:5]):
            print(f"Row {i}: {row.inner_text().strip()[:100]}")
            
        # Check if there's a div list
        divs = page.query_selector_all(".rg-list .rg-item")
        print(f"Found {len(divs)} div items")
        for i, div in enumerate(divs[:5]):
            print(f"Div {i}: {div.inner_text().strip()[:100]}")

        browser.close()

if __name__ == "__main__":
    run()
