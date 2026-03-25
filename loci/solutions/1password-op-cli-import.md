# 1Password op CLI: Bulk Import from CSV

## Context
Migrating Apple Passwords CSV export (1420 items) to 1Password via op CLI v2.32.0.

## Key Findings

**`op` has no import subcommand.** Must use `op item create` per item.

**Field assignment format for Login items:**
- `username=value` — no type annotation needed for built-in fields
- `password=value`
- `notesPlain=value` — NOT `notesPlain[notes]=value` (`notes` is not a valid type)
- `totp[otp]=otpauth://...` — OTP requires `[otp]` type annotation

**Rate limits:** 1Password API throttles at ~3+ concurrent workers ("Too many requests").
Settled on 1 worker + exponential backoff (3s → 6s → 12s → 24s → 48s). ~1 item/sec.

**409 Conflict:** Item already exists — treat as skip, not failure.

**Duplicate CSV entries:** Apple Passwords exports duplicates. Dedup by title before creating tasks.

**CXP credential exchange (macOS 26):** "Export all items to App" uses the FIDO CXP standard. Transfers passwords + passkeys encrypted, no CSV. 1Password hasn't implemented the receiving side yet (as of Mar 2026). Bitwarden + Dashlane have. Check back in a few months.

## Import Script
`/tmp/import_passwords.py` — tag `imported-from-apple` applied to all items for easy review.

## ERR-20260307-001: `op item edit` fails on items with ssoLogin field

`op item edit` validates the entire item before saving. If any field has type `ssoLogin` (e.g. "sign in with Google/Apple" saved by browser extension), the CLI rejects the edit with:

```
[ItemValidator] has found 1 errors: details.sections[0].fields[0] has unsupported field type: ssoLogin
```

**Workaround:** Edit in the 1Password app directly. The app UI handles ssoLogin fields without validation errors. CLI workaround (specifying field by ID) does not bypass the item-level validator.

## Cleanup
Delete `~/Downloads/Passwords.csv` after import completes.
