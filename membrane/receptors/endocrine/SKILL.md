---
name: endocrine
description: "Email — inbox triage, compose (send/reply/draft), and Cora AI assistant. Routes by intent. \"email\", \"inbox\", \"triage\", \"send email\", \"reply\", \"draft\", \"cora\", \"brief\", \"email todos\", \"endocrine\""
effort: high
user_invocable: true
triggers:
  - endocrine
  - email
  - inbox
  - email triage
  - review inbox
  - send email
  - reply to email
  - draft email
  - compose email
  - cora
  - email brief
  - email todos
---

# Endocrine — Email (one skill, three modes)

All email operations live here: triage, compose, Cora assistant. Internal routing by intent.

## Mode routing

| Intent | Mode | Trigger phrases |
|---|---|---|
| Read / clear inbox | **Triage** | "triage", "review inbox", "check email", "clear inbox" |
| Write outbound | **Compose** | "send", "reply", "draft", "compose" |
| Cora AI assistant | **Cora** | "cora", "brief", "cora todos" |

If intent is ambiguous ("email" alone with no verb), ask once: triage or compose?

## Tool discipline (all modes)

**All Gmail ops default to the `endosomal` MCP tool.** Typed inputs, structured outputs, enforceable contracts. Actions: `search`, `thread`, `categorize`, `archive`, `mark_read`, `label`, `filter`, `send`.

**Fall back to `gog gmail` CLI only for endosomal gaps** (see `finding_endosomal_mcp_gaps.md`):
- Reply with `--quote` (auto blockquote of original)
- Drafts CRUD (`drafts create`, `drafts list`, `drafts delete`)
- Priority-inbox filters with `--never-spam --important`

All other paths go through endosomal MCP. Never shell out to `gog gmail` for anything endosomal covers.

---

# Triage mode

A collaborative inbox review. Pull inbox + unread briefs, read everything, work through items with Terry.

**Rule: classify first, act in batches — never archive without categorizing.**

## Triage discipline

1. **Search before browsing** — `endosomal action=search query="..."`; negation clauses (`-in:inbox`) go inside one query string, not as separate tokens.
2. **Fetch full threads, not snippets** — `endosomal action=thread thread_id=<id>`; snippets miss context that changes the category.
3. **Categorize before archiving** — `endosomal action=categorize email_text="..."` on ambiguous emails; deterministic pass handles most, LLM only fires on genuine ambiguity.
4. **Batch archive** — collect all archive IDs, then one `endosomal action=archive message_ids=[...]` call. Never archive one at a time.
5. **Filter last** — only propose `endosomal action=filter` (`dry_run=true` first) after you've seen the pattern recur in 3+ messages. Confirm before flipping `dry_run=false`.

| Don't | Do |
|-------|-----|
| Archive without classifying | Categorize, then batch archive |
| Assume newsletter = archive | Check for action signals in body |
| Create filters for one-off senders | Wait for 3+ recurrences |
| Mark read without archiving action items | Surface action_required before touching read state |
| Pass negation as separate args | Pass as one quoted query string |

## Step 0 — Load context

Run in parallel:
1. Read `[[Email Threads Tracker]]` (`~/epigenome/chromatin/Email Threads Tracker.md`) — status on ongoing threads so you don't re-read histories or re-ask resolved questions.
2. Read `memory/priming.md` — check for any `WHEN: email triage` entries. Surface matched reminders before presenting the inbox. Delete entries after actioning.
3. If any action-required email involves someone Terry has history with, run `amicus lookup <name>` to surface last contact date and context. Only for replies/meetings where relationship context would help — not every email.

## Step 1 — Load the inbox and briefs

Run in parallel:
- `cora brief` — list all briefs, check for unread ones
- `endosomal action=search query="in:inbox"` — full inbox list
- `endosomal action=search query="label:Cora/Action"` — Cora-flagged actions outside inbox
- `endosomal action=search query="-in:inbox newer_than:7d"` — silent miss sweep, all non-inbox emails

**`Cora/Action` emails must be triaged** even though they're not in inbox — Cora flagged them as requiring action but stripped INBOX. Treat them identically to inbox items.

