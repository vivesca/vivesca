---
name: narrative-debt
description: Track stories told, detect contradictions. Use when prepping for next round at same company or reviewing interview consistency. Triggers on "narrative debt", "what stories did I tell", "consistency check".
---

# Narrative Debt

Track stories told to each company across interview rounds. Detect contradictions and ensure narrative consistency.

## Purpose

Track what you've said so YOU stay consistent. This skill:
- Keeps your numbers/details straight across rounds (88% not 85%)
- Flags if you told contradictory versions of the same story
- Provides quick reference before interviews

**Note:** Different interviewers rarely compare story details — they pass thumbs up/down, not transcripts. Don't overthink "avoiding repetition." Tell whatever story fits the question.

## Trigger

Use when:
- User says "narrative debt", "what did I tell them", "consistency check"
- Prepping for next round at a company (auto-trigger from `/interview-prep`)
- After debrief to log stories told

## Inputs

- **company**: Company name (required)
- **mode** (optional): "check" (review past) or "log" (add new story)

## Workflow

### Mode: Check (Pre-Interview)

1. **Read story log**:
   - [[Story Telling Log]] → Company section
   - Any interview notes for this company

2. **Build story history**:
   | Round | Interviewer | Stories Told | Key Points |
   |-------|-------------|--------------|------------|
   | 1st | [Name] | [Story] | [Emphasis] |

3. **Check for conflicts**:
   - Contradictory details (dates, numbers, outcomes) → Warning
   - Same story, wildly different framing → Note for consistency

4. **Output key facts to keep consistent** (the actual value)

### Mode: Log (Post-Interview)

1. **Capture stories told**:
   - Which stories were used
   - Key points emphasized
   - Interviewer reactions

2. **Update [[Story Telling Log]]**

3. **Check for new conflicts**

## Output

**Check Mode:**
```markdown
# Narrative Debt: [Company]

## Stories Already Told

| Round | Date | Interviewer | Story | Emphasis |
|-------|------|-------------|-------|----------|
| [Round] | [Date] | [Name] | [Story] | [Key points] |

## Conflict Check
- ✅ No contradictions detected
- ⚠️ [Story] told with different [metric/date/etc.] in rounds [X] and [Y]

## Recommendations for Next Round
1. **Use:** [Story] — complements prior emphasis on [X]
2. **Use:** [Story] — addresses concern about [X]
3. **Avoid:** [Story] — already told twice

## Story Freshness
- [Story]: Used [X] times at this company
- [Story]: Not yet used — good candidate
```

**Log Mode:**
```markdown
# Logged to Story Telling Log

| Date | Round | Interviewer | Story | Emphasis |
|------|-------|-------------|-------|----------|
| [Date] | [Round] | [Name] | [Story] | [Key points] |

## Updated Company Total
- Stories told at [Company]: [X]
- Unique stories: [Y]
```

## Conflict Detection Rules

Flag when:
- Same story has different quantified outcomes (88% vs 85% precision)
- Different timelines mentioned (2 months vs 3 months)
- Contradictory roles (I led vs I supported)
- Different team sizes (team of 5 vs team of 3)

## Integration

- **`/interview-prep`**: Auto-runs narrative debt check
- **`/debrief`**: Prompts to log stories told
- **[[Core Story Bank]]**: Reference for canonical story versions

## Examples

**User**: "narrative debt for Capco"
**Action**: Pull Capco story log, check for conflicts, recommend for next round
**Output**: Summary of stories told, any conflicts, recommendations

**User**: "I told them about the AML model in the Subashini interview"
**Action**: Log story to Story Telling Log, check against prior rounds
**Output**: Confirmation, any conflict warnings
