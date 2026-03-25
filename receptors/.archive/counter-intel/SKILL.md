---
name: counter-intel
description: Build interviewer profiles and track negotiation signals before meetings.
user_invocable: true
---

# Counter-Intel

Research interviewers and build profiles for better preparation and negotiation leverage.

## Purpose

Every interaction with an interviewer reveals signals:
- Their priorities and concerns
- Company urgency (or lack thereof)
- Negotiation leverage points
- Personal style and preferences

This skill systematically captures and uses these signals.

## Trigger

Use when:
- User says "counter-intel [name]", "research [interviewer]"
- Before an interview (auto-trigger from `/interview-prep`)
- Preparing for offer negotiation
- After interview to capture signals

## Inputs

- **name**: Interviewer name (required)
- **company**: Company (required)
- **mode** (optional): "research" (pre-interview) or "update" (post-interview)

## Workflow

### Mode: Research (Pre-Interview)

1. **LinkedIn scan** (via browser if available):
   - Current role and tenure
   - Career history
   - Education
   - Posts/articles (style, interests)

2. **Web search**:
   - Speaking engagements
   - Published content
   - News mentions

3. **Vault check**:
   - [[Interviewer Profiles]] for prior interactions
   - Shared connections from [[Contact Index]]

4. **Build profile**:
   - Background summary
   - Likely priorities (based on role)
   - Conversation hooks (shared interests, connections)
   - Interview style (if known)

### Mode: Update (Post-Interview)

1. **Capture interaction signals**:
   - What questions did they ask?
   - What seemed to matter to them?
   - How did they react to your answers?
   - Any urgency signals?
   - Negotiation hints?

2. **Update [[Interviewer Profiles]]**

3. **Extract negotiation intel**:
   - "We've been searching for 6 months" → leverage
   - "Budget is tight" → lower expectations
   - "You're perfect for this" → confidence
   - "We have other candidates" → pressure tactic?

## Output

**Research Mode:**
```markdown
# Counter-Intel: [Name] at [Company]

## Background
- **Current role:** [Title] at [Company]
- **Tenure:** [X years/months]
- **Career path:** [Summary]
- **Education:** [If relevant]

## Likely Priorities
Based on their role, they probably care about:
1. [Priority]
2. [Priority]

## Conversation Hooks
- [Shared connection, interest, or experience]

## Interview Style
- [If known from prior interactions]

## Preparation Notes
- Emphasize: [What to highlight]
- Address: [Potential concerns from their perspective]
```

**Update Mode:**
```markdown
# Updated: [Name] at [Company]

## Interaction Logged
- **Date:** [Date]
- **Stage:** [Interview round]
- **Duration:** [If known]

## What Mattered to Them
1. [Topic they focused on]
2. [Questions they asked]

## Style Notes
- [How they conducted the interview]

## Negotiation Intel
| Signal | Implication |
|--------|-------------|
| [What they said] | [What it means] |

## Profile Updated in [[Interviewer Profiles]]
```

## Integration

- **`/interview-prep`**: Auto-runs counter-intel research
- **`/debrief`**: Prompts to update profiles
- **[[Interviewer Profiles]]**: Central storage

## Research Sources (Priority Order)

1. **LinkedIn** (requires browser): Most reliable for current role/background
2. **Web search**: Articles, speaking, news
3. **Company website**: About page, leadership
4. **Vault**: Prior interactions

## Examples

**User**: "counter-intel Marco Chiu"
**Action**: Research Marco Chiu at Capco, build profile
**Output**: Background, priorities, conversation hooks

**User**: "Update profile for Subashini — she seemed really focused on governance"
**Action**: Add signal to Interviewer Profiles
**Output**: Updated profile, negotiation intel extracted
