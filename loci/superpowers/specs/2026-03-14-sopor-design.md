# Sopor — Unified Sleep Health CLI

**Date:** 2026-03-14
**Status:** Design
**Replaces:** oura-cli (Rust), somnus (Rust), nyx (Rust)
**Language:** Python (uv script or package)
**Name:** sopor (Latin, "deep sleep") — PyPI available

## Purpose

Single CLI for all sleep data: sync from Oura Ring + EightSleep, store in one DuckDB, analyse trends, and get LLM-powered insights. Oura is primary (body-worn, reliable biometrics); EightSleep is supplementary (noisy due to bed-sharing with Theo in the middle).

## Architecture

```
Oura API ──┐
           ├──▶ sopor sync ──▶ DuckDB (~/.local/share/sopor/sopor.duckdb)
8Sleep API ┘                          │
                                      ▼
                              sopor today/week/trend/why/...
                                      │
                              claude --print (for `why`)
```

### Credentials

- **Oura:** `OURA_TOKEN` env var (already set in `~/.zshenv.local`), fallback to keychain `oura-token`
- **EightSleep:** 1Password via `op item get "Eight Sleep" --vault Agents` at runtime, fallback to `EIGHTSLEEP_EMAIL` + `EIGHTSLEEP_PASSWORD` env vars. If `op` fails (LaunchAgent context, no session), skip EightSleep sync and log a warning — don't abort the entire sync.
- **EightSleep OAuth app credentials:** `CLIENT_ID` and `CLIENT_SECRET` are hardcoded constants in `eightsleep.py` (these are the app's OAuth credentials, not user credentials — same as in the Rust source)

### Database

Single DuckDB at `~/.local/share/sopor/sopor.duckdb`. Schema mirrors the existing Oura tables (proven, rich) plus an `eightsleep_sessions` table for EightSleep data.

**Oura tables to port** (from `~/oura-data/data/oura.duckdb`):
- `nightly_sleep` — the denormalised nightly view (primary query target)
- `daily_sleep`, `readiness`, `sleep` — raw API data
- `daily_activity`, `daily_stress` — activity/stress
- `heartrate` — HR timeseries
- `daily_spo2`, `daily_cardiovascular_age`, `vo2_max` — health metrics
- `sleep_time` — optimal bedtime recommendations
- `enhanced_tag`, `tag` — user tags
- `workout`, `session` — exercise/meditation
- `resilience`, `rest_mode_period` — recovery
- `sync_log` — sync tracking

**EightSleep table** (`eightsleep_sessions`):
- `session_id TEXT PRIMARY KEY` (EightSleep interval ID — dedup key; multiple sessions per night possible)
- `date DATE NOT NULL` (indexed, computed from timestamp)
- `duration_secs INTEGER`
- `deep_pct DOUBLE`, `light_pct DOUBLE`, `rem_pct DOUBLE`, `awake_pct DOUBLE`
- `hrv_avg DOUBLE`, `hr_avg DOUBLE`, `rr_avg DOUBLE`
- `bed_temp_avg DOUBLE` (from `timeseries.tempBedC`; NULL for migrated historical rows)
- `sleep_score INTEGER`
- `synced_at TIMESTAMP`

**Query target:** `nightly_sleep` is the single analysis target for all Oura-based display commands. Raw tables (`sleep`, `readiness`, `daily_activity`, etc.) are kept as staging tables written by sync. `nightly_sleep` is computed/upserted from them during sync. `daily_activity` is queried directly only by `monthly` (for active-days count) and `activity`.

### Data priority

When displaying metrics available from both sources:
- **HR, HRV, sleep stages, duration:** Use Oura (body-worn, individual)
- **Bed temperature, mattress settings:** Use EightSleep (only source)
- **Duration cross-check:** Show EightSleep duration as supplementary when it diverges >30min from Oura

## Commands

### `sopor sync [--days N]`
Sync both APIs. Default 30 days. Upserts into DuckDB.
- Oura: hits all endpoints (sleep, readiness, activity, stress, HR, etc.)
- EightSleep: auth via `op`, fetch intervals, upsert to `eightsleep_sessions`
- Prints summary: "Synced N Oura days + M EightSleep sessions"

### `sopor today [date]`
Last night's combined view. Default: most recent night.
```
Last night: 2026-03-13
  Sleep Score:  83        Readiness: 81
  Duration:     7h 12m    Efficiency: 93%
  Deep:         1h 30m (21%)
  REM:          1h 25m (20%)
  Light:        3h 17m (46%)
  Awake:        1h 00m (14%)
  HRV:          42 ms     HR: 51 bpm
  Bedtime:      23:45 → 06:57
  Temperature:  +0.2°C
  ── EightSleep ──
  Duration:     7h 35m    (vs Oura: +23m)
  Bed Temp:     27.2°C
```

### `sopor scores`
Quick one-liner: `Sleep 83  Readiness 81  Activity 72`
With readiness contributors beneath.

### `sopor week`
7-day table with key metrics. Matches current `nyx` default view format (This Week vs 4W Avg with delta).

### `sopor trend [N]`
N-day trend (default 30). ASCII charts for readiness and bedtime. Linear regression slope. Ported from nyx `trend`.

### `sopor event <date> <label>`
7-day before vs after comparison. Ported from nyx `event`.

### `sopor monthly [YYYY-MM]`
Monthly summary + saves report to `~/notes/Sleep/YYYY-MM-sopor.md`. Ported from nyx `monthly`.

### `sopor hypnogram [date]`
Sleep stage visualization (5-min intervals from `sleep_phase_5_min`). Ported from oura-cli `hypnogram`.

### `sopor readiness [date]`
Readiness score + contributors breakdown. Ported from oura-cli `readiness`.

### `sopor activity [date]`
Activity summary (steps, calories, movement). Ported from oura-cli `activity`.

### `sopor hrv [date]`
HRV from sleep. Ported from oura-cli `hrv`.

### `sopor stress [date]`
Daily stress summary. Ported from oura-cli `stress`.

### `sopor why [date]`
**New.** LLM-powered sleep analysis.

1. Queries DuckDB for: last night's data, 7-day history, 30-day averages
2. Writes structured context to `~/tmp/sopor-why-context.txt` (not `/tmp/` — cleaned aggressively)
3. Runs `env -u CLAUDECODE claude --print "$(cat ~/tmp/sopor-why-context.txt)"` — avoids shell interpolation issues with multi-line data
4. Prints the response

### `sopor json <endpoint> [date]`
Raw JSON from Oura API for piping/debugging. Ported from oura-cli `json`.

## Implementation

### Package structure

```
~/code/sopor/
├── pyproject.toml          # uv project, CLI entry point
├── src/
│   └── sopor/
│       ├── __init__.py
│       ├── cli.py          # Click/Typer CLI definitions
│       ├── db.py           # DuckDB open, schema, upsert, queries
│       ├── oura.py         # Oura API client (port from oura-cli/client.rs)
│       ├── eightsleep.py   # EightSleep API client (port from somnus/auth.rs + api.rs)
│       ├── display.py      # Formatting, tables, ASCII charts, colors
│       └── commands/
│           ├── sync.py
│           ├── today.py
│           ├── scores.py
│           ├── week.py
│           ├── trend.py
│           ├── event.py
│           ├── monthly.py
│           ├── hypnogram.py
│           ├── readiness.py
│           ├── activity.py
│           ├── hrv.py
│           ├── stress.py
│           ├── why.py
│           └── json_cmd.py
├── tests/
│   ├── test_db.py
│   ├── test_oura.py
│   └── test_display.py
└── AGENTS.md
```

### Dependencies

- `click` — CLI framework
- `duckdb` — local database
- `httpx` — HTTP client, sync mode (`httpx.Client`, not async — no asyncio boilerplate needed for a personal CLI)
- `rich` — tables + colored output (replaces comfy-table + colored)
- `python-dateutil` — date parsing

### Data migration

`sopor migrate` — one-time command to populate the unified DB from existing sources.

**Procedure:**
1. **Backup first:** `cp ~/oura-data/data/oura.duckdb ~/oura-data/data/oura.duckdb.bak` (and same for somnus)
2. **ATTACH source DBs** and `INSERT INTO ... SELECT` for each table. Idempotent — safe to rerun (uses `ON CONFLICT ... DO UPDATE`).
3. **Verify:** `sopor migrate --verify` prints row counts per table (source vs destination) and exits without writing. Run after migration to confirm.
4. **EightSleep historical rows:** `bed_temp_avg` will be NULL (somnus didn't store it). Documented, not a data loss.

After migration verified, old DBs can be archived.

### Agent-readiness

- All commands work non-interactively (no prompts)
- Credentials from env vars or 1Password (`op` CLI)
- Structured output for piping (`sopor json`)
- Exit codes: 0 success, 1 error
- `--json` flag on key commands for machine-readable output (v2)

### LaunchAgent

`com.terry.sopor-sync` — daily sync at 08:00 HKT. Replaces existing Oura sync cron.

```xml
<key>ProgramArguments</key>
<array>
  <string>/Users/terry/.local/bin/uv</string>
  <string>run</string>
  <string>--project</string>
  <string>/Users/terry/code/sopor</string>
  <string>sopor</string>
  <string>sync</string>
</array>
```

## What gets retired

After sopor is verified working:
1. `~/bin/oura` binary → remove
2. `~/bin/nyx` binary → remove
3. `~/bin/somnus` binary → remove
4. `~/code/oura-cli/` → archive
5. `~/code/somnus/` → archive
6. `~/code/nyx/` → archive
7. `~/oura-data/scripts/sync.py` → replaced by `sopor sync`
8. LaunchAgent `com.terry.oura-sync` (if exists) → replaced
9. LaunchAgent `com.terry.nyx-monthly` → replaced
10. Skills: `oura`, `somnus`, `nyx` → replaced by single `sopor` skill

## Success criteria

- [ ] `sopor sync` fetches from both APIs and populates unified DB
- [ ] `sopor today` shows combined Oura + EightSleep view
- [ ] `sopor week` matches nyx default output quality
- [ ] `sopor trend` renders ASCII charts with regression
- [ ] `sopor why` returns useful LLM analysis
- [ ] `sopor monthly` saves report to vault
- [ ] All existing oura/nyx/somnus commands have equivalents
- [ ] Data migrated from old DBs
- [ ] LaunchAgent syncing daily
- [ ] Old tools retired
