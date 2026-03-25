# Google Photos CLI (`gphotos`) — Technical Notes

## Overview
CLI tool accessing Google Photos via Chrome CDP, bypassing the dead Photos Library API (readonly scope killed Mar 2025).

**Location:** `~/code/gphotos/` | **Install:** `uv tool install -e ~/code/gphotos`

## Key Technical Details

### SPA Data Structure
- Google Photos embeds photo data in `AF_initDataCallback` script blocks
- **Individual photos** (with dimensions): `ds:0` block, pattern `"fife_url",width,height`
- **Categories/suggestions** (no dimensions): `ds:1` block, pattern `[null,null,timestamp,0,count,"Category Name",...]`
- Main page (`photos.google.com`) serves BOTH — ds:0 has the photo grid, ds:1 has categories

### Page Load Timing (critical)
- **t=12s**: Bare fife URLs appear in HTML (no dimensions yet)
- **t=15s**: Structured data arrives (`"url",width,height` in ds:0)
- **Cold Chrome start**: Can take 20+ seconds — must poll, not fixed sleep
- Implementation: 15s initial wait, then poll every 3s for `/pw/AP1Gcz` in HTML, +3s after detection for structured data

### Authentication / Download
- `Network.getCookies` with explicit URL list: `photos.google.com`, `photos.fife.usercontent.google.com`, `lh3.googleusercontent.com`, `accounts.google.com`, `www.google.com`
- **Must use `http.cookiejar.CookieJar`** with proper domain matching (leading dot). Raw Cookie header → 403.
- **CookieJar isn't picklable** — session cache stores cookies as JSON dicts, rebuilds jar on read
- Download suffixes: `=w800` (thumbnail), `=s0` (original), `=d` (original + EXIF)

### Search
- Navigate to `photos.google.com/search/<query>`
- Same extraction pipeline — structured data if available, bare URL fallback
- Search results may not always include dimensions (depends on page rendering path)

## Gotchas
- CDP Chrome port binding is flaky after restart — always verify with `curl`, kill -9 and relaunch if needed
- `_create_tab(url)` navigates immediately — don't navigate twice (was causing unnecessary SPA re-render)
- Session cache TTL: 30 min (photos + cookies in `/tmp/gphotos_session.json`)
