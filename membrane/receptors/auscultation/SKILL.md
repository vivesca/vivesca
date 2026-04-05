---
name: auscultation
description: Passive log listening — spot error patterns and timing anomalies. Use when something feels off but no single error is visible. "check logs", "listen to logs"
user_invocable: true
model: sonnet
context: fork
epistemics: [monitor, debug]
---

# Auscultation — Diagnostic Listening

A physician places a stethoscope and listens. Not looking, not probing — listening. Heart rhythm, breath sounds, bowel sounds. Each organ has a signature. Abnormal sounds precede visible symptoms.

Auscultation is passive diagnostic listening to system internals: log streams, error rates, timing distributions, silence where there should be sound. You learn to hear what the organism is saying.

## When to Use

- Something feels off but no single error is visible
- Preparing for a deeper investigation (palpation, integrin)
- After a deployment — confirm the new organism sounds right
- Scheduled: periodic listening to detect drift before it becomes failure
- The organism has been quiet too long (silence is also a sound)

## Method

### Step 1 — Find the listening surfaces

```bash
# LaunchAgent logs
ls ~/Library/Logs/vivesca/
tail -100 ~/Library/Logs/vivesca/*.log

# System process sounds
log show --predicate 'process == "python3"' --last 1h | grep -i error

# Cron / scheduled job output
cat ~/tmp/*.log | grep -E "(ERROR|WARN|FAIL)"

# MCP server health
# homeostasis_system tool
```

### Step 2 — Listen for rhythm anomalies

Normal rhythm: scheduled jobs fire on time, produce output, exit clean.

```bash
# Check last run times against expected schedule
grep "started\|completed\|error" ~/Library/Logs/vivesca/*.log | tail -50

# Duration anomalies (jobs that ran too long or too short)
# A job that always takes 30s now takes 5s = silent failure
# A job that always takes 30s now takes 300s = hanging
```

### Step 3 — Listen for error frequencies

One error = event. Same error 50 times = pattern. Pattern = finding.

```bash
grep -h "ERROR" ~/Library/Logs/vivesca/*.log | \
  sed 's/[0-9]//g' | sort | uniq -c | sort -rn | head -20
```

### Step 4 — Listen for silence

What should have made noise but didn't?
- Daily digest not in inbox → transduction failed
- Chromatin note count not growing → intake pipeline stalled
- No telemetry from a process that usually reports → process died silently

### Step 5 — Report the soundscape

Three categories:
- **Healthy sounds:** rhythm normal, no anomalous patterns
- **Concerning sounds:** patterns that warrant follow-up (palpation next)
- **Silence:** expected sounds absent

## Auscultation vs Palpation vs Integrin

| Skill | Approach | Depth |
|-------|----------|-------|
| auscultation | Passive listening to existing signals | Broad, shallow |
| palpation | Active manual probing of specific component | Narrow, deep |
| integrin | Automated probe across surfaces | Systematic, programmatic |

## Anti-patterns

- **Diagnosing while listening:** auscultation surfaces findings, not conclusions. Resist fixing during the listening pass.
- **Only listening to errors:** silence and rhythm anomalies are signals too. Don't filter to ERROR lines only.
- **Listening without a baseline:** you can't hear abnormal without knowing normal. Establish rhythm expectations first.
