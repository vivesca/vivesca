---
name: time
description: Check current time in Hong Kong. Use when user asks "what time is it", "time", or when you need to verify current time/date.
---

# Current Time

Show the current date and time in Hong Kong (HKT, UTC+8).

## Trigger

Use when:
- User asks "what time", "time", "what's the time"
- You need to verify current time/date before making time-sensitive statements

## Workflow

Run this command to get current HK time:

```bash
TZ='Asia/Hong_Kong' date '+%A, %B %d, %Y at %I:%M %p HKT'
```

## Output Example

```
Monday, January 19, 2026 at 01:20 PM HKT
```

## Notes

- Always use this skill rather than guessing or relying on context
- Hong Kong does not observe daylight saving time
- Useful before scheduling calls, checking deadlines, or making time-based recommendations
