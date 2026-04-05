# Site-Specific Browser Automation Notes

Per-site login flows, gotchas, and credentials. Referenced from [SKILL.md](SKILL.md).

## LinkedIn

- **Login from soma:** Blocked. Playwright login fails on soma (headless, headed, keyboard, JS — all fail).
- **Login from Mac:** Works. `ssh mac "agent-browser --headed open ..."` + `keyboard type` + `click`. See Tier 2.5.
- **Daily use:** `ssh mac "agent-browser ..."` — all commands work via SSH. Session persists in Mac's profile.
- **Fallback:** Tier 3 AppleScript if agent-browser session expires and re-login fails.
- **Cookie bridge fails:** `li_at` is browser-fingerprint bound. kleis/porta injection doesn't work even on same IP.
- **Profile editing:** Navigate to edit URLs (e.g. `/in/terrylihm/edit/about/`). Use native value setter + events.
- **`wait --load networkidle` times out.** Use `agent-browser wait 4000` instead.

## RVD E-Billing (gov.hk) — Tier 1, fully automated

Gov.hk SSO uses simple form POST, no reCAPTCHA. See `memory/reference_rvd_ebill_login.md`.

```bash
# 1. Landing page
agent-browser eval "window.location.href = 'https://ebill1.rvd.gov.hk/app/ebill/?locale=zh_HK'"
sleep 5
# 2. Submit username (form button is type="button" — must use form.submit())
agent-browser eval "document.querySelector('input[name=myid]').value = 'terry39'; document.getElementById('login').submit()"
sleep 8
# 3. Password page — fill and submit
agent-browser fill @PASSWORD_REF "$(op item get m7hpa... --fields password --reveal)"
agent-browser eval "document.querySelector('form').submit()"
sleep 8
# 4. Handle "already logged in" — click 重新登入
# 5. Dashboard → download PDF via fetch (see PDF Download pattern in SKILL.md)
```

**Gotchas:** Direct URL `/app/ebill/login` returns E-033. Must go through landing page flow.

## PPS (ppshk.com) — Unautomatable

reCAPTCHA v3 + frameset + `window.open` popup = triple wall.
- reCAPTCHA v3 scores Playwright as bot regardless of cookies/mode
- Login page only accessible via `popUp()` from frameset menu frame
- `popUp()` uses `window.open` which Chrome blocks without user gesture
- Cross-frame JS from AppleScript returns `missing value` (cross-origin policy)
- Coordinate-based clicking (cliclick) is fragile across frame offsets

**Solution:** Call PPS 2311 9876, set up standing instruction for RVD merchant 26041, account 1574010139530. Autopay forever.

## Schwab / Financial Sites

- **Login:** Tier 3 only. Akamai blocks login iframe in Playwright.
- **Alternative:** Download documents manually or via mobile app.

## OCI (Oracle Cloud)

- **Login:** agent-browser headed mode works. TOTP required — use rapid OTP fill pattern.
- **Console:** Content in `#sandbox-maui-preact-container` iframe. `snapshot` sees into it but not nested frames.
- **Prefer OCI CLI** (`oci`) for programmatic work. Browser only for billing/PAYG.

**OCI Payment Flow (4-level iframe chain):**
1. `cloud.oracle.com` → main page
2. `#sandbox-maui-preact-container` → OCI console iframe (same-origin, snapshot works)
3. `shop.oracle.com` → payment service iframe (cross-origin, snapshot/DOM blocked)
4. `secureacceptance.cybersource.com` → card form (cross-origin but Playwright `frame.fill()` works)

**shop.oracle.com button IDs:** `#ps-cc-button` (Credit Card), `#ps-pay-button` (Save), `#ps-close-button` (Close). Access via Playwright `frame.query_selector()` after `connect_over_cdp()` — agent-browser `snapshot`/`click` cannot reach cross-origin nested iframes.

**Combined form after clicking Credit Card — keyboard Tab order:**
Card Number → Exp Month (select) → Exp Year (select) → CVV → Address Line 1 → Address Line 2 → City → State → Country (select) → Postal Code → Phone

**CyberSource card fields (accessible via frame DOM):**
`card_number` (tel), `card_cvn` (tel), `card_type` (radio: 001=Visa 002=MC 003=Amex), `card_expiry_month`/`card_expiry_year` (selects), `commit` (submit)

**Card verification:** Mox virtual MC accepted after ~4h delay. CyberSource "Thank you" fires immediately but Oracle backend takes hours to register the card. Don't retry — poll billing page.

**CyberSource bot detection:** Headless Chrome blocked via `Runtime.enable` CDP signal. Must use Xvfb + `headless=False` + `--disable-blink-features=AutomationControlled` + `navigator.webdriver` override.

**1Password duplicate field gotcha:** `op --fields "expiry date"` returns first (empty) match. Use `--format json` and take last non-empty value per label.

## Workday Career Portals

- Block Playwright actions entirely. Use automation for login + CV upload, manual for dropdowns.

## Cloudflare-Protected Sites

Escalation: `peruro` (Firecrawl proxies) → kleis + stealth Playwright → nodriver headed login.

## Google OAuth

Google blocks Playwright login (popup-based, not redirect). Escalation:
1. `porta_inject domain=accounts.google.com` — works for redirect-based OAuth, fails for popup-based (GIS SDK)
2. **Email OTP fallback** — if the site offers email login, use email OTP + Gmail API instead (fully headless)
3. Headed mode — `AGENT_BROWSER_HEADED=1` for user to click Google login manually
4. `--auto-connect` — connect to user's real Chrome (needs `--remote-debugging-port=9222`)

## BuyAndShip (buyandship.today) — Tier 1 via email OTP

- **Google OAuth:** Blocked headless (popup-based). Use email OTP instead.
- **Login flow:** Enter email → click "Log in with a OTP" → grab code from Gmail (`gog gmail search "from:buyandship newer_than:5m" --account terry.li.hm@gmail.com`) → fill 6 digit boxes → logged in.
- **Warehouse addresses:** `/account/v2020/warehouse/` (NOT `/member/warehouses` which 404s). Click country flag to expand.
- **UK warehouse:** Terry BSWNZZTR, Unit 13 Ashford Business Centre, 166 Feltham Road, Ashford, TW15 1YQ, UK. Tel: 07468 466826.
- **Account email:** terry.li.hm@gmail.com

## Orea Shop (shop.orea.uk) — Tier 1 headless + Tier 2 for payment

- **Shopify-based.** Cart API works for adding items. Variant discovery via `/products/SLUG.js`.
- **V4 Wide variant ID:** 54607238070657
- **Card fields:** In Shopify iframes — agent-browser 0.24.1 handles via `snapshot -i` + `fill @ref`.
- **3D Secure:** Needs headed mode. `AGENT_BROWSER_HEADED=1` for the "Pay now" step.
- **Checkout session expiry:** ~10 min. If "problem with checkout" error, clear cart and restart.
- **Shipping to BuyAndShip UK:** GBP 1.99 (UK Standard). Direct to HK: HK$190 (FedEx). BuyAndShip saves ~HK$143.
