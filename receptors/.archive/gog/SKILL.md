---
name: gog
description: Google Workspace CLI for Gmail, Calendar, Drive, Contacts, Sheets, and Docs. Use when user needs to interact with Google services via CLI.
user_invocable: false
github_url: https://github.com/steipete/gogcli
---

# gog

Google Workspace CLI for Gmail, Calendar, Drive, Contacts, Sheets, and Docs.

## Prerequisites

- `gog` CLI installed: `brew install steipete/tap/gogcli`
- OAuth setup completed

## Setup

```bash
gog auth credentials /path/to/client_secret.json
gog auth add you@gmail.com --services gmail,calendar,drive,contacts,docs,sheets
gog auth list
```

## Gmail

```bash
# Search threads
gog gmail search 'newer_than:7d' --max 10

# Search messages (per email, ignores threading)
gog gmail messages search "in:inbox from:company.com" --max 20 --account you@example.com

# Send plain text
gog gmail send --to a@b.com --subject "Hi" --body "Hello"

# Send from file
gog gmail send --to a@b.com --subject "Hi" --body-file ./message.txt

# Send HTML
gog gmail send --to a@b.com --subject "Hi" --body-html "<p>Hello</p>"

# Create draft
gog gmail drafts create --to a@b.com --subject "Hi" --body-file ./message.txt

# Send draft
gog gmail drafts send <draftId>

# Reply
gog gmail send --to a@b.com --subject "Re: Hi" --body "Reply" --reply-to-message-id <msgId>
```

## Calendar

```bash
# List events
gog calendar events <calendarId> --from <iso> --to <iso>

# Create event
gog calendar create <calendarId> --summary "Title" --from <iso> --to <iso>

# Create with color
gog calendar create <calendarId> --summary "Title" --from <iso> --to <iso> --event-color 7

# Update event
gog calendar update <calendarId> <eventId> --summary "New Title" --event-color 4

# Show available colors
gog calendar colors
```

## Drive

```bash
gog drive search "query" --max 10
```

## Contacts

```bash
gog contacts list --max 20
```

## Sheets

```bash
# Get data
gog sheets get <sheetId> "Tab!A1:D10" --json

# Update cells
gog sheets update <sheetId> "Tab!A1:B2" --values-json '[["A","B"],["1","2"]]' --input USER_ENTERED

# Append rows
gog sheets append <sheetId> "Tab!A:C" --values-json '[["x","y","z"]]' --insert INSERT_ROWS

# Clear range
gog sheets clear <sheetId> "Tab!A2:Z"

# Get metadata
gog sheets metadata <sheetId> --json
```

## Docs

```bash
# Export to text
gog docs export <docId> --format txt --out /tmp/doc.txt

# Cat contents
gog docs cat <docId>
```

## Notes

- Use `gog` for CLI scripting; use Gmail MCP or browser for interactive email (replies, threads)
- Gmail MCP has limitations with replies — use browser automation for complex email workflows
