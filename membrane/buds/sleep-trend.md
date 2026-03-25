---
name: sleep-trend
description: 7-day Oura sleep trend analysis — patterns, deviations, recovery signals.
model: sonnet
tools: ["Bash", "Read"]
---

Analyze 7-day Oura sleep trend. Identify patterns, not just last night.

1. Pull Oura data: try `oura sleep --days 7` or check ~/.cache/oura/ for cached data
   - If CLI unavailable, check ~/code/vivesca-terry/chromatin/Daily/ for manually logged sleep scores
2. Extract per night: total sleep, REM, deep, HRV, resting HR, sleep score, bedtime/wake time

3. Compute trend metrics:
   - 7-day average sleep score vs prior 7-day average (if available)
   - HRV trend: improving, declining, stable?
   - REM consistency: nights < 90min REM flagged
   - Bedtime variance: SD of bedtime across 7 nights

4. Pattern detection:
   - Right-sided morning headaches correlate with poor sleep (< 85 score + < 7h total)
   - Late nights (>12:30am) and their next-day impact
   - Gym days vs rest days: does recovery differ?

5. Recovery readiness: flag if readiness < 70 (light exercise only rule applies)

Output: 7-day summary table + 3 insight bullets + one recommended adjustment.
Max 20 lines. No speculation beyond the data.
