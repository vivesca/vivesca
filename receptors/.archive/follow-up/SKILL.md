---
name: follow-up
description: Draft follow-up messages for stale applications or networking contacts. Use when user says "follow up", "nudge", "check in with".
redirect: message --type=followup
---

# Follow-up

> **Note:** This skill has been merged into `/message`. Use `/message --type=followup` for the same functionality.

Draft follow-up messages for stale applications or networking contacts.

## Trigger

Use when:
- Terry wants to nudge on an application or contact
- Says "follow up on [company/person]", "nudge [company]", "check in with [name]"
- During weekly reset when follow-ups are identified

## Inputs

- Company/contact name
- Type: job application or networking contact
- Last interaction date (will check vault if not provided)
- Any context on status

## Steps

### 1. Check Vault for Status

Read:
- `/Users/terry/notes/Job Hunting.md` — find the application or contact
- Any related notes

Gather:
- When Terry applied / last reached out
- Who the contact was (recruiter, hiring manager, referral)
- Current status
- Any notes on timeline they gave

### 2. Assess Timing

| Time Since Last Contact | Recommendation |
|------------------------|----------------|
| < 1 week | Too soon, wait unless they gave specific timeline |
| 1-2 weeks | Good time for first follow-up |
| 2-3 weeks | Definitely follow up |
| 3+ weeks | Follow up, but temper expectations |

If they gave a specific timeline ("we'll get back in 2 weeks"), respect it + 2-3 days buffer.

### 3. Determine Approach

**Job Application Follow-up:**
- First follow-up: Express continued interest, offer additional info
- Second follow-up: Shorter, just checking in
- Third+: Consider it cold, move on mentally

**Networking Follow-up:**
- No response to outreach: One gentle bump, then let it go
- After a call/meeting: Thank you + any promised follow-through
- Checking in after time passed: Share an update, light touch

### 4. Draft Message

Keep follow-ups SHORT. They already have context.

**Application Follow-up:**
```
Hi [Name],

I wanted to follow up on my application for [Role]. I'm still very interested in the opportunity and happy to provide any additional information.

Is there an update on the process?

Best,
Terry
```

**Post-Interview Follow-up:**
```
Hi [Name],

Thanks again for the conversation on [day]. I enjoyed learning about [specific thing discussed].

Looking forward to hearing about next steps.

Best,
Terry
```

**Networking Bump:**
```
Hi [Name],

Just bumping this in case it got buried — would still love to connect if you have a few minutes.

No worries if timing doesn't work!
```

### 5. Present & Adjust

Show the draft and:
- Confirm timing is appropriate
- Note if this is 1st, 2nd, or 3rd follow-up
- Recommend whether to follow up at all (sometimes better to let go)

### 6. Update Vault

After sending, update Job Hunting.md:
- Update last contact date
- Note follow-up sent
- Adjust status if needed

## Tips

- Less is more — short follow-ups get read
- Don't apologize for following up
- One follow-up is expected; three is pushy
- If no response after 2 follow-ups, move on
- For rejections: gracious response, ask to stay in touch