**Silent miss sweep** catches anything not in inbox — interview emails, ATS notifications, banking alerts, anything Cora moved to brief-only or Gmail miscategorised. Expect noise — scan for anything actionable and restore INBOX via `endosomal action=label name=INBOX message_ids=[<id>]`.

Then read **all unread briefs** before triaging:
```bash
cora brief show <id>    # for each unread brief
```

If `cora brief show` errors, note it but continue with the inbox. Multiple unread briefs → read newest first, older may be superseded.

Extract any action items from briefs and include them in Step 2 alongside inbox emails.

## Step 2 — Triage and present

Categorise every email into one of four buckets:

| Bucket | Criteria | Action |
|---|---|---|
| **Action required** | Needs a reply, decision, or follow-up | Present with context |
| **Borderline** | Probably noise but could matter — low confidence | One-line mention before archiving |
| **Monitor / waiting** | Ball is in someone else's court | Note and archive if clean |
| **Archive now** | Transactional, automated, or already handled | Archive without presenting |

**Borderline bucket** exists because email delegation is a single point of failure. When in doubt, surface it in one line rather than silently archiving. Examples: financial emails from unfamiliar senders, anything mentioning deadlines, emails from domains that previously contained action items. Present borderline items as a compact list after action-required items — Terry can scan in 10 seconds and say "all fine" or flag one.

**Archive now without asking:** OTPs, login notifications, password resets, automated "pending request" emails that have been superseded, booking confirmations already actioned.

**Always-surface heuristics.** Some email types warrant attention regardless of apparent actionability:
- **GitHub PR comments on your own PRs** (from `notifications@github.com`) — surface even positive feedback ("LGTM", "that is cool!"). It signals merge momentum. Do not deprioritise as "no action required".
- **Health/appointment emails** (clinics, labs, hospitals) — confirmations, reminders, results. Never archive silently.
- **SmarTone bill** — extract QR payment link: `endosomal action=thread thread_id=<id>` and grep body for `href="https://myaccount.smartone.com/QRBill[^"]*"`. Surface as clickable link with amount + due date.
- **LinkedIn job alerts** (`jobalerts-noreply@linkedin.com`) — if a Cora brief mentions them, scan role titles Manager+ only. Speculor handles bulk job triage separately.
- **Single payment/transfer ≥ HKD 10,000** — surface sender + amount even if categorized as routine (Cora "payments" bucket). Large transfers warrant verification regardless of likely-self-transfer prior. Codified after 2026-05-04 Slot 31: HKD 50K SC Pay receipt classified routine, caught only on Terry's "really nothing important?" probe.

**Probe-question semantics (added 2026-05-04 Slot 31).** When Terry asks "really nothing?" / "anything else?" / "are we sure?" after a sweep that CC has marked complete, treat it as a forcing function for re-scan with higher gain — NOT as a request for confirmation of the prior pass. The probe means "test whether your default-to-finished is real." Re-scan the briefs/inbox at higher signal threshold (large transactions, off-hours senders, unfamiliar domains, anything you sorted as routine without explicit verification). Codified after the same 2026-05-04 Slot 31 instance — HKD 50K only surfaced on probe.

**Cora Briefs emails — read before archiving.** Each brief email in inbox represents unread digest content. Read via `cora brief show <id>` first, extract action items, then archive the email. Never batch-archive briefs without reading them.

**Post-discussion cleanup.** After presenting items and getting Terry's agreement ("archive", "mark read", "all fine"), immediately mark_read + archive the discussed noise items in one batch. Don't wait for a separate instruction — agreement IS the gate.

**Batch processing over one-by-one.** Don't work through items sequentially waiting for approval on each. Instead:
1. Present all action-required items with recommendations
2. Present borderline items as a compact list
3. Auto-archive all noise
4. Pull full details on action items in parallel
5. Terry gives calls on the batch — then execute

**Thematic grouping for large inboxes (>10 items).** When presenting, group by theme (banking/tax, shipping, notifications, action-needed) rather than chronological order. Batch auto-archivable groups first (expired OTPs, superseded notifications, bot reviews on closed PRs), then present remaining groups for review. This lets Terry process faster — one "y" per theme instead of per email.

Present the action-required list first. For each item, include:
- Who it's from and subject
- What's needed (reply / decision / read)
- Any relevant context from vault (e.g. open items in NOW.md that match)

