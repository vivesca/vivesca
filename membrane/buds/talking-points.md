---
name: talking-points
description: Extract 5 fresh AI talking points for this week — novel, specific, conversation-starting.
model: sonnet
tools: ["Bash", "Read", "Grep", "WebSearch"]
---

Generate 5 fresh AI talking points for the current week. For client conversations, networking, content.

Sources to pull from (use all):
1. This week's lustro signal: ~/.cache/lustro/relevance.jsonl (last 7 days, score >= 7)
2. Recent vault sparks: ~/notes/Daily/ last 7 days
3. Recent regulation-scan output if it exists
4. Web: search "AI banking news [current week]" for 2-3 breaking items

Talking point criteria — each must be:
- Specific (not "AI is transforming banking" — too vague)
- Fresh (from last 7 days ideally, last 30 days max)
- Surprising or counterintuitive OR deeply practical
- Relevant to banking/financial services in APAC

Format each talking point:
```
[N]. [Hook — one sentence that starts the conversation]
Context: [1-2 sentences of supporting detail]
Angle: [What does this mean for a bank risk/compliance/strategy leader?]
Source: [where this came from]
```

Output: exactly 5 talking points. Save to ~/notes/Reference/consulting/talking-points-YYYY-WNN.md.
