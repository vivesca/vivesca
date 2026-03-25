# Due App .duedb Gotchas

## Format
- Gzipped JSON at `~/Library/Containers/com.phocusllp.duemac/Data/Library/Application Support/Due App/Due.duedb`
- Backup: `Baseline.duedb` in the same dir — restore to recover from corruption
- moneo auto-snapshots to `~/officina/backups/due-reminders.json` (git-tracked) after every write

## Schema (reminders array `re`)
- `n`: title, `d`: due ts, `b`: created, `m`: modified, `si`: snooze seconds (300=5min), `u`: UUID
- UUID = **base64 WITHOUT padding** (22 chars). With `==` padding → Due crashes on load with SIGABRT
- `rf`: recurrence flag (`d`=daily, `w`=weekly, `m`=monthly, `y`=yearly), `rd`: recurrence start ts
- `dl`: dict of deleted UUIDs → timestamp (deletion tombstones for CloudKit sync)

## Why Due (not Reminders.app)
- Due's killer feature: **repeating nag until dismissed + 10-min snooze loop**
- Reminders.app fires once only — no repeat nag, no snooze
- This is non-negotiable for medication and time-critical reminders
- The DB hack complexity is the price for this feature

## Sync Architecture
- Due uses **CloudKit**, not iCloud Drive
- **`add`**: URL scheme (`due://x-callback-url/add?...`) → Due opens editor → AppleScript clicks Save → CloudKit syncs to iPhone ✓
- **`edit`**: tombstones old entry + re-adds via AppleScript URL scheme → CloudKit syncs to iPhone ✓ (same path as `add`)
- **`rm`**: direct DB write + `open -a Due` — CloudKit *may* sync deletions via `dl` tombstones; unconfirmed. If not, delete on iPhone manually.
- Direct file edits alone (without opening Due) do NOT sync to iPhone

## Why No AppleScript for rm/edit
- Due is a **Catalyst app** — no AppleScript dictionary (`sdef` returns empty)
- `System Events` UI automation fails: no traditional window hierarchy, `entire contents of window 1` → invalid index
- URL scheme only supports `add` — no delete or edit actions
- DB write is the only programmatic option

## URL Scheme (`add` only)
- `due://x-callback-url/add?title=...&duedate=<unix_ts>`
- Recurrence: `&recurunit=<n>&recurfreq=1&recurfromdate=<ts>` (16=daily, 256=weekly, 8=monthly, 4=yearly)
- Weekly needs `&recurbyday=<n>` (Mon=2 … Sun=1)
- AppleScript clicks Save after 3s open delay, retries 20× at 0.5s intervals

## Quitting Due programmatically
- `osascript tell app "Due" to quit` → error (menu bar app, ignores it)
- `System Events quit process "Due"` → silently fails (process stays alive)
- `kill -15 <pid>` → works. Wait for process to exit before writing file.

## CLI: moneo (`~/bin/moneo`)
- `add` → AppleScript URL scheme path (syncs to iPhone)
- `rm` → DB write + open Due (iPhone sync unconfirmed — test and update this doc)
- `edit` → tombstone + re-add via AppleScript (syncs to iPhone ✓, same path as `add`)
- `rm --title "pattern"` → safe batch delete by name substring; avoids index-shift bug
- Duplicate guard: same title + same date + same HH:MM is rejected; same title + same date + different time is allowed
- git snapshot fires after every write → `~/officina/backups/due-reminders.json`

## Index-Shift Fix (2026-03-10)
- Index deletion removed entirely from moneo — `rm` now requires `--title <pattern>`, no positional index arg
- Previously: passing a string as positional index threw a parse error *before* `--title` was checked — made the feature undiscoverable
- `moneo rm --title "pinky"` deletes all reminders whose title contains "pinky" (case-insensitive substring match)

## Testing moneo (importlib gotcha)
- `moneo` has no `.py` extension — `importlib.util.spec_from_file_location()` returns `None`
- Use `SourceFileLoader` explicitly:
  ```python
  from importlib.machinery import SourceFileLoader
  import importlib.util
  loader = SourceFileLoader("moneo", str(Path.home() / "bin/moneo"))
  spec = importlib.util.spec_from_loader("moneo", loader)
  mod = importlib.util.module_from_spec(spec)
  loader.exec_module(mod)
  ```
- Tests live in `~/officina/tests/test_moneo.py`

## Binary Staging: com.apple.provenance SIGKILL (ERR-20260312-001)
- Binaries built in `/tmp/` and copied to `~/officina/bin/` acquire a `com.apple.provenance` extended attribute
- macOS kernel kills git (SIGKILL, rc=-9) when it tries to stage such binaries via `git add`
- xattr -d cannot remove `com.apple.provenance` — it's kernel-enforced
- Fix: add compiled binaries to `.gitignore`. Source code lives in `~/code/<project>`, binaries live in `~/bin/` but are not tracked in officina.
- Affects: any binary cp'd from /tmp/. Safe path: build directly in `~/code/` (but workspace issue currently blocks this for moneo).
