---
name: keryx
description: WhatsApp CLI wrapper — contact name resolution, dual-JID conversation merging, daemon-aware send block, sync daemon management. Use instead of raw wacli when working with contacts by name.
triggers:
  - keryx
  - whatsapp
  - wacli
  - send message
  - read chat
  - add contact
  - sync daemon
---

# keryx

Thin wrapper around `wacli` that fixes its four friction points: manual JID lookup, split conversations across phone/LID JIDs, daemon lock on send, and sync reliability (periodic catch-up).

## Pre-flight: Research Before Messaging

If the message asks for publicly available info (fee, hours, address, availability) — check anam + website before messaging (per CLAUDE.md "Check anam before re-researching" rule):
```bash
defuddle parse https://their-website.com   # fast, fails silently on JS-rendered sites
# if empty → fall back to:
agent-browser open https://their-website.com && agent-browser wait 3000 && agent-browser get text
```
Only draft the WhatsApp if both fail. Wix/React/SPA sites look scraped but return nothing to defuddle — agent-browser handles them.

## Commands

```bash
keryx read "Herman"            # merged conversation (phone + LID JIDs)
keryx read "Herman" --limit 5  # last 5 messages
keryx send "Herman" "Hi"              # prints daemon-safe 3-command block
keryx send "Herman" "Hi" --copy      # same + copies (tmux: set-buffer, paste with prefix+]; outside tmux: clipboard)
keryx send "Herman" "Hi" --execute   # executes directly: stop daemon → send → restart (use on Blink/iOS)
keryx chats                    # recent chats (passthrough)
keryx chats --limit 10
keryx add-contact "Dorothy" "+85252660778"  # add to Contacts.app + local alias

# Sync daemon management
keryx sync status              # show daemon PID, running state, last 5 log lines
keryx sync start               # load LaunchAgent
keryx sync stop                # unload LaunchAgent
keryx sync restart             # stop + start
keryx sync catchup             # stop → wacli sync --once → start (recover missed messages)
```

## How It Works

**`keryx read`**
1. Resolves name → all JIDs via `wacli contacts search --json` + `wacli chats list --query --json`
2. Queries all JIDs (both `@s.whatsapp.net` and `@lid`)
3. Merges and deduplicates by timestamp
4. Shows last N messages as `[HH:MM] Me: ...` / `[HH:MM] Name: ...`

**`keryx send`**
Prints the 3-command block — does NOT execute. Copy-paste to run:
```bash
launchctl unload ~/Library/LaunchAgents/com.terry.wacli-sync.plist
wacli send text --to "<JID>" --message "<message>"
launchctl load ~/Library/LaunchAgents/com.terry.wacli-sync.plist
```

## add-contact

`keryx add-contact "Name" "+852XXXXXXXX"` does two things:
1. Writes a vCard to `/tmp/keryx-<slug>.vcf` and opens Contacts.app — click Add to save to iPhone (syncs via iCloud)
2. Saves a local alias to `~/Library/Application Support/keryx/aliases.json`

The alias makes `keryx send` work **immediately** without waiting for WhatsApp to sync the new contact. Once WhatsApp syncs (open WhatsApp on phone to trigger), the normal contact resolution kicks in too.

## Files

- Binary: `~/bin/keryx`
- Source: `~/code/keryx/src/main.rs`
- Contact cache: `~/Library/Application Support/keryx/contacts.json` (1h TTL, auto-refreshed)
- Local aliases: `~/Library/Application Support/keryx/aliases.json`

## Gotchas

- **wacli daemon must be running** for reads to have current data. Check with `keryx sync status`. Restart with `keryx sync restart`.
- **`brew upgrade wacli` overwrites the patched binary.** keryx itself is fine but wacli may break — see `~/docs/solutions/wacli-business-message-fix.md` to re-patch.
- **Multiple name matches** are only an error if they're different people. Same-name / multiple-JID (dual-JID case) is handled automatically.
- **Send requires interactive terminal** — wacli enforces this at the binary level. `--execute` works from a user shell but Claude cannot invoke it on Terry's behalf (non-interactive subprocess). Always paste and run, or use `--execute` yourself.
- **Cache** at `~/Library/Application Support/keryx/contacts.json` — delete to force refresh if a new contact isn't found.
- **`dirs::config_dir()` on macOS** = `~/Library/Application Support/`, not `~/.config`. All keryx data lives there.
- **`add-contact` opens Contacts.app** — requires the Mac's GUI to be accessible. Works from Ghostty/local terminal; may fail silently from pure SSH.
- **`--copy` in tmux** uses `tmux set-buffer` — paste with `prefix + ]` (not Cmd+V). Outside tmux, uses osascript → system clipboard.
- **Quoted messages are truncated in plain output** — the `Text` column only shows the quoted prefix. Use `wacli messages list --chat <jid> --limit N --json` to get the full body (`Text` field in JSON = actual message, `DisplayText` = quote + body).
- **LID name mismatch — fixed in v0.2.0.** `chat_jids_for` now queries by first word and matches any word, so "Joel" LID merges with "Joel Tse" phone JID. Timestamps display in HKT (UTC+8).

## When to Use keryx vs wacli Directly

| Task | Use |
|------|-----|
| Read conversation by name | `keryx read "Name"` |
| Send message by name | `keryx send "Name" "..."` |
| List chats | `keryx chats` |
| Lookup by specific JID | `wacli messages list --chat <jid>` directly |
| Search across chats | `wacli messages search "keyword"` directly |
| Add new contact + save alias | `keryx add-contact "Name" "+852..."` |
| Check/manage sync daemon | `keryx sync status/start/stop/restart` |
| Recover missed messages | `keryx sync catchup` |
| Auth, contacts refresh | `wacli` directly |
