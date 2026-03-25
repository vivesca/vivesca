---
module: Browser Automation
date: 2026-03-02
problem_type: form_fill
component: browser_automation
symptoms:
  - "Date field resets to today's date after fill"
  - "Select dropdown value silently ignored"
  - "agent-browser eval fails with exit code 1 on complex JS"
root_cause: framework_reactivity
resolution_type: pattern
severity: medium
tags: [agent-browser, date-picker, select, eval, js, form, mycpa]
---

# Form Automation: Date Fields, Selects, and Complex JS

Lessons from automating the HKICPA MyCPA CPD self-declaration form (2026-03-02).

## 1. Date fields with calendar pickers — `fill` doesn't stick

**Problem:** `agent-browser fill @ref "21/12/2023"` appears to work but the field reverts
to today's date. The calendar picker overrides the typed value on blur.

**Fix:** Use JS native value setter + dispatch both `input` and `change` events:

```python
import subprocess

js = """
var el = document.querySelector('input[name="epDateFr"]');
el.value = '21-12-2023';
el.dispatchEvent(new Event('input', {bubbles:true}));
el.dispatchEvent(new Event('change', {bubbles:true}));
"""
subprocess.run(['agent-browser', 'eval', js], capture_output=True, text=True)
```

**Date format:** Always check by inspecting what the field shows after natural use
(screenshot, then read). MyCPA uses `DD-MM-YYYY` with dashes, not slashes.

## 2. Select option values ≠ display text — inspect before setting

**Problem:** `select.value = 'Verifiable'` silently fails if the actual option value
is `'3'` (not the display text).

**Always inspect first:**

```python
js = """
const selects = document.querySelectorAll('select');
const result = [];
selects.forEach((s, i) => {
  const opts = [...s.options].map(o => o.value + ':' + o.text);
  result.push('Select ' + i + ': ' + opts.join(', '));
});
result.join(' | ');
"""
```

Then set using the actual value:

```python
js = "document.querySelectorAll('select')[2].value='3'; document.querySelectorAll('select')[2].dispatchEvent(new Event('change',{bubbles:true}));"
```

## 3. Complex JS in eval — use Python subprocess, not shell heredoc

**Problem:** Shell heredoc quoting breaks with `agent-browser eval "$(cat ...)"`.
Inline JS with quotes or special chars fails with exit code 1.

**Fix:** Pass JS as a Python string via subprocess — no shell interpolation:

```python
import subprocess, json

def ab_eval(js):
    r = subprocess.run(['agent-browser', 'eval', js], capture_output=True, text=True)
    return r.stdout.strip()

# Safe string interpolation into JS:
title = "Course title with 'quotes'"
js = f'document.querySelector("input[name=\\"epName\\"]").value = {json.dumps(title)};'
ab_eval(js)
```

## 4. Inspect input names before using refs

Refs shift after any DOM mutation. Input `name` attributes are stable.

```python
js = """
const inputs = document.querySelectorAll('input[name]');
const result = [];
inputs.forEach((el, i) => result.push(i + ':name=' + el.name + ',value=' + el.value));
result.join(' | ');
"""
```

Use `document.querySelector('input[name="fieldName"]')` for all subsequent JS —
more robust than positional refs.

## 5. Batch form entry — "Save & add more" pattern

When a form has a "Save & add more" button, use it. The dialog clears and stays open,
avoiding re-navigation. Pattern for batch automation:

```python
entries = [...]

for entry in entries:
    # Set all fields via JS
    set_fields(entry)
    # Find and click "Save & add more"
    snap = ab(['snapshot'])
    ref = extract_ref(snap, 'Save & add more')
    ab(['click', f'@{ref}'])
    time.sleep(2)  # Wait for server round-trip
```

## 6. Consolidate entries for bulk logging

When logging many similar activities (50+ courses), check if the portal explicitly
allows consolidated entries. HKICPA MyCPA says:
> "You may use your own method for recording your CPD activity details."

Consolidate by year + type (verifiable/non-verifiable) = 7 entries vs 52.
Hours = sum of all courses in that group. Date range = first to last course date.
Include "see [document] for full list" in Remarks.

## 7. Verify via live counter, not success messages

The "successfully processed" toast is unreliable to catch programmatically.
Instead, watch the running counter (total hours displayed on the page) — it updates
after each successful save. If it doesn't increment, the entry didn't save.
