# SAP SuccessFactors Career Portal — Browser Automation

Confirmed working patterns for `career10.successfactors.com` (HKJC). Mar 2026.

## Navigation

**Direct URL fails.** `career10.successfactors.com/career?company=HongKongJC` returns "An error occurred." — no valid session token.

**Correct flow:** Navigate via the employer's careers site → find the job listing → click "Apply now". This creates the session. Then SuccessFactors loads correctly at `career10.successfactors.com/portalcareer`.

## Account Creation

SuccessFactors Terms of Use dialog is unreliable with Playwright clicks. Workaround: `document.getElementById('fbclc_createAccountButton').click()` submits the form directly regardless of ToU checkbox state. Account is created successfully.

## File Upload

Upload button opens a source dialog (Device / Dropbox / Google). Must click "Upload from Device" first, then the file input appears:

```bash
agent-browser click @e_upload_button   # opens source dialog
agent-browser click @e_upload_device   # click "Upload from Device"
# find the input:
agent-browser eval "Array.from(document.querySelectorAll('input[type=file]')).map(el => el.name + '|' + el.id).join('\n')"
# → fileData1|56:_file
agent-browser upload "input[type=file]" "/path/to/file.pdf"
```

## Dropdowns

No native `<select>` elements — all custom ARIA comboboxes. Pattern:

```bash
agent-browser click @e_combobox        # opens listbox
agent-browser snapshot                  # get option refs
agent-browser click @e_option_menuitem  # click the menuitem inside the option
```

The listbox stays open after clicking — next snapshot shows the selected value in the combobox. Refs shift after each interaction; always re-snapshot before the next action.

## Country/phone code dropdowns

Option values are country codes (e.g. `HK`), not dial codes (`852`). Inspect before setting:
```bash
agent-browser eval "Array.from(document.querySelectorAll('select')[0].options).slice(0,5).map(o => o.value).join(',')"
```

## Known site type

- No Cloudflare — `agent-browser` works without `peruro`
- ARIA comboboxes throughout — no `document.querySelectorAll('select')`
- File upload requires two-step dialog (source selector → device input)
