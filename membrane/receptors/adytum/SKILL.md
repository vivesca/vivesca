---
name: adytum
description: 1Password vault management CLI — migrate, save, hygiene, get, list items in the Agents vault. Use when managing 1Password entries, rotating credentials, or auditing vault contents. "adytum", "1password", "vault hygiene".
---

# adytum

1Password vault management companion.

## Usage

- **Migrate 1PUX:** `adytum migrate <file> [--category <cat>] [--confirm]`
- **Save Credential:** `adytum save --title <t> --url <u> --username <un> --password <p>`
- **Check Hygiene:** `adytum hygiene [--vault <v>]`
- **List Items:** `adytum list [--tag <t>] [--domain <d>]`
- **Get Field:** `adytum get <title> [--field <f>]`

## Categories

- `banking`: Financial institutions, insurance, payment processors.
- `jobs`: LinkedIn, Workday, job boards, recruitment portals.
- `social`: X, Discord, Reddit, Facebook, Instagram.
- `misc`: Everything else.

## Mandates

- **Claude Tag:** ALL items saved via `adytum save` MUST be tagged with `Claude`.
- **Deduplication:** `adytum save` performs a title-based dedup check before calling `op`.
- **Rate Limiting:** Migration includes a 1s delay between `op` calls to prevent 1Password rate limiting.
- **Default Vault:** `Agents` is the default vault for all operations.
