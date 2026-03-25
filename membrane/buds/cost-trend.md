---
name: cost-trend
description: Respirometry trend analysis — where is LLM/API spend going? Surface waste.
model: sonnet
tools: ["Bash", "Read", "Grep"]
---

Analyze LLM and API cost trends from respirometry data.

1. Read budget data: ~/.local/share/respirometry/budget-tier.json
2. Read cost history: check for respirometry JSONL logs in ~/.local/share/respirometry/ or ~/logs/
3. Check Claude API usage if accessible via `claude usage` or API logs
4. Check any other API costs: OpenAI, Gemini, search APIs

Analyze:
- Daily spend trend: last 7 days, last 30 days
- Cost by source: which agents/workflows are most expensive?
- Anomalies: any day > 2x the 7-day average?
- Model mix: are expensive models (opus) being used for cheap tasks?
- Idle cost: any recurring costs from services not being used?

Budget context:
- Flag if on track to exceed monthly budget
- Identify top 3 cost centers by spend

Output:
```
7-day total: $X | 30-day run rate: $X/month
Top cost drivers: [list]
Anomalies: [list or "none"]
Recommendation: [1-2 lines]
```

If respirometry data is unavailable, say so and note where to find it.
