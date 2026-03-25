# Kindle Cloud Reader Automation Gotchas

## The #1 Gotcha: Touch Events Only

**Kindle Cloud Reader is Ionic (mobile-first). It responds to `touchstart`/`touchend` events, NOT mouse `.click()` events.**

`element.click()` and `new MouseEvent('click')` are silently ignored. The click event fires (you can verify with `addEventListener`), but Kindle's own page-turn handler does not respond. This caused hours of debugging where pages appeared to "not advance" but the script counter incremented via fallback.

### Working pattern:
```javascript
var el = document.querySelector('#kr-chevron-right');
var r = el.getBoundingClientRect();
var cx = r.left + r.width/2, cy = r.top + r.height/2;
var t = new Touch({identifier: Date.now(), target: el, clientX: cx, clientY: cy, pageX: cx, pageY: cy});
el.dispatchEvent(new TouchEvent('touchstart', {bubbles: true, cancelable: true, touches: [t], targetTouches: [t], changedTouches: [t]}));
el.dispatchEvent(new TouchEvent('touchend', {bubbles: true, cancelable: true, touches: [], targetTouches: [], changedTouches: [t]}));
```

### Does NOT work:
- `element.click()`
- `new MouseEvent('click', {bubbles: true})`
- `agent-browser press ArrowLeft/ArrowRight` (no-op for page turns)
- `agent-browser click --ref e9` (Playwright blocks 150s waiting for navigation)

---

## Navigation: Getting to Page 1

**The left chevron (`#kr-chevron-left`) only navigates to previously-visited pages in the current session.** Opening a book via ASIN URL always resumes at the last-read position. The left chevron is visually enabled but functionally a no-op for unvisited pages — its `.click()` and touch events both silently fail for backward navigation to unvisited pages.

### Reliable approach: Table of Contents
```javascript
// 1. Open TOC
document.querySelector('[aria-label="Table of Contents"]').click();
// wait 2s
// 2. Click "Title Page" (index 1 — index 0 is the Cover image)
document.querySelectorAll('.toc-item-button')[1].click();
// wait 2s → page 1
```

This reliably navigates to page 1 and touch-event forward navigation works immediately after.

### Does NOT work:
- Scrubber to value=0: lands on Cover image page, forward touch nav broken
- ArrowLeft N times: breaks browser state after ~400 presses (`backdrop-no-scroll` + modal state)
- `#kr-chevron-left` JS click: silently ignored for unvisited pages

---

## DOM Structure

```
main-content
  ├── ION-MENU (side-menu)
  ├── ION-HEADER (reader-header)
  │     └── navigation buttons (Table of Contents, Search, etc.)
  ├── DIV (kr-interaction-layer-fullpage)
  │     ├── DIV.loader (empty, full-page, always display:block — normal)
  │     └── DIV.pagination-container
  │           ├── BUTTON#kr-chevron-left (Previous page — touch only works for visited pages)
  │           └── BUTTON#kr-chevron-right (Next page — touch events work)
  └── DIV.footer-label-color-default (data-testid="footer")
        ├── ION-RANGE#kr-scrubber-bar (progress scrubber, min=0, max=~969100)
        └── ION-FOOTER (page info text)
```

### Key selectors:
- `[data-testid='footer'], .footer-label-color-default` — footer with page info
- `#kr-chevron-right` / `#kr-chevron-left` — next/prev page buttons
- `#kr-scrubber-bar` — progress scrubber (Ionic range, location units not page numbers)
- `.toc-item-button` — TOC chapter entries (only visible when TOC panel open)
- `#kra-scrubber-back-button` — "Back to page X" button after jump navigation
- `[aria-label="Table of Contents"]` — TOC sidebar open button

---

## Page Numbering

Kindle uses two numbering systems that can switch mid-session:
- **Kindle pages**: e.g., "Page 98 of 559" — virtual pages, larger numbers
- **Book pages**: e.g., "Page 20 of 177" — actual printed page numbers, smaller
- **Locations**: e.g., "Location 1 of 8365" — front matter / cover area

`get_page_info` regex `Page (\d+) of (\d+)` captures both systems. After scrubber/TOC navigation, the numbering may change from Kindle pages to Book pages. Track the `total` carefully — it can change.

---

## backdrop-no-scroll

`document.body` always has class `kr-fullpage-body backdrop-no-scroll` in the Kindle reader. This is NORMAL — it's not a modal blocking state. Do not try to remove it; it's always there.

---

## Gotcha: Scrubber Navigation Breaks Forward Nav

After `scrubber.value = 0` + `ionChange` event:
- Book jumps to Cover page (Location 1)
- `#kra-scrubber-back-button` appears with "Back to X"
- Touch events on `#kr-chevron-right` do NOT work from the Cover page
- Only the Back button restores normal navigation

This is specific to the Cover page (index 0 in TOC). Navigating to "Title Page" (index 1 in TOC) and then using touch events works fine.

---

## Extraction Rate

- Sequential (old): ~17s/page actual (Gemini ~10-14s + 2.3s nav)
- Depth-5 pipeline: ~2.3–4s/page (navigation is the hard floor — can't navigate 2 pages simultaneously)
- **Pipeline depth ceiling = nav floor (~2.3s).** D=5 is the practical sweet spot. D=10 adds nothing except rate-limit risk.

## Current default model: gemini-3-flash-preview

Better instruction-following than 2.5-flash-lite (fewer garbled columns, better footer exclusion).
Disable thinking for OCR — no reasoning needed:

```python
config = types.GenerateContentConfig(
    thinking_config=types.ThinkingConfig(thinking_level="minimal")
)
```

Apply when `model.startswith("gemini-3")`. For 2.5 models use `thinking_budget=0` (different param name). Don't mix both in the same call.

## Queue Mode Gotchas

- **Book load detection needs patience**: 3 retries × 3s isn't enough mid-queue (browser still transitioning). Use 8 retries with increasing waits (3s→10s). A skipped book = silent data loss.
- **google-genai SDK: GOOGLE_API_KEY takes precedence over GEMINI_API_KEY** when both are set. Check `env | grep -i key` if behaviour seems wrong.
- **Retry tiers for API errors**: quick backoff (10s→60s) for burst rate limits, 5-min patience loop for quota exhaustion. Infinite patience = truly forgettable overnight queue.

## Script location
`~/code/kindle-extract/kindle-extract` (git repo: `terry-li-hm/kindle-extract`)
Symlinked: `~/bin/kindle-extract`
