# Workday Forms Block Browser Automation via CDP

## Problem

Workday career portals (e.g., Manulife `careers.manulife.com`) resist browser automation:

1. **Headless blocked entirely** — returns "Access Denied" for headless browsers
2. **CDP read works, actions timeout** — `snapshot`, `eval`, `get url` work fine, but `click`, `fill`, `select`, `scrollintoview` all timeout on form elements
3. **JS DOM manipulation doesn't sync React state** — setting `select.value` or `textarea.value` via `eval` updates DOM but Workday's internal state doesn't register. The "Next" button stays `disabled`.

## Root Cause

Workday uses anti-automation detection on Playwright's actionability checks. The `scrollIntoViewIfNeeded` step (which Playwright runs before every action) triggers a timeout. Elements are visible and resolved, but Playwright can't complete the action pipeline.

## What Works

- `agent-browser --cdp 9222 eval "JS"` — full DOM read/write
- `agent-browser --cdp 9222 snapshot` — accessibility tree with refs
- `agent-browser --cdp 9222 get url` / `get title`
- Step 1 personal info fields: `fill` works on simple text inputs
- File upload: `upload input[type=file] /path/to/file.pdf` works

## What Doesn't Work

- `click`, `fill`, `select` on Workday form elements (step 3+)
- `scrollintoview` on any Workday element
- JS-only value setting for React-controlled selects/textareas — DOM updates but form validation fails

## Workaround

For Workday applications:
- Use `agent-browser` for navigation, login, CV upload, and simple text fields
- For dropdowns, checkboxes, and later form steps: manual interaction required
- The form saves progress — user can pick up where automation left off

## Environment

- agent-browser v0.9.3 via CDP (port 9222)
- Chrome CDP wrapper app on macOS
- Workday career portal (Phenom-powered frontend)
