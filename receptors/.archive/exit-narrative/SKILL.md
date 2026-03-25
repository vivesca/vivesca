---
name: exit-narrative
description: Practice exit narrative until bulletproof. Stress-tests "why leaving" answers with follow-up probes and principle-based feedback. Use when user says "exit narrative", "practice my exit story", "why leaving practice".
---

# Exit Narrative Simulator

Practice your "why are you leaving?" answer until it passes every time.

## Trigger

Use when:
- User says "exit narrative", "practice my exit story", "stress test my story"
- Preparing for an interview where departure will be probed
- After /debrief reveals exit narrative concerns

## Inputs

- **mode** (optional): `interactive` (default) or `batch` (for agent use)
- **target** (optional): Number of clean passes required. Default: 3

## Workflow

### Step 1: Load Context

Read `/Users/terry/notes/Why leave CITIC.md` for the approved framing and principles.

If file missing, ask Terry to briefly describe the situation.

### Step 2: The Loop

Start with: "Why are you leaving your current role?"

After each response, evaluate against 5 principles (rate each 1-5):

| Principle | Good (Pass) | Red Flag (Fail) |
|-----------|-------------|-----------------|
| **Boring** | Organizational, procedural framing | Drama, emotion, personal conflict |
| **External** | Leadership change, role evolution | "I couldn't work with..." |
| **Forward-looking** | What you want next | Dwelling on what went wrong |
| **Concise** | One clear reason, move on | Multiple justifications, over-explaining |
| **No badmouthing** | Neutral on individuals | Criticism of CIO, bank, colleagues |

**If any principle scores < 3:**
1. Provide specific feedback using formula: `[observation] + [why it matters] + [concrete fix]`
2. Ask targeted follow-up probe based on the red flag:

| If Answer Contains | Follow-Up Probe |
|-------------------|-----------------|
| Mentions of conflict | "Tell me more about that dynamic" |
| Emotion words (frustrated, difficult) | "You sound frustrated, what happened?" |
| Vague references ("changes", "challenges") | "What do you mean by 'changes'?" |
| Multiple reasons | "Can you give me the short version?" |
| Criticism of people | "How would your manager describe it?" |
| Too long (>45 seconds spoken) | "Let me stop you there—what was the core reason?" |

**If all principles score >= 4:**
- Say "That's clean. Let's try a variation."
- Ask a different angle:
  - "What would your manager say about why you're leaving?"
  - "Did they ask you to leave?"
  - "Why leave before bonus?"
  - "Was this your decision or the bank's?"

Track clean passes. After 3 consecutive clean answers: end session.

Cap at 10 questions max to prevent session drift.

### Step 3: Session Summary

```
## Exit Narrative Practice Complete

**Clean passes:** [N]
**Total questions:** [N]

### What Worked
- [Patterns that consistently passed]

### Watch Out For
- [Patterns that triggered follow-ups]

### Suggested Phrasing
- [Any refined wording that emerged]

---
After real interview: run /debrief to capture how it landed.
```

## Error Handling

- **If user response is very short**: "That was brief—interviewers often probe further. Want to expand?"
- **If user gets frustrated**: "This is practice—take a breath. Want to try a different angle?"
- **If user says "done" early**: Provide abbreviated summary with what was covered
- **If vault file missing**: Ask Terry to describe the situation briefly, then proceed

## Batch Mode (Agent-Native)

For programmatic use by other skills:

```
/exit-narrative --mode=batch --questions='["Why leaving?"]' --answers='["Growth opportunity..."]'
```

Returns structured JSON:
```json
{
  "evaluations": [
    {
      "question": "Why leaving?",
      "answer": "...",
      "scores": {"boring": 4, "external": 5, "forward": 4, "concise": 3, "no_badmouth": 5},
      "passed": true,
      "feedback": null
    }
  ],
  "summary": {"clean_passes": 1, "total": 1}
}
```

## Integration

- **From /interview-prep:** Can be called as optional sub-step
- **To /debrief:** After real interview, suggest if exit narrative concerns surface
- **With /narrative-debt:** Track which framing was used with each company

## vs Practicing with Claude Directly

| Aspect | /exit-narrative | Just asking Claude |
|--------|-----------------|-------------------|
| Structured evaluation | Yes, 5 principles | Ad hoc |
| Follow-up probing | Automatic based on flags | Manual |
| Session tracking | Counts clean passes | None |
| Reproducible | Same rubric every time | Variable |

## Examples

**User:** "exit narrative"
**Action:** Load context, ask "Why are you leaving?", evaluate, probe until 3 clean passes
**Output:** Interactive Q&A with feedback, session summary

**User:** "practice my exit story"
**Action:** Same as above
**Output:** Interactive Q&A with feedback, session summary

**User:** "stress test my story before the Stripe interview"
**Action:** Load context, run focused practice session
**Output:** Interactive Q&A, summary noting what to watch for in Stripe interview
