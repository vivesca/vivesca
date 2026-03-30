---
name: ecdysis
description: Sunday weekly planning — next-week plan, backward glance, TODO prune. "weekly"
user_invocable: true
disable-model-invocation: true
---

# Weekly Planning

Sunday evening. Plan the week ahead, quick glance back. 20-30 minutes.

Lead with **forward** (what matters next week), support with **backward** (what happened, what's carrying over). Newport's insight: the weekly plan is the bridge between quarterly direction and daily action.

## Triggers

- weekly
- weekly review
- week in review
- sunday planning
- plan the week

## Workflow

### 0. Context Gather

```bash
weekly-gather
```

This runs all deterministic gathering in parallel (next week's calendar, TODO filtering, NOW.md, quarterly note, daily note scraping for Commute Close sections, Oura trends, job alerts, garden posts). Use `--json` for structured parsing.

### 1. Next week's plan (lead with this)

Using the gathered context — calendar, TODO items due this week, NOW.md gates, quarterly note:

Then ask Terry: **"What are the 3 things that matter this week?"**

Don't suggest — let him pick. The act of choosing is the value. Write them into the weekly note.

### 2. Quick backward glance

Use the daily note Commute Close sections and Oura trends from `weekly-gather` output.

Synthesize into **maximum 2-3 themes.** Don't linger — this is context for planning, not a retrospective.

- What moved forward vs what stalled?
- Where did energy go? (What to protect vs what to drop)
- Health flags? (Sleep trend, HRV drops)

### 3. Job alerts

- Check `~/epigenome/chromatin/Job Hunting/Job Alerts YYYY-MM-DD.md` for any flagged roles this week
- Surface unchecked items briefly
- Skip silently if no alerts or file missing

### 4. TODO prune

- Clear completed items from `~/epigenome/chromatin/Praxis.md`
- Flag anything untouched for 2+ weeks — delete or reschedule
- Drop low-stakes items that keep lingering (see `memory/feedback_todo_hygiene.md`)

### 5. Garden cull

- `ls -lt ~/epigenome/chromatin/Writing/Blog/Published/ | head -10` — anything published this week?
- Kill or merge weak posts (thin thesis, restating others, generic advice)

### 6. Write the weekly note

Create `~/epigenome/chromatin/Weekly/YYYY-Www.md`:

```markdown
# Week of YYYY-MM-DD

## This Week's Focus

1. [Primary]
2. [Secondary]
3. [Explore]

## Last Week — Quick Glance

### Themes
- [2-3 themes, one line each]

### Energy
- Gave energy: [what]
- Drained: [what]
- Adjust: [what to do differently]

### Health
[Stable / flags — keep it brief]

## Open Loops

- [ ] [Carrying into this week]
```

## Boundaries

- Do NOT run system health checks — nightly handles that
- Do NOT start execution tasks — plan only
- Do NOT expand beyond current + next week
- Lead with forward, not backward. The plan is the point.

## See also
- `/circadian` (dusk phase) — the daily routine (evening)
- `/mitosis` — first Sunday of the month, maintenance
- `/meiosis` — direction and finances (4x/year)
- `/circadian` (day phase) — ad-hoc "what now?"
- [[cadence-design]] — principles behind this cadence stack
