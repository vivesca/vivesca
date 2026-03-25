---
title: "wacli: WhatsApp Business messages display as '(message)'"
date: 2026-02-23
tags:
  - wacli
  - whatsapp-business
  - proto-handling
  - go
  - open-source-contribution
category: cli_tool
component: internal/wa/messages.go
severity: high
pr: https://github.com/steipete/wacli/pull/79
---

# wacli: WhatsApp Business Messages Fix

## Problem

All WhatsApp Business messages (appointment confirmations, menus, interactive buttons) showed as `(message)` in wacli output. Affected template messages, buttons, interactive messages, lists, and their response variants.

## Root Cause

`extractWAProto()` in `internal/wa/messages.go` only handled:
- `Conversation` (plain text)
- `ExtendedTextMessage` (links/rich text)
- Media types (image, video, audio, document, sticker)

Seven WhatsApp Business proto types were unhandled. When `pm.Text` stayed empty, `buildDisplayText()` fell through to the hardcoded `"(message)"` fallback.

## Solution

Added extraction for all business message types in `extractWAProto`:

| Proto Type | What It Is | Text Source |
|---|---|---|
| `TemplateMessage` | Business templates (most common) | `HydratedContentText`, title, footer |
| `ButtonsMessage` | Legacy button menus | `ContentText`, header, footer |
| `ButtonsResponseMessage` | User's button tap | `SelectedDisplayText` |
| `InteractiveMessage` | Modern interactive (shop, flow) | Header title, body text, footer |
| `InteractiveResponseMessage` | User's interactive response | Body text |
| `ListMessage` | Picker lists | Title, description |
| `ListResponseMessage` | User's list selection | Title or selected row ID |
| `TemplateButtonReplyMessage` | Template button reply | `SelectedDisplayText` |

Also extended `contextInfoForMessage` and `displayTextForProto` for reply-chain and quoted message support.

**No schema changes** — text flows into existing `pm.Text` field.

### Key pattern

```go
if tmpl := m.GetTemplateMessage(); tmpl != nil && pm.Text == "" {
    // extract title, content, footer → join with \n
    pm.Text = strings.Join(parts, "\n")
}
```

Helper functions: `hydratedTemplate()` (checks both template formats), `interactiveText()` (extracts header/body/footer).

## Build Gotcha

Must compile with FTS5 support:
```bash
CGO_ENABLED=1 go build -tags sqlite_fts5 -o wacli ./cmd/wacli/
```
Without `sqlite_fts5`, runtime error: `no such module: fts5`.

## Homebrew Patch Installation

Binary lives at `/opt/homebrew/Cellar/wacli/0.2.0/bin/wacli` (symlinked from `.msg-util-7f3a`). To install patched build:

```bash
chmod u+w /opt/homebrew/Cellar/wacli/0.2.0/bin/wacli
cp /tmp/wacli-patched /opt/homebrew/Cellar/wacli/0.2.0/bin/wacli
```

Backup at `wacli.bak` in same directory. `brew upgrade wacli` will overwrite — re-apply after upgrades until PR is merged and released.

## Limitation

Fix only applies to **new messages**. Existing `(message)` entries in the DB are not retroactively fixed — raw proto is not stored, only extracted text. A proper fix would require storing `proto_bytes` in the schema (proposed as future improvement).

## Verification

Tested live: sent message to QHMS (Quality HealthCare) business account, confirmed Nurse Angel bot response rendered with full text instead of `(message)`.

## Related

- PR: https://github.com/steipete/wacli/pull/79
- Fork: `terry-li-hm/wacli`, branch `feat/business-message-types`
- wacli send safety: `~/docs/solutions/patterns/critical-patterns.md` (never send directly)

## History Backfill Limitations (Mar 2026)

`wacli history backfill --chat <JID>` times out even with WhatsApp open on iPhone. On-demand history sync only works reliably immediately after initial device pairing — not for arbitrary past gaps. Messages missed during sync daemon downtime are unrecoverable via wacli.

**Prevention:** `keryx sync catchup` (runs every 2h via LaunchAgent) minimises gap windows. Manual recovery: check phone directly.