## Step 3 — Execute decisions

After Terry gives calls on the batch:
1. `cora email show <id>` or `endosomal action=thread thread_id=<id>` for threads that need drafting
2. Execute: draft reply (see **Compose mode** below) / archive / update vault / update calendar
3. Archive each email once resolved unless Terry says keep it

**Prefer Gmail filters over unsubscribing.** When a sender is consistently noise, create a filter via `endosomal action=filter from_sender="<sender>" archive=true dry_run=true` (flip `dry_run=false` to apply). Filters are reversible, don't require waiting for unsub propagation, and emails remain in archive for Cora briefs.

**Filter-creation scope preflight (run once per session before any filter attempt).** Both `endosomal action=filter` and `gog gmail filters create` require the `gmail.settings.basic` OAuth scope. If that scope is missing, every filter call 403s with `insufficientPermissions` — and the failure mode is identical across both tools, so there's no second-tool fallback. Before the first filter attempt of a session, either (a) `gog gmail filters list --plain` returns existing filters cleanly → scope is present, proceed, or (b) any 403 with "insufficient authentication scopes" → STOP, do NOT retry on the second tool. Queue the proposed filter spec for after the re-auth (Praxis Quick item) instead. See `marks/finding_gog_endosomal_missing_gmail_settings_scope.md`. Codified after 2026-04-28 triage where two tools hit the same 403 on the same scope gap before the pattern surfaced.

## Step 4 — Archive the noise

After working through all action items, batch-archive using the right tool per source:

- **Inbox emails** → `cora email archive <id>` first; if it still shows in inbox after, fall back to `endosomal action=archive message_ids=[<id>,...]`
- **Silent miss sweep / Cora/Action emails** → `endosomal action=archive message_ids=[...]` (`cora email archive` fails — Cora never indexed these)
- **Always verify** with `endosomal action=search query="in:inbox"` after archiving — `cora email archive` doesn't always remove INBOX cleanly

Batch, one call per source. Verify with `endosomal action=search query="in:inbox"` at the end.

**HARD GATE: Cora brief emails must be read via `cora brief show <id>` before archiving.** Even in ad-hoc inbox checks outside full triage mode — never batch-archive a Cora brief notification without reading its content first. Extract action items, then archive.

Then mark all processed briefs as read and archive their notification emails:
```bash
cora brief show <brief_id>                          # read content FIRST
cora brief read <brief_id>                          # mark brief as read
cora email archive <brief_notification_email_id>    # archive the "Morning Brief | ..." email
```

Confirm count: "Archived X emails. Inbox zero."

**Note:** Gmail's "All Mail" unread badge will still show a count — Cora intentionally never marks emails as read (the brief is the reading interface). Inbox zero is the goal; All Mail unread count is expected noise.

## Step 5 — Sync NOW.md

After the session:
- Update `[open]` items in NOW.md that were resolved
- Add new open items that surfaced
- Note emails still pending a reply (waiting on others)
- **Update `[[Email Threads Tracker]]`** — add new active threads, update status, move resolved to Resolved section

## Triage workflow conventions

- **Inbox = action queue.** Archive = done. Don't leave resolved emails in inbox.
- **Thread view first.** Before actioning, check for newer messages in the thread (`endosomal action=thread thread_id=<id>`).
- **Silent miss check.** For any expected email not in the inbox: `endosomal action=search query="from:<domain>"`.
- **Domain filters (priority inbox).** If a critical domain keeps missing the inbox, set a `--never-spam --important` filter. Endosomal's `filter` action lacks those flags, so use `gog gmail filters create --from "<domain>" --never-spam --important`. Currently set: `aia.com`, `mtr.com.hk`, `capco.com`, `myworkday.com`, `greenhouse.io`, `lever.co`, `smartrecruiters.com`, `taleo.net`, `icims.com`.

## Triage fail states

- `cora brief show` errors → try `porta run` fallback (below), continue with endosomal inbox search
- Email not in inbox but expected → `endosomal action=search query="from:<domain>"` before concluding missing
- Can't draft reply in session → add to NOW.md as `[open]` and archive

### `cora brief show` crash fallback

When `cora brief show <id>` crashes mid-render (known issue: PPS payment items), read the brief via browser:

