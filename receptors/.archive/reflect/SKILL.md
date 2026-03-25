---
name: reflect
description: End-of-session reflection to capture mistakes, preferences, daily updates, workflow improvements, and follow-up tasks. Use at the end of conversations to compound learnings.
redirect: review --mode=session
---

# Reflect

> **Note:** This skill has been merged into `/review`. Use `/review --mode=session` for the same functionality.

End-of-session reflection that reviews the conversation and updates relevant files with anything worth capturing.

## When to Use

- End of a productive session
- After discovering something that should be documented
- When Terry says "let's wrap up" or "end of session"
- Proactively suggest at natural stopping points

## What to Capture

### 1. Mistakes to Record

Things Claude got wrong that should go in CLAUDE.md's "Record Mistakes Here" section.

Look for:
- Corrections Terry made ("No, do it this way...")
- Repeated clarifications needed
- Wrong assumptions or approaches
- Tools used incorrectly

**Format for CLAUDE.md:**
```
- [Brief description of mistake and correction]
```

### 2. Preferences Learned

Patterns in how Terry likes things done that aren't already documented.

Look for:
- Explicit preferences stated ("I prefer X")
- Implicit patterns (consistently choosing one approach over another)
- Format or style preferences
- Tool preferences

**Add to relevant CLAUDE.md section or create new one if needed.**

### 3. Workflow Improvements

Skills, patterns, or automations worth documenting.

Look for:
- Multi-step processes that could become skills
- Workarounds that should be formalized
- Successful patterns to replicate

**Action:** Create new skill or update existing one, or add to CLAUDE.md.

### 4. Follow-up Tasks

Things to do next session or soon.

Look for:
- Unfinished work
- "We should do X later" mentions
- Blocked tasks waiting on external input
- Ideas to explore

**Add to daily note or a dedicated follow-ups section.**

### 5. Compound Check

Anything worth extracting to a reusable artifact? (Per Dan Shipper's compound engineering: if no file is edited, compounding didn't happen.)

Look for:
- **Core Story Bank addition** — New STAR story, interview insight, or reframeable experience
- **Template/script worth saving** — Outreach message that worked, question that landed well
- **Pattern worth documenting** — Decision heuristic, objection handling, market insight

**Action:** Update the relevant Obsidian note or create a new artifact. Be selective — only compound things you'd reuse 3+ times.

### 6. Daily Note Updates

Activity worth logging in the daily note (`/Users/terry/notes/YYYY-MM-DD.md`).

Categories:
- **Job search activity** — applications sent, responses received, interviews scheduled
- **Key learnings** — technical insights, career realizations
- **Tools/skills set up** — new capabilities configured
- **Mood check** — optional, only if naturally came up

## Instructions

### Step 1: Scan Conversation

Review the full conversation and extract items for each category above. Be selective — only capture things that are:
- Recurring (happened more than once)
- Significant (would meaningfully improve future sessions)
- Actionable (can be documented or fixed)

### Step 2: Present Summary

Show Terry what you found in a concise summary, then use `AskUserQuestion` to let him choose what to do:

```
## Session Reflection

### Mistakes to Record
- [item] → will add to CLAUDE.md

### Preferences Learned
- [item] → will add to [location]

### Workflow Improvements
- [item] → [proposed action]

### Follow-up Tasks
- [item]

### Compound Check
- [ ] Core Story Bank addition?
- [ ] Template/script worth saving?
- [ ] Pattern worth documenting?

### Daily Note Updates
- [items for today's note]
```

**Add a light recommendation after the summary:**

- If mistakes found → `**Recommend: Apply** (mistake worth recording)`
- If no findings → `**Recommend: Skip** (nothing significant)`
- Otherwise → omit (user decides from summary)

Then use `AskUserQuestion` with options like:
- "Apply all" — Update daily note, CLAUDE.md (if mistakes/preferences), skills (if improvements), and compound artifacts
- "Skip" — No updates, end session
- "Let me pick" — (Other) for selective updates

**Note:** Compound check items (story bank, templates, patterns) and skill improvements should ideally be applied during the session when discovered. Reflection confirms they were captured and creates the daily note summary.

### Step 3: Apply Updates (after confirmation)

1. **CLAUDE.md mistakes** — Append to "Record Mistakes Here" section
2. **CLAUDE.md preferences** — Add to relevant section
3. **Daily note** — Create or update `/Users/terry/notes/YYYY-MM-DD.md`
4. **Skills** — Create/update in `/Users/terry/skills/`
5. **Follow-ups** — Add to daily note under "## Follow-ups"

### Step 3b: Confirm Changes

After applying updates, show:

```
✅ **Applied:**
- [File]: [What changed]
- [Committed to git] or [No git changes]
```

Only list items actually written. Skip this section if nothing was applied.

### Step 4: Commit Changes

```bash
# If CLAUDE.md changed
cd ~/claude-config && git add -A && git commit -m "Update CLAUDE.md from session reflection" && git push

# If skills changed
cd ~/skills && git add -A && git commit -m "Update skills from session reflection" && git push
```

## Tips

- Run this before ending long sessions to avoid losing context
- If nothing significant happened, say so — don't force updates
- Keep entries concise and actionable
- Daily notes don't need git commits (Obsidian vault)

## Files

- This skill: `/Users/terry/skills/reflect/SKILL.md`
- CLAUDE.md: `/Users/terry/CLAUDE.md`
- Daily notes: `/Users/terry/notes/YYYY-MM-DD.md`
- Skills: `/Users/terry/skills/`
