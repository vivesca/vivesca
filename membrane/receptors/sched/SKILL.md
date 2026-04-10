---
name: sched
effort: low
description: >-
  Schedule events and manage Due reminders via cyclin CLI. Use for ANY Due or calendar
  operation: "schedule", "remind me", "add to Due", "remind me in X", "book X",
  "list/edit/delete reminders". Covers both one-off and recurring. Entry point for all
  scheduling — replaces the separate 'due' skill.
user_invocable: true
---

# /sched — Schedule + Remind

Single entry point for all scheduling. Due = nag reminders. Google Calendar = source of truth for time-blocked events.

**Default behaviour by type:**

| Type | Due | Google Calendar |
|------|-----|----------------|
| Appointment / meeting | ✅ 30 min before | ✅ |
| Recurring meeting | ✅ 5 min before | ✅ (if not already there) |
| Task / nudge / habit / follow-up | ✅ | ❌ |

## cyclin CLI Reference

`cyclin add` always syncs to iPhone via CloudKit.

```bash
cyclin ls                                                        # list all reminders with index
cyclin add "Call dentist" --in 30m                              # relative time
cyclin add "Standup" --at 09:30                                 # today at HH:MM
cyclin add "Pay rent" --date 2026-04-01 --at 10:00             # specific date + time
cyclin add "Team sync" --at 11:00 --recur weekly               # recurring weekly
cyclin add "Pay rent" --date 2026-04-01 --recur monthly        # recurring monthly
cyclin edit <index> --title "New title"                         # rename (Mac only)
cyclin edit <index> --at 16:00                                  # change time (Due opens to sync)
cyclin edit <index> --in 1h                                    # push forward (Due opens to sync)
cyclin add "Medicine" --at 09:00 --every 6h --until 2026-03-20  # interval expansion (skips overnight)
cyclin add "Standup" --at 09:30 --autosnooze 5                 # auto-snooze after 5 min
cyclin rm "pattern"                                             # delete all matching by title (case-insensitive)
cyclin search "medicine"                                        # launch Due and search
cyclin search "rent" --section Logbook                          # search in specific section
cyclin log                                                       # show last 20 completions (from Due's lb table)
cyclin log --n 50                                               # show more
cyclin log --filter "medicine"                                  # filter by title substring
cyclin snapshot                                                  # manual git snapshot of current DB state
```

### Time flags (mutually exclusive)

| Flag | Example | Meaning |
|---|---|---|
| `--in` | `--in 30m` | Relative: `s`, `m`, or `h` |
| `--at` | `--at 14:35` | Today at HH:MM (HKT) |
| `--date` + `--at` | `--date 2026-04-01 --at 09:00` | Specific date + time |
| `--date` only | `--date 2026-04-01` | That date at 09:00 |

`--recur daily|weekly|monthly|quarterly|yearly` — first occurrence = the date/time you specify. Quarterly = every 3 months.

`--every <interval>` + `--until <date>` — expands to individual reminders. Intervals: `Nh` (hours), `Nm` (minutes), `And` (days). Skips 23:00–07:00 by default. Use `--no-skip-night` to include overnight. Requires `--until`.

`--autosnooze <minutes>` — Due 3.2+. Valid: 1, 5, 10, 15, 30, 60.

## Adding to Google Calendar

For appointments and meetings:

```bash
gog calendar add primary \
  --summary "Event title" \
  --from "2026-03-10T10:00:00+08:00" \
  --to "2026-03-10T11:00:00+08:00" \
  --location "Optional location" \
  --description "Optional notes"
```

- Default calendar: `primary` (terry.li.hm@gmail.com)
- Family events: `family16675940229854502575@group.calendar.google.com`
- Times must be RFC3339 with `+08:00` offset (HKT)
- **Never add `--attendees`** — triggers email notifications
- Default duration: 1h if end time not given

## Steps for Appointments

1. Collect: title, date + time, end time (default +1h), location (optional)
2. `cyclin add` with reminder 30 min before (or 5 min before for recurring meetings)
3. `gog calendar add` for the event itself
4. Confirm both to user

## Example

> "Schedule AIA call tomorrow 10am, Tommy Lau +852 3727 6441"

```bash
cyclin add "AIA call - Tommy Lau" --date 2026-03-06 --at 09:30
gog calendar add primary --summary "AIA call - Tommy Lau" --from "2026-03-06T10:00:00+08:00" --to "2026-03-06T11:00:00+08:00" --description "Tommy Lau +852 3727 6441"
```

## Gotchas

- **cyclin is now a Python script** (`~/bin/cyclin` → `~/code/cyclin-py/cyclin.py`, `uv run --script`, zero deps). Repo: `terry-li-hm/cyclin` (private). Rust version archived at `~/code/cyclin/`.
- `cyclin add` uses AppleScript to open Due editor via URL scheme and auto-click Save → CloudKit sync to iPhone. Works screen-free.
- **LaunchAgent `com.terry.due-snapshot`** auto-runs `cyclin snapshot` every 5 min — git-commits DB state to `~/officina/backups/due-reminders.json` only when changed. Requires Full Disk Access granted to `~/bin/cyclin` in System Settings → Privacy & Security.
- `cyclin log` reads Due's `lb` table — includes both Mac and iPhone completions/dismissals. iPhone entries appear after CloudKit sync (typically <5 min). Note: `lb` records dismissals, not just true completions — no distinction available from DB.
- **`cyclin edit --at <time>` resets the date to today**, even if the reminder was set for a future date. To change only the time on a future reminder, always use `--date YYYY-MM-DD --at HH:MM` together.
- `cyclin rm` does not sync deletions to iPhone — delete in Due on iPhone directly
- `cyclin rm "<pattern>"` — batch delete by title pattern (case-insensitive). No `--title` flag — pattern is a positional arg.
- Same title at different times on the same day is allowed. Same title at the same time on the same day is rejected.
- Due uses CloudKit (not iCloud Drive). Direct file edits bypass CloudKit — always use `cyclin add`.
- UUID gotcha: Due requires base64 UUIDs without `=` padding — cyclin handles this automatically
- Always use HKT. cyclin handles timezone internally.
- `cyclin ls` shows ⚠ for overdue reminders
