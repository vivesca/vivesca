# Skill as Renderer Pattern

**Principle:** Skills fetch results; LaunchAgents collect them. Pre-compute in background, render instantly.

## The Problem

Skills that gather data live (API calls, file scans, web fetches) have variable latency and can fail mid-render. A skill that calls three APIs before showing output is fragile and slow.

## The Pattern

```
LaunchAgent (scheduled)     →  writes snapshot to known path
Skill (on demand)           →  reads snapshot, renders instantly
```

The skill becomes a pure reader. It can't fail due to network issues. It always returns in <1s.

## Examples

| Data | Background writer | Snapshot path | Skill |
|------|------------------|---------------|-------|
| Queue results | `legatus-notify` (post-batch) | `~/.cache/legatus-runs/latest-summary.md` | `/overnight`, `/auspex` |
| AI news | `lustro` (LaunchAgent, daily) | `~/epigenome/chromatin/AI & Tech/` | `/auspex` |
| Sleep data | `oura-sync` (LaunchAgent) | `~/oura-data/data/oura.duckdb` | `/oura`, `/nyx` |

## When to Apply

- Data has latency >2s to fetch live
- Data changes on a known schedule (not real-time)
- Multiple skills need the same data (single writer, multiple readers)
- Skill is used at session start (latency compounds with other setup)

## When Not to Apply

- Data must be real-time (current calendar, live Due reminders)
- Data is user-specific to the moment (search results, ad-hoc queries)
- LaunchAgent overhead exceeds the latency saved

## Tradeoff

Pre-computed snapshots can be stale. Tag snapshots with a timestamp and surface it in the render:
```
Last updated: 16:30 (38 min ago)
```
Let the user decide if it's fresh enough.

## Related

- `cron-hygiene.md` — LaunchAgent conventions
- `mcp-vs-cli-vs-skill.md` — when to use each layer
