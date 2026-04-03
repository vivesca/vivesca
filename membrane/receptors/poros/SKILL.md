---
name: poros
description: Query MTR (Hong Kong subway) point-to-point journey times. Use when asked how long the MTR takes between any two stations.
user_invocable: false
---

# poros — MTR Journey Time CLI

Queries MTR point-to-point journey times from a local cache. Source: piliapp.com (101 stations).

## Commands

```bash
poros "Wu Kai Sha" "Kwun Tong"   # → 39 min
                                  #    Route: Wu Kai Sha → [Tuen Ma] → Diamond Hill → [Kwun Tong] → Kwun Tong
poros kwun "wu kai"               # fuzzy, case-insensitive
poros --refresh                   # re-scrape piliapp (~5 min, 101 stations)
poros --matrix                    # dump full N×N TSV table
```

## Cache
- Location: `~/.local/share/poros/cache.json`
- Built by `--refresh` or auto-triggered on first query
- Scrape takes ~5 min (101 stations × agent-browser click + eval)

## Gotchas
- Binary at workspace root: `~/code/target/release/poros` (not `~/code/poros/target/`)
- Scraping shells out to `agent-browser` — must be in PATH
- piliapp.com station IDs: `t1`–`t120` (not all contiguous, gaps skipped)
- Journey Time mode must be selected before scraping (first option in dropdown)
- MTR blocks agent-browser directly — piliapp.com is the workaround

## Source
- Repo: `~/code/poros/`
- Install: `cp ~/code/target/release/poros ~/bin/poros`
