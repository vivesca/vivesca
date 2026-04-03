---
name: cardo
description: Midday reflection — scan morning sessions for shipped work and loose ends, then set afternoon priorities. Use when user says "cardo", "noon", "midday", "lunch check", or "afternoon".
user_invocable: true
---

# Cardo — Midday Reflection

Midday checkpoint — what shipped this morning, what's still open, and what matters this afternoon.

*Cardo* (Latin: hinge, pivot) — the structural turning point of the day.

Lighter than `/daily` (no weather, health, inbox). Heavier than a `/legatum` (synthesises across sessions, not just the current one). The goal: arrive in the afternoon with intent, not momentum.

## Triggers

- "cardo"
- "noon"
- "midday"
- "lunch check"
- "afternoon"
- "/cardo"

## Steps

1. **Get current time** — run `date`. If it's before 11am or after 3pm, note this is a midday reflection run at an unusual hour but proceed anyway.
   - If `date` fails, use the system-provided current time and continue.

2. **Scan morning sessions** (the core value):
   - Run: `anam search "" --days 1 2>/dev/null | head -100`
   - If `anam` fails or returns nothing, note "Session history unavailable" and continue with NOW.md/TODO-based reflection.
   - Filter mentally for today's morning (roughly 6am–12pm HKT)
   - Group prompts by session ID to understand what each session covered
   - Extract for each session: topic, key outputs/decisions, anything left open

3. **Read NOW.md** — `~/notes/NOW.md`
   - If NOW.md is missing, note "NOW.md unavailable" and continue.
   - Note anything that was flagged as active this morning
   - Cross-reference against what sessions actually shipped

4. **Inbox check**:
   - **Cora brief**: `cora brief show` (instant, no browser needed)
   - **Cora todos**: `cora todo list` — surface any action items Cora has flagged
   - **Inbox count**: `gog gmail search "in:inbox" --limit 5`
   - If inbox has items: surface count and nudge `/epistula` — don't triage inline here
   - If gog fails (keychain locked): note "Gmail unavailable — unlock keychain" and skip.

5. **LinkedIn job alerts** (speculor):
   - Check if today's note exists: `~/notes/Job Hunting/Job Alerts YYYY-MM-DD.md`
   - If exists: count flagged roles (lines starting with `- [ ]`) and surface them — "X roles flagged — run `/evaluate-job` on any that look interesting"
   - Skip silently if missing

6. **Theoria eval check** (Fridays only):
   - If today is Friday: "Which theoria cards this week did you actually use — in a meeting, a draft, or a conversation? Name 2-3." Log the answer to `~/notes/Theoria/eval-labels.md` with date.
   - Other days: skip silently

7. **Token budget** (brief):
   - Run: `ccusage daily 2>/dev/null | tail -5` or check `/status` if concerned
   - If both commands fail, skip budget commentary.
   - If budget is tight (<20% remaining), flag it — affects afternoon delegation strategy
   - If healthy, skip silently

5. **Synthesise**:
   - **Shipped:** What actually got done this morning (code, decisions, vault updates)
   - **Open loose ends:** Things discussed but not completed, or deferred with "fix next time"
   - **Unresolved decisions:** Naming choices, architecture questions, etc. that ended without conclusion

6. **Afternoon priorities** — delegate to kairos:
   - Run `/kairos` for the live situational snapshot: calendar, open NOW.md gates, overdue TODOs.
   - If kairos fails, generate priorities from Cardo's own session synthesis only.
   - Use its output alongside the session scan to propose 2–3 concrete afternoon options.
   - Kairos owns the "what's live right now" read; cardo contributes the "what shipped / what's still open" from this morning's sessions.

7. **File loose ends** — for each open item identified:
   - If it's a quick fix: add to TODO.md `someday` or `low-energy`
   - If it's a decision: add to TODO.md with "Revisit:" framing
   - If TODO.md is missing or write fails, list loose ends in output as "Not filed".
   - Don't over-file — only items with real risk of being lost

## Output

Short prose. Two sections max:

**This morning:** What shipped, what's pending, anything unresolved.

**This afternoon:** 2–3 candidate priorities (inferred from session scan + NOW.md), or prompt if genuinely unclear.

**Example:**

> **Monday 2 Mar, 12:45pm**
>
> Solid morning. Shipped: nexis v0.2, hypha CLI, trama to crates.io, lucus (worktree manager), keryx published, expedio skill renamed. Haircut booked with Herman (Mar 10, 12pm).
>
> Two loose ends: keryx `--copy` clipboard broken on M3 (filed as someday), claude-code-system naming unresolved (consilium ran, no conclusion — filed for revisit).
>
> This afternoon: Capco Theoria doc needs finishing, or GARP quiz if you want something lighter. Token budget looks healthy — delegate-first still viable.

## Notes

- Don't re-surface items already resolved in NOW.md or clearly completed this morning.
- If morning was light (few sessions, few prompts), the output should be proportionally short.
- This is a transition ritual, not an audit. Keep it under 2 minutes to run.
- For ad-hoc priority checks outside the midday window, `/kairos`.

## Boundaries

- Do NOT run weather or health checks; those belong to `/auspex`.
- Do NOT produce a full-day close; `/daily` owns that.
- Stop after midday synthesis + afternoon options; do not initiate new execution tasks unless explicitly asked.

## Calls
- `kairos` — afternoon situational snapshot (calendar, NOW.md, overdue TODOs)
