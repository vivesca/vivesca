# Radix UI — Browser Automation Patterns

## The Core Problem

Radix UI dropdown menu items cannot be triggered via standard DOM automation approaches. All of the following fail:

- `agent-browser click @ref` (ref-based Playwright click)
- `el.click()` via `eval`
- Synthetic `MouseEvent`/`PointerEvent` dispatch
- `agent-browser mouse move/down/up` (coordinate-based)
- `element.dispatchEvent(new PointerEvent('pointerdown'))` etc.

**Root cause:** Radix UI `DropdownMenu.Item` uses `onPointerDownCapture` internally. Items with destructive actions (e.g. Delete) also call `window.confirm()` for confirmation. `window.confirm()` in headless Playwright does not auto-accept — it blocks the async handler and the button's loading state (`n(!0)`) never resets (`n(!1)`), leaving the button disabled on next attempt.

## Working Solution: React Fiber Introspection

```javascript
// 1. Override confirm BEFORE anything else (otherwise button gets stuck disabled)
window.confirm = () => true;

// 2. Walk the React fiber tree from the target element to find the onClick handler
var el = document.querySelector('button[aria-label="Delete key"]');
// Or find by text:
// var buttons = [...document.querySelectorAll('button')];
// var el = buttons.find(b => b.textContent.includes('Delete'));

var fiber = el.__reactFiber || el[Object.keys(el).find(k => k.startsWith('__reactFiber'))];
var handler = null;
var node = fiber;
while (node) {
  if (node.memoizedProps && node.memoizedProps.onClick) {
    handler = node.memoizedProps.onClick;
    break;
  }
  node = node.return;
}

// 3. Call the handler with a mock event
if (handler) handler({ preventDefault: () => {}, stopPropagation: () => {} });
```

## Full Sequence (agent-browser)

```bash
# Step 1: open the dropdown menu first (click the trigger)
agent-browser click @ref_N   # the ... / kebab menu button
# Step 2: in a SEPARATE bash call, run the fiber eval
agent-browser eval 'window.confirm = () => true; var el = ...; ...'
```

**Critical:** Set `window.confirm = () => true` BEFORE calling the handler. If you call the handler first, the loading state (`n(!0)`) gets set but the async body throws (confirm returns undefined → falsy), so `n(!1)` is never called. The button is then stuck disabled until page reload.

## Next.js Server Actions (OpenRouter key delete)

The delete action POSTs to the server action endpoint with:
```
POST /settings/keys
body: ["<key-hash>", {"deleted": true}, {"isProvisioningKey": false}]
```
Confirmed via `window.fetch` interceptor. If React fiber approach is working, the POST fires automatically — no need to construct the request manually.

## Radix UI Dropdown: DOM Location

Radix UI renders dropdown content in a portal at `document.body` level, **not** inside the trigger element's DOM subtree. After opening a dropdown:
```javascript
document.body.querySelectorAll('[role="menuitem"]')  // finds items
```
The accessibility tree (`snapshot`) should reflect this — look for menu items near the bottom of the tree output, not nested under the trigger.

## Failure Mode: Button Stuck Disabled

If the button becomes unclickable after a failed attempt (React state stuck):
- Page reload resets React state
- After reload: set up `window.confirm` override FIRST, then open menu, then invoke handler — all without reload in between.

## Confirmed Working (Mar 2026)

OpenRouter dashboard (`openrouter.ai/settings/keys`) — deleted "consilium-test" key after ~20 attempts with other approaches. Final working eval: confirm override + `__reactFiber` walk + mock event call.
