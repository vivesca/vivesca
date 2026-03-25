# Bud Workflows

Pre-defined workflows connecting buds to triggers and cadences.
The operon pattern: signal → regulatory check → bud expression.

## Daily Cadence

| Time | Bud | Trigger | Product |
|------|-----|---------|---------|
| 00:15 | receptor-health | LaunchAgent (cron) | receptor-retirement.md |
| 07:00 | morning-digest | Manual or photoreception | Morning brief (20 lines) |
| 18:00 | calendar-context | interphase skill trigger | Tomorrow's meeting context |
| 18:30 | inbox-triage | interphase skill trigger | Action list from email |

## Weekly Cadence

| Day | Bud | Trigger | Product |
|-----|-----|---------|---------|
| Sun PM | spark-harvest | /expression or manual | Weekly consulting sparks |
| Sun PM | praxis-sweep | /ecdysis or manual | Overdue/stale item list |
| Sun PM | commit-hygiene | /ecdysis or manual | Git quality audit |
| Sun PM | lustro weekly digest | LaunchAgent | ~/code/vivesca-terry/chromatin/Reference/weekly-ai-digest |

## Monthly Cadence

| When | What | Trigger | Product |
|------|------|---------|---------|
| Month end | monthly-review colony | /ecdysis monthly | Monthly review doc |
| Month end | autopoiesis-measure | Part of monthly colony | Automation ratio trend |
| Month end | cosplay-detector | Manual | Bio-naming audit |
| Month end | titration-probe | Manual | One new titration attempt |

## On-Demand

| Trigger | What | Product |
|---------|------|---------|
| New client/project | /proliferation skill | Burst of domain-specific buds |
| System break | incident-response colony | Fix + incident report |
| Complex architecture | architecture-review colony | Ranked findings doc |
| High-stakes deliverable | content-production colony | Polished doc with citations |
| Budget concern | glycolysis-experiment | One LLM→deterministic conversion |
| Metabolic tier = catabolic | glycolysis-audit | Full symbiont dependency scan |

## Wiring

Buds at daily/weekly cadence should be wired to kinesin tasks or
LaunchAgents. On-demand buds are spawned manually or by skills.

To wire a bud to a schedule:
1. Add to ~/code/vivesca-terry/chromatin/agent-queue.yaml (kinesin task)
2. Create LaunchAgent plist if needs to run without CC session
3. The bud definition (.md) + the schedule = complete workflow
