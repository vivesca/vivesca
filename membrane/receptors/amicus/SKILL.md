---
name: amicus
description: Personal CRM CLI — relationship intelligence from Gmail + Calendar. Rust binary. Use when checking stale contacts, looking up who someone is, or getting pre-meeting context.
effort: low
user_invocable: true
---

# amicus — Personal CRM CLI

Local SQLite CRM built from Gmail + Calendar via `gog`. Single Rust binary. No Python/uv dependency. DB at `~/.crm/crm.db` (shared with the retired Python `crm` tool — data preserved on migration).

## Location

`~/code/amicus/` — Rust, clap 4 + rusqlite (bundled). Install: `cargo install --path ~/code/amicus`.

## Commands

```bash
amicus sync [--dry-run]    # Scan 365d Gmail + Calendar + Google Contacts → DB
amicus lookup "name"       # FTS5 search: profile + last 5 interactions
amicus stale [--days 30]   # Contacts not reached in N days (default 30)
amicus dossier --today     # Today's calendar attendees with CRM profiles
amicus stats               # Summary + top 10 most active contacts
amicus import <dir>        # Import LinkedIn data export (Connections.csv + messages.csv)
```

## First Run

```bash
amicus sync          # takes a few minutes on first run (365d of email)
amicus stats         # verify contacts loaded
```

## Auspex Integration

`amicus dossier --today` is called at step 10b of `/auspex`. Outputs plain text (no ANSI) when non-TTY — safe to pipe into briefing narrative.

## Gotchas

- **GOG_KEYRING_PASSWORD** — set automatically from Keychain at import time in sync.rs. No manual setup needed. If sync fails with keyring error, unlock keychain in another tmux tab: `security unlock-keychain`.
- **`amicus sync` is idempotent** — safe to re-run; deduplicates by SHA-256 thread hash per email+interaction_type.
- **Filtered contacts** (`is_filtered=1`) are excluded from `amicus stale` but still in DB. Filter patterns: `noreply@`, `no-reply@`, `notifications@`, `billing@`, `support@`, `donotreply@`, `automated@`, `mailer@`, `bounce@`, or >10 recipients.
- **Timestamps** stored as UTC ISO-8601, displayed as HKT (Asia/Hong_Kong) in dossier.
- **gog People API 403** — if Google People API not enabled, `amicus sync` skips contacts gracefully and continues with Gmail + Calendar. Not an error.
- **gog gmail JSON wraps results in `{"threads": [...]}` not a plain array** — handled internally; sync still works.
- **Re-install after code changes**: `cargo install --path ~/code/amicus` (NOT `cargo build --release` — that doesn't update `~/.cargo/bin/amicus`).
- **DB at `~/.crm/crm.db`** — same path as the old Python `crm` tool. Existing data from Python migration is preserved.
- **TTY detection** — `dossier` command auto-detects TTY: rich table in terminal, plain text for agent pipes. Use `2>/dev/null` in auspex to suppress errors without breaking output.

## LinkedIn Import

LinkedIn DMs are the primary channel for professional contacts — `amicus sync` alone won't capture those relationships. Bridge the gap with LinkedIn's official data export (zero scraping, no account risk):

1. LinkedIn → Settings → Data Privacy → Get a copy of your data → select **Connections** + **Messages**
2. Wait ~24h for the download email
3. Unzip, then: `amicus import ~/Downloads/linkedin-export/`

Run **monthly**. Imports:
- `Connections.csv` — seeds contacts with name, company, role, connected date
- `messages.csv` — updates `last_contact` from message timestamps (matched by name)

## Weekly Use

- `amicus stale` every Friday during `/weekly` — who to ping before the week closes
- `amicus dossier --today` fires automatically in `/auspex` when meetings exist

## Rebuild / Reinstall

```bash
cd ~/code/amicus
cargo install --path .
```

## Crate Stack

- `clap` 4 (derive) — CLI parsing
- `rusqlite` 0.32 (bundled) — SQLite with FTS5, no system lib dependency
- `serde` / `serde_json` — gog JSON parsing
- `anyhow` — error handling
- `chrono` — timestamp parsing + UTC→HKT display
- `comfy-table` — rich terminal tables
- `sha2` + `hex` — thread ID deduplication hashes
