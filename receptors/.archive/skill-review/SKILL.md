---
name: skill-review
description: Review the current conversation to analyze skill usage, extract feedback, and directly update skills. Use after long sessions to improve skills based on feedback given during conversation.
redirect: review --mode=skills
---

# Skill Review

> **Note:** This skill has been merged into `/review`. Use `/review --mode=skills` for the same functionality.

Review the current conversation to analyze skill usage, extract feedback and corrections, and **directly update the skills**. No review notes — just fix the skills.

## When to Use

Use this skill when the user:
- Sends `/skill-review`
- Says "review my skills usage" or "what skills need updating"
- Wants to iterate on custom skills based on feedback given during conversation

## Instructions

### Step 1: Review the Conversation

Scan the entire conversation history and identify:

1. **Skills invoked** - Both built-in and custom skills used (slash commands, agent types, etc.)
2. **Negative feedback** - Moments where the user corrected, redirected, or expressed frustration
3. **Positive signals** - Things that worked well and should be preserved
4. **Workarounds** - Manual steps the user had to take that a skill could automate

### Step 2: Extract Critical Feedback

For each piece of feedback found, categorize it:

| Category | Description | Example |
|----------|-------------|---------|
| **Procedure Error** | Skill followed wrong steps | "No, don't create a new file, edit the existing one" |
| **Missing Context** | Skill lacked necessary information | "You should have checked the CLAUDE.md first" |
| **Output Format** | Wrong format or structure | "Put this in a table instead" |
| **Trigger Mismatch** | Skill triggered when it shouldn't (or vice versa) | "I didn't want the full analysis, just a quick check" |
| **New Workflow** | User described a process not covered by existing skills | "When I share a LinkedIn job, I want you to..." |

### Step 3: Analyze Iteration Direction

For each feedback item, determine the action:

| Condition | Action |
|-----------|--------|
| Feedback targets specific procedure in existing skill | **Update existing skill** |
| Feedback reveals entirely new workflow | **Create new skill** |
| Feedback is one-time preference or edge case | **No action needed** |
| Feedback applies to multiple skills | **Update CLAUDE.md** (global instructions) |

### Step 4: Propose Changes

Present proposed changes to the user before implementing:

```
## Proposed Skill Updates

### [skill-name]
**File:** `/path/to/SKILL.md`
**Change:** [what will be changed]
**Before:** [current text]
**After:** [proposed text]

Proceed with these changes?
```

Wait for user confirmation before editing any files.

### Step 5: Implement Changes

After user approves:

1. **Update existing skills** — Edit the SKILL.md file directly
2. **Create new skills** — Write new SKILL.md if needed
3. **Update CLAUDE.md** — If feedback applies globally

### Step 6: Commit and Push

Skills in `~/.claude/skills/` are symlinked from the source repo at `~/skills/`. After changes are made:

1. `cd ~/skills` (the source repo, not `.claude/skills/`)
2. `git add` the changed skill files
3. `git commit` with message describing the skill update
4. `git push` to origin

Confirm completion to the user.

## Tips

- Run this at the end of long sessions before context is lost
- If the same feedback appears multiple times across sessions, it's high priority
- Keep skill updates minimal and focused — don't over-engineer

## Files

- This skill: `/Users/terry/.claude/skills/skill-review/SKILL.md`
- Skills location: `/Users/terry/.claude/skills/`

## Reference

Inspired by [@dontbesilent12's Skill Iteration Review concept](https://x.com/dontbesilent12/status/2011828768944636266)
