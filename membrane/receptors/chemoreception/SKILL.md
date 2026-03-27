---
name: chemoreception
description: On-demand AI landscape briefing when transduction output is stale or a meeting needs fresh signal. Governance translation + meeting routing.
user_invocable: true
model: sonnet
context: fork
epistemics: [research, monitor]
---

# /chemoreception — On-Demand AI Briefing

Augments transduction's scheduled pipeline with live search, governance action, and meeting routing. The pipeline handles cadence (daily/weekly/monthly/quarterly). This skill fires on demand.

## When to Use

- Before a client meeting or interview where AI landscape matters
- When transduction output is >3 days stale and Terry asks "what's happening in AI"
- When a specific development needs governance translation

## Step 1: Read Current State

- Read `[[Transduction]]` index for latest snapshot date
- If <3 days old and no meeting context, surface the latest snapshot — don't re-gather
- If stale or meeting-specific, proceed to Step 2

## Step 2: Live Gather

2-3 targeted WebSearches:
- "AI news banking financial services [month] [year]"
- "HKMA AI regulation [month] [year]"
- Topic-specific search if meeting context is known

Track provenance: note which items are fresh vs from existing snapshots.

## Step 3: Governance Translation Pass

For each significant development, ask: **does this expose a governance gap no current framework (MAS AIRM, HKMA, PRA SS1/23) explicitly covers?**

If yes — act:
1. Add row to `[[Capco - AI Regulatory Gap Assessment 2026]]`
2. If vendor/procurement: add clause to `codex-argentum-v1.txt` Section 8 or 3
3. Re-upload Codex Argentum to Lacuna if changed
4. Note what was updated

**Bar:** genuinely novel gap + clear trigger. When in doubt, flag don't act.

## Step 4: Meeting Routing

- Check `~/epigenome/chromatin/Praxis.md` for upcoming meetings
- Check `[[Capco Transition]]` for HSBC context
- If relevant to a specific meeting/interview, add talking points directly to that prep note
- For interview prep notes, add "Fresh intel" section with 3-4 bullets

## Anti-Patterns

- **Don't duplicate transduction.** If the pipeline ran this week, start from its output.
- **Don't be comprehensive.** 5 opinionated items beats 20 neutral summaries.
- **Don't hedge.** Take positions.

## Spark Routing

If any governance-relevant shift was identified in Steps 2–3, append to `~/epigenome/chromatin/Consulting/_sparks.md` under today's date: `- #policy-gap — **[Development]**: [one-line FS governance implication]`
