# Obsidian OOM with Large Git-Tracked Vaults

## Problem

Obsidian shows white screen and "Paused before potential out of memory crash" when DevTools is open. Triggered by sync/git operations on vaults with large `.git` directories (1.2GB+ pack files).

## Root Cause

Electron's V8 heap can't handle git operations on large repos in-process. The OOM pause only fires when DevTools is open — without DevTools, Obsidian either recovers silently or crashes without the debugger banner.

## Fixes

1. **Don't open DevTools** — the OOM pause is a DevTools feature, not an app crash
2. **Disable obsidian-git plugin** if using external git backup (e.g. cron script) — removes the in-process git trigger entirely
3. **`git gc --aggressive --prune=now`** — consolidates loose objects but won't shrink if large blobs are still reachable in history
4. **Strip large blobs from history** (`git filter-repo`) or nuke `.git` and reinit — nuclear option for vaults with accumulated binary files

## Terry's Vault Stats (Feb 2026)

- Vault: 3.2GB total, 1.3GB `.git/`
- Largest blobs: 30MB headshot TIFs, ebooks, archive PNGs/GIFs, 8-11MB dedao course markdown files
- Cron backup (`vault-git-backup.sh` every 30 min) makes obsidian-git plugin redundant

## Also Tried (Didn't Help Alone)

- Clearing GPUCache / Cache / Code Cache — fixes rendering issues but not OOM
- `--disable-gpu` flag — fixes GPU rendering, doesn't address memory
- Disabling `hot-reload` plugin — it injects `debugger;` statements but wasn't the OOM cause
