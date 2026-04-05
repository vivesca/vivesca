---
name: todo
description: Manage TODO.md in the vault with time-based scheduling. Use when user says "todo", "add todo", "check todo", "done with", "overdue", or "someday".
user_invocable: true
---

# Todo

Quick management of `~/epigenome/TODO.md` with time-based scheduling.

## Date Tag Format

Tasks can have inline date tags at the end of the line, wrapped in backticks:

```markdown
- [ ] Task with start date `when:2026-02-25`
- [ ] Task with deadline `due:2026-03-13`
- [ ] Task with both `when:2026-02-10` `due:2026-04-11`
- [ ] Deferred task `someday`
- [ ] Task with no dates (Anytime)
```

| Tag | Syntax | Meaning |
|-----|--------|---------|
| When | `` `when:YYYY-MM-DD` `` | Don't surface until this date |
| Deadline | `` `due:YYYY-MM-DD` `` | Hard due date. Overdue after this. |
| Someday | `` `someday` `` | Deferred indefinitely. Hidden from Today/Upcoming. |
| Agent | `` `agent:` `` | Claude executes this autonomously — not a Terry action. |
| Low-energy | `` `low-energy` `` | Quick/simple task for downtime. Surfaced by `/mora`. |
| No tag | (nothing) | Anytime — visible in Today and All views. |

Dates are always ISO-8601 (`YYYY-MM-DD`). Regex patterns for parsing:

```
`when:(\d{4}-\d{2}-\d{2})`
`due:(\d{4}-\d{2}-\d{2})`
`someday`
```

## Commands

If `~/epigenome/TODO.md` is missing, create it with a minimal heading before running any command. If creation fails, report "TODO store unavailable" and stop.

### `/todo` (Today view — default)

Show today's actionable tasks. This is the **default** when no subcommand is given.

**Logic:**
1. Run `date +%Y-%m-%d` to get today in HKT
   - If date command fails, use system-provided current date.
2. Read `~/epigenome/TODO.md`
3. For each unchecked line (`- [ ]`):
   - SKIP if line contains `` `someday` ``
   - SKIP if line has `` `when:YYYY-MM-DD` `` where date > today
   - INCLUDE everything else (Anytime tasks, tasks where `when:` <= today, tasks with `due:`)
4. Group results by section heading (`## ...`)
5. Show overdue items first (`due:` date < today) with a warning prefix
6. Then show remaining today items
7. End with count: "X tasks today, Y overdue"

### `/todo today`

Same as bare `/todo` above.

### `/todo upcoming`

Show tasks scheduled for the next 14 days.

**Logic:**
1. Get today's date
   - If date command fails, skip with "Upcoming unavailable (date error)".
2. For each unchecked line:
   - INCLUDE if `when:` date is between today and today+14
   - INCLUDE if `due:` date is between today and today+14
   - SKIP `someday` items
   - SKIP tasks with no date tags
3. Sort by earliest date (when or due)
4. Group by section heading

### `/todo overdue`

Show tasks past their deadline.

**Logic:**
1. Get today's date
   - If date command fails, skip with "Overdue unavailable (date error)".
2. For each unchecked line:
   - INCLUDE if `due:` date < today
3. Sort by how overdue (most overdue first)

### `/todo someday`

Show deferred tasks.

**Logic:** Show all unchecked lines containing `` `someday` ``, grouped by section.

### `/todo all`

Show all unchecked items regardless of date tags. This is the old default behaviour.

```bash
grep -n "^\- \[ \]" ~/epigenome/TODO.md
```
If no lines are returned, report "No open tasks."

### `/todo add <task>`

Add a new task. Append to end of file. User can include inline tags.

```bash
echo "- [ ] <task>" >> ~/epigenome/TODO.md
```
If append fails, report "Failed to add task" and do not claim success.

Examples:
- `/todo add Review PR #123`
- `/todo add Review PR #123 \`due:2026-02-14\``
- `/todo add Explore new framework \`someday\``

### `/todo done <partial match>`

