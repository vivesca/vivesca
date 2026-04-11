---
name: horizo
description: Appointment scheduling workflow — coordinate time via WhatsApp (keryx) then book to Google Calendar (gog). Use when scheduling a meeting, haircut, lunch, or any appointment.
---

# horizo

Two-step scheduling workflow: agree a time via WhatsApp, lock it in the calendar.

## Workflow

### 1. Coordinate via WhatsApp
```bash
keryx send "Name" "你幾時得空？" --copy   # propose / ask availability
keryx read "Name"                          # check their reply
```

### 2. Confirm and book calendar
```bash
# Once time is agreed:
gog calendar add primary \
  --summary "Event title" \
  --from "2026-03-10T12:00:00+08:00" \
  --to   "2026-03-10T13:00:00+08:00"
```

### 3. Confirm back (optional)
```bash
keryx send "Name" "好，X點見！" --copy
```

## gog calendar add flags

| Flag | Example | Notes |
|------|---------|-------|
| `--summary` | `"Haircut - Herman"` | Event title |
| `--from` | `"2026-03-10T12:00:00+08:00"` | RFC3339, always +08:00 for HKT |
| `--to` | `"2026-03-10T13:00:00+08:00"` | RFC3339 |
| `--description` | `"CWB salon"` | Optional notes |
| `calendarId` | `primary` | Use `primary` for main calendar |

## Gotchas

- **Always use `+08:00`** not `Z` for HKT — `Z` creates UTC events (8h off).
- **keryx `--copy` requires non-tmux terminal** to land in system clipboard (known issue). Workaround: pipe to `tg-clip` or copy from terminal output manually.
- **gog calendar add** requires `calendarId` as positional arg before flags — `gog calendar add primary --summary ...`

## Future CLI (horizo)

Name reserved on crates.io. Could eventually wrap both steps into:
```bash
horizo schedule "Herman" "Haircut" --date 2026-03-10 --time 12:00 --duration 60
```