```bash
cora email show <brief_email_id>   # find the "Read full brief" link
porta run --domain cora.computer --selector body "https://cora.computer/14910/briefs?date=<YYYY-MM-DD>&time=morning"
```

URL pattern: `https://cora.computer/14910/briefs?date=YYYY-MM-DD&time=morning` (account ID 14910). Login to cora.computer in Chrome first.

---

# Compose mode

Writing emails: send, reply with quote, drafts with attachments.

## Standalone-correspondence precondition (mandatory before send)

**Before any compose-and-send action** (email, Teams reply, WhatsApp draft handed to Terry, partner-comms): create a standalone chromatin file with the verbatim draft FIRST, then send. The standalone file is the precondition, not a post-hoc artefact.

File path: `~/epigenome/chromatin/immunity/YYYY-MM-DD-terry-<recipient>-<subject>.md` (or `terry-reply-<recipient>-<subject>.md` for replies).

Required frontmatter:
- `title`, `date`, `sent_at`, `type` (correspondence-sent / correspondence-draft), `channel`, `from`, `to`, `in_reply_to:` (wikilink to incoming if reply), `commits_to:` (any explicit promise/deadline), `related:` (interlinks to relevant chromatin notes — paper version, project notes, profiles).

Body sections: verbatim sent text under `## Sent text (verbatim)`, drafting context if applicable, commitment vs delivery state.

**Why mandatory:** `feedback_standalone_correspondence_notes.md` (PROTECTED, confirmed=2). The recurring failure mode is outbound captured only as a daily-note summary; commitments / verbatim / interlinks get lost. Three days later when traceability is needed, the verbatim has to be recovered via anam search of the session JSONL — slow, brittle, sometimes impossible if the session was on a different harness.

**Skip ONLY for:** pure logistics ("sure, 3pm works"), one-line acknowledgements, or messages with no commitment / decision / directional content. Bar is low: when in doubt, file it.

**Backstop if missed at send time:** `cytokinesis` §1a question 7 catches this at wrap. Backfill via anam search of session JSONL for verbatim; mark with `backfilled:` + `backfill_source:` frontmatter for transparency.

## Send (plain)

Default path is `endosomal` MCP. Covers `to`, `cc`, `subject`, `body`, `reply_to_message_id`, `attach`.

```
endosomal action=send
  to="recipient@example.com"
  subject="<subject>"
  body="<body>"
  cc="<optional cc>"
  attach=["/path/to/file.pdf", ...]
```

Always confirm with user before executing send. If send fails, report "Send failed" and keep the body for retry; do not silently retry.

## Reply with quote (DEFAULT for replies)

**Always use `--reply-to-message-id` + `--quote` when replying.** Never omit `--quote` unless explicitly asked. Until endosomal supports a quote flag, use gog:

```bash
gog gmail send \
  --reply-to-message-id "<message_id>" \
  --quote \
  --to "<recipient_email>" \
  --subject "Re: <original_subject>" \
  --body "<reply_body>"
```

- `--quote` fetches the original and includes it as blockquote (HTML blue border + plain `>` prefix)
- Preserves original formatting (links, bold, images)
- Adds "On <date>, <sender> wrote:" attribution
- Requires `--reply-to-message-id`, not just `--thread-id`

## Create draft (with attachments / threading)

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
- `--attach` is repeatable
- The `send` command has no `--draft` flag — use `drafts create`
- Missing attachment path → stop, report, don't silently skip
- Draft creation fails → report, do not attempt send

## List / delete drafts

```bash
gog gmail drafts list --plain
gog gmail drafts delete <draft_id> --force
```

If delete fails, report "Draft delete failed" and keep the draft ID in output.

## Verify sent status

"Did this email go out?"

```bash
gog gmail get <message_id> --plain | grep "label_ids"
```

- `label_ids` contains `SENT` → actually sent
- `label_ids` contains `DRAFT` → NOT sent, still a draft

A message in a thread view may be a DRAFT, not sent — always verify labels before claiming a message was sent.

When reporting status:
- SENT — confirmed sent (has SENT label)
- DRAFT — not sent yet (has DRAFT label)

## Compose gotcha: `gog gmail thread show` truncates body

