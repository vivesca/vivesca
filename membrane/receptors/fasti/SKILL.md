---
name: fasti
description: Google Calendar CLI wrapper — list, move, create, delete events via fasti instead of raw gog commands
triggers: ["fasti", "calendar list", "reschedule event", "move calendar event", "delete calendar event", "create calendar event", "schedule"]
---
# fasti — Google Calendar CLI

Thin Rust wrapper over `gog` for token-efficient calendar ops. Hardcoded to primary calendar (`terry.li.hm@gmail.com`). Use instead of raw `gog calendar` commands.

## Commands

```bash
# List events (defaults to today)
fasti list
fasti list tomorrow
fasti list 2026-03-10

# Create an event
fasti create "Event title" --date today --from 10:00 --to 11:00
fasti create "Meeting" --date 2026-03-12 --from 14:00 --to 15:00 --description "Optional notes"
fasti create "Interview" --date 2026-03-16 --from 15:30 --to 16:30 --location "8/F MTR HQ, KLB"

# Move an event (preserves duration)
fasti move <event-id> today 14:00
fasti move <event-id> tomorrow 09:30
fasti move <event-id> 2026-03-10 11:00

# Delete an event (no confirmation)
fasti delete <event-id>
```

## Schedule view — always check both calendar AND Due

When discussing or checking schedule, always run both:
```bash
fasti list [date]   # Google Calendar events
moneo ls            # Due app reminders
```
Due reminders (one-off and recurring) are not visible in fasti. Both together give the full picture.

## Creating events with attendees (use gog directly)

`fasti create` doesn't support attendees — use gog for those:

```bash
gog calendar create primary \
  --summary "Meeting" \
  --from "2026-03-12T10:00:00+08:00" \
  --to   "2026-03-12T11:00:00+08:00" \
  --attendees "cherry.ma@aia.com"
```

Time format: RFC3339 with HKT offset (`+08:00`). Calendar ID is always `primary`.

## Event IDs

`fasti list` shows 8-char prefix IDs. `move` and `delete` accept either the prefix or the full ID.

## Gotchas

- Gemini tested against live calendar during build — it will actually execute moves/deletes. Don't use as a dry-run tool.
- `fasti list` shows today by default; no flag needed.
- Duration is always preserved on `move` — it queries the event first, computes delta, applies to new start.
- Raw `gog` flags: `--from`/`--to` (not `--start`/`--end`), calendar ID required as positional arg before event ID.

## When to use

Prefer `fasti` over raw `gog calendar` for all list/move/delete ops — saves token roundtrips from flag/ID discovery.

## Source

`~/code/fasti/src/main.rs`
