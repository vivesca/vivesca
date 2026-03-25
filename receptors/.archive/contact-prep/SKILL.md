---
name: contact-prep
description: Surface past interactions before calls. Use when user says "prep for [contact name]", "call with [name]", or before any scheduled networking call.
---

# Contact Prep

Build a relationship brief before calls by surfacing all past interactions, topics discussed, and context.

## Trigger

Use when:
- Terry has a call scheduled with a contact
- User says "prep for [name]", "call with [name]", "meeting with [name]"
- Before networking coffee/lunch

## Inputs

- **name**: Contact name (required)
- **context** (optional): What the call is about

## Workflow

1. **Search vault for contact**:
   - Check [[Contact Index]] for quick lookup
   - Grep vault for name mentions
   - Search chat history (`~/.claude/history.jsonl`) for prior discussions
   - Check WhatsApp/LinkedIn references in notes

2. **Pull linked notes**:
   - Any dedicated notes (e.g., `[[Luna Yu - WhatsApp Exchange]]`)
   - Mentions in [[Job Hunting]] (Active Recruiter Conversations, etc.)
   - Interview notes if they've interviewed you

3. **Build relationship timeline**:
   - First contact date
   - All interactions (calls, messages, emails)
   - Key topics discussed
   - Outcomes (referrals made, roles discussed, etc.)

4. **Extract context signals**:
   - What did they care about last time?
   - Any pending items (you owe them something, they owe you something)
   - Their situation (new role, busy period, etc.)
   - Shared connections

5. **Output prep brief**

## Output

**Template:**
```markdown
# Contact Prep: [Name]

## Relationship Summary
- **Organization:** [Current company/role]
- **How you know them:** [Recruiter, former colleague, etc.]
- **First contact:** [Date]
- **Last contact:** [Date] — [brief summary]

## Interaction History
| Date | Type | Key Points |
|------|------|------------|
| [Date] | [Call/Message/Meeting] | [Summary] |

## Context for This Call
- **Pending from last time:** [Any follow-ups]
- **Their recent activity:** [If known]
- **Your agenda:** [What you want from this call]

## Talking Points
1. [Opening — reference last interaction]
2. [Main topic]
3. [Ask/request]

## Don't Forget
- [Any sensitive context or things to avoid]
```

## Error Handling

- **If contact not in vault**: Search chat history, ask Terry for context
- **If sparse history**: Note this is a newer relationship, focus on available info
- **If multiple people with same name**: Ask for clarification

## Integration

- Updates [[Contact Index]] after call (via `/debrief`)
- Links to [[Interviewer Profiles]] if contact has interviewed Terry
- For important meetings, use `/llm-council --social` to deliberate on approach, questions to ask, and things to avoid

## Examples

**User**: "prep for Luna"
**Action**: Search vault for Luna Yu, pull WhatsApp exchange, summarize relationship
**Output**: Prep brief with history, context, and talking points

**User**: "I have a call with German from ConnectedGroup tomorrow"
**Action**: Search for German Cham, pull recruiter conversation history
**Output**: Prep brief noting coffee scheduled, AI roles discussed
