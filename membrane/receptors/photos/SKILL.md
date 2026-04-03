---
name: photos
description: Access iCloud Photos from Claude Code sessions. Reference skill — not user-invocable.
user_invocable: true
disable-model-invocation: true
---

# Photos

Access iCloud Photos from Claude Code sessions. Reference skill — not user-invocable.

## When to Use

- User asks to check recent photos, today's photos, or photos from a date
- User wants to view/assess a photo (selfie, screenshot, product shot)
- User says "check my photos", "did the photo sync", "export that photo"

## Method Selection

| Method | When | Pros | Cons |
|--------|------|------|------|
| **osascript** (primary) | Always try first | Works regardless of FDA/TCC | Slower (~2-5s), needs Photos.app process |
| **photos.py** (fallback) | If osascript fails | Fast (<0.1s), rich filtering | Requires Full Disk Access on parent process |

**Default to osascript.** The `photos.py` SQLite approach breaks when TCC/FDA grants reset (macOS updates, new SSH sessions). osascript works reliably because it talks to Photos.app via Apple Events, not the raw database.

## osascript Workflow (Primary)

### 1. List recent photos

```bash
osascript -e '
tell application "Photos"
    set allItems to media items
    set itemCount to count of allItems
    set startIdx to itemCount - 9
    if startIdx < 1 then set startIdx to 1
    set output to ""
    repeat with i from startIdx to itemCount
        set p to item i of allItems
        set output to output & id of p & " | " & (date of p as text) & " | " & filename of p & linefeed
    end repeat
    return output
end tell
'
```

Adjust `-9` to control how many (e.g. `-4` for last 5).

### 2. Export by ID

```bash
mkdir -p ~/tmp/photos
osascript -e '
tell application "Photos"
    set ids to {"FULL-UUID/L0/001", "ANOTHER-UUID/L0/001"}
    set exportFolder to POSIX file "/Users/terry/tmp/photos" as alias
    set toExport to {}
    repeat with pid in ids
        set end of toExport to media item id pid
    end repeat
    export toExport to exportFolder with using originals
end tell
'
```

Replace the UUID strings with IDs from step 1. Exports as JPEG to `~/tmp/photos/`.

### 3. View

```bash
# Use Read tool on the exported file
Read ~/tmp/photos/IMG_XXXX.jpeg
```

## photos.py (Fallback)

Only use if osascript fails (rare). Requires FDA on the parent process (`sshd` for Blink, `Ghostty.app` for local terminal).

```bash
python3 ~/scripts/photos.py <command>
```

| Command | Example | Notes |
|---------|---------|-------|
| `today` | `photos.py today` | Today's photos |
| `recent [N]` | `photos.py recent 5` | Last N photos (default 10, last 7 days) |
| `date YYYY-MM-DD` | `photos.py date 2026-02-20` | Specific date |
| `range FROM TO` | `photos.py range 2026-02-18 2026-02-20` | Date range |
| `export UUID [...]` | `photos.py export E6F41232` | Export to `~/tmp/photos/` as JPEG |
| `search KEYWORD` | `photos.py search "Terry"` | Search descriptions, titles, people |

## Gotchas

- **iCloud sync lag:** iPhone photo may take 30-60s to appear on Mac. If missing, run `open -a Photos` to nudge sync, wait, recheck.
- **`photos.py` "unable to open database":** TCC/FDA issue. Switch to osascript method. Don't debug FDA mid-task.
- **osascript is slow on large libraries:** Listing all items iterates the full library. Keep the slice small (last 5-10).
- **osascript export `with using originals`:** Exports HEIC. If you need JPEG, drop the `with using originals` flag, or convert after: `sips -s format jpeg INPUT.heic --out OUTPUT.jpeg`
- **`[iCloud]` photos:** Not downloaded locally. osascript export may fail or return low-res derivative. Download in Photos.app first.
- **Photos.app must be running** for osascript (it launches automatically but first call may be slow).

## Direct sips bypass

If you have the file path (from photos.py or manual browse):

```bash
sips -s format jpeg -s formatOptions 92 "<Photos Library>/originals/{UUID_PREFIX}/{FULL_UUID}.heic" --out ~/tmp/photos/output.jpeg
```

## Architecture

- **osascript:** Apple Events → Photos.app process → no FDA needed
- **photos.py:** Direct SQLite on `~/Pictures/Photos Library.photoslibrary/database/Photos.sqlite` — Core Data epoch (2001-01-01), ZASSET table, read-only mode. Needs FDA.
