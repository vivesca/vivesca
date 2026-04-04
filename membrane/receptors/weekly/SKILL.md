---
name: weekly
description: Weekly synthesis and review. Use when user says "weekly", "weekly review", "week in review", or on Fridays.
user_invocable: true
triggers:
  - weekly
  - weekly review
  - week in review
  - synthesis
  - friday
---

# Weekly Synthesis

Create a weekly synthesis of work, thinking, and progress.

## Triggers

- "weekly", "weekly review", "week in review"
- Saturday morning — full week's data, fresh Max20 quota (resets Fri ~11am). Hook nudges Sat/Sun.

## Workflow

1. **Determine the week range** (Mon-Sun, HKT)
   - If date computation fails, default to "last 7 days" and note the fallback.

2. **Gather the week's data** (recursive — read distilled layers, not raw):
   - Read the **## Reflection**, **## Follow-ups**, and **## Mood** sections from each daily note `~/epigenome/chromatin/YYYY-MM-DD.md` (not the full session logs — those are raw context, already distilled into the reflection)
   - Read this week's **Theoria weekly snapshot** from `~/epigenome/chromatin/Theoria.md` (written by `/dialexis`). Reference it in the synthesis — don't re-derive AI themes from the raw AI News Log.
   - Read `~/epigenome/chromatin/Capco Transition.md` for transition status
   - Read `~/epigenome/TODO.md` for completed/outstanding items
   - Check `~/docs/solutions/` and `MEMORY.md` for entries this week
   - Check git log for skills/vault commits: `cd ~/skills && git log --oneline --since="7 days ago"`
   - Check `~/logs/` for cron output logs
   - Check CSB job monitor results: `tail -20 ~/logs/cron-csb-jobs.log` and `cat ~/.local/share/csb-jobs/seen.json | python3 -c "import sys,json; print(len(json.load(sys.stdin)),'jobs tracked')"`
   - **Lararium** — Surface the Mourner's recent observations: `ls ~/epigenome/chromatin/Lararium/mourner-*.md 2>/dev/null | tail -7 | xargs -I{} head -20 {}`. Include 1-2 of the most striking observations in the weekly note under `## Lararium`. If the Mourner named an abandoned project worth revisiting, flag it in Open Loops.
   - **GARP RAI exam prep** (until Apr 4 exam): run `melete stats && melete coverage`. Flag: (a) any weak topic (<60%) with no drill entry → create one; (b) low-coverage topics (<3 attempts) → note for next week's sessions; (c) overall rate trend vs last week.
   - If any source file is missing/unreadable, note it as unavailable and continue with remaining sources.
   - If a command fails, do not retry repeatedly; record one-line failure and continue.

3. **Synthesize into themes** — don't just list events, find patterns. Consult `topica`: which mental model did I miss or misapply this week?
   - **Maximum 3-4 themes.** If the week had 6 themes, the skill is logging, not synthesising. Pick the 3 that matter next week.
   - What topics kept coming up?
   - What moved forward vs what stalled?
   - Where did energy go?

4. **Create weekly note** at `~/epigenome/chromatin/Weekly/YYYY-Www.md` (e.g., `2026-W06.md`):

```markdown
# Week of YYYY-MM-DD

## At a Glance

- Days active: X/7
- Daily notes: [list]
- Pipeline changes: [summary]

## Key Themes

### [Theme 1]
- Where it appeared: [contexts]
- Progress: [what moved]
- Next: [what's next]

### [Theme 2]
...

## Progress

### Career / Capco
- Onboarding progress: [status]
- Client engagements: [any updates]
- Network: [new contacts, follow-ups]

### Skills & Tools
- New/updated skills: [list]
- Tool changes: [any]

### Projects
- [Project]: [status change]

### GARP RAI Prep (until Apr 4)
- Overall rate: X% (vs last week X%)
- Sessions this week: X
- Weak topics (<60%): [list]
- Low coverage (<3 attempts): [list]
- Drill gaps fixed: [any new drill entries created]
- Next focus: [topic to prioritise]

## Learnings Captured

- [Summary of learnings routed to `~/docs/solutions/`, `MEMORY.md`, or skills this week]

## Health & Recovery

Run `oura trend` for the week's scores, then correlate with daily notes:

```bash
oura trend --days 7
```

Analyse:
- **Sleep trend** — improving, declining, or stable? Flag any score <70
- **HRV pattern** — leading indicator of stress. Drops below 50 warrant attention
- **Bedtime drift** — are bedtimes creeping past 22:30? (Theo school drop-off = fixed wake-up, bedtime is the only lever)
- **Correlation with activity** — cross-reference low-score nights with that day's daily note. Look for: resignation conversations, late-night coding sessions, career rumination, insomnia entries
- **Stress data** — note any days with elevated stress_high (>1h)

Include in weekly note:

```markdown
## Health

