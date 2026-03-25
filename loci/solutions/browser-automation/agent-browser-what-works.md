# agent-browser: What Works and What Doesn't (CDP mode)

Tested Feb 2026 on Manulife Workday (v0.9.3, Chrome CDP port 9222, 8GB Mac).

## Reliability Tier List

### Always works
- `get url`, `get title` — basic page info
- `eval "JS"` — run any JS, read DOM, extract data
- `snapshot` — accessibility tree (may need `-d 3` depth limit on heavy SPAs)
- `upload "input[type=file]" "/path/to/file"` — file upload

### Usually works
- `fill @ref "text"` — text inputs on simple forms (step 1 personal info)
- `check "#id"` — checkboxes (use ID selector, not @ref if ref times out)
- `select @ref "value"` — simple dropdowns (worked on Gender, not on Workday questionnaires)
- `press "Enter"`, `press "Tab"` — keyboard events

### Unreliable on Workday/heavy SPAs
- `click @ref` — times out on Workday buttons (anti-automation actionability checks)
- `fill @ref` on complex widgets — times out on textareas, some selects
- `scrollintoview @ref` — times out (Playwright's pre-action check fails)
- `open "url"` — times out waiting for `load` event on SPAs

### Never works
- Headless mode on career sites — "Access Denied" (anti-bot)
- JS `.value =` for React/Angular state sync — DOM updates but framework state doesn't

## Fallback Patterns

| When this fails... | Do this instead |
|---|---|
| `open "url"` timeout | `eval "window.location.href = 'url'"` + `sleep 5` |
| `click @ref` timeout | `eval "document.querySelector('button.btn-next').click()"` |
| `fill @ref` timeout | `eval` with `nativeInputValueSetter` (DOM only, won't sync React) |
| `fill` doesn't sync React | `fill @ref "text"` + `press "Tab"` (blur triggers state update) |
| `type` overwrites wrong | `type` APPENDS. Use `fill` to replace, or `click` + `Ctrl+A` + `Backspace` + `type` |
| `snapshot` timeout | `eval` to extract form fields: `document.querySelectorAll('input,select,textarea')` |
| Playwright actions all timeout | Form is automation-proof. Use automation for login/upload/reading, manual for submission |

## Decision Flow for Form Filling

1. Navigate via `eval "window.location.href = ..."` (avoids load timeout)
2. Wait 5-10s for SPA to render
3. Try `snapshot -i` — if works, use @refs; if not, use `eval` to map fields
4. Fill text inputs with `fill @ref "value"` — these usually work
5. Upload files with `upload "input[type=file]" "/path"`
6. For dropdowns: try `select @ref "value"` — if timeout, use `eval` to set `.value` + `dispatchEvent`
7. For checkboxes: `check "#id"`
8. Click Next/Submit via `eval "button.click()"` as first choice (more reliable than Playwright click)
9. If form validation fails (Next disabled), the `eval`-set values didn't sync — need manual interaction

## Form Filling: Worth It Now That Patterns Are Mapped

First attempt took 2 hours (learning cost). With the playbook below, expect **10-15 minutes** per application including login.

**The fast path:**
1. `eval "window.location.href = ..."` to navigate (skip load timeout)
2. `fill @ref "text"` + `press Tab` for text inputs (triggers React blur)
3. `upload "input[type=file]" "/path"` for CV
4. `eval "button.click()"` for Next/Submit (skip Playwright actionability checks)
5. `check "#id"` for checkboxes
6. Personal details from `~/epigenome/chromatin/Personal Details for Applications.md`
7. Credentials from 1Password CLI

**Still manual:** Workday dropdowns that timeout on `select` — click them yourself. Everything else is automatable.

**If dropdowns also need automating**, use **Peekaboo** (macOS UI automation) — real OS-level clicks bypass all anti-automation.

## When User Needs to See the Browser (CAPTCHA, visual confirmation)

`agent-browser` is **headless** — invisible on screen and via Jump/remote desktop. If the user needs to watch or interact (e.g. CAPTCHA), use **osascript JS injection into visible Chrome** instead:

```bash
osascript << 'EOF'
tell application "Google Chrome"
  execute active tab of front window javascript "
    // 1. First get field names:
    // document.querySelectorAll('input,select').forEach(el => console.log(el.name, el.id))

    // 2. Fill with nativeInputValueSetter (works on plain HTML forms):
    function setVal(el, val) {
      var s = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
      if (s) s.set.call(el, val);
      el.dispatchEvent(new Event('input', {bubbles: true}));
      el.dispatchEvent(new Event('change', {bubbles: true}));
    }
    setVal(document.getElementById('fieldId'), 'value');
    document.getElementById('selectId').value = 'opt';
    document.getElementById('selectId').dispatchEvent(new Event('change', {bubbles:true}));
    'done';
  "
end tell
EOF
```

**Workflow:**
1. `open "https://..."` → opens in visible Chrome
2. Use osascript to query field names/IDs (`querySelectorAll('input,select')`)
3. Inject values via osascript JS
4. User handles CAPTCHA + final submit via Jump

**Limitation:** Works on plain HTML forms. React/Angular state-synced forms may need `fill @ref + Tab` via agent-browser instead.

## LinkedIn (Mar 2026)

| Scenario | What works | What fails |
|----------|-----------|------------|
| Page load | `open <url>` + `wait 4000` | `wait --load networkidle` — times out |
| Notification loop | `close` → `porta inject` → `open` → `wait 4000` | Repeated `open` calls — keeps looping |
| Verify URL | `eval "document.title + ' | ' + window.location.href"` | Trusting snapshot alone (may be wrong page) |
| Auth | `porta inject --browser chrome --domain linkedin.com` | Native profile login — often triggers loop |

**Notification loop** fires on fresh profiles and after `porta inject` into a new profile dir. Symptom: snapshot shows `mypreferences/d/notification-subcategories/...` instead of the target page. Fix: `close`, inject, reopen with fixed wait.

**Per-session profiles** (set in `~/.zshrc`): each tmux window gets `~/.agent-browser-profile-$N`. Run `porta inject` once per window — cookies don't transfer between profile dirs.

## Key Numbers

- v0.9.3 fixed EAGAIN (os error 35) that plagued v0.5.0 on 8GB Macs
- Workday SPA takes 5-10s to render after navigation
- CDP reconnects per command — keep tab count low to reduce memory pressure
- `snapshot -i -c -d 3` is the most reliable combo for heavy pages (interactive only, compact, depth-limited)
