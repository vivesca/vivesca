---
name: interview-prep
description: Prepare for interviews — company research, story matching, question prediction. "interview prep"
user_invocable: true
---

# Interview Prep

Prepare for an upcoming interview by researching the company, pulling relevant stories, and matching experience to role requirements.

## Trigger

Use when:
- Terry has an interview scheduled
- User says "prep for [company]", "interview prep", "prepare for interview"

## Inputs

- **company**: Company name (required)
- **role**: Role title (required)
- **stage** (optional): Phone screen, hiring manager, technical, etc.
- **date** (optional): Interview date/time

## Workflow

1. **Read context files**:
   - `/Users/terry/notes/CLAUDE.md` — personal context
   - `/Users/terry/notes/Core Story Bank.md` — prepared stories (if exists)
   - `/Users/terry/notes/Interview Preparation.md` — general prep notes (if exists)
   - `/Users/terry/notes/Job Hunting.md` — notes on this role/company

2. **Research interviewer** (if name known):
   - `/counter-intel` — Research interviewer background and style
   - Search vault for past interactions with this person

3. **Research company** via web search:
   - **Recent news** — last 3-6 months, anything notable
   - **Tech stack** — especially data/ML infrastructure
   - **Culture signals** — values, work style, reviews
   - **Key people** — who Terry might meet, their background
   - **Challenges** — problems they're likely solving

4. **Get fresh AI news** (for AI-forward companies):
   - Run `/ai-news quick` for recent developments and talking points
   - Especially useful if interview is >1 week away
   - Shows awareness of industry trends

3. **Map role to experience**:
   | Role Requirement | Terry's Relevant Experience |
   |------------------|----------------------------|
   | [Requirement] | [Matching experience/story] |

4. **Select 3-5 stories** from Core Story Bank most relevant to this role
   - Cross-check with narrative debt log to avoid repetition
   - Prioritize stories NOT yet told to this company

5. **Generate 5-7 questions to ask** (tailored to research findings):
   - Role-specific (day-to-day, expectations, success metrics)
   - Team/culture (how team works, collaboration)
   - Company direction (strategy, challenges, growth)

6. **Flag potential concerns**:
   - Gaps or transitions to address
   - Why leaving current role (clean narrative)
   - Salary expectations if likely to come up
   - Red flags from research

7. **Review with Judge:**
   - Run prep output through `/judge` with `technical` criteria
   - Check: completeness, appropriate_depth, actionable
   - If verdict is `needs_work`: revise (max 2 iterations)
   - Ensures prep is comprehensive and interview-ready

8. **Save prep notes** to vault (optional)

## Related Skills

- `/counter-intel` — Interviewer research and profile building
- `/debrief` — Capture signals after the interview
- `/ai-news` — Fresh AI news for talking points
- `vault-pathfinding` — Vault paths for reading context files

## Error Handling

- **If Core Story Bank doesn't exist**: Note what stories Terry should prepare
- **If company info sparse**: Focus on role requirements and general prep
- **If interview is soon**: Focus on essentials; if days away, go deeper

## Output

**Template:**
```markdown
# Interview Prep: [Company] - [Role]

## Company Briefing
[Concise summary — recent news, tech stack, culture]

## Role Mapping
| Requirement | Your Experience |
|-------------|-----------------|

## Stories to Use
1. [Story name] — [why relevant]

## Questions to Ask
1. [Question]

## Watch Out For
- [Concern and how to address]

## Next Steps
- [Any prep actions before interview]
```

**Location:** `/Users/terry/notes/Interview Prep - [Company].md`

## Examples

**User**: "prep for Stripe"
**Action**: Research Stripe, map experience, select stories, generate questions
**Output**: Interview prep note saved to vault, summary in chat