| Day | Sleep | Readiness | HRV | Bedtime | Note |
|-----|-------|-----------|-----|---------|------|
| Mon | 86 | 81 | 69 | 23:40 | — |
| ... | | | | | |

**Pattern:** [1-2 sentence summary of the week's health trend and any correlations found]
**Action:** [Anything to adjust, or "Steady"]
```

If all 7 days are within normal range (Sleep >75, HRV >50, bedtime <23:00), collapse to: "**Health: Stable week.** Sleep avg X, HRV avg Y. No flags." Don't enumerate 7 identical rows.

Keep it brief — the value is pattern recognition over weeks, not daily obsessing.

## Lararium

[1-2 of the Mourner's most striking observations this week. What did it grieve? Did it name something worth revisiting?]

## Energy Audit

- What gave energy: [activities, wins]
- What drained: [friction, blockers]
- Adjust next week: [what to do differently]

## Open Loops

- [ ] [Unresolved items carrying into next week]

## Next Week's Focus

1. [Primary]
2. [Secondary]
3. [Explore]
```

5. **Keep it honest** — this is for pattern recognition, not performance reporting. Short weeks with little output are fine to note as such.

## System & Tooling Health (weekly)

Run these checks every Friday and include results in the weekly note under `## System Health`.
If a check command fails, mark that metric as `Unavailable` in the table and continue.

### Infrastructure Services

8. **wacli daemon** — `launchctl list com.terry.wacli-sync`. Check exit code (0 = running, 113 = dead). If dead, flag for restart.
9. **Vault git backup** — Check recency: `cd ~/epigenome/chromatin && git log -1 --format='%ci'`. Flag if last commit >2h old (cron runs every 30 min).
10. **Vault link health** — Run two passes:
    - Broken links: `nexis ~/epigenome/chromatin --exclude Archive --exclude "Waking Up" --exclude memory 2>/dev/null`. Flag if broken link count >30 or increased from last week.
    - Asymmetric links: `nexis ~/epigenome/chromatin --asymmetry --exclude Archive --exclude "Waking Up" --exclude memory 2>/dev/null`. Surface notes that link out but have no backlinks — add backlinks inline if obvious, defer to `/nexis` session if large volume.
    Full triage (atomicity, restructuring) is a separate `/nexis` session — don't do it inline here.
11. **Agent-browser profile** — `ls -la ~/.agent-browser-profile/Default/Cookies 2>/dev/null && echo "OK" || echo "MISSING"`. Flag if profile directory is missing or Cookies file absent.

### AI Tooling

1. **Knowledge system hygiene** — The principle: minimum in CLAUDE.md/MEMORY.md (loads every session), maximum in skills (loads on trigger). Check line counts: CLAUDE.md target ≤50, MEMORY.md target ≤80.
   - **Mark decay scan:** `ls ~/epigenome/marks/feedback_*.md | wc -l` — target ≤150. For each mark in MEMORY.md's Behavioral section, grep this week's session logs for the mark filename. Any mark not cited in 4+ weeks → candidate for demotion to archive. Any archived mark cited this week → promote back from `~/epigenome/marks/archive/`.
   - **Archive rotation:** `ls ~/epigenome/marks/archive/*.md | wc -l` — report count. Scan archive for marks referenced in this week's work (grep session logs for archive filenames). Promote any cited marks back to active.
   - **Career north star check:** Surface `memory/user_career_north_star.md` — is this week's work building toward "real AI problems + sharp people who build"? Flag drift.
   - **Skill migration:** For each CLAUDE.md/MEMORY.md entry, ask: "does this only matter in a specific context?" If yes → move to the governing skill. Skills are contextual memory; CLAUDE.md/MEMORY.md are unconditional memory.
   - **Staleness scan:** Flag entries referencing retired tools, completed transitions, past dates.
   - Present concrete actions: "Remove X", "Demote Y", "Move Z to skill W".
2. **Skills inventory** — `ls ~/skills/*/SKILL.md | wc -l` for total count. `cd ~/skills && git log --oneline --since="7 days ago"` for changes.
   - **Description quality:** Spot-check 5 random skill descriptions. Is the trigger clear? Would the right skill fire from the description alone? If not, fix immediately — a perfectly written skill with a bad description is invisible.
   - **Duplicates:** Flag skills with overlapping trigger space. Fold thin skills into their parent.
   - **Retirements:** `grep -rl "DEPRECATED\|retire_after:" ~/skills/*/SKILL.md` — delete expired ones.
   - **Zero-fire skills:** Cross-reference `~/.claude/skill-usage.tsv` against `ls ~/skills/*/SKILL.md`. Any user-invocable skill with zero fires over 4+ weeks of data → candidate for removal or description fix. (Non-user-invocable reference skills are exempt.) Run:
     ```bash
     python3 -c "
     from pathlib import Path; from datetime import datetime, timedelta
     import re
     log = Path.home() / '.claude' / 'skill-usage.tsv'
     cutoff = datetime.now() - timedelta(weeks=4)
     fired = set()
     if log.exists():
         for line in log.read_text().splitlines():
             parts = line.split('\t')
             if len(parts) == 2 and datetime.fromisoformat(parts[0]) > cutoff:
                 fired.add(parts[1])
     skills_dir = Path.home() / 'skills'
     for s in sorted(skills_dir.glob('*/SKILL.md')):
         name = s.parent.name
         text = s.read_text()
         if 'user_invocable: true' in text and name not in fired:
             print(f'  ⚠  {name} — zero fires in 4 weeks')
     " 2>/dev/null
     ```
3. **MCP servers** — `claude mcp list` to verify health. Flag any disconnected, orphaned from experiments, or version-drifted servers.
4. **Token consumption** — Run `cu` alias for Max20 usage stats. Note weekly trend and any spikes.
5. **Oghma health** — `oghma stats` for DB size, memory count, extraction backlog.
6. **Cron scripts** — Check `~/scripts/crons/` and `~/logs/cron-*.log` for failures or stale output.
7. **QMD index** — `qmd cleanup && qmd update` to prune stale entries and re-index. Then `qmd status` for collection health.
8. **DR sync** — Run `dr-sync` to back up Claude Code config, memory, Brewfile to officina (git-backed). Verify commit pushed.
9. **Hook fire log** — Check `~/logs/hook-fire-log.jsonl` for the past 7 days:
   ```bash
   python3 -c "
   import json; from datetime import datetime, timedelta, timezone
   cutoff = datetime.now(timezone.utc) - timedelta(days=7)
   lines = open(Path.home() / 'logs' / 'hook-fire-log.jsonl').readlines()
   recent = [json.loads(l) for l in lines if json.loads(l)['ts'] > cutoff.isoformat()]
   from collections import Counter
   counts = Counter(e['hook']+': '+e['rule'][:50] for e in recent)
   [print(v, k) for k,v in sorted(counts.items(), key=lambda x:-x[1])]
   print(len(recent),'total fires')
   " 2>/dev/null || echo "No hook log yet"
   ```
   **Interpret:** High-frequency rules = not yet internalized. Zero fires on a rule = either working perfectly or dead code (verify with a test). Same rule firing 2+ times within minutes = deny message unclear. Flag rules with 5+ fires/week for message improvement.

Include a summary table in the weekly note:

```markdown
## System Health

| Metric | Value | Status |
|--------|-------|--------|
| wacli daemon | running/dead | ✅/🔴 |
| Vault backup | Xm ago | ✅/⚠️ |
| Vault broken links (signal) | X | ✅/⚠️ |
| Agent-browser profile | present/missing | ✅/⚠️ |
| CLAUDE.md lines | X | ✅/⚠️ |
| MEMORY.md lines | X | ✅/⚠️ |
| Skills (total) | X | — |
| Skills (changed this week) | X | — |
| MCP servers | X connected | ✅/⚠️ |
| Max20 usage | X% weekly | ✅/⚠️ |
| Oghma memories | X | — |
| Cron scripts (healthy/total) | X/Y | — |
| DR sync | pushed/stale | ✅/⚠️ |
| Hook fires (7d) | X total, top rule | — |
```

## Friday Reset Checklist

Run this alongside the synthesis every Friday:

1. **TODO.md prune** — Clear completed items, flag anything untouched for 2+ weeks (stale → delete or reschedule)
2. **Transition status** — Update [[Capco Transition]] (PILON, onboarding, handover)
3. **Networking status** — Who's in motion, who needs follow-up? (BOCHK bridge, Capco contacts)
4. **CSB job monitor** — Any new AI-related government vacancies this week? Check `~/logs/cron-csb-jobs.log` for matches
5. **Priorities for the week** — Top 2-3 actions
7. **AI landscape** — Run `/lustro --deep` first to pull full source sweep, then `/dialexis` for weekly synthesis (client talking points).
8. **Capco intel sweep** (until start date only — remove after onboarding):
   - Search: "Capco HK" or "Capco Asia" news this week
   - Search: HKMA AI/fintech guidance, GenAI deployments at HK banks
   - Search: competitor moves in HK FSI (Accenture, EY, KPMG, Deloitte)
   - Synthesize into 3 bullets: Capco firm news | AI x banking | Competitor signal
   - Feed anything useful into `~/epigenome/chromatin/Capco/Conversation Cards/` if it's a durable talking point
9. **ClawHub scan** — Browse [clawhub.ai](https://clawhub.ai) for new/notable skills using semantic search. Focus areas: messaging, health/biometrics, calendar, finance, relationship/CRM. Surface 1-3 ideas worth building; append to `~/epigenome/chromatin/Awesome OpenClaw Skills - Evaluation.md` if notable. Skip if nothing new since last week.
10. **Scripts repo hygiene** — `cd ~/scripts && git status --short`. Any untracked files? Commit and push. Keep the repo in sync with what's actually running.
11. **Garden cull** — Scan posts published this week (`ls -lt ~/epigenome/chromatin/Writing/Blog/Published/ | head -15`). Kill or merge weak ones (thin thesis, restating others without own angle, generic advice). Write freely during the week, cull on Friday.

12. **First Friday only** — Run `/monthly` (content digests, skill review, AI deep review, vault hygiene)
   - If a checklist command fails, keep the item open and note the failure reason in the weekly note.

[[Capco Transition]] is source of truth for exit/onboarding; [[Job Hunting]] is the archive.

## Notes

- Create `~/epigenome/chromatin/Weekly/` directory if it doesn't exist
- Link back to daily notes and relevant vault notes
- The synthesis captures the broader picture; the reset checklist is action-oriented
- The energy audit is the most valuable section long-term — it reveals what work is sustainable

## Boundaries

- Do NOT run full remediation workflows inline (e.g., full nexis triage or large refactors); only surface and flag.
- Do NOT expand beyond the current week scope.
- Stop after weekly note + reset checklist outputs; do not start execution tasks unless explicitly asked.

## Example

> Week of 2026-03-02: 5/7 active days. Themes were Capco transition prep, skill-system hardening, and inbox/process hygiene. Main carry-over is one unresolved architecture decision and two overdue admin items. System health is mostly green with one unavailable check (MCP list failed).
