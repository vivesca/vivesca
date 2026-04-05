---
name: message
description: Draft responses to recruiter and networking messages (LinkedIn DMs, WhatsApp intros, cold outreach). "reply to recruiter", "draft message", "respond to outreach". NOT for email/LinkedIn posts/iMessage.
user_invocable: true
---

# Message Response Skill

Draft responses to messages from recruiters, networking contacts, and others.

## Triggers

- "message" / "draft message"
- "reply to [name]"
- "[name] replied" / "[name] messaged"
- "follow up with [name]"
- "respond to [name]"

## Workflow

### 1. Find the Message

Check these sources:

- **Gmail**: `gog gmail search "from:[name]"`
- **LinkedIn**: Browser automation to check messaging
- **WhatsApp**: `keryx read "Name" --limit 30` (handles dual-JID merging automatically). If multiple matches, try full name. For full message text (keryx truncates), load the `whatsapp` skill and use `wacli messages list --chat "<jid>" --after <date> --json` — parse `Text` field from JSON output.

If user says "[name] replied" without specifying platform, check Gmail and LinkedIn first before asking.

### 2. Get Context from Vault

Search the vault for background on this person:

```bash
grep -ri "[name]" ~/epigenome/chromatin/*.md
```

Grep the canonical project note before drafting — council-reviewed drafts often already exist.

Key files to check:
- `Job Hunting.md` - recruiter interactions, role discussions
- `Draft Outreach Messages*.md` - previous message drafts
- `Capco/Capco Transition.md` - Gavin/Bertie/PILON/onboarding drafts live here
- Daily notes - recent interactions

### 3. Understand the Conversation

Review:
- What was the last message Terry sent?
- What is the person asking/proposing?
- What's the relationship (recruiter, hiring manager, networking contact)?
- Any pending action items or decisions?
- **Tone calibration:** Note opener format (e.g. `"Hey Name,"` vs `"Hi Name,"` vs no opener), punctuation style, and message length from the actual thread — don't infer from vault notes alone. Match exactly.

### 4. Draft Reply

> **Consult `cursus` skill** for career communication principles before drafting any outreach to a career contact (managers, clients, recruiters, peers). Key principles: no blank asks, show don't tell, narrative consistency, network capital.

**No blank asks — research first, then ask specifically.** For any outreach where Terry is asking for something (pre-reading, advice, intro, referral), check vault for prior research before drafting. Frame every ask as a specific gap: "I've done X and Y — is there Z I'm missing?" not "any advice?" or "anything to read?". A blank ask wastes the relationship — the more specific, the more it signals preparation. Applies especially to career-critical contacts. If vault has no prior research, run `cerno` + quick web search first, then draft.

**Start from natural speech, not formal drafts.** Ask: "what would Terry actually say to this person on WhatsApp?" — then polish. Don't anchor on council-approved or vault drafts and iterate from there; those are strategy, not phrasing. Natural first, refined second.

Apply Terry's messaging preferences:
- **Minimal exclamation marks** - one at most, prefer periods
- **No redundant context** - don't repeat what they already know
- **Trim filler** - keep it tight and direct
- **Match tone** - professional but warm for recruiters
- **Disclaimers can backfire** — "no stress either way," "no offence," etc. draw attention to exactly what they deny. Use only when genuinely needed; often cutting them makes the message more confident.
- **Pre-emptive thanks is filler** — thanking before the person has done anything reads as nervous, not polite. Cut it.
- **Don't manufacture reasons for a follow-up** — if a reason isn't genuinely true and naturally occurring, leave it out. A clean question stands on its own; over-explaining signals anxiety.
- **When someone is already acting on your behalf** (checking with boss, making an intro, forwarding your profile) — close short. Acknowledge, thank, stop. Don't re-sell, don't add CTAs, don't drill into details they mentioned in passing. The process is running; more words = noise.
- **Don't say what they already know** - "didn't know X" when there's no reason you would know is filler. "Hope for good news" puts outcome pressure on the helper.

For scheduling:
- Check `[[Schedule]]` for availability
- Propose specific times, not vague "next week"
- Account for HKT timezone

### 5. Review with Censor

Before presenting to Terry, run the draft through `/censor`:
- Use `outreach` criteria for networking/cold messages
- Use `default` criteria for simple replies
- If verdict is `needs_work`: revise based on feedback (max 2 iterations)
- Ensure personalization, clear ask, and appropriate length

### 6. Present and Confirm

Show:
1. Summary of their message
2. Relevant context from vault
3. Draft reply (censor-reviewed)

Ask Terry to confirm or adjust before sending.

### 7. Update Vault

After message is sent, update:
- `Job Hunting.md` with new status/next steps
- Create follow-up reminder if needed

## Example Usage

**User**: "german replied"

**Claude**:
1. Checks Gmail → finds LinkedIn notification
2. Opens LinkedIn messaging via browser
3. Reads German's message about coffee meeting
4. Finds context in vault (ConnectedGroup recruiter, senior data PM roles)
5. Drafts reply with WhatsApp number and confirms Feb 2-5 works
6. Presents draft for approval

## Outreach Templates

See `[[Networking Outreach Templates]]` in vault for message templates and principles.

## Platform Notes

- **LinkedIn:** Browser automation (requires login). To connect with someone:
  1. Open their profile with `agent-browser open <url>`
  2. If "Connect" button is visible directly → click it
  3. If only "Follow" / "Message" visible → click "More actions" → "Invite [Name] to connect" is in that dropdown (LinkedIn hides Connect for some profiles but it's always in More)
  4. On the "Add a note?" dialog → "Send without a note" for clean connects; add note only if cold outreach needs context
  5. To send a LinkedIn DM: click "Message [Name]" on their profile
- **Gmail:** `gog gmail search/get/send` — see `gmail` skill
- **WhatsApp:** `keryx read "Name"` — see `keryx` skill. Use keryx, not wacli directly, for name-based lookups.