Mark a task as done by partial text match. Find the line, replace `- [ ]` with `- [x]`, then move the completed line to `~/epigenome/TODO Archive.md` (append under the current month's section like `## March 2026`, creating it if it doesn't exist).
If no unique match is found, ask for a narrower match and do not modify files.

### `/todo schedule <match> <date>`

Add or update a `when:` date on a matching task.

**Logic:**
1. Find the unchecked line matching `<match>`
2. If line already has `` `when:...` ``, replace the date
3. If not, append `` `when:YYYY-MM-DD` `` before any existing `` `due:...` `` or at end of line
4. Use the Edit tool to modify the line
If `<date>` is not valid `YYYY-MM-DD`, reject and ask for a valid date.

### `/todo due <match> <date>`

Add or update a `due:` date on a matching task.

**Logic:**
1. Find the unchecked line matching `<match>`
2. If line already has `` `due:...` ``, replace the date
3. If not, append `` `due:YYYY-MM-DD` `` at end of line
4. Use the Edit tool to modify the line
If `<date>` is not valid `YYYY-MM-DD`, reject and ask for a valid date.

### `/todo defer <match>`

Add `someday` tag to a task. Removes any `when:` or `due:` tags (deferred = no dates).
If no unique match is found, ask for a narrower match and do not modify files.

### `/todo undefer <match>`

Remove `someday` tag from a task. Task becomes Anytime (visible in Today view).
If no unique match is found, ask for a narrower match and do not modify files.

### `/todo clean`

Move all checked items (`- [x]`) to `~/epigenome/TODO Archive.md` under the current month's section (e.g. `## March 2026`), appending to an existing section if present or creating a new one. Then remove all `[x]` lines from TODO.md and collapse any resulting double blank lines.
If archive write fails, do not remove checked items from TODO.md.

### `/todo spare`

Show the `🔋 Spare Capacity` section items — low-priority maintenance for when token budget has headroom.

## File Format

```markdown
## Section (optional emoji prefix)
- [ ] Unchecked task
- [ ] Task with dates `when:2026-02-25` `due:2026-03-13`
- [ ] Deferred task `someday`
- [x] Completed task
```

## Notes

- Single source: `~/epigenome/TODO.md`
- All agents (Claude Code, OpenCode) share this file
- Tasks grouped under `## Headings` — preserve section structure
- **NEVER leave `- [x]` lines in TODO.md.** When marking done — whether via `/todo done` or manually — always move the completed line to `~/epigenome/TODO Archive.md` in the same edit. No exceptions, no "clean up later".
- **Reflections/journaling items live in `~/epigenome/chromatin/Reflections Queue.md`** — not TODO.md
- **`🔋 Spare Capacity` section** = low-priority maintenance for spare token budget
- **`Someday` subsection** at the bottom of Spare Capacity = deferred indefinitely
- Dates are always ISO-8601 (`YYYY-MM-DD`), always in HKT context
- Tasks with no date tags are "Anytime" — shown in Today and All views
- When comparing dates, use `date +%Y-%m-%d` (system is HKT)
- Related files: `[[TODO Archive]]` · `[[Reflections Queue]]`

## Due Alarm Convention

When adding a task with `due:` within 7 days, also set a phone alarm:

```bash
pacemaker add --date YYYY-MM-DD "<task title>"
```

**Bar for Due at all:** Would forgetting cause real damage? If missing the moment has no cost (low-stakes admin, "sometime in April"), it belongs in TODO.md only — not Due. Due is for time-critical only.

**When to apply a pacemaker alarm:** Hard deadlines requiring action on a specific day — not `someday`, not `when:` gates, not recurring habits. Pick a time that fits the day (not just 9am default). This is a manual step — don't automate it, so the time is chosen deliberately.

## Boundaries

- Do NOT reinterpret task intent; only perform requested task list operations.
- Do NOT create project plans or prioritization frameworks here; this skill manages TODO state only.

## Example

> `/todo` → 6 tasks today, 2 overdue.
> Overdue: "Submit CPD record" (`due:2026-03-01`), "SmarTone bill" (`due:2026-03-02`).
> Added: "Review Capco deck `due:2026-03-05`".