`gog gmail thread show <id>` truncates the email body at ~1000 chars. For full content — headers (e.g. `List-Unsubscribe`) and base64 body parts — use `endosomal action=thread thread_id=<id>` (which does not truncate), or as a fallback:

```bash
gog gmail thread get <id> --json | python3 -c "
import sys, json
data = json.load(sys.stdin)
def walk(obj):
    if isinstance(obj, dict):
        if obj.get('name','').lower() == 'list-unsubscribe': print(obj.get('value',''))
        for v in obj.values(): walk(v)
    elif isinstance(obj, list): [walk(i) for i in obj]
walk(data)
"
```

## gog auth gotcha

`gog` requires `GOG_KEYRING_PASSWORD` in env. If not set (e.g. in Claude Code Bash calls):

```bash
GOG_KEYRING_PASSWORD=<password> gog gmail send ...
```

Password: 1Password item `sge746vsbefyi6pojwwodzu3o4`, field `gog_keyring_password`.

## Compose boundaries

- Never send emails without explicit user confirmation.
- Don't manage non-Gmail channels (WhatsApp, iMessage, Telegram) here.
- No trash/delete command in gog — user deletes manually in Gmail.

## Pre-flight (mandatory before first draft of any compose-mode email)

**Grep email-drafting marks BEFORE writing the first draft, not just at session start.** Genome §How to Think requires marks-grep when entering a domain; CC's failure mode is to grep at session start, then drift through multiple email iterations without re-checking. The em-dash recurrence (5+ violations across one session, 2026-05-02) demonstrated this — rule loaded at session start, violated at every draft.

```bash
grep -l "email\|drafting\|writing style" ~/epigenome/marks/*.md | head -5
```

Read `feedback_email_drafting_style.md` (PROTECTED, confirmed=1+) at minimum: no em dashes, no en dashes, no filler closers, no exclamation marks by default. Re-read at each major draft revision, not just first-draft.

## Polish iteration discipline (mandatory after cycle 2 on any micro-decision)

When user iterates on a single micro-decision (preposition choice, single-phrase add/drop, one-word swap) and the same decision cycles 2+ times, **stop producing fresh "honest comparison" tables and declare taste-level**. This applies when both options work and the choice is preference, not analysis.

**Stronger trigger (sharpened 2026-05-04 after 2nd instance):** the trigger is not "same micro-decision asked twice" — it's "user has questioned ANY aspect of the SAME draft 2 times via 'should we / what if / is it X?' framing." Even if the questions hop between micro-decisions (closer warmth, length-match, phrasing, filler), the cycle count is per-draft, not per-decision. After 2 such pushbacks on the same draft, the next response defaults to taste-level handling for whatever micro-decision arrives next — do not produce a fresh comparison.

Decision tree at cycle 2+:

1. **Both options work?** → "This is taste-level. Both work. Pick whichever reads right to you." Stop generating new analytic frames.
2. **Position genuinely held?** → "Same reasoning as before — [one sentence]. No new information changes the call." Don't generate fresh analysis to justify holding.
3. **Genuinely flipped by new context?** → "What's new is X — that changes the call to Y." Name the new information explicitly.

**Anti-pattern (filed as `finding_cc_polish_iteration_micro_edit_thrash.md`):** producing a fresh "honest comparison" table each cycle that conveniently lands where the user's question implies. Each cycle CC produces new tables/pros-cons/"honest reads" instead of recognizing taste-decision. This dilutes signal, costs tokens, and trains user to expect CC will flip on demand.

The sibling-pattern epistemics file is `~/epigenome/chromatin/euchromatin/epistemics/reactive-flip-needs-independent-grounding.md` — that covers grounded-position pushback. Polish-iteration thrash is the taste-decision sub-case where there are no grounds to defend; the right move is naming the decision-type, not generating analysis.

**Recurrence note (2026-05-04 Slot 31):** 2nd instance — Cartier reply 6 cycles, BOCHK reply 3 cycles. Skill-edit-only enforcement is demonstrably not deterring. If 3rd instance occurs, escalate to mitosis cycle as deterministic-enforcement candidate (hook: count fresh comparison frames within last N turns, fire when ≥2 same-draft).

---

# Cora mode

Cora (cora.computer) is an AI email assistant that processes Gmail, generates daily briefs, manages todos, and drafts replies. Interact via the `cora` CLI.

