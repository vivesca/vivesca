---
name: review
description: Unified reflection skill for daily notes, session capture, and skill updates. Use when user says "review", "daily", "reflect", "end of day", "end of session", or "skill review".
---

# Review

Unified reflection skill combining daily notes, session capture, and skill updates. Use `--mode` to select type.

## Trigger

Use when:
- User says "review", "daily", "reflect", "end of day"
- User says "end of session", "wrap up"
- User says "skill review", "update skills"

## Inputs

- **mode**: `daily` | `session` | `skills` (required, or inferred from context)
- **date** (optional): For daily mode, defaults to today

## Modes

### Daily Mode (`/review --mode=daily`)

End-of-day reflection capturing job search progress, learnings, and mood.

**Workflow:**
1. Get today's date (YYYY-MM-DD, HKT timezone)
2. Scan recent conversation for today's activity
3. Check for existing note at `~/notes/YYYY-MM-DD.md`
4. Walk through sections conversationally:
   - **Job Search Activity**: Applications, status updates, pipeline
   - **Learnings**: Insights about job search, interviews, companies
   - **Tools/Skills**: New tools or skills practiced
   - **Mood**: How are you feeling? (1-5 or word)
5. Create or update daily note
6. **Check if anything needs follow-up tomorrow**

**Output template:**
```markdown
# YYYY-MM-DD

## Job Search Activity
- Applied:
- Status updates:
- Next up:

## Learnings
-

## Tools/Skills
-

## Mood

```

---

### Session Mode (`/review --mode=session`)

End-of-session capture of mistakes, preferences, and follow-ups.

**Workflow:**
1. Scan full conversation for:
   - **Mistakes**: Corrections Terry made, wrong assumptions
   - **Preferences**: Patterns in how Terry likes things done
   - **Follow-ups**: Unfinished work, "do later" mentions
   - **Workflow improvements**: Patterns that should become skills

2. Present summary:
```
## Session Reflection

### Mistakes to Record
- [item] → will add to MEMORY.md or daily note

### Preferences Learned
- [item] → will add to [location]

### Follow-up Tasks
- [item]

### Workflow Improvements
- [item] → [proposed action]

Proceed with updates?
```

3. After confirmation, apply updates:
   - Mistakes/learnings → update MEMORY.md or daily note
   - Daily note → create/update with follow-ups
   - Skills → create/update as needed

4. Commit changes:
```bash
cd ~/skills && git add -A && git commit -m "Update skills" && git push
```

---

### Skills Mode (`/review --mode=skills`)

Review conversation and update skills based on feedback.

**Workflow:**
1. Scan conversation for:
   - Skills invoked (slash commands, agent types)
   - Negative feedback (corrections, redirections)
   - Positive signals (things that worked)
   - Workarounds (manual steps a skill could automate)

2. Categorize feedback:
   | Category | Description |
   |----------|-------------|
   | Procedure Error | Skill followed wrong steps |
   | Missing Context | Skill lacked necessary info |
   | Output Format | Wrong format or structure |
   | Trigger Mismatch | Triggered when it shouldn't (or vice versa) |
   | New Workflow | Process not covered by existing skills |

3. Propose changes:
```
## Proposed Skill Updates

### [skill-name]
**File:** `/path/to/SKILL.md`
**Change:** [what will be changed]
**Before:** [current text]
**After:** [proposed text]

Proceed with these changes?
```

4. After approval, edit skills and commit:
```bash
cd ~/skills && git add -A && git commit -m "Update skills from review" && git push
```

## Error Handling

- **If history.jsonl unreadable**: Skip chat scan, proceed with manual input
- **If note already exists**: Update rather than overwrite
- **If nothing significant in session**: Say so, don't force updates
- **If skill file not found**: Create new skill if warranted

## Files

- Daily notes: `~/notes/YYYY-MM-DD.md`
- Job context: `~/notes/CLAUDE.md`
- OpenClaw memory: `~/clawd/MEMORY.md`
- Skills: `~/skills/`

## Migration Note

This skill replaces:
- `/daily` → use `/review --mode=daily`
- `/reflect` → use `/review --mode=session`
- `/skill-review` → use `/review --mode=skills`

The old skills are kept for backwards compatibility but will redirect here.
