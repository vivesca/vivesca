# feat: Reflect Skill UX Improvements

## Enhancement Summary

**Deepened on:** 2026-01-22
**Research agents used:** best-practices-researcher (x3), code-simplicity-reviewer, architecture-strategist

### Key Insights from Research

1. **Skip detection is over-engineered** — Complex heuristics (message count, correction patterns, file tracking) to save ~5 seconds. User can already say "skip" or "no" when prompted. The skill already says "If nothing significant happened, say so." DELETE.

2. **Default recommendation is marginal value** — Current summary already presents findings clearly. Adding recommendation logic requires defining "significant" vs "minor" without clear criteria. User sees the data and decides. SIMPLIFIED to just a light nudge.

3. **Post-apply summary is high value, low cost** — Confirms what changed, reduces anxiety, catches silent failures. KEEP and refine.

### Revised Scope

| Feature | Original | After Research |
|---------|----------|----------------|
| Skip detection | Complex pre-flight heuristics | **REMOVED** — over-engineered |
| Default recommendation | Decision table with thresholds | **SIMPLIFIED** — light nudge only |
| Post-apply summary | Confirmation list | **KEEP** — high value |

**Net change:** ~10 lines instead of ~25 lines

---

## Overview

Enhance the `/reflect` skill with 2 UX improvements to reduce friction at end of sessions:

1. **Light recommendation nudge** — Brief guidance after presenting findings
2. **Post-apply summary** — Confirm what actually changed

## Problem Statement

The current reflect flow requires users to evaluate findings and decide whether to apply updates. At the end of a session when energy is low, users need:

- Brief guidance on what to do (not just neutral presentation)
- Confirmation that updates were applied correctly

## Proposed Solution

### 1. Light Recommendation Nudge (Step 2)

After presenting the summary, add a one-line nudge before `AskUserQuestion`:

**Simple logic:**
- If mistakes found → "**Recommend: Apply** (mistake worth recording)"
- If nothing found → "**Recommend: Skip** (nothing significant)"
- Otherwise → No nudge (let user decide based on summary)

**Example:**
```
## Session Reflection

### Mistakes to Record
- Used grep without -n flag → will add to CLAUDE.md

### Daily Note Updates
- LLM Council improvements

**Recommend: Apply** (found 1 mistake worth recording)
```

Or when trivial:
```
## Session Reflection

### Daily Note Updates
- Quick API syntax lookup

**Recommend: Skip** (routine session)
```

**Research insight:** Keep phrasing informational, not directive. "Recommend: X" not "You should X". Include brief reason in parentheses.

### 2. Post-Apply Summary (Step 3b)

After applying updates, show confirmation:

**Template:**
```
✅ **Applied:**
- CLAUDE.md: Added 1 item to "Record Mistakes Here"
- Daily note: Created 2026-01-22.md
- Follow-ups: Added 2 items

[Committed to git]
```

**Research insights:**
- Summarize by file/action, not exhaustive detail
- Only show items actually written (skip empty)
- Include git status if applicable
- Pattern matches Terraform, kubectl confirmation style

---

## Technical Approach

### File Changes

Single file: `/Users/terry/skills/reflect/SKILL.md`

### Changes by Section

#### Step 2: Add Light Nudge

Insert after the summary template (around line 128), before the `AskUserQuestion` paragraph:

```markdown
**Add a light recommendation after the summary:**

- If mistakes found → `**Recommend: Apply** (mistake worth recording)`
- If no findings → `**Recommend: Skip** (nothing significant)`
- Otherwise → omit (user decides from summary)
```

#### Step 3: Add Confirmation (new Step 3b)

Insert after Step 3 bullet list:

```markdown
### Step 3b: Confirm Changes

After applying updates, show:

```
✅ **Applied:**
- [File]: [What changed]
- [Committed to git] or [No git changes]
```

Only list items actually written. Skip this section if nothing was applied.
```

---

## Acceptance Criteria

- [ ] Light nudge appears after summary when clear recommendation exists
- [ ] Post-apply summary shows exactly what changed
- [ ] Existing flow unchanged for normal sessions
- [ ] Total additions ~10 lines

## Implementation Notes

- All changes are instructions in SKILL.md (prompt-based, no code)
- Follow existing formatting patterns
- Keep minimal — this is UX polish, not new features

## Files Modified

| File | Change |
|------|--------|
| `/Users/terry/skills/reflect/SKILL.md` | Add nudge logic + confirmation step |

## References

- Current skill: `/Users/terry/skills/reflect/SKILL.md`
- Research: CLI confirmation patterns (Terraform, kubectl, git)
- Pattern: Existing `AskUserQuestion` usage in Step 2
