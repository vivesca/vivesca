from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.hkma.gov.hk/eng/regulatory-resources/regulatory-guides/circulars/", timeout=60000)
        page.wait_for_load_state("networkidle")
        
        # Take a look at the body content
        content = page.content()
        with open("/home/terry/germline/.tmp/hkma_body.html", "w") as f:
            f.write(content)
        
        print("Body content saved.")
        browser.close()

if __name__ == "__main__":
    run()
