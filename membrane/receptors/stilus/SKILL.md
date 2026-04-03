---
name: stilus
description: Gmail operations via gog CLI — inbox triage, send/reply, archive, batch modify, drafts. Use for email actions. NOT for Cora features (briefs, todos, AI chat) — use nuntius.
user_invocable: true
triggers:
  - stilus
  - gmail
  - email
  - inbox
  - send email
  - reply to email
---

# Stilus

Gmail inbox processing — read, surface, clear. Status-aware operations using the `gog` CLI.

## Commands

### Check Inbox
```bash
gog gmail search "newer_than:1d" --plain | head -20
```
If `gog` fails (keychain locked, auth, no TTY), note "Gmail unavailable" and stop inbox processing for this run.

### Multi-Message Threads
When inbox results show `[N msgs]` on any thread, **always open it** with `gog gmail thread get <id> --plain`. A thread showing as SENT may contain unread replies from others. Never skip a thread based on the sender or label shown in the search results — the newest message may be from someone else.

### View Thread (with status check)
When viewing a thread, ALWAYS check each message's labels:
```bash
# Get thread overview
gog gmail thread get <thread_id>

# For any message you need to verify was actually sent:
gog gmail get <message_id> --plain | grep "label_ids"
```
If thread/message lookup fails, note "Thread/message unavailable" and skip status claim for that message.

**Critical:** A message in a thread view might be a DRAFT, not sent. Always verify:
- `label_ids` contains `SENT` → actually sent
- `label_ids` contains `DRAFT` → NOT sent, still a draft

### Check Drafts
```bash
gog gmail drafts list --plain
```
If this fails, note "Drafts unavailable" and continue with other checks.

### Reply to Thread (DEFAULT: always quote)
**Always use `--reply-to-message-id` + `--quote` when replying.** This is the default — never omit `--quote` unless explicitly asked.
```bash
gog gmail send \
  --reply-to-message-id "<message_id>" \
  --quote \
  --to "<recipient_email>" \
  --subject "Re: <original_subject>" \
  --body "<reply_body>"
```
- `--quote` fetches the original message and includes it as a proper blockquote (HTML with blue left border + plain text with `>` prefix)
- Preserves original formatting (links, bold, images) in the quote
- Adds "On \<date\>, \<sender\> wrote:" attribution line
- Requires `--reply-to-message-id` (not just `--thread-id`)

Always confirm with user before executing send.
If send fails, report "Send failed" and keep the reply body for retry; do not silently retry.

### Create Draft (with attachments / threading)
```bash
gog gmail drafts create \
  --to "recipient@example.com" \
  --cc "cc@example.com" \
  --subject "Re: Thread Subject" \
  --reply-to-message-id "<message_id>" \
  --body "Message body" \
  --attach /path/to/file1.pdf \
  --attach /path/to/file2.pdf
```
- `--reply-to-message-id` threads the draft correctly (sets In-Reply-To/References headers)
- `--attach` is repeatable for multiple files
- The `send` command does NOT have a `--draft` flag — use `drafts create` instead
- If attachment path is missing, stop draft creation and report the missing path.
- If draft creation fails, report failure and do not attempt send.

### Delete Draft
```bash
gog gmail drafts delete <draft_id> --force
```
If delete fails, report "Draft delete failed" and keep the draft ID in output.

## Status Indicators

When reporting email status to user, always be explicit:
- ✉️ SENT — confirmed sent (has SENT label)
- 📝 DRAFT — not sent yet (has DRAFT label)

## Inbox Triage (Morning Email Processing)

Standard flow for clearing the inbox:

### 1. Get inbox threads
```bash
gog gmail search "in:inbox" --max 50 --plain
```
If this returns empty, treat inbox as clear and stop triage.
If this fails, stop triage and report "Inbox fetch unavailable."

**Do NOT use `is:unread` alone** — it searches all mail including archived, and will return thousands of old emails. Always scope to `in:inbox` first.

### 2. Triage — categorise each as: action / informational / archive

**GitHub PR notifications:** Always surface comments on Terry's own PRs (from `notifications@github.com`), even if the comment contains no explicit ask. Positive feedback ("that is cool!", "LGTM") signals momentum toward review/merge and is worth knowing. Do not deprioritise as "no action required."

**Health & appointment emails:** Always surface emails from health providers (clinics, labs, hospitals) regardless of apparent actionability — confirmations, reminders, and results all warrant attention. Do not archive silently.

### 3. Batch mark read + archive
```bash
gog gmail batch modify <id1> <id2> ... --remove UNREAD --remove INBOX -y
```
If batch modify fails, do not continue cleanup; report IDs not processed.

**Thread gotcha:** Search results show one ID per thread. If a thread has `[2 msgs]` or more, the batch modify only marks the shown message — newer messages in the thread remain unread. Fix: after the batch, re-run `gog gmail search "in:inbox is:unread"` and clean up any stragglers.

### 4. Cora brief — read from website (more complete than email)
```bash
porta run --domain cora.computer "https://cora.computer/14910/briefs?date=<YYYY-MM-DD>&time=<morning|afternoon>"
```
Injects Chrome's Cora session into Playwright in the same context and navigates. More reliable than agent-browser profile (cookies don't persist across contexts for Cora).
**Prereq:** Must be logged into cora.computer in regular Chrome. If Chrome session expires, re-login there first.
If porta returns `ERROR: session invalid`, fall back to email: `gog gmail search "from:briefs@cora.computer newer_than:1d" --max 1 --plain`.
If both fail, note "Cora brief unavailable" and continue.

### 5a. LinkedIn job alerts — surface if Cora brief mentions them
If Cora brief mentions "job alerts", fetch directly from email (not in inbox — search all mail):
```bash
gog gmail search "in:all newer_than:2d from:jobalerts-noreply@linkedin.com" --max 3 --plain
gog gmail get <alert_id> --plain | grep -E "^(VP|Director|Manager|Lead|Senior|Principal|AI|Data)" | head -20
```
Surface role titles, companies, and LinkedIn URLs. Do not surface roles below Manager level unless directly relevant.

### 5. SmarTone bill — extract QR payment link
```bash
gog gmail get <smartone_id> --plain | grep -o 'href="https://myaccount.smartone.com/QRBill[^"]*"'
```
Surface as clickable link with amount and due date.
If grep finds no QR link, note "QR link not found" and continue without payment link.

## Auth Gotcha

`gog` requires `GOG_KEYRING_PASSWORD` in env. If not set (e.g. in Claude Code Bash calls):

```bash
GOG_KEYRING_PASSWORD=<password> gog gmail send ...
```

Password is in 1Password: item `sge746vsbefyi6pojwwodzu3o4`, field `gog_keyring_password`.

## Known Gaps
- **No trash/delete command in gog.** User must delete messages manually in Gmail.

## Common Patterns

### "Did this email go out?"
```bash
gog gmail get <message_id> --plain | grep "label_ids"
```
Check for SENT vs DRAFT label.

### "Check for replies"
```bash
gog gmail search "newer_than:1d is:unread" --plain
```

## Example

> Inbox scan complete: 12 inbox threads, 3 actionable, 7 archived, 2 left for reply.
> Cora brief fetched from website; one payment reminder surfaced.
> One draft found (not sent): `DRAFT` label confirmed.

## Boundaries

- Do NOT send emails without explicit user confirmation.
- Do NOT perform deep content summarization; surface actionable status only.
- Do NOT manage non-Gmail channels (WhatsApp/iMessage) in this skill.
