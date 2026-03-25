# Scheduled Praxis.md — Brainstorm

**Date:** 2026-02-08
**Status:** Brainstorm complete — ready for planning

## What We're Building

Enhance the existing `/todo` skill and `Praxis.md` format to support Things 3-style scheduling without introducing any new tools. The current flat checkbox system works for capture but fails at time-based prioritisation — tasks with no temporal dimension all feel equally urgent.

**Core addition:** Inline date metadata on TODO items that enables filtered views (Today, Upcoming, Someday, Overdue).

## Why This Approach

The original question was "should I build a CLI clone of Things 3?" Through brainstorming, we identified that:

1. **The real gap is scheduling**, not structure or capture
2. **Things 3 MCP servers already exist** (hald/things-mcp, excelsier/things-fastmcp) — building a clone would duplicate solved problems
3. **Buying Things 3 ($50) + MCP** is viable but introduces a new tool when the current markdown system is already Claude-accessible
4. **Enhancing Praxis.md** is the simplest intervention that solves the actual problem — zero new dependencies, zero new tools, immediate Claude Code integration

**YAGNI applied:** We don't need areas/projects hierarchy (section headers already provide this), mobile capture (OpenClaw handles it), or push notifications (morning triage covers it).

## Key Decisions

1. **Enhance Praxis.md over building/buying** — solves the scheduling gap with minimal intervention
2. **Inline metadata format** — dates live on the same line as the task, not in frontmatter or a separate database
3. **Things 3 mental model for scheduling** — adopt "when" (start date) vs "deadline" (hard due) and "someday" as concepts
4. **Claude-powered views** — the `/todo` skill generates filtered views on demand rather than maintaining separate files

## Proposed Format

```markdown
- [ ] Task description `when:2026-02-10` `deadline:2026-02-14`
- [ ] Another task `someday:`
- [ ] Urgent thing `deadline:2026-02-09`
- [ ] Regular task with no dates
```

- `when:YYYY-MM-DD` — "don't show me this until this date" (Things 3's scheduling)
- `deadline:YYYY-MM-DD` — hard due date (overdue after this)
- `someday:` — deferred indefinitely, hidden from Today/Upcoming views
- No tag = Anytime (visible in all views except Someday)

## Views the /todo Skill Would Support

- **Today** — `when:` <= today + any `deadline:` today + unscheduled (Anytime)
- **Upcoming** — `when:` in next 7/14 days
- **Overdue** — `deadline:` < today
- **Someday** — `someday:` tagged items
- **All** — current behaviour (everything)

## Open Questions

1. **Backtick syntax vs parenthetical?** — `` `when:2026-02-10` `` renders as inline code in Obsidian (visible but not pretty) vs `(when: Feb 10)` which is more readable but harder to parse
2. **Should `/morning` auto-show Today view?** — probably yes, as part of triage
3. **Recurring tasks?** — not for v1 (YAGNI), but could add `repeat:weekly` later
4. **Should overdue deadlines auto-surface in `/morning`?** — strong yes

## What We're NOT Building

- A standalone CLI tool or binary
- A database (SQLite or otherwise)
- Mobile app or sync layer
- Things 3 integration (can add later if Terry buys Things 3)
- Project/area hierarchy beyond existing markdown sections
- Push notifications or reminders

## Next Step

Run `/workflows:plan` to design the `/todo` skill enhancement — format spec, parsing logic, view filters, and `/morning` integration.
