---
name: tessera-google
description: Provision Google OAuth Desktop credentials headlessly — create GCP client, capture secret, run consent flow, store tokens. Extension of tessera for Google APIs.
triggers: ["google oauth", "gmail setup", "google api credentials", "gcp oauth client"]
epistemics: [browser-automation, credential-management]
---

# Tessera-Google: Google OAuth Credential Provisioning

Automate the full Google OAuth Desktop credential lifecycle from a headless server.

## Prerequisites
- Mac with Chrome signed into Google (cookie bridge at port 7743)
- Playwright on Mac (`uv run --with playwright`)
- 1Password CLI (`op`) on soma
- GCP project with target API enabled

## Workflow

### Step 1: Enable API on GCP
```bash
ssh mac "gcloud services enable gmail.googleapis.com --project=PROJECT_ID"
```

### Step 2: Create Desktop OAuth Client (capture secret)
Use Playwright on Mac with cookie injection + network interception.

```python
# Cookie injection from bridge (port 7743, NOT 9742)
cookies = json.loads(urllib.request.urlopen("http://localhost:7743/cookies?domain=google.com").read())

# Playwright flow
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    for name, value in cookies.items():
        try:
            ctx.add_cookies([{"name": name, "value": value, "domain": ".google.com", 
                            "path": "/", "secure": True, "sameSite": "Lax"}])
        except: pass
    
    page = ctx.new_page()
    captured = []
    page.on("response", lambda r: capture_if_secret(r, captured))
    
    page.goto(f"https://console.cloud.google.com/auth/clients/create?project={PROJECT}",
              wait_until="domcontentloaded", timeout=30000)
    time.sleep(20)  # SPA load time
    
    # Dismiss overlays
    page.evaluate("document.querySelectorAll('.cfc-page-overlay').forEach(e => e.remove())")
    try: page.locator("button", has_text="OK, got it").click(timeout=3000)
    except: pass
    
    # Fill form
    page.locator("[role=combobox]").last.click(); time.sleep(2)
    page.locator("[role=option]", has_text="Desktop app").click(); time.sleep(2)
    page.locator("input").first.fill(CLIENT_NAME); time.sleep(1)
    
    # Create via JS (bypasses overlay)
    page.evaluate("document.querySelectorAll('button').forEach(b => { if (b.innerText.trim() === 'Create') b.click(); })")
    time.sleep(8)
    
    # Secret is in captured responses — search for GOCSPX pattern
    import re
    for c in captured:
        secrets = re.findall(r'GOCSPX-[A-Za-z0-9_-]+', c)
        if secrets: CLIENT_SECRET = secrets[0]
```

**Key API**: `clientauthconfig.clients6.google.com/v1/clients` — returns full secret in JSON response.

### Step 3: Run OAuth Consent Flow
On Mac, use `InstalledAppFlow` with localhost redirect:
```python
flow = InstalledAppFlow.from_client_secrets_file(credentials_json, scopes)
creds = flow.run_local_server(port=8099, open_browser=True, timeout_seconds=180)
```

Then automate Chrome consent screens via AppleScript:
1. Account chooser: `document.querySelectorAll("[data-identifier]")[0].click()`
2. Unverified warning: Click "Advanced" → "Go to ... (unsafe)"
3. Consent grant: Click "Continue"

### Step 4: Store Credentials
```bash
op item create --vault Agents --category "API Credential" \
  --title "Gmail OAuth - Vivesca" \
  "client_id=..." "client_secret=..." "refresh_token=..."
```

Add env vars to `~/.zshenv`:
```
export GMAIL_CLIENT_ID="..."
export GMAIL_CLIENT_SECRET="..."
export GMAIL_REFRESH_TOKEN="..."
```

## Anti-patterns (what fails)
| Approach | Failure mode |
|----------|-------------|
| JS monkey-patching fetch/XHR/Blob | GCP uses compiled framework internals |
| AppleScript click on Download JSON | Chrome blocks programmatic downloads |
| gcloud CLI for OAuth clients | No command exists (IAP deprecated) |
| PKCE without client_secret | Google rejects for Desktop apps |
| gcloud's client_id for Gmail | Blocked — consent screen restriction |
| Chrome --remote-debugging-port | Requires non-default profile dir |
| Killing Chrome | Loses session cookies (memory-only) |

## CLI Tool
`tessera-google` effector: `~/germline/effectors/tessera-google`
```
tessera-google --project PROJECT --scope SCOPE --name CLIENT_NAME
```
Automates steps 1-4. Requires Mac Chrome authenticated + cookie bridge running.
