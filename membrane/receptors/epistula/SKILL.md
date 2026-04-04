---
name: epistula
description: "Guided inbox triage — review Gmail with Terry, prioritise action items, archive noise."
user_invocable: true
---

# Epistula — Email Review Session

A collaborative inbox triage. Claude pulls the inbox and all unread briefs, reads everything, and works through items with Terry one by one.

## Step 0 — Load context

Run in parallel:
1. Read `[[Email Threads Tracker]]` (`~/epigenome/chromatin/Email Threads Tracker.md`) — status on ongoing threads so you don't re-read full histories or re-ask resolved questions.
2. Read `memory/priming.md` — check for any `WHEN: email triage` entries. Surface matched reminders before presenting the inbox. Delete entries after actioning.
3. If any action-required email involves a person Terry has history with, run `amicus lookup <name>` to surface last contact date and context. Don't do this for every email — only for replies/meetings where relationship context would help Terry decide.

## Step 1 — Load the inbox and briefs

Run in parallel:
```bash
cora brief                                                                         # list all briefs — check for unread ones
gog gmail search "in:inbox" --limit 30                                             # full inbox list
gog gmail search "label:Cora/Action" --limit 20                                    # Cora-flagged actions outside inbox
gog gmail search "NOT in:inbox newer_than:7d" --limit 50  # silent miss sweep — all non-inbox emails
```

**`Cora/Action` emails must be triaged** even though they're not in inbox — Cora explicitly flagged them as requiring action but strips the INBOX label. Treat them identically to inbox items.

**Silent miss sweep** catches anything not in inbox — interview emails, ATS notifications, banking alerts, anything Cora moved to brief-only or Gmail miscategorised. Expect noise (newsletters, Vercel alerts, OTPs) — scan quickly for anything actionable and restore INBOX: `gog gmail thread modify <id> --add INBOX`.

Then read **all unread briefs** before triaging:
```bash
cora brief show <id>    # for each unread brief
```

If `cora brief show` errors, note it but continue with the inbox. If multiple unread briefs, read newest first — older ones may be superseded.

Extract any action items from briefs and include them in the Step 2 triage alongside inbox emails.

## Step 2 — Triage and present

Categorise every email into one of four buckets:

| Bucket | Criteria | Action |
|---|---|---|
| **Action required** | Needs a reply, decision, or follow-up | Present with context |
| **Borderline** | Probably noise but could matter — low confidence | One-line mention before archiving |
| **Monitor / waiting** | Ball is in someone else's court | Note and archive if clean |
| **Archive now** | Transactional, automated, or already handled | Archive without presenting |

**Borderline bucket** exists because email delegation is a single point of failure. When in doubt, surface it in one line rather than silently archiving. Examples: financial emails from unfamiliar senders, anything mentioning deadlines, emails from domains that have previously contained action items. Present borderline items as a compact list after action-required items — Terry can scan in 10 seconds and say "all fine" or flag one.

**Archive now without asking:** OTPs, login notifications, password resets, automated "pending request" emails that have been superseded, booking confirmations already actioned.

**Cora Briefs emails — read before archiving.** Each brief email in the inbox represents unread digest content. Read the brief via `cora brief show <id>` first, extract any action items, then archive the email. Never batch-archive briefs without reading them.

**Batch processing over one-by-one.** Don't work through items sequentially waiting for approval on each. Instead:
1. Present all action-required items with recommendations
2. Present borderline items as a compact list
3. Auto-archive all noise
4. Pull full details on action items in parallel
5. Terry gives calls on the batch — then execute

Present the action-required list first. For each item, include:
- Who it's from and subject
- What's needed (reply / decision / read)
- Any relevant context from vault (e.g. open items in NOW.md that match)

## Step 3 — Execute decisions

After Terry gives calls on the batch:
1. `cora email show <id>` or `gog gmail thread show <id>` for threads that need drafting
2. Execute: draft reply / archive / update vault / update calendar as agreed
3. Archive each email once resolved unless Terry says keep it

**Prefer Gmail filters over unsubscribing.** When a sender is consistently noise, create a filter (`gog gmail filters create --from "<sender>" --archive`) rather than unsubscribing. Filters are reversible, don't require waiting for unsub propagation, and emails remain in archive for Cora briefs.

## Step 4 — Archive the noise

After working through all action items, batch-archive using the right tool per email source:

- **Inbox emails** → `cora email archive <id>` first; if it still shows in inbox after, fall back to `gog gmail thread modify <id> --remove INBOX`
- **Silent miss sweep / Cora/Action emails** → `gog gmail thread modify <id> --remove INBOX` (`cora email archive` fails — Cora never indexed these)
- **Always verify** with `gog gmail search "in:inbox"` after archiving — `cora email archive` doesn't always remove INBOX cleanly

```bash
cora email archive <id1>   # inbox emails
gog gmail thread modify <id2> --remove INBOX  # silent miss sweep emails
```

Verify with `gog gmail search "in:inbox" --limit 20` at the end.

Then mark all processed briefs as read and archive their notification emails:
```bash
cora brief read <brief_id>                          # mark brief as read
cora email archive <brief_notification_email_id>    # archive the "Morning Brief | ..." email from inbox
```

Confirm count: "Archived X emails. Inbox zero."

**Note:** Gmail's unread badge in "All Mail" will still show a count — Cora intentionally never marks emails as read (the brief is the reading interface, not Gmail). Inbox zero is the goal; All Mail unread count is expected noise.

## Step 5 — Sync NOW.md

After the session:
- Update any `[open]` items in NOW.md that were resolved
- Add any new open items that surfaced
- Note any emails still pending a reply (waiting on others)
- **Update `[[Email Threads Tracker]]`** — add new active threads, update status on existing ones, move resolved threads to Resolved section

## Workflow conventions

- **Inbox = action queue.** Archive = done. Don't leave resolved emails in inbox.
- **Thread view first.** Before actioning, always check if there are newer messages in the thread (`gog gmail thread show`).
- **Silent miss check.** For any expected email that isn't in the inbox: `gog gmail search "from:<domain>"` — catches emails Cora missed entirely.
- **Domain filters.** If a critical domain keeps missing the inbox, add a filter: `gog gmail filters create --from "<domain>" --never-spam --important`. Currently set: `aia.com`, `mtr.com.hk`, `capco.com`, `myworkday.com`, `greenhouse.io`, `lever.co`, `smartrecruiters.com`, `taleo.net`, `icims.com`.

## Fail states

- `cora brief show` errors → try `porta run` as fallback (see below), then continue with gog inbox
- Email not in inbox but expected → search gog directly before concluding missing
- Can't draft reply in session → add to NOW.md as `[open]` and archive the email

### `cora brief show` crash fallback

When `cora brief show <id>` crashes mid-render (known issue: PPS payment items), read the brief via browser:

```bash
# Get the brief URL from the brief email in inbox
cora email show <brief_email_id>   # find the "Read full brief" link

# Then fetch via porta run (login to cora.computer in Chrome first)
porta run --domain cora.computer --selector body "https://cora.computer/<id>/briefs?date=<YYYY-MM-DD>&time=morning"
```

URL pattern: `https://cora.computer/14910/briefs?date=YYYY-MM-DD&time=morning` (account ID 14910).

## Calls
- `nuntius` — Cora CLI reference
