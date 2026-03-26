---
name: pseudopod
description: Web page ingestion — extract structured content from URLs when chemotaxis search synthesis is insufficient.
model: sonnet
---

# Pseudopod — extend toward the source

**Rule: use when you need the actual page, not a synthesis about the page.**

## When this fires

- Search results cite a specific URL and you need its exact content (prices, specs, schedules)
- Completing a device auth flow that requires browser interaction
- Verifying a claim against a specific page (not search synthesis)
- Taking a screenshot for visual confirmation

## Discipline

1. **Try `endocytosis_extract` first** — it has automated fallbacks built in (open → eval → get text → innerText). Don't pre-empt the fallback chain by calling lower-level browser commands.

2. **`wait_ms`** — default 3000ms is usually enough. Increase to 5000-8000 for JS-heavy pages (dashboards, SPAs). Check `success` field in result before reading `text`.

3. **`endocytosis_check_auth` before scraping login-gated content** — if you navigate to a domain that requires auth, the auth check will tell you and provide the fix command. Don't read text that's actually a login redirect.

4. **On headless (SSH/Blink)** — skip pseudopod entirely; agent-browser needs a display. Use chemotaxis_ask as fallback. See `memory/feedback_headless_skip_gui.md`.

5. **Two failed navigations = stop** — don't keep retrying with different approaches. Surface the failure and ask the user. See `memory/feedback_stop_browser_flailing.md`.

6. **Screenshots** — use `endocytosis_screenshot` for visual verification only; don't use as a substitute for text extraction when text is available.

## Anti-patterns

| Don't | Do |
|-------|-----|
| Use pseudopod when search synthesis suffices | Use noesis unless you need the exact page |
| Retry navigation more than twice | Stop at 2 failures, report and ask |
| Read text without checking success field | Always check success before parsing text |
| Skip auth check on login-gated domains | endocytosis_check_auth first |
| Use on headless sessions | Check display availability; use noesis as fallback |
