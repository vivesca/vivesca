---
name: debrief
description: Capture signals from interviews and recruiter calls. Updates Market Signals in Job Hunting.md.
user_invocable: true
---

# Debrief

Post-interview/call signal extraction. Captures what landed, what got pushback, and any persona mismatches — then updates the Market Signals section in Job Hunting.md.

This is the closed-loop feedback mechanism that makes your positioning smarter over time.

## Trigger

Use when:
- Terry says "debrief", "how did that go", "let's capture that"
- After any interview (phone, video, onsite)
- After meaningful recruiter conversations
- When Terry shares observations about a recent interaction

## Inputs

- **company**: Company name
- **role**: Role title (if known)
- **type**: Interview stage or call type (HR screen, HM interview, recruiter call, etc.)
- **date**: When it happened (default: today)

## Workflow

1. **Gather raw observations** (conversational):
   - What questions did they ask?
   - What seemed to resonate? (leaned in, asked follow-ups, positive reactions)
   - What got pushback or skepticism?
   - Any surprising questions or topics?
   - How did they react to your banking background?
   - Any signals about next steps?

2. **Extract structured signals**:

   **Objections** — Things that got pushback:
   - Quote or paraphrase the concern
   - Tag it: `#domain-mismatch`, `#title-concern`, `#technical-gap`, `#culture-fit`, `#salary`, `#overqualified`, `#underqualified`, `#experience-gap`

   **Wins** — Things that landed well:
   - Quote or paraphrase what resonated
   - Tag it: `#quantified-impact`, `#governance-angle`, `#production-experience`, `#stakeholder-management`, `#banking-credibility`, `#genai-experience`

   **Persona Mismatches** — Role expectation vs. your positioning:
   - What they seemed to want vs. how you presented
   - Learning for future similar roles

3. **Update vault files**:
   - Add rows to Market Signals tables in [[Job Hunting]]
   - Update Positioning Insights if pattern emerges
   - Update the specific role's status in Applied Jobs

4. **Update interviewer profile**:
   - `/counter-intel` (update mode) — Update interviewer profile with signals
   - Note which stories were told for future reference

5. **Suggest prep adjustments**:
   - If an objection is recurring, suggest reframing
   - If a hook consistently lands, note to emphasize it
   - Update Core Story Bank if relevant

## Integration

This skill integrates with:
- `/counter-intel` — Updates interviewer profiles with new signals
- [[Interviewer Profiles]] — Central storage for interviewer intel

## Error Handling

- **If Terry doesn't remember details**: Focus on overall impression and any standout moments
- **If it went poorly**: Still valuable signal — capture what didn't work

## Output

**Chat summary:**
```
## Debrief: [Company] - [Role] ([Date])

**Stage:** [Interview type]

**Wins:**
- [What landed] → added to Market Signals

**Objections:**
- [What got pushback] → added to Market Signals

**Next Steps:**
- [What's expected to happen next]

**Positioning Adjustment:**
- [Any suggested changes based on this interaction]
```

**Updates made:**
- Market Signals tables in Job Hunting.md
- Role status in Applied Jobs (if applicable)

## Examples

**User**: "Just finished the Capco interview, let's debrief"
**Action**: Ask about what questions came up, what landed, what got pushback
**Output**: Structured signal capture, updates to Job Hunting.md

**User**: "The KPMG call was interesting — they seemed concerned about my lack of consulting experience"
**Action**: Capture objection, suggest reframing for future consulting roles
**Output**: Add to Market Signals with #experience-gap tag, suggest positioning adjustment
