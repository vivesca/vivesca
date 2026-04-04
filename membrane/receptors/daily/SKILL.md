---
name: daily
description: Bedtime daily close (last thing before sleep). Full-day reflection and tomorrow preview. Use when user says "daily", "end of day", "eod", or before bed. Comes after eow and quies in the evening sequence. NOT for end-of-work (use eow) or session end (use legatum).
user_invocable: true
---

# Daily

Bedtime close → daily note. The final checkpoint of the day.

## Triggers

- "daily", "end of day", "eod"
- Before bed / winding down for the night

## Relationship to /eow

`/eow` (end of work) is the optional mid-day checkpoint — work themes, work mood, unfinished threads. If it was run, the daily note already has an "End of Work" section. This skill builds on top of it:

- **eow was run:** Skip re-summarising work. Focus on evening activity and full-day reflection.
- **eow was NOT run:** Cover the full day (work + personal) in one pass, same as before.

## Workflow

1. **Get today's date** (YYYY-MM-DD, HKT)
   - If `date` fails, use system-provided current date and continue.

2. **Read today's daily note** (`~/epigenome/chromatin/Daily/YYYY-MM-DD.md`)
   - Check for existing session logs from `/legatum` and an "End of Work" section from `/eow`.
   - If the note is empty or missing, **fallback:** delegate history scan to a subagent — use Task tool (subagent_type: "general-purpose", model: "haiku") with prompt: "Run `python ~/scripts/chat_history.py --full` and synthesize a concise summary of today's activity. Group by theme. List key accomplishments, decisions, and unfinished threads. Keep output under 30 lines."
   - If both note read and fallback scan fail, continue with a minimal close based on current session context and label it "partial".

3. **Conversation** — ask Terry one open question: **"How was today?"**
   - Let Terry talk. Follow up naturally — 2-3 exchanges max.
   - Use the daily note, NOW.md, and TODO scan as context to ask good follow-up questions — don't dump them as a report.
   - Things worth probing naturally if Terry doesn't mention them:
     - Whether the day moved the actual needle (check against NOW.md / imminent TODOs)
     - Theo time (if not mentioned)
     - Best moment (not most productive — best)
   - **If eow was run:** Work themes are already captured. Focus the conversation on the evening and the full-day arc.
   - **If no eow:** Cover the full day.

4. **Tomorrow preview** — scan for what's queued tomorrow:
   - Get tomorrow's date (`date -v+1d +%Y-%m-%d`)
   - If date command fails, skip tomorrow preview and note "Tomorrow preview unavailable".
   - Read `~/epigenome/chromatin/Schedule.md` — check for recurring commitments on that day of the week
   - If Schedule.md is missing, continue without recurring commitments.
   - Read `~/epigenome/TODO.md` and surface:
     - Items with `due:` = tomorrow (deadlines)
     - Items with `when:` = tomorrow (scheduled starts)
     - Any overdue items (`due:` < tomorrow) that weren't completed
   - Check if tomorrow's daily note already exists (carryover from today's follow-ups)
   - If TODO or tomorrow's note cannot be read, continue with whatever preview data is available.
   - **Thursday only (token budget check):** Weekly Claude Max reset is Friday ~11am HKT. Run `/status` or `cu` and if weekly usage is low (significant headroom remaining), surface it: "Weekly reset tomorrow 11am — X% unused. Spare Capacity tasks in TODO.md if you want to burn tokens tonight or early tomorrow."
   - If `/status`/`cu` unavailable, skip token budget line silently.

5. **Fix header** — validate and update the `# YYYY-MM-DD — Day` line:
   - Verify day-of-week matches `date` output (wrap sometimes gets this wrong). Fix if needed.
   - Append a thematic tagline: compress the themes to a few words each, comma-separated.
   - Result: `# 2026-02-19 — Thursday — Doumei shipped, CV submitted, GARP grinding`

6. **Finalize the daily note** — append all closing sections at once:

```markdown
---

## Day rating

[Assess from the evidence — session logs, things shipped, decisions made, needles moved. Don't ask Terry. 2-3 sentences. Be honest — 10 commits but no needle movement is "busy, not productive". A rest day with one good decision is "light but effective". A full Theo day with no work is "rest day, needed it".]

## Reflection

[Synthesise from the conversation — use Terry's framing, not yours. Weave in observable data (logs, TODO) but the arc should reflect what Terry said mattered. If eow exists, build on it. Honest, not cheerful.]

## Learnings

- [Insights from the day, if any — check wrap captures]

## Follow-ups

- [ ] [Things to do tomorrow]

## Tomorrow

- [Deadlines, scheduled items, overdue carryover — or "Clear plate."]
```

   - Tomorrow is a heads-up, not a plan. Morning skill handles the real-time brief.

## Notes

- If note exists, append/update rather than overwrite
- Don't force entries — "nothing notable" is fine
- The value is in the reflection, not the logging — wrap handles the session logging
- This is lightweight by design: wrap does the heavy lifting throughout the day
- Tomorrow preview is a closing thought — keep it to what's *known*, don't speculate

## Boundaries

- Do NOT run morning/inbox/weather routines; `/auspex` owns those.
- Do NOT start new execution work; this skill closes the day and writes reflection only.
