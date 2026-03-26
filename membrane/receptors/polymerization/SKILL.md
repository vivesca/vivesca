---
name: polymerization
description: Praxis.md task management — query and clean the canonical todo file, not a substitute for editing it.
model: sonnet
---

# Polymerization — assemble the action stack

**Rule: read Praxis state before proposing work; clean before adding.**

## When this fires

- User asks "what do I have to do today?" or "what's overdue?"
- Planning session: need to see current task state before prioritizing
- End of session: checking what was completed vs still pending
- Praxis.md feels cluttered or stats are off

## Discipline

1. **Subcommand selection:**
   - `today`: default for session planning — shows today-due items
   - `upcoming`: 7-day horizon — use for weekly planning
   - `overdue`: always run alongside today; overdue items need triage first
   - `stats`: use when discussing backlog health or task velocity
   - `clean`: run when stats show accumulation of stale items; destructive-ish, review output before acting
   - `all`/`someday`/`spare`: only when user explicitly asks for full inventory

2. **Sequence for session start**: overdue → today → upcoming. Surface overdue first — they preempt today's plan.

3. **Polymerization reads, Praxis.md writes** — don't use this tool to add or modify tasks. Edit Praxis.md directly.

4. **`clean` is not automatic** — show the output, confirm stale items are actually stale before treating the clean as done.

## Anti-patterns

| Don't | Do |
|-------|-----|
| Run `all` as the default view | Start with overdue + today |
| Run clean without reviewing output | Show output, get confirmation |
| Add tasks through this tool | Edit Praxis.md directly |
| Skip overdue when showing today | Overdue trumps today |
