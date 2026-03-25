# Web Fetch Tool Matrix — Cloudflare & JS-Rendered Sites

## Benchmark Results

### Test 1: OpenRice (Cloudflare Bot Management)
Tested 2026-03-08 against Dan Ryan's Cityplaza listing.

| Tool | Result | Notes |
|------|--------|-------|
| `WebFetch` | ❌ Blocked | Cloudflare WAF challenge page |
| `defuddle` | ❌ Blocked | "Please wait..." — single line |
| `noesis search` | ✅ Facts | Indirect via indexed sources — address, hours, phone. ~$0.006 |
| `exauro search` | ⚠️ Partial | URLs found, but snippets mixed cross-branch data |
| `peruro` | ✅ Full page | Name, address (EN+ZH), phone, hours, reviews, corkage fees. ~1 credit |
| `agent-browser --profile` | ❌ Blocked | Persistent profile doesn't help |
| `summarize` | ❌ Blocked | Chrome UA, still blocked |

### Test 2: danryans.com (Wix, JS-rendered, no Cloudflare)
Tested 2026-03-08 against /our-locations page.

| Tool | Result | Notes |
|------|--------|-------|
| `WebFetch` | ❌ No content | Got Wix JS bundle, not rendered content |
| `defuddle` | ⚠️ Partial | Boilerplate only, no location data |
| `noesis search` | ✅ Facts | Indirect from indexed snapshots. ~$0.006 |
| `exauro search` | ✅ Snippets | "three locations in Hong Kong: Festival Walk..." |
| `peruro` | ✅ Full page | Full addresses, phones, hours rendered. ~1 credit |

### Test 3: perplexity.ai/hub (Framer + Cloudflare Bot Management)
Tested 2026-03-04.

| Tool | Result | Notes |
|------|--------|-------|
| `defuddle` | ❌ 403 | Plain HTTP fetch |
| `summarize` | ❌ 403 | Chrome UA, still blocked |
| `nodriver` (stealth_web) | ❌ CF challenge stuck | "Performing security verification" — never clears |
| `agent-browser --profile` | ❌ CF challenge stuck | Persistent profile doesn't help |
| `openrss.org` | ❌ Timeout | Cloudflare blocks openrss too |
| `peruro` | ✅ Works | Residential proxies + legit fingerprints. ~1 credit |

---

## Decision Matrix

| Goal | Tool |
|------|------|
| Need facts from a page | `noesis search` — synthesises from indexed sources, no direct fetch needed |
| Need actual page content | `peruro` — only tool that reliably handles Cloudflare + JS-rendered |
| Find a URL (not content) | `exauro search` — good for discovery, snippets inconsistent |
| Static page, no protection | `defuddle` → `WebFetch` |

**Avoid `WebFetch`/`defuddle` for any Cloudflare or JS-heavy target.** They fetch the HTML shell, not rendered content.

---

## Cost

- `peruro` (Firecrawl): 500 free credits, 1 credit/page. Key in keychain as `peruro`.
- `noesis search`: ~$0.006/query. Good for facts; doesn't consume Firecrawl credits.
- `exauro search`: ~$0.001/query. Best for URL discovery.

---

## Confirmed working sites (peruro)

- **OpenRice** (2026-03-08) — full page including corkage fees, cake cutting info, opening hours
- **danryans.com** (2026-03-08) — full location data from Wix JS-rendered page
- **perplexity.ai/hub** (2026-03-04) — bypasses Framer + Cloudflare Bot Management

---

## Notes

- Cloudflare Bot Management ("Performing security verification" with Ray ID) = nothing headless works except Firecrawl.
- Cloudflare legacy rate-limiting (plain 403) is different — defuddle/summarize sometimes work there.
- JS-rendered sites (Wix, React SPAs) also need `peruro` — `WebFetch`/`defuddle` get the JS bundle, not content.
