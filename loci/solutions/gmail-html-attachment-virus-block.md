# Gmail blocks HTML files with embedded JavaScript as "Virus detected"

## Problem

Attaching an HTML file with a large inline `<script>` block (e.g., embedded SheetJS ~950KB) to a Gmail message triggers "Virus detected!" and blocks the attachment. This is a false positive — Gmail's scanner treats substantial inline JS as potentially malicious.

## Workaround

Password-protected zip bypasses Gmail's content scanner:

```bash
zip -e -P <password> output.zip file.html
```

Attach the .zip and include the password in the email body.

## Why it happens

Gmail scans inside unprotected archives and HTML files for malicious scripts. Any HTML with a large JS payload (especially minified, obfuscated-looking library code) triggers heuristic detection. Password-encrypted zips can't be scanned, so they pass through.

## Alternatives

- Share via cloud storage link (OneDrive, Google Drive) instead of attachment
- Rename to `.txt` (recipient renames back — awkward)
- Split JS into a separate `.js` file and zip both together (unprotected zip may still get flagged)
