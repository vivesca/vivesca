---
name: sopor
effort: low
description: >-
  Unified sleep health CLI — Oura Ring + EightSleep data in one DuckDB.
  Use when checking sleep data, running sync, asking "how did I sleep",
  or any sleep/readiness/HRV/activity query. Replaces oura, nyx, somnus.
  NOT for Oura hardware questions or EightSleep mattress settings.
user_invocable: false
triggers:
  - "how did I sleep"
  - "sleep data"
  - "sleep score"
  - "readiness"
  - "sopor"
  - "oura"
  - "eightsleep"
---

# sopor — Unified Sleep CLI

Oura Ring (primary biometrics) + EightSleep (supplementary, noisy due to bed-sharing) in one DuckDB at `~/.local/share/sopor/sopor.duckdb`.

## Commands

```bash
sopor sync [--days N]      # Sync both APIs (default 30 days)
sopor today [date]         # Last night combined view
sopor scores               # Quick one-liner: Sleep / Readiness / Activity
sopor week                 # 7-day vs 4-week average table
sopor trend [N]            # N-day ASCII charts + regression (default 30)
sopor event <date> <label> # Before/after comparison
sopor monthly [YYYY-MM]    # Monthly summary + vault report
sopor hypnogram [date]     # Sleep stage visualization
sopor readiness [date]     # Readiness + contributors
sopor activity [date]      # Steps, calories, movement
sopor hrv [date]           # HRV from sleep
sopor stress [date]        # Daily stress
sopor why [date]           # LLM analysis via claude --print (free on Max20)
sopor json <endpoint> [date]  # Raw Oura API JSON
sopor migrate [--verify]   # One-time import from old DBs
```

## Credentials

- **Oura:** `OURA_TOKEN` env var (in `~/.zshenv.local`)
- **EightSleep:** 1Password via `op item get "Eight Sleep" --vault Agents`. Fallback: `EIGHTSLEEP_EMAIL` + `EIGHTSLEEP_PASSWORD` env vars. If `op` fails (LaunchAgent), EightSleep sync skips gracefully.

## Data Priority

- HR, HRV, sleep stages, duration → Oura (body-worn, individual)
- Bed temperature → EightSleep (only source)
- `bedtime_start` stored as local HKT (no UTC conversion)

## Gotchas

- EightSleep can have multiple sessions per night (PK is `session_id`, not date)
- `nightly_sleep` is the single analysis target for all Oura display commands
- `sopor why` writes context to `~/tmp/sopor-why-context.txt` (not `/tmp/`)
- LaunchAgent: `com.terry.sopor-sync` daily 08:00 HKT (pending setup)

## Repo

`~/code/sopor/` — Python, uv. GitHub: `terry-li-hm/sopor` (private).
