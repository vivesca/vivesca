---
name: vectura
description: Import Apple Passwords CSV exports into 1Password via the op CLI. Use when migrating passwords or catching new items saved to Apple Passwords after the initial import.
effort: low
---

## Usage

```bash
# Dry run — see what would be imported (no op calls)
vectura import ~/Downloads/Passwords.csv --dry-run

# Full import into Personal vault (default)
vectura import ~/Downloads/Passwords.csv

# Custom vault and tag
vectura import ~/Downloads/Passwords.csv --vault Work --tag apple-import-2026

# Install / update
cargo install vectura
```

## How to export from Apple Passwords

iOS: Settings → Passwords → ⋯ → Export Passwords → Export
macOS: Passwords app → File → Export Passwords

Saves as `Passwords.csv` to Downloads.

## Behaviour

- Deduplicates by title before importing (Apple exports duplicates)
- Skips items that already exist in 1Password (409 conflict = not a failure)
- Rate limit: 1 worker, exponential backoff (3s → 6s → 12s → 24s → 48s, 5 attempts max)
- Tags all imported items (`imported-from-apple` by default) for easy review in 1Password
- OTP fields (`OTPAuth` column) imported as TOTP entries

## After import

- Review tagged items in 1Password: filter by tag `imported-from-apple`
- Delete the CSV: `rm ~/Downloads/Passwords.csv` — it contains plaintext passwords
- Disable Apple Passwords as AutoFill provider (iOS: Settings → Passwords → AutoFill Passwords) so new credentials go to 1Password only

## Gotchas

- `op` CLI must be installed and signed in (`op signin`) before running
- Large exports (~1400 items) take ~25 min at 1 item/sec due to rate limiting
- First import in Mar 2026 successfully migrated 1420 items from Apple Passwords
