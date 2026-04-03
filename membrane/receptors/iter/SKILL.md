---
name: iter
description: "HK bus stop navigator — tracks stops on unfamiliar routes with alerts. Also does Google Maps transit directions. NOT for MTR-only (use poros)."
---

# iter — HK Bus Stop Navigator

## Commands

```bash
# Navigate a journey (main use case)
iter <route> <from_stop> <to_stop>
iter 1 "Prince Edward" "Star Ferry"
iter 74X "Sai Kung" "Diamond Hill"

# GPS-based auto-tracking (no button presses)
iter 671 "Ngau Tau Kok" --inbound --watch          # auto-detects boarding stop from GPS
iter 671 "Victoria Park" "Ngau Tau Kok" --inbound --watch  # explicit boarding stop

# Adjust alert threshold (default: 2 stops out)
iter 1 "Mong Kok" "Jordan" --alert 3

# Browse all stops on a route first (then pick your stops)
iter 1 --list
iter 1 --list --inbound

# Force operator if auto-detect picks wrong one
iter 8 "Heng Fa Chuen" "Central" --operator ctb

# Get Google Maps transit directions (bus + MTR)
iter route "Pok Fu Lam Fire Station" "Grand Promenade Sai Wan Ho"
iter route "Central" "Diamond Hill"
```

## How it works

**Interactive mode** (default):
1. Fetches stop sequence from HK open data APIs (no auth required)
2. Fuzzy-matches your stop names (substring match first, then Jaro-Winkler fallback)
3. Shows the ordered stop list with boarding and exit highlighted
4. Press **Enter** each time you pass a stop
5. Sends a **Telegram push notification** at `--alert N` stops before destination
6. Prints "NEXT STOP IS YOURS" at 1 remaining; "GET OFF NOW" at 0

**Watch mode** (`--watch`):
1. Reads GPS from `~/.local/share/location/current.json` every 5 seconds
2. Finds nearest stop via haversine distance
3. Auto-detects boarding stop from GPS if not specified
4. Sends Telegram alert at `--alert N` stops remaining (default: 2)
5. Prints "GET OFF NOW" and sends final alert at destination (<200m)
6. Warns if location data is >10 min stale

**Requires:** OwnTracks iOS app posting to location receiver on `:8924` via Tailscale.

`iter route` calls Google Maps Routes API and shows each transit leg with route number, stop names, and total time.

## Location System

| Component | What | Where |
|-----------|------|-------|
| OwnTracks (iPhone) | GPS source | App Store, HTTP mode → `http://100.94.27.93:8924` |
| Location receiver | HTTP → JSON file | `~/code/iter/location-receiver.py`, LaunchAgent `com.terry.location-receiver` |
| Location file | Current lat/lng | `~/.local/share/location/current.json` |
| Tailscale | Phone → iMac transport | iPhone `100.72.110.20` → iMac `100.94.27.93` |

Receiver accepts both OwnTracks JSON and Overland GeoJSON batch formats.

## Operators

| Flag | Operator | Routes |
|------|----------|--------|
| auto | KMB first, CTB fallback | most routes |
| `--operator kmb` | KMB/LWB | Kowloon + NT |
| `--operator ctb` | CTB/NWFB | HK Island + cross-harbour |

GMB (green minibus) not supported — different API.

## Environment variables

| Var | Purpose | Source |
|-----|---------|--------|
| `TELEGRAM_BOT_TOKEN` | Telegram alerts | 1Password Agents vault |
| `GOOGLE_MAPS_API_KEY` | `iter route` subcommand | 1Password Agents vault (`iter-routes-gmaps-key`), GCP project `iter-hk-bus` |

Both injected automatically via `~/.zshenv.tpl` at login.

## Gotchas

- **Route not found**: try `--inbound` (some routes only run one direction, or the stops are listed in reverse)
- **Wrong stops shown**: use `--list` first to see exact stop names, then copy-paste
- **Telegram alert missing**: check `TELEGRAM_BOT_TOKEN` env var is set (injected via 1Password at login)
- **Stop name matches wrong stop**: substring matches now beat fuzzy score, but if still wrong use a more specific substring (e.g., "Star Ferry Harbour" instead of just "Star Ferry")
- **--watch shows stale location**: open OwnTracks and tap upload (↑) to force a publish
- **Location receiver not running**: `launchctl list | grep location-receiver` — if missing, `launchctl load ~/Library/LaunchAgents/com.terry.location-receiver.plist`
- **N+1 API calls**: ~25 HTTP calls to fetch stop names on first run — takes 5–10 seconds. Normal.
- **Binary in `~/bin/iter`**: Rust binary, not a Python script. Copy from `~/code/target/release/iter` after rebuild.
- **KMB API base URL**: `data.etabus.gov.hk/v1/transport/kmb/` (NOT `rt.data.gov.hk/v2/transport/kmb/` — that's CTB only)
- **Workspace build**: `cargo build --release` runs from `~/code/` workspace, so binary lands in `~/code/target/release/iter` (not `~/code/iter/target/`)
- **Google Maps project**: API key belongs to `iter-hk-bus` (project number `5375087751`). Routes API enabled there. Use gcloud to manage.

## Files

- Source: `~/code/iter/src/main.rs`
- Binary: `~/bin/iter` (copied from `~/code/target/release/iter`)
- Receiver: `~/code/iter/location-receiver.py`
- LaunchAgent: `~/Library/LaunchAgents/com.terry.location-receiver.plist` (source: `~/code/iter/`)
- Location data: `~/.local/share/location/current.json`
- Receiver log: `~/.local/share/location/receiver.log`
- Repo: `https://github.com/terry-li-hm/iter`
- APIs: `data.etabus.gov.hk` (KMB) · `rt.data.gov.hk` (CTB) · `routes.googleapis.com` (Google Maps)

## Related

- `poros` — MTR journey time CLI (sister tool)
