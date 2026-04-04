---
name: tessera
description: Authenticate a website for headless agent access — routes to headed login, porta (cookie bridge), or nodriver (stealth Chrome) as appropriate.
user_invocable: true
platform: claude-code
trigger_phrases: ["browser login", "save login", "browser-login"]
arguments: "<url>"
---

# Browser Login

Save a website login to the persistent agent-browser profile so future headless access works without re-authenticating.

## Flow

1. Close any existing agent-browser session
2. Open the target URL in **headed** mode (visible Chromium window)
3. User logs in via Jump Desktop / screen sharing
4. Confirm login succeeded
5. Close headed browser — cookies persist for headless use
6. Verify headless access works
7. Update the authenticated sites table below

```bash
# Step 1: Close existing session
agent-browser close

# Step 2: Open login page in visible browser
agent-browser --headed open "<url>"

# Step 3: Tell user to log in via Jump Desktop
# Step 4: User confirms they're logged in

# Step 5: Close headed browser
agent-browser close

# Step 6: Verify headless access
agent-browser open "<url>"
agent-browser get url  # Should NOT redirect to login
agent-browser get title
```

## Post-Login

After successful login, update the authenticated sites table in `~/docs/solutions/agent-browser-paywalled-auth.md`:

```markdown
| Site | Profile Auth | Notes |
|------|-------------|-------|
| <site> | Yes (<month> <year>) | <notes> |
```

## Authenticated Sites (Quick Reference)

| Site | Login URL | Verified | Notes |
|------|-----------|----------|-------|
| LinkedIn | linkedin.com/login | Mar 2026 | **Headed-only.** Headless always blocked. Use 1Password auto-login (see linkedin-research skill). |
| Substack (Latent Space) | substack.com/sign-in | Feb 2026 | |
| Taobao/Tmall | login.taobao.com | Feb 2026 | |

## Cloudflare + localStorage Auth Sites — Use `nodriver` Instead

If a site uses Cloudflare bot protection AND stores auth in localStorage (not cookies):
- `porta list --domain site.com` finds no cookies → can't bridge
- Headed Playwright (agent-browser `--headed`) is blocked by Cloudflare

Use nodriver with a persistent profile:
```bash
cd /tmp && uv run --python 3.13 --with nodriver python3 -c "
import asyncio, nodriver as uc
from pathlib import Path
PROFILE = Path.home() / '.config/endocytosis/nodriver-profile'
PROFILE.mkdir(parents=True, exist_ok=True)
async def main():
    b = await uc.start(headless=False, user_data_dir=str(PROFILE))
    await b.get('https://site.com/login')
    print('Log in via Jump Desktop — waiting 120s...')
    await asyncio.sleep(120)
    b.stop()
asyncio.run(main())
"
```
Session persists in `~/.config/endocytosis/nodriver-profile/` for future headless use.
Confirmed working: **quaily.com** (Mar 2026). Full reference: `browser-automation-comparison.md`.

**Decision flow:**
1. `porta list --domain site.com` → cookies found → use `porta inject`
2. No cookies + Google OAuth blocked → headed Playwright + Google sign-in not viable → try nodriver
3. No cookies + Cloudflare → nodriver headed login above

## Google OAuth Sites — Use `porta` Skill

If a site only supports Google SSO (e.g. Vercel, Google-gated dashboards), the headed Playwright flow will be blocked by Google's bot detection. Use the `porta` skill — it handles the full cookie-bridge workflow.

## Notes

- User must have visual access to the Mac (Jump Desktop, VNC, or physical screen)
- `AGENT_BROWSER_PROFILE` env var points to `~/.agent-browser-profile/` — set in `~/.zshenv`
- Profile backup: `~/officina/browser-profile/`
