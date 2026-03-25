# Extracting Download URLs from Gated Forms (HubSpot etc.)

When a website gates a PDF behind a form (common with HubSpot), the actual download URL is often triggered client-side after form submission. Playwright's `page.goto` will fail with "Download is starting" since it can't handle the navigation-to-download redirect.

## Pattern

1. Fill and submit the form via `agent-browser fill` + `agent-browser click`
2. After "Thank you" confirmation appears, extract the download URL from browser performance entries:

```js
performance.getEntriesByType('resource')
  .filter(e => e.name.includes('pdf') || e.name.includes('download'))
  .map(e => e.name)
```

3. Download via `curl` (not agent-browser — Playwright chokes on direct file downloads):

```bash
curl -L -o output.pdf "<extracted-url>"
```

## Why This Works

HubSpot forms trigger a client-side redirect to the file download after form submission. The browser fetches the resource, which gets logged in the Performance API even though it manifests as a download rather than a page navigation.

## Discovered

Feb 2026 — downloading Evident AI Index Payments report from evidentinsights.com (HubSpot-powered form gate).
