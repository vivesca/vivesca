# Authy TOTP Export — All Automated Methods Dead (Feb 2026)

## The Problem

Migrating from Authy to 1Password (or any other authenticator) requires extracting TOTP seeds. Authy deliberately blocks export.

## What We Tried

1. **`authy-export` Go CLI** (skrashevich/authy-export) — registers as new device, pulls seeds. Code-reviewed: clean (all calls to `api.authy.com` only, no exfiltration, minimal deps). But Authy's API now returns "device does not meet minimum integrity requirements" — blocks all unofficial clients. Phone number lookup also failed despite correct number (Authy ID bypass via code patch didn't help — integrity check is downstream).

2. **Browser console method** (gboudreau gist) — requires Authy desktop app 2.2.3 with `--remote-debugging-port=5858`. Desktop app discontinued Aug 2024; only works if you already have it installed and logged in.

## What Still Works (Feb 2026)

- **iOS mitmproxy intercept** (`BrenoFariasdaSilva/Authy-iOS-MiTM`) — confirmed working Feb 2026
- **GDPR data request to Twilio** — ~1 month turnaround, returns encrypted CSV, decrypt with `@nick22985/authy-decryptor`
- **Manual re-enrollment** — disable 2FA on each service, re-enable with new authenticator scanning QR. Tedious but guaranteed.

## Recommendation

If <15 tokens: manual re-enrollment, do it gradually as you log into each service.
If 30+: mitmproxy worth the setup time.
Don't bother with automated tools — they're all blocked.
