---
name: skill-review
description: Monthly review of skills for staleness, drift, and gaps. Use when skills feel out of sync or on first Friday of month. "skill review", "review skills", "skill audit"
effort: high
user_invocable: true
---

# Skill Review

Periodic audit to catch skill drift, identify gaps, and prune unused skills.

## Trigger

- First Sunday of the month
- When skills feel stale or routing seems off
- After major vault reorganization

## Workflow

### 1. Inventory Check

```bash
ls -la /home/vivesca/skills/*/SKILL.md | wc -l
ls -la /home/vivesca/.claude/skills/*/SKILL.md | wc -l
```

Count skills in both locations. Flag any missing symlinks.

**Budget check** — estimate character usage vs the configured limit:
```bash
# Skills in budget (excludes disable-model-invocation: true)
grep -rL 'disable-model-invocation: true' /home/vivesca/skills/*/SKILL.md | wc -l
# Rough estimate: in-budget count × 309 chars (200 avg desc + 109 overhead)
# Note: SLASH_COMMAND_TOOL_CHAR_BUDGET is a no-op since v2.1.32 — auto-scales at 2% of context window
# Sonnet 4.6 Max (200k) = ~4k token budget. Aim to reduce via consolidation.
# Full reference: ~/docs/solutions/ai-agent-skill-tool-count-research.md
```

### 2. Usage Scan

Search recent chat history for skill invocations. **Important:** Count BOTH explicit `/name` invocations AND keyword triggers — most skills are triggered by natural language, not slash commands. Counting only slash invocations drastically undercounts usage (e.g. quorate showed 0 slash but ~300 keyword triggers).

```python
# Slash invocations
import json, re, collections
counts = collections.Counter()
with open('/home/vivesca/.claude/anam.jsonl') as f:
    for line in f:
        data = json.loads(line)
        msg = data.get('display', '').lower()
        for m in re.findall(r'(?:^|\s)/([a-z][a-z0-9-]+)', msg):
            counts[m] += 1

# Keyword triggers (add patterns for high-value skills)
keywords = {
    'quorate': r'ask.llms|quorate|consilium|multi.llm|council',
    'gmail': r'check.*email|inbox|gmail',
    'whatsapp': r'whatsapp|check.*messages',
    'todo': r'todo|add.*todo|check.*todo',
    'oura': r'oura|sleep.*score|how.*sleep',
    'message': r'draft.*reply|draft.*message',
    'music': r'play.*music|spotify|sonos',
}
```

Identify:
- **Frequently used** — Working well, keep
- **Never used** — Consider deprecating or improving description
- **Often corrected** — Needs refinement

### 3. Memory/Config Bloat Check

```bash
wc -l ~/.claude/projects/-Users-terry/memory/MEMORY.md ~/CLAUDE.md
```

| File | Threshold | Action |
|------|-----------|--------|
| MEMORY.md | >150 lines | Audit for tool-specific content that belongs in skills |
| CLAUDE.md | >160 lines | Audit for detailed content that belongs in skills or docs/solutions |

If over threshold: scan each section and ask "is this a behavioral rule (stays) or tool-specific reference (move to skill)?"

### 4. Drift Detection

For each active skill, check:

| Check | How |
|-------|-----|
| **Vault references valid?** | Do paths in skill still exist? |
| **Vocabulary aligned?** | Does skill terminology match current vault notes? |
| **Workflow still accurate?** | Has the process changed since skill was written? |
| **Context shifted?** | Has a hook, tool, or other skill made parts of this skill redundant? A component can be correct but no longer worth its weight. See `~/docs/solutions/patterns/tightening-pass.md`. |
| **Description trigger timing?** | Does the description fire at the *earliest useful moment* — when the uncertainty exists — or only after the decision is already made? A skill consulted too late is a skill not consulted. |

**Open question (unresolved as of 2026-03-04):** MEMORY.md vs skill description — which is more reliable for behavioral nudges?
- MEMORY.md: always in context for Claude Code, but read reactively, truncates past line 200, easy to miss in a long list
- Skill description: fires at a specific trigger, but only if the description matches the right moment — too late = never loaded
- Current working hypothesis: skill descriptions are more reliable *if* the trigger is right; MEMORY.md is the fallback for patterns that don't have a natural trigger point
- Revisit this question each review — if skills are consistently being loaded too late or missed, the system needs a structural fix

### 5. Session Quality Review

Audit wrap output quality to catch skill drift before it compounds. Run once per monthly review.

**Extract a sample:**
```bash
evolvo              # 30-day window, 15-sample spread (default)
evolvo --days 90    # extend to 90 days for thorough monthly review
```

**Evaluate each sampled output against:**

| Signal | Healthy | Flag if |
|--------|---------|---------|
| **Narrative specificity** | Names tools, decisions, outcomes | Generic ("light session", "routine work") |
| **Multi-legatum rate** | <15% of sessions | >25% — skip gate not firing |
| **Pre-wrap block** | ⚠/✓ mix, dirty repos caught | Always "all clear" (may be skipping) |
| **Step 4 boilerplate** | "Nothing to implement" or silent skip | "Nothing new here" repeated >3× in sample |
| **Decisions captured** | Open items surface in NOW.md | Same open items appear across multiple wraps |

Flag any signal for skill edit. If multi-legatum rate is high, the skip gate in the legatum skill needs tightening.

### 6. Gap Analysis

Review recent sessions for patterns:
- Tasks done manually that could be skills
- Repeated multi-step workflows
- Questions asked that required vault deep-dives

### 7. Output

```markdown
## Skill Review - [Date]

### Healthy (Keep)
- `/skill-name` — Used X times, working well

### Needs Update
- `/skill-name` — Issue: [what's wrong]

### Candidates for Deprecation
- `/skill-name` — Last used: [date], reason to keep/remove

### Gaps Identified
- [Workflow that should be a skill]

### Actions
- [ ] Update X
- [ ] Create Y
- [ ] Deprecate Z
```

### 8. External Inspiration

Quick skim of releases/READMEs for new patterns worth cherry-picking. Don't adopt wholesale — just note anything novel.

| Repo | What to watch for |
|------|-------------------|
| [obra/superpowers](https://github.com/obra/superpowers/releases) | Skill methodology, discipline enforcement |
| [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) | Hook patterns, observability |
| [trailofbits/skills](https://github.com/trailofbits/skills) | Domain-specialized skill design |
| [OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files) | Planning workflows |
| [parcadei/Continuous-Claude-v3](https://github.com/parcadei/Continuous-Claude-v3) | Context management, state persistence |

### 9. Save to Vault

Save review to `/home/vivesca/notes/Skill Review - YYYY-MM.md`

## Quick Checks (Weekly)

Lighter version for weekly reset:

1. Any skills invoked incorrectly this week?
2. Any manual workflows repeated 3+ times?
3. Any skill descriptions that confused routing?
4. Any skill that should have fired but didn't — because the description trigger was too late?

## Related Skills

- `organogenesis` — How skills should be structured
- `vault-search` — Finding content skills reference

## Motifs
- [audit-first](../motifs/audit-first.md)
