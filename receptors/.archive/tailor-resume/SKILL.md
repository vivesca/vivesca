---
name: tailor-resume
description: Generate role-specific resume bullets from master experience document. Use when user says "tailor resume", "customize CV", "resume for [role]", or wants to optimize application materials.
---

# Tailor Resume

Generate role-specific resume bullets and talking points from Terry's master experience document. Optimizes for ATS keywords and role fit.

## Trigger

Use when:
- User says "tailor resume", "customize CV", "resume for [role]"
- User shares a job URL and wants application materials
- User says "optimize resume", "ATS keywords"
- After `/evaluate-job` returns APPLY recommendation

## Inputs

- **job_url** or **job_description**: The role to tailor for (required)
- **focus** (optional): Specific areas to emphasize (e.g., "leadership", "technical")

## Workflow

1. **Extract job requirements**:
   - Navigate to job URL or parse provided JD
   - Extract: required skills, preferred qualifications, responsibilities
   - Identify key themes (leadership, technical depth, stakeholder management, etc.)

2. **Load Terry's experience**:
   - Read `/Users/terry/notes/CLAUDE.md` for background
   - Read `/Users/terry/notes/Core Story Bank.md` if exists
   - Read master CV/resume if available

3. **Identify keyword gaps**:
   | JD Keyword | Terry's Experience | Gap? |
   |------------|-------------------|------|
   | [keyword] | [matching experience] | ✅/⚠️ |

4. **Generate tailored bullets**:
   - Match Terry's experience to each requirement
   - Reframe accomplishments using JD language
   - Quantify where possible (%, $, scale)
   - Prioritize most relevant 3-5 bullets per section

5. **Highlight transferable skills**:
   - Map banking/fintech experience to target industry
   - Connect AI/ML work to role requirements
   - Surface leadership/management experience

6. **Review with Judge:**
   - Run output through `/judge` with `default` criteria
   - Check: goal_alignment, completeness, accuracy, actionable
   - If verdict is `needs_work`: revise (max 2 iterations)
   - Ensures output is specific, accurate, and actionable

7. **Output tailored materials**

## Output

```markdown
# Resume Tailoring: [Role] at [Company]

## Keyword Analysis

**Must-Have Keywords (from JD):**
- [keyword 1] — ✅ covered in [section]
- [keyword 2] — ⚠️ not explicit, add to [section]
- [keyword 3] — ✅ covered in [section]

**Missing/Weak Areas:**
- [gap] — suggest adding: "[bullet]"

## Tailored Bullets

### [Section: e.g., Professional Experience]

**Original:** [current bullet]
**Tailored:** [reframed bullet with JD keywords]

**Original:** [current bullet]
**Tailored:** [reframed bullet with JD keywords]

### [Section: e.g., Skills]

**Add:** [skills from JD that Terry has but aren't listed]

## Cover Letter Points

Key angles to emphasize:
1. [Connection to company mission/product]
2. [Relevant accomplishment with metrics]
3. [Why this role specifically]

## Interview Talking Points

Prepare stories for:
- [Requirement 1] → [Story from bank]
- [Requirement 2] → [Story from bank]
```

## Error Handling

- **If JD inaccessible**: Ask user to paste job description
- **If master CV not found**: Work from CLAUDE.md context
- **If role very different from background**: Flag stretch areas, suggest bridge language
- **If ATS likely strict**: Prioritize exact keyword matches over synonyms

## Tips

- Use exact JD phrasing where Terry has matching experience
- Lead bullets with action verbs from JD (e.g., "Led", "Developed", "Scaled")
- Quantify everything possible: team size, budget, impact metrics
- For stretch roles, emphasize transferable skills and learning agility
- Keep bullets to 1-2 lines max

## Integration

This skill works well in sequence:
1. `/evaluate-job [url]` → APPLY
2. `/tailor-resume [url]` → Generate materials
3. `/message --type=cold` → Outreach to contact at company

## Files

- Master context: `/Users/terry/notes/CLAUDE.md`
- Story bank: `/Users/terry/notes/Core Story Bank.md`
- Job tracking: `/Users/terry/notes/Job Hunting.md`
