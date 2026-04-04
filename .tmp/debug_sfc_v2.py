import time

from playwright.sync_api import sync_playwright


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://apps.sfc.hk/edistributionWeb/gateway/EN/circular/", timeout=60000)
        time.sleep(10)
        content = page.content()
        with open("/home/terry/germline/.tmp/sfc_body.html", "w") as f:
            f.write(content)
        browser.close()


if __name__ == "__main__":
    run()
