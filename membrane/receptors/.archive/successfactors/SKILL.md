---
name: successfactors
description: Automate and work around SAP SuccessFactors job application portals. Use when filling SuccessFactors-based forms.
---

# SuccessFactors Portal Automation

Workarounds for automating SAP SuccessFactors career portals, which use custom UI widgets that resist standard form automation.

## When to Use

When filling job applications on SuccessFactors-based career portals (common among large enterprises like Shangri-La, many Fortune 500 companies).

**Signs you're on SuccessFactors:**
- URL contains `successfactors.com`
- Custom dropdown widgets with `sui-pill` classes
- Combobox + button pairs for dropdowns

## The Problem

SuccessFactors dropdowns don't respond well to:
- Standard `form_input` tool
- Coordinate clicks (often select wrong option)
- Keyboard navigation (inconsistent)

The dropdowns use custom widgets where the visual state and form validation are tied to internal state, not just input values.

## Solution: JavaScript Click on Role Options

### Step 1: Open the dropdown

Click the dropdown button to open the options list:

```javascript
// Using ref from read_page
computer action=left_click ref=ref_XX
```

### Step 2: Click the option via JavaScript

```javascript
// Find all listbox items and click the one matching your target
const listItems = document.querySelectorAll('[role="option"], [role="listitem"], li[data-value]');
for (const item of listItems) {
  if (item.textContent.trim() === 'TARGET_VALUE') {
    item.click();
    break;
  }
}
```

**Example for Yes/No dropdowns:**
```javascript
const listItems = document.querySelectorAll('[role="option"]');
for (const item of listItems) {
  if (item.textContent.trim() === 'No') {
    item.click();
    break;
  }
}
```

## Common Fields

### "How did you find out about this opportunity?"
Options typically include: LinkedIn, Facebook, Online Job Boards, Referral, Shangri-La Website, etc.

### "Are you currently employed by [Company]?"
Options: No Selection, No, Yes

### "Have you worked for [Company] before?"
Options: No Selection, No, Yes

## Workflow

1. **Login** — User handles manually (credentials)
2. **Personal info** — Usually pre-filled from profile
3. **Phone number** — May need manual entry via `form_input`
4. **Dropdowns** — Use JavaScript click method above
5. **Resume** — Often already uploaded from profile
6. **Checkboxes** — Use ref clicks (these work normally)
7. **Submit** — Click Apply button

## Tips

- Take screenshots after each dropdown to verify selection stuck
- The dropdown must be open (visible) before the JavaScript click will work
- Some fields show validation errors but still allow submission — proceed and check final confirmation
- Checkbox refs work normally, no special handling needed

## Files

- This skill: `/Users/terry/skills/successfactors/SKILL.md`
