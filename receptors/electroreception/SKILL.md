---
name: electroreception
description: Use when reading iPhone messages (iMessage/SMS) from local macOS database. "check messages", "read iMessage", "iPhone messages", "SMS"
user_invocable: false
---

# electroreception -- read iPhone messages from macOS

CLI: `electroreception` (on PATH at `~/.local/bin/electroreception`).

## Usage

```bash
electroreception                    # last 20 messages
electroreception -n 50              # last 50
electroreception -s MoxBank         # filter by sender (substring)
electroreception -d 3               # last 3 days
electroreception -q "Bowtie"        # search text content
electroreception --incoming         # incoming only
electroreception --json             # JSON output for piping
```

Flags combine: `electroreception --incoming -s BOCHK -d 7 -n 10`

## When to use Python instead

The CLI covers most cases. Drop to Python only when you need:
- Custom SQL joins (e.g. group chat names via `chat_message_join` + `chat`)
- Aggregation or analysis across the full database
- Integration with other tools mid-script

If you do, use the extraction function from the CLI source (`~/.local/bin/electroreception`).

## Key Gotchas

| Gotcha | Detail |
|--------|--------|
| **`text` is NULL** | Recent macOS stores text in `attributedBody` blob, not `text` column. The CLI handles this. |
| **LEFT JOIN handle** | INNER JOIN drops messages. The CLI uses LEFT JOIN. |
| **Apple epoch** | Dates are nanoseconds since 2001-01-01. Convert: `date/1000000000 + 978307200`. |
| **Sender format** | Business SMS: `#ServiceName` (e.g. `#MoxBank`). Phone numbers: `+852XXXXXXXX`. |
