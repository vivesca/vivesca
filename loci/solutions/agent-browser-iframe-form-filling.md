# agent-browser: Filling Forms with Cross-Origin Iframes (JotForm)

## Problem

JotForm embeds some fields (Chinese name, occupation, emergency contact, T&C) as cross-origin iframes (`widgets.jotform.io`, `app-widgets.jotform.io`). Standard agent-browser commands (`fill`, `type`, `click @ref`) can't target elements inside these iframes.

## What Doesn't Work

- **`fill`/`type` with iframe selector** — types to the iframe element, not inputs inside it
- **`eval` accessing iframe contentDocument** — blocked by same-origin policy
- **`postMessage` to iframe** — JotForm widgets don't respond to arbitrary messages
- **`Ctrl+A` inside iframe inputs** — selects parent page content, not iframe input text
- **`click @ref`** on radio buttons sometimes runs in background and fails (parallel tool call cascade issue)

## What Works

1. **Tab navigation** enters iframe inputs. From the field before the iframe, pressing Tab crosses the iframe boundary into the first input.
2. **Character-by-character `press`** types into the focused iframe input: `for char in B a n k i n g; do agent-browser press "$char"; done`
3. **`Shift+Tab`** moves backward through iframe inputs.
4. **`End` + repeated `Backspace`** clears iframe input text (since Ctrl+A doesn't work).
5. **`eval` with `document.getElementById().click()`** works for radio buttons and checkboxes in the parent frame.

## JotForm Date Picker Gotcha

JotForm date fields display DD-MM-YYYY format but parse input as MM-DD-YYYY internally. Entering "09-03-1989" becomes September 3, not March 9. The date picker button label reveals the actual parsed date. Opening the date picker (clicking the calendar button) can sometimes re-parse correctly.

## Pattern

```
# 1. Fill regular fields with fill/type
agent-browser fill @e12 "Ho Ming Terry"

# 2. Click radios/checkboxes via JS eval
agent-browser eval "document.getElementById('input_7_0').click()"

# 3. For iframe fields: Tab in, then press keys
agent-browser fill @e278 ""  # focus last field before iframe
agent-browser press Tab       # enters iframe
agent-browser press Tab       # first input in iframe
for char in B a n k i n g; do agent-browser press "$char"; done
```

## Parallel Tool Call Warning

Don't batch `agent-browser click` calls in parallel — if one fails, ALL sibling calls fail with "Sibling tool call errored". Run clicks sequentially or use a single `eval` block.

Discovered: 2026-02-25, filling Asia Medical Specialists patient registration form.
