---
name: melete
description: Daily consulting readiness drill — scenarios, reading prompts, observation logging. "consulting prep", "prep drill", "consulting drill", "melete"
user_invocable: true
model: sonnet
status: retiring
retire_after: 2026-04-08
---

# Consulting Prep

Daily practice skill for building consulting mental models before Capco start. Three modes based on day of week. ~15 minutes per session.

**Data:** `~/epigenome/chromatin/Career/Consulting Readiness Program.md` (master program, reading list, scenario bank)
**State:** `~/epigenome/chromatin/Career/.consulting-prep-state.json` (progress tracking)
**Log target:** Today's daily note at `~/epigenome/chromatin/Daily/YYYY-MM-DD.md`

**Expires:** 2026-04-08 (Capco start). After that, suggest switching to the live observation format described in the program note.

## Trigger

- "consulting prep", "consulting drill", "prep drill", "melete"
- `/consulting-prep`, `/phronesis`

## Workflow

### 1. Check State & Determine Mode

Read the state file. If it doesn't exist, initialise it:

```json
{
  "readings_completed": [],
  "scenarios_completed": [],
  "sessions": 0,
  "last_session": null
}
```

**Check time to start:** If today is within 14 days of 2026-04-08, activate **Endgame Mode** — regardless of day of week, default to Scenario Practice. Reading is optional only if Terry explicitly asks.

Determine today's mode from day of week (unless Endgame Mode is active):
- **Mon / Wed / Fri** → Read & Extract
- **Tue / Thu** → Scenario Practice
- **Sat / Sun** → Skip (weekends reserved for family)

Show a one-line status: `Session #N | Readings: X/15 | Scenarios: Y/10 | Mode: [today's mode]`
If Endgame Mode: append `⚡ Endgame Mode — N days to start`

**Pattern watch:** If `patterns_watching` exists in the state file, check each entry. If `count >= threshold`, trigger the listed `action_if_hit` before proceeding. Otherwise surface any active patterns as a one-liner: `⚠️ Watching: [pattern] (seen N/threshold times)`

### 2. Daily Scenario Warm-Up (Every Session, 5 min)

Before the main mode, run a quick scenario — even on Read & Extract days. This is the recall layer: short, sharp, no debrief needed.

1. Pick a scenario Terry has done before (rotating through completed ones). If none yet, use the first unplayed one.
2. Present it in one sentence (no scene-setting — he should be able to reconstruct from memory):

```
🔁 Recall: [scenario title] — what's your instinct?
```

3. Terry gives a one-line answer. Respond with one line only: what he got right, or what he missed. No extended debrief — save that for Scenario Practice days.
4. Move immediately to the main mode.

**Skip this step** only if Terry explicitly says "skip warm-up" or if it's the very first session.

### 2A. Read & Extract Mode (Mon/Wed/Fri)

1. Read the program note's reading list
2. Pick the next unread item (sequential order). **Skip the "Client-specific pre-work" block** — those are standalone research sessions run outside this skill, not 15-min reads.
3. **If it's a book:** Give a 2-3 paragraph summary of the key concepts relevant to Terry's situation. Focus on one actionable principle.
4. **If it's a search topic:** Run a web search, find the best piece, summarise in 2-3 paragraphs.
5. After presenting the material, ask Terry:

```
What's the one principle you'd take from this?
And how does it apply to Capco clients specifically?
```

6. **Training mode guard:** If Terry asks for your opinion before giving his own, redirect once: *"Your instinct first — what would you take from this? Then I'll push back."* Only share your view after he's committed to an answer.

7. Wait for Terry's response. Don't judge it — this is extraction practice, not a quiz.
8. Log to daily note and update state.

### 2B. Scenario Practice Mode (Tue/Thu)

**Scenario sources (in priority order):**
1. `~/epigenome/chromatin/Career/Consulting Readiness Program.md` — primary scenario bank
2. `~/germline/loci/solutions/agent-tests/` — HK FS consulting scenarios with multi-model analysis (proposal-architect, governance-sentinel, eval-designer). Use these for deeper domain practice: present the client brief, ask Terry how he'd approach it, then share the key insights from the README as the debrief.

1. Read the program note's scenario bank
2. Pick a scenario Terry hasn't done recently (prioritise unplayed, then least recent)
3. Present the scenario. Set the scene in 2-3 sentences — make it vivid enough to feel real.

```
🎯 Scenario #N: [title]

[2-3 sentence scene-setting. Put Terry in the room.]

What do you do?
```

4. Wait for Terry's response (his instinct).
5. After he responds, do THREE things:

   **a. Acknowledge what's good about his instinct.** Don't just correct — the instinct often has something right.

   **b. Name the gap.** What would the Career Principles frameworks suggest differently? Reference the specific principle (doctor model, defend the problem, private preview test, etc.)

   **c. Ask one follow-up question** that forces him to go deeper:
   - "What question would you ask before doing that?"
   - "Who in the room might feel threatened by that move?"
   - "What's the version of this that makes [stakeholder] look good?"

6. Wait for follow-up response, then close with a one-line takeaway.
7. Log to daily note and update state.

### 3. Log & Close

**Daily note entry** (append under a `## Consulting Prep` heading):

For Read & Extract:
```markdown
## Consulting Prep
📖 [title/source]
→ Principle: [Terry's extraction]
→ Capco client application: [Terry's application]
```

For Scenario Practice:
```markdown
## Consulting Prep
🎯 Scenario #N: [title]
→ My instinct: [summary of Terry's response]
→ Gap: [what the frameworks suggest]
→ Takeaway: [one line]
```

**Update state file:**
- Add reading/scenario to completed list
- Increment session count
- Update last_session date

**Close with:**
- If both readings and scenarios are progressing well: one encouraging line, no fluff
- If a pattern is emerging across sessions (e.g., consistently jumping to solutions): name it directly
- Remind of any GARP RAI quiz due today (check `melete today`)

### 4. Observation Prompt (Every Session)

Before closing, regardless of mode:

```
👁️ Quick check: did you notice anything today about listening, selling,
   power dynamics, or pushback — in any interaction, not just work?
```

If Terry has something, log it. If not, move on — don't force it.

## Scenario Bank

Stored in the program note. If Terry exhausts all 10, generate new ones based on:
- Patterns from his actual Capco prep (Capco Transition note, First 30 Days)
- Emerging weak areas from previous sessions
- Escalating difficulty (early scenarios are simpler dynamics, later ones combine multiple principles)

## Notes

- **Sonnet is fine.** This is structured prompting, not judgment-heavy work.
- **Keep it under 15 minutes.** If Terry is going deep, that's fine — but don't prompt for more than one reading or one scenario per session.
- **Don't lecture.** The Career Principles note has the frameworks. Reference them, don't repeat them.
- **Track patterns across sessions.** If Terry's instinct consistently jumps to building/fixing before asking, name that trend explicitly by session 3-4.
- **This skill expires.** Once Capco starts, suggest retiring it and switching to the live observation log format in the program note.
