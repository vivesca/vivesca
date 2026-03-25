# Instinct-Based Auto-Learning Pattern

Source: [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) (50K+ stars, Feb 2026)

## Concept

Instead of manual write-through learning (current approach: "after ANY correction, immediately write a rule"), automate the observation→extraction pipeline:

1. **Observe** — PreToolUse/PostToolUse hooks log events to JSONL (corrections, errors, repeated workflows, tool preferences)
2. **Extract** — Background Haiku agent runs every ~5 min, produces atomic "instincts" (single learned behaviours, not full skills)
3. **Score** — Each instinct gets a confidence score (0.3 tentative → 0.9 near-certain), earned through repeated observation
4. **Promote** — High-confidence instincts graduate into permanent rules/skills; low-confidence ones decay
5. **Share** — Instincts exportable (pattern summaries only, no code) for team sharing

## What's novel vs current setup

| Aspect | Current (manual) | Instinct pattern |
|--------|-----------------|------------------|
| Trigger | User correction → Claude writes rule | Hook observes event → background agent extracts |
| Granularity | Full rules in MEMORY.md | Atomic behaviours with confidence scores |
| Coverage | Only what's noticed | Continuous — catches patterns human might miss |
| Cost | Zero (manual) | Haiku calls every 5 min |
| Reliability | Depends on Claude following CLAUDE.md | Depends on hooks firing + Haiku producing useful output |

## Why not adopted (yet)

- Falls into the class of "plans that add memory to tools" — enforcement mechanism is still "instructions tell Claude to do it"
- Background Haiku agent quality unverified — could produce noise that degrades signal
- Current manual approach is working; no repeated pain point to justify the infrastructure
- Confidence scoring is the genuinely interesting piece — could be adopted standalone without the full pipeline

## When to reconsider

- If write-through learning starts being skipped regularly (pain: losing corrections)
- If team/multi-agent setup needs shared pattern propagation
- If a lighter implementation emerges (e.g., PostToolUse hook that just logs corrections to a file, reviewed weekly)

## Detection heuristic for "correction" — IMPLEMENTED

**Hook:** `~/.claude/hooks/correction-detector.js` (PostToolUse, all tools)
**Log:** `~/.claude/corrections.jsonl`
**State:** `~/.claude/last-edits.json`

Logic: tracks Edit/Write calls per file. If the same file is edited again after a 30s+ gap (meaning user intervened between edits), logs it as a potential correction with timestamps, gap duration, and before/after snippets.

Not a correction: same-response multi-edits (< 30s gap, filtered out).

Review the log periodically — signal-to-noise TBD. Kill the hook if it's pure noise after a few weeks.