## Cora auth

```bash
cora whoami     # verify authenticated
cora status     # account status, brief settings, usage
```

If not authenticated: `cora login --token=<TOKEN_FROM_1PASSWORD>`. Token lives in 1Password (do NOT hardcode in files).

## Cora briefs

```bash
cora brief              # list recent briefs
cora brief show         # show latest brief details
cora brief show <id>    # show specific brief
cora brief show --open  # show and open in browser
cora brief --json       # JSON output (briefs use --json, not --format json)
cora brief read <id>    # mark brief as read
```

**Crash fallback** — see "Triage fail states > `cora brief show` crash fallback" above.

## Cora todos

Cora maintains its own action queue independent of Gmail labels:

```bash
cora todo list                                           # pending todos
cora todo list --all                                     # include completed
cora todo show <id>                                      # details
cora todo create "Title"                                 # new todo
cora todo create "Title" --priority high --due tomorrow  # with options
cora todo edit <id> --title "New" --priority low         # update
cora todo complete <id>                                  # mark done
cora todo delete <id> --force                            # delete
cora todo list --format json                             # JSON output
```

## Cora email commands

```bash
cora email glimpse          # fast cached inbox view
cora email search "query"   # search with Gmail query syntax
cora email show <id>        # full email details
cora email archive <id>     # archive
cora email draft <id>       # queue reply draft (async, returns immediately)
```

## Cora chat (slow — use only when no instant command fits)

```bash
cora chat send "message"              # new conversation (10-60s)
cora chat send "message" --chat <id>  # continue conversation
```

Prefer instant commands. Chat is for open-ended requests that don't map to a CLI verb.

## Cora best practices

- **Prefer instant commands** over `cora chat send` — chat is 10-60s
- **briefs use `--json`**, not `--format json` (unlike other commands)
- **Don't use `cora flow`** — requires interactive stdin, will hang
- **Don't retry failures** more than once — ask user for guidance

## Cora gotchas (hard-won)

### `Cora/Action` label: invisible workflow (confirmed Mar 2026)
Emails labelled `Cora/Action` by Cora are excluded from both the inbox (INBOX stripped) AND the daily brief. The label exists but leads nowhere — no workflow surfaces it automatically.

**Mitigation:** Triage mode Step 1 explicitly pulls `label:Cora/Action` as a parallel search. Always triage these alongside the inbox.

### Interview/recruiter emails silently missing from inbox
Confirmed cases: MTR interview Mar 4 2026 (`important_draft` category), AIA/Cherry Ma Mar 6 2026 (`CATEGORY_PERSONAL`, no INBOX, no Cora label), AIA Workday Mar 9 2026 (from `aia@myworkday.com`, no Cora label). Root cause unclear — may be Gmail miscategorisation or Cora stripping INBOX during processing.

**Permanent mitigation:** Gmail filters force `--important` and `--never-spam` for active job domains. See Triage workflow conventions > Domain filters. Add new company domains when applying; ATS platforms are covered globally.

**When expecting a reply, also proactively search:**
```bash
endosomal action=search query="from:<domain>"
```

**If email is missing INBOX label, restore it:**
```bash
endosomal action=label name=INBOX message_ids=[<id>]
```

### "All Mail" unread count is expected noise
Cora intentionally never marks emails as read. Model: the daily brief is the reading interface, not Gmail. Cora labels emails (`Cora/Newsletter`, `Cora/Payments`, etc.) but leaves read/unread state alone. The `Next Brief` label tracks "briefed yet", not Gmail's unread flag.

**Don't try to zero the All Mail unread count** — it accumulates again. Set Gmail's unread badge to inbox-only (Settings → General → Inbox count). Inbox zero is the goal; All Mail unread is noise.

## Cora error codes

- `0` — Success
- `1` — General error
- `2` — Authentication required (`cora login`)
- `3` — Resource not found
- `4` — Validation error

---

## Known gaps

- **endosomal MCP** missing `--quote` reply and drafts CRUD — tracked in `finding_endosomal_mcp_gaps.md`. Compose mode falls back to `gog gmail` for these two cases.
- **Cora `brief show` crash on PPS items** — use `porta run` browser fallback.
