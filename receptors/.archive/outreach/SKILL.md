---
name: outreach
description: Draft personalized networking messages to contacts for job search. Use when user says "draft outreach", "network with", "reach out to".
redirect: message --type=warm
---

# Outreach

> **Note:** This skill has been merged into `/message`. Use `/message --type=warm` or `/message --type=cold` for the same functionality.

Draft personalized networking messages to contacts for job search.

## Trigger

Use when:
- Terry wants to reach out to a contact
- Says "draft outreach to [name]", "network with [name]", "message [name]"

## Inputs

- Contact name
- How Terry knows them (if not in vault)
- Purpose: catch-up, ask for referral, request intro, informational chat
- Channel: LinkedIn, email, WhatsApp (affects tone/length)

## Steps

### 1. Check Vault for Context

Look for the contact in:
- `/Users/terry/notes/Job Hunting.md` — networking section
- Any linked notes like `[[Contact Name]]`
- Search vault for mentions

Gather:
- How Terry knows them
- Last interaction
- Their current role/company
- Any shared history or mutual connections

### 2. Research Contact (if needed)

If not enough context in vault, offer to look up:
- Current role on LinkedIn (via web search)
- Recent activity or news
- Mutual connections or shared experiences

### 3. Determine Message Strategy

Based on purpose and relationship:

| Relationship | Approach |
|--------------|----------|
| Close contact | Direct ask is fine |
| Former colleague | Warm re-connection + ask |
| Weak tie | Value-first or soft ask |
| Cold contact | Need a hook (mutual connection, shared interest) |

### 4. Draft Message

Tailor to channel:

**LinkedIn** (keep short, ~100 words max):
- Brief context on connection
- Specific ask or reason for reaching out
- Easy call-to-action

**Email** (can be slightly longer):
- Subject line that gets opened
- Personal connection point
- Clear purpose
- Specific ask with easy next step

**WhatsApp** (casual, brief):
- Conversational tone
- Get to point quickly

### 5. Present Draft

Show the draft with:
- Suggested subject line (for email)
- The message
- Any notes on timing or follow-up

Ask Terry if he wants adjustments before sending.

### 6. Log in Vault

After Terry sends, offer to update Job Hunting.md:
- Add to networking section if not there
- Update last contact date
- Note the purpose/status

## Templates

### Warm Reconnection
```
Hi [Name],

Hope you're doing well! It's been a while since [shared context].

I'm currently exploring new opportunities in [area] and thought of you given your experience at [company/in field]. Would love to catch up briefly if you have 15-20 minutes sometime.

[Sign-off]
```

### Referral Ask (to someone you know)
```
Hi [Name],

I saw [Company] is hiring for [Role] and it caught my attention because [specific reason].

I know you're connected to [person/team there] — would you be open to making an intro? Happy to send a blurb you can forward.

Thanks!
```

### Informational Chat Request
```
Hi [Name],

I've been following [Company]'s work on [specific thing] and I'm curious to learn more about [aspect].

Would you have 20 minutes for a quick chat? I'd love to hear your perspective on [specific question].

[Sign-off]
```

## Tips

- Specific > generic. Reference something real.
- Make the ask easy to say yes to (short call, quick intro)
- Don't over-explain why you're job hunting
- For Hong Kong contacts, adjust formality as appropriate

## Style Refinement (Lessons Learned)

**Match their style:**
- If they wrote "Wed", use "Wed" not "Wednesday"
- If they're casual, be casual. If formal, match it.
- Mirroring signals you're on the same wavelength.

**Opener choices:**
- "Thanks, [Name]!" > "Great to hear back!" — uses their name, avoids "wow you replied" energy
- "Sounds great!" is clean and neutral

**Don't over-optimize:**
- If you're generating 5+ alternatives for a 2-sentence message, stop. The original was probably fine.
- `/ask-llms` for quick message feedback on routine drafts
- `/llm-council --social` for high-stakes outreach (senior contacts, critical asks). Can over-engineer simple messages.

**Peer vs senior dynamics:**
- Same title at bigger company = effectively senior. Small deference signals (going to them, letting them pick time/place) are appropriate.
- Don't time-box peer coffees ("20-30 mins" creates junior energy). Let it flow.
