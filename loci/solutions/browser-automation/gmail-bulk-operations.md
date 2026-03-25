# Gmail Bulk Operations via Browser Automation

LRN-20260305-001. Full inbox cleanup for terry39@gmail.com (6,114 → 198 unread in one session).
LRN-20260305-002. Selective inbox triage for terry39@gmail.com (198 → 0 in one session). Patterns for spam detection and sender-based batch operations documented below.

## Account Index Map (terry's Google accounts)

| Index | Account |
|-------|---------|
| u/0 | terry.li.hm@gmail.com (primary) |
| u/1 | taracny@gmail.com |
| u/2 | terry39us@gmail.com |
| u/3 | terry39@gmail.com |

URL pattern: `https://mail.google.com/mail/u/3/#category/promotions`

## Auth Flow

```bash
porta inject --domain google.com
agent-browser open "https://mail.google.com/mail/u/3/#inbox"
```

Always use `agent-browser open` (not `eval window.location.href`) for initial navigation — the persistent profile has many tabs and eval can hit the wrong one.

## Critical Bug: snapshot Deselects Page-Level Selection

`agent-browser snapshot` triggers a focus event in Gmail that **deselects** the current page selection (100 conversations selected state). This causes the infamous "None selected" mystery.

**Exception:** Snapshot does NOT deselect when the state is "All conversations selected" (after clicking the "Select all X conversations in" link). Only page-level (100 selected) is affected.

**Rule:** Use `agent-browser screenshot` for visual state verification. Only use snapshot when nothing is selected (to get refs) or when in "All conversations selected" state.

## Working Bulk Archive Sequence

For categories with >100 conversations:

```bash
# 1. Navigate to category
agent-browser open "https://mail.google.com/mail/u/3/#category/promotions"
sleep 4

# 2. Get Select button ref (snapshot safe here - nothing selected)
agent-browser snapshot > /tmp/snap.txt
# Expect: button "Select" [ref=e29], button "Show more messages" [ref=eNN]: 1–100 of X,XXX

# 3. Select all 100 on page
agent-browser click "@e29"

# 4. Click "Select all X,XXX conversations in" link via JS (NOT snapshot/ref)
agent-browser eval "Array.from(document.querySelectorAll('span,a')).find(function(el) { return el.textContent.includes('Select all') && el.textContent.includes('conversations') }).click()"

# 5. Now safe to snapshot - state is "All conversations selected"
agent-browser snapshot > /tmp/sel.txt
# Expect: text: All conversations selected
# Find: button "Archive" [ref=e32], button "Mark as read" [ref=e35]

# 6. Mark as read
agent-browser click "@e35"
sleep 2
# May show confirmation dialog:
agent-browser snapshot > /tmp/dlg.txt  # safe - "All conversations selected" persists through dialogs
# If dialog: button "OK" [ref=e3]
agent-browser click "@e3"
sleep 3

# 7. Re-select (mark-as-read resets selection)
agent-browser click "@e29"
agent-browser eval "Array.from(document.querySelectorAll('span,a')).find(function(el) { return el.textContent.includes('Select all') && el.textContent.includes('conversations') }).click()"

# 8. Archive - DO NOT snapshot between selection and this click
agent-browser click "@e32"
sleep 2
# Confirmation dialog appears
agent-browser eval "Array.from(document.querySelectorAll('button')).find(function(b) { return b.textContent.trim() === 'OK' }).click()"
sleep 5
```

For categories with <=100 conversations (fits on one page):
```bash
# All conversations selected immediately when clicking @e29
agent-browser click "@e29"
# Then directly click Archive/Mark as read refs
```

## Confirmation Dialog Pattern

Gmail shows "Confirm bulk action" dialog for any bulk operation affecting ALL conversations (even <100 if selected via "Select all X conversations" link). The dialog does NOT appear for page-level selections (100 items, no "Select all" link clicked).

Dialog buttons: `button "Cancel" [ref=e2]`, `button "OK" [ref=e3]`.

## Category URLs

| Category | URL hash |
|----------|----------|
| Promotions | `#category/promotions` |
| Social | `#category/social` |
| Updates | `#category/updates` |
| Forums | `#category/forums` |
| Purchases | `#category/purchases` |

## Why snapshot Sometimes Deselects

The Playwright accessibility tree inspector (snapshot) triggers DOM focus events. Gmail's selection state is managed by focus — when the inspector grabs focus to build the tree, Gmail's JS interprets it as "user clicked elsewhere" and fires the deselect handler. This only affects the intermediate "100 selected" state; the "All conversations selected" state is stored server-side and is immune.

## Selective Inbox Triage Workflow

For inbox cleanup when emails need per-sender decisions (spam vs archive vs keep).

### Step 1: Extract actual sender email addresses

Display names are unreliable — always get the real `from:` address first:

```javascript
// Run from inbox page to get sender email + subject for each row
Array.from(document.querySelectorAll('tr.zA')).map(function(r) {
  var s = r.querySelector('.yX');
  var e = r.querySelector('.zF');
  var subj = r.querySelector('.y6');
  return (s ? s.textContent.trim() : '?') + ' <' + (e ? e.getAttribute('email') : '?') + '>: ' + (subj ? subj.textContent.trim() : '?');
}).join('\n')
```

Run via: `agent-browser eval "..."` (write to /tmp/js first to avoid shell quoting issues).

### Step 2: Search by domain and bulk spam/archive

```bash
# Spam a batch of senders by domain
agent-browser open "https://mail.google.com/mail/u/3/#search/from%3Aspamsite.com+OR+from%3Aother.com+in%3Ainbox"
# Select all → Report spam → confirm dialog
```

**URL encode** the `@` signs as `%40` when using exact email addresses.

**Batch size**: Keep OR queries to ~15 email addresses/domains — longer queries work but are unwieldy.

### Step 3: "Report spam or unsubscribe?" dialog

Some senders trigger a dialog instead of immediate action. Always click "Report spam" (not Unsubscribe) for clear junk:

```javascript
Array.from(document.querySelectorAll('button')).find(function(b) { return b.textContent.trim() === 'Report spam' }).click()
```

### Phishing Detection Pattern

**Always verify display name vs actual `from:` domain.** Common deceptions found:
- "HSBC" displayed but sent from `violet.sclaudia@nifty.com` — phishing
- "Jessie" (personal name) sent from `andrewschristiana1@gmail.com` — romance scam
- Any bank/official name sent from gmail.com, hotmail.com, or random domains = phishing

The `.zF` email extraction step above catches these before you archive them by accident.

### Gibberish Sender Pattern

Spam campaigns use randomly-generated display names + gmail.com accounts. Pattern: `[4-9 lowercase letters] [5-8 alphanum]` as sender, gibberish subject like `kjqbahy iwobprkhaeuebmium Re: ygjgabv0`. Extract their actual gmail addresses and batch-spam by address list.

## Fallback: Find Archive Button by Position

If Archive button is not findable by `data-tooltip="Archive"` (multiple matches), find by DOM position:

```javascript
// The toolbar Archive button is index [1] (index [0] is invisible/off-screen)
var archives = Array.from(document.querySelectorAll('[data-tooltip="Archive"]'));
// Verify: archives[1].getBoundingClientRect() should show top ~78, left ~460
archives[1].click();
```
